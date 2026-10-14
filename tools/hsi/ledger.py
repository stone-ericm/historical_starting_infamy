# tools/hsi/ledger.py
"""The three hand-authored ledger CSVs (spec §5) and every structural refusal (spec §7)."""
from dataclasses import dataclass
from datetime import date
import csv
import re
import sys
from pathlib import Path
from . import constants as K
from .formula import GOALS

TYPES = {"recognized", "unrecognized", "decentralized"}
STANDINGS = {"capital", "homeland", "incorporated", "unincorporated"}
RESOLUTIONS = {"enforced", "dropped_peace", "dropped_backdown", "dropped_backer", "pending"}
GENERAL_SOURCES = {"measured_1836", "none"}
TAG_RE = re.compile(r"^[A-Z][A-Z0-9]{2}$")

ACT_COLUMNS = ["act_id", "title", "start_date", "end_date", "source", "notes"]
GOAL_COLUMNS = ["goal_id", "act_id", "wargoal", "holder", "holder_tag_1836", "holder_type", "target",
                "stakeholder", "victim_tag_1836", "claim_date", "resolution", "resolution_date",
                "loyal_subject", "rebellious_subject", "general_mult_source", "notes"]
STATE_COLUMNS = ["goal_id", "component_id", "state_key", "slices_1836", "owner_type", "standing",
                 "aggressor_homeland", "shared_language", "claim", "scripted_unification", "adjacent",
                 "interest_tier", "justification"]

class LedgerError(Exception):
    def __init__(self, messages):
        self.messages = list(messages)
        super().__init__("\n".join(self.messages))

@dataclass(frozen=True)
class Act:
    act_id: str; title: str; start_date: str; end_date: str; source: str; notes: str

@dataclass(frozen=True)
class Goal:
    goal_id: str; act_id: str; wargoal: str; holder: str; holder_tag_1836: str; holder_type: str
    target: str; stakeholder: str; victim_tag_1836: str; claim_date: date; resolution: str
    resolution_date: date | None; loyal_subject: bool; rebellious_subject: bool
    general_mult_source: str; notes: str

@dataclass(frozen=True)
class GoalState:
    goal_id: str; component_id: str; state_key: str; slices_1836: tuple; owner_type: str; standing: str
    aggressor_homeland: bool; shared_language: bool; claim: bool; scripted_unification: bool
    adjacent: bool; interest_tier: int; justification: str

@dataclass
class Ledger:
    acts: dict
    goals: dict
    goal_states: list

    def components_of(self, goal_id: str) -> list:
        return [s for s in self.goal_states if s.goal_id == goal_id]

    def all_slices(self) -> set:
        return {(s.state_key, tag) for s in self.goal_states for tag in s.slices_1836}

    def victim_tags(self) -> set:
        return {g.victim_tag_1836 for g in self.goals.values() if g.victim_tag_1836}

    def holder_tags(self) -> set:
        return {g.holder_tag_1836 for g in self.goals.values() if g.holder_tag_1836}

def _read_csv(path: Path, columns: list, errors: list) -> list:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        errors.append(f"{path.name}: empty file"); return []
    header = [h.strip() for h in rows[0]]
    if header != columns:
        errors.append(f"{path.name}: header mismatch, expected {columns}, got {header}"); return []
    out = []
    for n, raw in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in raw):
            continue
        if len(raw) != len(columns):
            errors.append(f"{path.name}:{n}: expected {len(columns)} cells, got {len(raw)}"); continue
        out.append({c: v.strip() for c, v in zip(columns, raw)})
    return out

def _bool(v: str, where: str, errors: list) -> bool:
    if v in ("0", "1"):
        return v == "1"
    errors.append(f"{where}: boolean must be 0 or 1, got {v!r}")
    return False

def _date(v: str, where: str, errors: list, optional=False):
    if v == "":
        if optional:
            return None
        errors.append(f"{where}: date required"); return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        errors.append(f"{where}: bad date {v!r}"); return None

def load_ledger(research_dir: Path) -> Ledger:
    research_dir = Path(research_dir)
    errors: list = []
    acts, goals, states = {}, {}, []
    for r in _read_csv(research_dir / "acts.csv", ACT_COLUMNS, errors):
        if r["act_id"] in acts:
            errors.append(f"acts.csv: duplicate act_id {r['act_id']}"); continue
        acts[r["act_id"]] = Act(**r)
    for r in _read_csv(research_dir / "goals.csv", GOAL_COLUMNS, errors):
        w = f"goals.csv {r['goal_id']}"
        if r["goal_id"] in goals:
            errors.append(f"{w}: duplicate goal_id"); continue
        goals[r["goal_id"]] = Goal(
            r["goal_id"], r["act_id"], r["wargoal"], r["holder"], r["holder_tag_1836"], r["holder_type"],
            r["target"], r["stakeholder"], r["victim_tag_1836"],
            _date(r["claim_date"], w + " claim_date", errors) or date(1900, 1, 1),
            r["resolution"], _date(r["resolution_date"], w + " resolution_date", errors, optional=True),
            _bool(r["loyal_subject"], w, errors), _bool(r["rebellious_subject"], w, errors),
            r["general_mult_source"], r["notes"])
    seen = set()
    for r in _read_csv(research_dir / "goal_states.csv", STATE_COLUMNS, errors):
        w = f"goal_states.csv {r['goal_id']}/{r['component_id']}"
        if (r["goal_id"], r["component_id"]) in seen:
            errors.append(f"{w}: duplicate component_id"); continue
        seen.add((r["goal_id"], r["component_id"]))
        try:
            tier = int(r["interest_tier"])
        except ValueError:
            errors.append(f"{w}: interest_tier must be an integer"); tier = 3
        states.append(GoalState(
            r["goal_id"], r["component_id"], r["state_key"],
            tuple(t.strip() for t in r["slices_1836"].split(";") if t.strip()),
            r["owner_type"], r["standing"],
            _bool(r["aggressor_homeland"], w, errors), _bool(r["shared_language"], w, errors),
            _bool(r["claim"], w, errors), _bool(r["scripted_unification"], w, errors),
            _bool(r["adjacent"], w, errors), tier, r["justification"]))
    if errors:
        raise LedgerError(errors)
    return Ledger(acts, goals, states)

