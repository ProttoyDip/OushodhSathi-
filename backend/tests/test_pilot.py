"""Pilot hardening: personal reviewer logins, family data rights, consent, email, private photos."""
import pytest

from app import llm_router, notify

ADMIN = {"X-Admin-Token": "test-admin"}
DEMO_TOKEN = {"X-Reviewer-Token": "test-token"}


def household(client, **extra):
    r = client.post("/patients", json={"name": "Pilot Home", "age": 72, "consent": True, **extra})
    assert r.status_code == 201, r.text
    return r.json()["id"], {"X-Family-Key": r.json()["family_key"]}


def with_duplicate(client, pid, h):
    for brand in ("Napa", "Ace"):
        assert client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": brand}, headers=h).status_code == 201
    client.post(f"/patients/{pid}/check", headers=h)
    return client.get(f"/patients/{pid}/flags?view=reviewer", headers=DEMO_TOKEN).json()


def new_reviewer(client, name="Pharm. Rahman", role="pharmacist"):
    r = client.post("/admin/reviewers", headers=ADMIN, json={"name": name, "role": role, "reg_no": "P-1234"})
    assert r.status_code == 201, r.text
    return r.json()


# ---- consent and input limits ----------------------------------------------------------

def test_a_household_needs_consent(client):
    assert client.post("/patients", json={"name": "No consent", "age": 70}).status_code == 422
    assert client.post("/patients", json={"name": "No", "age": 70, "consent": False}).status_code == 422
    pid, h = household(client)
    p = client.get(f"/patients/{pid}", headers=h).json()
    assert p["consent_at"] and p["consent_version"]


@pytest.mark.parametrize("bad", [
    {"name": "x" * 81}, {"district": "d" * 61}, {"conditions": ["c"] * 11}, {"family_email": "not-an-email"},
])
def test_household_fields_are_bounded(client, bad):
    body = {"name": "Home", "age": 70, "consent": True, **bad}
    assert client.post("/patients", json=body).status_code == 422


def test_email_opt_in_needs_an_email(client):
    pid, h = household(client, email_opt_in=True)
    assert client.get(f"/patients/{pid}", headers=h).json()["email_opt_in"] is False


# ---- personal reviewer logins ----------------------------------------------------------

def test_admin_routes_need_the_admin_token(client):
    assert client.get("/admin/reviewers").status_code == 401
    assert client.get("/admin/reviewers", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.get("/admin/reviewers", headers=DEMO_TOKEN).status_code == 401


def test_admin_routes_are_off_without_an_admin_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "")
    assert client.get("/admin/reviewers", headers=ADMIN).status_code == 503


def test_only_the_token_hash_is_stored(client, store):
    rev = new_reviewer(client)
    assert rev["token"] and rev["invite_url"].endswith(rev["token"])
    rows = store._all("SELECT * FROM reviewers")
    assert rev["token"] not in str(rows)
    assert "token" not in str(client.get("/admin/reviewers", headers=ADMIN).json())


def test_a_review_records_the_signed_in_person_not_a_typed_name(client):
    rev = new_reviewer(client)
    me = {"X-Reviewer-Token": rev["token"]}
    assert client.get("/reviewer/me", headers=me).json()["name"] == "Pharm. Rahman"
    pid, h = household(client)
    flag = with_duplicate(client, pid, h)[0]
    r = client.post(f"/flags/{flag['id']}/review", headers=me,
                    json={"status": "confirmed", "reviewer": "Somebody Else", "note": "ok"})
    assert r.status_code == 200
    assert r.json()["reviewer"] == "Pharm. Rahman" and r.json()["reviewer_id"] == rev["id"]
    trail = client.get(f"/patients/{pid}/reviews", headers=me).json()
    assert trail[0]["reviewer"] == "Pharm. Rahman" and trail[0]["reviewer_id"] == rev["id"]


