"""A second reader for the small print: a dedicated OCR model re-reads each photo, and the strength and
expiry the vision model extracted are checked against what the OCR saw. A disagreement marks the item
"please check" for a human. It never changes what was read and never creates a finding.

Provider: NVIDIA NIM for Image OCR, hosted.
  Request/response format: https://docs.nvidia.com/nim/ingestion/image-ocr/latest/use-the-api.html
    POST {"input": [{"type": "image_url", "url": "data:image/jpeg;base64,..."}]}
    -> {"data": [{"index": 0, "text_detections": [{"text_prediction": {"text", "confidence"}, "bounding_box"}]}]}
  Hosted URL for nvidia/nemotron-ocr-v2 (the model named in that page's example response) and for
  baidu/paddleocr (https://docs.nvidia.com/rag/2.6.0/nemoretriever-ocr.html lists
  https://ai.api.nvidia.com/v1/cv/baidu/paddleocr); both verified with a test image on 2026-11-18.
The photo is the same one already sent to the vision model; the OCR text itself is never stored or logged:
only the strengths and dates it contains are kept, with the verdict.
"""
from __future__ import annotations

import base64
import logging
import os
import re
from dataclasses import dataclass

import httpx

log = logging.getLogger("oushodh.ocr")

ENDPOINTS = (
    ("nvidia/nemotron-ocr-v2", "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"),
    ("baidu/paddleocr", "https://ai.api.nvidia.com/v1/cv/baidu/paddleocr"),
)
TIMEOUT_S = 15
MIN_CONFIDENCE = 0.6  # OCR lines below this are ignored rather than trusted

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_UNIT = {"mg": "mg", "mcg": "mcg", "µg": "mcg", "μg": "mcg", "ug": "mcg", "g": "g", "gm": "g", "ml": "ml",
         "iu": "iu", "%": "%"}
_STRENGTH = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|μg|ug|gm|g|ml|iu|%)(?![a-z])", re.I)
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DATE = re.compile(
    r"(?<!\d)(?P<m>0?[1-9]|1[0-2])\s*[/\-.]\s*(?P<y>20\d{2}|\d{2})(?!\d)"          # 03/2027, 3-27, 03.2027
    r"|(?P<mon>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*[/\-.]?\s*(?P<y2>20\d{2}|\d{2})(?!\d)"
    r"|(?<!\d)(?P<y3>20\d{2})\s*[/\-.]\s*(?P<m3>0?[1-9]|1[0-2])(?!\d)",            # 2027-03
    re.I)
_EXP = re.compile(r"\b(exp|expiry|expires|use\s*before|ব্যবহারের\s*শেষ|মেয়াদ)", re.I)


class OcrUnavailable(RuntimeError):
    pass


def configured() -> bool:
    if os.getenv("OCR_CHECK_DISABLED", "").strip().lower() in ("1", "true", "yes"):
        return False
    allowed = os.getenv("VISION_PROVIDERS", "").strip().lower()
    private = os.getenv("PRIVATE_VISION", "").strip().lower() in ("1", "true", "yes")
    if private and allowed and "nvidia" not in allowed.split(","):
        return False  # a family's photo goes only to the providers they were promised
    return bool(os.getenv("NVIDIA_API_KEY", "").strip())


def read_lines(image_jpeg: bytes, client: httpx.Client | None = None) -> tuple[list[str], str]:
    """-> (text lines with confidence >= MIN_CONFIDENCE, model id). Tries each endpoint in turn."""
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not key:
        raise OcrUnavailable("no NVIDIA_API_KEY")
    body = {"input": [{"type": "image_url", "url": "data:image/jpeg;base64," + base64.b64encode(image_jpeg).decode()}]}
    c = client or httpx.Client(timeout=TIMEOUT_S)
    errors = []
    for model, url in ENDPOINTS:
        try:
            r = c.post(url, json=body, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
            r.raise_for_status()
            dets = r.json()["data"][0]["text_detections"]
            return [d["text_prediction"]["text"] for d in dets
                    if d.get("text_prediction", {}).get("confidence", 0) >= MIN_CONFIDENCE], model
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            errors.append(f"{model}: {type(e).__name__}")
    raise OcrUnavailable("; ".join(errors))


def strengths_in(text: str) -> set[tuple[float, str]]:
    out = set()
    for num, unit in _STRENGTH.findall(text.translate(_BN_DIGITS)):
        out.add((float(num.replace(",", ".")), _UNIT[unit.lower()]))
    return out


def _year(y: str) -> int:
    return int(y) if len(y) == 4 else 2000 + int(y)


def dates_in(text: str) -> set[str]:
    """Every month-year in the text as YYYY-MM."""
    out = set()
    for m in _DATE.finditer(text.translate(_BN_DIGITS)):
        if m.group("m"):
            month, year = int(m.group("m")), _year(m.group("y"))
        elif m.group("mon"):
            month, year = _MONTHS[m.group("mon").lower()[:3]], _year(m.group("y2"))
        else:
            month, year = int(m.group("m3")), _year(m.group("y3"))
        if 2000 <= year <= 2099:
            out.add(f"{year:04d}-{month:02d}")
    return out


def expiry_dates(lines: list[str]) -> set[str]:
    """Dates on lines that say EXP (and the line after a lone EXP label); every date if no line says EXP."""
    marked = set()
    for i, line in enumerate(lines):
        if _EXP.search(line):
            marked |= dates_in(line)
            if not dates_in(line) and i + 1 < len(lines):
                marked |= dates_in(lines[i + 1])
    return marked or set().union(*(dates_in(x) for x in lines)) if lines else set()


@dataclass
class SecondRead:
    strength: str        # agree | disagree | unknown
    expiry: str          # agree | disagree | unknown
    model: str
    seen_strengths: list[str]
    seen_expiries: list[str]

    @property
    def disagrees(self) -> bool:
        return "disagree" in (self.strength, self.expiry)

    def to_dict(self) -> dict:
        return {"strength": self.strength, "expiry": self.expiry, "model": self.model,
                "seen_strengths": self.seen_strengths, "seen_expiries": self.seen_expiries}


def compare(strength: str | None, expiry: str | None, lines: list[str], model: str) -> SecondRead:
    """Agree when everything the vision model read is also in the OCR text; disagree when the OCR found
    strengths (or expiry dates) and none of them match; unknown when the OCR found none."""
    seen_s = strengths_in(" ".join(lines))
    seen_e = expiry_dates(lines)
    want_s = strengths_in(strength or "")
    if not want_s or not seen_s:
        s_verdict = "unknown"
    else:
        s_verdict = "agree" if want_s <= seen_s else "disagree"
    if not expiry or not seen_e:
        e_verdict = "unknown"
    else:
        e_verdict = "agree" if expiry in seen_e else "disagree"
    fmt = lambda v, u: f"{v:g} {u}"  # noqa: E731
    return SecondRead(s_verdict, e_verdict, model, sorted(fmt(v, u) for v, u in seen_s), sorted(seen_e))
