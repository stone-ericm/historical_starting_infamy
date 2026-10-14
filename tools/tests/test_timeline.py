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
