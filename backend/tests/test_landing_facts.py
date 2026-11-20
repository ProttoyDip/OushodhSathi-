"""The landing page prints numbers from committed JSON files; they must match the data and eval results."""
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gen_landing_facts.py"


def test_brand_facts_json_is_current():
    spec = importlib.util.spec_from_file_location("gen_landing_facts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert json.loads(mod.OUT.read_text(encoding="utf-8")) == mod.facts(), "run backend/scripts/gen_landing_facts.py"


def test_evidence_json_is_current():
    spec = importlib.util.spec_from_file_location("gen_landing_facts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert json.loads(mod.EVIDENCE_OUT.read_text(encoding="utf-8")) == mod.evidence(), "run backend/scripts/gen_landing_facts.py"


def test_landing_check_in_texts_match_what_is_sent():
    from app.voice_calls.script import PROMPTS
    from app.whatsapp_checkin import flow

    page = (Path(__file__).resolve().parents[2] / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    for text in (flow.DAILY, *flow.TEMPLATE_BUTTONS, PROMPTS["slot_morning"]["bn"]):
        assert f'"{text}"' in page, text
