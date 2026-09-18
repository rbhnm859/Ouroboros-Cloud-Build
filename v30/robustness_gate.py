#!/usr/bin/env python3
import argparse,glob,json,statistics,random,pathlib
ap=argparse.ArgumentParser(); ap.add_argument("--dir",required=True); ap.add_argument("--out",required=True)
a=ap.parse_args(); root=pathlib.Path(a.dir)
def load(prefix):
    d={}
    for p in glob.glob(str(root/(prefix+"*.json"))):
        x=json.load(open(p))
        if x.get("status")=="OK": d[x["window"]]=x
    return d
wf=load("WF-"); sens=load("SENS-"); cost=load("COST-")
wf_ok=bool(len(wf)==3 and sum(x["net"] for x in wf.values())>0 and max(x["max_dd_pct"] for x in wf.values())<=10
           and sum(1 for x in wf.values() if x["pf"]>1 and x["expectancy"]>0)>=2 and sum(x["execution_errors"] for x in wf.values())==0)
sens_expected={"BASE","M20","M10","M5","P5","P10","P20"}
sens_ok=bool(set(sens)==sens_expected and all(x["pf"]>=0.85 and x["max_dd_pct"]<=10 and x["execution_errors"]==0 for x in sens.values())
             and statistics.median(x["pf"] for x in sens.values())>1 and sens["BASE"]["pf"]>1 and sens["BASE"]["expectancy"]>0)
cost_expected={"SPREAD150","COMMISSION150","SLIPPAGE150","COMBINED"}
cost_ok=bool(set(cost)==cost_expected and all(x["pf"]>=0.85 and x["max_dd_pct"]<=10 and x["execution_errors"]==0 for x in cost.values())
             and statistics.median(x["pf"] for x in cost.values())>=0.95)

nets=sens.get("BASE",{}).get("basket_nets",[]); random.seed(3000); dd95=999.; p5=-1e99; ruin=1.
if nets:
    dds=[]; totals=[]; ruins=0
    for _ in range(5000):
        eq=10000.; peak=eq; mdd=0.; dead=False
        for v in random.choices(nets,k=len(nets)):
            eq+=v; peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100 if peak else 100)
            if eq<=0 and not dead: dead=True; ruins+=1
        dds.append(mdd); totals.append(eq-10000.)
    dds.sort(); totals.sort(); dd95=dds[int(.95*(len(dds)-1))]; p5=totals[int(.05*(len(totals)-1))]; ruin=ruins/5000
mc_ok=bool(dd95<=15 and ruin<=0.01)
out={"robustness_pass":bool(wf_ok and sens_ok and cost_ok and mc_ok),"walk_forward_pass":wf_ok,"sensitivity_pass":sens_ok,"cost_stress_pass":cost_ok,
     "monte_carlo_pass":mc_ok,"mc_95pct_max_dd":dd95,"mc_5pct_total_net":p5,"mc_risk_of_ruin":ruin,
     "walk_forward":wf,"sensitivity":sens,"cost_stress":cost}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
