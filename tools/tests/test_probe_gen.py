# tools/tests/test_probe_gen.py
from pathlib import Path
from hsi.ledger import load_ledger
from hsi.probe_gen import render, write_probe
from hsi.participants import probe_tags, probe_slices, diag_pairs
from hsi.bom import has_bom

FIX = Path(__file__).parent / "fixtures" / "ledger_ok"
CFG = {"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3, "fixture_slices": [], "rule": "very_low"}

def effect(cfg=CFG):
    return render(load_ledger(FIX), cfg)["common/scripted_effects/zz_hsi_probe_effects.txt"]

def test_render_contains_every_slice_holder_and_hook():
    files = render(load_ledger(FIX), CFG)
    eff = files["common/scripted_effects/zz_hsi_probe_effects.txt"]
    on = files["common/on_actions/zz_hsi_probe_on_actions.txt"]
    for sk, owner in [("STATE_ALEPPO", "EGY"), ("STATE_PELOPONNESE", "GRE"), ("STATE_HEDJAZ", "HDJ")]:
        assert f"s:{sk}.region_state:{owner} ?= {{" in eff
        assert f"STATE;{sk}/{owner};" in eff
    for tag in ("EGY", "GBR", "BOL", "FRA", "TUR"):            # holders, sampler, BOL, fixture holder, the ledger's victim
        assert f"COUNTRY;{tag};" in eff
    assert "DIAG;EGY/STATE_ALEPPO/EGY;root_tag=EGY;" in eff and "DIAG;GBR/STATE_ALEPPO/EGY;root_tag=GBR;" in eff
    assert "on_game_started = {\n\ton_actions = { hsi_probe_start_a }" in on
    assert "on_game_started_after_lobby = {\n\ton_actions = { hsi_probe_start_b }" in on
    assert "on_monthly_pulse_country = {\n\ton_actions = { hsi_probe_monthly }" in on
    assert "has_game_rule = infamy_generation_very_low" in eff and "flag=standard" in eff
    assert "var:hsi_sample <= 3" in eff
    assert "[TimeKeeper.GetCurrentDate.GetString]" in eff
    assert "hsi_probe_start_records_a = yes" in on and "hsi_probe_start_records_b = yes" in on

def test_every_value_goes_through_a_global_variable_and_hooks_are_literal():
    # 2026-10-14 boot: SCOPE.s*() inside debug_log resolved to nothing and $HOOK$ inside a string was mangled;
    # GetGlobalVariable(...).GetValue printed real values. The renderer may use only the proven path.
    eff = effect()
    assert "SCOPE.s" not in eff and "MakeScope" not in eff and "$HOOK$" not in eff and "$" not in eff
    assert "HSI;start_a;0;lobby;GLOBAL;-;" in eff and "HSI;start_b;0;lobby;GLOBAL;-;" in eff
    assert "HSI;start_a;0;lobby;RULE;-;flag=very_low" in eff and "HSI;start_b;0;lobby;RULE;-;flag=very_low" in eff
    state_line = next(l for l in eff.splitlines() if "HSI;start_a;0;lobby;STATE;STATE_ALEPPO/EGY;" in l)
    for f in ("owner_type", "pop", "gdp", "pop_share_uncapped", "gdp_share_uncapped", "incorporated", "capital", "owner_homeland", "base"):
        assert f"{f}=[GetGlobalVariable('hsi_g_" in state_line, f
    assert "set_global_variable = { name = hsi_g_base value = state_infamy_base }" in eff
    assert "set_global_variable = { name = hsi_g_gpop value = global_population }" in eff
    country_line = next(l for l in eff.splitlines() if "HSI;start_b;0;lobby;COUNTRY;FRA;" in l)
    assert "rank=[GetGlobalVariable('hsi_g_rank').GetValue|0]" in country_line and "gen_mult=[GetGlobalVariable('hsi_g_gen').GetValue|4]" in country_line
    assert "country_rank = rank_value:great_power } set_global_variable = { name = hsi_g_rank value = 7 }" in eff
    assert "country_rank = rank_value:unrecognized_power } set_global_variable = { name = hsi_g_rank value = 1 }" in eff
    diag = next(l for l in eff.splitlines() if "DIAG;EGY/STATE_ALEPPO/EGY;" in l)
    assert diag.count("HSI;monthly;[GetGlobalVariable('hsi_g_sample').GetValue|0];[TimeKeeper.GetCurrentDate.GetString];DIAG;") == 1
    for f in ("aggressor_homeland", "claim", "adjacent", "interest_bucket", "root_type", "owner_type", "unrec_mult", "pop_share_uncapped", "base", "siv"):
        assert f"{f}=[GetGlobalVariable('hsi_g_" in diag, f
    assert "set_global_variable = { name = hsi_g_siv value = state_infamy_value }" in eff
    assert "set_global_variable = { name = hsi_g_sample value = var:hsi_sample }" in eff
    assert "set_global_variable = { name = hsi_g_root_unrec value = hsi_probe_unrec }" in eff
    # saved scopes stay on the script side only (triggers), where they work
    assert "has_homeland = scope:hsi_state" in eff and "strategic_region = scope:hsi_region" in eff

def test_fixture_holder_and_slices_are_measured_independently_of_the_ledger():
    cfg = dict(CFG, fixture_holder="USA", fixture_slices=[["STATE_TEXAS", "MEX"], ["STATE_ALEPPO", "EGY"]])
    eff = effect(cfg)
    assert "c:USA = this" in eff and "c:BOL = this" in eff
    assert eff.count("HSI;start_a;0;lobby;STATE;STATE_TEXAS/MEX;") == 1 and eff.count("HSI;start_b;0;lobby;STATE;STATE_TEXAS/MEX;") == 1
    assert eff.count("HSI;monthly;[GetGlobalVariable('hsi_g_sample').GetValue|0];[TimeKeeper.GetCurrentDate.GetString];STATE;STATE_TEXAS/MEX;") == 1
    assert "DIAG;USA/STATE_TEXAS/MEX;root_tag=USA;" in eff and "DIAG;USA/STATE_ALEPPO/EGY;" in eff
    assert "DIAG;EGY/STATE_TEXAS/MEX;" not in eff
    assert "COUNTRY;USA;" in eff and "COUNTRY;MEX;" in eff                  # the capture target's rank is logged too
    led = load_ledger(FIX)
    assert "MEX" in probe_tags(led, cfg) and ("STATE_TEXAS", "MEX") in probe_slices(led, cfg)
    assert diag_pairs(led, cfg)["USA"] == [("STATE_ALEPPO", "EGY"), ("STATE_TEXAS", "MEX")]

def test_write_probe_writes_bom_files(tmp_path):
    paths = write_probe(tmp_path / "probe", load_ledger(FIX), CFG)
    names = {p.relative_to(tmp_path / "probe").as_posix() for p in paths}
    assert "common/scripted_effects/zz_hsi_probe_effects.txt" in names
    assert ".metadata/metadata.json" in names
    for p in paths:
        if p.suffix == ".txt":
            assert has_bom(p)
    assert (tmp_path / "probe" / ".metadata" / "metadata.json").read_text().count('"name": "HSI Probe"') == 1
