#!/usr/bin/env python3
"""Pure, fail-closed scenario admission for V74 day/week research.

No data fetching, no broker orders, no cTrader runtime, no OOF or learning.
Broker unit size and margin must be *provided* from audited account metadata.
Return planned net return only, not actual profits or a predicted win.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_FLOOR
import re

FAMILIES=("Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab",
          "DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD")
PROFILES={"DAY":(Decimal("0.005"),Decimal("0.0115")),
          "WEEK":(Decimal("0.010"),Decimal("0.0230"))}
REQUIRED_NET_RR=Decimal("2.30")
# A hard research safety bound, not a replacement for verified broker session calendars.
HORIZON_LIMIT={"DAY":timedelta(hours=24),"WEEK":timedelta(days=7)}

class ContractError(ValueError):
    pass

def value(x):
    try:
        d=Decimal(str(x))
    except Exception as e:
        raise ContractError("invalid numerical input") from e
    if not d.is_finite():raise ContractError("nonfinite numerical input")
    return d

def utc(x):
    if not isinstance(x,datetime) or x.tzinfo is None or x.utcoffset() is None:
        raise ContractError("timezone-aware time required")
    return x.astimezone(timezone.utc)

@dataclass(frozen=True)
class Proposal:
    event_id:str
    family:str
    side:str
    horizon:str
    available_at:datetime
    decision_at:datetime
    expires_at:datetime
    broker_horizon_close_at:datetime
    bid:Decimal
    ask:Decimal
    stop:Decimal
    target:Decimal
    equity_usd:Decimal
    available_margin_usd:Decimal
    broker_margin_usd_per_unit:Decimal
    broker_min_units:Decimal
    broker_unit_step:Decimal
    roundtrip_fee_usd_per_unit:Decimal
    swap_usd_per_unit:Decimal
    entry_slippage_usd_per_unit:Decimal
    exit_slippage_usd_per_unit:Decimal
    broker_spec_sha256:str
    used_event:bool=False
    active_basket:bool=False
    def __post_init__(self):
        if not self.event_id or self.family not in FAMILIES or self.side not in ("BUY","SELL") or self.horizon not in PROFILES:
            raise ContractError("invalid event, family, side or horizon")
        if not isinstance(self.used_event,bool) or not isinstance(self.active_basket,bool):
            raise ContractError("invalid event/basket flag")
        if not isinstance(self.broker_spec_sha256,str) or not re.fullmatch("[0-9a-f]{64}",self.broker_spec_sha256):
            raise ContractError("missing source-verified broker specification fingerprint")
        if not utc(self.available_at)<=utc(self.decision_at)<utc(self.expires_at)<=utc(self.broker_horizon_close_at):
            raise ContractError("future information / session expiry conflict")
        if utc(self.broker_horizon_close_at)-utc(self.decision_at)>HORIZON_LIMIT[self.horizon]:
            raise ContractError("holding horizon exceeds maximum; broker session close must also be verified")
        positive=("bid","ask","stop","target","equity_usd","broker_margin_usd_per_unit",
                  "broker_min_units","broker_unit_step")
        nonnegative=("available_margin_usd","roundtrip_fee_usd_per_unit","swap_usd_per_unit",
                     "entry_slippage_usd_per_unit","exit_slippage_usd_per_unit")
        for k in positive:
            if value(getattr(self,k))<=0:raise ContractError("nonpositive "+k)
        for k in nonnegative:
            if value(getattr(self,k))<0:raise ContractError("negative "+k)
        if value(self.ask)<value(self.bid):raise ContractError("crossed market quotes")
        if value(self.equity_usd)<Decimal("100"):raise ContractError("below supported research equity")

def assess(p:Proposal):
    """Returns independent scenario feasibility; does not execute.

    Cost inputs are per underlying unit USD. Broker's actual lot->unit mapping,
    tick value, quantity granularity and fees must be sourced, never assumed.
    """
    if not isinstance(p,Proposal):raise ContractError("invalid proposal")
    def reject(reason, **diagnostics):
        return {"status":"REJECT","reason":reason,"family":p.family,"horizon":p.horizon,
                "research_only":True,"order_enabled":False,**diagnostics}
    if p.used_event or p.active_basket:return reject("DUPLICATE_OR_BASKET")
    entry=value(p.ask) if p.side=="BUY" else value(p.bid)
    stop=value(p.stop);target=value(p.target)
    if (p.side=="BUY" and not stop<entry<target) or (p.side=="SELL" and not target<entry<stop):
        return reject("INVALID_PRICE_GEOMETRY")
    gross_loss=abs(entry-stop)
    gross_win=abs(target-entry)
    costs=sum((value(p.roundtrip_fee_usd_per_unit),value(p.swap_usd_per_unit),
               value(p.entry_slippage_usd_per_unit),value(p.exit_slippage_usd_per_unit)),Decimal(0))
    loss_unit=gross_loss+costs
    gain_unit=gross_win-costs
    if gain_unit<=0 or gain_unit/loss_unit<REQUIRED_NET_RR:
        return reject("PLANNED_NET_RR_TOO_LOW")
    risk_fraction,target_fraction=PROFILES[p.horizon]
    risk_budget=value(p.equity_usd)*risk_fraction
    # Preserve existing conservative 5x free-margin/risk headroom.
    max_by_margin=value(p.available_margin_usd)/(value(p.broker_margin_usd_per_unit)+Decimal("5")*loss_unit)
    max_by_risk=risk_budget/loss_unit
    cap=min(max_by_margin,max_by_risk)
    minimum=value(p.broker_min_units)
    step=value(p.broker_unit_step)
    if cap<minimum:return reject("BROKER_MIN_SIZE_INFEASIBLE")
    # Legal volume grid is min_units + k * step, not necessarily k * step.
    units=minimum+((cap-minimum)/step).to_integral_value(rounding=ROUND_FLOOR)*step
    planned_loss=loss_unit*units
    planned_gain=gain_unit*units
    if planned_loss>risk_budget or units*value(p.broker_margin_usd_per_unit)+planned_loss*5>value(p.available_margin_usd):
        raise ContractError("internal sizing guard failure")
    target_amount=value(p.equity_usd)*target_fraction
    if planned_gain<target_amount:
        # A shadow diagnostic: never turns a rejected proposal into an order.
        return reject("TARGET_EQUITY_PERCENT_NOT_FEASIBLE",
                      legal_units=str(units),planned_gain_usd=str(planned_gain),
                      target_gain_usd=str(target_amount),
                      shortfall_usd=str(target_amount-planned_gain),
                      planned_net_rr=str(gain_unit/loss_unit))
    return {"status":"ELIGIBLE_FOR_RESEARCH","research_only":True,"order_enabled":False,
            "family":p.family,"horizon":p.horizon,"units":str(units),
            "planned_loss_usd":str(planned_loss),"planned_gain_usd":str(planned_gain),
            "planned_net_rr":str(gain_unit/loss_unit),
            "planned_equity_gain_fraction":str(planned_gain/value(p.equity_usd)),
            "risk_budget_usd":str(risk_budget),
            "broker_spec_sha256":p.broker_spec_sha256}
