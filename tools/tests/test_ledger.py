# tools/tests/test_ledger.py
from datetime import date
from pathlib import Path
import shutil
import pytest
from hsi.ledger import load_ledger, validate_ledger, LedgerError, load_vanilla_tags

FIX = Path(__file__).parent / "fixtures" / "ledger_ok"
TAGS = {"EGY", "GBR", "TUR", "GRE", "HDJ", "BOL", "FRA", "RUS"}

def copy_fixture(tmp_path):
    d = tmp_path / "research"
    shutil.copytree(FIX, d)
    return d

def mutate(d, name, old, new):
    p = d / name
    s = p.read_text(encoding="utf-8")
    assert old in s, old
    p.write_text(s.replace(old, new), encoding="utf-8")

def test_load_ok_and_types():
    led = load_ledger(FIX)
    assert set(led.goals) == {"g_aleppo", "g_syria", "g_greece", "g_pending"}
    g = led.goals["g_aleppo"]
    assert g.claim_date == date(1831, 10, 1) and g.resolution_date == date(1833, 5, 1)
    assert led.goals["g_pending"].resolution_date is None
    assert led.components_of("g_greece")[1].state_key == "STATE_PELOPONNESE"
    assert ("STATE_HEDJAZ", "HDJ") in led.all_slices()
    assert led.holder_tags() == {"EGY", "GBR"}
    validate_ledger(led, TAGS)

def test_bom_crlf_and_padded_cells_load_identically(tmp_path):
    d = copy_fixture(tmp_path)
    for name in ("acts.csv", "goals.csv", "goal_states.csv"):
        p = d / name
        text = p.read_text(encoding="utf-8").replace("\n", "\r\n").replace(",EGY,", ", EGY ,")
        p.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    led = load_ledger(d)
    assert led.goals["g_aleppo"].holder == "EGY"
    validate_ledger(led, TAGS)

def test_header_mismatch_refused(tmp_path):
    d = copy_fixture(tmp_path)
    mutate(d, "goals.csv", "goal_id,act_id,", "goal_id,act,")
    with pytest.raises(LedgerError) as e:
        load_ledger(d)
    assert "header" in " ".join(e.value.messages)

@pytest.mark.parametrize("name,old,new,needle", [
    ("goals.csv", "g_syria,test_syria,conquer_state", "g_aleppo,test_syria,conquer_state", "duplicate"),
    ("goals.csv", "g_greece,test_greece,", "g_greece,no_such_act,", "orphan"),
    ("goal_states.csv", "g_pending,c1,", "g_ghost,c1,", "orphan"),
    ("goals.csv", "conquer_state,EGY,EGY,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "liberate_subject,EGY,EGY,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "wargoal"),
    ("goals.csv", "EGY,EGY,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "EGY,XXX,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "tag"),
    ("goals.csv", "1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "1815-12-31,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "window"),
    ("goals.csv", "1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "1831-10-01,enforced,1831-09-30,0,0,measured_1836,fixture\ng_syria", "before"),
    ("goals.csv", "1835-11-01,pending,,0,0", "1835-11-01,pending,1836-02-01,0,0", "pending"),
    ("goals.csv", "1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture\ng_syria", "1831-10-01,enforced,,0,0,measured_1836,fixture\ng_syria", "date"),
    ("goal_states.csv", "g_aleppo,c1,STATE_ALEPPO,EGY,recognized,homeland,0,1,0,0,1,3", "g_aleppo,c1,STATE_ALEPPO,EGY,recognized,homeland,0,1,1,0,1,3", "claim"),
    ("goal_states.csv", "g_greece,c2,STATE_PELOPONNESE,GRE", "g_greece,c2,STATE_PELOPONNESE,GRE;GRE", "slice"),
    ("goal_states.csv", "g_greece,c2,STATE_PELOPONNESE,GRE", "g_greece,c2,STATE_ATTICA,GRE", "slice"),
    ("goal_states.csv", ",0,1,0,0,1,3,fixture\ng_syria", ",0,1,0,0,1,7,fixture\ng_syria", "interest"),
    ("goals.csv", "g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,,1835-11-01,pending,,0,0,measured_1836,fixture pending goal", "g_pending,test_syria,make_protectorate,EGY,,unrecognized,HDJ,TUR,,1835-11-01,pending,,0,0,measured_1836,fixture pending goal", "general_mult_source"),
    # the other direction (review R1 finding L1): a holder that exists in 1836 may not opt into the absent-actor fallback
    ("goals.csv", "g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,,1835-11-01,pending,,0,0,measured_1836,fixture pending goal", "g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,,1835-11-01,pending,,0,0,none,fixture pending goal", "requires general_mult_source measured_1836"),
])
def test_refusals(tmp_path, name, old, new, needle):
    d = copy_fixture(tmp_path)
    mutate(d, name, old, new)
    with pytest.raises(LedgerError) as e:
        validate_ledger(load_ledger(d), TAGS)
    assert needle in " ".join(e.value.messages).lower()

def test_conquer_state_needs_exactly_one_component(tmp_path):
    d = copy_fixture(tmp_path)
    (d / "goal_states.csv").open("a", encoding="utf-8").write("g_syria,c2,STATE_LEBANON,EGY,recognized,incorporated,0,1,0,0,1,3,extra\n")
    with pytest.raises(LedgerError) as e:
        validate_ledger(load_ledger(d), TAGS)
    assert "exactly one component" in " ".join(e.value.messages)

def test_load_vanilla_tags(tmp_path):
    g = tmp_path / "game" / "common" / "country_definitions"
    g.mkdir(parents=True)
    (g / "00_countries.txt").write_text("﻿GBR = {\n\tcolor = x\n}\nEGY = {\n}\nnot_a_tag = {\n}\n", encoding="utf-8")
    assert load_vanilla_tags(tmp_path / "game") == {"GBR", "EGY"}
