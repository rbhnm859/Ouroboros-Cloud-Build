#!/usr/bin/env python3
import json,pathlib,sys,statistics,collections,math
v51=pathlib.Path(sys.argv[1]); v64c=pathlib.Path(sys.argv[2]); hist=pathlib.Path(sys.argv[3]); dev=pathlib.Path(sys.argv[4]); out=pathlib.Path(sys.argv[5]); out.mkdir(parents=True,exist_ok=True)

HIST_BEST={"baskets":58,"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":0.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":0.50,"max_dd_pct":6.0}

def load_one(root,needle):
    xs=[p for p in root.rglob("*.json") if needle in p.name]
    if not xs: raise SystemExit(f"missing {needle} under {root}")
    for p in xs:
        try:
            d=json.load(open(p))
            if "basket_outcomes" in d:return d
        except: pass
    raise SystemExit(f"no audit json for {needle}")

v51w={w:load_one(v51,f"-{w}.json") for w in "ABC"}
v64cw={w:load_one(v64c,f"-{w}.json") for w in "ABC"}
hw={w:load_one(hist,f"-{w}.json") for w in ["H21","H22","H23"]}
dw={w:load_one(dev,f"-{w}.json") for w in "ABC"}

def pf(vals):
    gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
    return gp/gl if gl else (999 if gp else 0)
def pct(v,p):
    if not v:return 0
    y=sorted(v);q=(len(y)-1)*p;lo=int(q);hi=min(len(y)-1,lo+1);return y[lo]+(y[hi]-y[lo])*(q-lo)
def aggregate(ws,years):
    rows=[r for z in ws.values() for r in z.get("basket_outcomes",[])]
    vals=[r["net"] for r in rows]; rr=[r.get("r",0) for r in rows]; wins=[x for x in rr if x>0]; n=len(rows)
    fam=collections.defaultdict(float)
    for r in rows:fam[r.get("pattern","UNKNOWN")]+=r["net"]
    top5=sum(sorted([max(0,x) for x in vals],reverse=True)[:5])
    return {
      "baskets":n,"frequency":n/years,"unique_setups":len({r.get("setup","") for r in rows}),
      "net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,
      "win_rate":sum(x>0 for x in vals)/n if n else 0,
      "max_dd_pct":max((z.get("max_dd_pct",0) for z in ws.values()),default=0),
      "all_windows_positive":all(z.get("net",0)>0 and z.get("pf",0)>1 and z.get("expectancy",0)>0 for z in ws.values()),
      "engineering_clean":all(z.get("engineering_clean",False) for z in ws.values()),
      "risk_clean":all(z.get("actual_basket_risk_violations",0)==0 and z.get("margin_risk_violations",0)==0 for z in ws.values()),
      "p95_winner_r":pct(wins,.95),"max_winner_r":max(wins) if wins else 0,
      "net_ex_top5":sum(vals)-top5,"family_net":dict(sorted(fam.items())),"windows":ws
    }

# Exact control equivalence on same setups and economic result.
def signature(ws):
    rows=[]
    for w in "ABC":
        for r in ws[w].get("basket_outcomes",[]):
            rows.append((w,r.get("setup",""),r.get("pattern",""),r.get("route",""),round(float(r.get("net",0)),2),round(float(r.get("r",0)),3)))
    return rows
control_equivalence=signature(v51w)==signature(v64cw)

c=aggregate(v51w,1.5); h=aggregate(hw,3.0); p=aggregate(dw,1.5)
p["right_tail_preservation_ratio"]=p["p95_winner_r"]/c["p95_winner_r"] if c["p95_winner_r"] else 0
p["frequency_delta_vs_control"]=p["frequency"]-c["frequency"]
p["net_delta_vs_control"]=p["net"]-c["net"]
p["frequency_expansion_gate"]=p["frequency_delta_vs_control"]<=1e-9 or p["net_delta_vs_control"]>0
p["right_tail_gate"]=p["right_tail_preservation_ratio"]>=0.80
p["historical_best_gate"]=(p["net"]>HIST_BEST["net"] and p["pf"]>HIST_BEST["pf"] and p["expectancy"]>HIST_BEST["expectancy"] and
                           p["win_rate"]>=HIST_BEST["win_rate"] and p["max_dd_pct"]<=HIST_BEST["max_dd_pct"])
p["commercial_gate"]=(p["baskets"]<=COMM["max_baskets"] and p["frequency"]>=COMM["min_frequency"] and p["net"]>=COMM["net"] and
                       p["pf"]>=COMM["pf"] and p["expectancy"]>=COMM["expectancy"] and p["win_rate"]>=COMM["win_rate"] and
                       p["max_dd_pct"]<=COMM["max_dd_pct"] and p["all_windows_positive"] and p["engineering_clean"] and p["risk_clean"])
p["concentration_gate"]=p["net_ex_top5"]>0
p["legacy_stability_gate"]=h["all_windows_positive"] and h["engineering_clean"] and h["risk_clean"]
p["control_equivalence_gate"]=control_equivalence

passes=[control_equivalence,p["frequency_expansion_gate"],p["right_tail_gate"],p["historical_best_gate"],p["commercial_gate"],p["concentration_gate"],p["legacy_stability_gate"]]
candidate="V64_PRODUCT" if all(passes) else ""
report={"version":"HarmonyBot V64","product_goal":"XAUUSD harmonic commercial cBot","immutable_v51_control":c,
        "legacy_2021_2023_fixed_product":h,"dev_2024h2_2025h2_product":p,"historical_best_reference":HIST_BEST,
        "commercial_minimum":COMM,"control_dynamic_equivalence":control_equivalence,"development_candidate":candidate,
        "status":"DEV_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE",
        "next_stage":"VALIDATION_2026_Q1_Q2" if candidate else "STOP_DEV_HOLD","fresh_used":False}
(out/"V64_PRODUCT_FRONTIER.json").write_text(json.dumps(report,indent=2))
(out/"candidate.txt").write_text(candidate)
print(json.dumps(report,indent=2))
