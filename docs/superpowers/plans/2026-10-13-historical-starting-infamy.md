# Historical Starting Infamy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a vanilla Victoria 3 1.14.5 mod that gives every 1836 country the infamy its 1816–1835 conduct would have generated under the game's own formula, derived reproducibly from a sourced ledger and an engine measurement.

**Architecture:** Pure-Python tooling under `tools/hsi/` turns three hand-authored ledger CSVs plus a probe-mod measurement into five rule-specific tables, a generated scripted effect, a README table and a full derivation. A throwaway probe mod measures 1836 shares, modifiers and the engine's own per-state values; the shipped mod is one additive on_action plus the generated effect. Acceptance reads a never-unpaused tick-0 save.

**Tech Stack:** Python 3.14 stdlib only (csv, dataclasses, decimal, hashlib, json, re, datetime); pytest via `uvx pytest`; Victoria 3 script (Jomini) for the probe and the shipped mod; `herdr` is not involved.

**Spec:** `docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` (v3.1, approved 2026-10-13). Read it first; every task below cites the section it implements.

## Global Constraints

- Target game: Victoria 3 vanilla **1.14.5**; vanilla scripts at `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game/` (spec §3). The generator takes this as `--game-dir`.
- Every game-script `.txt` file (shipped mod, probe mod) is written with a **UTF-8 BOM** through `hsi.bom.write_text_bom`; `validate.py` enforces it (spec §8).
- Python is **stdlib only**; tests run from `tools/` with `uvx pytest -q` (no system pytest on this Mac).
- All vanilla constants live in `tools/hsi/constants.py` with the defines file and line beside each (spec §7). No other module embeds a number from the game files.
- Shipped on_action registration is the additive form only: `on_game_started_after_lobby = { on_actions = { hsi_on_game_started } }` (spec §8). Never add an `effect` block to a vanilla on_action.
- Standard rule has **no flag**; it is the `else` branch (spec §3, §8). Flags: `infamy_generation_very_low`, `_low`, `_high`, `_very_high`.
- BOL is computed but never emitted (spec §2, §5).
- Horizon: balances are read at the **beginning of 1836-01-01**; events dated 1836-01-01 or later are not processed (spec §7).
- Window: `claim_date` in **1816-01-01..1835-12-31** (spec §5).
- Record line format for the probe is fixed in Task 7 and consumed by Tasks 8, 10 and 11: `HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v;k=v…`.
- Boots on this Mac: direct binary launch with `-debug_mode`; `content_load.json` is backed up before and restored after every boot (Task 8, Task 15). Never leave Eric's playset altered.
- Commits: spec and review artifacts have been committed on `main` so far; keep committing per task on `main` unless Eric says otherwise. Every commit message ends with the attribution lines in use in this repo (see `git log`).

## Review Focus

Inputs the spec implies but no task's tests exercised before this list was written; each now has a test in the owning task:

1. Ledger CSVs saved by a spreadsheet with a UTF-8 BOM, CRLF line endings or padded cells (`" EGY"`) must load identically to clean files, not fail or silently create a new TAG. Test added to Task 6.
2. `debug.log` numbers formatted with thousands separators (`1,022,805,087`) or a Unicode minus (`−0.05`) must parse; a line with the `HSI;` prefix embedded after the engine's own prefix must still be found. Test added to Task 7.
3. A country record whose nested sub-block also contains a key named `infamy` (for example inside an AI block) must not be misread; only the depth-1 scalar counts, and an absent depth-1 `infamy` means 0. Test added to Task 14.
4. A goal whose `resolution_date` is exactly 1836-01-01 must not be processed, and one dated 1835-12-31 must be; a `pending` goal with a stray date must be refused. Tests added to Tasks 5 and 6.
5. Two ordering candidates that are numerically equivalent on the loaded domain (for example clamp-then-floor versus floor-then-clamp with the regime-change bounds) must count as one class and not trigger the ambiguity refusal. Test added to Task 4.

---

## File structure

```
tools/
  hsi/__init__.py
  hsi/bom.py            write_text_bom(path, text) / has_bom(path)
  hsi/constants.py      every vanilla number, with defines file:line
  hsi/formula.py        Component, GoalSpec/GOALS, component_value, raw_goal_value, stage_values, nominal_charge
  hsi/ordering.py       Line, Fixture, CANDIDATES, fits, equivalent, select_order, OrderingNoFit, OrderingAmbiguous
  hsi/timeline.py       Event, replay, replay_steps
  hsi/ledger.py         Act, Goal, GoalState, Ledger, load_ledger, validate_ledger, load_vanilla_tags, LedgerError
  hsi/measurement.py    Record, parse_lines, group_samples, Snapshot, choose_snapshot, write_manifest, verify_manifest, ManifestError, StabilizationError
  hsi/probe_gen.py      write_probe(repo, ledger, config) -> list of written paths
  hsi/hashes.py         sha256_file, vanilla_input_paths, header_block, parse_header
  hsi/generate.py       main(): ledger + measurement + fixtures -> tables.json, effect, README table, derivation.csv
  hsi/validate.py       main(): BOM, braces, rule flags, header hashes, manifest
  hsi/savecheck.py      parse_save, check_save, main()
  tests/conftest.py     puts tools/ on sys.path
  tests/test_*.py       one file per module
  tests/fixtures/       fixture ledger, fixture probe log, fixture save text
research/
  acts.csv goals.csv goal_states.csv sources.md
  probe/config.json     {"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3}
  probe/.metadata/metadata.json + common/... (GENERATED by probe_gen)
  measurement/PROCEDURE.md
  measurement/<YYYY-MM-DD>/ (probe evidence, manifest-bound)
  acceptance/ACCEPTANCE.md  acceptance/<YYYY-MM-DD>/ (boot evidence, saves gitignored)
  fixtures.json         typed oracle fixtures transcribed from tooltips
  tables.json derivation.csv (GENERATED)
common/on_actions/zz_hsi_on_actions.txt            static
common/scripted_effects/zz_hsi_effects.txt         GENERATED
.metadata/metadata.json
README.md
```

---

### Task 1: Scaffold, test harness, BOM helper

**Files:**
- Create: `tools/hsi/__init__.py`, `tools/hsi/bom.py`, `tools/tests/conftest.py`, `tools/tests/test_bom.py`, `tools/pytest.ini`

**Interfaces:**
- Produces: `hsi.bom.write_text_bom(path: Path, text: str) -> None` (writes UTF-8 with BOM, LF endings), `hsi.bom.has_bom(path: Path) -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tools/tests/test_bom.py
from pathlib import Path
from hsi.bom import write_text_bom, has_bom

def test_write_text_bom_prefixes_bom_and_uses_lf(tmp_path: Path):
    p = tmp_path / "a.txt"
    write_text_bom(p, "x = {\r\n\ty = 1\r\n}\n")
    raw = p.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert has_bom(p)

def test_has_bom_false_without_bom(tmp_path: Path):
    p = tmp_path / "b.txt"
    p.write_bytes(b"x = 1\n")
    assert not has_bom(p)
```

- [ ] **Step 2: Create harness files and run the test to see it fail**

```python
# tools/tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

```ini
# tools/pytest.ini
[pytest]
testpaths = tests
```

`tools/hsi/__init__.py` is an empty file.

Run: `cd tools && uvx pytest -q tests/test_bom.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.bom'`

- [ ] **Step 3: Implement**

```python
# tools/hsi/bom.py
"""UTF-8 BOM helpers. The engine requires a BOM on every script .txt; editors and the Write tool strip it."""
from pathlib import Path

BOM = b"\xef\xbb\xbf"

def write_text_bom(path: Path, text: str) -> None:
    data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(BOM + data)

def has_bom(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(3) == BOM
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add tools/
git commit -m "Add test harness and BOM helper"
```

---

### Task 2: Constants and the per-component state value (spec §3, §7)

**Files:**
- Create: `tools/hsi/constants.py`, `tools/hsi/formula.py`, `tools/tests/test_formula_component.py`

**Interfaces:**
- Produces: `formula.Component` (frozen dataclass), `formula.share_uncapped(total, global_total, weight) -> float`, `formula.capped(x) -> float`, `formula.interest_factor(tier) -> float`, `formula.component_value(c, holder_type, unrec_mult) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_formula_component.py
import pytest
from hsi import constants as K
from hsi.formula import Component, capped, share_uncapped, interest_factor, component_value

def comp(**kw):
    base = dict(pop_share_uncapped=0.0, gdp_share_uncapped=0.0, standing="incorporated", owner_type="recognized")
    base.update(kw)
    return Component(**base)

def test_share_uncapped_scales_and_floors_denominator():
    # 1,000,000 of 1,000,000,000 people = 0.1% -> x10000 x0.375 = 3.75
    assert share_uncapped(1_000_000, 1_000_000_000, K.POP_WEIGHT) == pytest.approx(3.75)
    assert share_uncapped(5, 0, K.POP_WEIGHT) == pytest.approx(5 * K.POP_WEIGHT * K.WORLD_SHARE_SCALE)

@pytest.mark.parametrize("x,expected", [(10, 10), (12, 11), (20, 15), (30, 15), (3.5, 3.5)])
def test_capped_soft_and_hard_caps(x, expected):
    assert capped(x) == pytest.approx(expected)

@pytest.mark.parametrize("tier,factor", [(1, 1.25), (2, 1.10), (3, 1.0), (4, 1.0), (5, 0.8)])
def test_interest_factor_buckets(tier, factor):
    assert interest_factor(tier) == pytest.approx(factor)

def test_baseline_plus_shares_times_standing():
    c = comp(pop_share_uncapped=2.0, gdp_share_uncapped=1.0, standing="capital")
    assert component_value(c, "recognized", 0.0) == pytest.approx((5 + 2 + 1) * 2.0)

def test_homeland_takes_precedence_over_shared_language():
    c = comp(aggressor_homeland=True, shared_language=True)
    assert component_value(c, "recognized", 0.0) == pytest.approx(5 * 0.75)

def test_shared_language_alone():
    c = comp(shared_language=True)
    assert component_value(c, "recognized", 0.0) == pytest.approx(5 * 0.85)

def test_bonus_booleans_only_within_selected_branch():
    c = comp(aggressor_homeland=True, homeland_bonus=True, language_bonus=True)
    assert component_value(c, "recognized", 0.0) == pytest.approx(5 * 0.75 * 0.9)

def test_claim_takes_precedence_over_unification():
    c = comp(claim=True, scripted_unification=True)
    assert component_value(c, "recognized", 0.0) == pytest.approx(max(1.0, 5 * 0.25))

def test_adjacency_and_interest_stack():
    c = comp(adjacent=True, interest_tier=1)
    assert component_value(c, "recognized", 0.0) == pytest.approx(5 * 0.9 * 1.25)

def test_unrecognized_discount_requires_recognized_holder_and_unrecognized_owner():
    c = comp(owner_type="decentralized", standing="unincorporated")
    assert component_value(c, "recognized", -0.4) == pytest.approx(5 * 0.5 * 0.6)
    assert component_value(c, "unrecognized", -0.4) == pytest.approx(5 * 0.5)
    c2 = comp(owner_type="recognized")
    assert component_value(c2, "recognized", -0.4) == pytest.approx(5.0)

def test_state_floor_is_one():
    c = comp(standing="unincorporated", claim=True, adjacent=True, owner_type="decentralized")
    assert component_value(c, "recognized", -0.5) == pytest.approx(1.0)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_formula_component.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.constants'`

- [ ] **Step 3: Implement constants and the component formula**

```python
# tools/hsi/constants.py
"""Every vanilla 1.14.5 number the generator uses. Source: common/defines/00_defines.txt (D) and
common/script_values/00_diplomacy_values.txt (DV) unless noted. Re-read these on any game patch."""
STATE_BASELINE = 5.0                 # D:1121 WAR_GOAL_INFAMY_STATE_BASELINE
WORLD_SHARE_SCALE = 10000.0          # D:1113 WAR_GOAL_INFAMY_WORLD_SHARE_SCALE
POP_WEIGHT = 0.375                   # D:1114 WAR_GOAL_INFAMY_POPULATION_WEIGHT
GDP_WEIGHT = 0.375                   # D:1115 WAR_GOAL_INFAMY_GDP_WEIGHT
SHARE_MAX = 15.0                     # D:1117 / D:1118 (population, GDP)
SHARE_SOFT_CAP = 10.0                # D:1119 WAR_GOAL_INFAMY_SHARE_SOFT_CAP
SHARE_SOFT_CAP_SLOPE = 0.5           # D:1120 WAR_GOAL_INFAMY_SHARE_SOFT_CAP_SLOPE
STANDING = {                         # D:1149-1152
    "capital": 2.0, "homeland": 1.5, "incorporated": 1.0, "unincorporated": 0.5,
}
HOMELAND_FACTOR = -0.25              # D:1161 WAR_GOAL_INFAMY_HOMELAND_FACTOR
HOMELAND_BONUS_FACTOR = -0.1         # D:1162
SHARED_LANGUAGE_FACTOR = -0.15       # D:1153
SHARED_LANGUAGE_BONUS_FACTOR = -0.1  # D:1154
CLAIM_FACTOR = -0.75                 # D:1155
ADJACENCY_FACTOR = -0.1              # D:1156
SCRIPTED_UNIFICATION_FACTOR = -0.7   # D:1157
INTEREST_INCREASE_HIGH = 0.25        # DV:1068 (tier < 2)
INTEREST_INCREASE_MEDIUM = 0.10      # DV:1069 (tier < 3)
INTEREST_DECREASE_MEDIUM = -0.20     # DV:1070 (tier >= 5)
INTEREST_INCREASE_MAX_TIER = 2       # DV:1072
INTEREST_DECREASE_MIN_TIER = 5       # DV:1073
STATE_MIN = 1.0                      # D:1148 WAR_GOAL_INFAMY_MINIMUM (per state)
GOAL_MIN = 1.0                       # D:1148 (per war goal, after all multipliers)
SUBJECT_MULT = 0.25                  # D:1164 rebellious, D:1165 loyal (LD < 25, D:1167)
RULE_MULT = {                        # D:1122-1125; standard has no flag (00_game_rules.txt:97-117)
    "very_low": 0.5, "low": 0.75, "standard": 1.0, "high": 1.25, "very_high": 1.5,
}
RULE_FLAGS = {                       # 00_game_rules.txt:100-117
    "very_low": "infamy_generation_very_low", "low": "infamy_generation_low",
    "high": "infamy_generation_high", "very_high": "infamy_generation_very_high",
}
REFUND = {                           # fraction of the accrued charge returned when the goal is dropped
    "dropped_backdown": 0.75,        # D:1172 WAR_GOAL_INFAMY_DIPLO_PLAY_BACK_DOWN_REFUND
    "dropped_backer": 1.0,           # D:1173 WAR_GOAL_INFAMY_DIPLO_PLAY_BACKER_REFUND
    "dropped_peace": 0.5,            # D:1174 WAR_GOAL_INFAMY_PEACE_REFUND
}
VICTIM_REDUCTION = 0.5               # D:1175 WAR_GOAL_INFAMY_REDUCTION_FOR_TARGET (spec H2)
DECAY_PER_YEAR = 5.0                 # D:1006 BASE_YEARLY_INFAMY_DECAY_RATE
DAYS_PER_YEAR = 365.25               # declared model choice (spec §10)
INFAMY_MIN = 0.0                     # D:1000
INFAMY_MAX = 1000.0                  # D:1001
WINDOW_START = "1816-01-01"          # spec §5
WINDOW_END = "1835-12-31"            # spec §5
HORIZON = "1836-01-01"               # spec §7, balance read at the beginning of this day
```

```python
# tools/hsi/formula.py
"""Replication of common/script_values/00_infamy_values.txt (state value) and the per-goal processing
stages of common/war_goal_types/*.txt. Pure functions; constants come from hsi.constants."""
from dataclasses import dataclass
from . import constants as K

@dataclass(frozen=True)
class Component:
    pop_share_uncapped: float
    gdp_share_uncapped: float
    standing: str                 # capital | homeland | incorporated | unincorporated
    owner_type: str               # recognized | unrecognized | decentralized
    aggressor_homeland: bool = False
    shared_language: bool = False
    claim: bool = False
    scripted_unification: bool = False
    adjacent: bool = False
    interest_tier: int = 3
    homeland_bonus: bool = False  # diagnostic mode only
    language_bonus: bool = False  # diagnostic mode only

def share_uncapped(total: float, global_total: float, weight: float) -> float:
    """00_infamy_values.txt:1-26: share = total / max(global, 1), x weight x 10000."""
    return total / max(global_total, 1.0) * weight * K.WORLD_SHARE_SCALE

def capped(x: float) -> float:
    """00_infamy_values.txt:39-74: above the soft cap only half counts; hard max 15."""
    if x > K.SHARE_SOFT_CAP:
        x = K.SHARE_SOFT_CAP + (x - K.SHARE_SOFT_CAP) * K.SHARE_SOFT_CAP_SLOPE
    return min(x, K.SHARE_MAX)

def interest_factor(tier: int) -> float:
    """00_infamy_values.txt:208-255, one else-if chain."""
    if tier < K.INTEREST_INCREASE_MAX_TIER:
        return 1.0 + K.INTEREST_INCREASE_HIGH
    if tier < 3:
        return 1.0 + K.INTEREST_INCREASE_MEDIUM
    if tier >= K.INTEREST_DECREASE_MIN_TIER:
        return 1.0 + K.INTEREST_DECREASE_MEDIUM
    return 1.0

def component_value(c: Component, holder_type: str, unrec_mult: float) -> float:
    """state_infamy_value for one formula state, root = holder."""
    v = K.STATE_BASELINE + capped(c.pop_share_uncapped) + capped(c.gdp_share_uncapped)
    v *= K.STANDING[c.standing]
    if c.aggressor_homeland:
        v *= 1.0 + K.HOMELAND_FACTOR
        if c.homeland_bonus:
            v *= 1.0 + K.HOMELAND_BONUS_FACTOR
    elif c.shared_language:
        v *= 1.0 + K.SHARED_LANGUAGE_FACTOR
        if c.language_bonus:
            v *= 1.0 + K.SHARED_LANGUAGE_BONUS_FACTOR
    if c.claim:
        v *= 1.0 + K.CLAIM_FACTOR
    elif c.scripted_unification:
        v *= 1.0 + K.SCRIPTED_UNIFICATION_FACTOR
    if c.adjacent:
        v *= 1.0 + K.ADJACENCY_FACTOR
    v *= interest_factor(c.interest_tier)
    if holder_type == "recognized" and c.owner_type != "recognized":
        v *= 1.0 + unrec_mult
    return max(v, K.STATE_MIN)
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass (the `test_state_floor_is_one` case: 5 × 0.5 × 0.25 × 0.9 × 0.5 = 0.28 → floored to 1).

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/constants.py tools/hsi/formula.py tools/tests/test_formula_component.py
git commit -m "Add vanilla constants and the per-state infamy formula"
```

