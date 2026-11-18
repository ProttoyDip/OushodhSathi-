"""Daily Bangla check-in call with the simulator adapter: no account, no number, no network."""
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet

from app import explain
from app.voice_calls import phone as phones
from app.voice_calls import script, service
from app.voice_calls.simulator import SimulatorProvider
from tests.test_clinical import TOKEN, add, household

ADMIN = {"X-Admin-Token": "test-admin"}
CONSENT = {"local_time": "19:30", "consent": True, "consent_by": "daughter"}


def approved_household(client, slots=("morning", "night")):
    pid = household(client)
    it = add(client, pid, "Seclo", schedule=list(slots), prescriber="Dr A")
    r = client.post(f"/patients/{pid}/schedule/approve", headers=TOKEN, json={"reviewer": "P"})
    assert r.status_code == 200, r.text
    return pid, it["id"]


def at(hh, mm=0, day="2026-11-15"):
    return datetime.fromisoformat(f"{day}T{hh:02d}:{mm:02d}:00+06:00")


# ---- the script -------------------------------------------------------------------------------

def test_script_is_safe_and_names_no_one():
    for pid, texts in script.PROMPTS.items():
        assert explain.is_safe(texts["bn"]), pid
        for word in ("বন্ধ কর", "দ্বিগুণ", "বাদ দিন", "শুরু কর", "বাড়িয়ে", "কমিয়ে", "stop", "double", "skip"):
            assert word not in texts["bn"] and word not in texts["en"].lower()
    assert script.PROMPTS["emergency"]["bn"].startswith("এখনই ৯৯৯")


def test_state_machine_branches():
    steps = script.steps_for(["night", "morning"])
    assert steps == ["slot_morning", "slot_night", "emergency_ask"]
    i, rep, t = script.advance(steps, 0, "1", False)
    assert (i, t.record) == (1, {"morning": "taken"}) and t.play == ["slot_night"]
    i, rep, t = script.advance(steps, 1, None, False)          # no key: repeat once
    assert (i, rep, t.record) == (1, True, {})
    i, rep, t = script.advance(steps, 1, None, True)           # still nothing: move on, record nothing
    assert (i, t.record, t.play) == (2, {}, ["emergency_ask"])
    i, rep, t = script.advance(steps, 2, "1", True)
    assert t.done and t.play == ["closing"] and not t.emergency
    _, _, t = script.advance(steps, 0, "9", False)              # 9 anywhere
    assert t.emergency and t.done and t.play == ["emergency", "closing"]


# ---- consent and settings ---------------------------------------------------------------------

def test_consent_is_required_and_time_is_checked(client):
    pid, _ = approved_household(client)
    assert client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "consent": False}).status_code == 422
    assert client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "local_time": "22:00"}).status_code == 422
    assert client.post(f"/patients/{pid}/calls/test").status_code == 409  # not turned on
    r = client.put(f"/patients/{pid}/calls/settings", json=CONSENT).json()
    assert r["active"] and r["provider"] == "simulator" and not r["needs_phone"] and r["approved_slots"] == ["morning", "night"]
    assert client.delete(f"/patients/{pid}/calls/settings").json()["active"] is False


def test_phone_is_encrypted_and_erased_on_stop(client, store, monkeypatch):
    pid, _ = approved_household(client)
    assert client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "phone": "01712345678"}).status_code == 503
    monkeypatch.setenv("PHONE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "phone": "12345"}).status_code == 422
    r = client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "phone": "01712-345678"}).json()
    assert r["phone"] == "+88017•••••678"
    raw = store.get_call_schedule(pid)["phone_enc"]
    assert "1712345678" not in raw and phones.decrypt(raw) == "+8801712345678"
    client.delete(f"/patients/{pid}/calls/settings")
    assert store.get_call_schedule(pid)["phone_enc"] is None


# ---- a full call in the simulator -------------------------------------------------------------

def test_full_call_records_doses_with_source_call(client, store):
    pid, item_id = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)
    a = client.post(f"/patients/{pid}/calls/test").json()
    assert a["status"] == "ringing" and client.get(f"/patients/{pid}/calls/current").json()["id"] == a["id"]
    t = client.post(f"/calls/sim/{a['id']}/answer").json()
    assert t["play"] == ["greeting", "slot_morning"] and "১ চাপুন" in t["prompts"]["slot_morning"]["bn"]
    t = client.post(f"/calls/sim/{a['id']}/press", json={"digit": "1", "seq": t["seq"]}).json()
    again = client.post(f"/calls/sim/{a['id']}/press", json={"digit": "2", "seq": t["seq"] - 1}).json()  # stale: ignored
    assert again["answers"] == {"morning": "taken"}
    t = client.post(f"/calls/sim/{a['id']}/press", json={"digit": "2", "seq": t["seq"]}).json()
    assert t["play"] == ["emergency_ask"] and t["answers"] == {"morning": "taken", "night": "missed"}
    t = client.post(f"/calls/sim/{a['id']}/press", json={"digit": None, "seq": t["seq"]}).json()  # repeat once
    t = client.post(f"/calls/sim/{a['id']}/press", json={"digit": None, "seq": t["seq"]}).json()
    assert t["done"] and t["status"] == "completed" and t["play"] == ["closing"]
    doses = {(d["slot"], d["status"], d["source"]) for d in client.get(f"/patients/{pid}/doses").json()}
    assert doses == {("morning", "taken", "call"), ("night", "missed", "call")}
    assert client.post(f"/calls/sim/{a['id']}/press", json={"digit": "1", "seq": t["seq"]}).status_code == 409


