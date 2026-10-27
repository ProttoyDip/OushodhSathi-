"""Prompt registry: name -> active version file. Changing a prompt means adding a new
version file, pointing ACTIVE at it, and re-running eval/run_eval.py."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent

ACTIVE: dict[str, str] = {
    "extract_strip": "extract_strip.v1.md",
    "brand_lookup": "brand_lookup.v1.md",
    "explain_bn": "explain_bn.v1.md",
    "sathi_bn": "sathi_bn.v1.md",
    "sathi_nextstep": "sathi_nextstep.v1.md",
    "sathi_intent": "sathi_intent.v1.md",
    "case_summary": "case_summary.v1.md",
    "read_bp": "read_bp.v1.md",
}


def version(name: str) -> str:
    """e.g. "extract_strip.v1" """
    return ACTIVE[name].removesuffix(".md")


@lru_cache(maxsize=None)
def load(name: str) -> str:
    return (PROMPT_DIR / ACTIVE[name]).read_text(encoding="utf-8").strip()
