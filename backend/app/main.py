"""OushodhSathi API. OpenAPI docs at /docs."""
from __future__ import annotations

import hmac
import logging
import os
import threading
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError, model_validator

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from . import prompts  # noqa: E402
from .agent import read_shelf, resolve_brand  # noqa: E402
from .demo import DEMO_ITEMS, DEMO_LABEL  # noqa: E402
from .explain import explain_flag  # noqa: E402
from .ratelimit import limit_new_patient, limit_sathi, limit_scan, limit_writes  # noqa: E402
from . import llm_router  # noqa: E402
from .llm_router import NoProviderAvailable, Router, _env, configured_providers, provider_names  # noqa: E402
from .models import (  # noqa: E402
    ClinicalPatch, MedicineItem, MedicineItemIn, MedicineItemPatch, Patient, PatientIn, PatientPatch, ReviewIn,
    RuleItem, StoredFlag,
)
from .next_step import StepContext, next_step  # noqa: E402
from .refills import counts, refills_due  # noqa: E402
from .rules import run_rules  # noqa: E402
from . import clinical, sathi  # noqa: E402
from .stats import pilot_stats, proportion  # noqa: E402
from .store import Store, now  # noqa: E402
from .tables import load_rule_tables  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("oushodh.api")

app = FastAPI(
    title="OushodhSathi API",
    description="Medicine-safety review for elderly Bangladeshis. AI for perception, rules and humans for judgement.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in (os.getenv("CORS_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")],
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PHOTOS = 12
MAX_PHOTO_BYTES = 12 * 1024 * 1024


@lru_cache(maxsize=1)
def get_store() -> Store:
    store = Store()
    _load_model_preferences(store)  # the user's chosen AI models survive restarts
    return store


def demo_mode() -> bool:
    return _env("DEMO_MODE").lower() in ("1", "true", "yes")


def reviewer_token() -> str | None:
    token = _env("REVIEWER_TOKEN")
    if token:
        return token
    return "demo-reviewer" if demo_mode() else None


def _same(given: str | None, expected: str | None) -> bool:
    return bool(given and expected) and hmac.compare_digest(given.encode(), expected.encode())  # type: ignore[union-attr]


def require_reviewer(x_reviewer_token: str | None = Header(default=None)) -> None:
    expected = reviewer_token()
    if not expected:
        raise HTTPException(503, "REVIEWER_TOKEN is not configured on the server")
    if not _same(x_reviewer_token, expected):
        raise HTTPException(401, "Reviewer token required")


def family_access(
    pid: int,
    x_family_key: str | None = Header(default=None),
    x_reviewer_token: str | None = Header(default=None),
    store: Store = Depends(get_store),
) -> None:
    """A household opens with its private family link (X-Family-Key) or a reviewer token.
    The invented demo household stays open. Anything else is 'not found', so ids cannot be probed."""
    p = store.get_patient(pid)
    if p is None or not (p.is_demo or _same(x_reviewer_token, reviewer_token())
                         or _same(x_family_key, store.family_key(pid))):
        raise HTTPException(404, "Patient not found")


def item_access(
    item_id: int,
    x_family_key: str | None = Header(default=None),
    x_reviewer_token: str | None = Header(default=None),
    store: Store = Depends(get_store),
) -> None:
    item = store.get_item(item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    try:
        family_access(item.patient_id, x_family_key, x_reviewer_token, store)
    except HTTPException:
        raise HTTPException(404, "Item not found") from None


def _patient_or_404(store: Store, pid: int) -> Patient:
    p = store.get_patient(pid)
    if p is None:
        raise HTTPException(404, "Patient not found")
    return p


def _item_or_404(store: Store, item_id: int) -> MedicineItem:
    it = store.get_item(item_id)
    if it is None:
        raise HTTPException(404, "Item not found")
    return it


def _with_items(store: Store, flags: list[StoredFlag]) -> list[dict]:
    cache: dict[int, MedicineItem | None] = {}
    out = []
    for f in flags:
        items = []
        for i in f.item_ids:
            if i not in cache:
                cache[i] = store.get_item(i)
            if cache[i] is not None:
                items.append(cache[i].model_dump())
        out.append({**f.model_dump(), "items": items})
    return out


# ---- health ---------------------------------------------------------------------------

@app.get("/health")
def health(store: Store = Depends(get_store)) -> dict:
    """Configured providers are reported by NAME only, never keys."""
    ollama_up = False
    if base := _env("OLLAMA_BASE_URL"):
        try:
            ollama_up = httpx.get(base.rstrip("/").removesuffix("/v1") + "/api/tags", timeout=1.5).status_code == 200
        except httpx.HTTPError:
            ollama_up = False
    tests_dir = Path(__file__).resolve().parent.parent / "tests"
    test_count = sum(
        line.lstrip().startswith("def test_")
        for f in tests_dir.glob("test_*.py") for line in f.read_text(encoding="utf-8").splitlines()
    )
    return {
        "status": "ok",
        "demo_mode": demo_mode(),
        "providers": {t: provider_names(t) for t in ("vision", "text", "explain_bn")},
        "models": {
            "vision": _env("OPENROUTER_VISION_MODEL") or "auto (free OpenRouter image model)",
            "text": _env("OPENROUTER_TEXT_MODEL") or "auto (free OpenRouter text model)",
            "explain_bn_local": _env("OLLAMA_MODEL") or None,
        },
        "ollama_reachable": ollama_up,
        "web_lookup": {"tavily": bool(_env("TAVILY_API_KEY")), "perplexity": bool(_env("PERPLEXITY_API_KEY"))},
        "prompts": {name: prompts.version(name) for name in prompts.ACTIVE},
        "reviewer_login": "configured" if _env("REVIEWER_TOKEN") else ("demo token" if demo_mode() else "missing"),
        "test_count": test_count,
        "patients": len(store.list_patients()),
    }


# ---- patients and items ---------------------------------------------------------------

@app.get("/patients", dependencies=[Depends(require_reviewer)])
def list_patients(store: Store = Depends(get_store)) -> list[dict]:
    """Reviewer only. Includes each household's family key so a lost link can be re-shared."""
    return [{**p.model_dump(mode="json"), "family_key": store.family_key(p.id)} for p in store.list_patients()]


@app.post("/patients", status_code=201, dependencies=[Depends(limit_new_patient)])
def create_patient(body: PatientIn, store: Store = Depends(get_store)) -> dict:
    """Creates a household. The response carries its private family key: keep it, it opens the household."""
    if body.is_demo:
        raise HTTPException(422, "Demo households are created by the seed script only")
    p = store.create_patient(body)
    return {**p.model_dump(mode="json"), "family_key": store.family_key(p.id)}


@app.get("/patients/{pid}", dependencies=[Depends(family_access)])
def get_patient(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    return {**p.model_dump(), "demo_label": DEMO_LABEL if p.is_demo else None}


@app.get("/patients/{pid}/items", response_model=list[MedicineItem], dependencies=[Depends(family_access)])
def list_items(pid: int, store: Store = Depends(get_store)):
    _patient_or_404(store, pid)
    return store.list_items(pid)


@app.post("/patients/{pid}/items", response_model=MedicineItem, status_code=201,
          dependencies=[Depends(family_access), Depends(limit_writes)])
def add_item(pid: int, body: MedicineItemIn, confirmed: bool = False, store: Store = Depends(get_store)):
    _patient_or_404(store, pid)
    match = resolve_brand(body.brand, body.strength, store)
    item = store.add_item(pid, body, **match, confirmed=False)
    if confirmed:
        item = _confirm_allowed(store, item)
    return item


def _confirm_allowed(store: Store, item: MedicineItem) -> MedicineItem:
    """A human confirms an item. Unknown brands can be confirmed (they are then simply
    not checked by the rules) but stay marked needs_review in every view."""
    return store.update_item(item.id, confirmed=True)  # type: ignore[return-value]


@app.patch("/items/{item_id}", response_model=MedicineItem,
           dependencies=[Depends(item_access), Depends(limit_writes)])
def patch_item(item_id: int, body: MedicineItemPatch, store: Store = Depends(get_store)):
    item = _item_or_404(store, item_id)
    fields = body.model_dump(exclude_unset=True)
    if fields.get("set_aside") and not (item.stopped or is_expired(item)):
        # the family puts away only expired strips or what the reviewer stopped; nothing else
        raise HTTPException(422, "Only expired medicines or ones the pharmacist stopped can be set aside")
    if any(k in fields and fields[k] != getattr(item, k) for k in ("schedule", "per_dose")):
        fields.update(schedule_approved_by=None, schedule_approved_at=None)
    if "brand" in fields or "strength" in fields:
        brand = fields.get("brand", item.brand)
        strength = fields.get("strength", item.strength)
        fields.update(resolve_brand(brand, strength, store))
        # a human typed or corrected it: it is no longer a low-confidence machine reading
        fields["confidence"] = 1.0
        fields["source"] = item.source if "brand" not in fields else "manual"
    return store.update_item(item_id, **fields)


@app.delete("/items/{item_id}", status_code=204, dependencies=[Depends(item_access), Depends(limit_writes)])
def delete_item(item_id: int, store: Store = Depends(get_store)) -> None:
    _item_or_404(store, item_id)
    store.delete_item(item_id)


# ---- rules check ----------------------------------------------------------------------

def _notify_red_flags(pid: int, new_red: list[StoredFlag]) -> None:
    """n8n doctor_alert webhook: ids and codes only, no patient names or medicine details."""
    url = _env("N8N_ALERT_WEBHOOK")
    if not url or not new_red:
        return

    def send() -> None:
        try:
            httpx.post(url, timeout=5, json={
                "patient_id": pid,
                "flags": [{"id": f.id, "code": f.code, "severity": f.severity, "routed_to": f.routed_to}
                          for f in new_red],
            })
        except httpx.HTTPError as e:
            log.warning("n8n alert failed: %s", type(e).__name__)

    threading.Thread(target=send, daemon=True).start()


@app.post("/patients/{pid}/check", dependencies=[Depends(family_access), Depends(limit_writes)])
def run_check(pid: int, store: Store = Depends(get_store)) -> dict:
    """Runs the deterministic rules on CONFIRMED items. New flags start as pending_review."""
    patient = _patient_or_404(store, pid)
    before = {f.key for f in store.list_flags(pid, active_only=False)}
    confirmed = store.list_items(pid, confirmed_only=True)
    rule_items = [RuleItem(**it.model_dump(include=set(RuleItem.model_fields))) for it in confirmed]
    flags = run_rules(rule_items, patient.age, load_rule_tables(), date.today())
    stored = store.sync_flags(pid, flags)
    store.mark_checked(pid)
    new = [f for f in stored if f.key not in before]
    _notify_red_flags(pid, [f for f in new if f.severity == "red"])
    return {
        "checked_items": len(confirmed),
        "unchecked_items": sum(1 for it in confirmed if not it.generic),
        "flags_total": len(stored),
        "flags_new": len(new),
        "review_state": _review_state(store, pid),
    }


def _review_state(store: Store, pid: int) -> str:
    patient = store.get_patient(pid)
    if patient is None or patient.last_checked_at is None:
        return "not_checked"
    return "in_review" if store.list_flags(pid, statuses=("pending_review",)) else "reviewed"


@app.get("/patients/{pid}/status", dependencies=[Depends(family_access)])
def family_status(pid: int, store: Store = Depends(get_store)) -> dict:
    """Family-safe status: says whether a review is in progress, never what is pending."""
    p = _patient_or_404(store, pid)
    return {
        "review_state": _review_state(store, pid),
        "last_checked_at": p.last_checked_at,
        "confirmed_flags": len(store.list_flags(pid, statuses=("confirmed",))),
        "items_confirmed": len(store.list_items(pid, confirmed_only=True)),
    }


# ---- flags and review -----------------------------------------------------------------

@app.get("/patients/{pid}/flags", dependencies=[Depends(family_access)])
def list_flags(
    pid: int,
    view: Literal["family", "reviewer"] = Query("family"),
    x_reviewer_token: str | None = Header(default=None),
    store: Store = Depends(get_store),
) -> list[dict]:
    """view=family returns ONLY confirmed flags (AGENTS.md rule 2). view=reviewer needs the token."""
    _patient_or_404(store, pid)
    if view == "reviewer":
        require_reviewer(x_reviewer_token)
        return _with_items(store, store.list_flags(pid))
    flags = store.list_flags(pid, statuses=("confirmed",))
    assert all(f.status == "confirmed" for f in flags)
    return _with_items(store, flags)


@app.get("/flags", dependencies=[Depends(require_reviewer)])
def review_queue(
    status: Literal["pending_review", "confirmed", "dismissed", "all"] = "pending_review",
    store: Store = Depends(get_store),
) -> dict:
    """Reviewer queue across patients: red first, then longest waiting."""
    flags = store.list_flags(statuses=None if status == "all" else (status,))
    patients = {p.id: p for p in store.list_patients()}
    rows = []
    for f in _with_items(store, flags):
        p = patients.get(f["patient_id"])
        rows.append({**f, "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age,
                                      "is_demo": p.is_demo} if p else None})
    rows.sort(key=lambda r: (0 if r["severity"] == "red" else 1, r["created_at"]))
    pending = store.list_flags(statuses=("pending_review",))
    return {
        "flags": rows,
        "counts": {
            "pending": len(pending),
            "red": sum(f.severity == "red" for f in pending),
            "amber": sum(f.severity == "amber" for f in pending),
            "doctor": sum(f.routed_to == "doctor" for f in pending),
            "pharmacist": sum(f.routed_to == "pharmacist" for f in pending),
        },
    }


@app.post("/flags/{flag_id}/review", dependencies=[Depends(require_reviewer)])
def review_flag(flag_id: int, body: ReviewIn, store: Store = Depends(get_store)) -> dict:
    flag = store.get_flag(flag_id)
    if flag is None:
        raise HTTPException(404, "Flag not found")
    note = (body.note or "").strip() or None
    if body.status == "dismissed" and not note:
        raise HTTPException(422, "A short note is required to dismiss a flag")
    body = body.model_copy(update={"note": note})
    explanation = None
    if body.status == "confirmed":
        items = [it for i in flag.item_ids if (it := store.get_item(i))]
        patient = store.get_patient(flag.patient_id)
        confirmed_flag = flag.model_copy(update={"status": "confirmed"})
        explanation, how = explain_flag(
            confirmed_flag, items, note, Router(store=store),
            redact=[patient.name, patient.name_bn or ""] if patient else [],
        )
        log.info("flag %s explanation via %s", flag_id, how)
    opened = _parse_ts(flag.opened_at) if flag.opened_at else None
    seconds = (datetime.now(timezone.utc) - opened).total_seconds() if opened else None
    updated = store.review_flag(flag_id, body, explanation, seconds=seconds)
    return _with_items(store, [updated])[0]


@app.post("/flags/{flag_id}/undo", dependencies=[Depends(require_reviewer)])
def undo_review(flag_id: int, reviewer: str = Query(...), store: Store = Depends(get_store)) -> dict:
    flag = store.get_flag(flag_id)
    if flag is None:
        raise HTTPException(404, "Flag not found")
    return _with_items(store, [store.undo_review(flag_id, reviewer)])[0]


@app.get("/patients/{pid}/reviews", dependencies=[Depends(require_reviewer)])
def audit_trail(pid: int, store: Store = Depends(get_store)) -> list[dict]:
    _patient_or_404(store, pid)
    return store.list_reviews(pid)


# ---- passport and report --------------------------------------------------------------

SLOTS = ("morning", "noon", "night")


@app.get("/patients/{pid}/passport", dependencies=[Depends(family_access)])
def passport(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    items = [it for it in store.list_items(pid, confirmed_only=True) if counts(it)]

    def entry(it: MedicineItem) -> dict:
        return {"id": it.id, "generic": it.generic, "brand": it.brand, "strength": it.strength,
                "prescriber": it.prescriber, "needs_review": it.needs_review, "per_dose": it.per_dose,
                "purpose": it.purpose, "purpose_bn": it.purpose_bn, "schedule": it.schedule,
                "schedule_approved": it.schedule_approved_at is not None}

    groups = {slot: [entry(it) for it in items if slot in it.schedule] for slot in SLOTS}
    groups["as_needed"] = [entry(it) for it in items if not it.schedule]
    notes = [
        {"code": f.code, "severity": f.severity, "brands": [it["brand"] for it in f_items],
         "note": f.note, "explanation_bn": f.explanation_bn, "reviewer": f.reviewer,
         "reviewed_at": f.reviewed_at}
        for f, f_items in ((f, _with_items(store, [f])[0]["items"]) for f in store.list_flags(pid, statuses=("confirmed",)))
    ]
    prescribers: dict[str, list[str]] = {}
    for it in items:
        prescribers.setdefault(it.prescriber or "", []).append(it.brand)
    decided = [f for f in store.list_flags(pid, statuses=("confirmed", "dismissed"), active_only=False) if f.reviewed_at]
    last = max(decided, key=lambda f: _parse_ts(f.reviewed_at)) if decided else None
    return {
        "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age,
                    "conditions": p.conditions, "district": p.district},
        "groups": groups,
        "confirmed_notes": notes,
        "medicine_count": len(items),
        "allergies": p.allergies,
        "allergies_confirmed_by": p.allergies_confirmed_by,
        "allergies_confirmed_at": p.allergies_confirmed_at,
        "prescribers": [{"name": k or None, "medicines": v} for k, v in prescribers.items()],
        "last_reviewed": {"by": last.reviewer, "role": last.routed_to, "at": last.reviewed_at} if last else None,
        "emergency_enabled": store.emergency_token(pid) is not None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


class BPIn(BaseModel):
    systolic: int = Field(ge=60, le=260)
    diastolic: int = Field(ge=30, le=160)
    pulse: int | None = Field(default=None, ge=30, le=220)
    taken_on: date | None = None
    source: Literal["manual", "photo"] = "manual"  # photo = read from the monitor, then checked by the family

    @model_validator(mode="after")
    def _plausible(self) -> "BPIn":
        if self.systolic <= self.diastolic:
            raise ValueError("The top number (systolic) must be higher than the bottom number (diastolic)")
        # one day of slack: the server runs on UTC, families are up to 14 hours ahead of it
        if self.taken_on and self.taken_on > date.today() + timedelta(days=1):
            raise ValueError("The date cannot be in the future")
        return self


@app.post("/patients/{pid}/bp", status_code=201, dependencies=[Depends(family_access), Depends(limit_writes)])
def add_bp(pid: int, body: BPIn | None = Body(default=None), systolic: int | None = None,
           diastolic: int | None = None, taken_on: str | None = None,
           store: Store = Depends(get_store)) -> dict:
    """JSON body {systolic, diastolic, taken_on?}; query parameters still work for automations."""
    _patient_or_404(store, pid)
    if body is None:
        try:
            body = BPIn(systolic=systolic, diastolic=diastolic, taken_on=taken_on)  # type: ignore[arg-type]
        except ValidationError as e:
            raise HTTPException(422, e.errors(include_url=False, include_context=False)) from None
    store.add_bp(pid, (body.taken_on or date.today()).isoformat(), body.systolic, body.diastolic,
                 pulse=body.pulse, source=body.source)
    return {"ok": True, "readings": store.list_bp(pid)}


@app.get("/patients/{pid}/report", dependencies=[Depends(family_access)])
def weekly_report(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    items = store.list_items(pid, confirmed_only=True)
    all_flags = store.list_flags(pid, active_only=False)
    refills = [{"brand": it.brand, "generic": it.generic, "pills_left": it.pills_left, "days_left": days}
               for it, days in refills_due(items, within=7)]
    doses = None
    if p.is_demo:
        scheduled = sum(len(it.schedule) for it in items) * 7
        doses = {"scheduled": scheduled, "taken": max(scheduled - 4, 0), "is_demo": True,
                 "label": "Demo numbers — dose tracking is not built yet"}
    return {
        "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age},
        "bp": {"readings": store.list_bp(pid), "target": {"systolic": 140, "diastolic": 90}},
        "doses": doses,
        "flags": {
            "confirmed_open": sum(f.status == "confirmed" and f.active for f in all_flags),
            "resolved": sum(f.status == "confirmed" and not f.active for f in all_flags),
            "reviewed": sum(f.status in ("confirmed", "dismissed") for f in all_flags),
        },
        "refills_due": refills,
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


# ---- scan -----------------------------------------------------------------------------

@app.post("/patients/{pid}/scan", dependencies=[Depends(family_access), Depends(limit_scan)])
async def scan(pid: int, photos: list[UploadFile] = File(...), store: Store = Depends(get_store)) -> dict:
    """Photos -> shelf agent -> unconfirmed items. Photos stay in memory and are discarded
    after this request; thumbnails come back once as base64 and are never stored."""
    patient = _patient_or_404(store, pid)
    if not photos:
        raise HTTPException(422, "Add at least one photo")
    if len(photos) > MAX_PHOTOS:
        raise HTTPException(422, f"At most {MAX_PHOTOS} photos per scan")
    data = []
    for ph in photos:
        b = await ph.read()
        if len(b) > MAX_PHOTO_BYTES:
            raise HTTPException(413, "A photo is too large (12 MB max)")
        data.append(b)

    if not configured_providers("vision"):
        if not demo_mode():
            raise HTTPException(503, "No vision model is configured")
        # DEMO_MODE without keys: return the demo household so the UI always works.
        # Only the demo patient's list is replaced; real patients are never touched.
        if patient.is_demo:
            store.clear_items(pid)
        saved = [store.add_item(pid, it, **resolve_brand(it.brand, it.strength, store),
                                prompt_version="demo", model_id="demo (no model called)")
                 for it in DEMO_ITEMS]
        del data
        return {"items": [{**s.model_dump(), "thumbnail": None} for s in saved], "mode": "demo",
                "model_id": None, "warnings": ["Demo mode: no vision model configured, showing the demo household."]}

    try:
        outcome = await read_shelf(data, store=store, age=patient.age)
    except NoProviderAvailable as e:
        raise HTTPException(503, f"Could not read the photos right now ({e})") from e
    finally:
        del data  # AGENTS.md rule 6: never keep photos
    saved = []
    for s in outcome.items:
        item = store.add_item(pid, s.item, **s.match)
        saved.append({**item.model_dump(), "thumbnail": s.thumbnail})
    return {"items": saved, "mode": "live", "model_id": outcome.model_id,
            "needs_review": outcome.needs_review, "warnings": outcome.warnings}


# ---- evaluation results (read by the /docs page) -------------------------------------

EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "eval"


@app.get("/eval/results")
def eval_results() -> list[dict]:
    """Summaries of eval/results_*.json. Empty list means evaluation is in progress."""
    import json

    out = []
    for f in sorted(EVAL_DIR.glob("results_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        row = {k: data.get(k) for k in ("prompt_version", "model_id", "run_at", "images", "labelled_items",
                                         "brand_accuracy", "strength_accuracy", "avg_confidence")}
        n = data.get("labelled_items") or 0
        for key in ("brand_accuracy", "strength_accuracy"):
            if n and data.get(key) is not None:
                ci = proportion(key, round(data[key] * n), n)
                row[f"{key}_ci"] = [ci["ci_low"], ci["ci_high"]]
        out.append(row)
    return out


@app.get("/pilot/stats")
def pilot() -> dict:
    """Pilot proportions with 95% Wilson intervals, from eval/pilot.csv (real households only)."""
    return pilot_stats(EVAL_DIR / "pilot.csv")


# ---- AI models: visible, and the user may choose one ----------------------------------

MODEL_KINDS = ("vision", "text")


def _load_model_preferences(store: Store) -> None:
    import json

    for kind in MODEL_KINDS:
        raw = store.cache_get(f"pref:model:{kind}")
        pref = json.loads(raw) if raw else {}
        llm_router.set_preferred(kind, pref.get("provider"), pref.get("model"))


class ModelPreference(BaseModel):
    kind: Literal["vision", "text"]
    provider: str | None = None  # None/None = back to automatic
    model: str | None = None


@app.get("/models")
def models() -> dict:
    """The model chain per task (first answers, the rest are fallbacks), the user's choice,
    and what actually answered last. Names only; never keys."""
    out = {}
    for task in ("vision", "text", "explain_bn", "sathi"):
        kind = "vision" if task == "vision" else "text"
        pref = llm_router.preferred(kind)
        local_first = task in llm_router.LOCAL_FIRST
        out[task] = {
            "chain": [{"provider": p.name, "model": p.model} for p in configured_providers(task)],
            "preferred": {"provider": pref[0], "model": pref[1]} if pref and not local_first else None,
            "last_used": llm_router.last_used.get(task),
            "choosable": not local_first,
        }
    return {"tasks": out, "demo_mode": demo_mode()}


@app.put("/models/preference", dependencies=[Depends(require_reviewer)])
def set_model_preference(body: ModelPreference, store: Store = Depends(get_store)) -> dict:
    import json

    if body.provider and body.model:
        available = {(p.name, p.model) for p in configured_providers(body.kind)}
        if (body.provider, body.model) not in available:
            raise HTTPException(422, "That model is not available on this server")
        store.cache_set(f"pref:model:{body.kind}", json.dumps({"provider": body.provider, "model": body.model}))
    else:
        store.cache_set(f"pref:model:{body.kind}", "{}")
    llm_router.set_preferred(body.kind, body.provider, body.model)
    return models()


# ---- Sathi: next step, app guide, bridge to humans --------------------------------------

def _parse_ts(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value))


def step_context(store: Store, pid: int) -> StepContext:
    p = _patient_or_404(store, pid)
    items = store.list_items(pid)
    unconfirmed = [i for i in items if not i.confirmed]
    confirmed = [i for i in items if i.confirmed]
    last_emergency = _parse_ts(store.last_sathi_event(pid, "emergency"))
    unread = sum(1 for q in store.list_questions(pid) if q["reply"] and not q["reply_seen_at"])
    state = _review_state(store, pid)
    seen = _parse_ts(p.results_seen_at)
    confirmed_flags = store.list_flags(pid, statuses=("confirmed",))
    unseen = [f for f in confirmed_flags if f.reviewed_at and (seen is None or _parse_ts(f.reviewed_at) > seen)]
    # when the review finished: the last decision, or the check itself when nothing was found
    decided = [_parse_ts(f.reviewed_at) for f in store.list_flags(pid, statuses=("confirmed", "dismissed"))
               if f.reviewed_at]
    done_at = max(decided) if decided else _parse_ts(p.last_checked_at)
    finished_unseen = state == "reviewed" and done_at is not None and (seen is None or done_at > seen)
    last_check = _parse_ts(p.last_checked_at)
    newest_confirmed = _parse_ts(store.newest_item_at(pid, confirmed_only=True))
    return StepContext(
        emergency_recent=bool(last_emergency and last_emergency > datetime.now(timezone.utc) - timedelta(hours=24)),
        unread_replies=unread,
        unseen_results=len(unseen),
        results_ready=bool(unseen) or finished_unseen,
        unconfirmed=len(unconfirmed),
        unconfirmed_need_check=sum(1 for i in unconfirmed if i.needs_review),
        any_items=bool(items),
        ready_to_send=bool(confirmed) and (last_check is None
                                           or (newest_confirmed is not None and newest_confirmed > last_check)),
        in_review=state == "in_review",
        reviewed=state == "reviewed",
        passport_seen=p.passport_seen_at is not None,
        refills=[(it.brand, days) for it, days in refills_due(confirmed)],
    )


@app.get("/patients/{pid}/next-step", dependencies=[Depends(family_access)])
def get_next_step(pid: int, lang: Literal["bn", "en"] = "bn", phrase: bool = False,
                  store: Store = Depends(get_store)) -> dict:
    """The one thing to do next. Chosen by a state machine; with phrase=true the AI may
    reword the sentence (numbers and names are checked against the state)."""
    step = next_step(step_context(store, pid), pid)
    text, how = (sathi.phrase_next_step(step, lang, Router(store=store)) if phrase
                 else (step.text_bn if lang == "bn" else step.text_en, "fixed"))
    return {**step.to_dict(), "text": text, "button": step.button_bn if lang == "bn" else step.button_en,
            "phrased_by": how}


class AskIn(BaseModel):
    patient_id: int
    question: str = Field(min_length=1, max_length=500)
    lang: Literal["bn", "en"] = "bn"


def _notify_emergency(pid: int) -> None:
    """n8n alert so the family contact and a reviewer hear about it. Ids only."""
    url = _env("N8N_ALERT_WEBHOOK")
    if not url:
        return

    def send() -> None:
        try:
            httpx.post(url, timeout=5, json={"patient_id": pid, "event": "sathi_emergency"})
        except httpx.HTTPError as e:
            log.warning("n8n emergency alert failed: %s", type(e).__name__)

    threading.Thread(target=send, daemon=True).start()


@app.post("/assistant/ask", dependencies=[Depends(limit_sathi)])
def assistant_ask(body: AskIn, x_family_key: str | None = Header(default=None),
                  x_reviewer_token: str | None = Header(default=None), store: Store = Depends(get_store)) -> dict:
    family_access(body.patient_id, x_family_key, x_reviewer_token, store)
    patient = _patient_or_404(store, body.patient_id)
    state = next_step(step_context(store, body.patient_id), body.patient_id).code
    reply, ms = sathi.timed(sathi.ask, body.question, body.lang, body.patient_id, Router(store=store),
                            state=state, redact=[patient.name, patient.name_bn or ""])
    # AGENTS.md: every refusal and redirect is logged, anonymised (no text)
    store.log_sathi_event(body.patient_id, reply.kind, body.lang, reply.guide_ids, ms)
    if reply.kind == "emergency":
        _notify_emergency(body.patient_id)
    return reply.model_dump()


class QuestionIn(BaseModel):
    text: str = Field(min_length=2, max_length=1000)


@app.post("/patients/{pid}/questions", status_code=201,
          dependencies=[Depends(family_access), Depends(limit_writes)])
def ask_pharmacist(pid: int, body: QuestionIn, store: Store = Depends(get_store)) -> dict:
    """A family question for the reviewing pharmacist. Answered by a person, never by AI."""
    _patient_or_404(store, pid)
    return store.add_question(pid, body.text.strip())


@app.get("/patients/{pid}/questions", dependencies=[Depends(family_access)])
def family_questions(pid: int, store: Store = Depends(get_store)) -> list[dict]:
    return store.list_questions(pid)


@app.post("/patients/{pid}/questions/seen", status_code=204, dependencies=[Depends(family_access)])
def questions_seen(pid: int, store: Store = Depends(get_store)) -> None:
    store.mark_replies_seen(pid)


class SeenIn(BaseModel):
    what: Literal["results", "passport"]


@app.post("/patients/{pid}/seen", status_code=204, dependencies=[Depends(family_access)])
def mark_seen(pid: int, body: SeenIn, store: Store = Depends(get_store)) -> None:
    """The family opened results or the passport; moves the next step along."""
    store.update_patient(pid, **{f"{body.what}_seen_at": now()})


@app.get("/questions", dependencies=[Depends(require_reviewer)])
def reviewer_questions(status: Literal["open", "all"] = "open", store: Store = Depends(get_store)) -> dict:
    qs = store.list_questions(open_only=status == "open")
    patients = {p.id: p for p in store.list_patients()}
    rows = []
    for q in qs:
        p = patients.get(q["patient_id"])
        rows.append({**q, "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age,
                                      "is_demo": p.is_demo} if p else None})
    rows.sort(key=lambda q: q["created_at"])  # oldest first: the 1-2 day target
    return {"questions": rows, "open": len(store.list_questions(open_only=True))}


class ReplyIn(BaseModel):
    reply: str = Field(min_length=2, max_length=2000)
    reviewer: str = Field(min_length=1)


@app.post("/questions/{qid}/reply", dependencies=[Depends(require_reviewer)])
def reply_question(qid: int, body: ReplyIn, store: Store = Depends(get_store)) -> dict:
    if store.get_question(qid) is None:
        raise HTTPException(404, "Question not found")
    return store.reply_question(qid, body.reply.strip(), body.reviewer.strip())


@app.get("/eval/sathi")
def eval_sathi() -> list[dict]:
    """Summaries of eval/sathi_results_*.json, read by /docs and the README."""
    import json

    out = []
    for f in sorted(EVAL_DIR.glob("sathi_results_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out.append({k: data.get(k) for k in ("prompt_version", "mode", "run_at", "cases", "by_category",
                                              "leaks", "latency_ms")})
    return out


# ---- 6C: AI assist for reviewers, BP photos, passport, emergency page, FHIR -------------

def is_expired(item: MedicineItem, today: date | None = None) -> bool:
    """Expiry is printed as a month (YYYY-MM): usable to the end of that month."""
    if not item.expiry:
        return False
    try:
        y, m = (int(x) for x in item.expiry.split("-")[:2])
    except ValueError:
        return False
    t = today or date.today()
    return (y, m) < (t.year, t.month)


@app.patch("/patients/{pid}", dependencies=[Depends(family_access), Depends(limit_writes)])
def patch_patient(pid: int, body: PatientPatch, store: Store = Depends(get_store)) -> dict:
    """Allergies, emergency contact and visit questions, entered by the family."""
    p = _patient_or_404(store, pid)
    fields = body.model_dump(exclude_unset=True)
    if "allergies" in fields:
        fields["allergies"] = [a.strip() for a in fields["allergies"] or [] if a.strip()]
        if fields["allergies"] != p.allergies:  # a changed list needs the pharmacist again
            fields.update(allergies_confirmed_by=None, allergies_confirmed_at=None)
    if "visit_questions" in fields:
        fields["visit_questions"] = [q.strip() for q in fields["visit_questions"] or [] if q.strip()]
    updated = store.update_patient(pid, **fields)
    return {**updated.model_dump(), "demo_label": DEMO_LABEL if updated.is_demo else None}  # type: ignore[union-attr]


class ReviewerIn(BaseModel):
    reviewer: str = Field(min_length=1)


@app.post("/patients/{pid}/allergies/confirm", dependencies=[Depends(require_reviewer)])
def confirm_allergies(pid: int, body: ReviewerIn, store: Store = Depends(get_store)) -> dict:
    _patient_or_404(store, pid)
    return store.update_patient(pid, allergies_confirmed_by=body.reviewer, allergies_confirmed_at=now()).model_dump()  # type: ignore[union-attr]


@app.patch("/items/{item_id}/clinical", response_model=MedicineItem, dependencies=[Depends(require_reviewer)])
def clinical_patch(item_id: int, body: ClinicalPatch, store: Store = Depends(get_store)):
    """What it is for, and stopped: written by the pharmacist or doctor, never by AI."""
    _item_or_404(store, item_id)
    fields = body.model_dump(exclude_unset=True, exclude={"reviewer"})
    if "stopped" in fields:
        fields.update(stopped_by=body.reviewer if fields["stopped"] else None,
                      stopped_at=now() if fields["stopped"] else None)
    return store.update_item(item_id, **fields)


@app.post("/patients/{pid}/schedule/approve", dependencies=[Depends(require_reviewer)])
def approve_schedule(pid: int, body: ReviewerIn, store: Store = Depends(get_store)) -> dict:
    """The reviewer approves the times on the list. Only approved times reach Today's medicines."""
    _patient_or_404(store, pid)
    ts, n = now(), 0
    for it in store.list_items(pid, confirmed_only=True):
        if counts(it):
            store.update_item(it.id, schedule_approved_by=body.reviewer, schedule_approved_at=ts)
            n += 1
    return {"approved": n}


@app.post("/flags/{flag_id}/opened", status_code=204, dependencies=[Depends(require_reviewer)])
def flag_opened(flag_id: int, store: Store = Depends(get_store)) -> None:
    if store.get_flag(flag_id) is None:
        raise HTTPException(404, "Flag not found")
    store.mark_flag_opened(flag_id)


@app.get("/eval/review-time")
def review_time(store: Store = Depends(get_store)) -> dict:
    """Median minutes from opening a finding to deciding it: the cost of a review."""
    import statistics

    secs = [s for s in store.review_seconds() if 0 < s < 6 * 3600]  # ignore tabs left open for hours
    return {"reviews": len(secs), "median_seconds": round(statistics.median(secs), 1) if secs else None}


@app.get("/patients/{pid}/case-summary", dependencies=[Depends(require_reviewer)])
def get_case_summary(pid: int, reviewer: str | None = None, store: Store = Depends(get_store)) -> dict:
    """AI summary for the reviewer, facts only; names are checked against the record."""
    p = _patient_or_404(store, pid)
    items = [it for it in store.list_items(pid, confirmed_only=True) if counts(it)]
    flags = store.list_flags(pid, statuses=("pending_review", "confirmed"))
    out = clinical.case_summary(p, items, flags, Router(store=store))
    # automation bias: after a reviewer's first 10 reviews the panel starts collapsed
    return {**out, "collapsed": bool(reviewer) and store.reviews_by(reviewer) >= 10}


@app.post("/patients/{pid}/bp/read", dependencies=[Depends(family_access), Depends(limit_scan)])
async def read_bp(pid: int, photo: UploadFile = File(...), store: Store = Depends(get_store)) -> dict:
    """A photo of the BP monitor -> numbers for the family to check and save. Not stored."""
    _patient_or_404(store, pid)
    data = await photo.read()
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "The photo is too large (12 MB max)")
    if not configured_providers("vision"):
        raise HTTPException(503, "No vision model is configured")
    try:
        return clinical.read_bp_photo(data, Router(store=store))
    except NoProviderAvailable as e:
        raise HTTPException(503, f"Could not read the photo right now ({e})") from e
    finally:
        del data


@app.post("/patients/{pid}/emergency", dependencies=[Depends(family_access), Depends(limit_writes)])
def enable_emergency(pid: int, store: Store = Depends(get_store)) -> dict:
    """Turns on (or renews) the emergency page behind the passport QR. A new link replaces the old."""
    import secrets

    _patient_or_404(store, pid)
    token = secrets.token_urlsafe(18)
    store.update_patient(pid, emergency_token=token)
    return {"token": token}


@app.get("/patients/{pid}/emergency", dependencies=[Depends(family_access)])
def emergency_status(pid: int, store: Store = Depends(get_store)) -> dict:
    return {"token": store.emergency_token(pid)}


@app.delete("/patients/{pid}/emergency", status_code=204, dependencies=[Depends(family_access)])
def revoke_emergency(pid: int, store: Store = Depends(get_store)) -> None:
    store.update_patient(pid, emergency_token=None)


@app.get("/emergency/{token}", dependencies=[Depends(limit_writes)])
def emergency_page(token: str, store: Store = Depends(get_store)) -> dict:
    """Read-only, no login: medicines, allergies and the emergency contact. First name only."""
    p = store.patient_by_emergency_token(token) if len(token) >= 16 else None
    if p is None:
        raise HTTPException(404, "This emergency link is not active")
    items = [it for it in store.list_items(p.id, confirmed_only=True) if counts(it)]
    first = (p.name_bn or p.name).split()[0] if (p.name_bn or p.name) else ""
    first_en = p.name.split()[0] if p.name else ""
    return {
        "first_name": first, "first_name_en": first_en, "age": p.age,
        "medicines": [{"generic": it.generic, "brand": it.brand, "strength": it.strength, "schedule": it.schedule,
                       "per_dose": it.per_dose, "purpose": it.purpose, "purpose_bn": it.purpose_bn} for it in items],
        "allergies": p.allergies, "allergies_confirmed": p.allergies_confirmed_at is not None,
        "emergency_contact": {"name": p.emergency_contact_name, "phone": p.emergency_contact_phone}
        if p.emergency_contact_phone else None,
        "is_demo": p.is_demo,
    }


@app.get("/patients/{pid}/fhir", dependencies=[Depends(family_access)])
def fhir(pid: int, store: Store = Depends(get_store)) -> dict:
    """FHIR R4 Bundle: Patient + one MedicationStatement per current medicine. Prepares
    integration with Bangladesh's Shared Health Record and health ID plans."""
    p = _patient_or_404(store, pid)
    items = [it for it in store.list_items(pid, confirmed_only=True) if counts(it)]
    return clinical.fhir_bundle(p, items)


# ---- 6D: today's medicines, doctor visit, clean-up ---------------------------------------

@app.get("/patients/{pid}/today", dependencies=[Depends(family_access)])
def today(pid: int, store: Store = Depends(get_store)) -> dict:
    """Today's medicines from the APPROVED plan only. Items whose times the pharmacist has
    not checked yet are counted, not shown."""
    p = _patient_or_404(store, pid)
    items = [it for it in store.list_items(pid, confirmed_only=True) if counts(it)]
    approved = [it for it in items if it.schedule_approved_at and it.schedule]

    def entry(it: MedicineItem) -> dict:
        return {"id": it.id, "brand": it.brand, "generic": it.generic, "strength": it.strength,
                "per_dose": it.per_dose, "purpose": it.purpose, "purpose_bn": it.purpose_bn}

    return {
        "slots": {slot: [entry(it) for it in approved if slot in it.schedule] for slot in SLOTS},
        "waiting_approval": sum(1 for it in items if it.schedule and not it.schedule_approved_at),
        "as_needed": [entry(it) for it in items if not it.schedule],
        "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn},
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


@app.get("/patients/{pid}/visit", dependencies=[Depends(family_access)])
def visit_prep(pid: int, store: Store = Depends(get_store)) -> dict:
    """Before the doctor visit: medicines, what changed since the last visit and who changed
    it, confirmed findings and notes, recent blood pressure, and the family's questions."""
    p = _patient_or_404(store, pid)
    items = store.list_items(pid, confirmed_only=True)
    since = _parse_ts(p.last_visit_at)

    def after(ts) -> bool:
        return ts is not None and (since is None or _parse_ts(ts) > since)

    current = [it for it in items if counts(it)]
    changes = (
        [{"kind": "added", "brand": it.brand, "generic": it.generic, "at": it.created_at, "by": it.prescriber}
         for it in current if since is not None and after(it.created_at)]
        + [{"kind": "stopped", "brand": it.brand, "generic": it.generic, "at": it.stopped_at, "by": it.stopped_by}
           for it in items if it.stopped and after(it.stopped_at)]
    )
    four_weeks = (date.today() - timedelta(days=28)).isoformat()
    findings = [{**f, "items": [i["brand"] for i in f["items"]]}
                for f in _with_items(store, store.list_flags(pid, statuses=("confirmed",)))]
    return {
        "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age, "conditions": p.conditions},
        "last_visit_at": p.last_visit_at,
        "medicines": [{"brand": it.brand, "generic": it.generic, "strength": it.strength, "schedule": it.schedule,
                       "per_dose": it.per_dose, "prescriber": it.prescriber, "purpose": it.purpose,
                       "purpose_bn": it.purpose_bn} for it in current],
        "changes": changes,
        "findings": [{"code": f["code"], "severity": f["severity"], "brands": f["items"], "note": f["note"],
                      "explanation_bn": f["explanation_bn"], "reviewer": f["reviewer"]} for f in findings],
        "bp": store.list_bp(pid, limit=60, since=four_weeks),
        "questions": p.visit_questions,
        "pharmacist_questions": [{"text": q["text"], "reply": q["reply"], "replied_by": q["replied_by"]}
                                 for q in store.list_questions(pid)],
        "allergies": p.allergies,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


@app.post("/patients/{pid}/visit/done", dependencies=[Depends(family_access), Depends(limit_writes)])
def visit_done(pid: int, store: Store = Depends(get_store)) -> dict:
    """After the visit: start counting changes from now; the family scans the new prescription next."""
    _patient_or_404(store, pid)
    store.update_patient(pid, last_visit_at=now(), visit_questions=[])
    return {"next": f"/p/{pid}/scan"}


@app.get("/patients/{pid}/cleanup", dependencies=[Depends(family_access)])
def cleanup(pid: int, store: Store = Depends(get_store)) -> dict:
    """Strips to set aside so nobody takes them by mistake: expired, or stopped by the reviewer."""
    _patient_or_404(store, pid)
    items = store.list_items(pid, confirmed_only=True)

    def entry(it: MedicineItem, reason: str) -> dict:
        return {"id": it.id, "brand": it.brand, "generic": it.generic, "strength": it.strength,
                "expiry": it.expiry, "reason": reason, "stopped_by": it.stopped_by}

    todo = [entry(it, "expired" if is_expired(it) else "stopped")
            for it in items if not it.set_aside and (is_expired(it) or it.stopped)]
    done = [entry(it, "expired" if is_expired(it) else "stopped" if it.stopped else "other")
            for it in items if it.set_aside]
    return {"to_set_aside": todo, "set_aside": done}
