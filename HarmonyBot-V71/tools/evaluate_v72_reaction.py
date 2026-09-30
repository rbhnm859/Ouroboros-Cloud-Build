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

folds={}; all_rows=[]; family=collections.defaultdict(int)
for w in W:
    xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate shadow {w}: {len(xs)}")
    d=json.load(open(xs[0]))
    rows=[]
    seen=set()
    for r in d.get("shadow_outcomes",[]):
        if not r.get("capital_eligible",False): continue
        if int(r.get("path_state",0))==-2: continue
        k=(r.get("setup"),r.get("family"),r.get("route"))
        if k in seen: continue
        seen.add(k); rows.append(r); all_rows.append(r); family[r.get("family","UNKNOWN")]+=1
    v=[float(r.get("outcome_r",0.0)) for r in rows]
    n=len(v); m=mean(v); p=pf(v); q=lcb(v)
    wins=sum(x>0 for x in v)
    fold_pass=n>=MIN_N and m>0 and p>=MIN_PF and q>0
    folds[w]={"selected_n":n,"frequency_per_year":n,"mean_r":m,"pf_r":p,"lcb_r":q,
              "win_rate":wins/n if n else 0.0,"pass":fold_pass}

gate=all(x["pass"] for x in folds.values())
manifest={
 "architecture":"V72_DETERMINISTIC_REACTION_0618_PULLBACK_PROTECTED_ALPHA",
 "selection_model":"NONE",
 "tuning_model":"NONE",
 "rules":["FROZEN_HARMONIC_PATTERN","PRZ_TOUCH","FAMILY_NATIVE_REACTION_PROOF",
          "FIBONACCI_0618_PULLBACK_LIMIT_UNTIL_NEXT_M15_BOUNDARY","REACTION_EXTREME_COST_BUFFER_STOP_NEVER_WIDER_THAN_PATTERN_STOP",
          "PRIOR_COMPLETED_M1_PLUS_0_5R_ARMS_PLUS_0_1R_PROTECTION","COST_ADJUSTED_FIXED_2R_TARGET","V51_CORE_FIRST"],
 "min_selected_per_year":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,
 "folds":folds,"family_selected_counts":dict(sorted(family.items())),
 "rows":len(all_rows),"payoff_gate":gate,
 "gate_semantics":"DETERMINISTIC_3_YEAR_0618_PULLBACK_PROTECTED_CALIBRATION__NO_MODEL_FIT_NO_THRESHOLD_TUNING",
 "validation_used":False,"fresh_used":False
}
(out/"PAYOFF_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
