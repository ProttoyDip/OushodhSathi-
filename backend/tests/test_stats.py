import pytest

from app.stats import pilot_stats, wilson


def test_wilson_matches_reference_values():
    # Reference: Wilson (1927); 8/10 -> [0.490, 0.943], 0/10 -> [0, 0.278]
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-3) and hi == pytest.approx(0.9433, abs=1e-3)
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and hi == pytest.approx(0.2775, abs=1e-3)


def test_wilson_rejects_bad_input():
    with pytest.raises(ValueError):
        wilson(1, 0)
    with pytest.raises(ValueError):
        wilson(5, 3)


def test_pilot_stats_empty_until_real_data(tmp_path):
    f = tmp_path / "pilot.csv"
    f.write_text("household_id,visit_date,medicines,flags_raised,flags_confirmed\n", encoding="utf-8")
    assert pilot_stats(f) == {"households": 0, "proportions": []}
    assert pilot_stats(tmp_path / "missing.csv")["households"] == 0


def test_pilot_stats_proportions(tmp_path):
    f = tmp_path / "pilot.csv"
    f.write_text("household_id,visit_date,medicines,flags_raised,flags_confirmed\n"
                 "h1,2026-10-01,7,3,2\nh2,2026-10-02,3,1,0\n", encoding="utf-8")
    s = pilot_stats(f)
    assert s["households"] == 2 and s["medicines"] == 10
    first = s["proportions"][0]
    assert (first["k"], first["n"]) == (1, 2) and first["ci_low"] < 0.5 < first["ci_high"]
    assert s["proportions"][2]["k"] == 2 and s["proportions"][2]["n"] == 4


def test_pilot_endpoint(client):
    r = client.get("/pilot/stats")
    assert r.status_code == 200 and "proportions" in r.json()
