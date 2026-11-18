"""The daily WhatsApp check-in: simulator conversation, webhook (signature, matching, duplicates),
scheduling, safety of the fixed text. No network: the Cloud API is mocked."""
import hashlib
import hmac
import json
from datetime import datetime

import httpx
import pytest
from cryptography.fernet import Fernet

from app import explain
from app.whatsapp_checkin import cloud, flow, service
from tests.test_calls import CONSENT, approved_household, at
from tests.test_clinical import TOKEN

WA = {**CONSENT, "channel": "whatsapp"}


def test_fixed_text_is_safe_and_within_meta_limits():
    for text in flow.ALL_TEXTS:
        assert explain.is_safe(text), text
        for word in ("বন্ধ কর", "দ্বিগুণ", "বাদ দিন", "শুরু কর", "বাড়িয়ে", "কমিয়ে"):
            assert word not in text
    assert all(len(b) <= 25 for b in flow.TEMPLATE_BUTTONS)            # template quick replies
    assert all(len(t) <= 20 for _, t in flow.SLOT_BUTTONS)              # interactive reply titles
    assert len(flow.SLOT_BUTTONS) <= 3 and len(flow.TEMPLATE_BUTTONS) <= 3


def test_flow_branches():
    slots = ["night", "morning"]
    s = flow.reply("daily", slots, {}, flow.ALL_TAKEN)
    assert s.state == "done" and s.record == {"morning": "taken", "night": "taken"}
    s = flow.reply("daily", slots, {}, flow.SOME_MISSED)
    assert s.state == "slot:morning" and [b[0] for b in s.out[0].buttons] == ["morning:taken", "morning:missed", "morning:emergency"]
    s = flow.reply("slot:morning", slots, {}, "morning:missed")
    assert s.state == "slot:night" and s.record == {"morning": "missed"}
    s = flow.reply("slot:night", slots, {"morning": "missed"}, "night:taken")
    assert s.state == "done" and s.out[0].text == flow.CLOSING
    assert flow.reply("slot:night", slots, {}, "morning:taken").out == []   # stale tap: nothing changes
    for tap in (flow.EMERGENCY, "night:emergency"):
        assert flow.reply("slot:night", slots, {}, tap).emergency


def test_simulator_conversation_records_doses_with_source_whatsapp(client):
    pid, _ = approved_household(client)                  # Seclo: morning + night
    assert client.put(f"/patients/{pid}/calls/settings", json=WA).json()["channel"] == "whatsapp"
    c = client.post(f"/patients/{pid}/whatsapp/test").json()
    assert c["provider"] == "simulator" and c["status"] == "sent" and c["transcript"][0]["text"] == flow.DAILY
    c = client.post(f"/whatsapp/sim/{c['id']}/reply", json={"button": flow.SOME_MISSED}).json()
    assert c["state"] == "slot:morning"
    c = client.post(f"/whatsapp/sim/{c['id']}/reply", json={"button": "morning:taken"}).json()
    c = client.post(f"/whatsapp/sim/{c['id']}/reply", json={"button": "night:missed"}).json()
    assert c["status"] == "completed" and c["answers"] == {"morning": "taken", "night": "missed"}
    assert [m["text"] for m in c["transcript"] if m["from"] == "them"] == [flow.SOME_MISSED, flow.TAKEN, flow.MISSED]
    doses = {(d["slot"], d["status"], d["source"]) for d in client.get(f"/patients/{pid}/doses").json()}
    assert doses == {("morning", "taken", "whatsapp"), ("night", "missed", "whatsapp")}
    again = client.post(f"/whatsapp/sim/{c['id']}/reply", json={"button": flow.ALL_TAKEN}).json()
    assert again["status"] == "completed" and again["answers"] == c["answers"]   # finished: ignored


def test_emergency_button_and_typed_emergency_alert(client, monkeypatch):
    from app import main
    sent = []
    monkeypatch.setattr(main, "_notify_emergency", lambda pid, event="sathi_emergency": sent.append(event))
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=WA)
    c = client.post(f"/patients/{pid}/whatsapp/test").json()
    c = client.post(f"/whatsapp/sim/{c['id']}/reply", json={"button": flow.EMERGENCY}).json()
    assert c["status"] == "emergency" and c["transcript"][-2]["text"] == flow.EMERGENCY_TEXT
    c = client.post(f"/patients/{pid}/whatsapp/test").json()
    c = client.post(f"/whatsapp/sim/{c['id']}/text", json={"text": "বাবার বুকে ব্যথা হচ্ছে"}).json()
    assert c["status"] == "emergency" and sent == ["whatsapp_emergency", "whatsapp_emergency"]


def test_typed_text_is_not_interpreted_or_stored(client):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=WA)
    c = client.post(f"/patients/{pid}/whatsapp/test").json()
    c = client.post(f"/whatsapp/sim/{c['id']}/text", json={"text": "Can I stop Seclo? Rahima"}).json()
    assert c["status"] == "sent" and c["transcript"][-1]["text"] == flow.TAP_PLEASE
    assert "Rahima" not in json.dumps(c) and "Seclo" not in json.dumps(c["transcript"])


def test_whatsapp_needs_consent_and_its_own_channel(client):
    pid, _ = approved_household(client)
    assert client.post(f"/patients/{pid}/whatsapp/test").status_code == 409
    client.put(f"/patients/{pid}/calls/settings", json=CONSENT)           # call channel
    assert client.post(f"/patients/{pid}/whatsapp/test").status_code == 409


