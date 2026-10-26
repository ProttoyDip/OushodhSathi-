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


class MedicineItemPatch(BaseModel):
    brand: str | None = None
    strength: str | None = None
    expiry: str | None = None
    prescriber: str | None = None
    schedule: list[Literal["morning", "noon", "night"]] | None = None
    pills_left: int | None = None
    doses_per_day: float | None = None
    confirmed: bool | None = None


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


class ReviewIn(BaseModel):
    status: Literal["confirmed", "dismissed"]
    reviewer: str = Field(min_length=1)
    note: str | None = None


class Review(ReviewIn):
    id: int
    flag_id: int
    created_at: datetime