---

### Task 3: Goal table, raw goal value, processing stages, nominal charge (spec §3, §7)

**Files:**
- Modify: `tools/hsi/formula.py` (append)
- Create: `tools/tests/test_formula_goal.py`

**Interfaces:**
- Produces: `formula.GoalSpec`, `formula.GOALS: dict[str, GoalSpec]`, `formula.GoalInputs`, `formula.raw_goal_value(g) -> float`, `formula.STAGES = ("S","C","G","R","F")`, `formula.DEFAULT_ORDER`, `formula.stage_values(raw, spec, general_mult, rule_mult, order) -> dict[str, float]`, `formula.nominal_charge(g, rule_key, order) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_formula_goal.py
import pytest
from hsi import constants as K
from hsi.formula import (Component, GoalInputs, GOALS, raw_goal_value, stage_values,
                         nominal_charge, DEFAULT_ORDER)

def neutral(n=1):
    return tuple(Component(0.0, 0.0, "incorporated", "recognized") for _ in range(n))

def goal(wargoal, n=1, **kw):
    base = dict(wargoal=wargoal, components=neutral(n), holder_type="recognized",
                unrec_mult=0.0, general_mult=0.0)
    base.update(kw)
    return GoalInputs(**base)

def test_goal_table_matches_war_goal_types():
    assert GOALS["conquer_state"].severity == 1.0 and GOALS["conquer_state"].single_component
    assert GOALS["return_state"].requires_claim is True and GOALS["conquer_state"].requires_claim is False
    for w in ("make_protectorate", "make_dominion", "make_tributary", "make_personal_union"):
        assert GOALS[w].severity == 0.5 and GOALS[w].subject_blocks
    assert GOALS["transfer_subject"].severity == 0.4
    assert GOALS["liberate_country"].severity == 0.1 and not GOALS["liberate_country"].subject_blocks
    assert GOALS["release_as_subject"].severity == 0.6 and not GOALS["release_as_subject"].subject_blocks
    assert GOALS["regime_change"].clamp_min == 3.0 and GOALS["regime_change"].clamp_max == 10.0
    assert GOALS["restore_union"].severity == 0.1 and not GOALS["restore_union"].subject_blocks
    assert "liberate_subject" not in GOALS and "reduce_autonomy" not in GOALS

def test_raw_goal_value_sums_components_and_applies_subject_blocks_where_present():
    g = goal("annex_country", n=4, loyal_subject=True, rebellious_subject=True)
    assert raw_goal_value(g) == pytest.approx(20 * 0.25 * 0.25)
    g2 = goal("liberate_country", n=4, loyal_subject=True)
    assert raw_goal_value(g2) == pytest.approx(20.0)   # no subject block on liberation

def test_stage_values_default_order_protectorate():
    spec = GOALS["make_protectorate"]
    vals = stage_values(80.0, spec, 0.0, K.RULE_MULT["very_low"], DEFAULT_ORDER)
    assert vals["S"] == pytest.approx(40.0)
    assert vals["C"] == pytest.approx(40.0)
    assert vals["R"] == pytest.approx(20.0)
    assert vals["F"] == pytest.approx(20.0)

def test_regime_change_clamps_then_scales_under_default_order():
    spec = GOALS["regime_change"]
    vals = stage_values(2.0 / 0.1, spec, 0.0, 0.5, DEFAULT_ORDER)  # raw 20 -> S 2.0 -> clamp 3 -> rule 1.5 -> floor 1.5
    assert vals["C"] == pytest.approx(3.0) and vals["F"] == pytest.approx(1.5)

def test_nominal_charge_floor_binds_under_very_low():
    g = goal("conquer_state", n=1)          # raw 5
    assert nominal_charge(g, "standard") == pytest.approx(5.0)
    g_small = GoalInputs("conquer_state", (Component(0.0, 0.0, "unincorporated", "recognized", claim=True),),
                         "recognized", 0.0, 0.0)   # raw max(1, 5*0.5*0.25)=1
    assert nominal_charge(g_small, "very_low") == pytest.approx(1.0)
    assert nominal_charge(g_small, "very_high") == pytest.approx(1.5)

def test_general_modifier_applied():
    g = goal("conquer_state", n=2, general_mult=-0.05)
    assert nominal_charge(g, "standard") == pytest.approx(10 * 0.95)

def test_unknown_order_stage_rejected():
    with pytest.raises(ValueError):
        stage_values(1.0, GOALS["conquer_state"], 0.0, 1.0, ("S", "X"))
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_formula_goal.py`
Expected: FAIL with `ImportError: cannot import name 'GoalInputs'`

- [ ] **Step 3: Append to formula.py**

```python
# append to tools/hsi/formula.py

@dataclass(frozen=True)
class GoalSpec:
    severity: float                 # infamy_severity in the war goal file; 1.0 when absent
    clamp_min: float | None         # infamy_min, or None
    clamp_max: float | None         # infamy_max, or None
    subject_blocks: bool            # has the loyal/rebellious multiply blocks inside its infamy value
    single_component: bool          # acts on one scope:target_state
    requires_claim: bool | None     # return_state requires a claim, conquer_state rejects one, else None

GOALS: dict[str, GoalSpec] = {
    # common/war_goal_types/03_conquer_state.txt:24,34-36,57-93
    "conquer_state": GoalSpec(1.0, None, None, True, True, False),
    # 21_return_state.txt:24,34-36,57-62
    "return_state": GoalSpec(1.0, None, None, True, True, True),
    # 00_annex_country.txt:53-92
    "annex_country": GoalSpec(1.0, None, None, True, False, None),
    # 15_make_dominion / 16_make_protectorate / 17_make_tributary / 34_make_personal_union: severity 0.5
    "make_protectorate": GoalSpec(0.5, None, None, True, False, None),
    "make_dominion": GoalSpec(0.5, None, None, True, False, None),
    "make_tributary": GoalSpec(0.5, None, None, True, False, None),
    "make_personal_union": GoalSpec(0.5, None, None, True, False, None),
    # 26_transfer_subject.txt: severity 0.4
    "transfer_subject": GoalSpec(0.4, None, None, True, False, None),
    # 13_liberate_country.txt:45-56: severity 0.1, every_releasable_state, no subject blocks
    "liberate_country": GoalSpec(0.1, None, None, False, False, None),
    # 38_release_as_subject.txt:41-52: severity 0.6, releasable states, no subject blocks
    "release_as_subject": GoalSpec(0.6, None, None, False, False, None),
    # 20_regime_change.txt:42-84: severity 0.1, min MAJOR_DEMAND_MIN 3, max 10
    "regime_change": GoalSpec(0.1, 3.0, 10.0, True, False, None),
    # 29_restore_union.txt:69-75: severity 0.1, no subject blocks
    "restore_union": GoalSpec(0.1, None, None, False, False, None),
}

@dataclass(frozen=True)
class GoalInputs:
    wargoal: str
    components: tuple
    holder_type: str
    unrec_mult: float
    general_mult: float
    loyal_subject: bool = False
    rebellious_subject: bool = False

def raw_goal_value(g: GoalInputs) -> float:
    """The war goal's scripted `infamy` value: sum of state values, subject multipliers inside."""
    spec = GOALS[g.wargoal]
    raw = sum(component_value(c, g.holder_type, g.unrec_mult) for c in g.components)
    if spec.subject_blocks:
        if g.loyal_subject:
            raw *= K.SUBJECT_MULT
        if g.rebellious_subject:
            raw *= K.SUBJECT_MULT
    return raw

STAGES = ("S", "C", "G", "R", "F")          # severity, clamp, general modifier, rule, floor
DEFAULT_ORDER = ("S", "C", "G", "R", "F")   # spec hypothesis H1

def apply_stage(value: float, stage: str, spec: GoalSpec, general_mult: float, rule_mult: float) -> float:
    if stage == "S":
        return value * spec.severity
    if stage == "C":
        if spec.clamp_min is not None:
            value = max(value, spec.clamp_min)
        if spec.clamp_max is not None:
            value = min(value, spec.clamp_max)
        return value
    if stage == "G":
        return value * (1.0 + general_mult)
    if stage == "R":
        return value * rule_mult
    if stage == "F":
        return max(value, K.GOAL_MIN)
    raise ValueError(f"unknown stage {stage!r}")

def stage_values(raw: float, spec: GoalSpec, general_mult: float, rule_mult: float, order) -> dict[str, float]:
    """Running value after each stage, keyed by stage letter, for the given order."""
    out: dict[str, float] = {}
    v = raw
    for st in order:
        v = apply_stage(v, st, spec, general_mult, rule_mult)
        out[st] = v
    return out

def nominal_charge(g: GoalInputs, rule_key: str, order=DEFAULT_ORDER) -> float:
    """A_r(g): the finished charge for one goal under one rule setting (spec §7)."""
    spec = GOALS[g.wargoal]
    vals = stage_values(raw_goal_value(g), spec, g.general_mult, K.RULE_MULT[rule_key], order)
    return vals[order[-1]]
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/formula.py tools/tests/test_formula_goal.py
git commit -m "Add goal table, processing stages and nominal charge"
```

---

### Task 4: Ordering registry and fixture fit (spec §3 H1, §6 fixtures, §9 oracle B)

**Files:**
- Create: `tools/hsi/ordering.py`, `tools/tests/test_ordering.py`

**Interfaces:**
- Produces: `ordering.Line(stage: str, running_text: str | None, decimals: int)`; `ordering.Fixture(capture_id, wargoal, raw_subtotal, general_mult, rule_key, lines: tuple[Line, ...])` where `lines` are in display order and one line has `stage == "total"`; `ordering.fmt(value, decimals) -> str` (half-up rounding); `ordering.fits(order, fx) -> bool`; `ordering.equivalent(o1, o2, domain: list[GoalInputs]) -> bool`; `ordering.select_order(fixtures, domain) -> tuple`; exceptions `OrderingNoFit`, `OrderingAmbiguous(classes)`; `ordering.load_fixtures(path) -> list[Fixture]` reading `research/fixtures.json`.
- Consumes: `formula.GOALS`, `formula.stage_values`, `formula.nominal_charge`, `constants.RULE_MULT`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_ordering.py
import json
import pytest
from hsi.formula import Component, GoalInputs, DEFAULT_ORDER, GOALS
from hsi.ordering import (Line, Fixture, fmt, fits, equivalent, select_order, CANDIDATES,
                          OrderingNoFit, OrderingAmbiguous, load_fixtures)

def fx(capture, wargoal, raw, general, rule, *lines):
    return Fixture(capture, wargoal, raw, general, rule, tuple(lines))

def test_fmt_is_half_up_to_decimals():
    assert fmt(1.425, 1) == "1.4"
    assert fmt(1.45, 1) == "1.5"
    assert fmt(19.0, 1) == "19.0"
    assert fmt(0.5, 2) == "0.50"

def test_default_order_fits_h1_style_transcript():
    f = fx("A", "make_protectorate", 80.0, -0.05, "very_low",
           Line("S", None, 2), Line("G", None, 2), Line("R", None, 2), Line("total", "19.0", 1))
    assert fits(DEFAULT_ORDER, f)   # 80 x0.5 = 40, x0.95 = 38, x0.5 = 19

def test_transcript_order_constrains_candidates():
    # transcript shows the rule line before the clamp line: candidates with clamp before rule must fail
    f = fx("C", "regime_change", 20.0, 0.0, "very_low",
           Line("S", "2.00", 2), Line("R", "1.00", 2), Line("C", "3.00", 2), Line("total", "3.0", 1))
    assert not fits(DEFAULT_ORDER, f)
    assert fits(("S", "R", "C", "G", "F"), f)

def test_running_values_must_match_after_formatting():
    f = fx("B", "conquer_state", 10.0, 0.0, "very_low", Line("R", "5.00", 2), Line("total", "5.0", 1))
    assert fits(DEFAULT_ORDER, f)
    bad = fx("B", "conquer_state", 10.0, 0.0, "very_low", Line("R", "5.01", 2), Line("total", "5.0", 1))
    assert not fits(DEFAULT_ORDER, bad)

def domain():
    neutral = Component(2.0, 1.0, "incorporated", "recognized")
    return [GoalInputs("conquer_state", (neutral,), "recognized", 0.0, -0.05),
            GoalInputs("regime_change", (neutral, neutral), "recognized", 0.0, -0.05),
            GoalInputs("make_protectorate", (neutral, neutral, neutral), "recognized", -0.1, 0.0)]

def test_commuting_multiplications_are_equivalent():
    assert equivalent(("S", "C", "G", "R", "F"), ("S", "C", "R", "G", "F"), domain())

def test_clamp_floor_identity_is_equivalent_on_regime_bounds():
    # floor 1 before or after clamp [3,10] gives identical results on this domain (Review Focus 5)
    assert equivalent(("S", "C", "F", "G", "R"), ("S", "F", "C", "G", "R"), domain())

def test_moving_clamp_past_general_is_not_equivalent():
    assert not equivalent(("S", "C", "G", "R", "F"), ("S", "G", "C", "R", "F"), domain())

def test_select_order_unique_class():
    fixtures = [
        fx("A", "make_protectorate", 80.0, -0.05, "very_low", Line("S", "40.00", 2), Line("G", "38.00", 2), Line("R", "19.00", 2), Line("total", "19.0", 1)),
        fx("Cmax", "regime_change", 200.0, -0.05, "very_low", Line("S", "20.00", 2), Line("C", "10.00", 2), Line("G", "9.50", 2), Line("R", "4.75", 2), Line("total", "4.8", 1)),
        fx("Cmin", "regime_change", 20.0, -0.05, "very_low", Line("S", "2.00", 2), Line("C", "3.00", 2), Line("G", "2.85", 2), Line("R", "1.43", 2), Line("total", "1.4", 1)),
        fx("D", "conquer_state", 1.5, -0.05, "very_low", Line("G", "1.43", 2), Line("R", "0.71", 2), Line("F", "1.00", 2), Line("total", "1.0", 1)),
    ]
    order = select_order(fixtures, domain())
    assert order in (("S", "C", "G", "R", "F"), ("S", "C", "R", "G", "F"))

def test_select_order_no_fit_raises():
    fixtures = [fx("X", "conquer_state", 10.0, 0.0, "very_low", Line("total", "7.3", 1))]
    with pytest.raises(OrderingNoFit):
        select_order(fixtures, domain())

def test_select_order_ambiguous_raises_with_classes():
    # totals only, general factor 1: clamp-before-general and general-before-clamp both fit
    fixtures = [fx("A", "regime_change", 200.0, 0.0, "very_low", Line("total", "5.0", 1))]
    with pytest.raises(OrderingAmbiguous) as e:
        select_order(fixtures, domain())
    assert len(e.value.classes) >= 2

def test_load_fixtures_json(tmp_path):
    p = tmp_path / "fixtures.json"
    p.write_text(json.dumps([{"capture_id": "A", "wargoal": "make_protectorate", "raw_subtotal": 40.0,
                              "general_mult": -0.05, "rule_key": "very_low",
                              "lines": [{"stage": "S", "running_text": "20.00", "decimals": 2},
                                        {"stage": "total", "running_text": "9.5", "decimals": 1}]}]))
    fixtures = load_fixtures(p)
    assert fixtures[0].lines[0] == Line("S", "20.00", 2)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_ordering.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.ordering'`

- [ ] **Step 3: Implement ordering.py**

```python
# tools/hsi/ordering.py
"""Ordering registry for the goal-processing stages (spec §3 H1). A candidate is a permutation of
S, C, G, R, F. A fixture is a typed transcript of one in-game tooltip. Generation proceeds only when
exactly one equivalence class of candidates fits every fixture."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from itertools import permutations
import json
from pathlib import Path
from . import constants as K
from .formula import GOALS, STAGES, GoalInputs, stage_values, nominal_charge

@dataclass(frozen=True)
class Line:
    stage: str                 # one of STAGES, or "total"
    running_text: str | None   # the running value as displayed, or None when the UI shows only a multiplier
    decimals: int              # decimals the UI displayed for this line

@dataclass(frozen=True)
class Fixture:
    capture_id: str
    wargoal: str
    raw_subtotal: float        # the engine's own sum of state values before severity
    general_mult: float
    rule_key: str
    lines: tuple               # Line objects in display order; exactly one has stage == "total"

CANDIDATES = tuple(permutations(STAGES))

class OrderingNoFit(Exception):
    pass

class OrderingAmbiguous(Exception):
    def __init__(self, classes):
        super().__init__(f"{len(classes)} non-equivalent order classes fit the fixtures")
        self.classes = classes

def fmt(value: float, decimals: int) -> str:
    """UI-style half-up formatting. The float is first rounded to 9 decimals so binary noise
    (3 * 0.95 * 0.5 == 1.4249999999999998) cannot flip an exact-half case away from half-up."""
    q = Decimal(1).scaleb(-decimals)
    return str(Decimal(repr(round(value, 9))).quantize(q, rounding=ROUND_HALF_UP))

def fits(order, fx: Fixture) -> bool:
    spec = GOALS[fx.wargoal]
    vals = stage_values(fx.raw_subtotal, spec, fx.general_mult, K.RULE_MULT[fx.rule_key], order)
    stage_lines = [l for l in fx.lines if l.stage != "total"]
    positions = [order.index(l.stage) for l in stage_lines]
    if positions != sorted(positions):
        return False
    for l in stage_lines:
        if l.running_text is not None and fmt(vals[l.stage], l.decimals) != l.running_text:
            return False
    totals = [l for l in fx.lines if l.stage == "total"]
    if len(totals) != 1:
        raise ValueError(f"fixture {fx.capture_id} must have exactly one total line")
    return fmt(vals[order[-1]], totals[0].decimals) == totals[0].running_text

def equivalent(o1, o2, domain: list[GoalInputs]) -> bool:
    for g in domain:
        for rule in K.RULE_MULT:
            if abs(nominal_charge(g, rule, o1) - nominal_charge(g, rule, o2)) > 1e-9:
                return False
    return True

def select_order(fixtures: list[Fixture], domain: list[GoalInputs]):
    fitting = [o for o in CANDIDATES if all(fits(o, f) for f in fixtures)]
    if not fitting:
        raise OrderingNoFit("no candidate order reproduces every fixture")
    classes: list[list] = []
    for o in fitting:
        for cls in classes:
            if equivalent(o, cls[0], domain):
                cls.append(o)
                break
        else:
            classes.append([o])
    if len(classes) > 1:
        raise OrderingAmbiguous(classes)
    cls = classes[0]
    return tuple(STAGES) if tuple(STAGES) in cls else cls[0]

def load_fixtures(path: Path) -> list[Fixture]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for d in data:
        lines = tuple(Line(l["stage"], l.get("running_text"), int(l["decimals"])) for l in d["lines"])
        out.append(Fixture(d["capture_id"], d["wargoal"], float(d["raw_subtotal"]),
                           float(d["general_mult"]), d["rule_key"], lines))
    return out
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass. If `test_select_order_unique_class` fails on the Cmin line, recompute: raw 20 × 0.1 = 2.00 → clamp 3.00 → ×0.95 = 2.85 → ×0.5 = 1.425 → "1.43"; total floor 1.425 → "1.4".

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/ordering.py tools/tests/test_ordering.py
git commit -m "Add ordering registry, fixture fit and equivalence gate"
```

