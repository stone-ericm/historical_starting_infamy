# tools/hsi/generate.py
"""Ledger + the probe's day-one measurement -> five tables, the shipped effect, README table, derivation (spec §7, §8;
simplified by the 2026-10-14 ruling: the after-lobby sample is the snapshot, the stage order is the observed one, the rank
block is applied with measured 1836 ranks, output is whole numbers)."""
import csv
import json
import sys
from datetime import date
from pathlib import Path
from . import constants as K
from .bom import write_text_bom
from .formula import Component, GoalInputs, GOALS, component_value, component_breakdown, nominal_charge, stage_values, raw_goal_value, rank_mult, ORDER
from .hashes import generator_source_hashes, vanilla_input_hashes, measurement_hashes, header_block
from .ledger import Ledger, load_ledger, load_vanilla_tags, validate_ledger, LedgerError
from .measurement import (extract, session_logs, parse_lines, start_snapshot, sha256_file, expected_receipt,
                          check_receipt, missing_optional, monthly_snapshots, MeasurementError)
from .timeline import Event, replay_steps

RULES = ("very_low", "low", "standard", "high", "very_high")
TYPE_CODES = {0.0: "recognized", 1.0: "unrecognized", 2.0: "decentralized"}
EMIT_MIN = 0.5      # whole-number output: a finished balance below one half rounds to nothing (ruling 2026-10-14)

def _standing_from_state(rec: dict) -> str:
    if rec["incorporated"] == 1.0 and rec["capital"] == 1.0:
        return "capital"
    if rec["incorporated"] == 1.0 and rec["owner_homeland"] == 1.0:
        return "homeland"
    return "incorporated" if rec["incorporated"] == 1.0 else "unincorporated"

def _holder_mods(goal, snap) -> tuple:
    if goal.general_mult_source == "measured_1836" and goal.holder_tag_1836:
        c = snap.country(goal.holder_tag_1836)
        return c["gen_mult"], c["unrec_mult"]
    return 0.0, 0.0          # declared fallback for actors without a 1836 tag (spec §5, §10)

def _rank_of(tag: str, snap, fallback_type: str) -> tuple:
    """(rank, source): the measured 1836 rank for a tag the probe logged; the declared fallback by country type
    otherwise, labelled 'fallback-absent' (no 1836 tag) or 'fallback-unmeasured' (a tag the boot did not log:
    final review F5 keeps that distinction visible in the derivation)."""
    if tag and tag in snap.countries:
        return K.RANK_CODES[int(snap.country(tag)["rank"])], "measured"
    return K.FALLBACK_RANK[fallback_type], ("fallback-unmeasured" if tag else "fallback-absent")

def goal_inputs(goal, led: Ledger, snap) -> GoalInputs:
    gen, unrec = _holder_mods(goal, snap)
    comps = []
    for s in led.components_of(goal.goal_id):
        pop = sum(snap.slice(s.state_key, t)["pop_share_uncapped"] for t in s.slices_1836)
        gdp = sum(snap.slice(s.state_key, t)["gdp_share_uncapped"] for t in s.slices_1836)
        comps.append(Component(pop, gdp, s.standing, s.owner_type, s.aggressor_homeland, s.shared_language,
                               s.claim, s.scripted_unification, s.adjacent, s.interest_tier))
    components = led.components_of(goal.goal_id)
    target_type = components[0].owner_type if components else "recognized"
    hr, _ = _rank_of(goal.holder_tag_1836, snap, goal.holder_type)
    tr, _ = _rank_of(goal.victim_tag_1836, snap, target_type)
    return GoalInputs(goal.wargoal, tuple(comps), goal.holder_type, unrec, gen,
                      goal.loyal_subject, goal.rebellious_subject, holder_rank=hr, target_rank=tr)

def rank_sources(goal, led: Ledger, snap) -> tuple:
    components = led.components_of(goal.goal_id)
    target_type = components[0].owner_type if components else "recognized"
    return _rank_of(goal.holder_tag_1836, snap, goal.holder_type)[1], _rank_of(goal.victim_tag_1836, snap, target_type)[1]

def diagnostic_check(led: Ledger, snap, tolerance: float = 0.005) -> list:
    """Oracle A (spec §9): reproduce every engine-logged state_infamy_value from the operands the same DIAG
    record carries (the record is self-contained; review R1 finding B4)."""
    problems = []
    for (holder, sk, owner), d in sorted(snap.diag.items()):
        c = Component(d["pop_share_uncapped"], d["gdp_share_uncapped"], _standing_from_state(d),
                      TYPE_CODES[d["owner_type"]], d["aggressor_homeland"] == 1.0, d["shared_language"] == 1.0,
                      d["claim"] == 1.0, d["scripted_unification"] == 1.0, d["adjacent"] == 1.0,
                      int(d["interest_bucket"]), d["homeland_bonus"] == 1.0, d["language_bonus"] == 1.0)
        ours = component_value(c, TYPE_CODES[d["root_type"]], d["unrec_mult"])   # the root's modifier logged with the record (R2 N1)
        if abs(ours - d["siv"]) > tolerance:
            problems.append(f"{holder}/{sk}/{owner}: generator {ours:.4f} vs engine {d['siv']:.4f}")
    return problems

