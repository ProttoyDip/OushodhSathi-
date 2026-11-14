"""AI that assists clinicians, and exports for other systems.

- Case summary for the reviewer: facts only, every name checked against the input.
  The reviewer decides; the summary is shown as "check the evidence".
- Blood-pressure monitor photo -> numbers, validated, low confidence asks the family.
- FHIR R4 export of the confirmed medicine list.
"""
from __future__ import annotations

import base64
import logging
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from . import prompts
from .agent import _prepare
from .guard import _DOSE_NUMBER, medicine_names_in
from .llm_router import NoProviderAvailable, Router, parse_json
from .models import MedicineItem, Patient, StoredFlag

log = logging.getLogger("oushodh.clinical")

# ---- reviewer case summary ------------------------------------------------------------

class PrescriberLine(BaseModel):
    name: str
    medicines: list[str] = []


class CaseSummary(BaseModel):
    summary: list[str] = Field(min_length=1, max_length=3)
    prescribers: list[PrescriberLine] = []
    questions_to_check: list[str] = Field(default=[], max_length=3)


_OPINION = re.compile(r"\b(should|must|recommend|advis|consider (stopping|starting|switching)|diagnos)\w*",
                      re.IGNORECASE)


def case_input(patient: Patient, items: list[MedicineItem], flags: list[StoredFlag]) -> str:
    """What the model sees: age, medicines, findings. No patient name."""
    meds = "\n".join(f"- {it.brand} | generic: {it.generic or 'unknown'} | class: {it.drug_class or 'unknown'} | "
                     f"prescriber: {it.prescriber or 'unknown'} | source: {it.source or 'unknown'}" for it in items)
    found = "\n".join(f"- {f.code} ({f.severity}, for the {f.routed_to}): {f.evidence}" for f in flags) or "- none"
    return f"Patient age: {patient.age}\nConfirmed medicines:\n{meds or '- none'}\nRule findings:\n{found}"


def summary_problems(s: CaseSummary, items: list[MedicineItem]) -> list[str]:
    """Every medicine and prescriber named must exist in the input; no advice, doses or diagnoses."""
    brands = {it.brand.lower() for it in items}
    prescribers = {(it.prescriber or "").lower() for it in items if it.prescriber}
    allowed = "\n".join(f"{it.brand} {it.generic or ''}" for it in items)
    problems = []
    for p in s.prescribers:
        if p.name.lower() not in prescribers:
            problems.append(f"unknown prescriber {p.name!r}")
        problems += [f"unknown medicine {m!r}" for m in p.medicines if m.lower() not in brands]
    text = "\n".join([*s.summary, *s.questions_to_check])
    if extra := medicine_names_in(text) - medicine_names_in(allowed):
        problems.append(f"medicine not in input: {', '.join(sorted(extra))}")
    if _OPINION.search(text):
        problems.append("advice or diagnosis")
    if _DOSE_NUMBER.search(text):
        problems.append("dose")
    return problems


def case_summary(patient: Patient, items: list[MedicineItem], flags: list[StoredFlag],
                 router: Router | None) -> dict:
    """-> {"summary": CaseSummary | None, "source": ..., "dropped": reason | None}."""
    if router is None or not items:
        return {"summary": None, "source": None, "dropped": "no model" if items else "no medicines"}
    try:
        result = router.chat("text", [
            {"role": "system", "content": prompts.load("case_summary")},
            {"role": "user", "content": case_input(patient, items, flags)},
        ], json_mode=True, budget_s=30)
        parsed = CaseSummary.model_validate(parse_json(result.text))
    except NoProviderAvailable as e:
        return {"summary": None, "source": None, "dropped": f"no model answered ({e})"}
    except (ValueError, ValidationError):
        return {"summary": None, "source": None, "dropped": "the model's answer was not valid"}
    if problems := summary_problems(parsed, items):
        log.warning("case summary dropped: %s", "; ".join(problems))
        return {"summary": None, "source": f"{result.provider}/{result.model}", "dropped": "; ".join(problems)}
    return {"summary": parsed.model_dump(), "source": f"{result.provider}/{result.model}",
            "prompt_version": prompts.version("case_summary"), "dropped": None}


# ---- blood-pressure monitor photo -----------------------------------------------------

LOW_BP_CONFIDENCE = 0.8


class BPReading(BaseModel):
    systolic: int | None = None
    diastolic: int | None = None
    pulse: int | None = None
    confidence: float = Field(default=0, ge=0, le=1)

    @field_validator("systolic", "diastolic", "pulse", mode="before")
    @classmethod
    def _ints(cls, v):
        return None if v in ("", "null") else v


def plausible(r: BPReading) -> bool:
    return (r.systolic is not None and r.diastolic is not None and 60 <= r.systolic <= 260
            and 30 <= r.diastolic <= 160 and r.diastolic < r.systolic
            and (r.pulse is None or 30 <= r.pulse <= 220))


def read_bp_photo(photo: bytes, router: Router) -> dict:
    """Reads the monitor's display. The photo stays in memory (AGENTS.md rule 6).
    Impossible values are rejected; below 0.8 confidence the family confirms or corrects."""
    image, media_type = _prepare(photo, 1024)
    url = f"data:{media_type};base64,{base64.b64encode(image).decode()}"
    del image
    result = router.chat("vision", [
        {"role": "system", "content": prompts.load("read_bp")},
        {"role": "user", "content": [
            {"type": "text", "text": "Read the numbers on this blood-pressure monitor."},
            {"type": "image_url", "image_url": {"url": url}},
        ]},
    ], json_mode=True)
    try:
        reading = BPReading.model_validate(parse_json(result.text))
    except (ValueError, ValidationError):
        reading = BPReading()
    ok = plausible(reading)
    if not ok:
        reading = BPReading(confidence=0)
    return {**reading.model_dump(), "readable": ok, "needs_check": not ok or reading.confidence < LOW_BP_CONFIDENCE,
            "model": f"{result.provider}/{result.model}", "prompt_version": prompts.version("read_bp")}


# ---- FHIR R4 -----------------------------------------------------------------------------

EVENT_TIMING = {"morning": "MORN", "noon": "NOON", "night": "NIGHT"}  # HL7 EventTiming codes


def fhir_bundle(patient: Patient, items: list[MedicineItem], base_url: str = "") -> dict:
    """A FHIR R4 collection Bundle: one Patient (no identifiers beyond an internal id) and
    one MedicationStatement per current confirmed medicine."""
    pid = f"patient-{patient.id}"
    entries: list[dict] = [{
        "fullUrl": f"{base_url}/Patient/{pid}" if base_url else f"urn:uuid:{pid}",
        "resource": {"resourceType": "Patient", "id": pid, "active": True},
    }]
    for it in items:
        name = " ".join(x for x in (it.brand, it.strength) if x)
        statement: dict = {
            "resourceType": "MedicationStatement",
            "id": f"med-{it.id}",
            "status": "active",
            "medicationCodeableConcept": {"text": f"{name} ({it.generic})" if it.generic else name},
            "subject": {"reference": f"Patient/{pid}"},
        }
        if it.schedule:
            statement["dosage"] = [{
                "text": ", ".join(it.schedule),
                "timing": {"repeat": {"when": [EVENT_TIMING[s] for s in it.schedule]}},
            }]
        if it.purpose:
            statement["reasonCode"] = [{"text": it.purpose}]
        if it.prescriber:
            statement["informationSource"] = {"display": it.prescriber}
        entries.append({"fullUrl": f"urn:uuid:med-{it.id}", "resource": statement})
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}
