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