---

### Task 5: Country timeline replay (spec §7)

**Files:**
- Create: `tools/hsi/timeline.py`, `tools/tests/test_timeline.py`

**Interfaces:**
- Produces: `timeline.Event(date: datetime.date, kind: str, goal_id: str, delta: float)` with `kind in {"accrual","reduction","refund"}`; `timeline.KIND_RANK`; `timeline.decay(balance, days) -> float`; `timeline.replay(events, start=date(1816,1,1), horizon=date(1836,1,1)) -> float`; `timeline.replay_steps(events, ...) -> list[dict]` (one row per processed event with `date, kind, goal_id, before_decay, after_decay, delta, after_event`, plus a final `horizon` row).

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_timeline.py
from datetime import date
import pytest
from hsi.timeline import Event, decay, replay, replay_steps

D = date
def acc(y, m, d, g, v): return Event(D(y, m, d), "accrual", g, v)
def ref(y, m, d, g, v): return Event(D(y, m, d), "refund", g, -v)
def red(y, m, d, g, v): return Event(D(y, m, d), "reduction", g, -v)

def test_decay_is_linear_and_floored_at_zero():
    assert decay(10.0, 365.25) == pytest.approx(5.0)
    assert decay(2.0, 365.25) == 0.0

def test_single_balance_not_per_act():
    # two 20-point goals on the same day, read one year later: 35, not 30
    ev = [acc(1834, 1, 1, "a", 20), acc(1834, 1, 1, "b", 20)]
    assert replay(ev, horizon=D(1835, 1, 1)) == pytest.approx(35.0, abs=0.01)

def test_exhausted_balance_then_new_accrual_gets_full_charge():
    ev = [acc(1830, 1, 1, "a", 2), acc(1832, 1, 1, "b", 10)]
    # 2 has decayed to 0 long before 1832-01-01; the new goal lands on an empty balance, then one day of decay
    assert replay(ev, horizon=D(1832, 1, 2)) == pytest.approx(10.0 - 5 / 365.25, abs=1e-6)

def test_refund_after_isolated_zero_still_reduces_pooled_balance():
    ev = [acc(1830, 1, 1, "a", 10), acc(1833, 1, 1, "b", 30), ref(1833, 6, 1, "a", 5)]
    # a alone would be 0 by 1832; pooled: 10 decays to 0, +30 on 1833-01-01, 151 days of decay, -5 refund on
    # 1833-06-01 (still applied, the balance is pooled), then 30 more days of decay to the horizon
    v = replay(ev, horizon=D(1833, 7, 1))
    assert v == pytest.approx(30 - 5 * (151 / 365.25) - 5 - 5 * (30 / 365.25), abs=0.01)

def test_victim_reduction_cannot_go_below_zero():
    assert replay([red(1830, 1, 1, "a", 7)], horizon=D(1831, 1, 1)) == 0.0

def test_same_day_order_accrual_before_reduction_before_refund_and_row_order_irrelevant():
    ev1 = [ref(1835, 1, 1, "a", 10), acc(1835, 1, 1, "a", 10)]
    ev2 = list(reversed(ev1))
    assert replay(ev1, horizon=D(1835, 1, 2)) == replay(ev2, horizon=D(1835, 1, 2))
    assert replay(ev1, horizon=D(1835, 1, 2)) == pytest.approx(0.0, abs=1e-9)

def test_upper_bound_tie_order():
    ev = [red(1835, 1, 1, "x", 10), acc(1835, 1, 1, "y", 20)]
    start_high = [acc(1834, 12, 31, "z", 990)] + ev
    # 990 decays ~0.0137 overnight, then +20 -> clamp 1000, then -10 -> 990
    assert replay(start_high, horizon=D(1835, 1, 2)) == pytest.approx(990 - 5 / 365.25, abs=0.01)

def test_horizon_boundary_events():
    base = [acc(1835, 12, 31, "a", 10)]
    assert replay(base + [ref(1836, 1, 1, "a", 10)]) == pytest.approx(10 - 5 / 365.25, abs=0.001)
    assert replay(base + [ref(1836, 1, 2, "a", 10)]) == pytest.approx(10 - 5 / 365.25, abs=0.001)
    assert replay(base + [ref(1835, 12, 31, "a", 10)]) == 0.0

def test_final_interval_decays_to_zero_not_negative():
    assert replay([acc(1820, 1, 1, "a", 10)]) == 0.0

def test_replay_steps_rows():
    rows = replay_steps([acc(1835, 1, 1, "a", 10)])
    assert rows[0]["kind"] == "accrual" and rows[0]["after_event"] == pytest.approx(10.0)
    assert rows[-1]["kind"] == "horizon" and rows[-1]["after_decay"] == pytest.approx(10 - 5.0, abs=0.01)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_timeline.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.timeline'`

- [ ] **Step 3: Implement timeline.py**

```python
# tools/hsi/timeline.py
"""One decaying infamy balance per country (spec §7). Finished deltas in, balance out.
Recurrence: before each event I = max(0, I - 5*days/365.25); then I = min(1000, max(0, I + delta));
after the last processed event decay again to the horizon. Events dated on/after the horizon are ignored."""
from dataclasses import dataclass
from datetime import date
from . import constants as K

KIND_RANK = {"accrual": 0, "reduction": 1, "refund": 2}

@dataclass(frozen=True)
class Event:
    date: date
    kind: str       # accrual (+), reduction (-), refund (-)
    goal_id: str
    delta: float

def _parse(d: str) -> date:
    return date.fromisoformat(d)

def decay(balance: float, days: float) -> float:
    return max(K.INFAMY_MIN, balance - K.DECAY_PER_YEAR * days / K.DAYS_PER_YEAR)

def _ordered(events, horizon):
    kept = [e for e in events if e.date < horizon]
    for e in kept:
        if e.kind not in KIND_RANK:
            raise ValueError(f"unknown event kind {e.kind!r}")
    return sorted(kept, key=lambda e: (e.date, KIND_RANK[e.kind], e.goal_id))

def replay_steps(events, start: date | None = None, horizon: date | None = None) -> list[dict]:
    start = start or _parse(K.WINDOW_START)
    horizon = horizon or _parse(K.HORIZON)
    balance = 0.0
    cursor = start
    rows = []
    for e in _ordered(events, horizon):
        before = balance
        balance = decay(balance, (e.date - cursor).days)
        after_decay = balance
        balance = min(K.INFAMY_MAX, max(K.INFAMY_MIN, balance + e.delta))
        cursor = e.date
        rows.append({"date": e.date.isoformat(), "kind": e.kind, "goal_id": e.goal_id,
                     "before_decay": before, "after_decay": after_decay, "delta": e.delta,
                     "after_event": balance})
    before = balance
    balance = decay(balance, (horizon - cursor).days)
    rows.append({"date": horizon.isoformat(), "kind": "horizon", "goal_id": "",
                 "before_decay": before, "after_decay": balance, "delta": 0.0, "after_event": balance})
    return rows

def replay(events, start: date | None = None, horizon: date | None = None) -> float:
    return replay_steps(events, start, horizon)[-1]["after_event"]
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/timeline.py tools/tests/test_timeline.py
git commit -m "Add per-country infamy timeline replay"
```

---

### Task 6: Ledger schema, loading and validation (spec §5, §7 refusals)

**Files:**
- Create: `tools/hsi/ledger.py`, `tools/tests/test_ledger.py`, `tools/tests/fixtures/ledger_ok/acts.csv`, `tools/tests/fixtures/ledger_ok/goals.csv`, `tools/tests/fixtures/ledger_ok/goal_states.csv`

**Interfaces:**
- Produces: dataclasses `ledger.Act`, `ledger.Goal` (fields exactly the `goals.csv` columns, with `claim_date: date`, `resolution_date: date | None`, `loyal_subject: bool`, `rebellious_subject: bool`), `ledger.GoalState` (fields exactly the `goal_states.csv` columns, with `slices_1836: tuple[str, ...]`, booleans, `interest_tier: int`), `ledger.Ledger` with `.acts: dict[str, Act]`, `.goals: dict[str, Goal]`, `.goal_states: list[GoalState]`, `.components_of(goal_id) -> list[GoalState]`, `.all_slices() -> set[tuple[str, str]]`, `.holder_tags() -> set[str]`; `ledger.load_ledger(research_dir: Path) -> Ledger`; `ledger.load_vanilla_tags(game_dir: Path) -> set[str]`; `ledger.validate_ledger(ledger, vanilla_tags) -> None` raising `ledger.LedgerError` whose `.messages` lists every problem; CLI `python3 -m hsi.ledger <research_dir> --game-dir <dir>`.
- Consumes: `formula.GOALS`, `constants.WINDOW_START/WINDOW_END`.

- [ ] **Step 1: Create the fixture ledger** (used again by Tasks 7, 8 and 11)

```csv
# tools/tests/fixtures/ledger_ok/acts.csv
act_id,title,start_date,end_date,source,notes
test_syria,Fixture: conquest of Syria,1831-10-01,1833-05-01,fixture_src,fixture act
test_greece,Fixture: backing Greek independence,1827-07-01,1830-02-01,fixture_src,fixture act
```

```csv
# tools/tests/fixtures/ledger_ok/goals.csv
goal_id,act_id,wargoal,holder,holder_tag_1836,holder_type,target,stakeholder,victim_tag_1836,claim_date,resolution,resolution_date,loyal_subject,rebellious_subject,general_mult_source,notes
g_aleppo,test_syria,conquer_state,EGY,EGY,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture
g_syria,test_syria,conquer_state,EGY,EGY,unrecognized,TUR,,TUR,1831-10-01,enforced,1833-05-01,0,0,measured_1836,fixture
g_greece,test_greece,liberate_country,GBR,GBR,recognized,TUR,,TUR,1827-07-01,enforced,1830-02-01,0,0,measured_1836,fixture
g_pending,test_syria,make_protectorate,EGY,EGY,unrecognized,HDJ,TUR,,1835-11-01,pending,,0,0,measured_1836,fixture pending goal
```

```csv
# tools/tests/fixtures/ledger_ok/goal_states.csv
goal_id,component_id,state_key,slices_1836,owner_type,standing,aggressor_homeland,shared_language,claim,scripted_unification,adjacent,interest_tier,justification
g_aleppo,c1,STATE_ALEPPO,EGY,recognized,homeland,0,1,0,0,1,3,fixture
g_syria,c1,STATE_SYRIA,EGY,recognized,incorporated,0,1,0,0,1,3,fixture
g_greece,c1,STATE_ATTICA,GRE,recognized,incorporated,0,0,0,0,0,3,fixture
g_greece,c2,STATE_PELOPONNESE,GRE,recognized,incorporated,0,0,0,0,0,3,fixture
g_pending,c1,STATE_HEDJAZ,HDJ,unrecognized,capital,0,1,0,0,1,3,fixture
```

(Write them without the leading `# path` comment lines; those are labels for this plan.)

- [ ] **Step 2: Write the failing tests**

```python
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
```

- [ ] **Step 3: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_ledger.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.ledger'`

- [ ] **Step 4: Implement ledger.py**

```python
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
```

- [ ] **Step 5: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass. The `pending` mutation and the `general_mult_source` mutation are checked by `validate_ledger`, not by `load_ledger`.

- [ ] **Step 6: Commit**

```bash
git add tools/hsi/ledger.py tools/tests/test_ledger.py tools/tests/fixtures/ledger_ok/
git commit -m "Add ledger loading and validation with refusals"
```

---

### Task 7: Measurement records, snapshot selection, manifest (spec §6, §7)

**Files:**
- Create: `tools/hsi/measurement.py`, `tools/tests/test_measurement.py`, `tools/tests/fixtures/make_probe_log.py`

**Interfaces:**
- Record line format (fixed here, produced by Task 8, consumed by Task 11):
  `HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v;k=v…` with `hook ∈ {start_a, start_b, monthly}`, `sample` an integer (0 for start hooks), `date` a literal `lobby` for start hooks or the engine's `GetString` date (`February 1, 1836`) for monthly records, `kind ∈ {GLOBAL, STATE, COUNTRY, DIAG, RULE}`, `key`: `-` for GLOBAL and RULE, `STATE_KEY/OWNER` for STATE, `TAG` for COUNTRY, `HOLDER/STATE_KEY/OWNER` for DIAG. Fields per kind:
  - GLOBAL: `pop`, `gdp`
  - STATE: `owner_type` (0 recognized, 1 unrecognized, 2 decentralized), `pop`, `gdp`, `pop_share_uncapped`, `gdp_share_uncapped`, `incorporated`, `capital`, `owner_homeland`, `base`
  - COUNTRY: `country_type` (0/1/2), `gen_mult`, `unrec_mult`, `decay_mult`, `infamy`
  - DIAG: `root_tag`, `aggressor_homeland`, `homeland_bonus`, `shared_language`, `language_bonus`, `claim`, `scripted_unification`, `adjacent`, `interest_bucket` (1, 2, 3 or 5), `root_type`, `owner_type`, `siv`
  - RULE: `flag` (`very_low`, `low`, `standard`, `high`, `very_high`)
- Produces: `measurement.Record(hook, sample: int, date: str, kind, key, fields: dict[str, str])`; `measurement.parse_number(s) -> float`; `measurement.parse_lines(lines) -> list[Record]`; `measurement.extract(debug_log_path) -> list[str]` (the `HSI;…` payloads); `measurement.group_samples(records) -> dict[tuple[str, int], list[Record]]` (raises `MeasurementError` on duplicate (hook, sample, kind, key)); `measurement.Snapshot` with `.hook, .sample, .date, .global_pop, .global_gdp, .slice(state_key, owner) -> dict[str, float]`, `.country(tag) -> dict[str, float]`, `.diag: dict[tuple[str, str, str], dict[str, float]]`, `.rule: str | None`; `measurement.build_snapshot(records) -> Snapshot`; `measurement.choose_snapshot(records, required_slices, required_tags, tolerance=0.02) -> Snapshot` (last monthly sample; raises `MeasurementError` if incomplete, `StabilizationError` on the 2 % policy); `measurement.write_manifest(dir, names) -> Path`; `measurement.verify_manifest(dir) -> list[str]` (raises `ManifestError`); CLI `python3 -m hsi.measurement extract --debug-log <p> --out <p>`.

- [ ] **Step 1: Write the fixture log generator**

```python
# tools/tests/fixtures/make_probe_log.py
"""Deterministic synthetic probe output matching the fixture ledger. Used by test_measurement and the
Task 11 golden test. Numbers are invented but internally consistent with hsi.formula."""
from pathlib import Path

SLICES = [("STATE_ALEPPO", "EGY", 0), ("STATE_SYRIA", "EGY", 0), ("STATE_ATTICA", "GRE", 0),
          ("STATE_PELOPONNESE", "GRE", 0), ("STATE_HEDJAZ", "HDJ", 1)]
COUNTRIES = {"EGY": (1, -0.05, -0.1, 0.0, 0.0), "GBR": (0, -0.05, -0.3, 0.1, 0.0),
             "BOL": (0, 0.0, 0.0, 0.0, 50.0), "FRA": (0, -0.05, -0.3, 0.0, 0.0)}
HOLDERS = ["EGY", "GBR"]

def shares(i, sample):
    pop = 1.90 + 0.10 * i + 0.002 * sample
    gdp = 0.0 if sample == 0 else 1.10 + 0.05 * i + 0.001 * sample
    return pop, gdp

def lines(months=3, zero_gdp_at_start=True):
    out = []
    def state_lines(hook, sample, datestr):
        out.append(f"HSI;{hook};{sample};{datestr};GLOBAL;-;pop=1,022,805,087;gdp=2,000,000,000.00")
        for i, (sk, owner, otype) in enumerate(SLICES):
            pop, gdp = shares(i, sample)
            out.append(f"HSI;{hook};{sample};{datestr};STATE;{sk}/{owner};owner_type={otype};pop=500,000;gdp=300,000.00;"
                       f"pop_share_uncapped={pop:.4f};gdp_share_uncapped={gdp:.4f};incorporated=1;capital=0;owner_homeland=1;base={(5+pop+gdp)*1.5:.4f}")
        for tag, (ctype, gen, unrec, decay, inf) in COUNTRIES.items():
            out.append(f"HSI;{hook};{sample};{datestr};COUNTRY;{tag};country_type={ctype};gen_mult={gen:.4f};unrec_mult={unrec:.4f};decay_mult={decay:.4f};infamy={inf:.4f}")
    for hook in ("start_a", "start_b"):
        state_lines(hook, 0, "lobby")
        out.append(f"HSI;{hook};0;lobby;RULE;-;flag=very_low")
    for m in range(1, months + 1):
        datestr = ["February 1, 1836", "March 1, 1836", "April 1, 1836"][m - 1]
        state_lines("monthly", m, datestr)
        for holder in HOLDERS:
            for i, (sk, owner, otype) in enumerate(SLICES):
                pop, gdp = shares(i, m)
                siv = (5 + pop + gdp) * 1.5 * (0.85 if holder == "EGY" else 1.0) * (0.9 if holder == "EGY" else 1.0)
                if holder == "GBR" and otype != 0:
                    siv *= 1.0 + COUNTRIES["GBR"][2]      # recognized holder vs unrecognized owner: x(1 + unrec_mult)
                out.append(f"HSI;monthly;{m};{datestr};DIAG;{holder}/{sk}/{owner};root_tag={holder};aggressor_homeland=0;homeland_bonus=0;"
                           f"shared_language={1 if holder == 'EGY' else 0};language_bonus=0;claim=0;scripted_unification=0;"
                           f"adjacent={1 if holder == 'EGY' else 0};interest_bucket=3;root_type={1 if holder == 'EGY' else 0};owner_type={otype};siv={max(siv, 1.0):.4f}")
    return out

def write(path: Path, **kw):
    body = "\n".join(f"[12:00:00][jomini_script_system.cpp:123]: {l}" for l in lines(**kw)) + "\n"
    path.write_text(body, encoding="utf-8")
    return path

if __name__ == "__main__":
    import sys
    write(Path(sys.argv[1]))
```

