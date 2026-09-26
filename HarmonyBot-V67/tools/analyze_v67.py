#!/usr/bin/env python3
import argparse,json,pathlib,collections
ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
root=pathlib.Path(a.root); out=pathlib.Path(a.out)
rows=[]
for p in root.rglob("*.json"):
 try:d=json.load(open(p))
 except:continue
 if isinstance(d,dict) and d.get("version")=="HarmonyBot V67" and "basket_outcomes" in d: rows.append(d)
by={(x["mode"],x["window"]):x for x in rows}
wins=["CAL_A","CAL_B","CAL_C","DEV_A","DEV_B","DEV_C"]
missing=[f"{m}:{w}" for m in ["V67_V52_CONTROL","V67_PRODUCT"] for w in wins if (m,w) not in by]
if missing: raise SystemExit("missing evidence: "+",".join(missing))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0)); return gp/gl if gl else (999 if gp else 0)
def agg(mode,ws,years):
 xs=[by[(mode,w)] for w in ws]; b=[z for x in xs for z in x["basket_outcomes"]]; v=[z["net"] for z in b]
 fam=collections.defaultdict(list)
 for z in b:fam[z["pattern"]].append(z["net"])
 f={p:{"trades":len(q),"net":sum(q),"pf":pf(q),"expectancy":sum(q)/len(q),"win_rate":sum(x>0 for x in q)/len(q)} for p,q in fam.items()}
 return {"baskets":len(b),"frequency":len(b)/years,"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_positive":all(x["net"]>0 for x in xs),"clean":all(x["engineering_clean"] and x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),"family":f}
CC=agg("V67_V52_CONTROL",["CAL_A","CAL_B","CAL_C"],1.5)
PC=agg("V67_PRODUCT",["CAL_A","CAL_B","CAL_C"],1.5)
CD=agg("V67_V52_CONTROL",["DEV_A","DEV_B","DEV_C"],1.5)
PD=agg("V67_PRODUCT",["DEV_A","DEV_B","DEV_C"],1.5)
# Immutable V52 FULL_V52_COMMERCIAL calibration controls from formal run 35531304357.
expected={"CAL_A":{"baskets":25,"net":-455.94},"CAL_B":{"baskets":23,"net":-406.23},"CAL_C":{"baskets":69,"net":430.51}}
control_repro=all(by[("V67_V52_CONTROL",w)]["baskets"]==expected[w]["baskets"] and abs(by[("V67_V52_CONTROL",w)]["net"]-expected[w]["net"])<=.25 for w in expected)
fam=PD["family"]; total=max(1,PD["baskets"])
positive_families=[p for p,z in fam.items() if p!="AB=CD" and z["trades"]>=3 and z["net"]>0 and z["expectancy"]>0]
max_share=max([z["trades"]/total for p,z in fam.items() if p!="AB=CD"] or [0])
abcd_share=fam.get("AB=CD",{}).get("trades",0)/total
diversity=(len(positive_families)>=3 and max_share<=.55 and abcd_share<=.25)
commercial=(PD["baskets"]<=90 and PD["frequency"]>=60 and PD["net"]>=1800 and PD["pf"]>=2 and PD["expectancy"]>=20 and PD["win_rate"]>=.50 and PD["max_dd_pct"]<=6 and PD["all_positive"] and PD["clean"])
superior=(PD["net"]>2101.66 and PD["pf"]>2.1096878432 and PD["expectancy"]>36.2355 and PD["win_rate"]>=.534483 and PD["max_dd_pct"]<=4.49784)
throughput=(PD["frequency"]>=60 and PD["net"]>CD["net"])
candidate=bool(control_repro and commercial and superior and throughput and diversity)
o={"version":"HarmonyBot V67","control_calibration":CC,"product_calibration":PC,"control_dev":CD,"product_dev":PD,"control_reproduction":control_repro,"positive_non_abcd_families":positive_families,"family_diversity_gate":diversity,"abcd_trade_share":abcd_share,"max_non_abcd_family_share":max_share,"commercial_gate":commercial,"v51_superiority_gate":superior,"throughput_gate":throughput,"candidate":candidate,"status":"VALIDATION_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE","fresh_used":False}
out.write_text(json.dumps(o,indent=2)); print(json.dumps(o,indent=2))
