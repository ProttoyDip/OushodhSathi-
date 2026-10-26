"""OushodhSathi API. OpenAPI docs at /docs."""
from __future__ import annotations

import hmac
import logging
import os
import threading
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from . import prompts  # noqa: E402
from .agent import read_shelf, resolve_brand  # noqa: E402
from .demo import DEMO_ITEMS, DEMO_LABEL  # noqa: E402
from .explain import explain_flag  # noqa: E402
from . import llm_router  # noqa: E402
from .llm_router import NoProviderAvailable, Router, _env, configured_providers, provider_names  # noqa: E402
from .models import (  # noqa: E402
    MedicineItem, MedicineItemIn, MedicineItemPatch, Patient, PatientIn, ReviewIn, RuleItem, StoredFlag,
)
from .rules import run_rules  # noqa: E402
from .stats import pilot_stats, proportion  # noqa: E402
from .store import Store  # noqa: E402
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


def require_reviewer(x_reviewer_token: str | None = Header(default=None)) -> None:
    expected = reviewer_token()
    if not expected:
        raise HTTPException(503, "REVIEWER_TOKEN is not configured on the server")
    if not x_reviewer_token or not hmac.compare_digest(x_reviewer_token, expected):
        raise HTTPException(401, "Reviewer token required")


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

@app.get("/patients", response_model=list[Patient])
def list_patients(store: Store = Depends(get_store)):
    return store.list_patients()


@app.post("/patients", response_model=Patient, status_code=201)
def create_patient(body: PatientIn, store: Store = Depends(get_store)):
    return store.create_patient(body)


@app.get("/patients/{pid}")
def get_patient(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    return {**p.model_dump(), "demo_label": DEMO_LABEL if p.is_demo else None}


@app.get("/patients/{pid}/items", response_model=list[MedicineItem])
def list_items(pid: int, store: Store = Depends(get_store)):
    _patient_or_404(store, pid)
    return store.list_items(pid)


@app.post("/patients/{pid}/items", response_model=MedicineItem, status_code=201)
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


@app.patch("/items/{item_id}", response_model=MedicineItem)
def patch_item(item_id: int, body: MedicineItemPatch, store: Store = Depends(get_store)):
    item = _item_or_404(store, item_id)
    fields = body.model_dump(exclude_unset=True)
    if "brand" in fields or "strength" in fields:
        brand = fields.get("brand", item.brand)
        strength = fields.get("strength", item.strength)
        fields.update(resolve_brand(brand, strength, store))
        # a human typed or corrected it: it is no longer a low-confidence machine reading
        fields["confidence"] = 1.0
        fields["source"] = item.source if "brand" not in fields else "manual"
    return store.update_item(item_id, **fields)


@app.delete("/items/{item_id}", status_code=204)
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


@app.post("/patients/{pid}/check")
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


@app.get("/patients/{pid}/status")
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

@app.get("/patients/{pid}/flags")
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
    updated = store.review_flag(flag_id, body, explanation)
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


@app.get("/patients/{pid}/passport")
def passport(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    items = store.list_items(pid, confirmed_only=True)

    def entry(it: MedicineItem) -> dict:
        return {"id": it.id, "generic": it.generic, "brand": it.brand, "strength": it.strength,
                "prescriber": it.prescriber, "needs_review": it.needs_review}

    groups = {slot: [entry(it) for it in items if slot in it.schedule] for slot in SLOTS}
    groups["as_needed"] = [entry(it) for it in items if not it.schedule]
    notes = [
        {"code": f.code, "severity": f.severity, "brands": [it["brand"] for it in f_items],
         "note": f.note, "explanation_bn": f.explanation_bn, "reviewer": f.reviewer,
         "reviewed_at": f.reviewed_at}
        for f, f_items in ((f, _with_items(store, [f])[0]["items"]) for f in store.list_flags(pid, statuses=("confirmed",)))
    ]
    return {
        "patient": {"id": p.id, "name": p.name, "name_bn": p.name_bn, "age": p.age,
                    "conditions": p.conditions, "district": p.district},
        "groups": groups,
        "confirmed_notes": notes,
        "medicine_count": len(items),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


@app.post("/patients/{pid}/bp", status_code=201)
def add_bp(pid: int, systolic: int, diastolic: int, taken_on: str | None = None,
           store: Store = Depends(get_store)) -> dict:
    _patient_or_404(store, pid)
    store.add_bp(pid, taken_on or date.today().isoformat(), systolic, diastolic)
    return {"ok": True}


@app.get("/patients/{pid}/report")
def weekly_report(pid: int, store: Store = Depends(get_store)) -> dict:
    p = _patient_or_404(store, pid)
    items = store.list_items(pid, confirmed_only=True)
    all_flags = store.list_flags(pid, active_only=False)
    refills = []
    for it in items:
        if it.pills_left is not None and it.doses_per_day:
            days = it.pills_left / it.doses_per_day
            if days <= 7:
                refills.append({"brand": it.brand, "generic": it.generic, "pills_left": it.pills_left,
                                "days_left": round(days, 1)})
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
        "refills_due": sorted(refills, key=lambda r: r["days_left"]),
        "demo_label": DEMO_LABEL if p.is_demo else None,
    }


# ---- scan -----------------------------------------------------------------------------

@app.post("/patients/{pid}/scan")
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
    for task in ("vision", "text", "explain_bn"):
        kind = "vision" if task == "vision" else "text"
        pref = llm_router.preferred(kind)
        out[task] = {
            "chain": [{"provider": p.name, "model": p.model} for p in configured_providers(task)],
            "preferred": {"provider": pref[0], "model": pref[1]} if pref and task != "explain_bn" else None,
            "last_used": llm_router.last_used.get(task),
            "choosable": task != "explain_bn",
        }
    return {"tasks": out, "demo_mode": demo_mode()}


@app.put("/models/preference")
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
