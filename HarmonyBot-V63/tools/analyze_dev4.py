#!/usr/bin/env python3
import json,pathlib,sys,math,collections
dev=pathlib.Path(sys.argv[1]); gold=json.load(open(sys.argv[2])); out=pathlib.Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
F=["V63_CONDITIONAL_EXECUTION","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER","V63_POSITIVE_COHORT_RECOVERY","V63_OCCUPANCY_GOVERNOR"]
H={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(v,w):
 x=list(dev.rglob(f"{v}-{w}.json"))
 if not x: raise SystemExit(f"missing {v}-{w}")
 return json.load(open(x[0]))
def pf(v):
 gp=sum(x for x in v if x>0);gl=abs(sum(x for x in v if x<0));return gp/gl if gl else (999 if gp else 0)
def pct(v,p):
 if not v:return 0
 y=sorted(v);q=(len(y)-1)*p;lo=int(q);hi=min(len(y)-1,lo+1);return y[lo]+(y[hi]-y[lo])*(q-lo)
def aggregate(v):
 ws={w:find(v,w) for w in "ABC"}; rows=[r for z in ws.values() for r in z.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; rr=[r.get("r",0) for r in rows]; wins=[x for x in rr if x>0]; n=len(rows)
 byfam=collections.defaultdict(float)
 for r in rows: byfam[r.get("pattern","UNKNOWN")]+=r["net"]
 top5=sum(sorted([max(0,x) for x in vals],reverse=True)[:5]); leave={}
 for fam in byfam:
  fv=[r["net"] for r in rows if r.get("pattern")!=fam];leave[fam]=sum(fv)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max(z["max_dd_pct"] for z in ws.values()),"all_windows_positive":all(z["net"]>0 and z["pf"]>1 and z["expectancy"]>0 for z in ws.values()),"engineering_clean":all(z["engineering_clean"] for z in ws.values()),"risk_clean":all(z.get("actual_basket_risk_violations",0)==0 and z.get("margin_risk_violations",0)==0 for z in ws.values()),"p95_winner_r":pct(wins,.95),"max_winner_r":max(wins) if wins else 0,"mean_winner_r":sum(wins)/len(wins) if wins else 0,"net_ex_top5":sum(vals)-top5,"leave_one_family_out_net":leave,"windows":ws}
A={v:aggregate(v) for v in F}
goldRows=[r for w in "ABC" for r in gold["windows"][w].get("basket_outcomes",[])]; gr=[r.get("r",0) for r in goldRows if r.get("r",0)>0]; goldp95=pct(gr,.95); goldmax=max(gr) if gr else 0
gmap={r["setup"]:r for r in goldRows}
for v,z in A.items():
 z["delta_net_vs_golden"]=z["net"]-gold["net"]; z["delta_frequency_vs_golden"]=z["frequency"]-gold["frequency"]; z["right_tail_preservation_ratio"]=z["p95_winner_r"]/goldp95 if goldp95 else 0; z["max_winner_preservation_ratio"]=z["max_winner_r"]/goldmax if goldmax else 0
 rows={r["setup"]:r for w in "ABC" for r in z["windows"][w].get("basket_outcomes",[])}; ks=set(rows)&set(gmap); ds=[rows[k].get("r",0)-gmap[k].get("r",0) for k in ks]
 z["matched_n"]=len(ds);z["matched_mean_delta_r"]=sum(ds)/len(ds) if ds else 0;z["matched_positive_share"]=sum(x>0 for x in ds)/len(ds) if ds else 0
 z["frequency_expansion_gate"]=z["frequency"]<=gold["frequency"]+1e-9 or z["net"]>gold["net"]
 z["alpha_preservation_gate"]=z["right_tail_preservation_ratio"]>=.80 and z["max_winner_preservation_ratio"]>=.80 and z["matched_mean_delta_r"]>0 and z["frequency_expansion_gate"] and z["risk_clean"] and z["engineering_clean"]
 z["golden_superiority_gate"]=z["net"]>gold["net"] and z["pf"]>gold["pf"] and z["expectancy"]>gold["expectancy"] and z["frequency"]>gold["frequency"] and z["all_windows_positive"]
 z["historical_best_gate"]=z["net"]>H["net"] and z["pf"]>H["pf"] and z["expectancy"]>H["expectancy"] and z["win_rate"]>=H["win_rate"] and z["max_dd_pct"]<=H["max_dd_pct"]
 z["commercial_gate"]=z["baskets"]<=COMM["max_baskets"] and z["frequency"]>=COMM["min_frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"]
 z["concentration_gate"]=z["net_ex_top5"]>0
eligible=[v for v,z in A.items() if z["alpha_preservation_gate"] and z["golden_superiority_gate"] and z["historical_best_gate"] and z["commercial_gate"] and z["concentration_gate"]]
winner=max(eligible,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"])) if eligible else None
rep={"version":"HarmonyBot V63","golden_v51":{k:gold[k] for k in ["baskets","frequency","net","pf","expectancy","win_rate","max_dd_pct","reference_sha256"]},"historical_best_reference":H,"commercial_minimum":COMM,"variants":A,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION_2026_Q1_Q2" if winner else "STOP_DEV_HOLD","fresh_used":False}
(out/"V63_PERFORMANCE_FRONTIER.json").write_text(json.dumps(rep,indent=2));(out/"candidate.txt").write_text(winner or "");print(json.dumps(rep,indent=2))