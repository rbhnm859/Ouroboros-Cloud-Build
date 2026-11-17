#!/usr/bin/env python3
"""Research-only causal event state machine. No broker, orders, or trading API."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import re

STATES = ('DETECTED','PRZ_OBSERVED','REACTION_OBSERVED','CONFIRMABLE',
          'ENTRY_ELIGIBLE','ACTIVE','EXITED','EXPIRED','REJECTED')
TRANSITIONS = {
 'DETECTED': {'PRZ_OBSERVED','REJECTED','EXPIRED'},
 'PRZ_OBSERVED': {'REACTION_OBSERVED','REJECTED','EXPIRED'},
 'REACTION_OBSERVED': {'CONFIRMABLE','REJECTED','EXPIRED'},
 'CONFIRMABLE': {'ENTRY_ELIGIBLE','REJECTED','EXPIRED'},
 'ENTRY_ELIGIBLE': {'ACTIVE','REJECTED','EXPIRED'},
 'ACTIVE': {'EXITED'},
 'EXITED': set(), 'EXPIRED': set(), 'REJECTED': set(),
}

class ContractViolation(ValueError):
    pass

def utc(t):
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise ContractViolation('timestamps must be timezone-aware')
    return t.astimezone(timezone.utc)

def canonical_event_id(direction, completion_time, d_price, tick_size):
    """Direction + completion clock + D at symbol tick size."""
    if direction not in ('Buy','Sell'):
        raise ContractViolation('invalid direction')
    t = utc(completion_time)
    size, price = Decimal(str(tick_size)), Decimal(str(d_price))
    if not size.is_finite() or not price.is_finite() or size <= 0:
        raise ContractViolation('invalid tick size or D price')
    ticks = (price / size).to_integral_value(rounding=ROUND_HALF_UP)
    return f'{direction}|{t:%Y%m%d%H%M%S}|{ticks * size:f}'

@dataclass(frozen=True)
class DecisionSnapshot:
    event_id: str
    state: str
    event_at: datetime
    observed_at: datetime
    available_at: datetime
    decision_at: datetime
    provenance_sha256: str
    decision: str = 'NONE'

    def __post_init__(self):
        if not self.event_id or self.state not in STATES or self.decision not in ('NONE','DEFER','ENTER','REJECT','EXIT'):
            raise ContractViolation('invalid event/state/decision')
        if not re.fullmatch(r'[a-f0-9]{64}', self.provenance_sha256):
            raise ContractViolation('invalid source SHA256')
        e, o, a, d = map(utc, (self.event_at, self.observed_at, self.available_at, self.decision_at))
        if not e <= o <= a <= d:
            raise ContractViolation('future information / chronology violation')
        if self.decision == 'ENTER' and self.state != 'ACTIVE':
            raise ContractViolation('ENTER requires ACTIVE state')
        if self.decision == 'REJECT' and self.state != 'REJECTED':
            raise ContractViolation('REJECT requires REJECTED state')
        if self.decision == 'EXIT' and self.state != 'EXITED':
            raise ContractViolation('EXIT requires EXITED state')
        if self.state == 'ACTIVE' and self.decision != 'ENTER':
            raise ContractViolation('ACTIVE without ENTER')
        if self.state == 'REJECTED' and self.decision != 'REJECT':
            raise ContractViolation('REJECTED without REJECT')
        if self.state == 'EXITED' and self.decision != 'EXIT':
            raise ContractViolation('EXITED without EXIT')

class ResearchEventMachine:
    """Immutable snapshots only; ENTER is simulated, never a broker order."""
    def __init__(self, initial):
        if initial.state != 'DETECTED' or initial.decision != 'NONE':
            raise ContractViolation('bad initial state')
        self._items = [initial]
    @property
    def snapshots(self):
        return tuple(self._items)
    @property
    def state(self):
        return self._items[-1].state
    def advance(self, nxt):
        prev = self._items[-1]
        if nxt.event_id != prev.event_id:
            raise ContractViolation('event id mutation')
        if utc(nxt.decision_at) <= utc(prev.decision_at):
            raise ContractViolation('non-monotone decision clock')
        if utc(nxt.event_at) != utc(prev.event_at):
            raise ContractViolation('event time mutation')
        if nxt.state == prev.state:
            if nxt.decision != 'DEFER' or prev.state not in ('PRZ_OBSERVED','REACTION_OBSERVED','CONFIRMABLE','ENTRY_ELIGIBLE'):
                raise ContractViolation('illegal repeated state')
        elif nxt.state not in TRANSITIONS[prev.state]:
            raise ContractViolation('illegal state transition')
        self._items.append(nxt)
