#!/usr/bin/env python3
import json,pathlib,sys,math,statistics,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]; Z=1.645; MIN_N=60; MIN_PF=1.10
def mean(v): return sum(v)/len(v) if v else 0.0
def sd(v): return statistics.stdev(v) if len(v)>1 else 0.0
def pf(v):
    gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
    return gp/gl if gl else (999.0 if gp else 0.0)
def lcb(v): return mean(v)-Z*sd(v)/math.sqrt(len(v)) if len(v)>1 else -999.0
def stats(rows):
    v=[float(r.get("outcome_r",0.0)) for r in rows]; n=len(v)
    return {"n":n,"mean_r":mean(v),"pf_r":pf(v),"lcb_r":lcb(v),
            "win_rate":sum(x>0 for x in v)/n if n else 0.0}
folds={}; all_rows=[]; family=collections.defaultdict(int); lane_total=collections.defaultdict(int)
for w in W:
    xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate shadow {w}: {len(xs)}")
    d=json.load(open(xs[0])); rows=[]; seen=set()
    for r in d.get("shadow_outcomes",[]):
        if not r.get("capital_eligible",False): continue
        if int(r.get("path_state",0))==-2: continue
        lane=r.get("lane") or r.get("route") or "UNKNOWN"
        if lane=="TRANSITION_SHADOW": continue
        k=(r.get("setup"),r.get("family"),lane)
        if k in seen: continue
        seen.add(k); rows.append(r); all_rows.append(r)
        family[r.get("family","UNKNOWN")]+=1; lane_total[lane]+=1
    total=stats(rows); lane_stats={}; lane_guard=True
    for lane in sorted({(r.get("lane") or r.get("route") or "UNKNOWN") for r in rows}):
        z=stats([r for r in rows if (r.get("lane") or r.get("route") or "UNKNOWN")==lane])
        lane_stats[lane]=z
        if z["n"]>=20 and not (z["mean_r"]>0 and z["pf_r"]>1.0): lane_guard=False
    fold_pass=(total["n"]>=MIN_N and total["mean_r"]>0 and total["pf_r"]>=MIN_PF and total["lcb_r"]>0 and lane_guard)
    folds[w]={"selected_n":total["n"],"frequency_per_year":total["n"],"mean_r":total["mean_r"],
              "pf_r":total["pf_r"],"lcb_r":total["lcb_r"],"win_rate":total["win_rate"],
              "lane_stats":lane_stats,"lane_guard":lane_guard,"pass":fold_pass}
gate=all(x["pass"] for x in folds.values())
manifest={"architecture":"V72_HARMONIC_BIFURCATION_ALPHA","selection_model":"NONE","tuning_model":"NONE",
 "rules":["FROZEN_HARMONIC_EVENT","EXHAUSTION_REACTION_0618_PULLBACK",
          "TREND_VIRTUAL_0P5R_PROOF_THEN_0618_RELOAD",
          "PATTERN_FAILURE_BREAK_THEN_OPPOSITE_0618_CONTINUATION",
          "TRANSITION_SHADOW_ONLY","NO_CAPITAL_BEFORE_CAUSAL_PROOF",
          "COST_ADJUSTED_FIXED_2R_MINUS_1R","GRID_OFF","V51_CORE_FIRST"],
 "min_selected_per_year":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,"folds":folds,
 "family_selected_counts":dict(sorted(family.items())),"lane_selected_counts":dict(sorted(lane_total.items())),
 "rows":len(all_rows),"payoff_gate":gate,
 "gate_semantics":"DETERMINISTIC_3_YEAR_BIFURCATION_PAYOFF_GATE__NO_MODEL_FIT_NO_THRESHOLD_TUNING",
 "validation_used":False,"fresh_used":False}
(out/"PAYOFF_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
