#!/usr/bin/env python3
"""Five-decimal harmonic geometry contract + causal adaptive math features.

Detection envelopes remain broad enough to preserve supply. Canonical anchors are
used only to measure geometry quality/structure. All derived features use values
already available at the completed decision bar; no outcome/MFE/MAE is used.
"""
import math

# Registry keys match v74_model_lib.FAMILIES.
# Anchors are exact to 5 decimals. Multi-anchor legs represent canonical
# Fibonacci alternatives; residual uses the nearest legal anchor.
CANONICAL_5DP={
 "Gartley":{
   "xab":(.61800,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.27200,1.41400,1.61800), "xad":(.78600,),
   "abcd":(1.00000,1.27200)},
 "Bat":{
   "xab":(.38200,.50000), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.61800,2.00000,2.24000,2.61800), "xad":(.88600,),
   "abcd":(1.00000,1.27200)},
 "AltBat":{
   "xab":(.38200,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(2.00000,2.24000,2.61800,3.14000,3.61800), "xad":(1.13000,),
   "abcd":(1.61800,)},
 "Butterfly":{
   "xab":(.78600,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.61800,2.00000,2.24000,2.61800), "xad":(1.27200,1.61800),
   "abcd":(1.00000,1.27200,1.61800)},
 "Crab":{
   "xab":(.38200,.50000,.61800), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(2.24000,2.61800,3.14000,3.61800), "xad":(1.61800,),
   "abcd":(1.27200,1.61800)},
 "DeepCrab":{
   "xab":(.88600,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(2.00000,2.24000,2.61800,3.14000,3.61800), "xad":(1.61800,),
   "abcd":(1.00000,1.27200)},
 # Project constitutional families. These anchors are separated from the
 # detection envelope and are deliberately not allowed to redefine it.
 "DeepGartley":{
   "xab":(.78600,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.13000,1.27200,1.41400,1.61800,2.00000), "xad":(.88600,),
   "abcd":(1.00000,1.27200,1.61800)},
 "Rat":{
   "xab":(.50000,.61800,.78600), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.27200,1.61800,2.00000,2.24000,2.61800), "xad":(.88600,1.00000,1.13000),
   "abcd":(1.00000,1.27200,1.61800)},
 "Cypher":{
   "xab":(.38200,.50000,.61800), "abc":(1.13000,1.27200,1.41400),
   "bcd":(.78600,), "xad":(.78600,), "abcd":(1.00000,)},
 "Shark":{
   "xab":(.50000,.61800,.88600,1.13000), "abc":(1.13000,1.27200,1.41400,1.61800),
   "bcd":(1.61800,2.00000,2.24000), "xad":(.88600,1.00000,1.13000),
   "abcd":(1.00000,)},
 "FiveZero":{
   "xab":(1.13000,1.27200,1.41400,1.61800), "abc":(1.61800,2.00000,2.24000),
   "bcd":(.50000,.61800), "xad":(.50000,.61800,1.00000), "abcd":(1.00000,)},
 "ABCD":{
   "xab":(.61800,), "abc":(.38200,.50000,.61800,.78600,.88600),
   "bcd":(1.13000,1.27200,1.41400,1.61800,2.00000,2.24000,2.61800),
   "xad":(1.00000,), "abcd":(1.00000,1.27200,1.61800)}
}

# Current detector envelopes, represented independently from ideal anchors.
# They are audited so canonical precision cannot silently drift outside supply.
DETECTION_ENVELOPES_5DP={
 "Gartley":{"xab":(.60000,.63600),"abc":(.38200,.88600),"bcd":(1.13000,1.61800),"xad":(.77000,.80000)},
 "Bat":{"xab":(.38200,.50000),"abc":(.38200,.88600),"bcd":(1.61800,2.61800),"xad":(.87500,.89500)},
 "AltBat":{"xab":(.30000,.39500),"abc":(.38200,.88600),"bcd":(2.00000,3.61800),"xad":(1.10000,1.16000)},
 "Butterfly":{"xab":(.77000,.80000),"abc":(.38200,.88600),"bcd":(1.61800,2.61800),"xad":(1.24000,1.30000)},
 "Crab":{"xab":(.38200,.61800),"abc":(.38200,.88600),"bcd":(2.24000,3.61800),"xad":(1.58000,1.66000)},
 "DeepCrab":{"xab":(.87500,.90000),"abc":(.38200,.88600),"bcd":(2.00000,3.61800),"xad":(1.58000,1.66000)},
 "DeepGartley":{"xab":(.70000,.82000),"abc":(.38200,.88600),"bcd":(1.13000,2.00000),"xad":(.82000,.95000)},
 "Rat":{"xab":(.50000,.82000),"abc":(.38200,.88600),"bcd":(1.27200,2.61800),"xad":(.88000,1.13000)}
}

