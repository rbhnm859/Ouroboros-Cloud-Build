#!/usr/bin/env python3
import glob,json,pathlib,statistics,os
cands=["R1","R2","R3"]; wins=["DEV-A","DEV-B","DEV-C"]; result={}; passed=[]
for c in cands:
    rows=[]
    for w in wins:
        ps=glob.glob(f"all/**/{c}-{w}.json",recursive=True)
        if ps:
            x=json.load(open(ps[0]))
            if x.get("status")=="OK": rows.append(x)
    r={"candidate":c,"windows":{x["window"]:x for x in rows},"development_pass":False}
    if len(rows)==3:
        total=sum(x["baskets"] for x in rows); gp=sum(x["gross_profit"] for x in rows); gl=sum(x["gross_loss"] for x in rows); net=sum(x["net"] for x in rows)
        aggpf=gp/gl if gl else (999.0 if gp else 0.0); freq=total/1.5; exp=net/total if total else 0.0
        pfs=[x["pf"] for x in rows]; exps=[x["expectancy"] for x in rows]; dds=[x["max_dd_pct"] for x in rows]
        r.update({"total_baskets":total,"annualized_frequency":freq,"aggregate_pf":aggpf,"aggregate_net":net,"aggregate_expectancy":exp,
                  "worst_window_pf":min(pfs),"worst_window_expectancy":min(exps),"median_window_pf":statistics.median(pfs),
                  "max_dd_pct":max(dds),"execution_errors":sum(x["execution_errors"] for x in rows),"tail_top3_max_pct":max(x["top3_loss_pct"] for x in rows)})
        r["development_pass"]=bool(
            all(x["baskets"]>0 and x["pf"]>1.0 and x["expectancy"]>0 and x["net"]>0 for x in rows)
            and net>0 and exp>0 and max(dds)<=10 and r["execution_errors"]==0 and freq>=50
        )
        if r["development_pass"]: passed.append(c)
    result[c]=r
passed.sort(key=lambda c:(result[c]["worst_window_pf"],result[c]["worst_window_expectancy"],result[c]["aggregate_expectancy"],-result[c]["max_dd_pct"],result[c]["annualized_frequency"]),reverse=True)
winner=passed[0] if passed else ""
out={"winner":winner,"passed":passed,"candidates":result,
     "selection_rule":"3/3 PF>1 + 3/3 expectancy/net>0 + aggregate positive + DD<=10% + zero errors + >=50/year; rank worst PF, worst expectancy, aggregate expectancy, DD, frequency",
     "next_stage":"VALIDATION" if winner else "STRATEGY_ARCHITECTURE_LIMITATION"}
pathlib.Path("DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2))
if not winner:
    best=max(result.values(),key=lambda r:(r.get("worst_window_pf",0),r.get("worst_window_expectancy",-1e99),r.get("aggregate_expectancy",-1e99),r.get("annualized_frequency",0)))
    pathlib.Path("STRATEGY_ARCHITECTURE_LIMITATION.md").write_text(
      "# STRATEGY ARCHITECTURE LIMITATION\n\nNo preregistered R1/R2/R3 architecture passed the hard Development Gate.\n\n"
      f"Best candidate: {best['candidate']}\nWorst-window PF: {best.get('worst_window_pf',0):.3f}\n"
      f"Worst-window expectancy: {best.get('worst_window_expectancy',0):.4f}\nAggregate PF: {best.get('aggregate_pf',0):.3f}\n"
      f"Aggregate expectancy: {best.get('aggregate_expectancy',0):.4f}\nFrequency/year: {best.get('annualized_frequency',0):.2f}\n"
      f"Max DD: {best.get('max_dd_pct',0):.2f}%\n\nStop rule enforced: no sequential rescue strategy version.\n")
print(json.dumps(out,indent=2))
with open(os.environ["GITHUB_OUTPUT"],"a") as f:
    f.write(f"winner={winner}\n"); f.write("has_winner="+("true" if winner else "false")+"\n")
