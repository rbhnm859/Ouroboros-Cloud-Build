#!/usr/bin/env python3
import glob,json,pathlib,statistics,os
profiles=["P1","P2","P3"]; wins=["DEV-A","DEV-B","DEV-C"]; result={}; passed=[]
for p in profiles:
    rows=[]
    for w in wins:
        ps=glob.glob(f"all/**/{p}-{w}.json",recursive=True)
        if ps:
            x=json.load(open(ps[0]))
            if x.get("status")=="OK": rows.append(x)
    r={"profile":p,"windows":{x["window"]:x for x in rows},"development_pass":False}
    if len(rows)==3:
        total=sum(x["baskets"] for x in rows); gp=sum(x["gross_profit"] for x in rows); gl=sum(x["gross_loss"] for x in rows); net=sum(x["net"] for x in rows)
        aggpf=gp/gl if gl else (999.0 if gp else 0.0); freq=total/1.5; exp=net/total if total else 0.0
        pfs=[x["pf"] for x in rows]; dds=[x["max_dd_pct"] for x in rows]
        r.update({"total_baskets":total,"annualized_frequency":freq,"aggregate_pf":aggpf,"aggregate_net":net,"aggregate_expectancy":exp,
                  "worst_window_pf":min(pfs),"median_window_pf":statistics.median(pfs),"max_dd_pct":max(dds),
                  "execution_errors":sum(x["execution_errors"] for x in rows),"tail_top3_max_pct":max(x["top3_loss_pct"] for x in rows)})
        r["development_pass"]=bool(all(x["baskets"]>0 and x["pf"]>1 and x["expectancy"]>0 and x["net"]>0 for x in rows)
            and net>0 and exp>0 and max(dds)<=10 and r["execution_errors"]==0 and freq>=50)
        if r["development_pass"]: passed.append(p)
    result[p]=r
passed.sort(key=lambda p:(result[p]["worst_window_pf"],result[p]["aggregate_expectancy"],-result[p]["max_dd_pct"],result[p]["annualized_frequency"]),reverse=True)
winner=passed[0] if passed else ""
out={"winner":winner,"passed":passed,"profiles":result,
     "selection_rule":"3/3 PF>1, expectancy/net>0, aggregate positive, DD<=10%, zero errors, >=50 baskets/year; rank worst-window PF then expectancy then DD then frequency",
     "next_stage":"VALIDATION" if winner else "STRATEGY_ARCHITECTURE_LIMITATION"}
pathlib.Path("FINAL_DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2))
if not winner:
    best=max(result.values(),key=lambda r:(r.get("worst_window_pf",0),r.get("aggregate_expectancy",-1e99),r.get("annualized_frequency",0)))
    pathlib.Path("FINAL_STRATEGY_ARCHITECTURE_LIMITATION.md").write_text(
      "# FINAL STRATEGY ARCHITECTURE LIMITATION\n\nNo preregistered final profile passed the hard Development gate.\n\n"
      f"Best profile: {best['profile']}\nWorst-window PF: {best.get('worst_window_pf',0):.3f}\n"
      f"Aggregate PF: {best.get('aggregate_pf',0):.3f}\nAggregate expectancy: {best.get('aggregate_expectancy',0):.4f}\n"
      f"Annualized frequency: {best.get('annualized_frequency',0):.2f}\nMax DD: {best.get('max_dd_pct',0):.2f}%\n")
print(json.dumps(out,indent=2))
with open(os.environ["GITHUB_OUTPUT"],"a") as f:
    f.write(f"winner={winner}\n"); f.write("has_winner="+("true" if winner else "false")+"\n")
