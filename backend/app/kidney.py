"""Kidney function from a serum creatinine result. Pure arithmetic, no AI.

eGFR uses the 2021 CKD-EPI creatinine equation (race-free), adults 18+:
    eGFR = 142 x min(Scr/k, 1)^a x max(Scr/k, 1)^-1.200 x 0.9938^age x 1.012 [if female]
    k = 0.7 (female) / 0.9 (male); a = -0.241 (female) / -0.302 (male); Scr in mg/dL.
Sources:
- National Kidney Foundation, "CKD-EPI Creatinine Equation (2021)":
  https://www.kidney.org/content/ckd-epi-creatinine-equation-2021
- NIDDK, "Glomerular Filtration Rate Equations (adults)":
  https://www.niddk.nih.gov/research-funding/research-programs/kidney-clinical-research-epidemiology/laboratory/glomerular-filtration-rate-equations/adults
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

Sex = Literal["female", "male"]

UMOL_PER_MG_DL = 88.4          # creatinine: umol/L / 88.4 = mg/dL (NKF, NIDDK)
MIN_CREATININE_MG_DL = 0.2     # below this a result is not physiologically plausible (input check)
MAX_CREATININE_MG_DL = 20.0    # above this, a typing or unit error is far likelier than a real value


def to_mg_dl(value: float, unit: Literal["mg/dL", "umol/L"]) -> float:
    return value / UMOL_PER_MG_DL if unit == "umol/L" else value


def egfr_ckd_epi_2021(scr_mg_dl: float, age: int, sex: Sex) -> float:
    """mL/min/1.73 m^2. Adults only; the caller checks age >= 18."""
    female = sex == "female"
    k = 0.7 if female else 0.9
    a = -0.241 if female else -0.302
    ratio = scr_mg_dl / k
    value = 142 * min(ratio, 1) ** a * max(ratio, 1) ** -1.200 * 0.9938 ** age
    return value * 1.012 if female else value


def kdigo_stage(egfr: float) -> str:
    """GFR category, KDIGO 2012 Clinical Practice Guideline for the Evaluation and Management of
    Chronic Kidney Disease (Kidney Int Suppl 2013;3:1-150), table 5:
    https://kdigo.org/guidelines/ckd-evaluation-and-management/"""
    if egfr >= 90:
        return "G1"
    if egfr >= 60:
        return "G2"
    if egfr >= 45:
        return "G3a"
    if egfr >= 30:
        return "G3b"
    if egfr >= 15:
        return "G4"
    return "G5"


@dataclass(frozen=True)
class KidneyContext:
    """What the rules need: the latest eGFR (None when it cannot be computed, e.g. sex not
    recorded) and the date of the latest kidney test (None when there has never been one)."""
    egfr: float | None
    taken_on: date | None


def context_from(latest: dict | None, age: int | None, sex: str | None) -> KidneyContext:
    """latest: the newest kidney_tests row ({"taken_on": "YYYY-MM-DD", "creatinine_mg_dl": float})."""
    if not latest:
        return KidneyContext(egfr=None, taken_on=None)
    taken = date.fromisoformat(str(latest["taken_on"])[:10])
    egfr = None
    if sex in ("female", "male") and age is not None and age >= 18:
        egfr = egfr_ckd_epi_2021(float(latest["creatinine_mg_dl"]), age, sex)  # type: ignore[arg-type]
    return KidneyContext(egfr=egfr, taken_on=taken)
