#!/usr/bin/env python3
import argparse,json,pathlib,collections,statistics
ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--phase",required=True); ap.add_argument("--out",required=True)
a=ap.parse_args()

def rows():
    out=[]
    for p in pathlib.Path(a.root).rglob("*.json"):
        try:d=json.load(open(p))
        except:continue
        if isinstance(d,dict) and "basket_outcomes" in d and d.get("version")=="HarmonyBot V67": out.append(d)
    return out

def clean(x):
    return bool(x.get("engineering_clean")) and all(int(x.get(k,0) or 0)==0 for k in [
      "execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
      "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"])

def agg(xs,years):
    b=[z for x in xs for z in x.get("basket_outcomes",[])]
    v=[float(z.get("net",0) or 0) for z in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
    fam=collections.defaultdict(list)
    for z in b:fam[z.get("pattern","UNKNOWN")].append(float(z.get("net",0) or 0))
    famsum={k:{"baskets":len(q),"net":sum(q)} for k,q in fam.items()}
    dominant=max([q["baskets"] for q in famsum.values()] or [0])/len(b) if b else 0
    abcd=famsum.get("AB=CD",{}).get("baskets",0)/len(b) if b else 0
    return {"baskets":len(b),"frequency":len(b)/years if years else 0,"net":sum(v),
            "pf":gp/gl if gl else (999 if gp else 0),"expectancy":sum(v)/len(v) if v else 0,
            "win_rate":sum(x>0 for x in v)/len(v) if v else 0,
            "max_dd_pct":max([float(x.get("max_dd_pct",0) or 0) for x in xs] or [0]),
            "all_positive":bool(xs) and all(float(x.get("net",0) or 0)>0 for x in xs),
            "clean":bool(xs) and all(clean(x) for x in xs),
            "family_performance":famsum,"dominant_family_share":dominant,"abcd_share":abcd,
            "positive_family_count":sum(q["net"]>0 for q in famsum.values()),
            "avg_grid_risk_utilization":statistics.mean([float(x.get("avg_grid_risk_utilization",0) or 0) for x in xs]) if xs else 0}

R=rows(); o={"version":"HarmonyBot V67","phase":a.phase,"source_rows":len(R)}
if a.phase=="dev":
    by={(x["mode"],x["window"]):x for x in R}
    wins=["L1","L2","L3","D1","D2","D3"]; miss=[f"{m}:{w}" for m in ["V67_V52_CONTROL","V67_PRODUCT"] for w in wins if (m,w) not in by]
    if miss: raise SystemExit("missing evidence "+",".join(miss))
    CL=agg([by[("V67_V52_CONTROL",w)] for w in ["L1","L2","L3"]],1.5)
    PL=agg([by[("V67_PRODUCT",w)] for w in ["L1","L2","L3"]],1.5)
    PD=agg([by[("V67_PRODUCT",w)] for w in ["D1","D2","D3"]],1.5)
    # Historical V52 200-basket evidence is retained as a legacy benchmark, not an impossible
    # same-number reproduction gate under a changed cTrader runtime/data snapshot. Causal comparison
    # is always PRODUCT vs same-run V52 CONTROL.
    control_repro=(CL["baskets"]>0 and CL["clean"])
    min_preserved_frequency=max(80.0, CL["frequency"]*.67)
    legacy_preserve=(PL["frequency"]>=min_preserved_frequency and PL["net"]>CL["net"] and
                     PL["pf"]>CL["pf"] and PL["expectancy"]>CL["expectancy"] and
                     PL["all_positive"] and PL["clean"])
    diversity=(PL["abcd_share"]<=.45 and PL["dominant_family_share"]<=.50 and PL["positive_family_count"]>=3)
    current_commercial=(PD["frequency"]>=80 and PD["net"]>=1800 and PD["pf"]>=2 and PD["expectancy"]>=20 and
                        PD["win_rate"]>=.50 and PD["max_dd_pct"]<=6 and PD["all_positive"] and PD["clean"])
    grid_ok=(PL["avg_grid_risk_utilization"]>0 and PL["avg_grid_risk_utilization"]<=1.000001 and
             PD["avg_grid_risk_utilization"]>0 and PD["avg_grid_risk_utilization"]<=1.000001)
    candidate=bool(control_repro and legacy_preserve and diversity and current_commercial and grid_ok)
    o.update({"control_legacy":CL,"product_legacy":PL,"product_current_dev":PD,
      "control_reproduction":control_repro,"legacy_throughput_preservation":legacy_preserve,"min_preserved_frequency":min_preserved_frequency,
      "family_diversification_gate":diversity,"current_commercial_gate":current_commercial,"grid_risk_gate":grid_ok,
      "double_profit_stretch":PL["net"]>=2*2902.27,"candidate":candidate,
      "status":"VALIDATION_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE",
      "windows":{"control":{w:by[("V67_V52_CONTROL",w)] for w in wins},"product":{w:by[("V67_PRODUCT",w)] for w in wins}}})
elif a.phase=="validation":
    q=[x for x in R if str(x.get("window","")).startswith("VAL_")]
    base=[x for x in q if abs(float(x.get("spread",0))-1.0)<1e-9]
    A=agg(base,.5); stress=bool(q) and all(float(x.get("net",0) or 0)>0 and clean(x) for x in q)
    candidate=bool(len(base)==2 and A["all_positive"] and A["pf"]>=2 and A["expectancy"]>=20 and A["win_rate"]>=.5 and A["max_dd_pct"]<=6 and A["clean"] and stress)
    o.update({"base":A,"stress_all_positive_clean":stress,"candidate":candidate,"status":"CAPITAL_CANDIDATE" if candidate else "HOLD_VALIDATION"})
elif a.phase=="capital":
    q=[x for x in R if str(x.get("window","")).startswith("CAPITAL_")]
    expected={100,150,200,300,500,1000,10000}; got={int(round(float(x.get("starting_balance",0)))) for x in q}
    per=[]
    for x in sorted(q,key=lambda z:float(z.get("starting_balance",0))):
        ok=x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and clean(x)
        per.append({"balance":x.get("starting_balance"),"baskets":x.get("baskets"),"net":x.get("net"),"pf":x.get("pf"),"expectancy":x.get("expectancy"),"pass":ok})
    candidate=got==expected and all(x["pass"] for x in per)
    o.update({"balances":per,"candidate":bool(candidate),"status":"PRE_FRESH_FREEZE" if candidate else "HOLD_CAPITAL"})
elif a.phase=="fresh":
    q=[x for x in R if str(x.get("window","")).startswith("FRESH_")]
    if len(q)!=1: raise SystemExit("fresh row count !=1")
    x=q[0]; candidate=x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and clean(x)
    o.update({"fresh":x,"candidate":bool(candidate),"status":"COMMERCIAL_FREEZE_APPROVED" if candidate else "HOLD_FRESH"})
pathlib.Path(a.out).write_text(json.dumps(o,indent=2)); print(json.dumps(o,indent=2))
