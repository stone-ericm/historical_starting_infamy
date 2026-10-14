# tools/hsi/probe_gen.py
"""Generates the throwaway probe mod from the ledger and the probe config (spec section 6). Never shipped.

Every number reaches the log through a GLOBAL variable set in the right scope immediately before the debug_log
line, because that is the one data path the 2026-10-14 boot proved: `[GetGlobalVariable('x').GetValue|n]` printed
real values while `[SCOPE.sState('saved').MakeScope...]` resolved to nothing (every state value read 0, 1,344
NULL_STATE errors). The hook name is a literal in each string: `$HOOK$` inside a quoted string came out mangled
(`HSIstart_a$;`). Saved scopes are still used on the script side (triggers), where they do work."""
import json
from pathlib import Path
from .bom import write_text_bom
from .ledger import Ledger, load_ledger
from .participants import fixture_slices, probe_slices, probe_tags, guard_tags, diag_pairs

RANK_CODES = [   # trigger value -> code; 00_country_ranks.txt order, highest first (see constants.RANK_SCALING)
    ("great_power", 7), ("major_power", 6), ("minor_power", 5), ("insignificant_power", 4),
    ("unrecognized_major_power", 3), ("unrecognized_regional_power", 2), ("unrecognized_power", 1),
]
DATE = "[TimeKeeper.GetCurrentDate.GetString]"

def g(name: str, decimals: int) -> str:
    return f"[GetGlobalVariable('{name}').GetValue|{decimals}]"

def _flag(var: str, trigger: str) -> str:
    return (f"\tif = {{ limit = {{ {trigger} }} set_global_variable = {{ name = {var} value = 1 }} }}\n"
            f"\telse = {{ set_global_variable = {{ name = {var} value = 0 }} }}\n")

def _type_code(var: str, scope_open: str) -> str:
    """scope_open is '' (current scope), 'owner = { ' or 'root = { '; the brace is closed when one was opened."""
    close = " }" if scope_open else ""
    def t(kind):
        return f"{scope_open}is_country_type = {kind}{close}"
    return (f"\tif = {{ limit = {{ {t('decentralized')} }} set_global_variable = {{ name = {var} value = 2 }} }}\n"
            f"\telse_if = {{ limit = {{ {t('unrecognized')} }} set_global_variable = {{ name = {var} value = 1 }} }}\n"
            f"\telse = {{ set_global_variable = {{ name = {var} value = 0 }} }}\n")

def _rank_code(var: str) -> str:
    out = []
    first = True
    for rank, code in RANK_CODES:
        kw = "if" if first else "else_if"; first = False
        out.append(f"\t{kw} = {{ limit = {{ country_rank = rank_value:{rank} }} set_global_variable = {{ name = {var} value = {code} }} }}\n")
    out.append(f"\telse = {{ set_global_variable = {{ name = {var} value = 0 }} }}\n")
    return "".join(out)

STATE_FIELDS = (f"owner_type={g('hsi_g_ot', 0)};pop={g('hsi_g_pop', 0)};gdp={g('hsi_g_gdp', 2)};"
                f"pop_share_uncapped={g('hsi_g_pshare', 4)};gdp_share_uncapped={g('hsi_g_gshare', 4)};"
                f"incorporated={g('hsi_g_inc', 0)};capital={g('hsi_g_cap', 0)};owner_homeland={g('hsi_g_oh', 0)};base={g('hsi_g_base', 4)}")
COUNTRY_FIELDS = (f"country_type={g('hsi_g_ct', 0)};rank={g('hsi_g_rank', 0)};gen_mult={g('hsi_g_gen', 4)};"
                  f"unrec_mult={g('hsi_g_unrec', 4)};decay_mult={g('hsi_g_decay', 4)};infamy={g('hsi_g_infamy', 4)}")
DIAG_FIELDS = (f"aggressor_homeland={g('hsi_g_d_ah', 0)};homeland_bonus={g('hsi_g_d_ahb', 0)};shared_language={g('hsi_g_d_sl', 0)};"
               f"language_bonus={g('hsi_g_d_slb', 0)};claim={g('hsi_g_d_cl', 0)};scripted_unification={g('hsi_g_d_su', 0)};"
               f"adjacent={g('hsi_g_d_adj', 0)};interest_bucket={g('hsi_g_d_int', 0)};root_type={g('hsi_g_d_rt', 0)};"
               f"owner_type={g('hsi_g_ot', 0)};unrec_mult={g('hsi_g_root_unrec', 4)};"
               f"pop_share_uncapped={g('hsi_g_pshare', 4)};gdp_share_uncapped={g('hsi_g_gshare', 4)};"
               f"incorporated={g('hsi_g_inc', 0)};capital={g('hsi_g_cap', 0)};owner_homeland={g('hsi_g_oh', 0)};"
               f"base={g('hsi_g_base', 4)};siv={g('hsi_g_siv', 4)}")

