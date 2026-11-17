#!/usr/bin/env python3
"""V74 R19: deterministic, research-only, single-action executable-side tick replay.

No broker API, optimizer, protected years or model training. This is a *reference*
semantics test, not cTrader runtime parity or a source-certified price-history run.

Financial units: tick bid/ask, stop, target, entry/exit slippage and fees are
all **USD per unit of underlying** for XAUUSD. Position size and margin/unit
must come from certified broker metadata; no lot-to-unit conversion is guessed.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
from pathlib import Path
import re


class ReplayContractError(ValueError):
    pass


def as_utc(x: datetime) -> datetime:
    if not isinstance(x, datetime) or x.tzinfo is None or x.utcoffset() is None:
        raise ReplayContractError('timezone-aware time required')
    return x.astimezone(timezone.utc)


def dec(x) -> Decimal:
    try:
        value = Decimal(str(x))
    except Exception as exc:
        raise ReplayContractError('invalid decimal value') from exc
    if not value.is_finite():
        raise ReplayContractError('non-finite decimal')
    return value


def digest_check(x):
    if not isinstance(x, str) or not re.fullmatch(r'[a-f0-9]{64}', x):
        raise ReplayContractError('source hash not valid SHA256 format')


@dataclass(frozen=True)
class Tick:
    time: datetime
    seq: int
    bid: Decimal
    ask: Decimal
    tradable: bool

    def __post_init__(self):
        as_utc(self.time)
        if isinstance(self.seq, bool) or not isinstance(self.seq, int) or self.seq < 0:
            raise ReplayContractError('invalid tick sequence')
        if not isinstance(self.tradable, bool):
            raise ReplayContractError('tradable must be bool')
        if dec(self.bid) <= 0 or dec(self.ask) < dec(self.bid):
            raise ReplayContractError('crossed, zero or negative market quote')

    @property
    def key(self):
        return as_utc(self.time), self.seq


@dataclass(frozen=True)
class TickTape:
    ticks: tuple[Tick, ...]
    bytes_sha256: str
    max_gap_seconds: int

    def __post_init__(self):
        digest_check(self.bytes_sha256)
        if not self.ticks:
            raise ReplayContractError('empty tick tape')
        if not isinstance(self.max_gap_seconds, int) or self.max_gap_seconds <= 0:
            raise ReplayContractError('max gap must be positive seconds')
        previous = None
        for tick in self.ticks:
            if not isinstance(tick, Tick) or (previous is not None and tick.key <= previous):
                raise ReplayContractError('tick tape not strictly sequential')
            previous = tick.key


def read_tick_csv(path: Path, max_gap_seconds: int):
    """Exact-byte SHA256 + strict five-column UTF-8 tick input.

    A recorded hash is a custody fingerprint, NOT proof broker issued the data.
    """
    raw = Path(path).read_bytes()
    if not raw:
        raise ReplayContractError('empty tick file')
    import io
    rows = csv.DictReader(io.StringIO(raw.decode('utf-8', errors='strict')))
    required = ['time_utc', 'seq', 'bid', 'ask', 'tradable']
    if rows.fieldnames != required:
        raise ReplayContractError('exact tick columns required')
    parsed = []
    try:
        for row in rows:
            if None in row or any(row[k] is None for k in required):
                raise ReplayContractError('incorrect csv arity')
            stamp = row['time_utc']
            if not stamp.endswith('Z'):
                raise ReplayContractError('timestamp must be explicit UTC Z')
            t = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if row['tradable'] not in ('true', 'false'):
                raise ReplayContractError('invalid market availability')
            parsed.append(Tick(t, int(row['seq']), dec(row['bid']), dec(row['ask']), row['tradable'] == 'true'))
    except (TypeError, ValueError, KeyError, OverflowError) as exc:
        raise ReplayContractError('malformed tick file') from exc
    return TickTape(tuple(parsed), hashlib.sha256(raw).hexdigest(), max_gap_seconds)


@dataclass(frozen=True)
class TradeIntent:
    event_id: str
    side: str  # BUY/SELL
    decision_at: datetime
    available_at: datetime
    last_entry_at: datetime
    expires_at: datetime
    stop: Decimal
    target: Decimal
    units: Decimal
    equity_usd: Decimal
    free_margin_usd: Decimal
    margin_per_unit_usd: Decimal
    roundtrip_commission_per_unit_usd: Decimal
    modeled_swap_per_unit_usd: Decimal
    entry_slippage_usd: Decimal
    exit_slippage_usd: Decimal
    max_entry_spread_usd: Decimal
    minimum_stop_distance_usd: Decimal
    max_basket_risk_fraction: Decimal
    min_net_reward_risk: Decimal
    cost_source_sha256: str
    already_active_basket: bool
    used_event_before: bool

    def __post_init__(self):
        if not self.event_id or self.side not in ('BUY', 'SELL'):
            raise ReplayContractError('invalid canonical event or side')
        if not isinstance(self.already_active_basket, bool) or not isinstance(self.used_event_before, bool):
            raise ReplayContractError('basket/event flags must be explicit')
        digest_check(self.cost_source_sha256)
        if not as_utc(self.available_at) <= as_utc(self.decision_at) < as_utc(self.last_entry_at) < as_utc(self.expires_at):
            raise ReplayContractError('future features or invalid decision/expiry chronology')
        nonneg = ('roundtrip_commission_per_unit_usd', 'modeled_swap_per_unit_usd',
                  'entry_slippage_usd', 'exit_slippage_usd', 'max_entry_spread_usd',
                  'minimum_stop_distance_usd')
        positive = ('units', 'equity_usd', 'margin_per_unit_usd',
                    'max_basket_risk_fraction', 'min_net_reward_risk', 'stop', 'target')
        for name in nonneg:
            if dec(getattr(self, name)) < 0:
                raise ReplayContractError('negative assumed cost or tolerance: ' + name)
        for name in positive:
            if dec(getattr(self, name)) <= 0:
                raise ReplayContractError('nonpositive trade input: ' + name)
        if dec(self.free_margin_usd) < 0 or dec(self.max_basket_risk_fraction) > Decimal('0.05'):
            raise ReplayContractError('invalid margin or >5% basket risk constitution')
        if dec(self.min_net_reward_risk) < Decimal('2'):
            raise ReplayContractError('minimum net reward/risk constitution reduced')


@dataclass(frozen=True)
class ReplayResult:
    cause: str
    entered: bool
    entry_at: datetime | None
    exit_at: datetime | None
    entry_price: Decimal | None
    exit_price: Decimal | None
    planned_net_rr: Decimal | None
    realized_net_r: Decimal | None
    source_tick_sha256: str
    cost_source_sha256: str
    research_only: bool = True


def replay(intent: TradeIntent, tape: TickTape) -> ReplayResult:
    """Faithfully apply only explicit deterministic shadow-order assumptions.

    - First executable tick strictly AFTER decision can enter.
    - BUY enters at ask and exits on bid; SELL enters at bid and exits on ask.
    - Same-timestamp ordered ticks can resolve an open trade after entry.
    - Target/stop checked before time-expiry for ticks strictly before expiry.
    - Stop fills can gap beyond the stop, worsening realized R.
    - A gap in source tick coverage yields CENSORED, never an invented win.
    """
    if not isinstance(intent, TradeIntent) or not isinstance(tape, TickTape):
        raise ReplayContractError('invalid research contracts')

    def result(cause, entered=False, start=None, end=None, fill=None, exit_fill=None, rr=None, net_r=None):
        return ReplayResult(cause, entered, start, end, fill, exit_fill, rr, net_r,
                            tape.bytes_sha256, intent.cost_source_sha256)

    if intent.already_active_basket or intent.used_event_before:
        return result('REJECT_DUPLICATE_OR_BASKET')
    if tape.ticks[0].time > as_utc(intent.decision_at):
        return result('CENSORED')
    if dec(intent.units)*dec(intent.margin_per_unit_usd) > dec(intent.free_margin_usd):
        return result('REJECT_MARGIN')

    side = intent.side
    stop, target = dec(intent.stop), dec(intent.target)
    total_cost = dec(intent.roundtrip_commission_per_unit_usd)+dec(intent.modeled_swap_per_unit_usd)
    exit_slip = dec(intent.exit_slippage_usd)
    entered = False
    entry_key = None
    entry_t = entry_price = planned_rr = risk = None
    last_time = None
    saw_high_spread = False
    saw_session_closed = False
    for tick in tape.ticks:
        t = as_utc(tick.time)
        if last_time is not None and (t-last_time).total_seconds() > tape.max_gap_seconds:
            return result('CENSORED', entered, entry_t, None, entry_price, None, planned_rr)
        last_time = t
        if not entered:
            if t <= as_utc(intent.decision_at):
                continue
            if t > as_utc(intent.last_entry_at):
                return result('NO_FILL_SESSION' if saw_session_closed else
                              'NO_FILL_SPREAD' if saw_high_spread else 'NO_FILL_TIMEOUT')
            if not tick.tradable:
                saw_session_closed = True
                continue
            if dec(tick.ask)-dec(tick.bid)>dec(intent.max_entry_spread_usd):
                saw_high_spread = True
                continue
            fill = (dec(tick.ask)+dec(intent.entry_slippage_usd)) if side=='BUY' else (dec(tick.bid)-dec(intent.entry_slippage_usd))
            if fill<=0:
                return result('REJECT_GEOMETRY')
            stop_distance = fill-stop if side=='BUY' else stop-fill
            target_distance = target-fill if side=='BUY' else fill-target
            if stop_distance < dec(intent.minimum_stop_distance_usd) or target_distance<=0:
                return result('REJECT_GEOMETRY')
            risk = stop_distance+exit_slip+total_cost
            reward = target_distance-exit_slip-total_cost
            if risk<=0 or reward/risk<dec(intent.min_net_reward_risk):
                return result('REJECT_NET_RR')
            if risk*dec(intent.units)>dec(intent.equity_usd)*dec(intent.max_basket_risk_fraction):
                return result('REJECT_BASKET_RISK')
            entered=True
            entry_t=t
            entry_key=tick.key
            entry_price=fill
            planned_rr=reward/risk
            continue  # no exit on the entry tick: chronological causality

        if tick.key<=entry_key:
            raise ReplayContractError('broken tick sequence')
        if not tick.tradable:
            return result('CENSORED', True, entry_t, None, entry_price, None, planned_rr)
        if t>=as_utc(intent.expires_at):
            cause='TIME_EXPIRE'
            exit_price=(dec(tick.bid)-exit_slip) if side=='BUY' else (dec(tick.ask)+exit_slip)
        elif (side=='BUY' and dec(tick.bid)<=stop) or (side=='SELL' and dec(tick.ask)>=stop):
            cause='SL_FIRST'
            exit_price=(min(stop,dec(tick.bid))-exit_slip) if side=='BUY' else (max(stop,dec(tick.ask))+exit_slip)
        elif (side=='BUY' and dec(tick.bid)>=target) or (side=='SELL' and dec(tick.ask)<=target):
            cause='TP_FIRST'
            # Target price, not hindsight-best quote. Exit slippage is an explicit
            # pessimistic hypothesis; real limit-order behavior needs parity.
            exit_price=(target-exit_slip) if side=='BUY' else (target+exit_slip)
        else:
            continue
        net_profit=(exit_price-entry_price) if side=='BUY' else (entry_price-exit_price)
        net_profit-=total_cost
        return result(cause, True, entry_t, t, entry_price, exit_price, planned_rr, net_profit/risk)
    return result('CENSORED', entered, entry_t, None, entry_price, None, planned_rr)
