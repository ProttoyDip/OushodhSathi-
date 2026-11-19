"""The synthetic benchmark (Prompt 14B): its label files are valid, and its /docs card is separate from
real-photo results, always labelled, and absent until it has been run."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYNTH = ROOT / "eval" / "synthetic"
sys.path.insert(0, str(ROOT / "eval"))

import evalcommon  # noqa: E402


def test_committed_synthetic_labels_are_valid():
    rows = evalcommon.read_rows(SYNTH / "labels.csv", ("image_path", "brand", "strength", "expiry", "condition"))
    evalcommon.check_strip_rows(rows, SYNTH)
    assert len(rows) == 45 and len({r["image_path"] for r in rows}) == 30
    assert {r["condition"] for r in rows} == {"clear", "cut_strip", "glare", "bangla", "handwritten"}
    from app.brands import normalise
    seed = {normalise(r["brand"]) for r in csv.DictReader((ROOT / "backend/data/brands_seed.csv").open(encoding="utf-8"))}
    assert [r["brand"] for r in rows if normalise(r["brand"]) not in seed] == []
    bp = evalcommon.read_rows(SYNTH / "bp_labels.csv", ("image_path", "systolic", "diastolic", "pulse"))
    evalcommon.check_bp_rows(bp, SYNTH)
    assert len(bp) == 20


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _strip(kind: str) -> dict:
    p = {"label": "x", "k": 9, "n": 10, "p": 0.9, "ci_low": 0.6, "ci_high": 0.98}
    return {"kind": kind, "run_at": "2026-11-19T00:00:00+00:00", "prompt_version": "extract_strip.v1", "n_photos": 30,
            "labelled_items": 45, "status": "synthetic benchmark" if kind == "synthetic" else "measured",
            "brand_accuracy": 0.9, "images": 30,
            "runs": {"chain": {"brand": p, "strength": p, "expiry": None, "needs_check": p, "by_condition": {"glare": p},
                               "second_read": {"ran_on_items": 4, "strength": {"catch": p}, "expiry": {"catch": None}}}}}


def test_card_is_empty_until_the_benchmark_has_run(client, tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
    r = client.get("/eval/synthetic").json()
    assert r["strip"] is None and r["bp"] is None and "not real-photo accuracy" in r["label"]["en"]


def test_card_shows_the_synthetic_results_with_their_label(client, tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
    _write(tmp_path / "synthetic" / "results_extract_strip.v1.json", _strip("synthetic"))
    _write(tmp_path / "synthetic" / "bp_results_read_bp.v1.json", {"kind": "synthetic", "run_at": "x", "n_photos": 20,
                                                                    "systolic_accuracy": 0.95, "wrong_and_not_flagged": 1})
    r = client.get("/eval/synthetic").json()
    assert r["strip"]["n_photos"] == 30 and r["strip"]["by_condition"]["glare"]["p"] == 0.9
    assert r["strip"]["second_read"]["strength_catch"]["k"] == 9 and r["bp"]["systolic_accuracy"] == 0.95
    assert r["label"]["bn"] and "computer-drawn" in r["label"]["en"]


def test_synthetic_and_real_never_cross(client, tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
    # a synthetic file in the real folder is never real-photo accuracy...
    _write(tmp_path / "results_extract_strip.v1.json", _strip("synthetic"))
    assert client.get("/eval/results").json() == []
    # ...and a real file in the synthetic folder never shows in the synthetic card
    _write(tmp_path / "synthetic" / "results_extract_strip.v1.json", _strip("real"))
    assert client.get("/eval/synthetic").json()["strip"] is None


def test_real_results_still_show(client, tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
    _write(tmp_path / "results_extract_strip.v1.json", _strip("real"))
    rows = client.get("/eval/results").json()
    assert len(rows) == 1 and rows[0]["brand_accuracy"] == 0.9
