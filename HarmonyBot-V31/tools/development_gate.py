#!/usr/bin/env python3
import json,pathlib,os
rows=[]
for w in ("DEV-A","DEV-B","DEV-C"):
    p=pathlib.Path("all")/(w+".json")
    if p.exists():
        x=json.load(open(p))
        if x.get("status")=="OK": rows.append(x)
out={"version":"HarmonyBot V31.0","development_pass":False,"windows":{x["window"]:x for x in rows}}
if len(rows)==3:
    total=sum(x["baskets"] for x in rows); gp=sum(x["gross_profit"] for x in rows); gl=sum(x["gross_loss"] for x in rows); net=sum(x["net"] for x in rows)
    pf=gp/gl if gl else (999.0 if gp else 0.0); exp=net/total if total else 0.0; freq=total/1.5
    out.update({"total_baskets":total,"annualized_frequency":freq,"aggregate_pf":pf,"aggregate_net":net,"aggregate_expectancy":exp,
      "worst_window_pf":min(x["pf"] for x in rows),"worst_window_expectancy":min(x["expectancy"] for x in rows),
      "max_dd_pct":max(x["max_dd_pct"] for x in rows),"execution_errors":sum(x["execution_errors"] for x in rows)})
    out["development_pass"]=bool(all(x["baskets"]>0 and x["pf"]>1 and x["expectancy"]>0 and x["net"]>0 for x in rows)
      and pf>1 and exp>0 and net>0 and out["max_dd_pct"]<=10 and out["execution_errors"]==0 and freq>=50)
runtime_ok=bool(len(rows)==3 and all(x.get("runtime_started") for x in rows))
pipeline_total=sum(x.get("pipeline_detected",0) for x in rows)
if not runtime_ok or pipeline_total==0:
    out["development_pass"]=False
    out["engineering_pipeline_failure"]=True
    out["next_stage"]="ENGINEERING_PIPELINE_FAILURE"
else:
    out["engineering_pipeline_failure"]=False
    out["next_stage"]="DATA_GOVERNANCE_CHECK" if out["development_pass"] else "STRATEGY_ARCHITECTURE_LIMITATION"
pathlib.Path("DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
with open(os.environ["GITHUB_OUTPUT"],"a") as f:
    f.write("development_pass="+("true" if out["development_pass"] else "false")+"\n")