- [ ] **Step 2: Write the failing tests**

```python
# tools/tests/test_measurement.py
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
import make_probe_log
from hsi.measurement import (parse_number, parse_lines, extract, group_samples, build_snapshot,
                             choose_snapshot, write_manifest, verify_manifest,
                             MeasurementError, StabilizationError, ManifestError)

def records(tmp_path, **kw):
    p = make_probe_log.write(tmp_path / "debug.log", **kw)
    return parse_lines(extract(p))

def test_parse_number_handles_separators_and_unicode_minus():
    assert parse_number("1,022,805,087") == 1022805087.0
    assert parse_number("−0.05") == -0.05
    assert parse_number(" 3.75 ") == 3.75
    with pytest.raises(MeasurementError):
        parse_number("abc")
    with pytest.raises(MeasurementError):
        parse_number("nan")
    with pytest.raises(MeasurementError):
        parse_number("inf")

def test_extract_finds_payload_after_engine_prefix(tmp_path):
    p = make_probe_log.write(tmp_path / "debug.log")
    payloads = extract(p)
    assert all(l.startswith("HSI;") for l in payloads)
    assert len(payloads) == len(make_probe_log.lines())

def test_group_samples_and_duplicate_refused(tmp_path):
    recs = records(tmp_path)
    groups = group_samples(recs)
    assert ("start_a", 0) in groups and ("monthly", 3) in groups
    with pytest.raises(MeasurementError):
        group_samples(recs + [recs[0]])

def test_build_snapshot_fields(tmp_path):
    groups = group_samples(records(tmp_path))
    snap = build_snapshot(groups[("monthly", 3)])
    assert snap.global_pop == 1022805087.0
    s = snap.slice("STATE_ALEPPO", "EGY")
    assert s["pop_share_uncapped"] == pytest.approx(1.906)
    assert snap.country("EGY")["unrec_mult"] == pytest.approx(-0.1)
    assert snap.diag[("EGY", "STATE_ALEPPO", "EGY")]["shared_language"] == 1.0
    start = build_snapshot(groups[("start_b", 0)])
    assert start.rule == "very_low" and start.date == "lobby"

def test_choose_snapshot_takes_last_monthly_and_checks_completeness(tmp_path):
    recs = records(tmp_path)
    required = {("STATE_ALEPPO", "EGY"), ("STATE_HEDJAZ", "HDJ")}
    snap = choose_snapshot(recs, required, {"EGY", "GBR"})
    assert snap.sample == 3 and snap.hook == "monthly"
    with pytest.raises(MeasurementError):
        choose_snapshot(recs, required | {("STATE_NOWHERE", "XXX")}, {"EGY"})
    with pytest.raises(MeasurementError):
        choose_snapshot(recs, required, {"EGY", "RUS"})

def test_stabilization_policy(tmp_path):
    recs = records(tmp_path)
    required = {("STATE_ALEPPO", "EGY")}
    # the fixture drifts 0.002/month on ~1.9: ~0.1%, passes
    choose_snapshot(recs, required, {"EGY"})
    # inject a 10% jump into the last sample
    jumped = []
    for r in recs:
        if r.hook == "monthly" and r.sample == 3 and r.kind == "STATE" and r.key == "STATE_ALEPPO/EGY":
            f = dict(r.fields); f["pop_share_uncapped"] = "2.2000"
            r = type(r)(r.hook, r.sample, r.date, r.kind, r.key, f)
        jumped.append(r)
    with pytest.raises(StabilizationError):
        choose_snapshot(jumped, required, {"EGY"})

def test_stabilization_zero_transitions(tmp_path):
    recs = records(tmp_path)
    required = {("STATE_ALEPPO", "EGY")}
    def set_gdp(rs, sample, value):
        out = []
        for r in rs:
            if r.hook == "monthly" and r.sample == sample and r.kind == "STATE" and r.key == "STATE_ALEPPO/EGY":
                f = dict(r.fields); f["gdp_share_uncapped"] = value
                r = type(r)(r.hook, r.sample, r.date, r.kind, r.key, f)
            out.append(r)
        return out
    both_zero = set_gdp(set_gdp(recs, 2, "0.0000"), 3, "0.0000")
    choose_snapshot(both_zero, required, {"EGY"})            # zero -> zero passes
    with pytest.raises(StabilizationError):
        choose_snapshot(set_gdp(recs, 2, "0.0000"), required, {"EGY"})   # zero -> positive fails

def test_manifest_roundtrip_and_tamper(tmp_path):
    d = tmp_path / "m"; d.mkdir()
    (d / "a.log").write_text("one"); (d / "b.txt").write_text("two")
    write_manifest(d, ["a.log", "b.txt"])
    assert verify_manifest(d) == ["a.log", "b.txt"]
    (d / "a.log").write_text("changed")
    with pytest.raises(ManifestError):
        verify_manifest(d)

def test_manifest_rejects_unexpected_and_missing_files(tmp_path):
    d = tmp_path / "m"; d.mkdir()
    (d / "a.log").write_text("one")
    write_manifest(d, ["a.log"])
    (d / "extra.txt").write_text("x")
    with pytest.raises(ManifestError):
        verify_manifest(d)
    (d / "extra.txt").unlink(); (d / "a.log").unlink()
    with pytest.raises(ManifestError):
        verify_manifest(d)
```

- [ ] **Step 3: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_measurement.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.measurement'`

- [ ] **Step 4: Implement measurement.py**