def emitted_value(actor: str, finished_balance: float):
    """Emission: a country with a 1836 tag, not BOL, whose FINISHED balance is at least one half; the value is
    the balance rounded to a whole number (half up), never below 1."""
    if not (len(actor) == 3 and actor.isupper()) or actor == "BOL" or finished_balance < EMIT_MIN:
        return None
    import math
    return int(math.floor(finished_balance + 0.5))

def _actor_key(goal) -> str:
    return goal.holder_tag_1836 if goal.holder_tag_1836 else f"actor:{goal.holder}"

def compute_tables(led: Ledger, snap, order=ORDER):
    horizon = date.fromisoformat(K.HORIZON)
    tables, rows = {}, []
    charges = {}
    for g in led.goals.values():
        gi = goal_inputs(g, led, snap)
        hsrc, tsrc = rank_sources(g, led, snap)
        # component rows (rule-independent): every operand and intermediate of the state formula (F3)
        subtotal = 0.0
        for s, c in zip(led.components_of(g.goal_id), gi.components):
            b = component_breakdown(c, gi.holder_type, gi.unrec_mult)
            subtotal += b["value"]
            rows.append({"rule": "all", "actor": _actor_key(g), "kind": "component", "goal_id": g.goal_id,
                         "component_id": s.component_id, "slices": ";".join(f"{s.state_key}/{t}" for t in s.slices_1836),
                         "pop_share_uncapped": c.pop_share_uncapped, "gdp_share_uncapped": c.gdp_share_uncapped,
                         "pop_capped": b["pop_capped"], "gdp_capped": b["gdp_capped"], "base": b["base"],
                         "standing": f"{c.standing} x{b['standing_mult']}",
                         "factors": " ".join(f"{n}x{f:.4g}" for n, f in b["factors"]),
                         "pre_floor": b["pre_floor"], "value": b["value"]})
        raw = raw_goal_value(gi)
        subject = raw / subtotal if subtotal else 1.0
        for rule in RULES:
            vals = stage_values(raw, GOALS[gi.wargoal], gi.general_mult, K.RULE_MULT[rule], order, rank_mult(gi.holder_rank, gi.target_rank))
            charges[(g.goal_id, rule)] = vals[order[-1]]
            rows.append({"rule": rule, "actor": _actor_key(g), "kind": "charge", "goal_id": g.goal_id,
                         "date": g.claim_date.isoformat(), "value": charges[(g.goal_id, rule)],
                         "component_subtotal": subtotal, "subject_mult": subject, "raw": raw,
                         "holder_rank": gi.holder_rank, "holder_rank_source": hsrc,
                         "target_rank": gi.target_rank, "target_rank_source": tsrc,
                         **{f"after_{st}": vals[st] for st in order}})
    for rule in RULES:
        events: dict = {}
        for g in led.goals.values():
            a = charges[(g.goal_id, rule)]
            events.setdefault(_actor_key(g), []).append(Event(g.claim_date, "accrual", g.goal_id, a))
            if g.resolution in K.REFUND and g.resolution_date is not None:
                events[_actor_key(g)].append(Event(g.resolution_date, "refund", g.goal_id, -K.REFUND[g.resolution] * a))
            if g.resolution == "enforced" and g.victim_tag_1836 and g.resolution_date is not None:
                events.setdefault(g.victim_tag_1836, []).append(
                    Event(g.resolution_date, "reduction", g.goal_id, -K.VICTIM_REDUCTION * a))
        table = {}
        for actor, evs in sorted(events.items()):
            steps = replay_steps(evs, horizon=horizon)
            for s in steps:
                rows.append({"rule": rule, "actor": actor, **s, "value": s["after_event"]})
            finished = steps[-1]["after_event"]
            value = emitted_value(actor, finished)
            rows.append({"rule": rule, "actor": actor, "kind": "emit" if value is not None else "not_emitted",
                         "goal_id": "", "date": K.HORIZON, "value": value if value is not None else finished})
            if value is not None:
                table[actor] = value
        tables[rule] = table
    return tables, rows

