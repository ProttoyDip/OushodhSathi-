"""Counterfeit awareness: a reviewer-only pack checklist and a help-guide entry. No verdicts."""
from pathlib import Path

TOKEN = {"X-Reviewer-Token": "test-token"}
HELP = Path(__file__).resolve().parents[2] / "docs" / "help"


def flagged_home(client):
    r = client.post("/patients", json={"name": "Pack Home", "age": 70, "consent": True})
    pid, h = r.json()["id"], {"X-Family-Key": r.json()["family_key"]}
    for b in ("Napa", "Ace"):
        client.post(f"/patients/{pid}/items?confirmed=true", json={"brand": b}, headers=h)
    client.post(f"/patients/{pid}/check", headers=h)
    flag = client.get(f"/patients/{pid}/flags?view=reviewer", headers=TOKEN).json()[0]
    return pid, h, flag


def test_checklist_is_stored_with_the_review_and_hidden_from_the_family(client):
    pid, h, flag = flagged_home(client)
    r = client.post(f"/flags/{flag['id']}/review", headers=TOKEN,
                    json={"status": "confirmed", "note": "ok", "checklist": ["unlicensed_seller", "pack_unusual"]})
    assert r.json()["checklist"] == ["pack_unusual", "unlicensed_seller"]
    assert client.get(f"/patients/{pid}/reviews", headers=TOKEN).json()[0]["checklist"] == '["pack_unusual", "unlicensed_seller"]'
    family = client.get(f"/patients/{pid}/flags?view=family", headers=h).json()
    assert family and all("checklist" not in f for f in family)
    for path in ("/passport", "/visit", "/export"):
        assert "pack_unusual" not in str(client.get(f"/patients/{pid}{path}", headers=h).json()), path


def test_checklist_only_takes_known_observations_and_undo_clears_it(client):
    pid, h, flag = flagged_home(client)
    bad = client.post(f"/flags/{flag['id']}/review", headers=TOKEN,
                      json={"status": "confirmed", "note": "ok", "checklist": ["fake"]})
    assert bad.status_code == 422
    client.post(f"/flags/{flag['id']}/review", headers=TOKEN,
                json={"status": "confirmed", "note": "ok", "checklist": ["pack_unusual"]})
    undone = client.post(f"/flags/{flag['id']}/undo", headers=TOKEN).json()
    assert undone["checklist"] == []


def test_no_family_flag_code_for_authenticity():
    from typing import get_args

    from app.models import FlagCode

    assert not any("FAKE" in c or "COUNTERFEIT" in c for c in get_args(FlagCode))


def test_pack_check_guide_entry_in_both_languages_never_gives_a_verdict():
    en = (HELP / "help_en.md").read_text(encoding="utf-8")
    bn = (HELP / "help_bn.md").read_text(encoding="utf-8")
    assert "## pack.check" in en and "## pack.check" in bn
    assert "not necessarily fake" in en and "does not judge" in en
    assert "কোড না থাকা মানেই নকল নয়" in bn
