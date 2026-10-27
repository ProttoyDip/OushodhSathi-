"""lookup_unknown_brand: find the generic of a brand that is not in our tables.

Tavily search restricted to Bangladeshi medicine sites -> LLM (brand_lookup prompt)
reads ONLY those numbered snippets and must cite one -> if unknown, the Perplexity
Agent API with citations. Results are always stored as match_method "web_unverified" with the
source URL, and shown as needing human confirmation. Successes are cached; failures never.
"""
from __future__ import annotations

import json
import logging

import httpx

from . import prompts
from .llm_router import NoProviderAvailable, Router, _env, parse_json
from .tables import class_for_generic

log = logging.getLogger("oushodh.research")

DOMAINS = ["medex.com.bd", "arogga.com", "medeasy.health"]
TAVILY_URL = "https://api.tavily.com/search"
PERPLEXITY_URL = "https://api.perplexity.ai/v1/agent"  # Agent API (Sonar chat completions were retired)


def _clean_generic(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    g = value.strip().lower()
    return None if not g or g == "unknown" else g


def _result(generic: str, url: str, via: str) -> dict:
    return {
        "generic": generic,
        "drug_class": class_for_generic(generic) if "+" not in generic else None,
        "source_url": url,
        "match_method": "web_unverified",
        "via": via,
    }


def _tavily(query: str, client: httpx.Client) -> list[dict]:
    key = _env("TAVILY_API_KEY")
    if not key:
        return []
    r = client.post(TAVILY_URL, headers={"Authorization": f"Bearer {key}"},
                    json={"query": query, "include_domains": DOMAINS, "max_results": 5})
    r.raise_for_status()
    return [x for x in r.json().get("results", []) if x.get("url")]


def _from_snippets(brand: str, strength: str, results: list[dict], router: Router) -> dict | None:
    numbered = "\n\n".join(
        f"[{i}] {x.get('title', '')}\nURL: {x['url']}\n{(x.get('content') or '')[:800]}"
        for i, x in enumerate(results, 1)
    )
    messages = [
        {"role": "system", "content": prompts.load("brand_lookup")},
        {"role": "user", "content": f"Brand: {brand}\nStrength: {strength or 'not given'}\n\nSearch results:\n{numbered}"},
    ]
    out = parse_json(router.chat("text", messages, json_mode=True).text)
    generic, idx = _clean_generic(out.get("generic")), out.get("source_index")
    if generic and isinstance(idx, int) and 1 <= idx <= len(results):
        return _result(generic, results[idx - 1]["url"], "tavily")
    return None


def _perplexity_answer(data: dict) -> tuple[str, list[str]]:
    """Agent API response -> (answer text, cited URLs in result order)."""
    text, urls = "", []
    for item in data.get("output", []):
        if item.get("type") == "message":
            text += "".join(c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text")
        elif item.get("type") == "search_results":
            urls += [r["url"] for r in item.get("results", []) if r.get("url")]
    return text, urls


def _perplexity(brand: str, strength: str, client: httpx.Client) -> dict | None:
    key = _env("PERPLEXITY_API_KEY")
    if not key:
        return None
    body = {
        "effort": _env("PERPLEXITY_EFFORT") or "fast",  # "fast" is the old Sonar tier
        "input": prompts.load("brand_lookup")
        + "\nThe numbered search results are your citations; source_index refers to them."
        + f"\n\nBrand: {brand}\nStrength: {strength or 'not given'}",
        "tools": [{"type": "web_search", "filters": {"search_domain_filter": DOMAINS}}],
    }
    r = client.post(PERPLEXITY_URL, headers={"Authorization": f"Bearer {key}"}, json=body)
    r.raise_for_status()
    text, citations = _perplexity_answer(r.json())
    out = parse_json(text)
    generic, idx = _clean_generic(out.get("generic")), out.get("source_index")
    if generic and isinstance(idx, int) and 1 <= idx <= len(citations):
        return _result(generic, citations[idx - 1], "perplexity")
    return None


def lookup_unknown_brand(brand: str, strength: str | None, store=None, router: Router | None = None,
                         client: httpx.Client | None = None) -> dict | None:
    """Returns {"generic", "drug_class", "source_url", "match_method": "web_unverified", "via"} or None."""
    if not (_env("TAVILY_API_KEY") or _env("PERPLEXITY_API_KEY")):
        return None
    strength = strength or ""
    cache_key = "lookup:" + json.dumps([brand.lower().strip(), strength.lower().strip()])
    if store is not None and (hit := store.cache_get(cache_key)):
        return json.loads(hit)
    client = client or httpx.Client(timeout=30)
    router = router or Router(store=store, client=client)
    found = None
    try:
        results = _tavily(f"{brand} {strength} generic name Bangladesh", client)
        if results:
            found = _from_snippets(brand, strength, results, router)
    except (httpx.HTTPError, ValueError, KeyError, NoProviderAvailable) as e:
        log.warning("tavily lookup failed: %s", type(e).__name__)
    if found is None:
        try:
            found = _perplexity(brand, strength, client)
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as e:
            log.warning("perplexity lookup failed: %s", type(e).__name__)
    if found and store is not None:
        store.cache_set(cache_key, json.dumps(found))  # cache successes only
    return found

