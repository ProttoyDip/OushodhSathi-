"""The OCR second reader: parsing the small print, the verdict, and its place in a scan. No network."""
import asyncio
import json

import httpx
import pytest

from app import agent, ocr_check
from app.agent import ExtractedItem
from app.llm_router import Provider
from app.models import MedicineItem


def test_strengths_and_dates_are_parsed():
    assert ocr_check.strengths_in("Napa 500mg · 12.5 MG · ৫০ mg · 0,5 g") == {(500, "mg"), (12.5, "mg"), (50, "mg"), (0.5, "g")}
    assert ocr_check.strengths_in("500 mgx") == set()  # unit must end there
    assert ocr_check.dates_in("EXP 03/2027 MFG 3-25 Exp.: JAN 2028 2029-11") == {"2027-03", "2025-03", "2028-01", "2029-11"}
    assert ocr_check.dates_in("Batch 1234 · 13/2027") == set()


def test_expiry_prefers_lines_marked_exp():
    lines = ["MFG 02/2025", "EXP 01/2027"]
    assert ocr_check.expiry_dates(lines) == {"2027-01"}
    assert ocr_check.expiry_dates(["EXP:", "04/2027", "MFG 05/2025"]) == {"2027-04"}
    assert ocr_check.expiry_dates(["02/2025", "01/2027"]) == {"2025-02", "2027-01"}  # no label: every date


@pytest.mark.parametrize("strength,expiry,lines,verdict", [
    ("500 mg", "2027-03", ["Napa 500 mg", "EXP 03/2027"], ("agree", "agree")),
    ("50 mg", "2027-03", ["Napa 500 mg", "EXP 03/2027"], ("disagree", "agree")),
    ("500 mg", "2026-03", ["Napa 500 mg", "EXP 03/2027"], ("agree", "disagree")),
    ("50 mg + 12.5 mg", None, ["Losartan 50 mg", "HCTZ 12.5 mg"], ("agree", "unknown")),
    ("500 mg", "2027-03", ["Napa"], ("unknown", "unknown")),         # OCR saw nothing to compare: no flag
    (None, None, ["Napa 500 mg", "EXP 03/2027"], ("unknown", "unknown")),
])
def test_compare(strength, expiry, lines, verdict):
    r = ocr_check.compare(strength, expiry, lines, "m")
    assert (r.strength, r.expiry) == verdict
    assert r.disagrees == ("disagree" in verdict)


def test_read_lines_uses_the_documented_format_and_falls_back(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(str(req.url))
        body = json.loads(req.content)
        assert body["input"][0]["type"] == "image_url" and body["input"][0]["url"].startswith("data:image/jpeg;base64,")
        if "nemotron" in str(req.url):
            return httpx.Response(503)
        return httpx.Response(200, json={"data": [{"index": 0, "text_detections": [
            {"text_prediction": {"text": "Napa 500 mg", "confidence": 0.99}},
            {"text_prediction": {"text": "smudge", "confidence": 0.2}}]}]})

    lines, model = ocr_check.read_lines(b"jpeg", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert lines == ["Napa 500 mg"] and model == "baidu/paddleocr" and len(seen) == 2


def test_configured_respects_private_vision(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    assert ocr_check.configured()
    monkeypatch.setenv("PRIVATE_VISION", "true")
    monkeypatch.setenv("VISION_PROVIDERS", "ollama")
    assert not ocr_check.configured()
    monkeypatch.setenv("VISION_PROVIDERS", "nvidia,ollama")
    assert ocr_check.configured()
    monkeypatch.setenv("OCR_CHECK_DISABLED", "1")
    assert not ocr_check.configured()


def test_a_disagreement_marks_the_scanned_item_for_a_human(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setattr(agent, "configured_providers", lambda task: [Provider("nvidia", "u", "k", "m")])

    async def fake_extract(photo, providers, router, deps):
        return [ExtractedItem(brand="Napa", strength="50 mg", expiry="2027-03", confidence=0.95)], "nvidia", "m", False

    monkeypatch.setattr(agent, "_extract_one", fake_extract)
    monkeypatch.setattr(ocr_check, "read_lines", lambda img: (["Napa 500 mg", "EXP 03/2027"], "nvidia/nemotron-ocr-v2"))
    out = asyncio.run(agent.read_shelf([b"photo"]))
    sr = out.items[0].match["second_read"]
    assert sr["strength"] == "disagree" and sr["expiry"] == "agree" and sr["seen_strengths"] == ["500 mg"]
    item = MedicineItem(id=1, patient_id=1, **out.items[0].item.model_dump(), second_read=sr)
    assert item.confidence >= 0.75 and item.needs_review   # confident vision read, still sent to a human


def test_scan_works_without_the_second_reader(monkeypatch):
    monkeypatch.setattr(agent, "configured_providers", lambda task: [Provider("nvidia", "u", "k", "m")])

    async def fake_extract(photo, providers, router, deps):
        return [ExtractedItem(brand="Napa", strength="500 mg", confidence=0.95)], "nvidia", "m", False

    monkeypatch.setattr(agent, "_extract_one", fake_extract)
    out = asyncio.run(agent.read_shelf([b"photo"]))  # no NVIDIA key in tests: OCR is skipped
    assert "second_read" not in out.items[0].match


def test_second_read_is_stored_and_read_back(store):
    p = store.create_patient(__import__("app.models", fromlist=["PatientIn"]).PatientIn(name="x", age=70))
    from app.models import MedicineItemIn
    it = store.add_item(p.id, MedicineItemIn(brand="Napa", strength="50 mg", confidence=0.9),
                        second_read={"strength": "disagree", "expiry": "unknown", "model": "m",
                                     "seen_strengths": ["500 mg"], "seen_expiries": []})
    assert store.get_item(it.id).second_read["strength"] == "disagree" and store.get_item(it.id).needs_review
