"""Small, dependency-free statistics for published numbers.

Every proportion we show on /docs carries a 95% Wilson score interval, which behaves
well for the small samples a pilot produces (unlike the normal approximation).
"""
from __future__ import annotations

import csv
from math import sqrt
from pathlib import Path

Z95 = 1.959963984540054


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """95% Wilson score interval for k successes out of n trials."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError("k must be between 0 and n")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def proportion(label: str, k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"label": label, "k": k, "n": n, "p": round(k / n, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4)}


PILOT_COLUMNS = ("household_id", "visit_date", "medicines", "flags_raised", "flags_confirmed")


def pilot_stats(path: Path) -> dict:
    """Summarise eval/pilot.csv (one row per consenting pilot household, real data only).

    Returns {"households": 0, "proportions": []} when there is no pilot data yet.
    """
    rows: list[dict] = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if not (r.get("household_id") or "").strip():
                    continue
                rows.append({c: int(r[c] or 0) for c in ("medicines", "flags_raised", "flags_confirmed")})
    n = len(rows)
    if n == 0:
        return {"households": 0, "proportions": []}
    raised = sum(r["flags_raised"] for r in rows)
    out = [
        proportion("Households with at least one clinician-confirmed problem",
                   sum(r["flags_confirmed"] > 0 for r in rows), n),
        proportion("Households taking 5 or more medicines", sum(r["medicines"] >= 5 for r in rows), n),
    ]
    if raised:
        out.append(proportion("Rule flags confirmed by the clinician",
                              sum(r["flags_confirmed"] for r in rows), raised))
    return {"households": n, "medicines": sum(r["medicines"] for r in rows), "proportions": out}
