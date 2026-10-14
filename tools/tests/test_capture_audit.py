# tools/tests/test_capture_audit.py
"""The capture plan's static audit (review R1 findings B1/B2). Needs the vanilla install; skipped without it."""
import importlib.util
import json
import os
from pathlib import Path
import pytest

GAME = Path(os.environ.get("HSI_GAME_DIR", Path.home() / "Library/Application Support/Steam/steamapps/common/Victoria 3/game"))
REPO = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(not (GAME / "common/history/states/00_states.txt").exists(), reason="vanilla 1.14.5 install not present")

def load_audit():
    spec = importlib.util.spec_from_file_location("capture_audit", REPO / "research/scripts/capture_audit.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope="module")
def vanilla():
    mod = load_audit()
    return mod, mod.Vanilla(GAME)

def test_the_superseded_plan_is_rejected(vanilla):
    mod, V = vanilla
    old = {"holder": "FRA", "rule": "very_low", "general_mult_estimate": -0.05, "captures": [
        {"id": "B", "role": "factor_line", "wargoal": "conquer_state",
         "candidates": [{"target": "SAR", "state": "STATE_SAVOY", "adjacent": True}, {"target": "SAR", "state": "STATE_PIEDMONT", "adjacent": True}]},
        {"id": "D", "role": "floor_binds_under_rule", "wargoal": "liberate_country",
         "candidates": [{"target": "SIC", "release": "SIC"}, {"target": "AUS", "release": "LOM"}]}]}
    rows, ok = mod.audit(old, V)
    assert ok["B"] == (False, False) and ok["D"] == (False, False)
    reasons = {(r[0], r[1]): r[4] for r in rows if r[3] == "FAIL"}
    assert "relations 30 >= cordial 20" in reasons[("B", "SAR")]
    assert "already exists as a country" in reasons[("D", "SIC")]        # Two Sicilies is SIC itself; nothing to release
    assert "relations 20 >= cordial 20" in reasons[("D", "AUS")]

def test_the_committed_plan_passes_every_required_capture(vanilla):
    mod, V = vanilla
    plan = json.loads((REPO / "research/measurement/capture-plan.json").read_text(encoding="utf-8"))
    rows, ok = mod.audit(plan, V)
    for cap, (passing, optional) in ok.items():
        assert passing or optional, (cap, [r for r in rows if r[0] == cap])
    primaries = {r[0]: r for r in reversed(rows)}       # first row per capture
    assert primaries["A"][3] == "OK" and primaries["B"][3] == "OK" and primaries["Cmin"][3] == "OK" and primaries["Cmax"][3] == "OK"

def test_truce_and_claim_refusals(vanilla):
    # review R2 finding N3: a history truce or a holder claim must fail a candidate; the runtime conditions stay visible
    mod, V = vanilla
    plan = json.loads((REPO / "research/measurement/capture-plan.json").read_text(encoding="utf-8"))
    V.truces.add(frozenset(("FRA", "MAS")))
    V.states["STATE_FLANDERS"]["claims"].append("FRA")
    try:
        rows, ok = mod.audit(plan, V)
    finally:
        V.truces.discard(frozenset(("FRA", "MAS"))); V.states["STATE_FLANDERS"]["claims"].remove("FRA")
    fails = {(r[0], r[1], r[2]): r[4] for r in rows if r[3] == "FAIL"}
    assert "truce" in fails[("A", "MAS", "")] and "truce" in fails[("B", "MAS", "STATE_ALGIERS")]
    assert "Return State" in fails[("B", "BEL", "STATE_FLANDERS")]
    assert ok["B"] == (False, False)
    rows, ok = mod.audit(plan, V)
    cmin = [r for r in rows if r[0] == "Cmin"][0]
    assert "UNVERIFIED at runtime" in cmin[4] and "ideological opinion" in cmin[4]
    assert any("activism" in r[4] for r in rows if r[0] == "D")

def test_fixture_slices_cover_every_candidate(vanilla):
    mod, V = vanilla
    plan = json.loads((REPO / "research/measurement/capture-plan.json").read_text(encoding="utf-8"))
    slices = set(map(tuple, mod.fixture_slices(plan, V)))
    assert ("STATE_ALGIERS", "MAS") in slices and ("STATE_FLANDERS", "BEL") in slices and ("STATE_EMILIA", "LUC") in slices
    assert ("STATE_WALES", "GBR") in slices and ("STATE_AUSTRIA", "AUS") in slices and ("STATE_BRANDENBURG", "PRU") in slices
    assert not any(owner == "RUS" and sk not in {"STATE_KAUNAS", "STATE_VILNIUS"} for sk, owner in slices)
    # every candidate's priced slices are logged, resolved independently of fixture_slices()
    for cap in plan["captures"]:
        for cand in cap["candidates"]:
            if cap["wargoal"] in ("make_protectorate", "regime_change"):
                for sk, _ in V.owned_slices(cand["target"]):
                    assert (sk, cand["target"]) in slices, (cap["id"], cand["target"], sk)
    cfg = json.loads((REPO / "research/probe/config.json").read_text(encoding="utf-8"))
    assert set(map(tuple, cfg["fixture_slices"])) == slices, "research/probe/config.json is stale: rerun capture_audit.py --write-config"
