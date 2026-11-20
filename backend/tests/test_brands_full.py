"""The full Bangladesh brand list (data/brands_full.csv, from "Medicinal Products in Bangladesh", CC BY 4.0).
Skipped when the file is absent. The rest of the suite runs on the curated seed (see conftest.py)."""
from pathlib import Path

import pytest

from app import brand_suggest, brands, tables

FULL = Path(__file__).resolve().parent.parent / "data" / "brands_full.csv"
pytestmark = pytest.mark.skipif(not FULL.exists(), reason="data/brands_full.csv not present")

CACHES = [c for c in (tables.load_brands, brands._index, brands._bn_index, brand_suggest._names) if hasattr(c, "cache_clear")]


@pytest.fixture
def full_list(monkeypatch):
    monkeypatch.setenv("OUSHODH_BRANDS", "full")
    for c in CACHES:
        c.cache_clear()
    yield
    monkeypatch.setenv("OUSHODH_BRANDS", "seed")
    for c in CACHES:
        c.cache_clear()


def test_brands_missing_from_the_seed_now_match(full_list):
    m = brands.match_brand("Rupadin")
    assert m.row is not None and m.row.generic == "rupatadine fumarate"
    assert not m.row.verified  # dataset rows are never shown as pharmacist-verified


def test_the_curated_seed_still_wins(full_list):
    # the antibiotic and safety rules key on the seed's drug classes
    for name in ("Napa", "Zimax", "Seclo"):
        assert brands.match_brand(name).row.source_file == "brands_seed.csv"


def test_a_misread_suggests_the_real_brand_and_nothing_unrelated(full_list):
    out = [s["brand"] for s in brand_suggest.suggest("Rupain")]
    assert "Rupadin" in out and "Tryptin" not in out


def test_every_dataset_row_is_unverified_and_names_a_generic():
    import csv

    with FULL.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(line for line in f if not line.lstrip().startswith("#")))
    assert len(rows) > 10_000
    assert all(r["verified"].strip().lower() not in ("yes", "true", "1") for r in rows)
    assert all(r["generic"].strip() for r in rows)
