#!/usr/bin/env python3
"""Twelve-family pre-D projection. Research only. No broker orders.

Ratio ranges are SOURCE-PINNED to existing V71 canonical family profiles,
not represented as new Carney-standard assertions. D cannot move a PRZ.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

FAMILY_BANDS = {
  'Gartley': ((.600,.636),(.382,.886),(1.13,1.618),(.770,.800)),
  'Bat': ((.382,.500),(.382,.886),(1.618,2.618),(.875,.895)),
  'AltBat': ((.300,.395),(.382,.886),(2.0,3.618),(1.10,1.16)),
  'Butterfly': ((.770,.800),(.382,.886),(1.618,2.618),(1.24,1.30)),
  'Crab': ((.382,.618),(.382,.886),(2.24,3.618),(1.58,1.66)),
  'DeepCrab': ((.875,.900),(.382,.886),(2.0,3.618),(1.58,1.66)),
  'DeepGartley': ((.70,.82),(.382,.886),(1.13,2.0),(.82,.95)),
  'Rat': ((.50,.82),(.382,.886),(1.272,2.618),(.88,1.13))
}
FAMILIES = (*FAMILY_BANDS.keys(), 'Cypher', 'Shark', 'FiveZero', 'ABCD')

class PatternContractError(ValueError): pass

def D(x):
    try: y=Decimal(str(x))
    except Exception as exc: raise PatternContractError('invalid price/ratio') from exc
    if not y.is_finite(): raise PatternContractError('nonfinite price/ratio')
    return y

def utc(t):
    if not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise PatternContractError('timezone-aware timestamp required')
    return t.astimezone(timezone.utc)

def inside(x,r):
    return D(str(r[0])) <= x <= D(str(r[1]))

def price_band(anchor, direction, span, bounds):
    u=anchor + direction*span*D(str(bounds[0]))
    v=anchor + direction*span*D(str(bounds[1]))
    return min(u,v),max(u,v)

def intersect(bands):
    lo=max(z[0] for z in bands)
    hi=min(z[1] for z in bands)
    return (lo,hi) if lo<=hi else None

@dataclass(frozen=True)
class KnownPivots:
    x:Decimal
    a:Decimal
    b:Decimal
    c:Decimal
    x_at:datetime
    a_at:datetime
    b_at:datetime
    c_at:datetime
    c_confirmed_at:datetime
    decision_at:datetime
    atr_at_decision:Decimal
    def __post_init__(self):
        for label in ('x','a','b','c','atr_at_decision'):
            if D(getattr(self,label))<=0: raise PatternContractError('nonpositive '+label)
        if not utc(self.x_at)<utc(self.a_at)<utc(self.b_at)<utc(self.c_at)<=utc(self.c_confirmed_at)<=utc(self.decision_at):
            raise PatternContractError('pivot timing or confirmation is noncausal')
        x,a,b,c=map(D,(self.x,self.a,self.b,self.c))
        if not (a>x and b<a and c>b) and not (a<x and b>a and c<b):
            raise PatternContractError('nonalternating known pivots')

    @property
    def side(self): return 'BUY' if D(self.a)>D(self.x) else 'SELL'
    @property
    def sign(self): return D('-1') if self.side=='BUY' else D('1')

@dataclass(frozen=True)
class Prediction:
    family:str
    side:str
    core_low:Decimal
    core_high:Decimal
    source_cutoff:datetime
    def observational_band(self,atr,extra_atr):
        if D(extra_atr) not in (D('0'),D('0.10'),D('0.20')):
            raise PatternContractError('only preregistered observation buffers are allowed')
        if D(atr)<=0:raise PatternContractError('ATR must be positive')
        delta=D(atr)*D(extra_atr)
        return self.core_low-delta,self.core_high+delta


def predict(family,p:KnownPivots):
    """Pre-D pattern hypothesis, not permission to trade.

    ALL price bands use X,A,B,C, confirmed by decision_at. Neither D nor
    any future high/low/exit/PnL is passed to this function.
    """
    if family not in FAMILIES or not isinstance(p,KnownPivots):
        raise PatternContractError('unknown family or pivots')
    x,a,b,c=map(D,(p.x,p.a,p.b,p.c))
    xa=abs(a-x);ab=abs(b-a);bc=abs(c-b);xc=abs(c-x)
    r=ab/xa;s=bc/ab
    sign=p.sign
    if family in FAMILY_BANDS:
        rb,sb,tb,qb=FAMILY_BANDS[family]
        if not inside(r,rb) or not inside(s,sb):return None
        bands=(price_band(a,sign,xa,qb),price_band(c,sign,bc,tb))
    elif family=='ABCD':
        if not inside(s,(.382,.886)):return None
        bands=(price_band(c,sign,ab,(.80,1.25)),price_band(c,sign,bc,(1.13,2.618)))
    elif family=='Cypher':
        if not inside(r,(.382,.618)) or not inside(xc/xa,(1.13,1.414)):return None
        bands=(price_band(c,sign,xc,(.70,.90)),)
    elif family=='Shark':
        if not inside(s,(1.13,1.618)):return None
        bands=(price_band(a,sign,xa,(.85,1.25)),price_band(c,sign,bc,(1.13,2.24)))
    else:  # FiveZero
        if not inside(r,(1.13,1.618)) or not inside(s,(1.618,2.24)):return None
        bands=(price_band(c,sign,bc,(.45,.65)),)
    z=intersect(bands)
    if z is None:return None
    return Prediction(family,p.side,z[0],z[1],utc(p.decision_at))


def review_completion(p:KnownPivots, pred:Prediction, d_price, d_observed_at:datetime, observation_buffer_atr=0):
    """Separately report observed PRZ touch vs exact canonical family identity.

    Near-miss observations NEVER become a valid pattern via buffer expansion.
    """
    if pred is None or not isinstance(pred,Prediction) or pred.family not in FAMILIES:
        raise PatternContractError('invalid projection')
    if not utc(d_observed_at)>utc(p.decision_at)>=pred.source_cutoff:
        raise PatternContractError('completion must happen after prediction')
    x,a,b,c=map(D,(p.x,p.a,p.b,p.c));d=D(d_price)
    if d<=0:raise PatternContractError('invalid D price')
    direction_ok=(d<c) if p.side=='BUY' else (d>c)
    band=pred.observational_band(p.atr_at_decision,observation_buffer_atr)
    observed=bool(band[0]<=d<=band[1] and direction_ok)
    xa=abs(a-x);ab=abs(a-b);bc=abs(c-b);cd=abs(c-d)
    r=ab/xa;s=bc/ab;t=cd/bc;q=abs(d-a)/xa;u=cd/ab;xc=abs(c-x)
    fam=pred.family
    if fam in FAMILY_BANDS:
        rb,sb,tb,qb=FAMILY_BANDS[fam]
        identity=inside(r,rb) and inside(s,sb) and inside(t,tb) and inside(q,qb)
    elif fam=='ABCD':identity=inside(s,(.382,.886)) and inside(t,(1.13,2.618)) and inside(u,(.80,1.25))
    elif fam=='Cypher':identity=inside(r,(.382,.618)) and inside(xc/xa,(1.13,1.414)) and inside(cd/xc,(.70,.90))
    elif fam=='Shark':identity=inside(s,(1.13,1.618)) and inside(t,(1.13,2.24)) and inside(q,(.85,1.25))
    else:identity=inside(r,(1.13,1.618)) and inside(s,(1.618,2.24)) and inside(t,(.45,.65))
    return {'family':fam,'side':p.side,'observed_prz_touch':observed,
            'canonical_identity':bool(identity and direction_ok),
            'research_signal_only':True,'trade_authorized':False}


def all_family_predictions(p):
    return tuple(z for f in FAMILIES if (z:=predict(f,p)) is not None)
