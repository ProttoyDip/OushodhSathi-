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
    "DUPLICATE_GENERIC", "THERAPEUTIC_DUPLICATION", "INTERACTION", "BEERS_65", "EXPIRED",
    "ANTICHOLINERGIC_BURDEN", "LOOK_ALIKE_NAMES", "TRIPLE_WHAMMY",
    "KIDNEY_DOSE", "KIDNEY_TEST_DUE", "ANTIBIOTIC_NO_PRESCRIPTION",
]
# Where a medicine came from, picked by the family on the confirm screen (never guessed by a model)
PrescriberKind = Literal["doctor", "village_doctor", "drug_shop", "self", "unknown"]
MatchMethod = Literal["exact", "fuzzy", "web_unverified", "not_found", "manual"]


class PatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    name_bn: str | None = Field(default=None, max_length=80)
    age: int = Field(ge=0, le=120)
    district: str | None = Field(default=None, max_length=60)
    conditions: list[str] = Field(default=[], max_length=10)
    is_demo: bool = False


CONSENT_VERSION = "2026-11"  # bump when the privacy notice changes; stored with each household
EMAIL_PATTERN = r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$"


class PatientCreate(PatientIn):
    """A new household from /start. Consent to the privacy notice is required; email is optional."""

    consent: Literal[True]
    family_email: str | None = Field(default=None, max_length=254, pattern=EMAIL_PATTERN)
    email_opt_in: bool = False


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
    family_email: str | None = None
    email_opt_in: bool = False
    consent_at: datetime | None = None
    consent_version: str | None = None
    sex: Literal["female", "male"] | None = None  # needed for eGFR (CKD-EPI 2021); optional


class PatientPatch(BaseModel):
    """What the family can change. Editing allergies clears the pharmacist's confirmation."""

    allergies: list[str] | None = Field(default=None, max_length=20)
    emergency_contact_name: str | None = Field(default=None, max_length=80)
    emergency_contact_phone: str | None = Field(default=None, max_length=20, pattern=r"^[0-9+\- ]*$")
    visit_questions: list[str] | None = Field(default=None, max_length=20)
    family_email: str | None = Field(default=None, max_length=254, pattern=EMAIL_PATTERN)
    email_opt_in: bool | None = None
    sex: Literal["female", "male"] | None = None


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
    prescriber_kind: PrescriberKind = "unknown"


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
    prescriber_kind: PrescriberKind | None = None


class ClinicalPatch(BaseModel):
    """Reviewer-only fields on an item: written by the pharmacist or doctor, never by AI."""

    purpose: str | None = Field(default=None, max_length=120)
    purpose_bn: str | None = Field(default=None, max_length=120)
    stopped: bool | None = None
    reviewer: str | None = None  # ignored for personal reviewer logins: the server records who it was


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
    def aware_group(self) -> str | None:
        """WHO AWaRe group (Access / Watch / Reserve) when the generic is a known antibiotic."""
        from .tables import aware_group
        return aware_group(self.generic)

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
    prescriber_kind: PrescriberKind = "unknown"


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
    reviewer_id: int | None = None  # the personal reviewer login that decided it (None: demo token)
    note: str | None = None
    reviewed_at: datetime | None = None
    explanation_bn: str | None = None
    opened_at: datetime | None = None  # first opened by a reviewer
    checklist: list[str] = []  # reviewer-only pack observations (never shown to the family)


# Where-did-it-come-from observations the pharmacist can tick with a review. Neutral notes for the
# record: the app never says a medicine is fake, and no model judges authenticity.
PackCheck = Literal["pack_unusual", "unlicensed_seller"]


class ReviewIn(BaseModel):
    status: Literal["confirmed", "dismissed"]
    reviewer: str | None = None  # ignored for personal reviewer logins: the server records who it was
    note: str | None = Field(default=None, max_length=2000)
    checklist: list[PackCheck] = Field(default=[], max_length=2)


class ReviewerAccount(BaseModel):
    """A pharmacist or doctor with a personal, revocable login. The token itself is never stored."""

    id: int
    name: str
    role: Literal["pharmacist", "doctor"]
    reg_no: str | None = None
    created_at: datetime
    revoked_at: datetime | None = None
    is_demo: bool = False  # the shared demo token (DEMO_MODE only), not a real person


class ReviewerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    role: Literal["pharmacist", "doctor"]
    reg_no: str | None = Field(default=None, max_length=40)  # BMDC or Pharmacy Council registration


class Review(ReviewIn):
    id: int
    flag_id: int
    created_at: datetime
