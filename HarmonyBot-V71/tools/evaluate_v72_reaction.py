#!/usr/bin/env python3
import json,pathlib,sys,math,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]; Z=1.645; MIN_N=60; MIN_PF=1.10

def merge(items):
    z={"n":0,"sum_r":0.0,"sum_sq_r":0.0,"gross_profit_r":0.0,"gross_loss_r":0.0,"wins":0}
    for x in items:
        z["n"]+=int(x.get("n",0)); z["sum_r"]+=float(x.get("sum_r",0.0)); z["sum_sq_r"]+=float(x.get("sum_sq_r",0.0))
        z["gross_profit_r"]+=float(x.get("gross_profit_r",0.0)); z["gross_loss_r"]+=float(x.get("gross_loss_r",0.0))
        z["wins"]+=int(x.get("wins",0))
    return z

def stats(z):
    n=int(z["n"])
    if n<=0: return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0}
    m=z["sum_r"]/n
    if n>1:
        var=max(0.0,(z["sum_sq_r"]-n*m*m)/(n-1))
        sd=math.sqrt(var); q=m-Z*sd/math.sqrt(n)
    else: q=-999.0
    gl=z["gross_loss_r"]; gp=z["gross_profit_r"]
    p=gp/gl if gl>0 else (999.0 if gp>0 else 0.0)
    return {"n":n,"mean_r":m,"pf_r":p,"lcb_r":q,"win_rate":z["wins"]/n}

folds={}; family_total=collections.defaultdict(int); lane_total=collections.defaultdict(int); total_rows=0
for w in W:
    xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate shadow {w}: {len(xs)}")
    d=json.load(open(xs[0]))
    census=d.get("payoff_census",[])
    if not census:
        raise SystemExit(f"missing exact V72 payoff census {w}; refuse row-log fallback")
    total=stats(merge(census)); lane_stats={}; lane_guard=True
    for lane in sorted({x["lane"] for x in census}):
        z=stats(merge([x for x in census if x["lane"]==lane]))
        lane_stats[lane]=z
        if z["n"]>=20 and not (z["mean_r"]>0 and z["pf_r"]>1.0): lane_guard=False
        lane_total[lane]+=z["n"]
    for fam in sorted({x["family"] for x in census}):
        family_total[fam]+=sum(int(x["n"]) for x in census if x["family"]==fam)
    total_rows+=total["n"]
    fold_pass=(total["n"]>=MIN_N and total["mean_r"]>0 and total["pf_r"]>=MIN_PF and total["lcb_r"]>0 and lane_guard)
    folds[w]={"selected_n":total["n"],"frequency_per_year":total["n"],"mean_r":total["mean_r"],
              "pf_r":total["pf_r"],"lcb_r":total["lcb_r"],"win_rate":total["win_rate"],
              "lane_stats":lane_stats,"lane_guard":lane_guard,"pass":fold_pass}

gate=all(x["pass"] for x in folds.values())
manifest={"architecture":"V72_HARMONIC_BIFURCATION_ALPHA","selection_model":"NONE","tuning_model":"NONE",
 "telemetry":"ONSTOP_EXACT_DEDUP_MOMENT_CENSUS",
 "rules":["FROZEN_HARMONIC_EVENT","EXHAUSTION_REACTION_0618_PULLBACK",
          "TREND_VIRTUAL_0P5R_PROOF_THEN_0618_RELOAD",
          "PATTERN_FAILURE_BREAK_THEN_OPPOSITE_0618_CONTINUATION",
          "TRANSITION_SHADOW_ONLY","NO_CAPITAL_BEFORE_CAUSAL_PROOF",
          "COST_ADJUSTED_FIXED_2R_MINUS_1R","GRID_OFF","V51_CORE_FIRST"],
 "min_selected_per_year":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,"folds":folds,
 "family_selected_counts":dict(sorted(family_total.items())),"lane_selected_counts":dict(sorted(lane_total.items())),
 "rows":total_rows,"payoff_gate":gate,
 "gate_semantics":"DETERMINISTIC_3_YEAR_BIFURCATION_PAYOFF_GATE__EXACT_AGGREGATE_TELEMETRY__NO_MODEL_FIT_NO_THRESHOLD_TUNING",
 "validation_used":False,"fresh_used":False}
(out/"PAYOFF_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
