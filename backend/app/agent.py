"""The shelf agent (Pydantic-AI): medicine photos in, typed medicine items out.

The agent reads photos and may call match_brand, lookup_unknown_brand and the
read-only check_medicines tool. It can never write flags: flags are only created by
rules.py when POST /patients/{id}/check runs on items a human has confirmed.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_ai import Agent, BinaryContent, RunContext
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from . import prompts
from .brands import match_brand as _match_brand
from .llm_router import NoProviderAvailable, Provider, Router, configured_providers, parse_json
from .models import MedicineItemIn, RuleItem
from .research import lookup_unknown_brand as _lookup
from .rules import run_rules
from .tables import load_rule_tables

log = logging.getLogger("oushodh.agent")

_YM = re.compile(r"^(\d{4})-(\d{1,2})")


class ExtractedItem(BaseModel):
    brand: str = Field(min_length=1)
    strength: str = ""
    form: str = ""
    expiry: str | None = None
    source: Literal["strip", "box", "prescription"] = "strip"
    prescriber: str | None = None
    confidence: float = Field(ge=0, le=1)

    @field_validator("expiry", mode="before")
    @classmethod
    def _expiry(cls, v: Any) -> str | None:
        if v in (None, "", "null", "None"):
            return None
        m = _YM.match(str(v).strip())
        if not m or not 1 <= int(m.group(2)) <= 12:
            return None  # unreadable expiry is dropped, never guessed
        return f"{m.group(1)}-{int(m.group(2)):02d}"

    @field_validator("prescriber", mode="before")
    @classmethod
    def _prescriber(cls, v: Any) -> str | None:
        return None if v in (None, "", "null", "None") else str(v)


class Extraction(BaseModel):
    items: list[ExtractedItem]


@dataclass
class ShelfDeps:
    store: Any = None
    age: int | None = None


@dataclass
class ScannedItem:
    item: MedicineItemIn
    match: dict
    thumbnail: str | None = None  # short-lived data URL, never stored


@dataclass
class ScanOutcome:
    items: list[ScannedItem] = field(default_factory=list)
    model_id: str | None = None
    provider: str | None = None
    needs_review: bool = False
    warnings: list[str] = field(default_factory=list)


# ---- brand resolution (shared with manual add) ---------------------------------------

def resolve_brand(brand: str, strength: str | None, store=None) -> dict:
    """match_brand -> if not found, web lookup (web_unverified). Returns item match fields."""
    m = _match_brand(brand)
    if m.row is not None:
        return {"generic": m.generic, "drug_class": m.drug_class or None, "match_method": m.match_method,
                "match_score": m.match_score, "match_source": m.source}
    found = _lookup(brand, strength, store=store)
    if found:
        return {"generic": found["generic"], "drug_class": found.get("drug_class"),
                "match_method": "web_unverified", "match_score": None, "match_source": found["source_url"]}
    return {"generic": None, "drug_class": None, "match_method": "not_found", "match_score": None,
            "match_source": None}


# ---- image helpers ----------------------------------------------------------------------

def _prepare(photo: bytes, max_side: int) -> tuple[bytes, str]:
    """Downscale in memory (fewer tokens, smaller payload). Returns (jpeg bytes, media type)."""
    try:
        from PIL import Image, ImageOps
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(photo))).convert("RGB")
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80 if max_side > 400 else 65)
        return buf.getvalue(), "image/jpeg"
    except Exception:  # not an image Pillow understands: send as-is
        return photo, "image/jpeg"


def thumbnail(photo: bytes) -> str:
    data, mt = _prepare(photo, 320)
    return f"data:{mt};base64,{base64.b64encode(data).decode()}"


# ---- the agent ------------------------------------------------------------------------

def build_agent(model) -> Agent[ShelfDeps, Extraction]:
    agent = Agent(
        model,
        output_type=Extraction,
        instructions=prompts.load("extract_strip"),
        deps_type=ShelfDeps,
        retries=1,  # one automatic retry on invalid output
        name="shelf_agent",
    )

    @agent.tool_plain
    def match_brand(brand: str) -> dict:
        """Look up a Bangladeshi brand name in the local brand table. Returns the generic or not_found."""
        m = _match_brand(brand)
        return {"brand": brand, "generic": m.generic, "match_method": m.match_method}

    @agent.tool
    def lookup_unknown_brand(ctx: RunContext[ShelfDeps], brand: str, strength: str = "") -> dict | None:
        """Search Bangladeshi medicine sites for a brand not in the local table. Result is unverified."""
        return _lookup(brand, strength, store=ctx.deps.store)

    @agent.tool
    def check_medicines(ctx: RunContext[ShelfDeps], brands: list[str]) -> list[dict]:
        """Read-only preview of rule findings for a list of brands. Does not create or save flags."""
        items = []
        for i, b in enumerate(brands):
            m = _match_brand(b)
            items.append(RuleItem(id=i, brand=b, generic=m.generic, drug_class=m.drug_class))
        flags = run_rules(items, ctx.deps.age, load_rule_tables(), date.today())
        return [{"code": f.code, "severity": f.severity, "brands": [brands[i] for i in f.item_ids]} for f in flags]

    return agent


def _pydantic_ai_model(providers: list[Provider]):
    models = [OpenAIChatModel(p.model, provider=OpenAIProvider(base_url=p.base_url, api_key=p.api_key))
              for p in providers]
    return models[0] if len(models) == 1 else FallbackModel(*models)


def _salvage(raw: str) -> list[ExtractedItem]:
    """Keep whatever items validate from a bad output, forced to low confidence."""
    try:
        data = parse_json(raw)
    except ValueError:
        return []
    out = []
    for x in data.get("items", []) if isinstance(data, dict) else []:
        try:
            item = ExtractedItem.model_validate({**x, "confidence": 0.3} if isinstance(x, dict) else x)
            out.append(item)
        except ValidationError:
            continue
    return out


def _extract_plain(router: Router, image: bytes, media_type: str) -> tuple[list[ExtractedItem], str, str, bool]:
    """Fallback for models without tool calling: plain JSON via the router.
    One retry on invalid output, then salvage and mark needs_review."""
    url = f"data:{media_type};base64,{base64.b64encode(image).decode()}"
    messages: list[dict] = [
        {"role": "system", "content": prompts.load("extract_strip")},
        {"role": "user", "content": [
            {"type": "text", "text": "Read every medicine in this photo."},
            {"type": "image_url", "image_url": {"url": url}},
        ]},
    ]
    result = router.chat("vision", messages, json_mode=True)
    try:
        return Extraction.model_validate(parse_json(result.text)).items, result.provider, result.model, False
    except (ValueError, ValidationError) as e:
        retry = messages + [
            {"role": "assistant", "content": result.text},
            {"role": "user", "content": f"That was not valid. Error: {str(e)[:300]}. Return ONLY the JSON object."},
        ]
        result = router.chat("vision", retry, json_mode=True)
        try:
            return Extraction.model_validate(parse_json(result.text)).items, result.provider, result.model, False
        except (ValueError, ValidationError):
            return _salvage(result.text), result.provider, result.model, True


async def _extract_one(photo: bytes, providers: list[Provider], router: Router, deps: ShelfDeps
                       ) -> tuple[list[ExtractedItem], str | None, str | None, bool]:
    image, media_type = _prepare(photo, 1600)
    store = deps.store
    key = "extract:" + hashlib.sha256(
        json.dumps([prompts.version("extract_strip"), [p.model for p in providers]]).encode() + image
    ).hexdigest()
    if store is not None and (hit := store.cache_get(key)):
        cached = json.loads(hit)
        return [ExtractedItem(**x) for x in cached["items"]], cached["provider"], cached["model"], False

    items: list[ExtractedItem] = []
    provider = model_id = None
    needs_review = False
    try:
        agent = build_agent(_pydantic_ai_model(providers))
        result = await agent.run(
            ["Read every medicine in this photo.", BinaryContent(data=image, media_type=media_type)],
            deps=deps,
        )
        items = result.output.items
        model_id = getattr(result.response, "model_name", None) or providers[0].model
        provider = "pydantic-ai"
    except Exception as e:  # tool calling unsupported, output invalid after its retry, provider errors
        log.info("agent path failed (%s); using plain router extraction", type(e).__name__)
        items, provider, model_id, needs_review = await asyncio.to_thread(_extract_plain, router, image, media_type)

    if store is not None and not needs_review:
        store.cache_set(key, json.dumps({"items": [i.model_dump() for i in items],
                                         "provider": provider, "model": model_id}))
    return items, provider, model_id, needs_review


async def read_shelf(photos: list[bytes], store=None, age: int | None = None,
                     router: Router | None = None) -> ScanOutcome:
    """Photos are held in memory only for this call (AGENTS.md rule 6)."""
    providers = configured_providers("vision")
    if not providers:
        raise NoProviderAvailable("no vision provider configured")
    router = router or Router(store=store)
    deps = ShelfDeps(store=store, age=age)
    outcome = ScanOutcome()
    results = await asyncio.gather(*(_extract_one(p, providers, router, deps) for p in photos),
                                   return_exceptions=True)
    seen: dict[tuple, ScannedItem] = {}
    for photo, res in zip(photos, results):
        if isinstance(res, BaseException):
            outcome.warnings.append(f"one photo could not be read ({type(res).__name__})")
            continue
        items, provider, model_id, needs_review = res
        outcome.provider = outcome.provider or provider
        outcome.model_id = outcome.model_id or model_id
        outcome.needs_review |= needs_review
        # AGENTS.md rule 6: only strip and box photos get a small thumbnail (for the family to
        # compare against the strip, kept in their browser only). A photo with a prescription
        # in it can show the patient's name, so it gets none.
        has_prescription = any(x.source == "prescription" for x in items)
        thumb = thumbnail(photo) if items and not has_prescription else None
        for x in items:
            dedupe = (x.brand.lower(), x.strength.lower(), x.expiry, (x.prescriber or "").lower())
            if dedupe in seen and seen[dedupe].item.confidence >= x.confidence:
                continue
            match = await asyncio.to_thread(resolve_brand, x.brand, x.strength, store)
            match.update(prompt_version=prompts.version("extract_strip"), model_id=model_id)
            seen[dedupe] = ScannedItem(
                item=MedicineItemIn(brand=x.brand, strength=x.strength or None, form=x.form or None,
                                    expiry=x.expiry, prescriber=x.prescriber, source=x.source,
                                    confidence=x.confidence),
                match=match, thumbnail=thumb if x.source in ("strip", "box") else None,
            )
    outcome.items = list(seen.values())
    return outcome
