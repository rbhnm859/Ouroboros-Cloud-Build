#!/usr/bin/env python3
import json,math,pathlib,statistics,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=("Y2021","Y2022","Y2023"); Z=1.645; MIN_N=39

def merge(items):
    z={"n":0,"sum_r":0.0,"sum_sq_r":0.0,"gross_profit_r":0.0,"gross_loss_r":0.0,"wins":0}
    for x in items:
        for k in z: z[k]+=float(x.get(k,0)) if k!="n" and k!="wins" else int(x.get(k,0))
    return z

def stats(z):
    n=int(z["n"])
    if n<=0:return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0}
    m=z["sum_r"]/n
    lcb=m-Z*math.sqrt(max(0.0,(z["sum_sq_r"]-n*m*m)/(n-1)))/math.sqrt(n) if n>1 else -999.0
    gp=z["gross_profit_r"]; gl=z["gross_loss_r"]
    return {"n":n,"mean_r":m,"pf_r":gp/gl if gl>0 else (999.0 if gp>0 else 0.0),
            "lcb_r":lcb,"win_rate":z["wins"]/n}

folds={}; family_counts={}
for w in W:
    xs=list(root.rglob(f"R_V72_FAILURE_AUCTION_CAUSAL-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate failure auction {w}: {len(xs)}")
    d=json.load(open(xs[0]))
    census=[x for x in d.get("payoff_census",[]) if x.get("lane")=="FAILURE_AUCTION_CONTINUATION"]
    if not census: raise SystemExit(f"missing exact failure-auction census {w}")
    total=stats(merge(census))
    fam={}
    for f in sorted({x["family"] for x in census}):
        st=stats(merge([x for x in census if x["family"]==f])); fam[f]=st
        family_counts[f]=family_counts.get(f,0)+st["n"]
    passed=total["n"]>=MIN_N and total["mean_r"]>0 and total["pf_r"]>1.0 and total["lcb_r"]>0
    folds[w]={"selected_n":total["n"],"frequency_per_year":total["n"],"mean_r":total["mean_r"],
              "pf_r":total["pf_r"],"lcb_r":total["lcb_r"],"win_rate":total["win_rate"],
              "family_stats":fam,"pass":passed}
gate=all(folds[w]["pass"] for w in W)
manifest={"architecture":"V72_HARMONIC_FAILURE_AUCTION_CAUSAL",
 "stage":"BURNED_CALIBRATION_PRECAPITAL_GATE","selection_model":"NONE","tuning_model":"NONE",
 "reversal_capital_lane":"ELIMINATED_AFTER_3Y_NEGATIVE_EVIDENCE",
 "entry_semantics":"STRUCTURAL_FAILURE_BREAK_THEN_BOUNDARY_RETEST_THEN_LATER_COMPLETED_BAR_BREAK_OF_RETEST_EXTREME",
 "target_semantics":"FIXED_NET_2R","grid":"OFF","risk_pct":1.0,
 "min_selected_per_year":MIN_N,"lcb_z":Z,"folds":folds,
 "family_selected_counts":dict(sorted(family_counts.items())),
 "failure_auction_gate":gate,
 "gate_semantics":"DETERMINISTIC_3_YEAR_FAILURE_AUCTION_GATE__NO_MODEL_FIT_NO_THRESHOLD_TUNING",
 "capital_execution_used":False,"validation_used":False,"fresh_used":False}
(out/"FAILURE_AUCTION_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