def _records_block(hook: str, sample_expr: str, date_expr: str, slices, tags, sampler: str, indent: str) -> str:
    """GLOBAL, STATE and COUNTRY records of one sample; the current scope on entry does not matter."""
    out = [f"{indent}c:{sampler} ?= {{\n{indent}\tset_global_variable = {{ name = hsi_g_gpop value = global_population }}\n"
           f"{indent}\tset_global_variable = {{ name = hsi_g_ggdp value = global_gdp }}\n{indent}}}\n",
           f'{indent}debug_log = "HSI;{hook};{sample_expr};{date_expr};GLOBAL;-;pop={g("hsi_g_gpop", 0)};gdp={g("hsi_g_ggdp", 2)}"\n']
    for sk, owner in slices:
        out.append(f"{indent}s:{sk}.region_state:{owner} ?= {{\n{indent}\thsi_probe_state_globals = yes\n"
                   f'{indent}\tdebug_log = "HSI;{hook};{sample_expr};{date_expr};STATE;{sk}/{owner};{STATE_FIELDS}"\n{indent}}}\n')
    for tag in tags:
        out.append(f"{indent}c:{tag} ?= {{\n{indent}\thsi_probe_country_globals = yes\n"
                   f'{indent}\tdebug_log = "HSI;{hook};{sample_expr};{date_expr};COUNTRY;{tag};{COUNTRY_FIELDS}"\n{indent}}}\n')
    return "".join(out)

def _rule_block(hook: str) -> str:
    def line(flag):
        return f'debug_log = "HSI;{hook};0;lobby;RULE;-;flag={flag}"'
    return ("\tif = { limit = { has_game_rule = infamy_generation_very_low } " + line("very_low") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_low } " + line("low") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_high } " + line("high") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_very_high } " + line("very_high") + " }\n"
            "\telse = { " + line("standard") + " }\n")

