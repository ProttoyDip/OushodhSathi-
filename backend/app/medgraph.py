"""The medicine knowledge graph: a typed graph built ONLY from the existing reference tables.

It explains and retrieves; it never decides. rules.py does not import it, and run_rules gives the same
flags with or without it (tested). Uses NetworkX in memory (no graph database: the graph is a few
hundred nodes, rebuilt from the CSVs in well under a second, and free hosting has no room for Neo4j).
A snapshot is persisted to kg_nodes / kg_edges (Postgres or SQLite) so it can be inspected and exported.

Nodes  Brand, Generic, DrugClass, ClassGroup, Interaction, BeersRule, AcbScore, AwareGroup, RenalRule, Source
Edges  Brand-CONTAINS->Generic (a combination brand has several), Generic-IN_CLASS->DrugClass,
       DrugClass-IN_GROUP->ClassGroup (the triple-whammy groups), Generic/DrugClass-INTERACTS{severity}->Interaction
       (and Interaction-INTERACTS->the other side), Generic/DrugClass-FLAGGED_BY->BeersRule/RenalRule,
       Generic-ACB{score}->AcbScore, Generic-AWARE->AwareGroup, and every rule node -CITED_BY->Source.
Every edge also carries a `source` attribute naming the table row it came from.
"""
from __future__ import annotations

import json
from functools import lru_cache

import networkx as nx

from .tables import DATA_DIR, _read_csv, load_brands, load_rule_tables

BRANDS_SOURCE = "brands_seed.csv (demo seed - verify against MedEx)"


def _n(kind: str, key: str) -> str:
    return f"{kind}:{key.strip().lower()}"


def _target_node(target: str) -> tuple[str, str]:
    """A table target is a generic or "class:<drug class>"."""
    if target.startswith("class:"):
        return _n("DrugClass", target[6:]), "DrugClass"
    return _n("Generic", target), "Generic"


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    sources: dict[str, str] = {}

    def node(id_: str, kind: str, label: str, **attrs) -> str:
        if id_ not in g:
            g.add_node(id_, type=kind, label=label, **attrs)
        return id_

    def source(text: str) -> str:
        sid = sources.setdefault(text, f"Source:S{len(sources) + 1}")
        return node(sid, "Source", text)

    def edge(a: str, b: str, kind: str, src: str, **attrs) -> None:
        g.add_edge(a, b, key=kind, type=kind, source=src, **attrs)

    # brands -> generics -> classes (combination products pair by position)
    for row in load_brands().values():
        b = node(_n("Brand", row.brand), "Brand", row.brand, verified=row.verified)
        gens = list(row.generics)
        classes = [c.strip() for c in row.drug_class.split("+") if c.strip()]
        for i, gen in enumerate(gens):
            gn = node(_n("Generic", gen), "Generic", gen)
            edge(b, gn, "CONTAINS", BRANDS_SOURCE)
            cls = classes[i] if len(classes) == len(gens) else (classes[0] if len(classes) == 1 else "")
            if cls:
                cn = node(_n("DrugClass", cls), "DrugClass", cls)
                edge(gn, cn, "IN_CLASS", BRANDS_SOURCE)

    tables = load_rule_tables()
    # class groups (raas / diuretic / nsaid) for the triple whammy
    for r in _read_csv(DATA_DIR / "class_groups.csv"):
        cn = node(_n("DrugClass", r["drug_class"]), "DrugClass", r["drug_class"])
        grp = node(_n("ClassGroup", r["group"]), "ClassGroup", r["group"])
        edge(cn, grp, "IN_GROUP", r["source"])
        edge(grp, source(r["source"]), "CITED_BY", r["source"])

    for i, row in enumerate(tables.interactions):
        it = node(f"Interaction:{row.a}|{row.b}", "Interaction",
                  f"{row.a.removeprefix('class:')} + {row.b.removeprefix('class:')}",
                  severity=row.severity, effect=row.effect)
        for target in (row.a, row.b):
            tn, kind = _target_node(target)
            node(tn, kind, target.removeprefix("class:"))
            edge(tn, it, "INTERACTS", row.source, severity=row.severity)
        edge(it, source(row.source), "CITED_BY", row.source)

    beers_src = "AGS Beers Criteria (beers_seed.csv)"
    for row in tables.beers:
        rule = node(f"BeersRule:{row.target}", "BeersRule", row.target, reason=row.reason)
        tn, kind = _target_node(row.target)
        node(tn, kind, row.target.removeprefix("class:"))
        edge(tn, rule, "FLAGGED_BY", beers_src)
        edge(rule, source(beers_src), "CITED_BY", beers_src)

    for row in tables.renal:
        rule = node(f"RenalRule:{row.target}<{row.egfr_below:g}", "RenalRule", f"{row.target} eGFR < {row.egfr_below:g}",
                    severity=row.severity, note=row.note)
        tn, kind = _target_node(row.target)
        node(tn, kind, row.target.removeprefix("class:"))
        edge(tn, rule, "FLAGGED_BY", row.source)
        edge(rule, source(row.source), "CITED_BY", row.source)

    acb_path = DATA_DIR / "acb_seed.csv"
    for r in _read_csv(acb_path) if acb_path.exists() else []:
        score = node(f"AcbScore:{r['score']}", "AcbScore", f"ACB score {r['score']}")
        gn = node(_n("Generic", r["generic"]), "Generic", r["generic"].lower())
        edge(gn, score, "ACB", r["source"], score=int(r["score"]))
        edge(score, source(r["source"]), "CITED_BY", r["source"])

    aware_path = DATA_DIR / "aware_2025.csv"
    for r in _read_csv(aware_path) if aware_path.exists() else []:
        grp = node(f"AwareGroup:{r['group']}", "AwareGroup", f"WHO AWaRe {r['group']}")
        gn = node(_n("Generic", r["generic"]), "Generic", r["generic"].lower())
        edge(gn, grp, "AWARE", r["source"])
        edge(grp, source(r["source"]), "CITED_BY", r["source"])
    return g


