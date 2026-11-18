"""Running the WhatsApp check-in: start one, handle taps and typed text, schedule the daily message.

Shares consent, time, quiet hours and the stop switch with the check-in call (call_schedules, channel
"whatsapp"). Real messages go through the WhatsApp Cloud API when its keys are set; otherwise the
browser simulator plays the same conversation. Typed text never reaches a model: emergency words get
the emergency reply (guard.is_emergency), anything else a fixed "please tap a button".
"""
from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import datetime, timedelta

from ..guard import is_emergency
from ..store import Store
from ..voice_calls import phone as phones
from ..voice_calls import service as calls
from . import cloud, flow

NO_REPLY_AFTER = timedelta(hours=12)
OPEN = ("sent", "answering")


def real() -> bool:
    return cloud.configured()


def _send(store: Store, checkin: dict, outs: list[flow.Out], number: str | None) -> list[dict]:
    """Sends (or, in the simulator, only records) each message; links every wamid to the check-in."""
    sent = []
    for out in outs:
        wamid = cloud.send(number, out) if checkin["provider"] == "whatsapp" else f"sim-{secrets.token_hex(8)}"
        store.link_wa_message(wamid, checkin["id"])
        sent.append({"from": "us", "id": wamid, "text": out.text, "buttons": [list(b) for b in out.buttons]})
    return sent


def _number(store: Store, pid: int) -> str | None:
    sch = store.get_call_schedule(pid)
    return phones.decrypt(sch["phone_enc"]) if sch else None


def start(store: Store, pid: int, at: datetime) -> dict:
    provider = "whatsapp" if real() else "simulator"
    number = _number(store, pid) if provider == "whatsapp" else None
    if provider == "whatsapp" and not number:
        raise ValueError("no WhatsApp number on file")
    slots = calls.approved_slots(store, pid)
    c = store.add_checkin(pid, at.astimezone(calls.DHAKA).date().isoformat(), provider, slots)
    try:
        transcript = _send(store, c, [flow.start()], number)
    except cloud.SendFailed:
        return store.update_checkin(c["id"], status="failed")
    return store.update_checkin(c["id"], status="sent", transcript=transcript)


def reply(store: Store, checkin: dict, tapped: str, on_emergency: Callable[[int], None]) -> dict:
    """A tapped button (template label or interactive id). Stale taps change nothing."""
    if checkin["status"] not in OPEN:
        return checkin
    step = flow.reply(checkin["state"], checkin["slots"], checkin["answers"], tapped)
    if not step.out:
        return checkin
    # show the label that was tapped (an interactive reply arrives as our id, e.g. "morning:taken")
    titles = {i: t for m in checkin["transcript"] if m["from"] == "us" for i, t in m.get("buttons", [])}
    return _apply(store, checkin, step, {"from": "them", "text": titles.get(tapped, tapped)}, on_emergency)


def typed(store: Store, checkin: dict, text: str, on_emergency: Callable[[int], None]) -> dict:
    """Typed text is never interpreted beyond the emergency word list."""
    if checkin["status"] not in OPEN:
        return checkin
    them = {"from": "them", "text": "…"}  # the family's own words are not stored
    if is_emergency(text):
        step = flow.Step([flow.Out(flow.EMERGENCY_TEXT), flow.Out(flow.CLOSING)], "emergency", emergency=True)
        return _apply(store, checkin, step, them, on_emergency)
    number = _number(store, checkin["patient_id"]) if checkin["provider"] == "whatsapp" else None
    sent = _send(store, checkin, [flow.Out(flow.TAP_PLEASE)], number)
    return store.update_checkin(checkin["id"], transcript=[*checkin["transcript"], them, *sent])


def _apply(store: Store, checkin: dict, step: flow.Step, them: dict, on_emergency: Callable[[int], None]) -> dict:
    answers = {**checkin["answers"], **step.record}
    if step.record:
        calls._record(store, checkin["patient_id"], datetime.fromisoformat(checkin["day"]).date(), step.record,
                      source="whatsapp")
    if step.emergency:
        on_emergency(checkin["patient_id"])
    status = "emergency" if step.emergency else "completed" if step.state == "done" else "answering"
    number = _number(store, checkin["patient_id"]) if checkin["provider"] == "whatsapp" else None
    try:
        sent = _send(store, checkin, step.out, number)
    except cloud.SendFailed:
        sent = []
    return store.update_checkin(checkin["id"], status=status, state=step.state, answers=answers,
                                transcript=[*checkin["transcript"], them, *sent])


def run_due(store: Store, at: datetime) -> dict:
    """Called by the same cron as the calls. One daily message per household; no retries (one paid
    template a day); unanswered after NO_REPLY_AFTER counts as no reply."""
    at = at.astimezone(calls.DHAKA)
    out = {"sent": 0, "no_reply": 0, "skipped": {}}
    for sch in store.active_call_schedules():
        if sch.get("channel") != "whatsapp":
            continue
        pid = sch["patient_id"]
        for c in store.list_checkins(pid):
            if c["status"] in OPEN and at - datetime.fromisoformat(c["created_at"]).astimezone(calls.DHAKA) >= NO_REPLY_AFTER:
                store.update_checkin(c["id"], status="no_reply")
                out["no_reply"] += 1
        if calls.quiet(at) or at.time() < datetime.strptime(sch["local_time"], "%H:%M").time():
            continue
        if store.list_checkins(pid, day=at.date().isoformat()) or not calls.approved_slots(store, pid):
            continue
        try:
            start(store, pid, at)
            out["sent"] += 1
        except ValueError:
            out["skipped"]["no_number"] = out["skipped"].get("no_number", 0) + 1
    return out


def handle_webhook(store: Store, body: dict, on_emergency: Callable[[int], None]) -> int:
    """Processes taps and texts from a verified webhook body. Returns how many messages were handled.
    Replies are matched by the message they answer (context.id), never by phone number alone."""
    handled = 0
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []) or []:
                if not store.first_time_inbound(msg.get("id", "")):
                    continue
                checkin = store.checkin_for_message((msg.get("context") or {}).get("id", ""))
                if checkin is None:
                    # not an answer to one of our messages, so no household is known; an emergency
                    # still gets the fixed 999 reply, straight back to whoever wrote
                    text = (msg.get("text") or {}).get("body", "") if msg.get("type") == "text" else ""
                    sender = msg.get("from") or msg.get("from_user_id")
                    if text and is_emergency(text) and sender and real():
                        try:
                            cloud.send(sender, flow.Out(flow.EMERGENCY_TEXT))
                        except cloud.SendFailed:
                            pass
                        handled += 1
                    continue
                if msg.get("type") == "button":
                    reply(store, checkin, (msg.get("button") or {}).get("payload", ""), on_emergency)
                elif msg.get("type") == "interactive":
                    reply(store, checkin, ((msg.get("interactive") or {}).get("button_reply") or {}).get("id", ""),
                          on_emergency)
                elif msg.get("type") == "text":
                    typed(store, checkin, (msg.get("text") or {}).get("body", ""), on_emergency)
                handled += 1
    return handled
