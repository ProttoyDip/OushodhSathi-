"""Strip-reading eval scoring and the labelling tool. No photos, no models: pure functions."""
import csv
import importlib.util
from pathlib import Path

from app.agent import ExtractedItem

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run_eval = _load("run_eval", ROOT / "eval" / "run_eval.py")
labeller = _load("label_photos", ROOT / "backend" / "scripts" / "label_photos.py")


def item(brand, strength="", expiry=None, confidence=0.9):
    return ExtractedItem(brand=brand, strength=strength, expiry=expiry, confidence=confidence)


LABELS = {
    "photos/a.jpg": [{"image_path": "photos/a.jpg", "brand": "Napa", "strength": "500 mg", "expiry": "2027-03", "condition": "cut_strip"},
                     {"image_path": "photos/a.jpg", "brand": "Seclo", "strength": "20 mg", "expiry": "", "condition": "cut_strip"}],
    "photos/b.jpg": [{"image_path": "photos/b.jpg", "brand": "Camlodin", "strength": "5 mg", "expiry": "2026-12", "condition": "bangla"}],
}


def test_score_counts_brand_strength_expiry_and_needs_check():
    outputs = {"photos/a.jpg": [item("NAPA", "500mg", "2027-03", 0.95), item("Seclo", "40 mg", None, 0.6),
                                item("Ace", "", None, 0.8)],          # Ace is not in the photo
               "photos/b.jpg": []}                                     # Camlodin missed
    r = run_eval.score(LABELS, outputs)
    assert (r["brand"]["k"], r["brand"]["n"]) == (2, 3)
    assert (r["strength"]["k"], r["strength"]["n"]) == (1, 3)         # Seclo strength wrong
    assert (r["expiry"]["k"], r["expiry"]["n"]) == (1, 2)             # only rows with a labelled expiry
    assert (r["needs_check"]["k"], r["needs_check"]["n"]) == (1, 2)   # Seclo at 0.6 < 0.75
    assert r["by_condition"]["cut_strip"]["k"] == 2 and r["by_condition"]["bangla"]["k"] == 0
    assert r["per_image"][0]["extra_items"] == ["Ace"]
    rel = {b["confidence"]: b for b in r["reliability"]}
    assert rel["0.75-0.90"]["observed"]["k"] == 0 and rel["0.75-0.90"]["items"] == 1   # Ace: confident and wrong
    assert rel["0.90-1.00"]["observed"]["k"] == 1
    assert 0 <= r["brand"]["ci_low"] <= r["brand"]["p"] <= r["brand"]["ci_high"] <= 1


def test_score_with_nothing_read():
    r = run_eval.score(LABELS, {})
    assert r["brand"]["k"] == 0 and r["needs_check"] is None and r["avg_confidence"] is None


def test_labeller_needs_the_privacy_tick_and_valid_expiry():
    form = {"brand0": ["Napa"], "strength0": ["500 mg"], "expiry0": ["2027-03"], "condition": ["glare"]}
    rows, errors = labeller.validate(form, "photos/x.jpg")
    assert errors == ["Tick the privacy checklist first."]
    rows, errors = labeller.validate({**form, "private": ["1"]}, "photos/x.jpg")
    assert not errors and rows == [{"image_path": "photos/x.jpg", "brand": "Napa", "strength": "500 mg",
                                    "expiry": "2027-03", "condition": "glare"}]
    _, errors = labeller.validate({**form, "private": ["1"], "expiry0": ["03/27"]}, "photos/x.jpg")
    assert any("YYYY-MM" in e for e in errors)
    _, errors = labeller.validate({"private": ["1"], "condition": ["clear"]}, "photos/x.jpg")
    assert any("at least one brand" in e for e in errors)


def test_labeller_upgrades_an_old_labels_file(tmp_path, monkeypatch):
    f = tmp_path / "labels.csv"
    f.write_text("image_path,brand,strength\nphotos/old.jpg,Napa,500 mg\n", encoding="utf-8")
    monkeypatch.setattr(labeller, "LABELS", f)
    labeller.append([{"image_path": "photos/new.jpg", "brand": "Seclo", "strength": "20 mg", "expiry": "", "condition": "clear"}])
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    assert [r["image_path"] for r in rows] == ["photos/old.jpg", "photos/new.jpg"]
    assert rows[0]["expiry"] == "" and rows[1]["condition"] == "clear"
    assert run_eval.load_labels(f)["photos/new.jpg"][0]["brand"] == "Seclo"


