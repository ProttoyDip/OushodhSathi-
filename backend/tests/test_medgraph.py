"""Medicine knowledge graph + Graph RAG case summary. The graph explains; rules.py decides."""
import json
from datetime import date

from app import clinical, medgraph
from app.models import MedicineItem, Patient, RuleItem, StoredFlag
from app.rules import run_rules
from app.tables import load_rule_tables
from tests.test_clinical import TOKEN, FakeRouter, add, household


def test_graph_counts_and_every_edge_has_a_source():
    c = medgraph.counts()
    assert c["nodes"]["Brand"] >= 20 and c["nodes"]["Generic"] >= 20 and c["nodes"]["ClassGroup"] == 3
    g = medgraph.graph()
    assert all(d.get("source") for _, _, d in g.edges(data=True))
    assert {d["type"] for _, _, d in g.edges(data=True)} >= {"CONTAINS", "IN_CLASS", "IN_GROUP", "INTERACTS",
                                                            "FLAGGED_BY", "CITED_BY"}


def test_combination_brand_expands_to_each_generic():
    g = medgraph.graph()
    contains = {g.nodes[b]["label"] for _, b, d in g.out_edges("Brand:osartil plus", data=True) if d["type"] == "CONTAINS"}
    assert contains == {"losartan", "hydrochlorothiazide"}


def test_triple_whammy_path_is_found():
    paths = medgraph.path_for(["Osartil Plus", "Clofenac"], [], "TRIPLE_WHAMMY")
    groups = {s["node"] for line in paths for s in line if s["type"] == "ClassGroup"}
    assert groups == {"raas", "diuretic", "nsaid"}
    assert all(s.get("source") for line in paths for s in line[1:])


def test_rules_are_identical_with_or_without_the_graph(monkeypatch):
    items = [RuleItem(id=1, brand="Osartil Plus", generic="losartan + hydrochlorothiazide", drug_class="ARB + thiazide diuretic"),
             RuleItem(id=2, brand="Clofenac", generic="diclofenac", drug_class="NSAID"),
             RuleItem(id=3, brand="Napa", generic="paracetamol"), RuleItem(id=4, brand="Ace", generic="paracetamol")]
    before = run_rules(items, 70, load_rule_tables(), date(2026, 11, 1))
    medgraph.graph()  # build and cache it
    after = run_rules(items, 70, load_rule_tables(), date(2026, 11, 1))
    assert [f.model_dump() for f in before] == [f.model_dump() for f in after]
    import app.rules as rules
    assert "medgraph" not in vars(rules)


def test_facts_are_numbered_and_sourced():
    facts = medgraph.facts_for(["losartan", "diclofenac"])
    assert facts and [f["id"] for f in facts] == [f"F{i}" for i in range(1, len(facts) + 1)]
    assert all(f["source"] for f in facts)
    assert medgraph.facts_for(["not-a-medicine"]) == []


def test_persist_writes_a_snapshot(store):
    c = medgraph.persist(store)
    assert store._all("SELECT COUNT(*) AS n FROM kg_nodes")[0]["n"] == sum(c["nodes"].values())
    medgraph.persist(store)  # idempotent: replaced, not appended
    assert store._all("SELECT COUNT(*) AS n FROM kg_edges")[0]["n"] == sum(c["edges"].values())


# ---- Graph RAG summary ---------------------------------------------------------------------

PATIENT = Patient(id=1, name="Rahima Begum", age=70, created_at="2026-10-01T00:00:00+00:00")
ITEMS = [MedicineItem(id=1, patient_id=1, brand="Osartil Plus", generic="losartan + hydrochlorothiazide", prescriber="Dr A"),
         MedicineItem(id=2, patient_id=1, brand="Clofenac", generic="diclofenac", prescriber="Drug shop")]
FLAG = StoredFlag(id=9, patient_id=1, key="k", code="TRIPLE_WHAMMY", severity="red", item_ids=[1, 2],
                  evidence="ARB + thiazide + NSAID", routed_to="doctor", data_source="Medsafe",
                  created_at="2026-10-01T00:00:00+00:00")


def _graph_summary(summary, questions=()):
    return json.dumps({"summary": list(summary), "prescribers": [{"name": "Dr A", "medicines": ["Osartil Plus"]}],
                       "questions_to_check": list(questions)})


def test_validator_drops_uncited_sentences():
    kept, dropped = clinical.keep_cited(["Cited. [F1]", "No id here.", "Unknown id. [F99]", "Two ids. [F1] [R1]"],
                                        {"F1", "R1"})
    assert kept == ["Cited. [F1]", "Two ids. [F1] [R1]"] and dropped == 2


def test_graph_summary_keeps_only_cited_lines_and_never_sends_the_name():
    router = FakeRouter(_graph_summary(["Osartil Plus and Clofenac form the triple-whammy combination. [R1] [F1]",
                                        "This sentence has no citation."],
                                       ["Does Dr A know about the Clofenac? [R1]"]))
    out = clinical.case_summary_graph(PATIENT, ITEMS, [FLAG], router)
    assert out["summary"] and out["summary"]["summary"] == ["Osartil Plus and Clofenac form the triple-whammy combination. [R1] [F1]"]
    assert out["uncited_dropped"] == 1 and out["prompt_version"].endswith("v2")
    assert [f["id"] for f in out["facts"]] == ["F1"]
    assert "Rahima" not in json.dumps(router.calls)


def test_graph_summary_falls_back_to_v1():
    # every sentence uncited -> no summary (the endpoint then uses v1); advice is still rejected
    def v2(text):
        return clinical.case_summary_graph(PATIENT, ITEMS, [FLAG], FakeRouter(text))
    assert v2(_graph_summary(["No ids."]))["dropped"] == "no summary sentence cited a fact"
    assert v2(_graph_summary(["The patient should stop Clofenac. [R1]"]))["summary"] is None
    assert v2(None)["summary"] is None


def test_why_endpoint_is_reviewer_only(client):
    pid = household(client)
    add(client, pid, "Osartil Plus", prescriber="a")
    add(client, pid, "Clofenac", prescriber="b")
    client.post(f"/patients/{pid}/check")
    flags = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()
    tw = next(f for f in flags if f["code"] == "TRIPLE_WHAMMY")
    assert client.get(f"/flags/{tw['id']}/why").status_code == 401
    r = client.get(f"/flags/{tw['id']}/why", headers=TOKEN).json()
    assert {s["node"] for line in r["paths"] for s in line if s["type"] == "ClassGroup"} == {"raas", "diuretic", "nsaid"}
