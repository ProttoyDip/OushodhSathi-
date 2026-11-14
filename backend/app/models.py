"""Pydantic models shared by the API, store, rules engine and agent."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field

LOW_CONFIDENCE = 0.75  # AGENTS.md rule 4

Severity = Literal["red", "amber"]
RoutedTo = Literal["doctor", "pharmacist"]
FlagStatus = Literal["pending_review", "confirmed", "dismissed"]
FlagCode = Literal[
    "DUPLICATE_GENERIC", "THERAPEUTIC_DUPLICATION", "INTERACTION", "BEERS_65", "EXPIRED"
]
MatchMethod = Literal["exact", "fuzzy", "web_unverified", "not_found", "manual"]


class PatientIn(BaseModel):
    name: str
    name_bn: str | None = None
    age: int = Field(ge=0, le=120)
    district: str | None = None
    conditions: list[str] = []
    is_demo: bool = False


class Patient(PatientIn):
    id: int
    created_at: datetime
    last_checked_at: datetime | None = None
    allergies: list[str] = []
    allergies_confirmed_by: str | None = None
    allergies_confirmed_at: datetime | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    last_visit_at: datetime | None = None
    results_seen_at: datetime | None = None
    passport_seen_at: datetime | None = None
    visit_questions: list[str] = []
    ramadan_status: Literal["requested", "approved"] | None = None
    ramadan_requested_at: datetime | None = None
    ramadan_note: str | None = None
    ramadan_approved_by: str | None = None
    ramadan_approved_at: datetime | None = None


class PatientPatch(BaseModel):
    """What the family can change. Editing allergies clears the pharmacist's confirmation."""

    allergies: list[str] | None = Field(default=None, max_length=20)
    emergency_contact_name: str | None = Field(default=None, max_length=80)
    emergency_contact_phone: str | None = Field(default=None, max_length=20, pattern=r"^[0-9+\- ]*$")
    visit_questions: list[str] | None = Field(default=None, max_length=20)


class MedicineItemIn(BaseModel):
    """What a family member (or the extraction agent) submits for one medicine."""

    brand: str
    strength: str | None = None
    form: str | None = None
    expiry: str | None = Field(default=None, description="YYYY-MM")
    prescriber: str | None = None
    source: str | None = "manual"  # strip | box | prescription | manual
    confidence: float = Field(default=1.0, ge=0, le=1)
    schedule: list[Literal["morning", "noon", "night"]] = []
    pills_left: int | None = None
    doses_per_day: float | None = None
    per_dose: int = Field(default=1, ge=1, le=10)  # tablets each time


class MedicineItemPatch(BaseModel):
    brand: str | None = None
    strength: str | None = None
    expiry: str | None = None
    prescriber: str | None = None
    schedule: list[Literal["morning", "noon", "night"]] | None = None
    pills_left: int | None = None
    doses_per_day: float | None = None
    per_dose: int | None = Field(default=None, ge=1, le=10)
    confirmed: bool | None = None
    set_aside: bool | None = None


class ClinicalPatch(BaseModel):
    """Reviewer-only fields on an item: written by the pharmacist or doctor, never by AI."""

    purpose: str | None = Field(default=None, max_length=120)
    purpose_bn: str | None = Field(default=None, max_length=120)
    stopped: bool | None = None
    reviewer: str = Field(min_length=1)


class MedicineItem(MedicineItemIn):
    id: int
    patient_id: int
    generic: str | None = None
    drug_class: str | None = None
    match_method: MatchMethod = "not_found"
    match_score: float | None = None
    match_source: str | None = None  # data file name or URL
    prompt_version: str | None = None
    model_id: str | None = None
    confirmed: bool = False
    purpose: str | None = None
    purpose_bn: str | None = None
    stopped: bool = False
    stopped_by: str | None = None
    stopped_at: datetime | None = None
    set_aside: bool = False
    schedule_approved_by: str | None = None
    schedule_approved_at: datetime | None = None
    created_at: datetime | None = None
    ramadan_slots: list[Literal["sehri", "iftar"]] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def needs_review(self) -> bool:
        return (
            self.confidence < LOW_CONFIDENCE
            or self.match_method in ("web_unverified", "not_found")
        )


class RuleItem(BaseModel):
    """The minimum the rules engine needs to know about one confirmed item."""

    id: int
    brand: str
    generic: str | None
    drug_class: str | None = None
    strength: str | None = None
    expiry: str | None = None
    prescriber: str | None = None


class Flag(BaseModel):
    """A safety finding. Only rules.py creates these."""

    key: str
    code: FlagCode
    severity: Severity
    item_ids: list[int]
    evidence: str
    routed_to: RoutedTo
    data_source: str
    meta: dict = {}


class StoredFlag(Flag):
    id: int
    patient_id: int
    status: FlagStatus = "pending_review"
    active: bool = True
    created_at: datetime
    reviewer: str | None = None
    note: str | None = None
    reviewed_at: datetime | None = None
    explanation_bn: str | None = None
    opened_at: datetime | None = None  # first opened by a reviewer


class ReviewIn(BaseModel):
    status: Literal["confirmed", "dismissed"]
    reviewer: str = Field(min_length=1)
    note: str | None = None


class Review(ReviewIn):
    id: int
    flag_id: int
    created_at: datetime