def render_effect(tables: dict, notes: dict, header: str) -> str:
    out = ["# GENERATED by tools/hsi/generate.py from the ledger and measurement. Do not edit by hand.\n", header]
    out.append("hsi_apply_starting_infamy = {\n\tif = {\n\t\tlimit = { NOT = { has_global_variable = hsi_applied } }\n")
    out.append("\t\tif = { limit = { has_game_rule = infamy_generation_very_low } hsi_table_very_low = yes }\n")
    out.append("\t\telse_if = { limit = { has_game_rule = infamy_generation_low } hsi_table_low = yes }\n")
    out.append("\t\telse_if = { limit = { has_game_rule = infamy_generation_high } hsi_table_high = yes }\n")
    out.append("\t\telse_if = { limit = { has_game_rule = infamy_generation_very_high } hsi_table_very_high = yes }\n")
    out.append("\t\telse = { hsi_table_standard = yes }\n\t\tset_global_variable = hsi_applied\n\t}\n}\n")
    for rule in RULES:
        out.append(f"hsi_table_{rule} = {{\n")
        for tag, value in sorted(tables[rule].items()):
            out.append(f"\tc:{tag} ?= {{ change_infamy = {value} }}   # {' '.join(notes.get(tag, []))}\n")
        out.append("}\n")
    return "".join(out)

def render_readme_table(tables: dict) -> str:
    tags = sorted({t for r in RULES for t in tables[r]})
    lines = ["| Country | Very Low | Low | Standard | High | Very High |", "|---|---:|---:|---:|---:|---:|"]
    for t in tags:
        cells = [f"{tables[r][t]}" if t in tables[r] else "0" for r in RULES]
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    if not tags:
        lines.append("| (no country) | 0 | 0 | 0 | 0 | 0 |")
    return "\n".join(lines) + "\n"

def update_readme(path: Path, table_md: str) -> None:
    text = path.read_text(encoding="utf-8")
    start, end = "<!-- hsi:table:start -->", "<!-- hsi:table:end -->"
    i, j = text.index(start) + len(start), text.index(end)
    path.write_text(text[:i] + "\n" + table_md + text[j:], encoding="utf-8")

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--game-dir", required=True)
    ap.add_argument("--measurement", required=True, help="the collected boot directory (debug*.log + probe-config.json)")
    a = ap.parse_args(argv)
    repo, game, meas = Path(a.repo), Path(a.game_dir), Path(a.measurement)
    try:
        led = load_ledger(repo / "research")
        validate_ledger(led, load_vanilla_tags(game))
        probe_config = json.loads((meas / "probe-config.json").read_text(encoding="utf-8"))
        logs = session_logs(meas)
        if not logs:
            raise MeasurementError(f"no debug*.log in {meas}")
        recs = parse_lines(extract(logs))
        expected = expected_receipt(led.all_slices(), led.holder_tags(), probe_config, led.victim_tags())
        receipt = check_receipt(recs, expected, require_monthly=False)
        if receipt:
            raise MeasurementError("incomplete day-one receipt:\n" + "\n".join(receipt))
        for t in missing_optional(recs, expected):
            print(f"note: victim {t} was not logged by this boot; its rank is the declared fallback (see derivation target_rank_source)", file=sys.stderr)
        snaps = monthly_snapshots(recs)
        n_diag = sum(len(s.diag) for s in snaps)
        if n_diag == 0:
            raise MeasurementError("no monthly DIAG records: the formula check (oracle A) has nothing to compare")
        problems = []
        for s in snaps:
            problems += [f"sample {s.sample}: {p}" for p in diagnostic_check(led, s)]
        if problems:
            raise MeasurementError("oracle A failed:\n" + "\n".join(problems))
        snap = start_snapshot(recs)
    except (LedgerError, MeasurementError) as err:
        print(f"REFUSED: {err}", file=sys.stderr)
        return 1
    tables, rows = compute_tables(led, snap)
    notes: dict = {}
    for g in led.goals.values():
        if g.holder_tag_1836:
            notes.setdefault(g.holder_tag_1836, []).append(g.goal_id)
    entries = {f"ledger/{n}": sha256_file(repo / "research" / n) for n in ("acts.csv", "goals.csv", "goal_states.csv")}
    entries.update(measurement_hashes(meas))
    entries["order"] = "".join(ORDER)
    entries.update(generator_source_hashes(Path(__file__).parent))
    entries.update(vanilla_input_hashes(game))
    write_text_bom(repo / "common" / "scripted_effects" / "zz_hsi_effects.txt", render_effect(tables, notes, header_block(entries)))
    (repo / "research" / "tables.json").write_text(json.dumps(tables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with open(repo / "research" / "derivation.csv", "w", newline="", encoding="utf-8") as f:
        keys = ["rule", "actor", "kind", "goal_id", "date", "component_id", "slices", "pop_share_uncapped", "gdp_share_uncapped",
                "pop_capped", "gdp_capped", "base", "standing", "factors", "pre_floor", "component_subtotal", "subject_mult", "raw",
                "holder_rank", "holder_rank_source", "target_rank", "target_rank_source"] + [f"after_{st}" for st in ORDER] + \
               ["before_decay", "after_decay", "delta", "after_event", "value"]
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    update_readme(repo / "README.md", render_readme_table(tables))
    print(f"snapshot {snap.hook} ({snap.date}); oracle A {n_diag} records over {len(snaps)} monthly samples, 0 mismatches; "
          + "; ".join(f"{r}: {len(tables[r])} countries" for r in RULES))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
