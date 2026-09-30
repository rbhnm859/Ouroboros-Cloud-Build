#!/usr/bin/env python3
import collections,json,math,pathlib,statistics,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=("Y2021","Y2022","Y2023"); Z=1.645; MIN_N=39

def merge(items):
    z={"n":0,"sum_r":0.0,"sum_sq_r":0.0,"gross_profit_r":0.0,"gross_loss_r":0.0,"wins":0}
    for x in items:
        z["n"]+=int(x.get("n",0)); z["sum_r"]+=float(x.get("sum_r",0)); z["sum_sq_r"]+=float(x.get("sum_sq_r",0))
        z["gross_profit_r"]+=float(x.get("gross_profit_r",0)); z["gross_loss_r"]+=float(x.get("gross_loss_r",0)); z["wins"]+=int(x.get("wins",0))
    return z

def stats(z):
    n=int(z["n"])
    if n<=0: return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0}
    m=z["sum_r"]/n
    lcb=m-Z*math.sqrt(max(0.0,(z["sum_sq_r"]-n*m*m)/(n-1)))/math.sqrt(n) if n>1 else -999.0
    gp=z["gross_profit_r"]; gl=z["gross_loss_r"]
    return {"n":n,"mean_r":m,"pf_r":gp/gl if gl>0 else (999.0 if gp>0 else 0.0),
            "lcb_r":lcb,"win_rate":z["wins"]/n}

folds={}; family_total=collections.defaultdict(int); lane_total=collections.defaultdict(int)
for w in W:
    xs=list(root.rglob(f"R_V72_FAMILY_NATIVE_CAUSAL-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate family-native shadow {w}: {len(xs)}")
    d=json.load(open(xs[0]))
    census=[x for x in d.get("payoff_census",[]) if str(x.get("lane","")).startswith("FAMILY_NATIVE_") and x.get("lane")!="FAMILY_NATIVE_SHADOW_ONLY"]
    if not census: raise SystemExit(f"missing exact family-native payoff census {w}")
    total=stats(merge(census)); lane_stats={}; lane_guard=True
    for lane in sorted({x["lane"] for x in census}):
        st=stats(merge([x for x in census if x["lane"]==lane])); lane_stats[lane]=st; lane_total[lane]+=st["n"]
        if st["n"]>=20 and not (st["mean_r"]>0 and st["pf_r"]>1.0): lane_guard=False
    family_stats={}
    for fam in sorted({x["family"] for x in census}):
        st=stats(merge([x for x in census if x["family"]==fam])); family_stats[fam]=st; family_total[fam]+=st["n"]
    passed=total["n"]>=MIN_N and total["mean_r"]>0 and total["pf_r"]>1.0 and total["lcb_r"]>0 and lane_guard
    folds[w]={"selected_n":total["n"],"frequency_per_year":total["n"],"mean_r":total["mean_r"],
              "pf_r":total["pf_r"],"lcb_r":total["lcb_r"],"win_rate":total["win_rate"],
              "lane_stats":lane_stats,"family_stats":family_stats,"lane_guard":lane_guard,"pass":passed}

gate=all(folds[w]["pass"] for w in W)
manifest={"architecture":"V72_FAMILY_NATIVE_COMPLETED_BAR_CAUSAL_RESOLUTION",
 "stage":"BURNED_CALIBRATION_SHADOW_ONLY","selection_model":"NONE","tuning_model":"NONE",
 "entry_semantics":"FAMILY_NATIVE_COMPLETED_BAR_PROOF_CLOSE",
 "failure_semantics":"STRUCTURAL_BREAK_THEN_LATER_BOUNDARY_RETEST_THEN_CONTINUATION_CLOSE",
 "target_semantics":"FAMILY_CANONICAL_T1_T2_MIN_NET_RR_2; FAILURE_FIXED_NET_2R",
 "grid":"OFF","risk_pct":1.0,"min_selected_per_year":MIN_N,"lcb_z":Z,
 "folds":folds,"family_selected_counts":dict(sorted(family_total.items())),
 "lane_selected_counts":dict(sorted(lane_total.items())),"family_native_gate":gate,
 "gate_semantics":"DETERMINISTIC_3_YEAR_FAMILY_NATIVE_CAUSAL_GATE__NO_MODEL_FIT_NO_THRESHOLD_TUNING",
 "capital_execution_used":False,"validation_used":False,"fresh_used":False}
(out/"FAMILY_NATIVE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
