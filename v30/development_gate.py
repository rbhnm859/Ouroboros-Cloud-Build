#!/usr/bin/env python3
import glob,json,pathlib,os,statistics
rows=[]
for w in ("DEV-A","DEV-B","DEV-C"):
    p=pathlib.Path(f"all/V30-{w}.json")
    if p.exists():
        x=json.load(open(p))
        if x.get("status")=="OK": rows.append(x)
out={"version":"HarmonyBot V30.0 Regime-Routed Harmonic Portfolio Engine","development_pass":False,"windows":{x["window"]:x for x in rows}}
if len(rows)==3:
    total=sum(x["baskets"] for x in rows); gp=sum(x["gross_profit"] for x in rows); gl=sum(x["gross_loss"] for x in rows); net=sum(x["net"] for x in rows)
    pf=gp/gl if gl else (999.0 if gp else 0.0); exp=net/total if total else 0.0; freq=total/1.5
    out.update({"total_baskets":total,"annualized_frequency":freq,"aggregate_pf":pf,"aggregate_net":net,"aggregate_expectancy":exp,
                "worst_window_pf":min(x["pf"] for x in rows),"worst_window_expectancy":min(x["expectancy"] for x in rows),
                "max_dd_pct":max(x["max_dd_pct"] for x in rows),"execution_errors":sum(x["execution_errors"] for x in rows),
                "direction_totals":{"buy":sum(x["direction"]["buy"]["count"] for x in rows),"sell":sum(x["direction"]["sell"]["count"] for x in rows)}})
    out["development_pass"]=bool(all(x["baskets"]>0 and x["pf"]>1 and x["expectancy"]>0 and x["net"]>0 for x in rows)
                                 and pf>1 and net>0 and exp>0 and out["max_dd_pct"]<=10 and out["execution_errors"]==0 and freq>=50)
out["next_stage"]="VALIDATION" if out["development_pass"] else "HOLD_ARCHITECTURE_LIMITATION"
pathlib.Path("V30_DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2))
if not out["development_pass"]:
    pathlib.Path("V30_ARCHITECTURE_LIMITATION.md").write_text(
      "# HarmonyBot V30.0 Architecture Limitation\n\nV30.0 did not pass all three Development windows. "
      "Per one-pass rule, do not retune V30 against DEV-A/B/C.\n\n"
      f"Aggregate PF: {out.get('aggregate_pf',0):.3f}\nWorst PF: {out.get('worst_window_pf',0):.3f}\n"
      f"Aggregate expectancy: {out.get('aggregate_expectancy',0):.4f}\nFrequency/year: {out.get('annualized_frequency',0):.2f}\n")
print(json.dumps(out,indent=2))
with open(os.environ["GITHUB_OUTPUT"],"a") as f:
    f.write("has_winner="+("true" if out["development_pass"] else "false")+"\n")