def load_vanilla_tags(game_dir: Path) -> set:
    tags = set()
    for p in sorted((Path(game_dir) / "common" / "country_definitions").glob("*.txt")):
        for m in re.finditer(r"(?m)^([A-Z][A-Z0-9]{2}) = \{", p.read_text(encoding="utf-8-sig")):
            tags.add(m.group(1))
    return tags

def validate_ledger(led: Ledger, vanilla_tags: set) -> None:
    e: list = []
    start, end = date.fromisoformat(K.WINDOW_START), date.fromisoformat(K.WINDOW_END)
    for g in led.goals.values():
        w = f"goal {g.goal_id}"
        if g.act_id not in led.acts:
            e.append(f"{w}: orphan act_id {g.act_id}")
        if g.wargoal not in GOALS:
            e.append(f"{w}: unknown or excluded wargoal {g.wargoal}")
        if g.holder_type not in TYPES:
            e.append(f"{w}: holder_type must be one of {sorted(TYPES)}")
        for field, tag in (("holder_tag_1836", g.holder_tag_1836), ("victim_tag_1836", g.victim_tag_1836)):
            if tag and (not TAG_RE.match(tag) or tag not in vanilla_tags):
                e.append(f"{w}: {field} {tag!r} is not a vanilla TAG")
        if not (start <= g.claim_date <= end):
            e.append(f"{w}: claim_date {g.claim_date} outside the window {K.WINDOW_START}..{K.WINDOW_END}")
        if g.resolution not in RESOLUTIONS:
            e.append(f"{w}: unknown resolution {g.resolution}")
        if g.resolution == "pending" and g.resolution_date is not None:
            e.append(f"{w}: pending goal must not carry a resolution_date")
        if g.resolution != "pending" and g.resolution_date is None:
            e.append(f"{w}: resolution {g.resolution} requires a resolution_date")
        if g.resolution_date is not None and g.resolution_date < g.claim_date:
            e.append(f"{w}: resolution_date before claim_date")
        if g.general_mult_source not in GENERAL_SOURCES:
            e.append(f"{w}: general_mult_source must be one of {sorted(GENERAL_SOURCES)}")
        if g.general_mult_source == "measured_1836" and not g.holder_tag_1836:
            e.append(f"{w}: general_mult_source measured_1836 requires a holder_tag_1836")
        if g.general_mult_source == "none" and g.holder_tag_1836:
            e.append(f"{w}: a holder with a holder_tag_1836 requires general_mult_source measured_1836 (the zero fallback is for absent actors only)")
        comps = led.components_of(g.goal_id)
        spec = GOALS.get(g.wargoal)
        if spec is not None:
            if spec.single_component and len(comps) != 1:
                e.append(f"{w}: {g.wargoal} needs exactly one component, has {len(comps)}")
            if not spec.single_component and len(comps) == 0:
                e.append(f"{w}: country-level goal has no components")
            for c in comps:
                if spec.requires_claim is True and not c.claim:
                    e.append(f"{w}/{c.component_id}: return_state requires claim = 1")
                if spec.requires_claim is False and c.claim:
                    e.append(f"{w}/{c.component_id}: conquer_state cannot carry a claim")
        slice_seen = set()
        for c in comps:
            for t in c.slices_1836:
                if (c.state_key, t) in slice_seen:
                    e.append(f"{w}: slice {c.state_key}/{t} appears twice within the goal")
                slice_seen.add((c.state_key, t))
    for s in led.goal_states:
        w = f"component {s.goal_id}/{s.component_id}"
        if s.goal_id not in led.goals:
            e.append(f"{w}: orphan goal_id")
        if s.owner_type not in TYPES:
            e.append(f"{w}: owner_type must be one of {sorted(TYPES)}")
        if s.standing not in STANDINGS:
            e.append(f"{w}: standing must be one of {sorted(STANDINGS)}")
        if not s.slices_1836:
            e.append(f"{w}: at least one slice required")
        if len(set(s.slices_1836)) != len(s.slices_1836):
            e.append(f"{w}: duplicate slice TAG inside slices_1836")
        for t in s.slices_1836:
            if not TAG_RE.match(t):
                e.append(f"{w}: slice {t!r} is not a TAG")
        if not (1 <= s.interest_tier <= 5):
            e.append(f"{w}: interest_tier must be 1..5")
    if e:
        raise LedgerError(e)

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Validate the ledger CSVs")
    ap.add_argument("research_dir")
    ap.add_argument("--game-dir", required=True)
    a = ap.parse_args(argv)
    try:
        led = load_ledger(Path(a.research_dir))
        validate_ledger(led, load_vanilla_tags(Path(a.game_dir)))
    except LedgerError as err:
        print("\n".join(err.messages), file=sys.stderr)
        return 1
    print(f"ledger ok: {len(led.acts)} acts, {len(led.goals)} goals, {len(led.goal_states)} components")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
