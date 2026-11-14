TOKEN = {"X-Reviewer-Token": "test-token"}


def make_patient(client, age=68):
    """Creates a household and, like the family app, sends its private key from then on."""
    r = client.post("/patients", json={"name": "Test Patient", "age": age})
    assert r.status_code == 201
    client.headers["X-Family-Key"] = r.json()["family_key"]
    return r.json()["id"]


def add(client, pid, brand, **kw):
    r = client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": brand, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def test_family_view_never_returns_pending_or_dismissed(client):
    pid = make_patient(client)
    for b in ("Napa", "Ace", "Rivotril", "Tryptin"):
        add(client, pid, b, prescriber=b)
    assert client.post(f"/patients/{pid}/check").status_code == 200

    reviewer = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()
    assert len(reviewer) >= 3 and all(f["status"] == "pending_review" for f in reviewer)
    assert client.get(f"/patients/{pid}/flags?view=family").json() == []

    confirm, dismiss = reviewer[0]["id"], reviewer[1]["id"]
    r = client.post(f"/flags/{confirm}/review", headers=TOKEN,
                    json={"status": "confirmed", "reviewer": "Pharm", "note": "Seen"})
    assert r.status_code == 200 and r.json()["explanation_bn"]
    client.post(f"/flags/{dismiss}/review", headers=TOKEN,
                json={"status": "dismissed", "reviewer": "Pharm", "note": "Old strip, not in use"})

    family = client.get(f"/patients/{pid}/flags?view=family").json()
    assert [f["id"] for f in family] == [confirm]
    assert all(f["status"] == "confirmed" for f in family)
    # the default view is the family view
    assert [f["id"] for f in client.get(f"/patients/{pid}/flags").json()] == [confirm]


def test_reviewer_endpoints_need_token(client):
    pid = make_patient(client)
    assert client.get(f"/patients/{pid}/flags?view=reviewer").status_code == 401
    bad = {"X-Reviewer-Token": "nope"}
    assert client.get(f"/patients/{pid}/flags?view=reviewer", headers=bad).status_code == 401
    assert client.get("/flags").status_code == 401
    assert client.post("/flags/1/review", json={"status": "confirmed", "reviewer": "x"}).status_code == 401


def test_dismiss_requires_note(client):
    pid = make_patient(client)
    add(client, pid, "Napa", prescriber="a")
    add(client, pid, "Ace", prescriber="b")
    client.post(f"/patients/{pid}/check")
    fid = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]["id"]
    r = client.post(f"/flags/{fid}/review", headers=TOKEN, json={"status": "dismissed", "reviewer": "P"})
    assert r.status_code == 422


def test_rerunning_check_keeps_review_decisions(client):
    pid = make_patient(client)
    add(client, pid, "Napa", prescriber="shop")
    add(client, pid, "Ace", prescriber="village")
    client.post(f"/patients/{pid}/check")
    fid = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]["id"]
    client.post(f"/flags/{fid}/review", headers=TOKEN, json={"status": "confirmed", "reviewer": "Dr", "note": "ok"})

    add(client, pid, "Seclo")  # an unrelated new medicine
    client.post(f"/patients/{pid}/check")
    client.post(f"/patients/{pid}/check")
    flags = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()
    dup = [f for f in flags if f["code"] == "DUPLICATE_GENERIC"]
    assert len(dup) == 1 and dup[0]["id"] == fid
    assert dup[0]["status"] == "confirmed" and dup[0]["reviewer"] == "Dr"


def test_undo_returns_flag_to_pending_and_hides_it_from_family(client):
    pid = make_patient(client)
    add(client, pid, "Napa", prescriber="a")
    add(client, pid, "Ace", prescriber="b")
    client.post(f"/patients/{pid}/check")
    fid = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]["id"]
    client.post(f"/flags/{fid}/review", headers=TOKEN, json={"status": "confirmed", "reviewer": "Dr"})
    assert len(client.get(f"/patients/{pid}/flags").json()) == 1
    client.post(f"/flags/{fid}/undo?reviewer=Dr", headers=TOKEN)
    assert client.get(f"/patients/{pid}/flags").json() == []
    trail = client.get(f"/patients/{pid}/reviews", headers=TOKEN).json()
    assert [r["status"] for r in trail] == ["undone", "confirmed"]


def test_unconfirmed_items_are_not_checked(client):
    pid = make_patient(client)
    client.post(f"/patients/{pid}/items", json={"brand": "Napa"})
    client.post(f"/patients/{pid}/items", json={"brand": "Ace"})
    assert client.post(f"/patients/{pid}/check").json()["flags_total"] == 0


def test_low_confidence_and_unknown_items_need_review(client):
    pid = make_patient(client)
    low = client.post(f"/patients/{pid}/items", json={"brand": "Napa", "confidence": 0.6}).json()
    unknown = client.post(f"/patients/{pid}/items", json={"brand": "Zzyxoprin"}).json()
    ok = client.post(f"/patients/{pid}/items", json={"brand": "Napa", "confidence": 0.9}).json()
    assert low["needs_review"] and unknown["needs_review"] and not ok["needs_review"]
    assert unknown["match_method"] == "not_found"


def test_editing_brand_rematches_it(client):
    pid = make_patient(client)
    item = client.post(f"/patients/{pid}/items", json={"brand": "Nappa", "confidence": 0.5}).json()
    fixed = client.patch(f"/items/{item['id']}", json={"brand": "Ace", "confirmed": True}).json()
    assert fixed["generic"] == "paracetamol" and fixed["confirmed"] and not fixed["needs_review"]


def test_family_status_never_exposes_pending_details(client):
    pid = make_patient(client)
    add(client, pid, "Napa", prescriber="a")
    add(client, pid, "Ace", prescriber="b")
    client.post(f"/patients/{pid}/check")
    s = client.get(f"/patients/{pid}/status").json()
    assert s["review_state"] == "in_review" and s["confirmed_flags"] == 0
    assert "flags" not in s


def test_demo_scan_without_keys_returns_demo_household(client):
    pid = make_patient(client)
    photo = ("photos", ("shelf.jpg", b"not-really-a-jpeg", "image/jpeg"))
    r = client.post(f"/patients/{pid}/scan", files=[photo])
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo" and len(body["items"]) == 9
    assert all(not it["confirmed"] for it in body["items"])


def test_passport_and_report(client):
    pid = make_patient(client)
    add(client, pid, "Camlodin", schedule=["morning"], pills_left=3, doses_per_day=1)
    add(client, pid, "Comet", schedule=["morning", "night"])
    p = client.get(f"/patients/{pid}/passport").json()
    assert [m["brand"] for m in p["groups"]["morning"]] == ["Camlodin", "Comet"]
    assert [m["brand"] for m in p["groups"]["night"]] == ["Comet"]
    rep = client.get(f"/patients/{pid}/report").json()
    assert rep["refills_due"][0]["brand"] == "Camlodin"
    assert rep["doses"] is None  # no invented numbers for real patients


def test_health_reports_names_not_keys(client, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-secret-value")
    h = client.get("/health").json()
    assert "tvly-secret-value" not in str(h)
    assert h["web_lookup"]["tavily"] is True