@lru_cache(maxsize=1)
def graph() -> nx.MultiDiGraph:
    return build_graph()


def counts(g: nx.MultiDiGraph | None = None) -> dict:
    g = g or graph()
    nodes: dict[str, int] = {}
    edges: dict[str, int] = {}
    for _, d in g.nodes(data=True):
        nodes[d["type"]] = nodes.get(d["type"], 0) + 1
    for _, _, d in g.edges(data=True):
        edges[d["type"]] = edges.get(d["type"], 0) + 1
    return {"nodes": nodes, "edges": edges, "total_nodes": g.number_of_nodes(), "total_edges": g.number_of_edges()}


# ---- persistence ------------------------------------------------------------------------------

def persist(store, g: nx.MultiDiGraph | None = None) -> dict:
    """Replaces the kg_nodes / kg_edges snapshot (both databases)."""
    g = g or graph()
    store._many([
        ("CREATE TABLE IF NOT EXISTS kg_nodes (id TEXT PRIMARY KEY, type TEXT NOT NULL, label TEXT NOT NULL, "
         "attrs TEXT NOT NULL)", ()),
        ("CREATE TABLE IF NOT EXISTS kg_edges (src TEXT NOT NULL, dst TEXT NOT NULL, type TEXT NOT NULL, "
         "source TEXT NOT NULL, attrs TEXT NOT NULL)", ()),
        ("DELETE FROM kg_edges", ()),
        ("DELETE FROM kg_nodes", ()),
    ])
    rows = [("INSERT INTO kg_nodes (id, type, label, attrs) VALUES (?,?,?,?)",
             (n, d["type"], d["label"], json.dumps({k: v for k, v in d.items() if k not in ("type", "label")},
                                                   ensure_ascii=False, default=str)))
            for n, d in g.nodes(data=True)]
    rows += [("INSERT INTO kg_edges (src, dst, type, source, attrs) VALUES (?,?,?,?,?)",
              (a, b, d["type"], d["source"], json.dumps({k: v for k, v in d.items() if k not in ("type", "source")},
                                                        ensure_ascii=False, default=str)))
             for a, b, d in g.edges(data=True)]
    store._many(rows)
    return counts(g)


# ---- Graph RAG: numbered facts for the case summary ------------------------------------------

