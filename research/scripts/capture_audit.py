"""Static audit of the oracle capture plan (spec section 6; review R1 findings B1/B2/B3).
Usage: python3 research/scripts/capture_audit.py <game_dir> [--plan research/measurement/capture-plan.json]
                                                    [--write-config research/probe/config.json]
VERIFIED STATICALLY (from the vanilla files): the target exists, is not decentralized, is not the holder's subject;
the relations blocker (strictly below the cordial threshold, including a subject's overlord) for the plays that carry
it; no history truce between holder and target; no holder claim on a Conquer State target (the play would be Return
State); the state or release exists and the release is not a living country; whether the holder owns a state in the
target's strategic region (ownership guarantees involvement, 00_defines.txt INTEREST_STATE_OR_CLAIM_MIN_TARGET_INVOLVEMENT,
not a tier).
UNVERIFIED AT RUNTIME (printed per candidate, resolved only at the keyboard): the interest tier at tick 0 (every play
carries requires_interest_marker by default, diplomatic_plays.md); regime change's ideological-opinion and installable-IG
conditions (validate_regime_change, WAR_GOAL_REGIME_CHANGE_MAX_IDEOLOGICAL_OPINION); liberation's secession movement with
10 % support and activism (WAR_GOAL_LIBERATE_COUNTRY_MIN_POPULAR_SUPPORT); subject rank rules for make_protectorate
(validate_subject_relation, 00_subject_types.txt); aggressive_diplomatic_plays_permitted.
ESTIMATE PROXIES (never transcription values): gdp share = pop share; interest tier 3 (neutral); adjacency as declared
in the plan, to be confirmed by the "Borders … by land" line; the holder's modifier against unrecognized targets from the
plan's unrec_mult_estimate (France: Colonization, -0.1); shared-language and bonus factors not modelled.
Exit 1 when a required capture has no candidate that passes every static check."""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from hsi import constants as K
from hsi.formula import GOALS, Component, component_value, nominal_charge, GoalInputs, DEFAULT_ORDER

RELATIONS_BLOCKER = {"conquer_state", "liberate_country", "return_state", "annex_country"}   # 00_diplomatic_plays.txt
OVERLORD_ONLY_BLOCKER = {"transfer_subject"}
REQUIRES_INTEREST = {"conquer_state", "make_protectorate", "liberate_country", "make_tributary", "make_dominion", "annex_country", "return_state"}
SUBJECT_TYPES = {"puppet", "protectorate", "dominion", "personal_union", "tributary", "crown_land", "chartered_company", "colony", "vassal"}
CORDIAL = 20   # 00_defines.txt RELATIONS_THRESHOLD_CORDIAL
RUNTIME = {   # conditions the files document but cannot decide before the boot
    "regime_change": "ideological opinion <= -5 and an installable non-marginalized interest group (validate_regime_change)",
    "liberate_country": "a secession movement for the release with >= 10% support and activism",
    "make_protectorate": "subject rank/type rules (validate_subject_relation)",
}

def blocks(text, pat):
    for m in re.finditer(pat, text):
        i = m.end(); d = 1; j = i
        while d and j < len(text):
            d += (text[j] == "{") - (text[j] == "}"); j += 1
        yield m.group(1), text[i:j - 1]

