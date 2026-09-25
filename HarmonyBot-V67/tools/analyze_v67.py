#!/usr/bin/env python3
import argparse,json,pathlib,collections,statistics,math

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--phase",choices=["calibration","dev","validation","capital","fresh"],required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

def load_rows(root):
    out=[]
    for p in pathlib.Path(root).rglob("*.json"):
        try:d=json.load(open(p))
        except Exception:continue
        if isinstance(d,dict) and "basket_outcomes" in d and str(d.get("family","")).startswith("V67_"):
            d["_path"]=str(p); out.append(d)
    return out

def econ_from_baskets(b):
    vals=[float(x.get("net",0) or 0) for x in b]
    gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
    return {
      "baskets":len(b),
      "net":sum(vals),
      "pf":gp/gl if gl else (999.0 if gp else 0.0),
      "expectancy":sum(vals)/len(vals) if vals else 0.0,
      "win_rate":sum(x>0 for x in vals)/len(vals) if vals else 0.0
    }

def aggregate(xs,years):
    b=[z for x in xs for z in x.get("basket_outcomes",[])]
    e=econ_from_baskets(b)
    fam=collections.defaultdict(list)
    for z in b:fam[z["pattern"]].append(z)
    fam_e={k:econ_from_baskets(v) for k,v in sorted(fam.items())}
    top=max([len(v) for v in fam.values()] or [0])/max(1,len(b))
    non_abcd=econ_from_baskets([z for z in b if z["pattern"]!="AB=CD"])
    positive_families=sum(1 for v in fam_e.values() if v["baskets"]>=5 and v["net"]>0 and v["pf"]>1)
    e.update({
      "frequency":len(b)/years if years else 0,
      "max_dd_pct":max([float(x.get("max_dd_pct",0) or 0) for x in xs] or [0]),
      "all_positive":bool(xs) and all(float(x.get("net",0) or 0)>0 for x in xs),
      "clean":bool(xs) and all(bool(x.get("engineering_clean")) and int(x.get("actual_basket_risk_violations",0) or 0)==0 and int(x.get("margin_risk_violations",0) or 0)==0 and int(x.get("execution_errors",0) or 0)==0 for x in xs),
      "family_performance":fam_e,
      "top_family_share":top,
      "non_abcd_net":non_abcd["net"],
      "non_abcd_pf":non_abcd["pf"],
      "positive_families_ge5":positive_families
    })
    return e

rows=load_rows(a.root)
o={"version":"HarmonyBot V67","phase":a.phase,"source_rows":len(rows)}

if a.phase=="calibration":
    by={(x["family"],x["window"]):x for x in rows}
    req=[("V67_CONTROL",w) for w in ["A","B","C"]]+[("V67_PRODUCT",w) for w in ["A","B","C"]]
    miss=[f"{m}:{w}" for m,w in req if (m,w) not in by]
    if miss: raise SystemExit("missing calibration evidence: "+",".join(miss))
    C=aggregate([by[("V67_CONTROL",w)] for w in ["A","B","C"]],1.5)
    P=aggregate([by[("V67_PRODUCT",w)] for w in ["A","B","C"]],1.5)
    historical_v52={"run_id":35531304357,"sha":"c6c22289bba0a7966ab044f859833264fd8f8da0",
                    "variant":"FAMILY_IDENTITY_RECONSTRUCTION","baskets":200,"frequency":133.3333333333,
                    "net":2902.27,"pf":1.3754845136750589,"expectancy":14.51135,"win_rate":0.435,
                    "max_dd_pct":9.815,"data_snapshot_sha":None}
    historical_exact=(C["baskets"]==200 and abs(C["net"]-2902.27)<=0.05 and
                      abs(C["pf"]-1.3754845136750589)<=0.002 and abs(C["frequency"]-133.3333333333)<=0.01)
    # Same-run current control is the valid causal baseline. The 2026-09-20 historical V52 artifact
    # did not persist a market-data hash, so failure to exactly reproduce its totals is reported,
    # not silently treated as an Alpha failure.
    control_replay_valid=(C["clean"] and C["frequency"]>=80 and C["frequency"]<=150 and
                          C["net"]>0 and C["pf"]>1 and C["expectancy"]>0)
    diversity=(P["top_family_share"]<=0.55 and P["non_abcd_net"]>0 and P["positive_families_ge5"]>=3)
    breakthrough=(P["all_positive"] and P["clean"] and P["frequency"]>=80 and P["frequency"]<=150 and
                  P["net"]>max(historical_v52["net"],C["net"]) and P["pf"]>=2.0 and
                  P["expectancy"]>=20 and P["win_rate"]>=.50 and P["max_dd_pct"]<=6 and diversity)
    candidate=bool(control_replay_valid and breakthrough)
    delta={"baskets":P["baskets"]-C["baskets"],"frequency":P["frequency"]-C["frequency"],
           "net":P["net"]-C["net"],"pf":P["pf"]-C["pf"],"expectancy":P["expectancy"]-C["expectancy"],
           "win_rate":P["win_rate"]-C["win_rate"],"max_dd_pct":P["max_dd_pct"]-C["max_dd_pct"]}
    o.update({"historical_v52_reference":historical_v52,
              "historical_exact_reproduction":historical_exact,
              "data_governance_note":"Historical V52 artifact has no data_snapshot_sha; current same-run control is used for causal comparison.",
              "control":C,"product":P,"control_replay_valid":control_replay_valid,"delta_vs_control":delta,
              "diversity_gate":diversity,"breakthrough_gate":breakthrough,"candidate":candidate,
              "status":"DEV_CANDIDATE" if candidate else "HOLD_CALIBRATION"})