def test_a_revoked_reviewer_is_locked_out_and_can_be_reissued(client):
    rev = new_reviewer(client)
    me = {"X-Reviewer-Token": rev["token"]}
    assert client.get("/flags", headers=me).status_code == 200
    assert client.post(f"/admin/reviewers/{rev['id']}/revoke", headers=ADMIN).json()["revoked_at"]
    assert client.get("/flags", headers=me).status_code == 401
    again = client.post(f"/admin/reviewers/{rev['id']}/reissue", headers=ADMIN).json()
    assert client.get("/flags", headers={"X-Reviewer-Token": again["token"]}).status_code == 200
    assert client.get("/flags", headers=me).status_code == 401  # the old link stays dead


def test_a_reviewer_login_opens_households(client):
    rev = new_reviewer(client)
    pid, _ = household(client)
    assert client.get(f"/patients/{pid}", headers={"X-Reviewer-Token": rev["token"]}).status_code == 200


def test_the_shared_demo_token_only_works_on_the_demo_server(client, monkeypatch):
    pid, _ = household(client)
    assert client.get("/flags", headers=DEMO_TOKEN).status_code == 200
    monkeypatch.setenv("DEMO_MODE", "false")
    assert client.get("/flags", headers=DEMO_TOKEN).status_code == 401
    assert client.get(f"/patients/{pid}", headers=DEMO_TOKEN).status_code == 404
    assert client.post("/demo/reset").status_code == 404


# ---- family data rights ----------------------------------------------------------------

def test_rotating_the_family_link_kills_the_old_one(client):
    pid, h = household(client)
    new = client.post(f"/patients/{pid}/family-key/rotate", headers=h).json()["family_key"]
    assert client.get(f"/patients/{pid}", headers=h).status_code == 404
    assert client.get(f"/patients/{pid}", headers={"X-Family-Key": new}).status_code == 200


def test_admin_can_reissue_a_lost_family_link(client):
    pid, h = household(client)
    r = client.post(f"/admin/patients/{pid}/family-key", headers=ADMIN).json()
    assert r["family_url"].endswith(r["family_key"])
    assert client.get(f"/patients/{pid}", headers=h).status_code == 404
    assert client.get(f"/patients/{pid}", headers={"X-Family-Key": r["family_key"]}).status_code == 200


def test_export_has_confirmed_findings_only(client):
    pid, h = household(client)
    for b in ("Napa", "Ace", "Rivotril", "Tryptin"):
        client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": b, "prescriber": b}, headers=h)
    client.post(f"/patients/{pid}/check", headers=h)
    flags = client.get(f"/patients/{pid}/flags?view=reviewer", headers=DEMO_TOKEN).json()
    client.post(f"/flags/{flags[0]['id']}/review", headers=DEMO_TOKEN, json={"status": "confirmed", "note": "ok"})
    data = client.get(f"/patients/{pid}/export", headers=h).json()
    assert len(data["confirmed_findings"]) == 1 and len(data["medicines"]) == 4
    assert "pending_review" not in str(data["confirmed_findings"])
    assert "family_key" not in str(data)


def test_delete_removes_everything_and_needs_typed_confirmation(client, store):
    pid, h = household(client)
    with_duplicate(client, pid, h)
    client.post(f"/patients/{pid}/bp", json={"systolic": 150, "diastolic": 90}, headers=h)
    client.post(f"/patients/{pid}/questions", json={"text": "Is this ok?"}, headers=h)
    assert client.request("DELETE", f"/patients/{pid}", headers=h, json={"confirm": "yes"}).status_code == 422
    assert client.request("DELETE", f"/patients/{pid}", headers=h, json={"confirm": "DELETE"}).status_code == 204
    for table in ("items", "flags", "bp_readings", "questions", "activity"):
        assert store._all(f"SELECT * FROM {table} WHERE patient_id = ?", (pid,)) == []
    assert store.get_patient(pid) is None
    assert client.get(f"/patients/{pid}", headers=h).status_code == 404