class Vanilla:
    def __init__(self, game: Path):
        self.states = {}      # STATE -> {"owners": [(tag, type)], "homelands": [...], "claims": [...]}
        txt = (game / "common/history/states/00_states.txt").read_text(encoding="utf-8-sig")
        for name, blk in blocks(txt, r"s:(STATE_[A-Z0-9_]+)\s*=\s*\{"):
            owners = []
            for _, cs in blocks(blk, r"(create_state)\s*=\s*\{"):
                tag = re.search(r"country\s*=\s*c:([A-Z0-9]+)", cs).group(1)
                st = re.search(r"state_type\s*=\s*(\w+)", cs)
                owners.append((tag, st.group(1) if st else "incorporated"))
            self.states[name] = {"owners": owners, "homelands": re.findall(r"add_homeland\s*=\s*cu:([a-z_]+)", blk),
                                 "claims": re.findall(r"add_claim\s*=\s*c:([A-Z0-9]+)", blk)}
        cdef = "".join(p.read_text(encoding="utf-8-sig") for p in (game / "common/country_definitions").glob("*.txt"))
        self.ctype, self.capital, self.cultures = {}, {}, {}
        for tag, blk in blocks(cdef, r"(?m)^([A-Z][A-Z0-9]{2})\s*=\s*\{"):
            m = re.search(r"country_type\s*=\s*(\w+)", blk); self.ctype[tag] = m.group(1) if m else "?"
            m = re.search(r"capital\s*=\s*(STATE_[A-Z0-9_]+)", blk); self.capital[tag] = m.group(1) if m else None
            m = re.search(r"cultures\s*=\s*\{([^}]*)\}", blk); self.cultures[tag] = m.group(1).split() if m else []
        self.region = {}
        for p in (game / "common/strategic_regions").glob("*.txt"):
            for name, blk in blocks(p.read_text(encoding="utf-8-sig"), r"(?m)^(region_[a-z_]+)\s*=\s*\{"):
                for s in re.findall(r"(STATE_[A-Z0-9_]+)", blk): self.region[s] = name
        self.pop = {}
        for p in (game / "common/history/pops").glob("*.txt"):
            t = p.read_text(encoding="utf-8-sig")
            for name, blk in blocks(t, r"s:(STATE_[A-Z0-9_]+)\s*=\s*\{"):
                for tag, sub in blocks(blk, r"region_state:([A-Z0-9]+)\s*=\s*\{"):
                    self.pop[(name, tag)] = self.pop.get((name, tag), 0) + sum(int(x) for x in re.findall(r"size\s*=\s*(\d+)", sub))
        self.world_pop = sum(self.pop.values())
        self.subject_of = {}
        st = (game / "common/history/diplomacy/00_subject_relationships.txt").read_text(encoding="utf-8-sig")
        for overlord, blk in blocks(st, r"c:([A-Z0-9]+)\s*\?=\s*\{"):
            for m in re.finditer(r"country\s*=\s*c:([A-Z0-9]+)\s*type\s*=\s*(\w+)", blk):
                if m.group(2) in SUBJECT_TYPES: self.subject_of[m.group(1)] = overlord
        self.relations = {}
        rt = (game / "common/history/diplomacy/00_relations.txt").read_text(encoding="utf-8-sig")
        for tag, blk in blocks(rt, r"c:([A-Z0-9]+)\s*\?=\s*\{"):
            for m in re.finditer(r"country\s*=\s*c:([A-Z0-9]+)\s*value\s*=\s*(-?\d+)", blk):
                self.relations[frozenset((tag, m.group(1)))] = int(m.group(2))
        self.truces = set()
        tt = (game / "common/history/diplomacy/00_truces.txt").read_text(encoding="utf-8-sig")
        for tag, blk in blocks(tt, r"c:([A-Z0-9]+)\s*\?=\s*\{"):
            for m in re.finditer(r"country\s*=\s*c:([A-Z0-9]+)", blk): self.truces.add(frozenset((tag, m.group(1))))
        self.releasable = {}
        rel = (game / "common/country_creation/00_releasable_countries.txt").read_text(encoding="utf-8-sig")
        for tag, blk in blocks(rel, r"(?m)^([A-Z][A-Z0-9]{2})\s*=\s*\{"):
            self.releasable[tag] = re.findall(r"(STATE_[A-Z0-9_]+)", blk)

    def rel(self, a, b): return self.relations.get(frozenset((a, b)), 0)
    def owned_slices(self, tag): return [(s, t) for s, d in self.states.items() for o, t in d["owners"] if o == tag]
    def owns_in_region(self, tag, region): return any(self.region.get(s) == region for s, _ in self.owned_slices(tag))

    def standing(self, state, owner, stype):
        if stype != "incorporated": return "unincorporated"
        if self.capital.get(owner) == state: return "capital"
        if any(c in self.cultures.get(owner, []) for c in self.states[state]["homelands"]): return "homeland"
        return "incorporated"

    def estimate_state(self, holder, state, owner, stype, adjacent, unrec_mult=0.0):
        share = self.pop.get((state, owner), 0) / max(self.world_pop, 1) * K.POP_WEIGHT * K.WORLD_SHARE_SCALE
        c = Component(share, share, self.standing(state, owner, stype), self.ctype.get(owner, "recognized"),
                      aggressor_homeland=any(c in self.cultures.get(holder, []) for c in self.states[state]["homelands"]),
                      adjacent=adjacent, interest_tier=3)
        return component_value(c, self.ctype.get(holder, "recognized"), unrec_mult)