def test_nine_sends_the_emergency_message_and_alert(client, monkeypatch):
    from app import main
    sent = []
    monkeypatch.setattr(main, "_notify_emergency", lambda pid, event="sathi_emergency": sent.append((pid, event)))
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)
    a = client.post(f"/patients/{pid}/calls/test").json()
    t = client.post(f"/calls/sim/{a['id']}/answer").json()
    t = client.post(f"/calls/sim/{a['id']}/press", json={"digit": "9", "seq": t["seq"]}).json()
    assert t["status"] == "emergency" and t["play"] == ["emergency", "closing"]
    assert sent == [(pid, "call_emergency")]
    assert client.get(f"/patients/{pid}/doses").json() == []  # nothing recorded


def test_other_households_cannot_drive_a_call(client):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)
    a = client.post(f"/patients/{pid}/calls/test").json()
    client.headers["X-Family-Key"] = "wrong"
    assert client.post(f"/calls/sim/{a['id']}/answer").status_code == 404


# ---- scheduling: quiet hours, retry, daily cap --------------------------------------------------

def test_run_due_quiet_hours_retry_and_cap(client, store, monkeypatch):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)  # 19:30
    prov = SimulatorProvider()
    assert service.run_due(store, prov, "x", at(19, 0))["placed"] == 0            # not yet
    assert service.run_due(store, prov, "x", at(21, 30))["skipped"] == {"quiet_hours": 1}
    assert service.run_due(store, prov, "x", at(7, 59, "2026-11-16"))["skipped"] == {"quiet_hours": 1}

    clock = {"now": at(19, 30)}
    monkeypatch.setattr("app.store.now", lambda: clock["now"].isoformat(timespec="seconds"))
    assert service.run_due(store, prov, "x", clock["now"])["placed"] == 1
    assert service.run_due(store, prov, "x", clock["now"])["placed"] == 0          # idempotent
    clock["now"] = at(19, 46)
    r = service.run_due(store, prov, "x", clock["now"])
    assert r["marked_no_answer"] == 1 and r["retried"] == 1                         # one retry after 15 min
    clock["now"] = at(20, 2)
    r = service.run_due(store, prov, "x", clock["now"])
    assert r["marked_no_answer"] == 1 and r["skipped"] == {"daily_cap": 1}
    statuses = [a["status"] for a in store.list_call_attempts(pid)]
    assert statuses == ["no_answer", "no_answer"]


def test_run_due_endpoint_needs_the_admin_token(client):
    assert client.post("/calls/run-due").status_code == 401
    assert client.post("/calls/run-due", headers=ADMIN).status_code == 200


def test_public_webhook_refuses_the_simulator_and_unknown_providers(client):
    assert client.post("/calls/webhook/simulator", data={"call_id": "sim-1"}).status_code == 404
    assert client.post("/calls/webhook/twilio", data={"CallSid": "x"}).status_code == 404


# ---- reviewer history, triage, export and delete ---------------------------------------------

def test_reviewer_history_and_calls_missed(client, store):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)
    for _ in range(3):
        a = client.post(f"/patients/{pid}/calls/test").json()
        client.post(f"/calls/sim/{a['id']}/decline")
    assert client.get(f"/patients/{pid}/calls").status_code == 401
    h = client.get(f"/patients/{pid}/calls", headers=TOKEN).json()
    assert h["answer_rate"]["k"] == 0 and h["answer_rate"]["n"] == 3 and len(h["attempts"]) == 3
    assert service.calls_missed(store, pid)
    from app.triage import household_risk
    p = store.get_patient(pid)
    r = household_risk(p, [], [], {}, calls_missed=True)
    assert {"code": "calls_missed", "points": 1, "value": True} in r["reasons"]


def test_export_masks_the_number_and_delete_removes_calls(client, store, monkeypatch):
    monkeypatch.setenv("PHONE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json={**CONSENT, "phone": "01812345678"})
    client.post(f"/patients/{pid}/calls/test")
    ex = client.get(f"/patients/{pid}/export").json()["check_in_calls"]
    assert ex["schedule"]["phone"] == "+88018•••••678" and len(ex["calls"]) == 1
    assert "01812345678" not in str(ex) and "1812345678" not in str(ex)
    assert client.request("DELETE", f"/patients/{pid}", json={"confirm": "DELETE"}).status_code == 204
    assert store.get_call_schedule(pid) is None and store.list_call_attempts(pid) == []


@pytest.mark.parametrize("raw,ok", [("01712345678", "+8801712345678"), ("+8801912345678", "+8801912345678"),
                                    ("8801512345678", "+8801512345678"), ("01212345678", None), ("0171234567", None)])
def test_bangladeshi_mobile_numbers_only(raw, ok):
    assert phones.normalise(raw) == ok


def test_call_time_window():
    assert service.valid_call_time("08:00") and service.valid_call_time("20:45")
    assert not service.valid_call_time("20:46") and not service.valid_call_time("07:59")
    assert service.quiet(at(21, 0)) and service.quiet(at(7, 59)) and not service.quiet(at(8, 0))
    assert service.DHAKA.utcoffset(None) == timedelta(hours=6)


def test_call_audio_speaks_digits_as_words_and_stays_safe():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("make_call_audio", Path(__file__).resolve().parents[1] / "scripts" / "make_call_audio.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.spoken("সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।") == "সকালের ওষুধ খেয়ে থাকলে এক চাপুন, না খেলে দুই চাপুন।"
    assert mod.spoken("এখনই ৯৯৯-এ ফোন করুন") == "এখনই নয় নয় নয় নম্বরে ফোন করুন"
    for texts in script.PROMPTS.values():
        said = mod.spoken(texts["bn"])
        assert not any(c in said for c in "০১২৩৪৫৬৭৮৯") and explain.is_safe(said)
