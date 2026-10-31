#!/usr/bin/env python3
import json,pathlib,os,statistics
rows=[]
for w in ("DEV-A","DEV-B","DEV-C"):
    p=pathlib.Path("all")/(w+".json")
    if p.exists():
        x=json.load(open(p))
        if x.get("status")=="OK": rows.append(x)
out={"version":"HarmonyBot V32.0","development_pass":False,"grid_no_edge":False,"windows":{x["window"]:x for x in rows}}
if len(rows)==3:
    total=sum(x["baskets"] for x in rows); gp=sum(x["gross_profit"] for x in rows); gl=sum(x["gross_loss"] for x in rows); net=sum(x["net"] for x in rows)
    pf=gp/gl if gl else (999.0 if gp else 0.0); exp=net/total if total else 0.0; freq=total/1.5
    sgp=sum(x["single_entry_equivalent"]["gross_profit"] for x in rows); sgl=sum(x["single_entry_equivalent"]["gross_loss"] for x in rows)
    sn=sum(x["single_entry_equivalent"]["count"] for x in rows); snet=sum(x["single_entry_equivalent"]["net"] for x in rows)
    spf=sgp/sgl if sgl else (999.0 if sgp else 0.0); sexp=snet/sn if sn else 0.0
    out.update({"total_baskets":total,"annualized_frequency":freq,"aggregate_pf":pf,"aggregate_net":net,"aggregate_expectancy":exp,
      "max_dd_pct":max(x["max_dd_pct"] for x in rows),"execution_errors":sum(x["execution_errors"] for x in rows),
      "grid_risk_violations":sum(x["grid_risk_violations"] for x in rows),"duplicate_grid_legs":sum(x["duplicate_grid_legs"] for x in rows),
      "orphan_pending_orders":sum(x["orphan_pending_orders"] for x in rows),"stop_widening_violations":sum(x["stop_widening_violations"] for x in rows),
      "single_entry_equivalent":{"count":sn,"pf":spf,"net":snet,"expectancy":sexp,"max_dd_pct":max(x["single_entry_equivalent"]["max_dd_pct"] for x in rows)},
      "average_entry_improvement_pips":statistics.mean([x["grid_attribution"]["average_entry_improvement_pips"] for x in rows]),
      "mean_mae_r":statistics.mean([x["mean_mae_r"] for x in rows]),
      "single_mean_mae_r":statistics.mean([x["single_entry_equivalent"]["mean_mae_r"] for x in rows])})
    hard=all(x["baskets"]>0 and x["pf"]>1 and x["expectancy"]>0 and x["net"]>0 for x in rows)
    hard=hard and pf>1 and exp>0 and net>0 and out["max_dd_pct"]<=10 and out["execution_errors"]==0 and freq>=50
    hard=hard and out["grid_risk_violations"]==0 and out["duplicate_grid_legs"]==0 and out["orphan_pending_orders"]==0 and out["stop_widening_violations"]==0
    out["development_pass"]=bool(hard)
    dd_worse=out["max_dd_pct"]>out["single_entry_equivalent"]["max_dd_pct"]
    pf_not_better=pf<=spf; exp_not_better=exp<=sexp
    mae_not_better=out["mean_mae_r"]>=out["single_mean_mae_r"]
    entry_not_better=out["average_entry_improvement_pips"]<=0
    out["grid_no_edge"]=bool(dd_worse and pf_not_better and exp_not_better and mae_not_better and entry_not_better)
runtime_ok=len(rows)==3 and all(x.get("runtime_started") for x in rows)
pipeline_total=sum(x.get("pipeline_detected",0) for x in rows)
if not runtime_ok or pipeline_total==0:
    out["development_pass"]=False; out["engineering_pipeline_failure"]=True; out["next_stage"]="ENGINEERING_PIPELINE_FAILURE"
else:
    out["engineering_pipeline_failure"]=False
    out["next_stage"]="DATA_GOVERNANCE_CHECK" if out["development_pass"] else ("FIBONACCI_GRID_NO_EDGE" if out["grid_no_edge"] else "STRATEGY_ARCHITECTURE_LIMITATION")
pathlib.Path("DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
with open(os.environ["GITHUB_OUTPUT"],"a") as f:
    f.write("development_pass="+("true" if out["development_pass"] else "false")+"\n")
