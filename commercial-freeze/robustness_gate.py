#!/usr/bin/env python3
import argparse,glob,json,statistics,random,pathlib
ap=argparse.ArgumentParser(); ap.add_argument("--dir",required=True); ap.add_argument("--out",required=True)
a=ap.parse_args(); base=pathlib.Path(a.dir)
def load(prefix):
    out={}
    for p in glob.glob(str(base/(prefix+"*.json"))):
        x=json.load(open(p))
        if x.get("status")=="OK": out[x["window"]]=x
    return out
sens=load("SENS-"); costs=load("COST-"); wf=load("WF-")
sens_expected={"BASE","THRESH_M20","THRESH_M10","THRESH_M5","THRESH_P5","THRESH_P10","THRESH_P20"}
cost_expected={"SPREAD_150","COMMISSION_150","SLIPPAGE_150","COMBINED"}
sens_ok=bool(set(sens)==sens_expected and all(x["max_dd_pct"]<=10 and x["execution_errors"]==0 and x["pf"]>=0.85 for x in sens.values())
             and statistics.median([x["pf"] for x in sens.values()])>1.0 and sens["BASE"]["pf"]>1 and sens["BASE"]["expectancy"]>0)
cost_ok=bool(set(costs)==cost_expected and all(x["max_dd_pct"]<=10 and x["execution_errors"]==0 and x["pf"]>=0.85 for x in costs.values())
             and statistics.median([x["pf"] for x in costs.values()])>0.95)
wf_rows=list(wf.values())
wf_ok=bool(len(wf_rows)==3 and sum(1 for x in wf_rows if x["pf"]>1 and x["expectancy"]>0)>=2
           and sum(x["net"] for x in wf_rows)>0 and max(x["max_dd_pct"] for x in wf_rows)<=10 and sum(x["execution_errors"] for x in wf_rows)==0)

nets=sens.get("BASE",{}).get("basket_nets",[])
random.seed(2956); dd95=999.; ruin=1.; p5=-1e99
if nets:
    dds=[]; totals=[]; ruined=0
    for _ in range(5000):
        eq=10000.; peak=eq; mdd=0.; dead=False
        for v in random.choices(nets,k=len(nets)):
            eq+=v; peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100 if peak else 100)
            if eq<=0 and not dead: dead=True; ruined+=1
        dds.append(mdd); totals.append(eq-10000.)
    dds.sort(); totals.sort(); dd95=dds[int(.95*(len(dds)-1))]; p5=totals[int(.05*(len(totals)-1))]; ruin=ruined/5000
mc_ok=bool(dd95<=15 and ruin<=0.01)
out={"robustness_pass":bool(sens_ok and cost_ok and wf_ok and mc_ok),"sensitivity_pass":sens_ok,"cost_stress_pass":cost_ok,
     "walk_forward_pass":wf_ok,"monte_carlo_pass":mc_ok,"mc_95pct_max_dd":dd95,"mc_5pct_total_net":p5,"mc_risk_of_ruin":ruin,
     "sensitivity":sens,"cost_stress":costs,"walk_forward":wf}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