```python
# tools/hsi/measurement.py
"""Probe output: HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v... (spec §6). Snapshot selection with the
2 % stabilization policy and the measurement manifest (spec §6, §7)."""
from dataclasses import dataclass
import hashlib
import math
import re
import sys
from pathlib import Path

KINDS = {"GLOBAL", "STATE", "COUNTRY", "DIAG", "RULE"}
MANIFEST = "manifest.sha256"
SAVES_DIR = "saves"   # gitignored; never listed in the manifest

class MeasurementError(Exception):
    pass

class StabilizationError(MeasurementError):
    pass

class ManifestError(Exception):
    pass

@dataclass(frozen=True)
class Record:
    hook: str
    sample: int
    date: str
    kind: str
    key: str
    fields: dict

_NUM_CLEAN = str.maketrans({",": "", " ": "", "−": "-", " ": ""})

def parse_number(s: str) -> float:
    t = s.translate(_NUM_CLEAN)
    try:
        x = float(t)
    except ValueError:
        raise MeasurementError(f"not a number: {s!r}")
    if not math.isfinite(x):
        raise MeasurementError(f"non-finite number: {s!r}")
    return x

def extract(debug_log: Path) -> list:
    out = []
    with open(debug_log, encoding="utf-8", errors="replace") as f:
        for line in f:
            i = line.find("HSI;")
            if i >= 0:
                out.append(line[i:].rstrip("\r\n"))
    return out

def parse_lines(lines) -> list:
    recs = []
    for n, line in enumerate(lines, start=1):
        parts = line.split(";")
        if len(parts) < 6 or parts[0] != "HSI":
            raise MeasurementError(f"line {n}: malformed record {line!r}")
        _, hook, sample, date, kind, key = parts[:6]
        if kind not in KINDS:
            raise MeasurementError(f"line {n}: unknown kind {kind!r}")
        try:
            sample_i = int(sample)
        except ValueError:
            raise MeasurementError(f"line {n}: sample must be an integer, got {sample!r}")
        fields = {}
        for kv in parts[6:]:
            if "=" not in kv:
                raise MeasurementError(f"line {n}: field without '=': {kv!r}")
            k, v = kv.split("=", 1)
            if k in fields:
                raise MeasurementError(f"line {n}: duplicate field {k}")
            fields[k] = v
        recs.append(Record(hook, sample_i, date, kind, key, fields))
    return recs

def group_samples(records) -> dict:
    groups: dict = {}
    seen = set()
    for r in records:
        ident = (r.hook, r.sample, r.kind, r.key)
        if ident in seen:
            raise MeasurementError(f"duplicate record {ident}")
        seen.add(ident)
        groups.setdefault((r.hook, r.sample), []).append(r)
    return groups

@dataclass
class Snapshot:
    hook: str
    sample: int
    date: str
    global_pop: float
    global_gdp: float
    slices: dict
    countries: dict
    diag: dict
    rule: str | None

    def slice(self, state_key: str, owner: str) -> dict:
        try:
            return self.slices[(state_key, owner)]
        except KeyError:
            raise MeasurementError(f"slice {state_key}/{owner} not in sample {self.hook}/{self.sample}")

    def country(self, tag: str) -> dict:
        try:
            return self.countries[tag]
        except KeyError:
            raise MeasurementError(f"country {tag} not in sample {self.hook}/{self.sample}")

def _numeric(fields: dict, skip=()) -> dict:
    return {k: parse_number(v) for k, v in fields.items() if k not in skip}

def build_snapshot(records) -> Snapshot:
    globals_ = [r for r in records if r.kind == "GLOBAL"]
    if len(globals_) != 1:
        raise MeasurementError(f"sample needs exactly one GLOBAL record, has {len(globals_)}")
    g = globals_[0]
    slices, countries, diag, rule = {}, {}, {}, None
    for r in records:
        if r.kind == "STATE":
            sk, owner = r.key.split("/")
            slices[(sk, owner)] = _numeric(r.fields)
        elif r.kind == "COUNTRY":
            countries[r.key] = _numeric(r.fields)
        elif r.kind == "DIAG":
            holder, sk, owner = r.key.split("/")
            d = _numeric(r.fields, skip=("root_tag",))
            d["root_tag"] = r.fields.get("root_tag", "")
            if d["root_tag"] != holder:
                raise MeasurementError(f"DIAG {r.key}: root_tag {d['root_tag']!r} is not the holder")
            diag[(holder, sk, owner)] = d
        elif r.kind == "RULE":
            rule = r.fields.get("flag")
    return Snapshot(g.hook, g.sample, g.date, parse_number(g.fields["pop"]), parse_number(g.fields["gdp"]),
                    slices, countries, diag, rule)

def _rel_change(prev: float, cur: float):
    if prev == 0.0 and cur == 0.0:
        return 0.0
    if prev == 0.0 or cur == 0.0:
        return None
    return abs(cur - prev) / abs(prev)

def choose_snapshot(records, required_slices, required_tags, tolerance: float = 0.02) -> Snapshot:
    groups = group_samples(records)
    monthly = sorted(k for k in groups if k[0] == "monthly")
    if len(monthly) < 2:
        raise MeasurementError("need at least two monthly samples")
    last, prev = build_snapshot(groups[monthly[-1]]), build_snapshot(groups[monthly[-2]])
    missing = [s for s in required_slices if s not in last.slices]
    if missing:
        raise MeasurementError(f"last sample lacks slices: {sorted(missing)}")
    missing_tags = [t for t in required_tags if t not in last.countries]
    if missing_tags:
        raise MeasurementError(f"last sample lacks countries: {sorted(missing_tags)}")
    problems = []
    for sk, owner in sorted(required_slices):
        for field in ("pop_share_uncapped", "gdp_share_uncapped"):
            p, c = prev.slice(sk, owner)[field], last.slice(sk, owner)[field]
            rc = _rel_change(p, c)
            if rc is None:
                problems.append(f"{sk}/{owner} {field}: zero transition {p} -> {c}")
            elif rc > tolerance:
                problems.append(f"{sk}/{owner} {field}: relative change {rc:.3%} > {tolerance:.0%}")
    if problems:
        raise StabilizationError("\n".join(problems))
    return last

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(directory: Path, names) -> Path:
    directory = Path(directory)
    names = sorted(names)
    if MANIFEST in names:
        raise ManifestError("the manifest never lists itself")
    body = "".join(f"{sha256_file(directory / n)}  {n}\n" for n in names)
    out = directory / MANIFEST
    out.write_text(body, encoding="utf-8")
    return out

def verify_manifest(directory: Path) -> list:
    directory = Path(directory)
    mp = directory / MANIFEST
    if not mp.exists():
        raise ManifestError(f"{mp} missing")
    listed = {}
    for line in mp.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        listed[name] = digest
    present = {p.name for p in directory.iterdir() if p.is_file() and p.name != MANIFEST}
    problems = [f"unexpected file {n}" for n in sorted(present - set(listed))]
    for name, digest in listed.items():
        p = directory / name
        if not p.exists():
            problems.append(f"missing file {name}")
        elif sha256_file(p) != digest:
            problems.append(f"digest mismatch {name}")
    if problems:
        raise ManifestError("\n".join(problems))
    return sorted(listed)

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract"); ex.add_argument("--debug-log", required=True); ex.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "extract":
        payloads = extract(Path(a.debug_log))
        recs = parse_lines(payloads)
        groups = group_samples(recs)
        Path(a.out).write_text("\n".join(payloads) + "\n", encoding="utf-8")
        for (hook, sample), rs in sorted(groups.items()):
            kinds = {}
            for r in rs:
                kinds[r.kind] = kinds.get(r.kind, 0) + 1
            print(f"{hook} sample {sample} date {rs[0].date}: {kinds}")
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass. `verify_manifest` ignores subdirectories such as `saves/` by design (`is_file()`).

- [ ] **Step 6: Commit**

```bash
git add tools/hsi/measurement.py tools/tests/test_measurement.py tools/tests/fixtures/make_probe_log.py
git commit -m "Add probe record parsing, snapshot selection and manifest"
```

---

### Task 8: Probe mod generator and boot procedure (spec §6)

**Files:**
- Create: `tools/hsi/probe_gen.py`, `tools/tests/test_probe_gen.py`, `research/probe/config.json`, `research/measurement/PROCEDURE.md`
- Generated at run time (committed once produced): `research/probe/.metadata/metadata.json`, `research/probe/common/on_actions/zz_hsi_probe_on_actions.txt`, `research/probe/common/script_values/zz_hsi_probe_values.txt`, `research/probe/common/scripted_effects/zz_hsi_probe_effects.txt`

**Interfaces:**
- Consumes: `ledger.Ledger` (`all_slices()`, `holder_tags()`), `bom.write_text_bom`.
- Produces: `probe_gen.write_probe(probe_dir: Path, led: Ledger, config: dict) -> list[Path]`; `probe_gen.render(led, config) -> dict[str, str]` (relative path → text); CLI `python3 -m hsi.probe_gen --research research --out research/probe`.
- `config.json`: `{"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3}`. The sampler emits GLOBAL/STATE/COUNTRY in its monthly pulse; every holder emits its own DIAG lines; the fixture holder and BOL are added to the COUNTRY list and the monthly guard.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_probe_gen.py
from pathlib import Path
from hsi.ledger import load_ledger
from hsi.probe_gen import render, write_probe
from hsi.bom import has_bom

FIX = Path(__file__).parent / "fixtures" / "ledger_ok"
CFG = {"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3}

def test_render_contains_every_slice_holder_and_hook():
    files = render(load_ledger(FIX), CFG)
    eff = files["common/scripted_effects/zz_hsi_probe_effects.txt"]
    on = files["common/on_actions/zz_hsi_probe_on_actions.txt"]
    for sk, owner in [("STATE_ALEPPO", "EGY"), ("STATE_PELOPONNESE", "GRE"), ("STATE_HEDJAZ", "HDJ")]:
        assert f"s:{sk}.region_state:{owner} ?= {{" in eff
        assert f"STATE;{sk}/{owner};" in eff
    for tag in ("EGY", "GBR", "BOL", "FRA"):
        assert f"COUNTRY;{tag};" in eff
    assert "DIAG;EGY/STATE_ALEPPO/EGY;" in eff and "DIAG;GBR/STATE_ALEPPO/EGY;" in eff
    assert "on_game_started = {\n\ton_actions = { hsi_probe_start_a }" in on
    assert "on_game_started_after_lobby = {\n\ton_actions = { hsi_probe_start_b }" in on
    assert "on_monthly_pulse_country = {\n\ton_actions = { hsi_probe_monthly }" in on
    assert "has_game_rule = infamy_generation_very_low" in eff and "flag=standard" in eff
    assert "var:hsi_sample <= 3" in eff
    assert "[TimeKeeper.GetCurrentDate.GetString]" in eff and "HSI;$HOOK$;0;lobby;" in eff
    assert "hsi_probe_start_records = { HOOK = start_a }" in on and "hsi_probe_start_records = { HOOK = start_b }" in on
    assert "state_infamy_population_share_uncapped" in eff and "set_variable = { name = hsi_siv value = state_infamy_value }" in eff

def test_write_probe_writes_bom_files(tmp_path):
    paths = write_probe(tmp_path / "probe", load_ledger(FIX), CFG)
    names = {p.relative_to(tmp_path / "probe").as_posix() for p in paths}
    assert "common/scripted_effects/zz_hsi_probe_effects.txt" in names
    assert ".metadata/metadata.json" in names
    for p in paths:
        if p.suffix == ".txt":
            assert has_bom(p)
    assert (tmp_path / "probe" / ".metadata" / "metadata.json").read_text().count('"name": "HSI Probe"') == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_probe_gen.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.probe_gen'`

- [ ] **Step 3: Implement probe_gen.py**

```python
# tools/hsi/probe_gen.py
"""Generates the throwaway probe mod from the ledger (spec §6). Never shipped."""
import json
from pathlib import Path
from .bom import write_text_bom
from .ledger import Ledger, load_ledger

def _flag(var: str, trigger: str) -> str:
    return (f"\tif = {{ limit = {{ {trigger} }} set_variable = {{ name = {var} value = 1 }} }}\n"
            f"\telse = {{ set_variable = {{ name = {var} value = 0 }} }}\n")

def _type_code(var: str, scope_open: str) -> str:
    """scope_open is '' (current scope), 'owner = { ' or 'root = { '; the brace is closed when one was opened."""
    close = " }" if scope_open else ""
    def t(kind):
        return f"{scope_open}is_country_type = {kind}{close}"
    return (f"\tif = {{ limit = {{ {t('decentralized')} }} set_variable = {{ name = {var} value = 2 }} }}\n"
            f"\telse_if = {{ limit = {{ {t('unrecognized')} }} set_variable = {{ name = {var} value = 1 }} }}\n"
            f"\telse = {{ set_variable = {{ name = {var} value = 0 }} }}\n")

def _sv(var: str) -> str:
    return f"[SCOPE.sState('hsi_state').MakeScope.Var('{var}').GetValue|0]"

def _state_line(hook: str, sample_expr: str, date_expr: str, sk: str, owner: str) -> str:
    s = "SCOPE.sState('hsi_state').MakeScope"
    return (f'\t\tdebug_log = "HSI;{hook};{sample_expr};{date_expr};STATE;{sk}/{owner};owner_type={_sv("hsi_ot")};'
            f"pop=[{s}.ScriptValue('hsi_probe_state_pop')|0];gdp=[{s}.ScriptValue('hsi_probe_state_gdp')|2];"
            f"pop_share_uncapped=[{s}.ScriptValue('state_infamy_population_share_uncapped')|4];"
            f"gdp_share_uncapped=[{s}.ScriptValue('state_infamy_gdp_share_uncapped')|4];"
            f"incorporated={_sv('hsi_inc')};capital={_sv('hsi_cap')};owner_homeland={_sv('hsi_oh')};"
            f"base=[{s}.ScriptValue('state_infamy_base')|4]\"\n")

def _country_line(hook: str, sample_expr: str, date_expr: str, tag: str) -> str:
    c = "SCOPE.sCountry('hsi_country').MakeScope"
    return (f'\t\tdebug_log = "HSI;{hook};{sample_expr};{date_expr};COUNTRY;{tag};country_type=[{c}.Var(\'hsi_ct\').GetValue|0];'
            f"gen_mult=[{c}.ScriptValue('hsi_probe_gen')|4];unrec_mult=[{c}.ScriptValue('hsi_probe_unrec')|4];"
            f"decay_mult=[{c}.ScriptValue('hsi_probe_decay')|4];infamy=[{c}.ScriptValue('hsi_probe_infamy')|4]\"\n")

def _records_block(hook: str, sample_expr: str, date_expr: str, slices, tags, sampler: str) -> str:
    out = []
    out.append(f"\tc:{sampler} ?= {{\n\t\tset_global_variable = {{ name = hsi_gpop value = global_population }}\n"
               f"\t\tset_global_variable = {{ name = hsi_ggdp value = global_gdp }}\n\t}}\n")
    out.append(f'\tdebug_log = "HSI;{hook};{sample_expr};{date_expr};GLOBAL;-;pop=[GetGlobalVariable(\'hsi_gpop\').GetValue|0];'
               f"gdp=[GetGlobalVariable('hsi_ggdp').GetValue|2]\"\n")
    for sk, owner in sorted(slices):
        out.append(f"\ts:{sk}.region_state:{owner} ?= {{\n\t\tsave_scope_as = hsi_state\n\t\thsi_probe_state_flags = yes\n")
        out.append(_state_line(hook, sample_expr, date_expr, sk, owner))
        out.append("\t}\n")
    for tag in sorted(tags):
        out.append(f"\tc:{tag} ?= {{\n\t\tsave_scope_as = hsi_country\n\t\thsi_probe_country_flags = yes\n")
        out.append(_country_line(hook, sample_expr, date_expr, tag))
        out.append("\t}\n")
    return "".join(out)

def _rule_block(hook: str) -> str:
    def line(flag):
        return f'debug_log = "HSI;{hook};0;lobby;RULE;-;flag={flag}"'
    return ("\tif = { limit = { has_game_rule = infamy_generation_very_low } " + line("very_low") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_low } " + line("low") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_high } " + line("high") + " }\n"
            "\telse_if = { limit = { has_game_rule = infamy_generation_very_high } " + line("very_high") + " }\n"
            "\telse = { " + line("standard") + " }\n")

def _diag_line(holder: str, sk: str, owner: str) -> str:
    sample_expr = "[SCOPE.sCountry('hsi_root').MakeScope.Var('hsi_sample').GetValue|0]"
    date_expr = "[TimeKeeper.GetCurrentDate.GetString]"
    s = "SCOPE.sState('hsi_state').MakeScope"
    return (f'\t\t\tdebug_log = "HSI;monthly;{sample_expr};{date_expr};DIAG;{holder}/{sk}/{owner};'
            f"root_tag=[SCOPE.sCountry('hsi_root').GetTagName];aggressor_homeland={_sv('hsi_d_ah')};homeland_bonus={_sv('hsi_d_ahb')};"
            f"shared_language={_sv('hsi_d_sl')};language_bonus={_sv('hsi_d_slb')};claim={_sv('hsi_d_cl')};"
            f"scripted_unification={_sv('hsi_d_su')};adjacent={_sv('hsi_d_adj')};interest_bucket={_sv('hsi_d_int')};"
            f"root_type={_sv('hsi_d_rt')};owner_type={_sv('hsi_ot')};siv=[{s}.Var('hsi_siv').GetValue|4]\"\n")

def render(led: Ledger, config: dict) -> dict:
    sampler = config["sampler_tag"]
    months = int(config["months"])
    holders = sorted(led.holder_tags())
    tags = sorted(set(holders) | {config["fixture_holder"], "BOL", sampler})
    slices = sorted(led.all_slices())
    guard = " ".join(f"c:{t} = this" for t in sorted(set(holders) | {sampler}))
    on_actions = (
        "on_game_started = {\n\ton_actions = { hsi_probe_start_a }\n}\n"
        "on_game_started_after_lobby = {\n\ton_actions = { hsi_probe_start_b }\n}\n"
        "on_monthly_pulse_country = {\n\ton_actions = { hsi_probe_monthly }\n}\n"
        "hsi_probe_start_a = {\n\teffect = { hsi_probe_start_records = { HOOK = start_a } }\n}\n"
        "hsi_probe_start_b = {\n\teffect = { hsi_probe_start_records = { HOOK = start_b } }\n}\n"
        "hsi_probe_monthly = {\n\teffect = { hsi_probe_monthly_records = yes }\n}\n")
    values = (
        "hsi_probe_state_pop = { value = state_population }\n"
        "hsi_probe_state_gdp = { value = gdp }\n"
        "hsi_probe_gen = { value = modifier:country_infamy_generation_mult }\n"
        "hsi_probe_unrec = { value = modifier:country_infamy_generation_against_unrecognized_mult }\n"
        "hsi_probe_decay = { value = modifier:country_infamy_decay_mult }\n"
        "hsi_probe_infamy = { value = infamy }\n")
    eff = []
    eff.append("# GENERATED by tools/hsi/probe_gen.py from the ledger. Throwaway measurement mod; never shipped.\n")
    eff.append("hsi_probe_state_flags = {\n" + _flag("hsi_inc", "is_incorporated = yes") + _flag("hsi_cap", "is_capital = yes")
               + _flag("hsi_oh", "is_homeland_of_country_cultures = owner") + _type_code("hsi_ot", "owner = { ") + "}\n")
    eff.append("hsi_probe_country_flags = {\n" + _type_code("hsi_ct", "") + "}\n")
    eff.append("hsi_probe_diag_flags = {\n"
               + _flag("hsi_d_ah", "is_homeland_of_country_cultures = root")
               + _flag("hsi_d_ahb", "root = { modifier:country_homeland_infamy_reduction_bool = yes }")
               + _flag("hsi_d_sl", "any_scope_culture = { has_homeland = scope:hsi_state shares_language_trait_with_any_primary_culture = root }")
               + _flag("hsi_d_slb", "root = { modifier:country_shared_language_infamy_reduction_bool = yes }")
               + _flag("hsi_d_cl", "has_claim_by = root")
               + _flag("hsi_d_su", "root = { is_scripted_unification_conquest = { TARGET = scope:hsi_state.owner } }")
               + _flag("hsi_d_adj", "root = { is_land_adjacent_to_state = scope:hsi_state }")
               + "\tif = { limit = { root = { NOT = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 2 } } } } set_variable = { name = hsi_d_int value = 1 } }\n"
               + "\telse_if = { limit = { root = { NOT = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 3 } } } } set_variable = { name = hsi_d_int value = 2 } }\n"
               + "\telse_if = { limit = { root = { has_strategic_region_interest_tier = { strategic_region = scope:hsi_region value >= 5 } } } set_variable = { name = hsi_d_int value = 5 } }\n"
               + "\telse = { set_variable = { name = hsi_d_int value = 3 } }\n"
               + _type_code("hsi_d_rt", "root = { ") + "}\n")
    eff.append("hsi_probe_start_records = {\n" + _records_block("$HOOK$", "0", "lobby", slices, tags, sampler) + _rule_block("$HOOK$") + "}\n")
    monthly = ["hsi_probe_monthly_records = {\n", f"\tif = {{ limit = {{ OR = {{ {guard} }} }}\n",
               "\t\tif = { limit = { NOT = { has_variable = hsi_sample } } set_variable = { name = hsi_sample value = 0 } }\n",
               "\t\tchange_variable = { name = hsi_sample add = 1 }\n",
               f"\t\tif = {{ limit = {{ var:hsi_sample <= {months} }}\n\t\t\tsave_scope_as = hsi_root\n"]
    sample_expr = "[SCOPE.sCountry('hsi_root').MakeScope.Var('hsi_sample').GetValue|0]"
    date_expr = "[TimeKeeper.GetCurrentDate.GetString]"
    monthly.append(f"\t\t\tif = {{ limit = {{ c:{sampler} = this }}\n")
    monthly.append("".join("\t\t" + l for l in _records_block("monthly", sample_expr, date_expr, slices, tags, sampler).splitlines(True)))
    monthly.append("\t\t\t}\n")
    for holder in holders:
        # every holder evaluates every ledger slice, so the same state is observed under two actors with different factors
        monthly.append(f"\t\t\tif = {{ limit = {{ c:{holder} = this }}\n")
        for sk, owner in slices:
            monthly.append(f"\t\t\t\ts:{sk}.region_state:{owner} ?= {{\n\t\t\t\t\tsave_scope_as = hsi_state\n"
                           f"\t\t\t\t\tregion = {{ save_scope_as = hsi_region }}\n\t\t\t\t\thsi_probe_state_flags = yes\n"
                           f"\t\t\t\t\thsi_probe_diag_flags = yes\n\t\t\t\t\tset_variable = {{ name = hsi_siv value = state_infamy_value }}\n")
            monthly.append("\t\t" + _diag_line(holder, sk, owner))
            monthly.append("\t\t\t\t}\n")
        monthly.append("\t\t\t}\n")
    monthly.append("\t\t}\n\t}\n}\n")
    eff.append("".join(monthly))
    metadata = {"name": "HSI Probe", "id": "", "version": "0.0.1", "supported_game_version": "1.14.*",
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
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass.

- [ ] **Step 5: Write `research/probe/config.json` and the procedure**

```json
{"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3}
```

```markdown
# research/measurement/PROCEDURE.md — probe boot (Eric), about fifteen minutes

Prerequisites (Claude): the ledger validates; `python3 -m hsi.probe_gen --research research --out research/probe`
has written the probe; `tools/hsi/validate.py --probe` passes (BOM, braces).

1. Stage the probe as a local mod and back up the playset. From the repo root:
   ```bash
   V3="$HOME/Documents/Paradox Interactive/Victoria 3"
   cp "$V3/content_load.json" "$V3/content_load.json.bak-$(date +%Y%m%d-%H%M%S)"
   rm -rf "$V3/mod/hsi_probe" && cp -R research/probe "$V3/mod/hsi_probe"
   printf '{"enabledMods":[{"path":"%s"}],"disabledDLC":[],"enabledUGC":[]}\n' "$V3/mod/hsi_probe" > "$V3/content_load.json"
   ```
2. Launch the game directly with debug mode (Steam is bypassed; `SteamAPI_Init() failed` on stdout is expected):
   ```bash
   G="$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3"
   cd "$G" && "$G/binaries/victoria3.app/Contents/MacOS/victoria3" -debug_mode
   ```
3. New Game. Pick the fixture holder (France). On the New Game page set **Infamy Generation = Very Low**. Start.
4. Before unpausing, capture the four oracle tooltips. For each, open Diplomacy → the target country → start a diplomatic
   play draft, hover the war goal's infamy value, and screenshot the full breakdown (⇧⌘4, saved to the Desktop). Targets
   are listed in `research/fixtures.json` under `capture_plan` (Claude fills them in before the boot): (A) make protectorate
   against a non-subject target, (B) conquer state with a visible homeland/claim/adjacency line, (C) regime change against
   a tiny and against a large target, (D) a conquer state whose Standard value lies between 1 and 2. Cancel every draft.
5. Switch to Observe (console: `observe`). Set speed 5 and let the game run until **after April 1, 1836**. Quit to desktop.
6. Restore the playset:
   ```bash
   cp "$(ls -t "$V3"/content_load.json.bak-* | head -1)" "$V3/content_load.json"
   ```
7. Tell Claude. Claude copies `$V3/logs/debug.log`, `$V3/logs/system.log` and the screenshots into
   `research/measurement/<date>/`, runs `python3 -m hsi.measurement extract --debug-log ... --out probe-extract.log`,
   transcribes the tooltips into `research/fixtures.json`, writes `engine.txt` (rawVersion from the launcher settings),
   `playset.txt` (the content_load.json used) and the manifest.
```

- [ ] **Step 6: Generate the probe once from the fixture ledger to smoke-test the writer, then delete the output**

Run: `cd tools && python3 -m hsi.probe_gen --research tests/fixtures/ledger_ok --out /tmp/hsi_probe_smoke` after creating `/tmp/hsi_probe_smoke/config.json` with the config above; inspect the effects file by eye for balanced braces; `rm -rf /tmp/hsi_probe_smoke`.

- [ ] **Step 7: Commit**

```bash
git add tools/hsi/probe_gen.py tools/tests/test_probe_gen.py research/probe/config.json research/measurement/PROCEDURE.md
git commit -m "Add probe mod generator and the measurement boot procedure"
```

---

### Task 9: Author the ledger (spec §5) — research, validated by the loader

**Files:**
- Create: `research/acts.csv`, `research/goals.csv`, `research/goal_states.csv`, `research/sources.md`, `research/not_representable.md`

**Interfaces:**
- Consumes: `python3 -m hsi.ledger research --game-dir "<vanilla>"` (Task 6) as the gate after every batch.
- Produces: the three CSVs with the exact headers of Task 6, every act cited in `sources.md`, and `not_representable.md` listing every candidate act that the v1 rules cannot express and why.

This task is research with a validator, not code. Work act by act. The validator refuses structural errors; the historical judgments go in `justification` and `notes`.

- [ ] **Step 1: Create the files with headers only and confirm the validator accepts an empty ledger**

```bash
printf 'act_id,title,start_date,end_date,source,notes\n' > research/acts.csv
printf 'goal_id,act_id,wargoal,holder,holder_tag_1836,holder_type,target,stakeholder,victim_tag_1836,claim_date,resolution,resolution_date,loyal_subject,rebellious_subject,general_mult_source,notes\n' > research/goals.csv
printf 'goal_id,component_id,state_key,slices_1836,owner_type,standing,aggressor_homeland,shared_language,claim,scripted_unification,adjacent,interest_tier,justification\n' > research/goal_states.csv
printf '# Sources\n\nOne block per act, keyed by the `source` cell. Give the treaty or event name, date, and a reference a reader can check (a standard history or an encyclopedia article).\n' > research/sources.md
printf '# Not representable under v1\n\nCandidate acts the ledger cannot express under the spec §5 rules, with the rule that excludes each.\n' > research/not_representable.md
cd tools && python3 -m hsi.ledger ../research --game-dir "$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game"
```
Expected: `ledger ok: 0 acts, 0 goals, 0 components`.

- [ ] **Step 2: For each candidate, decide and record**

Work through this roster. For each act: (a) find the source and record it in `sources.md`; (b) decide the war goal mapping; (c) find the 1836 slices in `common/history/states/00_states.txt` (`s:STATE_X = {` blocks list `create_state = { country = c:TAG ... }`); (d) decide standing under the historical owner by reading that owner's 1836 incorporation of its comparable states in the same file and writing the reasoning in `justification`; (e) set the aggressor factors with a one-line justification each; (f) run the validator. If a candidate cannot be expressed (a demand took part of one 1836 slice, or holder ≠ creator), record it in `not_representable.md` instead.

Candidate roster, with the mapping to start from (every date and mapping must be checked against the source before it is written):

| act | holder (tag, type) | goals | notes to resolve |
|---|---|---|---|
| Egypt's conquest of Syria 1831–33 | EGY (unrecognized) | `conquer_state` × STATE_ALEPPO, STATE_SYRIA, STATE_LEBANON, STATE_PALESTINE (slice EGY), STATE_ADANA (slice EGY only; TUR slice stays) | claim 1831-10 (Ibrahim's advance on Acre), enforced 1833-05 (Kütahya); victim TUR; standing under TUR per Ottoman incorporation; shared language misri/mashriqi: check `common/cultures` language traits |
| Bolivia and Peru 1835–36 | BOL (recognized) | `make_protectorate` × NPU, SPU | computed, never emitted (vanilla 50) |
| Russo-Persian War 1826–28 | RUS (recognized) | `conquer_state` × STATE_ARMENIA, STATE_AZERBAIJAN (slices RUS) | Persia attacked; Russia added the goals: claim 1826-07, enforced 1828-02 (Turkmenchay); victim PER |
| Russo-Turkish War 1828–29 | RUS | `conquer_state` × STATE_DOBRUDJA (slice RUS, the Danube delta) | claim 1828-04, enforced 1829-09 (Adrianople); the protectorate over Moldavia/Wallachia is not a Vic3 subject transfer (they stay TUR subjects in 1836): note it, do not model it |
| Caucasian War, Dagestan/Circassia campaigns 1829–35 | RUS | `conquer_state` × RUS slices of STATE_DAGESTAN, STATE_KUBAN, STATE_CIRCASSIA (owners CHC/CIR are decentralized or unrecognized) | dates per campaign from the source; `owner_type` from the 1836 owner of the remaining slice |
| First Anglo-Burmese War 1824–26 | BIC (recognized; the Company fought it) | `conquer_state` × BIC slices of STATE_ARAKAN, STATE_TENASSERIM, STATE_ASSAM | claim 1824-03, enforced 1826-02 (Yandabo); victim BUR; Manipur as a protectorate only if the source supports it |
| Greek independence, backers 1827–30 | GBR, FRA, RUS (each its own goal) | `liberate_country` with components = GRE's 1836 states (STATE_ATTICA plus the others GRE owns) | claim 1827-07 (Treaty of London), enforced 1830-02 (London Protocol); victim TUR |
| French conquest of Algiers 1830–32 | FRA | `conquer_state` × FRA slices of STATE_ALGIERS, STATE_ORAN, STATE_CONSTANTINE | the Regency of Algiers has no 1836 tag: `victim_tag_1836` empty; dates per city from the source |
| Belgian independence, backers 1830–39 | FRA, GBR | `liberate_country` with components = BEL's 1836 states | claim 1830-12 (London Protocol), `pending` (Dutch acceptance came in 1839) |
| Dutch Ten Days' Campaign 1831 | NET | `return_state` × BEL slices of the Belgian states (claims = 1) | claim 1831-08-02, `dropped_backdown` 1831-08-12 under French intervention |
| Peshawar and Ladakh, Sikh Empire 1834–35 | PAN (unrecognized) | `conquer_state` × PAN slice of the state holding Peshawar (find it in `00_states.txt`); Ladakh is `pending` if LAD still exists in 1836 | dates from the source |
| Vietnamese annexation of Cambodia 1834–35 | DAI (unrecognized) | `make_protectorate` or `annex_country` of CAM depending on CAM's 1836 status in `00_subject_relationships.txt` | claim 1833-12, enforced 1834 |
| Siamese campaigns: Vientiane 1827–28, Cambodia 1833–34, Kedah 1821 | SIA (unrecognized) | `conquer_state` × SIA slice of STATE_LAOS; `make_protectorate` CAM `dropped_peace` 1834; Kedah per `00_states.txt` | all dates from the source |
| Egyptian conquest of Sudan 1820–21 | EGY | `conquer_state` × EGY slices of STATE_KORDOFAN and the Sennar state | decays to zero but is recorded |
| Haitian occupation of Santo Domingo 1822 | HAI | `conquer_state` × STATE_SANTO_DOMINGO (slice HAI) | claim and enforcement 1822-02 |
| Spanish Barradas expedition 1829 | SPA | `return_state` × MEX slice of the Tamaulipas state (claim = 1) | `dropped_peace` 1829-09 |
| Ottoman reassertion over Tripoli 1835 | TUR | depends on TRI's 1836 status; if TRI is already a TUR subject, the only allowed analog is `make_protectorate` with `loyal_subject` or `rebellious_subject` per the source | record the judgment |
| Persian siege of Herat 1833 | PER (unrecognized) | `conquer_state` × the Herat state, `dropped_peace` 1833 | |
| Zulu campaigns under Dingane 1828–35; Merina conquests 1817–28 | ZUL, MAD (unrecognized) | `conquer_state` × their 1836 slices that were conquered in the window, decentralized owners | include only what the source dates inside the window |
| US Indian Removal 1830–36, Black Hawk War 1832 | USA | not representable: the removals took parts of 1836 USA slices | write to `not_representable.md` with the whole-slice rule |
| Austrian interventions in the Papal States 1831–32; French occupation of Ancona 1832 | AUS, FRA | no infamy-generating analog (no territorial or subjugation demand) | write to `not_representable.md` |
| Coorg 1834 and Cachar 1832 annexations | BIC | not representable: parts of 1836 BIC slices | `not_representable.md` |

Commit after each batch of acts that validates:

```bash
cd tools && python3 -m hsi.ledger ../research --game-dir "$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game" && cd .. && git add research && git commit -m "Ledger: <acts added>"
```

- [ ] **Step 3: Final ledger review**

Read every `justification` and `notes` cell once more against its source. Confirm `not_representable.md` lists every roster row that was dropped. Run the validator one last time and commit.

---

### Task 10: Probe boot, measurement capture, oracle fixtures (spec §6)

**Files:**
- Create: `research/measurement/<YYYY-MM-DD>/` with `debug.log`, `system.log`, `probe-extract.log`, `oracle-tooltips.md`, `fixture-*.png`, `engine.txt`, `playset.txt`, `manifest.sha256`; `research/fixtures.json`
- Modify: `.gitignore` (add `research/measurement/*/saves/` and `research/acceptance/*/saves/`)

**Interfaces:**
- Consumes: Task 8's probe and PROCEDURE.md; Task 7's extractor and `write_manifest`.
- Produces: `research/fixtures.json` in the shape `load_fixtures` reads (Task 4), plus a `capture_plan` key the loader ignores; the measurement directory the generator consumes (Task 11).

- [ ] **Step 1: Generate the probe from the real ledger and validate it**

```bash
cd tools && python3 -m hsi.probe_gen --research ../research --out ../research/probe
python3 -m hsi.validate --repo .. --game-dir "$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game" --probe-only
```

- [ ] **Step 2: Fill in the capture plan before the boot**

Choose four targets for France (the fixture holder) and write them into `research/fixtures.json` as a `capture_plan` list, each with `capture_id`, `wargoal`, `target_tag`, `target_state_key` (for conquer_state) and the reason it exercises its boundary. Rules: (A) `make_protectorate` against a non-subject, cost expected above 5 under Very Low; (B) `conquer_state` against a state where France has a claim or adjacency so a factor line appears; (C) `regime_change` against a very small country (below the minimum 3) and against a large one (above the maximum 10); (D) `conquer_state` against an unincorporated single-slice state with a claim so the Standard value lies between 1 and 2 (the floor binds under Very Low). Use the ledger's per-component arithmetic with population from `common/history/pops/` to pick candidates; the boot confirms.

- [ ] **Step 3: Eric runs PROCEDURE.md** (about fifteen minutes). Do not touch the game yourself.

- [ ] **Step 4: Capture the evidence**

```bash
D=research/measurement/$(date +%Y-%m-%d); mkdir -p "$D"
V3="$HOME/Documents/Paradox Interactive/Victoria 3"
cp "$V3/logs/debug.log" "$V3/logs/system.log" "$D/"
cp ~/Desktop/Screenshot*.png "$D/"        # rename to fixture-A.png, fixture-B.png, fixture-Cmin.png, fixture-Cmax.png, fixture-D.png
grep -E '"rawVersion"' "$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/launcher/launcher-settings.json" > "$D/engine.txt"
cp "$(ls -t "$V3"/content_load.json.bak-* | head -1)" "$D/playset.txt"   # the playset Eric restored; the probe-only one is reconstructed from PROCEDURE step 1
cd tools && python3 -m hsi.measurement extract --debug-log "../$D/debug.log" --out "../$D/probe-extract.log"
```
Expected: the extractor prints `start_a sample 0`, `start_b sample 0`, and `monthly sample 1..3` with their dates and record counts. If any sample is missing or `RULE` differs between `start_a` and `start_b`, record the observation in `oracle-tooltips.md` (an equal reading is an observation, not a failure).

- [ ] **Step 5: Transcribe the fixtures**

Open each screenshot. In `oracle-tooltips.md` write, per capture: capture id, date and tick (1836-01-01, tick 0), holder, target, rule (very_low), then every breakdown line in display order with its label and number exactly as shown. Then fill `research/fixtures.json`:

```json
[
  {"capture_id": "A", "wargoal": "make_protectorate", "raw_subtotal": 0.0, "general_mult": -0.05, "rule_key": "very_low",
   "lines": [{"stage": "S", "running_text": null, "decimals": 2},
             {"stage": "G", "running_text": null, "decimals": 2},
             {"stage": "R", "running_text": null, "decimals": 2},
             {"stage": "total", "running_text": "0.0", "decimals": 1}]}
]
```
Replace `raw_subtotal` with the engine's own sum of state values before severity (the per-state lines of the breakdown), `general_mult` with France's measured `gen_mult` from the tick-0 `COUNTRY;FRA` record, `running_text` with the running value where the UI shows one and `null` where it shows only a multiplier, and the total as displayed. One object per capture (A, B, Cmin, Cmax, D).

- [ ] **Step 6: Write the manifest and commit**

```bash
cd tools && python3 - <<'PY'
from pathlib import Path
from hsi.measurement import write_manifest
import sys
d = sorted(Path("../research/measurement").glob("2026-*"))[-1]
names = [p.name for p in d.iterdir() if p.is_file() and p.name != "manifest.sha256"]
print(write_manifest(d, names))
PY
cd .. && printf 'research/measurement/*/saves/\nresearch/acceptance/*/saves/\n' >> .gitignore
git add research/measurement research/fixtures.json .gitignore
git commit -m "Measurement $(date +%Y-%m-%d): probe boot, extract, oracle fixtures"
```

- [ ] **Step 7: If the probe printed something unparseable** (the first-boot risk the spec names), fix `probe_gen.py` with a failing test first, regenerate, and repeat from Step 3. Record the failed attempt's `debug.log` under `research/measurement/<date>-attempt1/` with its own manifest.

---

### Task 11: Generator: tables, effect, README, derivation, hashes (spec §7, §8, §9 oracles)

**Files:**
- Create: `tools/hsi/hashes.py`, `tools/hsi/generate.py`, `tools/tests/test_generate.py`, `tools/tests/fixtures/fixtures_ok.json`

**Interfaces:**
- Produces: `hashes.sha256_file` (re-exported from measurement), `hashes.generator_source_hashes(tools_hsi_dir) -> dict[str, str]`, `hashes.vanilla_input_hashes(game_dir) -> dict[str, str]`, `hashes.header_block(entries: dict[str, str]) -> str` (lines `# HSI-HASH <name> <hex>`), `hashes.parse_header(text) -> dict[str, str]`; `generate.goal_inputs(goal, led, snap) -> GoalInputs`; `generate.diagnostic_check(led, snap) -> list[str]`; `generate.compute_tables(led, snap, order) -> tuple[dict[str, dict[str, float]], list[dict]]` (tables per rule key → {tag: rounded value}, derivation rows); `generate.render_effect(tables, notes: dict[str, list[str]], header: str) -> str`; `generate.render_readme_table(tables) -> str`; `generate.update_readme(path, table_md) -> None`; `generate.main(argv)` with `--repo --game-dir --measurement --fixtures`.
- Consumes: everything from Tasks 2–7.

- [ ] **Step 1: Write the fixture file and the failing tests**

```json
// tools/tests/fixtures/fixtures_ok.json
[
 {"capture_id": "A", "wargoal": "make_protectorate", "raw_subtotal": 80.0, "general_mult": -0.05, "rule_key": "very_low",
  "lines": [{"stage": "S", "running_text": "40.00", "decimals": 2}, {"stage": "G", "running_text": "38.00", "decimals": 2}, {"stage": "R", "running_text": "19.00", "decimals": 2}, {"stage": "total", "running_text": "19.0", "decimals": 1}]},
 {"capture_id": "Cmax", "wargoal": "regime_change", "raw_subtotal": 200.0, "general_mult": -0.05, "rule_key": "very_low",
  "lines": [{"stage": "S", "running_text": "20.00", "decimals": 2}, {"stage": "C", "running_text": "10.00", "decimals": 2}, {"stage": "G", "running_text": "9.50", "decimals": 2}, {"stage": "R", "running_text": "4.75", "decimals": 2}, {"stage": "total", "running_text": "4.8", "decimals": 1}]},
 {"capture_id": "Cmin", "wargoal": "regime_change", "raw_subtotal": 20.0, "general_mult": -0.05, "rule_key": "very_low",
  "lines": [{"stage": "S", "running_text": "2.00", "decimals": 2}, {"stage": "C", "running_text": "3.00", "decimals": 2}, {"stage": "G", "running_text": "2.85", "decimals": 2}, {"stage": "R", "running_text": "1.43", "decimals": 2}, {"stage": "total", "running_text": "1.4", "decimals": 1}]},
 {"capture_id": "D", "wargoal": "conquer_state", "raw_subtotal": 1.5, "general_mult": -0.05, "rule_key": "very_low",
  "lines": [{"stage": "G", "running_text": "1.43", "decimals": 2}, {"stage": "R", "running_text": "0.71", "decimals": 2}, {"stage": "F", "running_text": "1.00", "decimals": 2}, {"stage": "total", "running_text": "1.0", "decimals": 1}]}
]
```
(JSON has no comments; the `//` line is a label for this plan.)

```python
# tools/tests/test_generate.py
from pathlib import Path
import json
import shutil
import sys
import pytest
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
import make_probe_log
from hsi.ledger import load_ledger
from hsi.measurement import parse_lines, extract, choose_snapshot, write_manifest
from hsi.ordering import load_fixtures, select_order
from hsi.formula import DEFAULT_ORDER
from hsi import generate, hashes

FIX = Path(__file__).parent / "fixtures"

def setup_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "research").mkdir(parents=True)
    for n in ("acts.csv", "goals.csv", "goal_states.csv"):
        shutil.copy(FIX / "ledger_ok" / n, repo / "research" / n)
    shutil.copy(FIX / "fixtures_ok.json", repo / "research" / "fixtures.json")
    m = repo / "research" / "measurement" / "2026-01-01"; m.mkdir(parents=True)
    make_probe_log.write(m / "debug.log")
    (m / "engine.txt").write_text('"rawVersion": "1.14.5"\n')
    write_manifest(m, ["debug.log", "engine.txt"])
    (repo / "common" / "scripted_effects").mkdir(parents=True)
    (repo / "README.md").write_text("# T\n\n<!-- hsi:table:start -->\nold\n<!-- hsi:table:end -->\n", encoding="utf-8")
    game = tmp_path / "game"
    for rel in ("common/script_values/00_infamy_values.txt", "common/defines/00_defines.txt",
                "common/script_values/00_diplomacy_values.txt", "common/game_rules/00_game_rules.txt",
                "common/war_goal_types/03_conquer_state.txt", "common/country_definitions/00_countries.txt"):
        p = game / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(f"stub {rel}\n")
    (game / "common/country_definitions/00_countries.txt").write_text("EGY = {\n}\nGBR = {\n}\nTUR = {\n}\nGRE = {\n}\nHDJ = {\n}\nBOL = {\n}\nFRA = {\n}\n")
    (game / "common/game_rules/00_game_rules.txt").write_text("infamy_generation = {\n\tinfamy_generation_very_low = { flag = infamy_generation_very_low }\n\tinfamy_generation_low = { flag = infamy_generation_low }\n\tinfamy_generation_standard = { }\n\tinfamy_generation_high = { flag = infamy_generation_high }\n\tinfamy_generation_very_high = { flag = infamy_generation_very_high }\n}\n")
    return repo, game, m

def snapshot(led, m):
    recs = parse_lines(extract(m / "debug.log"))
    return choose_snapshot(recs, led.all_slices(), led.holder_tags())

def test_diagnostic_check_passes_on_consistent_fixture(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    assert generate.diagnostic_check(led, snapshot(led, m)) == []

def test_diagnostic_check_fails_on_perturbed_siv(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    snap = snapshot(led, m)
    snap.diag[("EGY", "STATE_ALEPPO", "EGY")]["siv"] += 0.5
    problems = generate.diagnostic_check(led, snap)
    assert problems and "STATE_ALEPPO" in problems[0]

def test_compute_tables_hand_checked_values(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    led = load_ledger(repo / "research")
    tables, rows = generate.compute_tables(led, snapshot(led, m), DEFAULT_ORDER)
    # g_pending: (5+2.306+1.303)*2.0*0.85*0.9 = 13.17177 -> x0.5 x0.95 = 6.25659, decays 61 days (0.83505) -> 5.42
    assert tables["standard"] == {"EGY": 5.42}
    assert tables["very_low"] == {"EGY": 2.29}
    assert tables["low"] == {"EGY": 3.86}
    assert tables["high"] == {"EGY": 6.99}
    # very_high: the 1831 goals (8.73081 + 5.92955 = 14.66036 standard, x1.5 = 21.99054) decay 1492 days
    # (20.42437) to 1.56617 on 1835-11-01, then +9.38489 and 61 days of decay (0.83505) -> 10.116 -> 10.12
    assert tables["very_high"] == {"EGY": 10.12}
    kinds = {(r["actor"], r["kind"]) for r in rows}
    assert ("TUR", "reduction") in kinds and ("EGY", "accrual") in kinds
    assert all("BOL" != r["actor"] or r["kind"] != "emit" for r in rows)

def test_render_effect_shape():
    tables = {"standard": {"EGY": 5.42}, "very_low": {}, "low": {"EGY": 3.86}, "high": {"EGY": 6.99}, "very_high": {"EGY": 8.55}}
    text = generate.render_effect(tables, {"EGY": ["g_pending"]}, "# HSI-HASH x y\n")
    assert text.startswith("# GENERATED")
    assert "limit = { NOT = { has_global_variable = hsi_applied } }" in text
    assert "else = { hsi_table_standard = yes }" in text
    assert "hsi_table_very_low = {\n}" in text
    assert "c:EGY ?= { change_infamy = 5.42 }   # g_pending" in text
    assert "set_global_variable = hsi_applied" in text
    assert "infamy_generation_standard" not in text

def test_main_end_to_end_writes_outputs(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    rc = generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m),
                        "--fixtures", str(repo / "research" / "fixtures.json")])
    assert rc == 0
    eff = (repo / "common" / "scripted_effects" / "zz_hsi_effects.txt").read_bytes()
    assert eff.startswith(b"\xef\xbb\xbf")
    header = hashes.parse_header(eff.decode("utf-8-sig"))
    assert "ledger/goals.csv" in header and "vanilla/common/defines/00_defines.txt" in header
    assert "generator/generate.py" in header and "measurement/manifest.sha256" in header
    tables = json.loads((repo / "research" / "tables.json").read_text())
    assert tables["standard"]["EGY"] == 5.42
    readme = (repo / "README.md").read_text()
    assert "| EGY |" in readme and "old" not in readme
    assert (repo / "research" / "derivation.csv").exists()

def test_main_refuses_on_ambiguous_fixtures(tmp_path):
    repo, game, m = setup_repo(tmp_path)
    (repo / "research" / "fixtures.json").write_text(json.dumps([
        {"capture_id": "A", "wargoal": "regime_change", "raw_subtotal": 200.0, "general_mult": 0.0, "rule_key": "very_low",
         "lines": [{"stage": "total", "running_text": "5.0", "decimals": 1}]}]))
    rc = generate.main(["--repo", str(repo), "--game-dir", str(game), "--measurement", str(m),
                        "--fixtures", str(repo / "research" / "fixtures.json")])
    assert rc == 1
    assert not (repo / "common" / "scripted_effects" / "zz_hsi_effects.txt").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_generate.py`
Expected: FAIL with `ImportError` on `hsi.generate` / `hsi.hashes`.

- [ ] **Step 3: Implement hashes.py**

```python
# tools/hsi/hashes.py
"""Binds generated output to every numerical input (spec §7 outputs, §9 step 1)."""
from pathlib import Path
from .measurement import sha256_file

VANILLA_FIXED = ["common/script_values/00_infamy_values.txt", "common/defines/00_defines.txt",
                 "common/script_values/00_diplomacy_values.txt", "common/game_rules/00_game_rules.txt"]

def generator_source_hashes(tools_hsi_dir: Path) -> dict:
    return {f"generator/{p.name}": sha256_file(p) for p in sorted(Path(tools_hsi_dir).glob("*.py"))}

def vanilla_input_hashes(game_dir: Path) -> dict:
    game_dir = Path(game_dir)
    out = {f"vanilla/{rel}": sha256_file(game_dir / rel) for rel in VANILLA_FIXED}
    for p in sorted((game_dir / "common" / "war_goal_types").glob("*.txt")):
        out[f"vanilla/common/war_goal_types/{p.name}"] = sha256_file(p)
    return out

def header_block(entries: dict) -> str:
    return "".join(f"# HSI-HASH {k} {v}\n" for k, v in sorted(entries.items()))

def parse_header(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if line.startswith("# HSI-HASH "):
            _, _, name, digest = line.split(" ", 3)
            out[name] = digest.strip()
    return out
```

- [ ] **Step 4: Implement generate.py**

```python
# tools/hsi/generate.py
"""Ledger + measurement + fixtures -> five tables, the shipped effect, README table, derivation (spec §7, §8)."""
import csv
import json
import sys
from datetime import date
from pathlib import Path
from . import constants as K
from .bom import write_text_bom
from .formula import Component, GoalInputs, GOALS, component_value, nominal_charge
from .hashes import generator_source_hashes, vanilla_input_hashes, header_block
from .ledger import Ledger, load_ledger, load_vanilla_tags, validate_ledger, LedgerError
from .measurement import (extract, parse_lines, choose_snapshot, verify_manifest, sha256_file,
                          MeasurementError, ManifestError, MANIFEST)
from .ordering import load_fixtures, select_order, OrderingNoFit, OrderingAmbiguous
from .timeline import Event, replay_steps

RULES = ("very_low", "low", "standard", "high", "very_high")
TYPE_CODES = {0.0: "recognized", 1.0: "unrecognized", 2.0: "decentralized"}
EMIT_MIN = 0.05

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

def goal_inputs(goal, led: Ledger, snap) -> GoalInputs:
    gen, unrec = _holder_mods(goal, snap)
    comps = []
    for s in led.components_of(goal.goal_id):
        pop = sum(snap.slice(s.state_key, t)["pop_share_uncapped"] for t in s.slices_1836)
        gdp = sum(snap.slice(s.state_key, t)["gdp_share_uncapped"] for t in s.slices_1836)
        comps.append(Component(pop, gdp, s.standing, s.owner_type, s.aggressor_homeland, s.shared_language,
                               s.claim, s.scripted_unification, s.adjacent, s.interest_tier))
    return GoalInputs(goal.wargoal, tuple(comps), goal.holder_type, unrec, gen,
                      goal.loyal_subject, goal.rebellious_subject)

def diagnostic_check(led: Ledger, snap, tolerance: float = 0.005) -> list:
    """Oracle A (spec §9): reproduce every engine-logged state_infamy_value from the same sample's inputs."""
    problems = []
    for (holder, sk, owner), d in sorted(snap.diag.items()):
        st = snap.slice(sk, owner)
        c = Component(st["pop_share_uncapped"], st["gdp_share_uncapped"], _standing_from_state(st),
                      TYPE_CODES[d["owner_type"]], d["aggressor_homeland"] == 1.0, d["shared_language"] == 1.0,
                      d["claim"] == 1.0, d["scripted_unification"] == 1.0, d["adjacent"] == 1.0,
                      int(d["interest_bucket"]), d["homeland_bonus"] == 1.0, d["language_bonus"] == 1.0)
        unrec = snap.country(holder)["unrec_mult"]
        ours = component_value(c, TYPE_CODES[d["root_type"]], unrec)
        if abs(ours - d["siv"]) > tolerance:
            problems.append(f"{holder}/{sk}/{owner}: generator {ours:.4f} vs engine {d['siv']:.4f}")
    return problems

def _actor_key(goal) -> str:
    return goal.holder_tag_1836 if goal.holder_tag_1836 else f"actor:{goal.holder}"

def compute_tables(led: Ledger, snap, order):
    horizon = date.fromisoformat(K.HORIZON)
    tables, rows = {}, []
    charges = {}
    for g in led.goals.values():
        gi = goal_inputs(g, led, snap)
        for rule in RULES:
            charges[(g.goal_id, rule)] = nominal_charge(gi, rule, order)
            rows.append({"rule": rule, "actor": _actor_key(g), "kind": "charge", "goal_id": g.goal_id,
                         "date": g.claim_date.isoformat(), "value": charges[(g.goal_id, rule)]})
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
            final = round(steps[-1]["after_event"], 2)
            emit = (len(actor) == 3 and actor.isupper() and actor != "BOL" and final >= EMIT_MIN)
            rows.append({"rule": rule, "actor": actor, "kind": "emit" if emit else "not_emitted",
                         "goal_id": "", "date": K.HORIZON, "value": final})
            if emit:
                table[actor] = final
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
            out.append(f"\tc:{tag} ?= {{ change_infamy = {value:.2f} }}   # {' '.join(notes.get(tag, []))}\n")
        out.append("}\n")
    return "".join(out)

def render_readme_table(tables: dict) -> str:
    tags = sorted({t for r in RULES for t in tables[r]})
    lines = ["| Country | Very Low | Low | Standard | High | Very High |", "|---|---:|---:|---:|---:|---:|"]
    for t in tags:
        cells = [f"{tables[r][t]:.2f}" if t in tables[r] else "0" for r in RULES]
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
    ap.add_argument("--measurement", required=True); ap.add_argument("--fixtures", required=True)
    a = ap.parse_args(argv)
    repo, game, meas = Path(a.repo), Path(a.game_dir), Path(a.measurement)
    try:
        led = load_ledger(repo / "research")
        validate_ledger(led, load_vanilla_tags(game))
        verify_manifest(meas)
        recs = parse_lines(extract(meas / "debug.log"))
        snap = choose_snapshot(recs, led.all_slices(), led.holder_tags())
        problems = diagnostic_check(led, snap)
        if problems:
            raise MeasurementError("oracle A failed:\n" + "\n".join(problems))
        fixtures = load_fixtures(Path(a.fixtures))
        domain = [goal_inputs(g, led, snap) for g in led.goals.values()]
        order = select_order(fixtures, domain)
    except (LedgerError, MeasurementError, ManifestError, OrderingNoFit, OrderingAmbiguous) as err:
        print(f"REFUSED: {err}", file=sys.stderr)
        return 1
    tables, rows = compute_tables(led, snap, order)
    notes: dict = {}
    for g in led.goals.values():
        if g.holder_tag_1836:
            notes.setdefault(g.holder_tag_1836, []).append(g.goal_id)
    entries = {f"ledger/{n}": sha256_file(repo / "research" / n) for n in ("acts.csv", "goals.csv", "goal_states.csv")}
    entries[f"measurement/{MANIFEST}"] = sha256_file(meas / MANIFEST)
    entries["fixtures/fixtures.json"] = sha256_file(Path(a.fixtures))
    entries["order"] = "".join(order)
    entries.update(generator_source_hashes(Path(__file__).parent))
    entries.update(vanilla_input_hashes(game))
    write_text_bom(repo / "common" / "scripted_effects" / "zz_hsi_effects.txt", render_effect(tables, notes, header_block(entries)))
    (repo / "research" / "tables.json").write_text(json.dumps(tables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with open(repo / "research" / "derivation.csv", "w", newline="", encoding="utf-8") as f:
        keys = ["rule", "actor", "kind", "goal_id", "date", "before_decay", "after_decay", "delta", "after_event", "value"]
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    update_readme(repo / "README.md", render_readme_table(tables))
    print(f"order {''.join(order)}; " + "; ".join(f"{r}: {len(tables[r])} countries" for r in RULES))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass. If `test_compute_tables_hand_checked_values` is off by 0.01 on a table, recompute by hand with the derivation rows printed; do not change the expected numbers to match the code without a worked explanation in the test's comment.

- [ ] **Step 6: Commit**

```bash
git add tools/hsi/hashes.py tools/hsi/generate.py tools/tests/test_generate.py tools/tests/fixtures/fixtures_ok.json
git commit -m "Add generator: nominal charges, timelines, five tables, effect and README"
```

---

### Task 12: Static validator (spec §9 step 1)

**Files:**
- Create: `tools/hsi/validate.py`, `tools/tests/test_validate.py`

**Interfaces:**
- Produces: `validate.check_bom(paths) -> list[str]`, `validate.check_braces(text, name) -> list[str]` (ignores `#` comments and quoted strings), `validate.check_rule_flags(effect_text, game_dir) -> list[str]`, `validate.check_header(repo, game_dir, measurement_dir, fixtures) -> list[str]`, `validate.main(argv)` with `--repo --game-dir [--measurement DIR --fixtures FILE] [--probe-only]`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_validate.py
from pathlib import Path
import shutil
from hsi import validate
from hsi.bom import write_text_bom

def test_check_bom_reports_missing(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    write_text_bom(a, "x = 1\n"); b.write_text("x = 1\n")
    assert validate.check_bom([a, b]) == [f"missing BOM: {b}"]

def test_check_braces_ignores_strings_and_comments():
    ok = 'a = {\n\tdebug_log = "HSI;{x}"  # comment with }\n}\n'
    assert validate.check_braces(ok, "ok.txt") == []
    bad = "a = {\n\tb = {\n}\n"
    assert validate.check_braces(bad, "bad.txt") == ["bad.txt: unbalanced braces (depth 1 at end)"]

def test_check_rule_flags(tmp_path):
    g = tmp_path / "game" / "common" / "game_rules"; g.mkdir(parents=True)
    (g / "00_game_rules.txt").write_text("infamy_generation = {\n\tx = { flag = infamy_generation_very_low }\n\ty = { flag = infamy_generation_low }\n}\n")
    eff = "if = { limit = { has_game_rule = infamy_generation_very_low } }\nelse_if = { limit = { has_game_rule = infamy_generation_higher } }\n"
    assert validate.check_rule_flags(eff, tmp_path / "game") == ["unknown game rule flag: infamy_generation_higher"]

def test_main_probe_only_on_generated_probe(tmp_path):
    probe = tmp_path / "repo" / "research" / "probe" / "common" / "x"
    probe.mkdir(parents=True)
    write_text_bom(probe / "ok.txt", "a = { b = 1 }\n")
    rc = validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(tmp_path), "--probe-only"])
    assert rc == 0
    (probe / "bad.txt").write_text("a = {\n")
    assert validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(tmp_path), "--probe-only"]) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_validate.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.validate'`

- [ ] **Step 3: Implement validate.py**

```python
# tools/hsi/validate.py
"""Static checks before any commit touching game files (spec §9 step 1)."""
import re
import sys
from pathlib import Path
from .bom import has_bom
from .hashes import generator_source_hashes, vanilla_input_hashes, parse_header
from .measurement import verify_manifest, sha256_file, ManifestError, MANIFEST

def check_bom(paths) -> list:
    return [f"missing BOM: {p}" for p in paths if not has_bom(p)]

def check_braces(text: str, name: str) -> list:
    depth = 0
    in_str = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "#":
            j = text.find("\n", i)
            i = len(text) if j < 0 else j
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return [f"{name}: unbalanced braces (closing brace before opening at offset {i})"]
        i += 1
    return [] if depth == 0 else [f"{name}: unbalanced braces (depth {depth} at end)"]

def check_rule_flags(effect_text: str, game_dir: Path) -> list:
    rules = (Path(game_dir) / "common" / "game_rules" / "00_game_rules.txt").read_text(encoding="utf-8-sig")
    known = set(re.findall(r"flag = ([a-z_]+)", rules))
    used = set(re.findall(r"has_game_rule = ([a-z_]+)", effect_text))
    return [f"unknown game rule flag: {f}" for f in sorted(used - known)]

def check_header(repo: Path, game_dir: Path, measurement: Path, fixtures: Path) -> list:
    eff = repo / "common" / "scripted_effects" / "zz_hsi_effects.txt"
    if not eff.exists():
        return [f"missing generated effect {eff}"]
    header = parse_header(eff.read_text(encoding="utf-8-sig"))
    expected = {f"ledger/{n}": sha256_file(repo / "research" / n) for n in ("acts.csv", "goals.csv", "goal_states.csv")}
    expected[f"measurement/{MANIFEST}"] = sha256_file(measurement / MANIFEST)
    expected["fixtures/fixtures.json"] = sha256_file(fixtures)
    expected.update(generator_source_hashes(Path(__file__).parent))
    expected.update(vanilla_input_hashes(game_dir))
    problems = []
    for k, v in sorted(expected.items()):
        if header.get(k) != v:
            problems.append(f"stale or missing header hash: {k}")
    if "order" not in header:
        problems.append("header lacks the ordering record")
    try:
        verify_manifest(measurement)
    except ManifestError as e:
        problems.append(f"manifest: {e}")
    return problems

def _script_files(root: Path) -> list:
    return sorted(p for p in root.rglob("*.txt") if "common" in p.parts)

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--game-dir", required=True)
    ap.add_argument("--measurement"); ap.add_argument("--fixtures"); ap.add_argument("--probe-only", action="store_true")
    a = ap.parse_args(argv)
    repo, game = Path(a.repo), Path(a.game_dir)
    roots = [repo / "research" / "probe"] if a.probe_only else [repo / "common", repo / "research" / "probe"]
    files = [f for r in roots if r.exists() for f in _script_files(r)]
    problems = check_bom(files)
    for f in files:
        problems += check_braces(f.read_text(encoding="utf-8-sig"), str(f.relative_to(repo)))
    if not a.probe_only:
        eff = repo / "common" / "scripted_effects" / "zz_hsi_effects.txt"
        if eff.exists():
            problems += check_rule_flags(eff.read_text(encoding="utf-8-sig"), game)
        if a.measurement and a.fixtures:
            problems += check_header(repo, game, Path(a.measurement), Path(a.fixtures))
    for p in problems:
        print(p, file=sys.stderr)
    print("validate: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/validate.py tools/tests/test_validate.py
git commit -m "Add static validator: BOM, braces, rule flags, binding hashes"
```

---

### Task 13: Shipped mod files and first generation (spec §8)

**Files:**
- Create: `.metadata/metadata.json`, `common/on_actions/zz_hsi_on_actions.txt`, `README.md`
- Generated: `common/scripted_effects/zz_hsi_effects.txt`, `research/tables.json`, `research/derivation.csv`

**Interfaces:**
- Consumes: Task 11 `generate.main`, Task 12 `validate.main`, the Task 10 measurement directory and `research/fixtures.json`.

- [ ] **Step 1: Write the static files**

```json
{
  "name": "Historical Starting Infamy",
  "id": "",
  "version": "0.1.0",
  "supported_game_version": "1.14.*",
  "short_description": "Every 1836 country starts with the infamy its 1816-1835 conduct would have generated under the game's own rules, decayed to 1836.",
  "tags": ["Historical", "Balance"],
  "relationships": [],
  "game_custom_data": {
    "multiplayer_synchronized": true
  }
}
```

`common/on_actions/zz_hsi_on_actions.txt` (write through `write_text_bom`, for example `cd tools && python3 -c "from pathlib import Path; from hsi.bom import write_text_bom; write_text_bom(Path('../common/on_actions/zz_hsi_on_actions.txt'), open('/dev/stdin').read())" <<'TXT'`):

```
# Historical Starting Infamy: additive registration on the after-lobby hook (spec §8).
# on_game_started fires while players are still in the lobby, before the game rules are final;
# vanilla reads has_game_rule only in on_game_started_after_lobby.
on_game_started_after_lobby = {
	on_actions = { hsi_on_game_started }
}
hsi_on_game_started = {
	effect = {
		hsi_apply_starting_infamy = yes
	}
}
```

`README.md`:

```markdown
# Historical Starting Infamy

A Victoria 3 (1.14.5) mod. Every country starts 1836 with the infamy its conduct between 1816 and 1835 would have generated under the game's own formula, replayed as one decaying balance per country and read off on 1 January 1836. Vanilla does this for Bolivia alone (50 for the conquest of Peru); this mod extends it to everyone else, and leaves Bolivia's 50 as it is.

## Starting infamy by game rule

<!-- hsi:table:start -->
<!-- hsi:table:end -->

Values apply once, when a new campaign opens. Adding the mod to an existing save changes nothing.

## How the numbers were derived

Each historical act is mapped to the vanilla war goal it corresponds to, priced with the vanilla 1.14.5 formula on measured 1836 population and GDP shares, charged on the day the demand was made, refunded or reduced as the game would do, and decayed at 5 per year to 1836. The full ledger, sources, measurement and derivation are in `research/`.

This is a fixed-snapshot approximation. In particular: 1836 shares and modifiers stand in for their historical values; split regions are priced as one state made of whole 1836 slices; the aggressor is always the goal's creator; standing, claims, adjacency and interest are documented historical judgments; decay runs at the base rate without modifiers; each goal has one claim and one resolution, without the primary-demand surcharge; same-day events follow a fixed order; the victim's reduction uses the creator's charge; results are rounded to two decimals and dropped below 0.05. Acts the rules cannot express are listed in `research/not_representable.md`.
```

- [ ] **Step 2: Generate and validate**

```bash
G="$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game"
M=$(ls -d research/measurement/2026-* | tail -1)
cd tools && python3 -m hsi.generate --repo .. --game-dir "$G" --measurement "../$M" --fixtures ../research/fixtures.json && \
python3 -m hsi.validate --repo .. --game-dir "$G" --measurement "../$M" --fixtures ../research/fixtures.json
```
Expected: `order SCGRF; ...` (or the measured order) and `validate: OK`. A refusal here is the gate doing its job: fix the ledger, the fixtures or the probe, never the generator's constants.

- [ ] **Step 3: Read the generated effect by eye** for the three things no test covers: every emitted tag is a country alive in 1836 (check `common/history/countries/`), no value looks implausible against its derivation row, and the comment on each line names the goals you expect.

- [ ] **Step 4: Commit**

```bash
git add .metadata common README.md research/tables.json research/derivation.csv
git commit -m "Ship: metadata, on_action registration, first generated effect and README table"
```

---

### Task 14: Save checker with failure-direction tests (spec §9 steps 3–6)

**Files:**
- Create: `tools/hsi/savecheck.py`, `tools/tests/test_savecheck.py`

**Interfaces:**
- Produces: `savecheck.block_at(text, idx) -> str`, `savecheck.top_block(text, key) -> str`, `savecheck.children(block) -> list[tuple[str, str]]`, `savecheck.depth1_scalars(block) -> dict[str, str]`, `savecheck.SaveInfo(game_date: str, rule_flags: set[str], countries: dict[str, float], global_flags: set[str])`, `savecheck.parse_save(path) -> SaveInfo`, `savecheck.check_save(info, tables: dict, rule_key: str, tolerance: float) -> list[str]`, `savecheck.main(argv)` with `--save --tables --rule --tolerance`.
- Facts relied on (from an EoR 1.14 plaintext save on this engine family): the gamestate has top-level blocks `meta_data`, `variables`, `country_manager`; `meta_data` holds `game_date=1836.1.1` and `game_rules={ settings={ ... } }` listing active flags; country records live under `country_manager={ database={ <id>={ ... } } }` with `definition="TAG"` and a depth-1 `infamy=` that is **absent when zero**; global variables appear under `variables={ data={ { flag=<name> ... } } }`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/tests/test_savecheck.py
from pathlib import Path
import pytest
from hsi import savecheck

SAVE = """SAV0100test
meta_data={
	save_game_version=1
	version="1.14.5"
	game_date=1836.1.1
	game_rules={
		settings={ achievements_allowed infamy_generation_very_low }
	}
}
variables={
	data={ {
			flag=hsi_applied
			tick=0
			data={
				type=boolean
				identity=1
			}
		} {
			flag=other_flag
			tick=0
		} }
	list={ }
}
country_manager={
	database={
		1={
			definition="EGY"
			infamy=2.29
			ai={
				infamy=99
			}
		}
		2={
			definition="BOL"
			infamy=50
		}
		3={
			definition="GBR"
			ai={
				infamy=7
			}
		}
	}
}
"""
TABLES = {"standard": {"EGY": 5.42}, "very_low": {"EGY": 2.29}, "low": {}, "high": {}, "very_high": {}}

def write(tmp_path, text=SAVE):
    p = tmp_path / "s.v3"; p.write_text(text, encoding="utf-8"); return p

def test_parse_save_fields(tmp_path):
    info = savecheck.parse_save(write(tmp_path))
    assert info.game_date == "1836.1.1"
    assert info.rule_flags == {"achievements_allowed", "infamy_generation_very_low"}
    assert info.countries == {"EGY": 2.29, "BOL": 50.0, "GBR": 0.0}   # nested ai.infamy ignored; absent -> 0
    assert "hsi_applied" in info.global_flags

def test_check_passes_on_matching_save(tmp_path):
    info = savecheck.parse_save(write(tmp_path))
    assert savecheck.check_save(info, TABLES, "very_low", 0.005) == []

@pytest.mark.parametrize("old,new,needle", [
    ("flag=hsi_applied", "flag=hsi_unapplied", "hsi_applied"),
    ("infamy=2.29\n", "", "EGY"),                       # hook never applied: expected positive missing
    ("infamy=2.29\n", "infamy=0\n", "positive"),       # zero where positive expected
    ("infamy=2.29\n", "infamy=4.58\n", "EGY"),         # doubled application
    ('definition="EGY"', 'definition="EGX"', "EGY"),   # wrong recipient
    ("game_date=1836.1.1", "game_date=1836.1.2", "date"),
    ("infamy_generation_very_low", "infamy_generation_low", "rule"),
    ('definition="GBR"\n', 'definition="GBR"\n\t\t\tinfamy=0.3\n', "GBR"),   # unexpected positive
    ("infamy=50\n", "infamy=49\n", "BOL"),
])
def test_failure_directions(tmp_path, old, new, needle):
    assert old in SAVE
    info = savecheck.parse_save(write(tmp_path, SAVE.replace(old, new, 1)))
    problems = savecheck.check_save(info, TABLES, "very_low", 0.005)
    assert problems, "expected a failure"
    assert any(needle in p for p in problems)

def test_boundary_tolerance_rejects_half_of_smallest_amount(tmp_path):
    tables = {"very_low": {"EGY": 0.05}}
    info = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.0")))
    assert savecheck.check_save(info, tables, "very_low", 0.005)
    info2 = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.1")))
    assert savecheck.check_save(info2, tables, "very_low", 0.005)
    info3 = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.052")))
    assert savecheck.check_save(info3, tables, "very_low", 0.005) == []

def test_empty_table_accepted_when_replay_says_so(tmp_path):
    text = SAVE.replace("infamy=2.29\n", "").replace("infamy_generation_very_low", "infamy_generation_low")
    info = savecheck.parse_save(write(tmp_path, text))
    assert savecheck.check_save(info, TABLES, "low", 0.005) == []

def test_truncated_save_fails_loudly(tmp_path):
    with pytest.raises(savecheck.SaveParseError):
        savecheck.parse_save(write(tmp_path, SAVE[: len(SAVE) // 2]))

REAL = sorted(Path(__file__).resolve().parents[2].glob("research/acceptance/*/saves/hsi_accept_std_1836_01_01*.v3"))

@pytest.mark.skipif(not REAL, reason="retained acceptance save absent on this machine")
def test_real_acceptance_save_matches_standard_table():
    import json
    repo = Path(__file__).resolve().parents[2]
    tables = json.loads((repo / "research" / "tables.json").read_text())
    info = savecheck.parse_save(REAL[-1])
    assert savecheck.check_save(info, tables, "standard", 0.005) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tools && uvx pytest -q tests/test_savecheck.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hsi.savecheck'`

- [ ] **Step 3: Implement savecheck.py**

```python
# tools/hsi/savecheck.py
"""Structural reader for plaintext 1.14 saves and the acceptance comparison (spec §9 steps 3-6).
Readers fail closed: a malformed save raises; nothing is guessed."""
from dataclasses import dataclass
import json
import re
import sys
from pathlib import Path
from . import constants as K

class SaveParseError(Exception):
    pass

def block_at(text: str, idx: int) -> str:
    i = text.index("{", idx)
    depth = 0
    for k in range(i, len(text)):
        c = text[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i:k + 1]
    raise SaveParseError(f"unbalanced block starting at offset {idx}")

def top_block(text: str, key: str) -> str:
    m = re.search(r"(?m)^" + re.escape(key) + r"=\{", text)
    if not m:
        raise SaveParseError(f"top-level block {key!r} not found")
    return block_at(text, m.start())

def children(block: str) -> list:
    """Direct `name={...}` children of a balanced block."""
    inner = block[1:-1]
    out = []
    i = 0
    while True:
        m = re.compile(r"([A-Za-z0-9_]+)=\{").search(inner, i)
        if not m:
            break
        # only accept matches at depth 0 of `inner`
        depth = inner.count("{", 0, m.start()) - inner.count("}", 0, m.start())
        if depth != 0:
            i = m.end(); continue
        child = block_at(inner, m.start())
        out.append((m.group(1), child))
        i = m.start() + len(child)
    return out

def depth1_scalars(block: str) -> dict:
    """name=value pairs at depth 1 only; nested blocks are skipped."""
    inner = block[1:-1]
    out, depth, i = {}, 0, 0
    line_start = 0
    while i < len(inner):
        c = inner[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "\n":
            if depth == 0:
                m = re.match(r"\s*([A-Za-z0-9_]+)=([^{}\s]+)\s*$", inner[line_start:i])
                if m:
                    out[m.group(1)] = m.group(2).strip('"')
            line_start = i + 1
        i += 1
    return out

@dataclass
class SaveInfo:
    game_date: str
    rule_flags: set
    countries: dict
    global_flags: set

def parse_save(path: Path) -> SaveInfo:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    meta = top_block(text, "meta_data")
    scal = depth1_scalars(meta)
    if "game_date" not in scal:
        raise SaveParseError("meta_data.game_date missing")
    rules = ""
    for name, blk in children(meta):
        if name == "game_rules":
            for n2, b2 in children(blk):
                if n2 == "settings":
                    rules = b2
    flags = set(re.findall(r"[A-Za-z0-9_]+", rules[1:-1])) if rules else set()
    countries = {}
    for name, blk in children(top_block(text, "country_manager")):
        if name != "database":
            continue
        for _id, rec in children(blk):
            s = depth1_scalars(rec)
            if "definition" in s:
                countries[s["definition"]] = float(s.get("infamy", "0"))
    globs = set(re.findall(r"\bflag=([A-Za-z0-9_]+)", top_block(text, "variables")))
    return SaveInfo(scal["game_date"], flags, countries, globs)

def check_save(info: SaveInfo, tables: dict, rule_key: str, tolerance: float) -> list:
    problems = []
    if info.game_date != "1836.1.1":
        problems.append(f"game date is {info.game_date}, expected 1836.1.1")
    expected_flag = K.RULE_FLAGS.get(rule_key)
    infamy_flags = {f for f in info.rule_flags if f.startswith("infamy_generation_")}
    if expected_flag is None and infamy_flags:
        problems.append(f"rule mismatch: save has {sorted(infamy_flags)} but table is standard")
    if expected_flag is not None and infamy_flags != {expected_flag}:
        problems.append(f"rule mismatch: save has {sorted(infamy_flags)}, expected {expected_flag}")
    if "hsi_applied" not in info.global_flags:
        problems.append("global variable hsi_applied is absent")
    table = tables[rule_key]
    for tag, want in sorted(table.items()):
        if tag not in info.countries:
            problems.append(f"expected positive record for {tag} is missing")
            continue
        got = info.countries[tag]
        if got <= 0.0:
            problems.append(f"{tag}: expected positive {want}, save has {got} (not positive)")
        elif abs(got - want) > tolerance:
            problems.append(f"{tag}: save has {got}, table says {want} (tolerance {tolerance})")
    for tag, got in sorted(info.countries.items()):
        if tag == "BOL":
            if abs(got - 50.0) > tolerance:
                problems.append(f"BOL: expected vanilla 50, save has {got}")
        elif tag not in table and got != 0.0:
            problems.append(f"{tag}: unexpected infamy {got}, not in the {rule_key} table")
    return problems

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True); ap.add_argument("--tables", required=True)
    ap.add_argument("--rule", required=True, choices=sorted(K.RULE_MULT)); ap.add_argument("--tolerance", type=float, default=0.005)
    a = ap.parse_args(argv)
    try:
        info = parse_save(Path(a.save))
    except SaveParseError as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr); return 2
    problems = check_save(info, json.loads(Path(a.tables).read_text()), a.rule, a.tolerance)
    for p in problems:
        print(p, file=sys.stderr)
    print("savecheck: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `cd tools && uvx pytest -q`
Expected: all pass except the real-save test, which skips with `retained acceptance save absent on this machine` until Task 15.

- [ ] **Step 5: Commit**

```bash
git add tools/hsi/savecheck.py tools/tests/test_savecheck.py
git commit -m "Add structural save checker with failure-direction tests"
```

---

### Task 15: Acceptance boots, lifecycle checks, error-log diff (spec §9 steps 3–7)

**Files:**
- Create: `research/acceptance/ACCEPTANCE.md`, `research/acceptance/<date>/error-vanilla.log`, `error-std.log`, `error-vlow.log`, `error-diff.txt`, `saves.sha256`, `launcher-playset.txt`; saves under `research/acceptance/<date>/saves/` (gitignored). Acceptance evidence lives apart from `research/measurement/<date>/`, whose manifest is already bound into the generated header and must not change.

**Interfaces:**
- Consumes: Task 14 `savecheck.main`, `research/tables.json`.

- [ ] **Step 1: Write ACCEPTANCE.md for Eric**

```markdown
# Acceptance boots (Eric), four short sessions

Setup once, from the repo root (backs up the playset, stages the shipped mod as the only enabled content):
```bash
V3="$HOME/Documents/Paradox Interactive/Victoria 3"; G="$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3"
cp "$V3/content_load.json" "$V3/content_load.json.bak-$(date +%Y%m%d-%H%M%S)"
```
Boot 0, vanilla baseline for the error log: write `{"enabledMods":[],"disabledDLC":[],"enabledUGC":[]}` to `$V3/content_load.json`, launch
`"$G/binaries/victoria3.app/Contents/MacOS/victoria3" -debug_mode`, New Game, Observe, quit without unpausing. Tell Claude (copies `logs/error.log` → `error-vanilla.log`).

Boot 1, Standard: write `{"enabledMods":[{"path":"$PWD"}],"disabledDLC":[],"enabledUGC":[]}` (the repo path), launch the same way, New Game with default rules, **Observe, do not unpause**, Save Game as `hsi_accept_std_1836_01_01`, quit. Tell Claude.

Boot 2, Very Low: same, with Infamy Generation set to Very Low on the New Game page; save as `hsi_accept_vlow_1836_01_01`; quit. Tell Claude.

Boot 3, lifecycle: Load Game `hsi_accept_std_1836_01_01` (stay paused), Save Game as `hsi_reload_1836_01_01`, quit. Then Load any older vanilla save you have (for example `france_1836_01_01`), stay paused, save as `hsi_lateenable_check`, quit. Tell Claude.

Finally restore the playset: `cp "$(ls -t "$V3"/content_load.json.bak-* | head -1)" "$V3/content_load.json"`.
```

- [ ] **Step 2: After each boot, Claude collects**

```bash
D=research/acceptance/$(date +%Y-%m-%d); V3="$HOME/Documents/Paradox Interactive/Victoria 3"
mkdir -p "$D/saves"
cp "$V3/logs/error.log" "$D/error-vanilla.log"      # after boot 0; error-std.log after boot 1; error-vlow.log after boot 2
cp "$V3/save games/hsi_accept_std_1836_01_01.v3" "$D/saves/"   # likewise vlow, reload, lateenable
sqlite3 "$V3/launcher-v2.sqlite" "SELECT m.displayName, pm.enabled FROM playsets_mods pm JOIN mods m ON m.id=pm.modId JOIN playsets p ON p.id=pm.playsetId WHERE p.isActive=1;" > "$D/launcher-playset.txt"
(cd "$D/saves" && shasum -a 256 *.v3) > "$D/saves.sha256"
```
If a save is not plaintext (`head -c 3` is `SAV` followed by a zip signature at offset 24), the game was not launched with `-debug_mode`: repeat the boot.

- [ ] **Step 3: Run the checks**

```bash
cd tools
python3 -m hsi.savecheck --save "../$D/saves/hsi_accept_std_1836_01_01.v3"  --tables ../research/tables.json --rule standard --tolerance 0.005
python3 -m hsi.savecheck --save "../$D/saves/hsi_accept_vlow_1836_01_01.v3" --tables ../research/tables.json --rule very_low --tolerance 0.005
python3 -m hsi.savecheck --save "../$D/saves/hsi_reload_1836_01_01.v3"      --tables ../research/tables.json --rule standard --tolerance 0.005
python3 - <<'PY'
# late-enable: every country's infamy unchanged versus the save it was loaded from, and no hsi_applied
from pathlib import Path
from hsi.savecheck import parse_save
import glob
d = sorted(glob.glob("../research/acceptance/2026-*"))[-1]
late = parse_save(Path(d) / "saves" / "hsi_lateenable_check.v3")
print("hsi_applied present:", "hsi_applied" in late.global_flags, "(expected False)")
print("positive infamy countries:", {k: v for k, v in late.countries.items() if v > 0})
PY
python3 - <<'PY'
# error log: new distinct messages after the mod boots
from pathlib import Path
import glob, re
d = Path(sorted(glob.glob("../research/acceptance/2026-*"))[-1])
def msgs(p): return {re.sub(r"^\[[^\]]*\]\[[^\]]*\]:\s*", "", l).strip() for l in p.read_text(errors="replace").splitlines() if l.strip()}
base = msgs(d / "error-vanilla.log")
out = []
for name in ("error-std.log", "error-vlow.log"):
    new = sorted(msgs(d / name) - base)
    out.append(f"== {name}: {len(new)} distinct NEW messages ==\n" + "\n".join(new))
(d / "error-diff.txt").write_text("\n\n".join(out) + "\n")
print("\n\n".join(out))
PY
```
Expected: three `savecheck: OK`; late-enable shows `hsi_applied present: False` and no new positive countries beyond the loaded save's own; `error-diff.txt` lists zero new distinct messages, or each listed one is explained in `ACCEPTANCE.md` with a fix or a reason.

- [ ] **Step 4: Storage precision check** (the tolerance's basis): in the Standard save, read the raw `infamy=` text of two emitted countries and record in `ACCEPTANCE.md` how many decimals the engine stored. If fewer than two, the tolerance must be raised to half a unit of the last stored decimal and the smallest emitted amount re-examined.

- [ ] **Step 5: Re-run the whole suite** (the real-save test now runs) and commit the evidence (saves stay gitignored; their hashes are committed)

```bash
cd tools && uvx pytest -q && cd .. && git add research/acceptance && git commit -m "Acceptance: standard and very-low boots, lifecycle checks, error-log diff"
```

---

### Task 16: Observer A/B logger and run (spec §9 step 8, evidence only)

**Files:**
- Create: `research/ab_logger/.metadata/metadata.json`, `research/ab_logger/common/on_actions/zz_hsi_ab_on_actions.txt`, `research/acceptance/AB.md`, `research/acceptance/<date>/ab-A-debug.log`, `ab-B-debug.log`, `ab-A-counts.txt`, `ab-B-counts.txt`

- [ ] **Step 1: Write the logger mod** (through `write_text_bom`)

```
# Test-only: logs every diplomatic play start. Loaded in both A/B arms; never shipped.
on_diplomatic_play_started = {
	on_actions = { hsi_ab_play_started }
}
hsi_ab_play_started = {
	effect = {
		debug_log = "HSIAB;[TimeKeeper.GetCurrentDate.GetString];initiator=[SCOPE.sCountry('initiator').GetTagName];target=[SCOPE.sCountry('target').GetTagName]"
	}
}
```
with a metadata.json naming it "HSI A/B logger", version 0.0.1, `multiplayer_synchronized: false`.

- [ ] **Step 2: AB.md procedure for Eric**

Two boots with `-debug_mode`, same custom RNG seed (the New Game page has the seed box in 1.14.5), Observe, speed 5 until 1842-01-01, quit. Arm A: `enabledMods` = logger only. Arm B: logger plus the shipped mod. Start `tools/drive/logcopy.py`-style copying of `debug.log` is not needed for six years at this volume, but copy `debug.log` immediately after each quit because the engine rotates it.

- [ ] **Step 3: Count and report**

```bash
D=$(ls -d research/acceptance/2026-* | tail -1)
for arm in A B; do grep -o 'HSIAB;[^"]*' "$D/ab-$arm-debug.log" | awk -F'initiator=' '{split($2,a,";"); c[a[1]]++} END {for (k in c) print k, c[k]}' | sort > "$D/ab-$arm-counts.txt"; done
```
Write the two tables side by side into `AB.md` for the ledger countries with one sentence: one matched seed, an observation, not an estimate. Commit.

---

## Execution notes

- Tasks 1–8 and 11–12 are pure Python with tests and can proceed without Eric. Task 9 is research. Tasks 10, 15 and 16 need Eric at the keyboard for the boots. Task 13 needs Task 10's measurement.
- The probe (Task 8) is the first thing the engine sees. If its first boot prints nothing parseable, the fix is in `probe_gen.py` with a failing test first; a second attempt's evidence is kept beside the first.
- Never edit `tools/hsi/constants.py` to make a test or an oracle pass. A mismatch between the generator and the engine is either a ledger judgment, a fixture transcription, or a formula-reading error, and each is fixed at its source.
