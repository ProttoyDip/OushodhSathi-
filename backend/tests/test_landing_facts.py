"""The landing page prints brand-table numbers from a committed JSON; it must match the data."""
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gen_landing_facts.py"


def test_brand_facts_json_is_current():
    spec = importlib.util.spec_from_file_location("gen_landing_facts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert json.loads(mod.OUT.read_text(encoding="utf-8")) == mod.facts(), "run backend/scripts/gen_landing_facts.py"
