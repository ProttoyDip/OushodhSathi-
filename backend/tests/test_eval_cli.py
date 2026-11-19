"""--labels / --out / --kind for the strip and BP evals (Prompt 14A). Vision is mocked: CI has no keys."""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "eval"
sys.path.insert(0, str(EVAL))

import evalcommon  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, EVAL / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\nfake")


def test_defaults_are_unchanged():
    o = evalcommon.parse([], default_labels="labels.csv", out_name="results_extract_strip.v1.json")
    assert o.kind == "real" and o.labels == EVAL / "labels.csv" and o.out == EVAL / "results_extract_strip.v1.json"
    assert o.base == EVAL


def test_synthetic_paths_resolve_next_to_their_labels():
    o = evalcommon.parse(["--kind", "synthetic", "--labels", str(EVAL / "synthetic" / "labels.csv")],
                         default_labels="labels.csv", out_name="results_extract_strip.v1.json")
    assert o.base == EVAL / "synthetic" and o.out == EVAL / "synthetic" / "results_extract_strip.v1.json"


@pytest.mark.parametrize("out", ["results_extract_strip.v1.json", "bp_results_read_bp.v1.json", "results_x.json"])
def test_synthetic_may_not_overwrite_real_results(out):
    with pytest.raises(SystemExit, match="Refusing to write synthetic results"):
        evalcommon.parse(["--kind", "synthetic", "--labels", str(EVAL / "synthetic" / "labels.csv"),
                          "--out", str(EVAL / out)], default_labels="labels.csv", out_name=out)


def test_real_runs_need_real_labels():
    with pytest.raises(SystemExit, match="--kind real expects labels"):
        evalcommon.parse(["--labels", str(EVAL / "synthetic" / "labels.csv")], default_labels="labels.csv", out_name="x.json")


def test_label_validation_errors_are_readable(tmp_path):
    _png(tmp_path / "photos" / "a.jpg")
    f = tmp_path / "labels.csv"
    f.write_text("image_path,brand,strength,expiry,condition\nphotos/a.jpg,Napa,500 mg,03/27,glare\n"
                 "photos/missing.jpg,,5 mg,,blurry\n", encoding="utf-8")
    rows = evalcommon.read_rows(f, ("image_path", "brand"))
    with pytest.raises(evalcommon.LabelError) as e:
        evalcommon.check_strip_rows(rows, tmp_path)
    msg = str(e.value)
    assert "line 2: expiry '03/27' is not YYYY-MM" in msg and "line 3: image not found: photos/missing.jpg" in msg
    assert "line 3: brand is empty" in msg and "condition 'blurry'" in msg
    (tmp_path / "bad.csv").write_text("path,brand\n", encoding="utf-8")
    with pytest.raises(evalcommon.LabelError, match="missing column"):
        evalcommon.read_rows(tmp_path / "bad.csv", ("image_path", "brand"))


def test_bp_validation(tmp_path):
    _png(tmp_path / "bp_photos" / "a.jpg")
    f = tmp_path / "bp_labels.csv"
    f.write_text("image_path,systolic,diastolic,pulse\nbp_photos/a.jpg,140,,7x\n", encoding="utf-8")
    with pytest.raises(evalcommon.LabelError) as e:
        evalcommon.check_bp_rows(evalcommon.read_rows(f, ("image_path", "systolic", "diastolic", "pulse")), tmp_path)
    assert "diastolic is empty" in str(e.value) and "pulse '7x' is not a whole number" in str(e.value)


def test_synthetic_strip_run_end_to_end(tmp_path, monkeypatch):
    run_eval = _load("run_eval")
    from app.agent import ExtractedItem, ScanOutcome, ScannedItem
    from app.models import MedicineItemIn

    synth = tmp_path / "synthetic"
    for i in range(3):
        _png(synth / "photos" / f"p{i}.jpg")
    (synth / "labels.csv").write_text("image_path,brand,strength,expiry,condition\n" + "".join(
        f"photos/p{i}.jpg,Napa,500 mg,,clear\n" for i in range(3)), encoding="utf-8")
    seen = []

    async def fake_read(photos):
        seen.append(photos[0])
        it = MedicineItemIn(brand="Napa", strength="500 mg", confidence=0.95)
        return ScanOutcome(items=[ScannedItem(item=it, match={})], model_id="mock")

    monkeypatch.setattr(run_eval.agent, "read_shelf", fake_read)
    assert ExtractedItem  # the real types are used, only the call is mocked
    out = synth / "results.json"
    code = asyncio.run(run_eval.main(["--kind", "synthetic", "--labels", str(synth / "labels.csv"), "--out", str(out)]))
    assert code == 0 and len(seen) == 3
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["kind"] == "synthetic" and r["n_photos"] == 3 and r["status"] == "synthetic benchmark"
    assert r["brand_accuracy"] == 1.0                     # 3 photos: no MIN_PHOTOS gate for synthetic
    assert "not real-photo accuracy" in r["label"]["en"] and r["label"]["bn"]


def test_real_run_keeps_the_photo_minimum(tmp_path, monkeypatch):
    run_eval = _load("run_eval")
    from app.agent import ScanOutcome, ScannedItem
    from app.models import MedicineItemIn

    monkeypatch.setattr(evalcommon, "EVAL", tmp_path)
    _png(tmp_path / "photos" / "p.jpg")
    (tmp_path / "labels.csv").write_text("image_path,brand\nphotos/p.jpg,Napa\n", encoding="utf-8")

    async def fake_read(photos):
        return ScanOutcome(items=[ScannedItem(item=MedicineItemIn(brand="Napa", confidence=0.9), match={})], model_id="m")

    monkeypatch.setattr(run_eval.agent, "read_shelf", fake_read)
    out = tmp_path / "results_x.json"
    assert asyncio.run(run_eval.main(["--labels", str(tmp_path / "labels.csv"), "--out", str(out)])) == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["kind"] == "real" and r["brand_accuracy"] is None and r["status"].startswith("evaluation in progress (n = 1")
    assert "label" not in r


def test_synthetic_bp_run(tmp_path, monkeypatch):
    run_bp = _load("run_bp_eval")
    synth = tmp_path / "synthetic"
    _png(synth / "bp_photos" / "a.jpg")
    (synth / "bp_labels.csv").write_text("image_path,systolic,diastolic,pulse\nbp_photos/a.jpg,140,90,72\n", encoding="utf-8")
    monkeypatch.setattr(run_bp, "Router", lambda: None)
    monkeypatch.setattr(run_bp, "read_bp_photo",
                        lambda photo, router: {"systolic": 140, "diastolic": 90, "pulse": 70, "needs_check": False})
    out = synth / "bp.json"
    assert run_bp.main(["--kind", "synthetic", "--labels", str(synth / "bp_labels.csv"), "--out", str(out)]) == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["kind"] == "synthetic" and r["n_photos"] == 1 and r["systolic_accuracy"] == 1.0 and r["pulse_accuracy"] == 0.0