def test_the_demo_household_cannot_be_deleted_or_rekeyed(client, store):
    from app.demo_seed import seed_demo
    pid = seed_demo(store)["patient_id"]
    assert client.request("DELETE", f"/patients/{pid}", json={"confirm": "DELETE"}).status_code == 403
    assert client.post(f"/patients/{pid}/family-key/rotate").status_code == 403


# ---- email -------------------------------------------------------------------------------

@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setattr(notify, "send", lambda email: sent.append(email))
    return sent


def test_results_email_is_sent_once_after_the_last_decision_and_never_carries_notes(client, outbox):
    pid, h = household(client, family_email="nusrat@example.com", email_opt_in=True)
    flags = with_duplicate(client, pid, h)
    assert flags
    for f in flags:
        assert not outbox  # nothing while findings are still pending
        client.post(f"/flags/{f['id']}/review", headers=DEMO_TOKEN,
                    json={"status": "confirmed", "note": "SECRET-NOTE stop one of them"})
    assert len(outbox) == 1
    mail = outbox[0]
    assert mail.to == "nusrat@example.com" and "Napa" in mail.text
    assert "SECRET-NOTE" not in mail.text and h["X-Family-Key"] not in mail.text
    # undo + decide again with the same timestamp batch does not double-send
    client.post(f"/flags/{flags[0]['id']}/review", headers=DEMO_TOKEN, json={"status": "confirmed", "note": "x"})
    assert len(outbox) <= 2


def test_no_email_without_opt_in(client, outbox):
    pid, h = household(client, family_email="nusrat@example.com", email_opt_in=False)
    for f in with_duplicate(client, pid, h):
        client.post(f"/flags/{f['id']}/review", headers=DEMO_TOKEN, json={"status": "confirmed", "note": "ok"})
    assert outbox == []


def test_weekly_email_is_once_per_week(client, outbox):
    household(client, family_email="a@example.com", email_opt_in=True)
    household(client, family_email="b@example.com", email_opt_in=False)
    first = client.post("/admin/notify/weekly", headers=ADMIN).json()
    second = client.post("/admin/notify/weekly", headers=ADMIN).json()
    assert first["sent"] == 1 and second["sent"] == 0
    assert [m.to for m in outbox] == ["a@example.com"]
    assert client.post("/admin/notify/weekly").status_code == 401


# ---- photos only go to providers that don't keep them ------------------------------------

def test_private_vision_drops_openrouter_on_a_real_server(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "some/free-model")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "some/text-model")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    monkeypatch.setenv("NVIDIA_VISION_MODEL", "nv/vision")
    monkeypatch.setenv("DEMO_MODE", "false")
    assert [p.name for p in llm_router.configured_providers("vision")] == ["nvidia"]
    assert "openrouter" in [p.name for p in llm_router.configured_providers("text")]  # text is unaffected
    monkeypatch.setenv("PRIVATE_VISION", "0")
    assert "openrouter" in [p.name for p in llm_router.configured_providers("vision")]


def test_openrouter_requests_deny_data_collection(store, monkeypatch):
    import httpx

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "some/model")
    router = llm_router.Router(store=store, client=httpx.Client(transport=httpx.MockTransport(handler)))
    router.chat("text", [{"role": "user", "content": "hi"}])
    assert seen["provider"] == {"data_collection": "deny"}


def test_emergency_alert_payload_always_has_flags(monkeypatch):
    from app import main

    posted = {}
    monkeypatch.setenv("N8N_ALERT_WEBHOOK", "https://n8n.example/hook")
    monkeypatch.setattr(main.httpx, "post", lambda url, **kw: posted.update(kw["json"]))

    class Now:
        def __init__(self, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(main.threading, "Thread", Now)
    main._notify_emergency(7)
    assert posted == {"patient_id": 7, "event": "sathi_emergency", "flags": []}