def test_docs_endpoint_hides_numbers_below_the_photo_minimum(client, tmp_path, monkeypatch):
    import json

    from app import main
    chain = run_eval.score(LABELS, {"photos/a.jpg": [item("Napa", "500 mg", "2027-03")]})
    for status in ("evaluation in progress (n = 2 photos; 25 needed)", "measured"):
        (tmp_path / "results_extract_strip.v1.json").write_text(json.dumps(
            {"prompt_version": "extract_strip.v1", "images": 2, "labelled_items": 3, "status": status,
             "brand_accuracy": None, "runs": {"chain": chain}}), encoding="utf-8")
        monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
        row = client.get("/eval/results").json()[0]
        if status == "measured":
            assert row["brand_accuracy"] == chain["brand"]["p"] and len(row["brand_accuracy_ci"]) == 2
        else:
            assert row["brand_accuracy"] is None and row["needs_check_rate"] is None
            assert "brand_accuracy_ci" not in row and row["status"].startswith("evaluation in progress")


def test_score_measures_the_second_reader_gain():
    outputs = {"photos/a.jpg": [item("Napa", "50 mg", "2027-03", 0.95), item("Seclo", "20 mg", None, 0.9)],
               "photos/b.jpg": [item("Camlodin", "5 mg", "2026-12", 0.9)]}
    seconds = {"photos/a.jpg": [{"strength": "disagree", "expiry": "agree"}, {"strength": "agree", "expiry": "unknown"}],
               "photos/b.jpg": [{"strength": "disagree", "expiry": "agree"}]}   # Camlodin right, flagged anyway
    sr = run_eval.score(LABELS, outputs, seconds)["second_read"]
    assert (sr["strength"]["catch"]["k"], sr["strength"]["catch"]["n"]) == (1, 1)            # Napa 50 vs 500 caught
    assert (sr["strength"]["false_alarm"]["k"], sr["strength"]["false_alarm"]["n"]) == (1, 2)
    assert sr["expiry"]["catch"] is None and sr["expiry"]["false_alarm"]["n"] == 2
    assert sr["ran_on_items"] == 3 and sr["needs_check_with_second_read"]["k"] == 2
    assert run_eval.score(LABELS, outputs)["second_read"]["ran_on_items"] == 0              # OCR off: nothing claimed


def test_brand_alternatives_in_either_script_and_strength_only_where_labelled():
    labels = {"photos/s.jpg": [{"image_path": "photos/s.jpg", "brand": "Nasovap|ন্যাসোভ্যাপ", "strength": "", "condition": "bangla"}],
              "photos/t.jpg": [{"image_path": "photos/t.jpg", "brand": "Napa", "strength": "500 mg", "condition": "clear"}]}
    outputs = {"photos/s.jpg": [item("ন্যাসোভ্যাপ", "100 ml")], "photos/t.jpg": [item("Napa", "500 mg")]}
    r = run_eval.score(labels, outputs)
    assert (r["brand"]["k"], r["brand"]["n"]) == (2, 2)          # the Bangla read of Nasovap counts
    assert (r["strength"]["k"], r["strength"]["n"]) == (1, 1)    # the syrup's volume is not scored as a strength
    assert r["per_image"][0]["extra_items"] == []
    assert run_eval.score(labels, {"photos/s.jpg": [item("Nasovap")]})["brand"]["k"] == 1


def test_labeller_prefills_drafts_but_still_needs_the_privacy_tick(tmp_path):
    f = tmp_path / "drafts.csv"
    f.write_text("image_path,brand,strength,expiry,condition\nphotos/x.jpg,Napa,500 mg,,glare\n", encoding="utf-8")
    labeller.DRAFTS.clear()
    labeller.DRAFTS.update(labeller.load_drafts(f))
    try:
        h = labeller.page("photos/x.jpg", 1)
        assert 'value="Napa"' in h and 'value="500 mg"' in h and "<option selected>glare" in h and "Pre-filled" in h
        assert "Pre-filled" not in labeller.page("photos/other.jpg", 1)
        _, errors = labeller.validate({"brand0": ["Napa"], "condition": ["glare"]}, "photos/x.jpg")
        assert errors == ["Tick the privacy checklist first."]
    finally:
        labeller.DRAFTS.clear()
