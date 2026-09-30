#!/usr/bin/env python3
import collections,json,math,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=("Y2021","Y2022","Y2023"); Z=1.645; MIN_N=60; MIN_PF=1.20

def merge(items):
 z={"n":0,"sum_r":0.0,"sum_sq_r":0.0,"gross_profit_r":0.0,"gross_loss_r":0.0,"wins":0}
 for x in items:
  z["n"]+=int(x.get("n",0)); z["sum_r"]+=float(x.get("sum_r",0)); z["sum_sq_r"]+=float(x.get("sum_sq_r",0))
  z["gross_profit_r"]+=float(x.get("gross_profit_r",0)); z["gross_loss_r"]+=float(x.get("gross_loss_r",0)); z["wins"]+=int(x.get("wins",0))
 return z
def stats(z):
 n=int(z["n"])
 if n<=0:return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0}
 m=z["sum_r"]/n
 var=max(0.0,(z["sum_sq_r"]-n*m*m)/(n-1)) if n>1 else 0.0
 lcb=m-Z*math.sqrt(var)/math.sqrt(n) if n>1 else -999.0
 gp=z["gross_profit_r"]; gl=z["gross_loss_r"]
 return {"n":n,"mean_r":m,"pf_r":gp/gl if gl>0 else (999.0 if gp>0 else 0.0),"lcb_r":lcb,"win_rate":z["wins"]/n}

folds={}; family_total=collections.defaultdict(int); lane_total=collections.defaultdict(int); mode_total=collections.defaultdict(int); runtime={}
for w in W:
 xs=list(root.rglob(f"R_V72_CRAE_CAUSAL-{w}.json"))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate CRAE {w}: {len(xs)}")
 d=json.load(open(xs[0])); runtime[w]=d.get("crae_summary",{})
 if not runtime[w].get("counterfactual_core_independent",False): raise SystemExit(f"CRAE ledger not core-independent {w}")
 census=[x for x in d.get("crae_census",[]) if str(x.get("lane","")).startswith("CRAE_") and x.get("lane")!="CRAE_ABCD_STANDALONE_SHADOW" and x.get("family")!="ABCD"]
 if not census: raise SystemExit(f"missing CRAE census {w}")
 total=stats(merge(census))
 lanes={}; lane_guard=True
 for lane in sorted({x["lane"] for x in census}):
  st=stats(merge([x for x in census if x["lane"]==lane])); lanes[lane]=st; lane_total[lane]+=st["n"]
  if st["n"]>=20 and not(st["mean_r"]>0 and st["pf_r"]>1 and st["lcb_r"]>0): lane_guard=False
 modes={}; mode_guard=True
 for mode in sorted({x.get("mode","UNKNOWN") for x in census}):
  st=stats(merge([x for x in census if x.get("mode","UNKNOWN")==mode])); modes[mode]=st; mode_total[mode]+=st["n"]
  if st["n"]>=20 and not(st["mean_r"]>0 and st["pf_r"]>1 and st["lcb_r"]>0): mode_guard=False
 fams={}
 for fam in sorted({x["family"] for x in census}):
  st=stats(merge([x for x in census if x["family"]==fam])); fams[fam]=st; family_total[fam]+=st["n"]
 passed=total["n"]>=MIN_N and total["mean_r"]>0 and total["pf_r"]>=MIN_PF and total["lcb_r"]>0 and lane_guard and mode_guard
 folds[w]={"selected_n":total["n"],"frequency_per_year":total["n"],"mean_r":total["mean_r"],"pf_r":total["pf_r"],"lcb_r":total["lcb_r"],"win_rate":total["win_rate"],"lane_stats":lanes,"mode_stats":modes,"family_stats":fams,"lane_guard":lane_guard,"mode_guard":mode_guard,"pass":passed}
gate=all(folds[w]["pass"] for w in W)
m={"architecture":"V72_REGIME_CONDITIONED_CAUSAL_RESOLUTION_ENGINE","stage":"V72_CANDIDATE_BURNED_CALIBRATION_SHADOW",
"truth_ledger":"COUNTERFACTUAL_ALPHA_INDEPENDENT_OF_V51_CORE_OVERLAP",
"regime_semantics":"CONTEMPORANEOUS_H4_H1_M15_OBSERVABLES_ONLY_NO_YEAR_CLASSIFIER_NO_PNL_FIT",
"resolution_semantics":"TREND_RELOAD_OR_EXHAUSTION_REVERSAL_OR_FAILURE_CONTINUATION_ELSE_NO_TRADE",
"proof_semantics":"STRICT_COMPLETED_M1_PRZ_LIQUIDITY_RECLAIM_BOS_LATER_STRUCTURE_RETEST",
"grid":"OFF","risk_pct":1.0,"min_selected_per_year":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,
"folds":folds,"family_selected_counts":dict(sorted(family_total.items())),"lane_selected_counts":dict(sorted(lane_total.items())),"mode_selected_counts":dict(sorted(mode_total.items())),
"runtime_summary":runtime,"crae_gate":gate,
"gate_semantics":"3YEAR_CRAE_CAUSAL_GATE__NO_YEAR_CLASSIFIER_NO_PNL_SELECTOR_NO_THRESHOLD_TUNING_NO_CORE_OVERLAP_FILTER",
"capital_execution_used":False,"validation_used":False,"fresh_used":False}
(out/"CRAE_MANIFEST.json").write_text(json.dumps(m,indent=2)); print(json.dumps(m,indent=2))
