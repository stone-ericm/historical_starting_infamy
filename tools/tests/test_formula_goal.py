# tools/tests/test_formula_goal.py
import pytest
from hsi import constants as K
from hsi.formula import (Component, GoalInputs, GOALS, raw_goal_value, stage_values,
                         nominal_charge, rank_mult, truncate1, DEFAULT_ORDER, ORDER)

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

def test_rank_block_values_and_fallbacks():
    assert rank_mult("great_power", "unrecognized_regional_power") == pytest.approx(0.8)     # France vs Mascara
    assert rank_mult("great_power", "great_power") == pytest.approx(1.4)                      # France vs Austria
    assert rank_mult("great_power", "insignificant_power") == pytest.approx(1.1)              # France vs Lucca
    assert rank_mult("minor_power", "minor_power") == pytest.approx(1.0)
    assert rank_mult(K.FALLBACK_RANK["unrecognized"], K.FALLBACK_RANK["recognized"]) == pytest.approx(1.3)
    assert ORDER == ("S", "C", "G", "K", "R", "F")

def test_observed_capture_a_mascara_protectorate_2026_10_14():
    # fixture-A: Algiers 18.0 + Oran 17.4 = 35.5; x0.50 severity; -5 %; +20 % France GP; -40 % Mascara unrec. regional; -50 % rule; shown 6.7
    algiers = Component(4.6, 3.9, "homeland", "unrecognized", adjacent=True, interest_tier=2)       # +5.0 +4.6 +3.9, x1.5, x0.9, +10 %, x0.9
    oran = Component(2.6, 2.2, "capital", "unrecognized", adjacent=True, interest_tier=2)           # +5.0 +2.6 +2.2, x2.0, x0.9, +10 %, x0.9
    g = GoalInputs("make_protectorate", (algiers, oran), "recognized", -0.1, -0.05, holder_rank="great_power", target_rank="unrecognized_regional_power")
    assert truncate1(raw_goal_value(g)) == pytest.approx(35.5)
    assert truncate1(nominal_charge(g, "very_low")) == pytest.approx(6.7)
    assert nominal_charge(g, "very_low") == pytest.approx(35.5 * 0.5 * 0.95 * 0.8 * 0.5, abs=0.01)
    # the additive alternative (one percentage block of -25 %) would have shown 6.6, which the tooltip did not
    assert truncate1(35.5 * 0.5 * 0.75 * 0.5) == pytest.approx(6.6)

def test_observed_capture_cmin_parma_regime_change_2026_10_14():
    # fixture-Cmin-parma: +5.0 +1.7 +1.3, x2.0 capital = 16.0; x0.10; Minimum of 3; -5 %; +20 %; -10 % insignificant; -50 %; shown 1.5
    parma = Component(1.7, 1.3, "capital", "recognized", interest_tier=3)
    g = GoalInputs("regime_change", (parma,), "recognized", -0.1, -0.05, holder_rank="great_power", target_rank="insignificant_power")
    vals = stage_values(raw_goal_value(g), GOALS["regime_change"], -0.05, 0.5, ORDER, rank_mult("great_power", "insignificant_power"))
    assert vals["S"] == pytest.approx(1.6) and vals["C"] == pytest.approx(3.0)
    assert truncate1(nominal_charge(g, "very_low")) == pytest.approx(1.5)

def test_observed_capture_cmax_austria_regime_change_2026_10_14():
    # fixture-Cmax-austria: 345.2 from 15 states; x0.10; Maximum of 10; -5 %; +20 %; +20 %; -50 %; shown 6.6
    big = tuple(Component(15.0, 15.0, "capital", "recognized") for _ in range(5))     # 5 x 70 = 350: above the cap either way
    g = GoalInputs("regime_change", big, "recognized", -0.1, -0.05, holder_rank="great_power", target_rank="great_power")
    assert nominal_charge(g, "very_low") == pytest.approx(10 * 0.95 * 1.4 * 0.5)
    assert truncate1(nominal_charge(g, "very_low")) == pytest.approx(6.6)

def test_unknown_order_stage_rejected():
    with pytest.raises(ValueError):
        stage_values(1.0, GOALS["conquer_state"], 0.0, 1.0, ("S", "X"))
