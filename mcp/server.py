"""OushodhSathi MCP server (stdio). Four read-only tools over the backend modules.

It can never write flags: check_medicines runs the deterministic rules engine and
returns findings as data; nothing is stored and nothing reaches a family.

Run:  backend/.venv/Scripts/python mcp/server.py      (Windows)
      backend/.venv/bin/python mcp/server.py          (macOS / Linux)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp_types import ToolAnnotations  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")

from app.brands import match_brand as _match_brand  # noqa: E402
from app.kidney import KidneyContext  # noqa: E402
from app import medgraph  # noqa: E402
from app.models import RuleItem  # noqa: E402
from app.research import lookup_unknown_brand as _lookup  # noqa: E402
from app.rules import run_rules  # noqa: E402
from app.tables import load_rule_tables  # noqa: E402

server = MCPServer(
    name="oushodhsathi",
    title="OushodhSathi medicine safety tools",
    instructions=(
        "Read-only tools for Bangladeshi medicine lists. match_brand maps a brand to its generic; "
        "lookup_unknown_brand searches Bangladeshi medicine sites (results are unverified); "
        "check_medicines runs the deterministic safety rules; explain_flag_path shows the knowledge-graph "
        "path (with sources) that links medicines to a rule. Findings must be confirmed by a "
        "pharmacist or doctor. Never tell a patient to stop, start or change a medicine."
    ),
    version="0.1.0",
)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


@server.tool(annotations=READ_ONLY)
def match_brand(brand: str) -> dict:
    """Map a Bangladeshi medicine brand name (e.g. "Napa 500 mg") to its generic and drug class.

    Uses exact then strict fuzzy matching; combination brands such as "Napa Extra" are never
    force-matched to "Napa".
    """
    m = _match_brand(brand)
    return {
        "brand": brand,
        "normalised": m.normalised,
        "generic": m.generic,
        "drug_class": m.drug_class or None,
        "match_method": m.match_method,
        "match_score": m.match_score,
        "source": m.source,
        "verified": bool(m.row and m.row.verified),
    }


@server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True))
def lookup_unknown_brand(brand: str, strength: str = "") -> dict:
    """Search medex.com.bd, arogga.com and medeasy.health for the generic of a brand that is not
    in the local table. The answer must cite a source and is always marked unverified.
    Needs TAVILY_API_KEY or PERPLEXITY_API_KEY in backend/.env."""
    found = _lookup(brand, strength)
    if not found:
        return {"brand": brand, "generic": None, "match_method": "not_found",
                "note": "No cited result (or no web search key configured)."}
    return {"brand": brand, **found}


class MedicineIn(BaseModel):
    brand: str
    strength: str | None = None
    expiry: str | None = Field(default=None, description="YYYY-MM as printed on the strip")
    prescriber: str | None = None


@server.tool(annotations=READ_ONLY)
def check_medicines(items: list[MedicineIn], age: int | None = None, egfr: float | None = None,
                   kidney_test_date: str | None = None) -> dict:
    """Run the deterministic safety rules (duplicate generic, same-class duplication,
    interactions, AGS Beers 65+, expiry, anticholinergic burden, look-alike names, triple whammy,
    and kidney dose when egfr / kidney_test_date (YYYY-MM-DD) are given) on a medicine list.
    Read-only: nothing is saved.
    Every finding still needs a pharmacist or doctor to confirm it."""
    rule_items, unmatched = [], []
    for i, it in enumerate(items, 1):
        m = _match_brand(it.brand)
        if m.generic is None:
            unmatched.append(it.brand)
        rule_items.append(RuleItem(id=i, brand=it.brand, generic=m.generic, drug_class=m.drug_class,
                                   strength=it.strength, expiry=it.expiry, prescriber=it.prescriber))
    kidney = None
    if egfr is not None or kidney_test_date:
        kidney = KidneyContext(egfr=egfr, taken_on=date.fromisoformat(kidney_test_date) if kidney_test_date else None)
    flags = run_rules(rule_items, age, load_rule_tables(), date.today(), kidney)
    return {
        "findings": [
            {"code": f.code, "severity": f.severity, "routed_to": f.routed_to,
             "medicines": [items[i - 1].brand for i in f.item_ids], "evidence": f.evidence,
             "data_source": f.data_source}
            for f in flags
        ],
        "not_checked": unmatched,
        "status": "pending clinician review — not for patients",
    }



@server.tool(annotations=READ_ONLY)
def explain_flag_path(generics: list[str]) -> dict:
    """Show how the given generics connect in the medicine knowledge graph: generic -> drug class ->
    class group / interaction / Beers / kidney / anticholinergic / AWaRe rule, every step with the
    table it came from. Read-only. It explains links; it does not create or change findings."""
    gens = sorted({g.strip().lower() for g in generics if g.strip()})
    g = medgraph.graph()
    known = [x for x in gens if f"Generic:{x}" in g]
    return {
        "facts": medgraph.facts_for(known),
        "unknown_generics": [x for x in gens if x not in known],
        "status": "explanation only - findings come from the rules engine and need a clinician",
    }

if __name__ == "__main__":
    server.run("stdio")