elif a.phase=="dev":
    q=[x for x in rows if x["family"]=="V67_PRODUCT"]
    by={x["window"]:x for x in q}
    req=["D_A","D_B","D_C"]
    if any(w not in by for w in req): raise SystemExit("missing dev windows")
    D=aggregate([by[w] for w in req],1.5)
    diversity=(D["top_family_share"]<=0.55 and D["non_abcd_net"]>0 and D["positive_families_ge5"]>=3)
    candidate=(D["all_positive"] and D["clean"] and D["frequency"]>=60 and D["frequency"]<=150 and D["net"]>=1800 and
               D["pf"]>=2 and D["expectancy"]>=20 and D["win_rate"]>=.50 and D["max_dd_pct"]<=6 and diversity)
    o.update({"dev":D,"diversity_gate":diversity,"candidate":bool(candidate),
              "status":"VALIDATION_CANDIDATE" if candidate else "HOLD_DEV"})

elif a.phase=="validation":
    q=[x for x in rows if x["family"]=="V67_PRODUCT" and str(x["window"]).startswith("VAL_")]
    base=[x for x in q if abs(float(x.get("spread",1) or 1)-1.0)<1e-9]
    B=aggregate(base,.5)
    stress=bool(q) and all(float(x.get("net",0) or 0)>0 and bool(x.get("engineering_clean")) for x in q)
    candidate=(len(base)==2 and B["all_positive"] and B["clean"] and B["pf"]>=2 and B["expectancy"]>=20 and
               B["win_rate"]>=.50 and B["max_dd_pct"]<=6 and stress)
    o.update({"validation":B,"stress_all_positive":stress,"candidate":bool(candidate),
              "status":"CAPITAL_CANDIDATE" if candidate else "HOLD_VALIDATION"})

elif a.phase=="capital":
    caps=[x for x in rows if x["family"]=="V67_PRODUCT" and str(x["window"]).startswith("CAPITAL_")]
    expected={100,150,200,300,500,1000,10000}
    got={int(round(float(x.get("starting_balance",0) or 0))) for x in caps}
    per=[]
    for x in sorted(caps,key=lambda z:float(z.get("starting_balance",0) or 0)):
        ok=(x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and
            float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and bool(x.get("engineering_clean")) and
            int(x.get("actual_basket_risk_violations",0) or 0)==0 and int(x.get("margin_risk_violations",0) or 0)==0)
        per.append({"balance":x.get("starting_balance"),"baskets":x.get("baskets"),"net":x.get("net"),"pf":x.get("pf"),
                    "expectancy":x.get("expectancy"),"max_dd_pct":x.get("max_dd_pct"),"pass":ok})
    candidate=(got==expected and all(x["pass"] for x in per))
    o.update({"balances":per,"candidate":bool(candidate),"status":"PRE_FRESH_FREEZE" if candidate else "HOLD_CAPITAL"})

elif a.phase=="fresh":
    q=[x for x in rows if x["family"]=="V67_PRODUCT" and str(x["window"]).startswith("FRESH_")]
    if len(q)!=1: raise SystemExit("expected one fresh row")
    x=q[0]
    candidate=(x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and
               float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and bool(x.get("engineering_clean")))
    o.update({"fresh":x,"candidate":bool(candidate),"status":"COMMERCIAL_FREEZE_APPROVED" if candidate else "HOLD_FRESH"})

pathlib.Path(a.out).write_text(json.dumps(o,indent=2))
print(json.dumps(o,indent=2))
