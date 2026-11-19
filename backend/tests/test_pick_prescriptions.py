"""Picking real prescriptions from the Mendeley dataset (Prompt 14C): matching, the privacy gate, redaction,
the source column. Uses small made-up files; the real dataset is never needed (or committed)."""
import csv
import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pick = _load("pick_prescriptions", ROOT / "backend" / "scripts" / "pick_prescriptions.py")
run_eval = _load("run_eval", ROOT / "eval" / "run_eval.py")

SEED = ["Napa", "Napa Extra", "Seclo", "Amdocal", "Amdocal Plus", "Ace"]
BN = [("নাপা", "Napa")]


def test_continuation_rows_belong_to_the_image_above(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("image_filename,description_english,description_bangla\n0001.jpg,Tab Napa 500mg,\n,1+0+1 after food,\n"
                 "0002.jpg,Cap Seclo 20,\n,,\n", encoding="utf-8")
    t = pick.load_texts(f)
    assert t == {"0001.jpg": "Tab Napa 500mg 1+0+1 after food", "0002.jpg": "Cap Seclo 20"}


def test_brands_are_matched_as_whole_words_and_in_bangla():
    assert set(pick.find_brands("Tab. NAPA 500 mg, Cap Seclo-20", SEED, BN)) == {"Napa", "Seclo"}
    assert pick.find_brands("Napa Extra 1+1", SEED, BN) == ["Napa Extra"]          # not Napa as well
    assert pick.find_brands("Amdocal Plus 5/25", SEED, BN) == ["Amdocal Plus"]
    assert pick.find_brands("face cream, place", SEED, BN) == []                    # "ace" inside words is not Ace
    assert pick.find_brands("ট্যাব নাপা ৫০০", SEED, BN) == ["Napa"]


def test_candidates_cover_brands_before_repeating():
    texts = {f"{i:04d}.jpg": "Napa Seclo Ace" for i in range(30)}
    texts["0900.jpg"] = "Amdocal"
    texts["0901.jpg"] = "no brand here"
    c = pick.candidates(texts, SEED, BN, k=5)
    assert len(c) == 5 and "0900.jpg" in [n for n, _ in c[:2]] and "0901.jpg" not in [n for n, _ in c]


def test_privacy_tick_is_required_before_anything_is_saved():
    form = {"brand0": ["Napa"], "strength0": ["500 mg"], "rects": ["[[0.1,0.1,0.5,0.2]]"]}
    rows, rects, errors = pick.validate(form)
    assert any("privacy check" in e for e in errors)
    rows, rects, errors = pick.validate({**form, "private": ["1"]})
    assert not errors and rects == [[0.1, 0.1, 0.5, 0.2]]
    assert rows == [{"brand": "Napa", "strength": "500 mg", "expiry": "", "condition": "handwritten",
                     "source": "mendeley:tg2hm7n2bs"}]
    assert any("at least one brand" in e for e in pick.validate({"private": ["1"]})[2])
    assert any("could not be read" in e for e in pick.validate({**form, "private": ["1"], "rects": ["nope"]})[2])


def test_redaction_blacks_out_and_drops_metadata():
    from PIL import Image

    img = Image.new("RGB", (200, 100), "white")
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=Image.Exif())
    out = Image.open(io.BytesIO(pick.redact(buf.getvalue(), [[0.0, 0.0, 0.5, 0.5]])))
    assert out.getpixel((20, 20))[0] < 30 and out.getpixel((180, 80))[0] > 225
    assert not out.info.get("exif")


def test_save_writes_a_neutral_name_and_the_source_column(tmp_path):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(buf, "JPEG")
    labels = tmp_path / "labels.csv"
    labels.write_text("image_path,brand,strength,expiry,condition\nphotos/own_01.jpg,Seclo,20 mg,,clear\n", encoding="utf-8")
    rows, rects, _ = pick.validate({"brand0": ["Napa"], "strength0": ["500 mg"], "private": ["1"], "rects": ["[]"]})
    out = pick.save("0302.jpg", buf.getvalue(), rows, rects, photos=tmp_path / "photos", labels=labels)
    assert out == "rx_mendeley_01.jpg" and (tmp_path / "photos" / out).exists()
    got = list(csv.DictReader(labels.open(encoding="utf-8")))
    assert got[0]["source"] == "" and got[1]["source"] == "mendeley:tg2hm7n2bs" and got[1]["image_path"] == f"photos/{out}"
    assert pick.next_names(tmp_path / "photos", 2) == ["rx_mendeley_02.jpg", "rx_mendeley_03.jpg"]


def test_older_files_load_and_results_split_by_source(tmp_path):
    from app.agent import ExtractedItem

    old = tmp_path / "labels.csv"
    old.write_text("image_path,brand,strength,expiry,condition\nphotos/a.jpg,Napa,500 mg,,clear\n", encoding="utf-8")
    assert run_eval.load_labels(old)["photos/a.jpg"][0].get("source", "") == ""   # 5-column file still loads
    labels = {"photos/a.jpg": [{"image_path": "photos/a.jpg", "brand": "Napa", "strength": "500 mg", "condition": "clear"}],
              "photos/rx_mendeley_01.jpg": [{"image_path": "photos/rx_mendeley_01.jpg", "brand": "Seclo", "strength": "20 mg",
                                             "condition": "handwritten", "source": "mendeley:tg2hm7n2bs"}]}
    outputs = {"photos/a.jpg": [ExtractedItem(brand="Napa", strength="500 mg", confidence=0.9)], "photos/rx_mendeley_01.jpg": []}
    r = run_eval.score(labels, outputs)
    assert r["by_source"]["own"]["k"] == 1 and r["by_source"]["mendeley:tg2hm7n2bs"]["k"] == 0


def test_results_endpoint_reports_sources(client, tmp_path, monkeypatch):
    import json

    from app import main
    monkeypatch.setattr(main, "EVAL_DIR", tmp_path)
    p = {"label": "x", "k": 1, "n": 2, "p": 0.5, "ci_low": 0.1, "ci_high": 0.9}
    (tmp_path / "results_extract_strip.v1.json").write_text(json.dumps({
        "kind": "real", "status": "evaluation in progress (n = 2 photos; 25 needed)", "images": 2,
        "runs": {"chain": {"brand": p, "by_source": {"own": p, "mendeley:tg2hm7n2bs": p}}}}), encoding="utf-8")
    row = client.get("/eval/results").json()[0]
    assert row["sources"] == ["mendeley:tg2hm7n2bs", "own"] and row["brand_accuracy"] is None
