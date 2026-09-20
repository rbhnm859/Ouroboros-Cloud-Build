#!/usr/bin/env python3
import json,pathlib,re,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V39/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V39/final")
out.mkdir(parents=True,exist_ok=True)
fams=["BASELINE_CONTROL","REGIME_SELECTOR","ROUTE_SPECIALIZED","FULL_PORTFOLIO"]
def locate(name):
    xs=list(root.rglob(name))
    if not xs: raise SystemExit(f"missing {name}")
    return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def aggregate(f):
    xs=[read(f,w) for w in "ABC"]
    gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
    n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
    return {
      "baskets":n,"executable_baskets_per_year":n/1.5,
      "pf":gp/gl if gl else (999 if gp else 0),"net":net,"expectancy":net/n if n else 0,
      "win_rate":wins/n if n else 0,
      "positive_windows":sum(x["net"]>0 for x in xs),
      "all_windows_non_negative":all(x["net"]>=0 for x in xs),
      "worst_window_pf":min(x["pf"] for x in xs),
      "max_dd_pct":max(x["max_dd_pct"] for x in xs),
      "engineering_clean":all(x["engineering_clean"] and x["summary_present"] and x["broker_profile_present"] for x in xs),
      "portfolio_evaluated":sum(x.get("portfolio_evaluated",0) for x in xs),
      "portfolio_accepted":sum(x.get("portfolio_accepted",0) for x in xs),
      "portfolio_rejected":sum(x.get("portfolio_rejected",0) for x in xs),
      "route_specialization_rejected":sum(x.get("route_specialization_rejected",0) for x in xs),
      "stress_quarantine_rejected":sum(x.get("stress_quarantine_rejected",0) for x in xs),
      "risk_renormalizations":sum(x.get("risk_renormalizations",0) for x in xs),
      "risk_rejects":sum(x.get("risk_rejects",0) for x in xs),
      "shadow_targets":sum(x.get("shadow_targets",0) for x in xs),
      "shadow_stops":sum(x.get("shadow_stops",0) for x in xs),
      "shadow_unresolved":sum(x.get("shadow_unresolved",0) for x in xs),
      "windows":{w:read(f,w) for w in "ABC"}
    }
a={f:aggregate(f) for f in fams}
for f,v in a.items():
    v["frequency_multiple_vs_v351"]=v["executable_baskets_per_year"]/44.0 if v["executable_baskets_per_year"] else 0
    v["frequency_multiple_vs_v36_structured"]=v["executable_baskets_per_year"]/51.333333333333336 if v["executable_baskets_per_year"] else 0
    v["net_profit_gate"]=v["net"]>0 and v["all_windows_non_negative"]
    v["promotion_floor_pass"]=(v["engineering_clean"] and v["net_profit_gate"] and
       v["executable_baskets_per_year"]>=50 and v["pf"]>=1.10 and v["expectancy"]>0 and
       v["worst_window_pf"]>=0.80 and v["max_dd_pct"]<=10)
    v["major_breakthrough"]=(v["promotion_floor_pass"] and
       (v["executable_baskets_per_year"]>=100 or v["frequency_multiple_vs_v351"]>=2.0))
eligible=[(v["executable_baskets_per_year"],v["pf"],v["net"],f) for f,v in a.items() if v["promotion_floor_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V39","architecture":"REGIME_CONDITIONED_HARMONIC_PORTFOLIO",
 "evidence_scope":"DEV-A/B/C only; fresh validation untouched",
 "hard_requirement":"aggregate Net Profit > 0 AND each DEV window Net Profit >= 0",
 "families":a,"development_candidate":winner,
 "major_breakthrough":bool(winner and a[winner]["major_breakthrough"]),
 "status":"MAJOR_BREAKTHROUGH" if winner and a[winner]["major_breakthrough"] else ("DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE")}
(out/"V39_PORTFOLIO_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={"version":"HarmonyBot V39","development_candidate":winner,"status":frontier["status"],
 "major_breakthrough":frontier["major_breakthrough"],"net_profit_gate":"REQUIRED_AND_NON_NEGOTIABLE",
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "REASSESS_PATTERN_ROUTE_REGIME_ATTRIBUTION",
 "fresh_validation_used":False,"m1_strategy_dependency":False}
(out/"V39_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
funnel={"version":"HarmonyBot V39","scope":"DEV-A/B/C","families":{}}
for f in fams:
    z={"detected":0,"validated":0,"routed":0,"prz":0,"confirming":0,"armed":0,"basket_planned":0,"executed":0,"rejected":0,"expired":0,"invalidated":0}
    for w in "ABC":
        lp=locate(f"V39-{f}-{w}-B10000.log")
        t=lp.read_text(errors="ignore")
        matches=re.findall(r"\[V39-PIPELINE\].*?detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+).*?executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)",t)
        for m in matches:
            for k,val in zip(["detected","validated","routed","prz","confirming","armed","basket_planned","executed","expired","rejected","invalidated"],map(int,m)):
                z[k]+=val
    funnel["families"][f]=z
(out/"V39_SIGNAL_TRADE_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
print("CANDIDATE="+(winner or ""))
