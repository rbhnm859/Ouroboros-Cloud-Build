#!/usr/bin/env python3
import json,pathlib,sys,collections
v64=pathlib.Path(sys.argv[1]); v66c=pathlib.Path(sys.argv[2]); legacy=pathlib.Path(sys.argv[3]); dev=pathlib.Path(sys.argv[4]); out=pathlib.Path(sys.argv[5]); out.mkdir(parents=True,exist_ok=True)

HIST_BEST={"baskets":58,"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":0.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":0.50,"max_dd_pct":6.0}
THROUGHPUT_PRESERVATION=0.65

def load_one(root,needle):
    for p in root.rglob("*.json"):
        if needle not in p.name: continue
        try:
            d=json.load(open(p))
            if "basket_outcomes" in d:return d
        except: pass
    raise SystemExit(f"missing audit {needle} under {root}")

v64w={w:load_one(v64,f"-{w}.json") for w in "ABC"}
v66cw={w:load_one(v66c,f"-{w}.json") for w in "ABC"}
hw={w:load_one(legacy,f"-{w}.json") for w in ["H21","H22","H23"]}
dw={w:load_one(dev,f"-{w}.json") for w in "ABC"}

def pf(vals):
    gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
    return gp/gl if gl else (999 if gp else 0)
def pct(v,p):
    if not v:return 0
    y=sorted(v); q=(len(y)-1)*p; lo=int(q); hi=min(len(y)-1,lo+1)
    return y[lo]+(y[hi]-y[lo])*(q-lo)
def aggregate(ws,years):
    rows=[r for z in ws.values() for r in z.get("basket_outcomes",[])]
    vals=[r["net"] for r in rows]; rr=[r.get("r",0) for r in rows]; wins=[x for x in rr if x>0]; n=len(rows)
    top5=sum(sorted([max(0,x) for x in vals],reverse=True)[:5])
    fam=collections.defaultdict(float); route=collections.defaultdict(float)
    for r in rows:
        fam[r.get("pattern","UNKNOWN")]+=r["net"]; route[r.get("route","UNKNOWN")]+=r["net"]
    return {"baskets":n,"frequency":n/years,"unique_setups":len({r.get("setup","") for r in rows}),
      "net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,
      "max_dd_pct":max((z.get("max_dd_pct",0) for z in ws.values()),default=0),
      "all_windows_positive":all(z.get("net",0)>0 and z.get("pf",0)>1 and z.get("expectancy",0)>0 for z in ws.values()),
      "engineering_clean":all(z.get("engineering_clean",False) for z in ws.values()),
      "risk_clean":all(z.get("actual_basket_risk_violations",0)==0 and z.get("margin_risk_violations",0)==0 for z in ws.values()),
      "p95_winner_r":pct(wins,.95),"max_winner_r":max(wins) if wins else 0,"net_ex_top5":sum(vals)-top5,
      "family_net":dict(sorted(fam.items())),"route_net":dict(sorted(route.items())),"windows":ws}

def signature(ws):
    rows=[]
    for w in "ABC":
        for r in ws[w].get("basket_outcomes",[]):
            rows.append((w,r.get("setup",""),r.get("pattern",""),r.get("route",""),round(float(r.get("net",0)),2),round(float(r.get("r",0)),3)))
    return rows

control_equivalence=signature(v64w)==signature(v66cw)
base=aggregate(v64w,1.5); hist=aggregate(hw,3.0); prod=aggregate(dw,1.5)

prod["net_delta_vs_v64"]=prod["net"]-base["net"]
prod["pf_delta_vs_v64"]=prod["pf"]-base["pf"]
prod["frequency_delta_vs_v64"]=prod["frequency"]-base["frequency"]
prod["right_tail_preservation_ratio"]=prod["p95_winner_r"]/base["p95_winner_r"] if base["p95_winner_r"] else 0
prod["right_tail_gate"]=prod["right_tail_preservation_ratio"]>=0.80
prod["throughput_preservation_ratio"]=prod["frequency"]/base["frequency"] if base["frequency"] else 0
prod["throughput_gate"]=prod["throughput_preservation_ratio"]>=THROUGHPUT_PRESERVATION
prod["frequency_expansion_gate"]=prod["frequency_delta_vs_v64"]<=1e-9 or prod["net_delta_vs_v64"]>0
prod["known_failure_stress_repaired"]=hw["H23"]["net"]>0 and hw["H23"]["pf"]>1 and hw["H23"]["expectancy"]>0
prod["legacy_preservation_gate"]=all(hw[w]["net"]>0 and hw[w]["pf"]>1 and hw[w]["expectancy"]>0 for w in ["H21","H22"])
prod["dev_stability_gate"]=prod["all_windows_positive"] and prod["engineering_clean"] and prod["risk_clean"]
prod["concentration_gate"]=prod["net_ex_top5"]>0
prod["alpha_breakthrough_gate"]=(control_equivalence and prod["dev_stability_gate"] and prod["known_failure_stress_repaired"] and
    prod["legacy_preservation_gate"] and prod["net"]>base["net"] and prod["pf"]>=1.50 and prod["expectancy"]>10 and
    prod["max_dd_pct"]<=6 and prod["right_tail_gate"] and prod["throughput_gate"] and prod["frequency_expansion_gate"])
prod["historical_best_gate"]=(prod["net"]>HIST_BEST["net"] and prod["pf"]>HIST_BEST["pf"] and prod["expectancy"]>HIST_BEST["expectancy"] and
    prod["win_rate"]>=HIST_BEST["win_rate"] and prod["max_dd_pct"]<=HIST_BEST["max_dd_pct"])
prod["commercial_gate"]=(prod["baskets"]<=COMM["max_baskets"] and prod["frequency"]>=COMM["min_frequency"] and prod["net"]>=COMM["net"] and
    prod["pf"]>=COMM["pf"] and prod["expectancy"]>=COMM["expectancy"] and prod["win_rate"]>=COMM["win_rate"] and
    prod["max_dd_pct"]<=COMM["max_dd_pct"] and prod["dev_stability_gate"] and prod["concentration_gate"])

candidate="V66_PRODUCT" if prod["alpha_breakthrough_gate"] else ""
commercial_ready=bool(candidate and prod["commercial_gate"] and prod["historical_best_gate"])
report={"version":"HarmonyBot V66","architecture":"Harmonic Evidence Accumulator","v64_product_control":base,
 "v66_control_dynamic_equivalence":control_equivalence,"legacy_stress_2021_2023":hist,"dev_2024h2_2025h2":prod,
 "throughput_preservation_min_ratio":THROUGHPUT_PRESERVATION,"historical_best_reference":HIST_BEST,"commercial_minimum":COMM,
 "development_candidate":candidate,"commercial_ready_on_dev":commercial_ready,
 "status":"ALPHA_BREAKTHROUGH_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE",
 "next_stage":"VALIDATION_2026_Q1_Q2" if candidate else "STOP_DEV_HOLD","fresh_used":False}
(out/"V66_ALPHA_FRONTIER.json").write_text(json.dumps(report,indent=2))
(out/"candidate.txt").write_text(candidate)
(out/"commercial_ready.txt").write_text("true" if commercial_ready else "false")
print(json.dumps(report,indent=2))
