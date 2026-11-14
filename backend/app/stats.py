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


# ---- blood-pressure trend (reviewer only) -------------------------------------------

# two-sided 95% t critical values; df >= 30 uses the normal value
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
        10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110,
        18: 2.101, 19: 2.093, 20: 2.086, 22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048}
BP_TARGET = (140, 90)
BP_MIN_READINGS = 4
BP_MIN_SPAN_DAYS = 3


def _t95(df: int) -> float:
    if df >= 30:
        return Z95
    return _T95.get(df) or _T95[max(k for k in _T95 if k <= df)]


def _slope(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares slope and its standard error."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    resid = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    se = sqrt(resid / (n - 2) / sxx) if n > 2 else float("inf")
    return b, se


def bp_trend(readings: list[dict]) -> dict:
    """Describe home blood-pressure readings for the reviewer: a straight-line trend per
    week with a 95% confidence interval, plus how many readings were at or above 140/90.

    Pure arithmetic, no AI. It describes the numbers; it never says what to do.
    "falling"/"rising" only when the whole 95% interval is on one side of zero.
    """
    from datetime import date as _date

    rows = sorted(readings, key=lambda r: r["taken_on"])
    n = len(rows)
    above = sum(r["systolic"] >= BP_TARGET[0] or r["diastolic"] >= BP_TARGET[1] for r in rows)
    out: dict = {"n": n, "above_target": above, "target": {"systolic": BP_TARGET[0], "diastolic": BP_TARGET[1]}}
    if n == 0:
        return {**out, "status": "no_readings"}
    days = [(_date.fromisoformat(str(r["taken_on"])[:10]) - _date.fromisoformat(str(rows[0]["taken_on"])[:10])).days
            for r in rows]
    out["first"], out["last"] = str(rows[0]["taken_on"])[:10], str(rows[-1]["taken_on"])[:10]
    out["mean"] = {"systolic": round(sum(r["systolic"] for r in rows) / n),
                   "diastolic": round(sum(r["diastolic"] for r in rows) / n)}
    if n < BP_MIN_READINGS or days[-1] - days[0] < BP_MIN_SPAN_DAYS or len(set(days)) < 2:
        return {**out, "status": "too_few"}
    result = {}
    for k in ("systolic", "diastolic"):
        b, se = _slope(days, [float(r[k]) for r in rows])
        half = _t95(n - 2) * se
        per_week, lo, hi = 7 * b, 7 * (b - half), 7 * (b + half)
        result[k] = {"per_week": round(per_week, 1), "ci_low": round(lo, 1), "ci_high": round(hi, 1)}
    s = result["systolic"]
    status = "falling" if s["ci_high"] < 0 else "rising" if s["ci_low"] > 0 else "no_clear_change"
    return {**out, "status": status, "slope": result}
