import os

import pytest

from app.models import Flag, MedicineItemIn, PatientIn, ReviewIn

TOKEN = {"X-Reviewer-Token": "test-token"}
PHOTO = ("photos", ("shelf.jpg", b"not-really-a-jpeg", "image/jpeg"))


def household(client):
    r = client.post("/patients", json={"name": "Private Household", "age": 70})
    assert r.status_code == 201
    return r.json()["id"], r.json()["family_key"]


# ---- private family links --------------------------------------------------------------

FAMILY_ROUTES = ["", "/items", "/status", "/flags", "/passport", "/report"]


def test_household_is_not_found_without_its_key(client):
    pid, key = household(client)
    for route in FAMILY_ROUTES:
        url = f"/patients/{pid}{route}"
        assert client.get(url).status_code == 404, url
        assert client.get(url, headers={"X-Family-Key": "wrong"}).status_code == 404, url
        assert client.get(url, headers={"X-Family-Key": key}).status_code == 200, url
        assert client.get(url, headers=TOKEN).status_code == 200, url  # reviewers see every household
    assert client.post(f"/patients/{pid}/items", json={"brand": "Napa"}).status_code == 404
    assert client.post(f"/patients/{pid}/scan", files=[PHOTO]).status_code == 404
    assert client.post(f"/patients/{pid}/bp", json={"systolic": 140, "diastolic": 90}).status_code == 404


def test_items_need_the_key_of_their_household(client):
    pid, key = household(client)
    other_pid, other_key = household(client)
    item = client.post(f"/patients/{pid}/items", json={"brand": "Napa"}, headers={"X-Family-Key": key}).json()
    assert client.patch(f"/items/{item['id']}", json={"confirmed": True}).status_code == 404
    assert client.patch(f"/items/{item['id']}", json={"confirmed": True},
                        headers={"X-Family-Key": other_key}).status_code == 404
    assert client.delete(f"/items/{item['id']}", headers={"X-Family-Key": other_key}).status_code == 404
    assert client.patch(f"/items/{item['id']}", json={"confirmed": True},
                        headers={"X-Family-Key": key}).status_code == 200


def test_demo_household_stays_open(client, store):
    demo = store.create_patient(PatientIn(name="Demo", age=68, is_demo=True))
    assert client.get(f"/patients/{demo.id}/passport").status_code == 200


def test_missing_and_private_households_look_the_same(client):
    pid, _ = household(client)
    assert client.get(f"/patients/{pid}").json() == client.get("/patients/99999").json()


def test_patient_list_is_reviewer_only(client):
    _, key = household(client)
    assert client.get("/patients").status_code == 401
    rows = client.get("/patients", headers=TOKEN).json()
    assert rows[0]["family_key"] == key


def test_nobody_creates_demo_households_over_the_api(client):
    assert client.post("/patients", json={"name": "X", "age": 70, "is_demo": True}).status_code == 422


# ---- rate limits -----------------------------------------------------------------------

def test_scan_is_rate_limited_per_ip(client, monkeypatch):
    monkeypatch.setenv("SCAN_LIMIT_PER_IP", "2")
    pid, key = household(client)
    h = {"X-Family-Key": key, "X-Forwarded-For": "203.0.113.7, 10.0.0.1"}
    assert [client.post(f"/patients/{pid}/scan", files=[PHOTO], headers=h).status_code for _ in range(3)] == [200, 200, 429]
    # another address still gets through
    h2 = {**h, "X-Forwarded-For": "198.51.100.4"}
    assert client.post(f"/patients/{pid}/scan", files=[PHOTO], headers=h2).status_code == 200


def test_forged_forwarded_for_does_not_reset_the_limit_behind_cloudflare(client, monkeypatch):
    monkeypatch.setenv("SCAN_LIMIT_PER_IP", "1")
    pid, key = household(client)
    codes = [client.post(f"/patients/{pid}/scan", files=[PHOTO],
                         headers={"X-Family-Key": key, "CF-Connecting-IP": "203.0.113.9",
                                  "X-Forwarded-For": f"10.9.9.{i}"}).status_code
             for i in range(2)]
    assert codes == [200, 429]


def test_scan_has_a_global_daily_ceiling(client, monkeypatch):
    monkeypatch.setenv("SCAN_LIMIT_GLOBAL", "2")
    pid, key = household(client)
    codes = [client.post(f"/patients/{pid}/scan", files=[PHOTO],
                         headers={"X-Family-Key": key, "X-Forwarded-For": f"198.51.100.{i}"}).status_code
             for i in range(3)]
    assert codes == [200, 200, 429]


