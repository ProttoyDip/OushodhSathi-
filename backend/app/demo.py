"""The demo household from BUILD_PLAN.md. Invented data, always labelled as such."""
from __future__ import annotations

from datetime import date, timedelta

from .models import MedicineItemIn, PatientIn

DEMO_LABEL = "Demo household — invented data"

DEMO_PATIENT = PatientIn(
    name="Rahima Begum", name_bn="রহিমা বেগম", age=68, district="Cumilla",
    conditions=["hypertension", "type 2 diabetes"], is_demo=True,
)

DR_A = "Dr. A (Cumilla Medical College OPD)"
VILLAGE = "Village doctor"
SHOP = "Local drug shop"

DEMO_ITEMS: list[MedicineItemIn] = [
    MedicineItemIn(brand="Napa", strength="500 mg", form="tablet", expiry="2027-03", prescriber=SHOP,
                   source="strip", confidence=0.96, schedule=["morning", "night"], pills_left=14, doses_per_day=2),
    MedicineItemIn(brand="Ace", strength="500 mg", form="tablet", expiry="2026-12", prescriber=VILLAGE,
                   source="strip", confidence=0.91, schedule=["noon"], pills_left=9, doses_per_day=1),
    MedicineItemIn(brand="Camlodin", strength="5 mg", form="tablet", expiry="2027-06", prescriber=DR_A,
                   source="box", confidence=0.97, schedule=["morning"], pills_left=22, doses_per_day=1),
    MedicineItemIn(brand="Amdocal", strength="5 mg", form="tablet", expiry="2027-01", prescriber=VILLAGE,
                   source="strip", confidence=0.82, schedule=["night"], pills_left=12, doses_per_day=1),
    MedicineItemIn(brand="Angilock", strength="50 mg", form="tablet", expiry="2027-08", prescriber=DR_A,
                   source="box", confidence=0.95, schedule=["morning"], pills_left=4, doses_per_day=1),
    MedicineItemIn(brand="Clofenac", strength="50 mg", form="tablet", expiry="2026-11", prescriber=SHOP,
                   source="strip", confidence=0.88, schedule=["noon", "night"], pills_left=10, doses_per_day=2),
    MedicineItemIn(brand="Rivotril", strength="0.5 mg", form="tablet", expiry="2027-02", prescriber=VILLAGE,
                   source="strip", confidence=0.9, schedule=["night"], pills_left=18, doses_per_day=1),
    MedicineItemIn(brand="Tryptin", strength="10 mg", form="tablet", expiry="2026-09", prescriber=VILLAGE,
                   source="strip", confidence=0.68, schedule=["night"], pills_left=6, doses_per_day=1),
    MedicineItemIn(brand="Comet", strength="500 mg", form="tablet", expiry="2027-05", prescriber=DR_A,
                   source="box", confidence=0.94, schedule=["morning", "night"], pills_left=8, doses_per_day=2),
]

DEMO_BP = [(168, 98), (164, 96), (159, 94), (162, 97), (150, 92), (146, 90), (142, 88)]

# Sample clinician notes used only by `seed_demo.py --reviewed` (labelled demo).
DEMO_NOTES = {
    "DUPLICATE_GENERIC:paracetamol": "Both strips are paracetamol. Please bring both strips to the next visit so we can decide together.",
    "DUPLICATE_GENERIC:amlodipine": "Two prescribers gave amlodipine. I have contacted Dr. A so that only one prescription continues.",
}


def demo_bp_dates(today: date | None = None) -> list[str]:
    today = today or date.today()
    return [(today - timedelta(days=6 - i)).isoformat() for i in range(7)]