def audit(plan: dict, V: Vanilla):
    holder = plan["holder"]; G = plan.get("general_mult_estimate", 0.0); rule = plan["rule"]
    unrec_est = plan.get("unrec_mult_estimate", 0.0)
    rows, ok_by_capture = [], {}
    for cap in plan["captures"]:
        spec = GOALS[cap["wargoal"]]
        passing = []
        for cand in cap["candidates"]:
            tgt = cand["target"]; problems, warnings = [], []
            if tgt not in V.ctype: problems.append("no such country")
            else:
                if V.ctype[tgt] == "decentralized": problems.append("decentralized target: no diplomatic play")
                if V.subject_of.get(tgt) == holder: problems.append("target is the holder's subject")
                if cap["wargoal"] in RELATIONS_BLOCKER:
                    r = V.rel(holder, tgt)
                    if r >= CORDIAL: problems.append(f"relations {r} >= cordial {CORDIAL}")
                    ov = V.subject_of.get(tgt)
                    if ov and V.rel(holder, ov) >= CORDIAL: problems.append(f"overlord {ov} relations {V.rel(holder, ov)} >= cordial")
                if frozenset((holder, tgt)) in V.truces: problems.append("history truce with the holder")
                if cap["wargoal"] in OVERLORD_ONLY_BLOCKER:
                    ov = V.subject_of.get(tgt)
                    if not ov: problems.append("not a subject")
                    elif V.rel(holder, ov) >= CORDIAL: problems.append(f"overlord {ov} relations >= cordial")
            if problems:
                rows.append((cap["id"], tgt, cand.get("state") or cand.get("release", ""), "FAIL", "; ".join(problems), "")); continue
            # the slices this candidate prices
            if cap["wargoal"] == "conquer_state":
                st = cand["state"]; owners = dict(V.states.get(st, {"owners": []})["owners"])
                if tgt not in owners: problems.append(f"{tgt} owns no slice of {st}")
                elif holder in V.states[st]["claims"]: problems.append(f"{holder} has a claim on {st}: the play would be Return State")
                slices = [(st, tgt, owners.get(tgt, "incorporated"))]
            elif cap["wargoal"] == "liberate_country":
                relx = cand["release"]
                if relx not in V.releasable: problems.append(f"no releasable {relx}")
                elif relx == tgt or V.owned_slices(relx): problems.append(f"{relx} already exists as a country; nothing to liberate")
                slices = [(s, tgt, dict(V.states[s]["owners"]).get(tgt)) for s in V.releasable.get(relx, []) if tgt in dict(V.states[s]["owners"])]
                if not slices and not problems: problems.append(f"{tgt} owns none of {relx}'s states")
                warnings.append("needs a secession movement with 10% support (unverifiable statically)")
            else:
                slices = [(s, tgt, t) for s, t in V.owned_slices(tgt)]
            if problems:
                rows.append((cap["id"], tgt, cand.get("state") or cand.get("release", ""), "FAIL", "; ".join(problems), "")); continue
            regions = {V.region.get(s) for s, _, _ in slices}
            if not any(V.owns_in_region(holder, r) for r in regions):
                warnings.append(f"holder owns nothing in {sorted(r for r in regions if r)}: interest not shown statically")
            unverified = ["interest tier at tick 0"] + ([RUNTIME[cap["wargoal"]]] if cap["wargoal"] in RUNTIME else [])
            warnings.append("UNVERIFIED at runtime: " + "; ".join(unverified))
            raw = sum(V.estimate_state(holder, s, o, t, cand.get("adjacent", False), unrec_est) for s, o, t in slices)
            gi = GoalInputs(cap["wargoal"], (), V.ctype.get(holder, "recognized"), 0.0, G, False, False)
            after_g = raw * spec.severity
            if spec.clamp_min is not None: after_g = max(after_g, spec.clamp_min)
            if spec.clamp_max is not None: after_g = min(after_g, spec.clamp_max)
            standard = after_g * (1 + G); very_low = standard * K.RULE_MULT[rule]
            role = cap["role"]; boundary_ok = {
                "above_floor_with_severity": very_low > 2.0,
                "factor_line": cand.get("adjacent", False),
                "clamp_min": raw * spec.severity < spec.clamp_min - 0.3 if spec.clamp_min else False,
                "clamp_max": raw * spec.severity > spec.clamp_max + 3 if spec.clamp_max else False,
                "floor_binds_under_rule": 1.05 < standard < 1.95,
            }[role]
            est = f"raw~{raw:.1f} std~{standard:.2f} vlow~{very_low:.2f}"
            status = "OK" if boundary_ok else "BOUNDARY?"
            if boundary_ok: passing.append(cand)
            rows.append((cap["id"], tgt, cand.get("state") or cand.get("release", ""), status, "; ".join(warnings), est))
        ok_by_capture[cap["id"]] = (bool(passing), cap.get("optional", False))
    return rows, ok_by_capture

