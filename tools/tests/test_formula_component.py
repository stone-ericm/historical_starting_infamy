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
