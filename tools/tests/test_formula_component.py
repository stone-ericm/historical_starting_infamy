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
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx((5 + 2 + 1) * 2.0)

def test_homeland_takes_precedence_over_shared_language():
    c = comp(aggressor_homeland=True, shared_language=True)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx(5 * 0.75)

def test_shared_language_alone():
    c = comp(shared_language=True)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx(5 * 0.85)

def test_bonus_booleans_only_within_selected_branch():
    c = comp(aggressor_homeland=True, homeland_bonus=True, language_bonus=True)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx(5 * 0.75 * 0.9)

def test_claim_takes_precedence_over_unification():
    c = comp(claim=True, scripted_unification=True)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx(max(1.0, 5 * 0.25))

def test_adjacency_and_interest_stack():
    c = comp(adjacent=True, interest_tier=1)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx(5 * 0.9 * 1.25)

def test_unrecognized_discount_requires_recognized_holder_and_unrecognized_owner():
    c = comp(owner_type="decentralized", standing="unincorporated")
    assert component_value(c, "recognized", -0.4, game="1.14.5") == pytest.approx(5 * 0.5 * 0.6)
    assert component_value(c, "unrecognized", -0.4, game="1.14.5") == pytest.approx(5 * 0.5)
    c2 = comp(owner_type="recognized")
    assert component_value(c2, "recognized", -0.4, game="1.14.5") == pytest.approx(5.0)

def test_state_floor_is_one():
    c = comp(standing="unincorporated", claim=True, adjacent=True, owner_type="decentralized")
    assert component_value(c, "recognized", -0.5, game="1.14.5") == pytest.approx(1.0)


# 1.15 (00_defines.txt:1080, 00_infamy_values.txt:31-75): WAR_GOAL_INFAMY_STATE_BASELINE = 1 is a floor under each
# of the population and GDP contributions, no longer a flat 5 added to their sum.

def test_115_baseline_floors_each_share_instead_of_adding():
    c = comp(pop_share_uncapped=2.0, gdp_share_uncapped=0.5, standing="capital")
    assert component_value(c, "recognized", 0.0) == pytest.approx((2.0 + 1.0) * 2.0)
    assert component_value(c, "recognized", 0.0, game="1.14.5") == pytest.approx((5 + 2.0 + 0.5) * 2.0)

def test_115_empty_state_is_two_floors():
    assert component_value(comp(), "recognized", 0.0) == pytest.approx(2.0)

def test_115_caps_unchanged_above_the_floor():
    c = comp(pop_share_uncapped=12.0, gdp_share_uncapped=20.0)
    assert component_value(c, "recognized", 0.0) == pytest.approx(11.0 + 15.0)

def test_115_state_minimum_still_one():
    c = comp(standing="unincorporated", claim=True, adjacent=True, owner_type="decentralized")
    assert component_value(c, "recognized", -0.5) == pytest.approx(1.0)

def test_default_game_is_115():
    assert K.GAME_VERSION == "1.15"
    c = comp(pop_share_uncapped=3.0, gdp_share_uncapped=4.0)
    assert component_value(c, "recognized", 0.0) == component_value(c, "recognized", 0.0, game=K.GAME_VERSION)

def test_unknown_game_refused():
    with pytest.raises(ValueError):
        component_value(comp(), "recognized", 0.0, game="1.13")


# Factor and precedence rules are the same in both games; check them under each, with shares above the 1.15 floor
# so a version-specific slip shows (review v02-r1 R3: disabling the unrecognized discount for 1.15 alone used to pass).
BASE_OF = {"1.14.5": lambda p, g: 5 + p + g, "1.15": lambda p, g: max(p, 1) + max(g, 1)}

@pytest.mark.parametrize("game", ["1.14.5", "1.15"])
def test_factors_and_precedence_in_both_games(game):
    b = BASE_OF[game](4.6, 3.9)
    shares = dict(pop_share_uncapped=4.6, gdp_share_uncapped=3.9)
    assert component_value(comp(**shares, aggressor_homeland=True, shared_language=True), "recognized", 0.0, game=game) == pytest.approx(b * 0.75)
    assert component_value(comp(**shares, shared_language=True), "recognized", 0.0, game=game) == pytest.approx(b * 0.85)
    assert component_value(comp(**shares, aggressor_homeland=True, homeland_bonus=True, language_bonus=True), "recognized", 0.0, game=game) == pytest.approx(b * 0.75 * 0.9)
    assert component_value(comp(**shares, claim=True, scripted_unification=True), "recognized", 0.0, game=game) == pytest.approx(b * 0.25)
    assert component_value(comp(**shares, adjacent=True, interest_tier=1), "recognized", 0.0, game=game) == pytest.approx(b * 0.9 * 1.25)
    c = comp(**shares, standing="homeland", owner_type="unrecognized", adjacent=True, interest_tier=2)
    assert component_value(c, "recognized", -0.1, game=game) == pytest.approx(b * 1.5 * 0.9 * 1.1 * 0.9)   # unrecognized discount
    assert component_value(c, "unrecognized", -0.1, game=game) == pytest.approx(b * 1.5 * 0.9 * 1.1)       # only for a recognized holder