# ---- the real Cloud API path, mocked --------------------------------------------------------------

@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "106540352242922")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify-me")
    monkeypatch.setenv("PHONE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    # real messages respect quiet hours: test at midday in Dhaka whatever the machine's clock says
    monkeypatch.setattr("app.voice_calls.service.dhaka_now", lambda: at(12, 0))
    posted = []

    def fake_send(to, out, client=None):
        posted.append(cloud.payload(to, out))
        return f"wamid.{len(posted)}"

    monkeypatch.setattr(cloud, "send", fake_send)
    return posted


def _signed(client, body: dict, secret="secret"):
    raw = json.dumps(body).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return client.post("/whatsapp/webhook", content=raw, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})


def _tap(msg_id, context_id, payload):
    return {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {"messages": [
        {"from": "8801712345678", "id": msg_id, "context": {"id": context_id}, "type": "button",
         "button": {"payload": payload, "text": payload}}]}}]}]}


def test_payloads_follow_the_documented_format():
    t = cloud.payload("+8801712345678", flow.start())
    assert t["type"] == "template" and t["template"] == {"name": flow.TEMPLATE_NAME, "language": {"code": "bn"}}
    i = cloud.payload("+8801712345678", flow.Out("q", [("morning:taken", "খেয়েছি")]))
    assert i["interactive"]["action"]["buttons"][0] == {"type": "reply", "reply": {"id": "morning:taken", "title": "খেয়েছি"}}
    assert cloud.payload("x", flow.Out("hi"))["text"] == {"body": "hi"}
    assert all(p["messaging_product"] == "whatsapp" for p in (t, i))


def test_send_reads_the_message_id(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")

    def handler(req):
        assert str(req.url) == "https://graph.facebook.com/v27.0/123/messages" and req.headers["authorization"] == "Bearer t"
        return httpx.Response(200, json={"messaging_product": "whatsapp", "messages": [{"id": "wamid.X"}]})

    assert cloud.send("+880", flow.Out("hi"), client=httpx.Client(transport=httpx.MockTransport(handler))) == "wamid.X"


def test_webhook_signature_subscription_matching_and_duplicates(client, store, live):
    pid, _ = approved_household(client)
    assert client.put(f"/patients/{pid}/calls/settings", json={**WA, "phone": "01712345678"}).json()["whatsapp_live"]
    c = client.post(f"/patients/{pid}/whatsapp/test").json()
    assert c["provider"] == "whatsapp" and live[0]["to"] == "+8801712345678" and live[0]["type"] == "template"

    v = client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "1158201444"})
    assert v.status_code == 200 and v.text == "1158201444"
    assert client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"}).status_code == 403

    body = _tap("wamid.in1", "wamid.1", flow.ALL_TAKEN)
    assert _signed(client, body, secret="wrong").status_code == 403
    assert _signed(client, body).json() == {"handled": 1}
    assert _signed(client, body).json() == {"handled": 0}               # Meta re-delivered: ignored
    got = store.get_checkin(c["id"])
    assert got["status"] == "completed" and got["answers"] == {"morning": "taken", "night": "taken"}
    assert _signed(client, _tap("wamid.in2", "wamid.unknown", flow.ALL_TAKEN)).json() == {"handled": 0}


def test_unlinked_typed_emergency_still_gets_the_999_reply(client, live):
    body = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "8801812345678", "id": "wamid.in9", "type": "text", "text": {"body": "chest pain help"}}]}}]}]}
    assert _signed(client, body).json() == {"handled": 1}
    assert live[-1]["text"] == {"body": flow.EMERGENCY_TEXT} and live[-1]["to"] == "8801812345678"


def test_run_due_sends_once_a_day_and_marks_no_reply(client, store, monkeypatch):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=WA)   # 19:30, simulator
    clock = {"now": at(19, 30)}
    monkeypatch.setattr("app.store.now", lambda: clock["now"].isoformat(timespec="seconds"))
    assert service.run_due(store, at(19, 0))["sent"] == 0
    assert service.run_due(store, at(21, 30))["sent"] == 0      # quiet hours
    assert service.run_due(store, clock["now"])["sent"] == 1
    assert service.run_due(store, clock["now"])["sent"] == 0    # one a day
    clock["now"] = datetime.fromisoformat("2026-11-16T08:15:00+06:00")
    r = service.run_due(store, clock["now"])
    assert r["no_reply"] == 1
    from app.voice_calls import service as calls
    assert calls.history(store, pid)["attempts"][-1]["status"] == "no_answer"


def test_export_and_delete_cover_checkins(client, store):
    pid, _ = approved_household(client)
    client.put(f"/patients/{pid}/calls/settings", json=WA)
    client.post(f"/patients/{pid}/whatsapp/test")
    ex = client.get(f"/patients/{pid}/export").json()["check_in_calls"]
    assert ex["schedule"]["channel"] == "whatsapp" and len(ex["whatsapp_checkins"]) == 1
    assert client.get(f"/patients/{pid}/calls", headers=TOKEN).json()["attempts"][0]["provider"] == "whatsapp-simulator"
    assert client.request("DELETE", f"/patients/{pid}", json={"confirm": "DELETE"}).status_code == 204
    assert store.list_checkins(pid) == []