def render(led: Ledger, config: dict) -> dict:
    sampler = config["sampler_tag"]
    months = int(config["months"])
    slices = probe_slices(led, config)
    tags = probe_tags(led, config)
    guard = " ".join(f"c:{t} = this" for t in guard_tags(led, config))
    on_actions = (
        "on_game_started = {\n\ton_actions = { hsi_probe_start_a }\n}\n"
        "on_game_started_after_lobby = {\n\ton_actions = { hsi_probe_start_b }\n}\n"
        "on_monthly_pulse_country = {\n\ton_actions = { hsi_probe_monthly }\n}\n"
        "hsi_probe_start_a = {\n\teffect = { hsi_probe_start_records_a = yes }\n}\n"
        "hsi_probe_start_b = {\n\teffect = { hsi_probe_start_records_b = yes }\n}\n"
        "hsi_probe_monthly = {\n\teffect = { hsi_probe_monthly_records = yes }\n}\n")
    values = (
        "hsi_probe_state_pop = { value = state_population }\n"
        "hsi_probe_state_gdp = { value = gdp }\n"
        "hsi_probe_gen = { value = modifier:country_infamy_generation_mult }\n"
        "hsi_probe_unrec = { value = modifier:country_infamy_generation_against_unrecognized_mult }\n"
        "hsi_probe_decay = { value = modifier:country_infamy_decay_mult }\n"
        "hsi_probe_infamy = { value = infamy }\n")
    eff = ["# GENERATED by tools/hsi/probe_gen.py from the ledger and config. Throwaway measurement mod; never shipped.\n"]
    eff.append("hsi_probe_state_globals = {\n"      # current scope: one formula state
               "\tset_global_variable = { name = hsi_g_pop value = hsi_probe_state_pop }\n"
               "\tset_global_variable = { name = hsi_g_gdp value = hsi_probe_state_gdp }\n"
               "\tset_global_variable = { name = hsi_g_pshare value = state_infamy_population_share_uncapped }\n"
               "\tset_global_variable = { name = hsi_g_gshare value = state_infamy_gdp_share_uncapped }\n"
               "\tset_global_variable = { name = hsi_g_base value = state_infamy_base }\n"
               + _flag("hsi_g_inc", "is_incorporated = yes") + _flag("hsi_g_cap", "is_capital = yes")
               + _flag("hsi_g_oh", "is_homeland_of_country_cultures = owner") + _type_code("hsi_g_ot", "owner = { ") + "}\n")
    eff.append("hsi_probe_country_globals = {\n"    # current scope: one country
               + _type_code("hsi_g_ct", "") + _rank_code("hsi_g_rank")
               + "\tset_global_variable = { name = hsi_g_gen value = hsi_probe_gen }\n"
               "\tset_global_variable = { name = hsi_g_unrec value = hsi_probe_unrec }\n"
               "\tset_global_variable = { name = hsi_g_decay value = hsi_probe_decay }\n"
               "\tset_global_variable = { name = hsi_g_infamy value = hsi_probe_infamy }\n}\n")
    eff.append("hsi_probe_diag_globals = {\n"       # current scope: one formula state, root = the holder, scope:hsi_state/hsi_region saved
               + _flag("hsi_g_d_ah", "is_homeland_of_country_cultures = root")
               + _flag("hsi_g_d_ahb", "root = { modifier:country_homeland_infamy_reduction_bool = yes }")
               + _flag("hsi_g_d_sl", "any_scope_culture = { has_homeland = scope:hsi_state shares_language_trait_with_any_primary_culture = root }")
               + _flag("hsi_g_d_slb", "root = { modifier:country_shared_language_infamy_reduction_bool = yes }")
               + _flag("hsi_g_d_cl", "has_claim_by = root")
               + _flag("hsi_g_d_su", "root = { is_scripted_unification_conquest = { TARGET = scope:hsi_state.owner } }")
               + _flag("hsi_g_d_adj", "root = { is_land_adjacent_to_state = scope:hsi_state }")
               + "\tif = { limit = { root = { NOT = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 2 } } } } set_global_variable = { name = hsi_g_d_int value = 1 } }\n"
               + "\telse_if = { limit = { root = { NOT = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 3 } } } } set_global_variable = { name = hsi_g_d_int value = 2 } }\n"
               + "\telse_if = { limit = { root = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 5 } } } set_global_variable = { name = hsi_g_d_int value = 5 } }\n"
               + "\telse = { set_global_variable = { name = hsi_g_d_int value = 3 } }\n"
               + _type_code("hsi_g_d_rt", "root = { ")
               + "\tset_global_variable = { name = hsi_g_siv value = state_infamy_value }\n}\n")
    for hook in ("start_a", "start_b"):   # one effect per hook; the hook name is a literal in every string
        eff.append(f"hsi_probe_start_records_{hook[-1]} = {{\n" + _records_block(hook, "0", "lobby", slices, tags, sampler, "\t") + _rule_block(hook) + "}\n")
    sample_expr = g("hsi_g_sample", 0)
    monthly = ["hsi_probe_monthly_records = {\n", f"\tif = {{ limit = {{ OR = {{ {guard} }} }}\n",
               "\t\tif = { limit = { NOT = { has_variable = hsi_sample } } set_variable = { name = hsi_sample value = 0 } }\n",
               "\t\tchange_variable = { name = hsi_sample add = 1 }\n",
               f"\t\tif = {{ limit = {{ var:hsi_sample <= {months} }}\n",
               "\t\t\tset_global_variable = { name = hsi_g_sample value = var:hsi_sample }\n",
               "\t\t\tset_global_variable = { name = hsi_g_root_unrec value = hsi_probe_unrec }\n"]
    monthly.append(f"\t\t\tif = {{ limit = {{ c:{sampler} = this }}\n")
    monthly.append(_records_block("monthly", sample_expr, DATE, slices, tags, sampler, "\t\t\t\t"))
    monthly.append("\t\t\t}\n")
    for holder, diag_slices in diag_pairs(led, config).items():
        # every ledger holder evaluates every ledger slice, so the same state is observed under two actors with
        # different factors; the fixture holder additionally evaluates the fixture target slices
        monthly.append(f"\t\t\tif = {{ limit = {{ c:{holder} = this }}\n")
        for sk, owner in diag_slices:
            monthly.append(f"\t\t\t\ts:{sk}.region_state:{owner} ?= {{\n\t\t\t\t\tsave_scope_as = hsi_state\n"
                           f"\t\t\t\t\tregion = {{ save_scope_as = hsi_region }}\n\t\t\t\t\thsi_probe_state_globals = yes\n"
                           f"\t\t\t\t\thsi_probe_diag_globals = yes\n"
                           f'\t\t\t\t\tdebug_log = "HSI;monthly;{sample_expr};{DATE};DIAG;{holder}/{sk}/{owner};root_tag={holder};{DIAG_FIELDS}"\n'
                           f"\t\t\t\t}}\n")
        monthly.append("\t\t\t}\n")
    monthly.append("\t\t}\n\t}\n}\n")
    eff.append("".join(monthly))
    metadata = {"name": "HSI Probe", "id": "", "version": "0.0.2", "supported_game_version": "1.14.*",
                "short_description": "Throwaway measurement probe for Historical Starting Infamy. Do not ship.",
                "tags": ["Utilities"], "relationships": [], "game_custom_data": {"multiplayer_synchronized": False}}
    return {
        ".metadata/metadata.json": json.dumps(metadata, indent=2) + "\n",
        "common/on_actions/zz_hsi_probe_on_actions.txt": on_actions,
        "common/script_values/zz_hsi_probe_values.txt": values,
        "common/scripted_effects/zz_hsi_probe_effects.txt": "".join(eff),
    }

def write_probe(probe_dir: Path, led: Ledger, config: dict) -> list:
    probe_dir = Path(probe_dir)
    written = []
    for rel, text in render(led, config).items():
        p = probe_dir / rel
        if p.suffix == ".txt":
            write_text_bom(p, text)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        written.append(p)
    return written

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--research", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    led = load_ledger(Path(a.research))
    config = json.loads((Path(a.out) / "config.json").read_text(encoding="utf-8"))
    for p in write_probe(Path(a.out), led, config):
        print(p)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