def test_new_households_are_rate_limited(client, monkeypatch):
    monkeypatch.setenv("PATIENT_LIMIT_PER_IP", "2")
    codes = [client.post("/patients", json={"name": "H", "age": 70}).status_code for _ in range(3)]
    assert codes == [201, 201, 429]


# ---- blood pressure --------------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    {"systolic": 300, "diastolic": 90},
    {"systolic": 140, "diastolic": 10},
    {"systolic": 90, "diastolic": 120},
    {"systolic": 140, "diastolic": 90, "taken_on": "2999-01-01"},
])
def test_bp_rejects_implausible_readings(client, bad):
    pid, key = household(client)
    assert client.post(f"/patients/{pid}/bp", json=bad, headers={"X-Family-Key": key}).status_code == 422


def test_bp_json_body_and_query_params(client):
    pid, key = household(client)
    h = {"X-Family-Key": key}
    r = client.post(f"/patients/{pid}/bp", json={"systolic": 150, "diastolic": 95, "taken_on": "2026-10-20"}, headers=h)
    assert r.status_code == 201 and r.json()["readings"][-1]["systolic"] == 150
    assert client.post(f"/patients/{pid}/bp?systolic=142&diastolic=88", headers=h).status_code == 201
    assert client.post(f"/patients/{pid}/bp?systolic=88&diastolic=142", headers=h).status_code == 422
    readings = client.get(f"/patients/{pid}/report", headers=h).json()["bp"]["readings"]
    assert [x["systolic"] for x in readings] == [150, 142]


# ---- store round-trip: SQLite always, Postgres when TEST_DATABASE_URL is set ------------

def _stores(tmp_path):
    from app.store import Store
    yield "sqlite", Store(tmp_path / "rt.db")
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        s = Store(url=url)
        s.reset()
        yield "postgres", s


def test_store_round_trip(tmp_path):
    for name, s in _stores(tmp_path):
        p = s.create_patient(PatientIn(name="RT", age=70, conditions=["htn"]))
        assert s.family_key(p.id) and s.get_patient(p.id).conditions == ["htn"], name
        a = s.add_item(p.id, MedicineItemIn(brand="Napa", schedule=["morning"], confidence=0.8), generic="paracetamol")
        b = s.add_item(p.id, MedicineItemIn(brand="Ace"), generic="paracetamol")
        assert s.update_item(a.id, confirmed=True, pills_left=4).pills_left == 4, name
        assert s.get_item(a.id).confidence == pytest.approx(0.8), name
        flag = Flag(key="dup:paracetamol", code="DUPLICATE_GENERIC", severity="red", item_ids=[a.id, b.id],
                    evidence="same generic", routed_to="doctor", data_source="test", meta={"generic": "paracetamol"})
        [stored] = s.sync_flags(p.id, [flag])
        s.review_flag(stored.id, ReviewIn(status="confirmed", reviewer="Dr"), "ব্যাখ্যা")
        assert s.sync_flags(p.id, [flag])[0].status == "confirmed", name  # upsert keeps the decision
        assert s.sync_flags(p.id, []) == [], name  # no longer produced: inactive, not deleted
        assert s.list_reviews(p.id)[0]["status"] == "confirmed", name
        s.add_bp(p.id, "2026-10-20", 150, 95)
        assert s.list_bp(p.id) == [{"taken_on": "2026-10-20", "systolic": 150, "diastolic": 95}], name
        s.cache_set("k", "1")
        s.cache_set("k", "2")
        assert s.cache_get("k") == "2", name
        assert s.delete_item(b.id) and not s.delete_item(b.id), name


def test_old_databases_get_family_keys(tmp_path):
    import sqlite3

    from app.store import Store

    path = tmp_path / "old.db"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_bn TEXT, age INTEGER NOT NULL,"
               " district TEXT, conditions TEXT NOT NULL DEFAULT '[]', is_demo INTEGER NOT NULL DEFAULT 0,"
               " created_at TEXT NOT NULL, last_checked_at TEXT)")
    db.execute("INSERT INTO patients (name, age, created_at) VALUES ('Old', 70, '2026-01-01T00:00:00+00:00')")
    db.commit()
    db.close()
    s = Store(path)
    assert s.family_key(1) and len(s.family_key(1)) >= 20
