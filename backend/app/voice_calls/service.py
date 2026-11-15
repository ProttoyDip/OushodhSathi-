"""Call scheduling and the call flow, shared by the simulator page and real provider webhooks.

Rules (Prompt 13C): calls only with recorded consent; never 21:00-08:00 Bangladesh time; at most
MAX_ATTEMPTS_PER_DAY per household (the first call plus one retry RETRY_AFTER later if unanswered);
answers become dose_events with source="call" for the pharmacist-approved slots only; 9 sends the
fixed emergency message and an alert. No AI anywhere, and nothing about a call reaches a model.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone

from ..models import MedicineItem
from ..refills import counts
from ..store import Store
from . import phone as phones
from . import script
from .base import CallProvider

# Bangladesh Standard Time is UTC+6 with no daylight saving (fixed offset: Windows has no tz database)
DHAKA = timezone(timedelta(hours=6), "Asia/Dhaka")
QUIET_FROM, QUIET_UNTIL = time(21, 0), time(8, 0)
RETRY_AFTER = timedelta(minutes=15)
MAX_ATTEMPTS_PER_DAY = 2
ANSWERED = ("in_progress", "completed", "emergency")


def dhaka_now() -> datetime:
    return datetime.now(DHAKA)


def quiet(at: datetime) -> bool:
    t = at.astimezone(DHAKA).time()
    return t >= QUIET_FROM or t < QUIET_UNTIL


def valid_call_time(hhmm: str) -> bool:
    try:
        t = time.fromisoformat(hhmm)
    except ValueError:
        return False
    return QUIET_UNTIL <= t < time(20, 46)  # the retry 15 minutes later must still end before 21:00


def _tickable(it: MedicineItem) -> bool:
    return counts(it) and bool(it.schedule) and it.schedule_approved_at is not None


def approved_slots(store: Store, pid: int) -> list[str]:
    items = [it for it in store.list_items(pid, confirmed_only=True) if _tickable(it)]
    return [s for s in script.SLOTS if any(s in it.schedule for it in items)]


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def place(store: Store, provider: CallProvider, pid: int, at: datetime, callback_url: str,
          phone_e164: str | None, attempt_no: int) -> dict:
    steps = script.steps_for(approved_slots(store, pid))
    day = at.astimezone(DHAKA).date().isoformat()
    aid = store.add_call_attempt(pid, day, at.isoformat(timespec="minutes"), attempt_no, provider.name, steps)
    try:
        call_id = provider.place_call(aid, phone_e164, callback_url)
    except Exception:  # noqa: BLE001 - a provider error is a failed attempt, never a crash of the cron
        store.update_call_attempt(aid, status="failed")
        return store.get_call_attempt(aid)  # type: ignore[return-value]
    store.update_call_attempt(aid, provider_call_id=call_id)
    return store.get_call_attempt(aid)  # type: ignore[return-value]


def run_due(store: Store, provider: CallProvider, callback_url: str, at: datetime | None = None) -> dict:
    """Called by the cron (POST /calls/run-due). Idempotent: running it twice places nothing twice."""
    at = (at or dhaka_now()).astimezone(DHAKA)
    out = {"placed": 0, "retried": 0, "marked_no_answer": 0, "skipped": {}}

    def skip(reason: str) -> None:
        out["skipped"][reason] = out["skipped"].get(reason, 0) + 1

    for sch in store.active_call_schedules():
        pid = sch["patient_id"]
        today = store.list_call_attempts(pid, day=at.date().isoformat())
        for a in today:  # a call still ringing after RETRY_AFTER was not answered
            if a["status"] == "ringing" and at - _parse(a["created_at"]).astimezone(DHAKA) >= RETRY_AFTER:
                store.update_call_attempt(a["id"], status="no_answer")
                a["status"] = "no_answer"
                out["marked_no_answer"] += 1
        if quiet(at):
            skip("quiet_hours")
            continue
        if at.time() < time.fromisoformat(sch["local_time"]):
            continue
        if any(a["status"] in (*ANSWERED, "ringing") for a in today):
            continue
        if len(today) >= MAX_ATTEMPTS_PER_DAY:
            skip("daily_cap")
            continue
        if today and at - _parse(today[-1]["updated_at"]).astimezone(DHAKA) < RETRY_AFTER:
            continue
        if not approved_slots(store, pid):
            skip("no_approved_times")
            continue
        number = phones.decrypt(sch["phone_enc"]) if provider.needs_phone else None
        if provider.needs_phone and not number:
            skip("no_phone")
            continue
        place(store, provider, pid, at, callback_url, number, len(today) + 1)
        out["retried" if today else "placed"] += 1
    return out


def _turn(attempt: dict, turn: script.Turn) -> dict:
    return {"attempt_id": attempt["id"], "seq": attempt["seq"], "status": attempt["status"],
            "play": turn.play, "prompts": {p: script.PROMPTS[p] for p in turn.play},
            "expects_input": turn.expects_input, "done": turn.done, "answers": attempt["answers"]}


def answer(store: Store, attempt: dict) -> dict:
    """The phone is picked up: greeting + the first question."""
    if attempt["status"] != "ringing":
        raise ValueError("This call is not ringing")
    store.update_call_attempt(attempt["id"], status="in_progress", seq=1)
    a = store.get_call_attempt(attempt["id"])
    return _turn(a, script.start(a["steps"]))  # type: ignore[arg-type]


def press(store: Store, attempt: dict, digit: str | None, seq: int,
          on_emergency: Callable[[int], None]) -> dict:
    """One key (or a timeout: digit None). `seq` makes it idempotent: a repeated delivery of the same
    callback returns the current state without recording anything twice."""
    if attempt["status"] != "in_progress":
        raise ValueError("This call is not in progress")
    steps = attempt["steps"]
    if seq != attempt["seq"]:  # duplicate or stale delivery
        idx = min(attempt["step_index"], len(steps) - 1)
        return _turn(attempt, script.Turn(play=[steps[idx]], expects_input=True))
    idx, repeated, turn = script.advance(steps, attempt["step_index"], digit, bool(attempt["repeated"]))
    answers = {**attempt["answers"], **turn.record}
    status = "emergency" if turn.emergency else "completed" if turn.done else "in_progress"
    store.update_call_attempt(attempt["id"], step_index=idx, repeated=int(repeated), seq=attempt["seq"] + 1,
                              answers=answers, status=status)
    if turn.record:
        _record(store, attempt["patient_id"], date.fromisoformat(attempt["day"]), turn.record)
    if turn.emergency:
        on_emergency(attempt["patient_id"])
    return _turn(store.get_call_attempt(attempt["id"]), turn)  # type: ignore[arg-type]


def _record(store: Store, pid: int, day: date, record: dict[str, str]) -> None:
    """Writes the answer for every pharmacist-approved medicine in that slot; nothing else."""
    for it in store.list_items(pid, confirmed_only=True):
        if not _tickable(it):
            continue
        for slot, status in record.items():
            if slot in it.schedule:
                store.record_dose(pid, it.id, day.isoformat(), slot, status, source="call")


def history(store: Store, pid: int, days: int = 14) -> dict:
    """Reviewer view: recent calls and how many were answered (answered = picked up)."""
    from ..stats import proportion

    since = (dhaka_now().date() - timedelta(days=days - 1)).isoformat()
    attempts = store.list_call_attempts(pid, since_day=since)
    finished = [a for a in attempts if a["status"] != "ringing"]
    picked = sum(a["status"] in ANSWERED for a in finished)
    sch = store.get_call_schedule(pid)
    return {"active": bool(sch and sch["active"]), "local_time": sch["local_time"] if sch else None,
            "attempts": [{k: a[k] for k in ("day", "attempt_no", "status", "provider", "answers", "created_at")}
                         for a in reversed(attempts)],
            "answer_rate": proportion("answered", picked, len(finished)) if finished else None}


def calls_missed(store: Store, pid: int) -> bool:
    """Triage: 3 of the last 5 finished calls were not answered."""
    last = [a for a in store.list_call_attempts(pid) if a["status"] != "ringing"][-5:]
    return sum(a["status"] in ("no_answer", "failed") for a in last) >= 3
