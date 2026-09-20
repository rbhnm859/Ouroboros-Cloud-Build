#!/usr/bin/env python3
import json,pathlib,statistics,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V40/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V40/final")
out.mkdir(parents=True,exist_ok=True)
fams=["LEGACY_CONTROL","RANK_ONLY","RANK_FOLLOWTHROUGH","FULL_V40"]
def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit(f"missing {name}")
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def agg(f):
 xs=[read(f,w) for w in "ABC"]
 gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
 risk_clean=all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs)
 v={"baskets":n,"executable_baskets_per_year":n/1.5,"pf":gp/gl if gl else (999 if gp else 0),
    "net":net,"expectancy":net/n if n else 0,"win_rate":wins/n if n else 0,
    "positive_windows":sum(x["net"]>0 for x in xs),"all_windows_non_negative":all(x["net"]>=0 for x in xs),
    "all_windows_have_trades":all(x["baskets"]>0 for x in xs),"worst_window_pf":min(x["pf"] for x in xs),
    "max_dd_pct":max(x["max_dd_pct"] for x in xs),
    "engineering_clean":all(x["engineering_clean"] for x in xs),"risk_clean":risk_clean,
    "rank_first_released":sum(x.get("rank_first_released",0) for x in xs),
    "follow_through_observed":sum(x.get("follow_through_observed",0) for x in xs),
    "thesis_failure_exits":sum(x.get("thesis_failure_exits",0) for x in xs),
    "attribution_observed":sum(x.get("attribution_observed",0) for x in xs),
    "shadow_targets":sum(x.get("shadow_targets",0) for x in xs),
    "shadow_stops":sum(x.get("shadow_stops",0) for x in xs),
    "shadow_unresolved":sum(x.get("shadow_unresolved",0) for x in xs),
    "windows":{w:read(f,w) for w in "ABC"}}
 v["net_profit_gate"]=v["net"]>0 and v["all_windows_non_negative"]
 v["promotion_floor_pass"]=(v["engineering_clean"] and v["risk_clean"] and v["all_windows_have_trades"] and
   v["net_profit_gate"] and v["pf"]>=1.15 and v["expectancy"]>0 and v["max_dd_pct"]<=10 and
   v["executable_baskets_per_year"]>=50)
 return v
A={f:agg(f) for f in fams}
eligible=[(v["executable_baskets_per_year"],v["pf"],v["net"],f) for f,v in A.items() if v["promotion_floor_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None

# Attribution matrix from executed outcomes, kept DEV-only.
rows=[]
for f in fams:
 for w in "ABC":
  for x in read(f,w).get("attribution_outcomes",[]):
   y=dict(x); y["family"]=f; y["window"]=w; rows.append(y)

def bucket_atr(x):
 a=x.get("atr_ratio",0)
 return "LOW_VOL" if a<.75 else ("HIGH_VOL" if a>1.35 else "NORMAL_VOL")
def bucket_eff(x):
 e=x.get("efficiency",0)
 return "LOW_EFF" if e<.16 else ("HIGH_EFF" if e>=.28 else "MID_EFF")
groups={}
for x in rows:
 key=(x["family"],x["pattern"],x["route"],bucket_atr(x),bucket_eff(x))
 groups.setdefault(key,[]).append(x)
matrix=[]
for k,xs in groups.items():
 nets=[x["net"] for x in xs]; gp=sum(z for z in nets if z>0); gl=abs(sum(z for z in nets if z<0))
 matrix.append({"family":k[0],"pattern":k[1],"route":k[2],"atr_bucket":k[3],"efficiency_bucket":k[4],
  "trades":len(xs),"net":sum(nets),"expectancy":sum(nets)/len(xs),"win_rate":sum(z>0 for z in nets)/len(xs),
  "pf":gp/gl if gl else (999 if gp else 0),
  "mean_mfe_r":statistics.mean(x["mfe_r"] for x in xs),"mean_mae_r":statistics.mean(x["mae_r"] for x in xs),
  "mean_follow":statistics.mean(x["follow"] for x in xs),"mean_attribution":statistics.mean(x["attribution"] for x in xs)})
matrix.sort(key=lambda x:(x["family"],-x["trades"],-x["expectancy"]))
(out/"V40_ATTRIBUTION_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V40","scope":"DEV-A/B/C only","rows":matrix},indent=2))

frontier={"version":"HarmonyBot V40","architecture":"ATTRIBUTION_RANK_FIRST_FOLLOW_THROUGH",
 "evidence_scope":"DEV-A/B/C only; fresh validation untouched",
 "external_control":{"V36_STRUCTURED_RECALL":{"executable_baskets_per_year":51.333333333333336,"pf":1.2124297856312334,
   "net":648.58,"expectancy":8.423116883116883,"max_dd_pct":8.768267223382058}},
 "hard_requirement":"A/B/C Net>=0; aggregate Net>0; PF>=1.15; Expectancy>0; DD<=10%; >=50 executable baskets/year; engineering+risk clean",
 "families":A,"development_candidate":winner,
 "status":"DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE"}
(out/"V40_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={"version":"HarmonyBot V40","development_candidate":winner,"status":frontier["status"],
 "fresh_validation_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "ATTRIBUTION_DIAGNOSIS",
 "net_profit_gate":"REQUIRED_AND_NON_NEGOTIABLE"}
(out/"V40_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
print("CANDIDATE="+(winner or ""))