def fixture_slices(plan: dict, V: Vanilla) -> list:
    out = set()
    for cap in plan["captures"]:
        for cand in cap["candidates"]:
            tgt = cand["target"]
            if cap["wargoal"] == "conquer_state": out.add((cand["state"], tgt))
            elif cap["wargoal"] == "liberate_country":
                out |= {(s, tgt) for s in V.releasable.get(cand["release"], []) if tgt in dict(V.states.get(s, {"owners": []})["owners"])}
            elif not cand.get("no_fixture_records"):
                out |= {(s, tgt) for s, _ in V.owned_slices(tgt)}
    return sorted(out)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("game_dir"); ap.add_argument("--plan", default="research/measurement/capture-plan.json")
    ap.add_argument("--write-config", help="write the candidates' slices into this probe config as fixture_slices")
    a = ap.parse_args(argv)
    V = Vanilla(Path(a.game_dir)); plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    rows, ok = audit(plan, V)
    print(f"holder {plan['holder']} rule {plan['rule']} general_mult {plan.get('general_mult_estimate', 0.0)} unrec_mult {plan.get('unrec_mult_estimate', 0.0)}; "
          "estimates: gdp share = pop share, interest tier 3, adjacency as declared; statuses verify the static chain only")
    print(f"{'cap':5} {'target':7} {'state/release':20} {'status':10} estimate (pop-only, gdp=pop)   notes")
    for r in rows: print(f"{r[0]:5} {r[1]:7} {r[2]:20} {r[3]:10} {r[5]:32} {r[4]}")
    failed = [c for c, (p, opt) in ok.items() if not p and not opt]
    for c, (p, opt) in ok.items():
        if not p and opt: print(f"capture {c}: optional, no candidate passes statically (capture only if the game offers it)")
    if a.write_config:
        cfg_path = Path(a.write_config); cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["fixture_holder"] = plan["holder"]; cfg["rule"] = plan["rule"]; cfg["fixture_slices"] = [list(s) for s in fixture_slices(plan, V)]
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {len(cfg['fixture_slices'])} fixture slices to {cfg_path}")
    if failed:
        print(f"AUDIT FAILED: no passing candidate for {failed}"); return 1
    print("AUDIT OK"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