def _sentence(g: nx.MultiDiGraph, a: str, b: str, d: dict) -> str | None:
    la, lb = g.nodes[a]["label"], g.nodes[b]["label"]
    kind = d["type"]
    if kind == "CONTAINS":
        return f"The brand {la} contains {lb}."
    if kind == "IN_CLASS":
        return f"{la} is in the class {lb}."
    if kind == "IN_GROUP":
        return f"The class {la} belongs to the {lb} group used by the triple-whammy rule."
    if kind == "INTERACTS":
        node_b = g.nodes[b]  # one sentence per interaction, whichever side reaches it first
        return f"There is a {node_b.get('severity', '')} interaction between {lb}: {node_b.get('effect', '')}".strip()
    if kind == "FLAGGED_BY":
        nb = g.nodes[b]
        if nb["type"] == "BeersRule":
            return f"{la} is listed in the AGS Beers Criteria for adults 65+: {nb.get('reason', '')}".strip()
        return f"{la} has a kidney-function rule ({lb}): {nb.get('note', '')}".strip()
    if kind == "ACB":
        return f"{la} has an anticholinergic burden score of {d.get('score')}."
    if kind == "AWARE":
        return f"{la} is in the {lb} group."
    return None


def facts_for(generics: list[str], g: nx.MultiDiGraph | None = None) -> list[dict]:
    """Numbered facts ({"id": "F1", "text": ..., "source": ...}) about THIS household only: its generics,
    their classes and triple-whammy groups, and the interaction, Beers, kidney, anticholinergic and
    AWaRe rules attached to them. An interaction is included only when every side of it is on the list,
    so other medicines that merely share a class or a score never appear. Sources stay attached."""
    g = g or graph()
    seeds = {_n("Generic", x) for x in generics if _n("Generic", x) in g}
    here = seeds | {b for s in seeds for _, b, d in g.out_edges(s, data=True) if d["type"] == "IN_CLASS"}
    facts, seen = [], set()
    for a, b, d in sorted(g.out_edges(here, data=True), key=lambda e: (e[0], e[1], e[2]["type"])):
        if d["type"] == "INTERACTS":
            sides = {x for x, _, d2 in g.in_edges(b, data=True) if d2["type"] == "INTERACTS"}
            if not sides <= here:
                continue
        text = _sentence(g, a, b, d)
        if text and text not in seen:
            seen.add(text)
            facts.append({"id": f"F{len(facts) + 1}", "text": text, "source": d["source"]})
    return facts


# ---- "Why?": the graph path that explains a finding -------------------------------------------

def path_for(brands: list[str], generics: list[str], code: str, meta: dict | None = None,
             g: nx.MultiDiGraph | None = None) -> list[dict]:
    """One line per medicine: brand -> generic -> class (-> group / rule), each step with its source."""
    g = g or graph()
    meta = meta or {}
    lines = []
    for brand in brands:
        bn = _n("Brand", brand)
        if bn not in g:
            continue
        for _, gn, d in g.out_edges(bn, data=True):
            if d["type"] != "CONTAINS" or (generics and g.nodes[gn]["label"] not in generics):
                continue
            steps = [{"node": g.nodes[bn]["label"], "type": "Brand"},
                     {"node": g.nodes[gn]["label"], "type": "Generic", "via": "CONTAINS", "source": d["source"]}]
            for _, nxt, d2 in g.out_edges(gn, data=True):
                t = d2["type"]
                if t == "IN_CLASS":
                    steps.append({"node": g.nodes[nxt]["label"], "type": "DrugClass", "via": t, "source": d2["source"]})
                    for _, grp, d3 in g.out_edges(nxt, data=True):
                        if d3["type"] == "IN_GROUP" and code == "TRIPLE_WHAMMY":
                            steps.append({"node": g.nodes[grp]["label"], "type": "ClassGroup", "via": "IN_GROUP",
                                          "source": d3["source"]})
                elif (t == "ACB" and code == "ANTICHOLINERGIC_BURDEN") or (t == "AWARE" and code == "ANTIBIOTIC_NO_PRESCRIPTION") \
                        or (t == "FLAGGED_BY" and code in ("BEERS_65", "KIDNEY_DOSE")):
                    steps.append({"node": g.nodes[nxt]["label"], "type": g.nodes[nxt]["type"], "via": t,
                                  "source": d2["source"]})
            lines.append(steps)
    return lines