_RATIO_INDEX={"xab":12,"abc":13,"bcd":14,"xad":15,"abcd":16}

def _finite(x):
    try:return math.isfinite(float(x))
    except Exception:return False

def nearest_log_residual(value,anchors):
    """Signed log-ratio residual to nearest canonical anchor."""
    if not _finite(value) or float(value)<=0 or not anchors:return 0.0
    v=float(value)
    a=min((float(z) for z in anchors if z>0),key=lambda z:abs(math.log(v/z)))
    return math.log(v/a)

def harmonic_precision_vector(family,features):
    """Causal high-math geometry vector derived from existing setup telemetry.

    Output:
      5 signed nearest-anchor log residuals
      L1/L2/Linf residual norms
      residual-energy entropy + concentration
      XABCD closure error and AB*BC/CD identity error
      geometry x regime interactions (ATR percentile/transition/trend/MTF)
    """
    spec=CANONICAL_5DP.get(family,CANONICAL_5DP["ABCD"])
    r=[]
    for k in ("xab","abc","bcd","xad","abcd"):
        idx=_RATIO_INDEX[k]
        v=features[idx] if idx<len(features) else 0.0
        r.append(nearest_log_residual(v,spec.get(k,())))
    ar=[abs(x) for x in r]
    l1=sum(ar)/len(ar)
    l2=math.sqrt(sum(x*x for x in r)/len(r))
    linf=max(ar) if ar else 0.0
    e=[x*x for x in r];es=sum(e)
    if es>1e-18:
        p=[x/es for x in e if x>0]
        entropy=-sum(q*math.log(q) for q in p)/math.log(len(r))
        concentration=max(p)
    else:
        entropy=0.0;concentration=0.0

    xab=float(features[12]) if len(features)>12 else 0.0
    abc=float(features[13]) if len(features)>13 else 0.0
    bcd=float(features[14]) if len(features)>14 else 0.0
    xad=float(features[15]) if len(features)>15 else 0.0
    abcd=float(features[16]) if len(features)>16 else 0.0
    # Alternating XABCD closure: AD/XA = XAB*(1-ABC+ABC*BCD).
    pred_xad=xab*(1.0-abc+abc*bcd) if xab>0 and abc>0 and bcd>0 else 0.0
    closure=math.log(max(pred_xad,1e-12)/max(xad,1e-12)) if pred_xad>0 and xad>0 else 0.0
    # CD/AB should equal (BC/AB)*(CD/BC).
    pred_abcd=abc*bcd if abc>0 and bcd>0 else 0.0
    abcd_closure=math.log(max(pred_abcd,1e-12)/max(abcd,1e-12)) if pred_abcd>0 and abcd>0 else 0.0

    trend=abs(float(features[9])) if len(features)>9 else 0.0
    mtf=abs(float(features[11])) if len(features)>11 else 0.0
    atrp=max(0.0,min(1.0,float(features[26]))) if len(features)>26 else 0.0
    transition=max(0.0,min(1.0,float(features[29]))) if len(features)>29 else 0.0
    return r+[l1,l2,linf,entropy,concentration,closure,abcd_closure,
              l2*atrp,l2*transition,l2*trend,l2*mtf,
              abs(closure)*atrp,abs(abcd_closure)*transition]

def contract_audit():
    issues=[]
    for fam,env in DETECTION_ENVELOPES_5DP.items():
        spec=CANONICAL_5DP[fam]
        for leg,(lo,hi) in env.items():
            anchors=spec.get(leg,())
            if not any(lo-1e-12<=a<=hi+1e-12 for a in anchors):
                issues.append({"family":fam,"leg":leg,"reason":"NO_CANONICAL_ANCHOR_INSIDE_ENVELOPE",
                               "envelope":[lo,hi],"anchors":list(anchors)})
    return {"families":len(CANONICAL_5DP),"precision_decimals":5,
            "issues":issues,"pass":len(CANONICAL_5DP)==12 and not issues}
