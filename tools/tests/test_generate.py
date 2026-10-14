# tools/tests/test_generate.py
from pathlib import Path
import json
import shutil
import sys
import pytest
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
import make_probe_log
from hsi.ledger import load_ledger
from hsi.measurement import parse_lines, extract, start_snapshot, monthly_snapshots
from hsi import generate, hashes

FIX = Path(__file__).parent / "fixtures"
CFG = {"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3, "fixture_slices": [], "rule": "very_low"}

def setup_repo(tmp_path, **log_kw):
    repo = tmp_path / "repo"
    (repo / "research").mkdir(parents=True)
    for n in ("acts.csv", "goals.csv", "goal_states.csv"):
        shutil.copy(FIX / "ledger_ok" / n, repo / "research" / n)
    m = repo / "research" / "measurement" / "2026-01-01-run-test"; m.mkdir(parents=True)
    make_probe_log.write(m / "debug.log", **log_kw)
    (m / "engine.txt").write_text('"rawVersion": "1.14.5"\n')
    (m / "probe-config.json").write_text(json.dumps(CFG))
    (repo / "common" / "scripted_effects").mkdir(parents=True)
    (repo / "README.md").write_text("# T\n\n<!-- hsi:table:start -->\nold\n<!-- hsi:table:end -->\n", encoding="utf-8")
    game = tmp_path / "game"
    for rel in ("common/script_values/00_infamy_values.txt", "common/defines/00_defines.txt",
                "common/script_values/00_diplomacy_values.txt", "common/game_rules/00_game_rules.txt",
                "common/country_ranks/00_country_ranks.txt",
                "common/war_goal_types/03_conquer_state.txt", "common/country_definitions/00_countries.txt"):
        p = game / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(f"stub {rel}\n")
    (game / "common/country_definitions/00_countries.txt").write_text("EGY = {\n}\nGBR = {\n}\nTUR = {\n}\nGRE = {\n}\nHDJ = {\n}\nBOL = {\n}\nFRA = {\n}\n")
    (game / "common/game_rules/00_game_rules.txt").write_text("infamy_generation = {\n\tinfamy_generation_very_low = { flag = infamy_generation_very_low }\n\tinfamy_generation_low = { flag = infamy_generation_low }\n\tinfamy_generation_standard = { }\n\tinfamy_generation_high = { flag = infamy_generation_high }\n\tinfamy_generation_very_high = { flag = infamy_generation_very_high }\n}\n")
    return repo, game, m

def snapshot(m):
    return start_snapshot(parse_lines(extract(m / "debug.log")))

def test_diagnostic_check_passes_on_consistent_fixture(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    for s in monthly_snapshots(parse_lines(extract(m / "debug.log"))):
        assert generate.diagnostic_check(led, s) == []

def test_diagnostic_check_runs_on_every_sample_and_uses_the_record_operands(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    snaps = monthly_snapshots(parse_lines(extract(m / "debug.log")))
    assert [s.sample for s in snaps] == [1, 2, 3]
    snaps[0].diag[("EGY", "STATE_ALEPPO", "EGY")]["siv"] += 0.5
    assert any("STATE_ALEPPO" in p for p in generate.diagnostic_check(led, snaps[0]))
    snaps[2].slices[("STATE_ALEPPO", "EGY")]["pop_share_uncapped"] += 0.3       # the sampler's record, not the DIAG operand
    snaps[2].countries["GBR"]["unrec_mult"] = -0.4                              # likewise the sampler's COUNTRY modifier
    assert generate.diagnostic_check(led, snaps[2]) == []
    snaps[1].diag[("GBR", "STATE_HEDJAZ", "HDJ")]["unrec_mult"] = -0.4           # the record's own modifier is what the gate uses
    assert any("HEDJAZ" in p for p in generate.diagnostic_check(led, snaps[1]))

def expected_standard_egy():
    """Hand derivation from the synthetic day-one sample (make_probe_log: pop 1.9+0.1i, gdp 1.1+0.05i, i = slice index)
    and the fixture ledger; ranks EGY unrecognized major (+0.50 as aggressor), TUR major (+0.10 as target), the pending
    goal's absent target falls back to unrecognized_power (-0.50)."""
    aleppo = (5 + 1.9 + 1.10) * 1.5 * 0.85 * 0.9          # homeland standing, shared language, adjacent; EGY is unrecognized: no unrec factor
    syria = (5 + 2.0 + 1.15) * 1.0 * 0.85 * 0.9           # incorporated standing
    hedjaz = (5 + 2.3 + 1.30) * 2.0 * 0.85 * 0.9          # capital standing
    k_vs_tur = 1 + 0.5 + 0.1
    k_vs_absent = 1 + 0.5 - 0.5
    c_aleppo = aleppo * 1.0 * 0.95 * k_vs_tur             # conquer_state: severity 1, no clamp, general -5 %, rank block, rule 1
    c_syria = syria * 1.0 * 0.95 * k_vs_tur
    c_pending = hedjaz * 0.5 * 0.95 * k_vs_absent         # make_protectorate severity 0.5
    decay_1831_to_1835_11 = 5 * 1492 / 365.25
    decay_61 = 5 * 61 / 365.25
    bal = max(0.0, c_aleppo + c_syria - decay_1831_to_1835_11) + c_pending
    return max(0.0, bal - decay_61), (c_aleppo, c_syria, c_pending)

def test_compute_tables_hand_checked_whole_numbers(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    tables, rows = generate.compute_tables(led, snapshot(m))
    finished, (c_aleppo, c_syria, c_pending) = expected_standard_egy()
    assert finished == pytest.approx(8.421, abs=0.01)
    assert tables["standard"] == {"EGY": 8}
    charges = {r["goal_id"]: r for r in rows if r["kind"] == "charge" and r["rule"] == "standard"}
    assert charges["g_aleppo"]["value"] == pytest.approx(c_aleppo) and charges["g_syria"]["value"] == pytest.approx(c_syria)
    assert charges["g_pending"]["value"] == pytest.approx(c_pending)
    assert charges["g_aleppo"]["holder_rank"] == "unrecognized_major_power" and charges["g_aleppo"]["target_rank"] == "major_power"
    assert charges["g_pending"]["target_rank"] == "unrecognized_power"            # absent target: declared fallback
    assert charges["g_aleppo"]["after_K"] == pytest.approx(charges["g_aleppo"]["after_G"] * 1.6)
    # the other rules scale every charge; the floor of 1 and the decay are the only non-linearities
    assert tables["very_low"] == {"EGY": 2} and tables["low"] == {"EGY": 4}
    assert tables["high"] == {"EGY": 16} and tables["very_high"] == {"EGY": 23}
    comps = [r for r in rows if r["kind"] == "component" and r["goal_id"] == "g_greece"]
    assert [c["component_id"] for c in comps] == ["c1", "c2"] and comps[0]["slices"] == "STATE_ATTICA/GRE"
    assert comps[0]["base"] == pytest.approx(5 + 2.1 + 1.2) and comps[0]["value"] == pytest.approx(8.3)
    assert sum(c["value"] for c in comps) == pytest.approx(charges["g_greece"]["component_subtotal"])
    assert charges["g_greece"]["raw"] == pytest.approx(charges["g_greece"]["component_subtotal"] * charges["g_greece"]["subject_mult"])
    assert charges["g_aleppo"]["holder_rank_source"] == "measured" and charges["g_aleppo"]["target_rank_source"] == "measured"
    assert charges["g_pending"]["target_rank_source"] == "fallback-absent"
    aleppo_c = [r for r in rows if r["kind"] == "component" and r["goal_id"] == "g_aleppo"][0]
    assert "homeland x1.5" in aleppo_c["standing"] and "shared_languagex0.85" in aleppo_c["factors"] and "adjacentx0.9" in aleppo_c["factors"]
    kinds = {(r["actor"], r["kind"]) for r in rows}
    assert ("TUR", "reduction") in kinds and ("EGY", "accrual") in kinds
    assert all("BOL" != r["actor"] or r["kind"] != "emit" for r in rows)
    assert "GBR" not in tables["standard"]                                        # 1827 liberation decayed to nothing

def test_present_but_unmeasured_target_is_labelled_not_called_absent(tmp_path):
    # final review F5: a tag the boot did not log gets the fallback rank but the derivation says so
    repo, game, m = setup_repo(tmp_path)
    text = (repo / "research" / "goals.csv").read_text()
    text = text.replace("g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,,", "g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,HDJ,")
    (repo / "research" / "goals.csv").write_text(text)
    led = load_ledger(repo / "research")
    assert generate.rank_sources(led.goals["g_pending"], led, snapshot(m)) == ("measured", "fallback-unmeasured")
    tables, rows = generate.compute_tables(led, snapshot(m))
    assert tables["standard"] == {"EGY": 8}                                      # same fallback rank, same number, labelled honestly

def test_emission_thresholds_and_rounds_to_whole_numbers():
    assert generate.emitted_value("EGY", 0.49) is None
    assert generate.emitted_value("EGY", 0.5) == 1
    assert generate.emitted_value("EGY", 8.421) == 8
    assert generate.emitted_value("EGY", 8.5) == 9
    assert generate.emitted_value("BOL", 50.0) is None            # computed, never emitted
    assert generate.emitted_value("actor:Mehmet", 9.0) is None    # no 1836 tag

def test_render_effect_shape():
    tables = {"standard": {"EGY": 8}, "very_low": {}, "low": {"EGY": 4}, "high": {"EGY": 16}, "very_high": {"EGY": 23}}
    text = generate.render_effect(tables, {"EGY": ["g_pending"]}, "# HSI-HASH x y\n")
    assert text.startswith("# GENERATED")
    assert "limit = { NOT = { has_global_variable = hsi_applied } }" in text
    assert "else = { hsi_table_standard = yes }" in text
    assert "hsi_table_very_low = {\n}" in text
    assert "c:EGY ?= { change_infamy = 8 }   # g_pending" in text
    assert "set_global_variable = hsi_applied" in text
    assert "infamy_generation_standard" not in text

def test_main_end_to_end_writes_outputs(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    rc = generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m)])
    assert rc == 0
    eff = (repo / "common" / "scripted_effects" / "zz_hsi_effects.txt").read_bytes()
    assert eff.startswith(b"\xef\xbb\xbf")
    header = hashes.parse_header(eff.decode("utf-8-sig"))
    assert "ledger/goals.csv" in header and "vanilla/common/defines/00_defines.txt" in header
    assert "vanilla/common/country_ranks/00_country_ranks.txt" in header
    assert "generator/generate.py" in header and "measurement/debug.log" in header and header["order"] == "SCGKRF"
    tables = json.loads((repo / "research" / "tables.json").read_text())
    assert tables["standard"]["EGY"] == 8
    readme = (repo / "README.md").read_text()
    assert "| EGY | 2 | 4 | 8 | 16 | 23 |" in readme and "old" not in readme
    deriv = (repo / "research" / "derivation.csv").read_text()
    assert "after_K" in deriv.splitlines()[0] and "unrecognized_major_power" in deriv and ",component," in deriv

def test_main_tolerates_an_incomplete_last_month_but_not_a_broken_formula(tmp_path):
    # ruling 2026-10-14: the day-one sample is the input; monthly samples feed oracle A and may be short
    repo, game, m = setup_repo(tmp_path)
    text = (m / "debug.log").read_text()
    (m / "debug.log").write_text("\n".join(l for l in text.splitlines() if "HSI;monthly;3;" not in l or "HEDJAZ" not in l) + "\n")
    assert generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m)]) == 0
    import re
    bad = re.sub(r"(HSI;monthly;1;February 1, 1836;DIAG;EGY/STATE_ALEPPO/EGY;.*;siv=)[0-9.]+", r"\g<1>99.0000", text, count=1)
    assert bad != text
    (m / "debug.log").write_text(bad)
    assert generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m)]) == 1
    (m / "debug.log").write_text("\n".join(l for l in text.splitlines() if "HSI;start_b;" not in l) + "\n")
    assert generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m)]) == 1
