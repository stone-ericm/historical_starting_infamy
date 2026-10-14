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

def component_breakdown(c: Component, holder_type: str, unrec_mult: float) -> dict:
    """state_infamy_value for one formula state, root = holder, with every intermediate (the derivation's
    component rows, final review F3): capped shares, base, standing, each factor applied, the pre-floor value."""
    pop_c, gdp_c = capped(c.pop_share_uncapped), capped(c.gdp_share_uncapped)
    base = K.STATE_BASELINE + pop_c + gdp_c
    v = base * K.STANDING[c.standing]
    factors = []
    if c.aggressor_homeland:
        factors.append(("homeland", 1.0 + K.HOMELAND_FACTOR))
        if c.homeland_bonus:
            factors.append(("homeland_bonus", 1.0 + K.HOMELAND_BONUS_FACTOR))
    elif c.shared_language:
        factors.append(("shared_language", 1.0 + K.SHARED_LANGUAGE_FACTOR))
        if c.language_bonus:
            factors.append(("language_bonus", 1.0 + K.SHARED_LANGUAGE_BONUS_FACTOR))
    if c.claim:
        factors.append(("claim", 1.0 + K.CLAIM_FACTOR))
    elif c.scripted_unification:
        factors.append(("scripted_unification", 1.0 + K.SCRIPTED_UNIFICATION_FACTOR))
    if c.adjacent:
        factors.append(("adjacent", 1.0 + K.ADJACENCY_FACTOR))
    factors.append((f"interest_tier_{c.interest_tier}", interest_factor(c.interest_tier)))
    if holder_type == "recognized" and c.owner_type != "recognized":
        factors.append(("against_unrecognized", 1.0 + unrec_mult))
    for _, f in factors:
        v *= f
    return {"pop_capped": pop_c, "gdp_capped": gdp_c, "base": base, "standing_mult": K.STANDING[c.standing],
            "factors": factors, "pre_floor": v, "value": max(v, K.STATE_MIN)}

def component_value(c: Component, holder_type: str, unrec_mult: float) -> float:
    """state_infamy_value for one formula state, root = holder."""
    return component_breakdown(c, holder_type, unrec_mult)["value"]

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
    holder_rank: str = "minor_power"      # constants.RANK_SCALING keys; the aggressor scaling
    target_rank: str = "minor_power"      # the play's target country; the target scaling

def rank_mult(holder_rank: str, target_rank: str) -> float:
    """1 + aggressor scaling + target scaling: one additive block, observed 2026-10-14 (Austria: +20 % and +20 % read as x1.4,
    not x1.44), applied as its own multiplication after the general modifier (Mascara: x0.95 then x0.80, not x0.75)."""
    return 1.0 + K.RANK_SCALING[holder_rank][0] + K.RANK_SCALING[target_rank][1]

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

STAGES = ("S", "C", "G", "K", "R", "F")       # severity, clamp, general modifier, rank block, rule, floor
# The order observed in the 2026-10-14 tooltips (severity, then the clamp line, then the percentage block, then the
# rule line) for S, C, G, K, R; F (the define's "after all multipliers") is last by the define comment, unobserved.
ORDER = STAGES
DEFAULT_ORDER = ORDER

def apply_stage(value: float, stage: str, spec: GoalSpec, general_mult: float, rule_mult: float, rank: float = 1.0) -> float:
    if stage == "K":
        return value * rank
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

def stage_values(raw: float, spec: GoalSpec, general_mult: float, rule_mult: float, order=ORDER, rank: float = 1.0) -> dict[str, float]:
    """Running value after each stage, keyed by stage letter, for the given order."""
    out: dict[str, float] = {}
    v = raw
    for st in order:
        v = apply_stage(v, st, spec, general_mult, rule_mult, rank)
        out[st] = v
    return out

def nominal_charge(g: GoalInputs, rule_key: str, order=ORDER) -> float:
    """A_r(g): the finished charge for one goal under one rule setting (spec §7, rank block added 2026-10-14)."""
    spec = GOALS[g.wargoal]
    vals = stage_values(raw_goal_value(g), spec, g.general_mult, K.RULE_MULT[rule_key], order, rank_mult(g.holder_rank, g.target_rank))
    return vals[order[-1]]

def truncate1(value: float) -> float:
    """What the 1.14.5 UI shows: one decimal, truncated (observed: 17.46 -> 17.4, 6.745 -> 6.7, 6.65 -> 6.6)."""
    import math
    return math.floor(value * 10 + 1e-9) / 10
