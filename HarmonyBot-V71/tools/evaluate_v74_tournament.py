#!/usr/bin/env python3
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,TRAINERS,predict,train_protection,apply_protection,PROTECTION_KEYS,RCR_KEYS,HYBRID_KEYS,REACTION_COMMIT_KEYS,HIGH_CONVICTION_KEYS,SEQUENTIAL_KEYS

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"]
ALL=RESEARCH+BURNED
MIN_N=250
MIN_MEAN=.90
MIN_PF=3.30
MIN_WR=.70
MIN_RR=2.30
ABCD_TRAIN_MIN_N=300
ABCD_TRAIN_MIN_PF=1.20
SELECTION_QUANTILE=.60

rows=load_rows(root,ALL)
if not rows: raise SystemExit("no V74 tournament rows")

def quantile(vals,q):
    if not vals:return math.inf
    xs=sorted(float(x) for x in vals); pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return xs[lo] if lo==hi else xs[lo]*(hi-pos)+xs[hi]*(pos-lo)

def score_rows(name,model,xs):
    out=[]
    for r in xs:
        z=predict(name,model,r)
        q=dict(r); q.update({"pred_mean":float(z.get("mean",0.0)),"pred_win":float(z.get("win",0.0)),
                             "pred_lcb":float(z.get("lcb",-999.0)),"pred_hold":float(z.get("hold",180.0)),
                             "support":int(z.get("support",0)),"score":float(z.get("score",-999.0)),
                             "base_eligible":bool(z.get("base_eligible",False))})
        out.append(q)
    return out

def calibrate_threshold(name,model,tr):
    raw=score_rows(name,model,tr)
    eligible=[x["score"] for x in raw if x["base_eligible"] and math.isfinite(x["score"])]
    threshold=quantile(eligible,SELECTION_QUANTILE)
    model["selection_quantile"]=SELECTION_QUANTILE
    model["selection_threshold"]=threshold
    selected=score_rows(name,model,tr)
    selected=[x for x in selected if x["base_eligible"] and x["score"]>=threshold]
    return threshold,selected

def protection_summary(xs):
    d={k:0 for k in ["NONE"]+PROTECTION_KEYS}
    for r in xs:d[r.get("protection_key","NONE")]=d.get(r.get("protection_key","NONE"),0)+1
    return d

def gate_metrics(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)

models_blob={"architecture":"V74_ALPHA_TOURNAMENT_CAUSAL_STATE_40D_PLUS_SEQUENTIAL_PROTECTION","models":{}}
summary={"version":"HarmonyBot V74 Candidate",
         "architecture":"CAUSAL_STATE_40D_FIXED_TRAINING_QUANTILE_PLUS_COMPLETED_BAR_SEQUENTIAL_PROTECTION",
         "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
         "selection_policy":{"training_score_quantile":SELECTION_QUANTILE,
                             "test_year_never_sets_threshold":True,
                             "pre_entry_features_only":True},
         "protection_policy":{"keys":PROTECTION_KEYS,
                              "decision":"TRAINING_ONLY_DELTA_MODEL_LCB95_GT_0_AND_SUPPORT_GE_20",
                              "activation":"NEXT_COMPLETED_M1_BAR_AFTER_MILESTONE",
                              "same_bar_ambiguity":"PROTECTIVE_FLOOR_FIRST_CONSERVATIVE",
                              "no_stop_widening":True},
         "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
                 "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
         "models":{},"validation_used":False,"fresh_used":False,
         "rcr_policy":{"routes":RCR_KEYS,
                       "capital_entry":"REACTION_THEN_COMPLETED_BAR_RETRACE_RECLAIM",
                       "route_selection":"TRAINING_ONLY",
                       "minimum_net_rr_unchanged":True},
         "hybrid_survival_policy":{"routes":HYBRID_KEYS,
                                   "early_adverse_cut":"COMPLETED_M1_CLOSE_ONLY_BEFORE_POSITIVE_REACTION",
                                   "profit_frontier":"NEXT_BAR_ARMED_025_050_075_100_150_STAIRCASE",
                                   "runner_target":"UNCHANGED_CANONICAL_TARGET",
                                   "selection":"TRAINING_ONLY_WORST_YEAR_LCB_WITH_AVG_RR_GE_2P30",
                                   "no_stop_widening":True},
         "reaction_commit_policy":{"routes":REACTION_COMMIT_KEYS,
                                   "observation":"NO_CAPITAL_UNTIL_0P75R_OR_1P00R_VIRTUAL_REACTION",
                                   "entry":"NEXT_COMPLETED_DIRECTIONAL_M1_CLOSE_HOLDING_REACTION_FLOOR",
                                   "initial_stop":"REACTION_STRUCTURE_FLOOR_NO_WIDENING",
                                   "minimum_route_net_rr":2.30,
                                   "early_adverse_cut":"COMPLETED_CLOSE_ONLY_BEFORE_FIRST_LIVE_POSITIVE_MILESTONE",
                                   "profit_frontier":"LIVE_TRADE_025_050_075_100_150_STAIRCASE",
                                   "route_selection":"TRAINING_ONLY_WORST_YEAR_LCB",
                                   "test_year_never_selects_route":True},
         "high_conviction_policy":{"routes":HIGH_CONVICTION_KEYS,
                                   "observation":"NO_CAPITAL_UNTIL_1P75R_OR_2P00R_VIRTUAL_REACTION",
                                   "entry":"LATER_COMPLETED_M1_HOLD_OR_DIRECTIONAL_HOLD",
                                   "stop":"COMPLETED_ENTRY_BAR_MICRO_STRUCTURE",
                                   "minimum_route_net_rr":2.30,
                                   "profit_target":"UNCHANGED_CANONICAL_TARGET",
                                   "early_loss_only":"CLOSE_CUT_AT_MINUS_0P25_BEFORE_LIVE_PLUS_0P25R_PROOF",
                                   "no_small_profit_floor":True,
                                   "route_selection":"TRAINING_ONLY_WORST_YEAR_LCB",
                                   "test_year_never_selects_route":True},
         "causal_sequential_policy":{"routes":SEQUENTIAL_KEYS,
                                     "observation":"SHADOW_FIRST_PASSAGE_1P25R_OR_1P50R",
                                     "capital_entry":"LATER_COMPLETED_M1_REACTION_HOLD_ONLY",
                                     "stop":"REACTION_STRUCTURE_FLOOR_STRICTLY_INSIDE_NATIVE_RISK",
                                     "minimum_route_net_rr":2.30,
                                     "early_invalidation":"COMPLETED_CLOSE_MINUS_0P25R_BEFORE_PRIOR_PLUS_0P50R_PROOF",
                                     "frontier":"OPTIONAL_NEXT_BAR_ARMED_0P75_1P25_1P75_TO_0P25_0P65_1P00",
                                     "hazard_state":"FIRST_PASSAGE_TIME_MFE_MAE_BODY_WICKS_RETRACE_REMAINING_R_DIRECTION_EFFICIENCY_PLUS_PREENTRY_REGIME",
                                     "hazard_model":"ADDITIVE_HIERARCHICAL_PARTIAL_POOLING_NOT_STATIC_ENTRY_CLASSIFIER",
                                     "route_and_threshold_selection":"TRAINING_WINDOWS_ONLY_WORST_YEAR_ROBUST_OBJECTIVE",
                                     "same_bar_ambiguity":"ALREADY_ARMED_FLOOR_THEN_STOP_THEN_TARGET",
                                     "no_stop_widening":True,
                                     "test_year_never_selects_route_or_threshold":True}}

passers=[]
for name,trainer in TRAINERS.items():
    folds={}; fold_models={}; fold_protection={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        model=trainer(tr)
        threshold,training_selected=calibrate_threshold(name,model,tr)
        fold_models[test]=model

        protection_models={k:train_protection(training_selected,k) for k in PROTECTION_KEYS}
        fold_protection[test]=protection_models

        abcd_train=metrics([r for r in training_selected if r["family"]=="ABCD"])
        abcd_training_capital_eligible=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                                            abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)

        selected_native=[]
        for r in te:
            z=predict(name,model,r)
            if not z.get("selected"):continue
            if r["family"]=="ABCD" and not abcd_training_capital_eligible:continue
            q=dict(r); q.update({"pred_mean":z.get("mean",0.0),"pred_win":z.get("win",0.0),
                                 "pred_lcb":z.get("lcb",-999.0),"pred_hold":z.get("hold",180.0),
                                 "support":z.get("support",0),"score":z.get("score",-999.0)})
            selected_native.append(q)

        native_metrics=metrics(selected_native)
        selected=[apply_protection(protection_models,r) for r in selected_native]
        m=metrics(selected)
        m["pass"]=gate_metrics(m)
        m["native_metrics"]=native_metrics
        m["training_windows"]=train_windows
        m["selection_threshold"]=threshold
        m["training_selected_metrics"]=metrics(training_selected)
        m["protection_counts"]=protection_summary(selected)
        m["protection_delta_mean_r"]=m["mean_r"]-native_metrics["mean_r"]
        m["protection_delta_pf_r"]=m["pf_r"]-native_metrics["pf_r"]
        m["protection_delta_win_rate"]=m["win_rate"]-native_metrics["win_rate"]
        m["abcd_training_metrics"]=abcd_train
        m["abcd_training_capital_eligible"]=abcd_training_capital_eligible
        m["abcd_oof_native_metrics"]=metrics([r for r in selected_native if r["family"]=="ABCD"])
        m["abcd_oof_protected_metrics"]=metrics([r for r in selected if r["family"]=="ABCD"])
        folds[test]=m

    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)

    final_model=trainer(rows)
    final_threshold,final_training_selected=calibrate_threshold(name,final_model,rows)
    final_protection={k:train_protection(final_training_selected,k) for k in PROTECTION_KEYS}
    final_protected=[apply_protection(final_protection,r) for r in final_training_selected]
    abcd_final_train=metrics([r for r in final_training_selected if r["family"]=="ABCD"])
    abcd_final_eligible=bool(abcd_final_train["n"]>=ABCD_TRAIN_MIN_N and abcd_final_train["mean_r"]>0 and
                             abcd_final_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_final_train["lcb_r"]>0)
    final_model["abcd_training_capital_eligible"]=abcd_final_eligible

    models_blob["models"][name]={"folds":fold_models,"protection_folds":fold_protection,
                                  "final":final_model,"protection_final":final_protection,
                                  "abcd_final_capital_eligible":abcd_final_eligible}
    summary["models"][name]={"folds":folds,"pass":model_pass,
                              "final_selection_threshold":final_threshold,
                              "final_training_selected_metrics":metrics(final_training_selected),
                              "final_training_protected_metrics":metrics(final_protected),
                              "final_protection_counts":protection_summary(final_protected),
                              "abcd_final_training_metrics":abcd_final_train,
                              "abcd_final_capital_eligible":abcd_final_eligible,
                              "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,name))


def with_rcr_outcome(r,key):
    v=r.get("rcr",{}).get(key)
    if v is None or not math.isfinite(float(v)):return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=float(v);q["rcr_key"]=key
    return q

def rcr_metric_rows(xs,key,family=None,action=None):
    out=[]
    for r in xs:
        if family is not None and r["family"]!=family:continue
        if action is not None and r["action"]!=action:continue
        q=with_rcr_outcome(r,key)
        if q is not None:out.append(q)
    return out

def choose_global_rcr(train_rows,train_windows):
    candidates=[]
    for key in RCR_KEYS:
        agg=rcr_metric_rows(train_rows,key)
        m=metrics(agg)
        yearly=[]
        for w in train_windows:
            ym=metrics(rcr_metric_rows([r for r in train_rows if r["window"]==w],key))
            if ym["n"]>=40: yearly.append(ym["lcb_r"])
        if m["n"]>=300 and m["mean_r"]>0 and m["pf_r"]>=1.20 and m["average_rr"]>=2.0 and m["lcb_r"]>0 and len(yearly)>=4:
            candidates.append((min(yearly),m["lcb_r"],m["mean_r"],key,m))
    candidates.sort(reverse=True)
    return candidates[0][3] if candidates else None

def choose_hier_rcr(train_rows,global_key):
    policy={}
    for fam in sorted({r["family"] for r in train_rows}):
        for action in ("REVERSAL","CONTINUATION"):
            candidates=[]
            for key in RCR_KEYS:
                rr=rcr_metric_rows(train_rows,key,fam,action)
                m=metrics(rr)
                if m["n"]>=40 and m["mean_r"]>0 and m["pf_r"]>=1.20 and m["average_rr"]>=2.0 and m["lcb_r"]>0:
                    candidates.append((m["lcb_r"],m["mean_r"],m["n"],key))
            candidates.sort(reverse=True)
            policy[fam+"|"+action]=candidates[0][3] if candidates else global_key
    return policy

def apply_rcr_policy(xs,policy,global_key=None,abcd_allowed=True):
    out=[]
    for r in xs:
        if r["family"]=="ABCD" and not abcd_allowed:continue
        key=policy.get(r["family"]+"|"+r["action"],global_key) if isinstance(policy,dict) else global_key
        if not key:continue
        q=with_rcr_outcome(r,key)
        if q is not None:out.append(q)
    return out

for rcr_name,hierarchical in [("D_REACTION_CONFIRMED_REENTRY_GLOBAL",False),
                              ("E_REACTION_CONFIRMED_REENTRY_HIERARCHICAL",True)]:
    folds={}; fold_policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        global_key=choose_global_rcr(tr,train_windows)
        policy=choose_hier_rcr(tr,global_key) if hierarchical else {}
        abcd_key=(policy.get("ABCD|REVERSAL") or policy.get("ABCD|CONTINUATION") or global_key) if hierarchical else global_key
        abcd_train=metrics(rcr_metric_rows([r for r in tr if r["family"]=="ABCD"],abcd_key)) if abcd_key else metrics([])
        abcd_allowed=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                          abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        selected=apply_rcr_policy(te,policy,global_key,abcd_allowed)
        m=metrics(selected);m["pass"]=gate_metrics(m);m["training_windows"]=train_windows
        m["global_route"]=global_key;m["route_policy"]=policy
        m["abcd_training_metrics"]=abcd_train;m["abcd_training_capital_eligible"]=abcd_allowed
        folds[test]=m
        fold_policies[test]={"global_route":global_key,"route_policy":policy,"abcd_capital_eligible":abcd_allowed}
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_global=choose_global_rcr(rows,ALL)
    final_policy=choose_hier_rcr(rows,final_global) if hierarchical else {}
    final_abcd_key=(final_policy.get("ABCD|REVERSAL") or final_policy.get("ABCD|CONTINUATION") or final_global) if hierarchical else final_global
    final_abcd=metrics(rcr_metric_rows([r for r in rows if r["family"]=="ABCD"],final_abcd_key)) if final_abcd_key else metrics([])
    final_abcd_allowed=bool(final_abcd["n"]>=ABCD_TRAIN_MIN_N and final_abcd["mean_r"]>0 and final_abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and final_abcd["lcb_r"]>0)
    final_selected=apply_rcr_policy(rows,final_policy,final_global,final_abcd_allowed)
    models_blob["models"][rcr_name]={"type":"REACTION_CONFIRMED_REENTRY",
                                     "folds":fold_policies,
                                     "final":{"global_route":final_global,"route_policy":final_policy},
                                     "abcd_final_capital_eligible":final_abcd_allowed}
    summary["models"][rcr_name]={"folds":folds,"pass":model_pass,
                                 "final_global_route":final_global,"final_route_policy":final_policy,
                                 "final_training_metrics":metrics(final_selected),
                                 "abcd_final_training_metrics":final_abcd,
                                 "abcd_final_capital_eligible":final_abcd_allowed,
                                 "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,rcr_name))


def with_hybrid_outcome(r,key):
    v=r.get("hybrid",{}).get(key)
    if v is None or not math.isfinite(float(v)):return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=float(v);q["hybrid_key"]=key
    return q

def hybrid_metric_rows(xs,key,family=None,action=None):
    out=[]
    for r in xs:
        if family is not None and r["family"]!=family:continue
        if action is not None and r["action"]!=action:continue
        q=with_hybrid_outcome(r,key)
        if q is not None:out.append(q)
    return out

def choose_hybrid_policy(train_selected,train_windows):
    candidates=[]
    for key in HYBRID_KEYS:
        agg=metrics(hybrid_metric_rows(train_selected,key))
        yearly=[]
        for w in train_windows:
            ym=metrics(hybrid_metric_rows([r for r in train_selected if r["window"]==w],key))
            if ym["n"]>=80:yearly.append(ym)
        if agg["n"]<300 or agg["average_rr"]<MIN_RR or len(yearly)<4:continue
        worst_lcb=min(z["lcb_r"] for z in yearly)
        worst_mean=min(z["mean_r"] for z in yearly)
        candidates.append((worst_lcb,worst_mean,agg["lcb_r"],agg["mean_r"],agg["pf_r"],agg["win_rate"],key,agg))
    candidates.sort(reverse=True)
    return candidates[0][6] if candidates else None

def base_selected_rows(base_name,model,xs):
    return [r for r in xs if predict(base_name,model,r).get("selected")]

for hybrid_name,base_name in [
    ("F_HYBRID_SURVIVAL_HIERARCHICAL","A_HIERARCHICAL_COMPETING_RISK"),
    ("G_HYBRID_SURVIVAL_STUMPS","B_BOUNDED_GRADIENT_STUMPS"),
    ("H_HYBRID_SURVIVAL_MANIFOLD","C_CONFORMAL_STATE_MANIFOLD")]:
    folds={};fold_policies={}
    base_pack=models_blob["models"][base_name]
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        base_model=base_pack["folds"][test]
        training_selected=base_selected_rows(base_name,base_model,tr)
        hybrid_key=choose_hybrid_policy(training_selected,train_windows)
        hybrid_train=hybrid_metric_rows(training_selected,hybrid_key) if hybrid_key else [dict(r) for r in training_selected]
        abcd_train=metrics([r for r in hybrid_train if r["family"]=="ABCD"])
        abcd_allowed=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                          abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        test_native=base_selected_rows(base_name,base_model,te)
        if not abcd_allowed:test_native=[r for r in test_native if r["family"]!="ABCD"]
        selected=hybrid_metric_rows(test_native,hybrid_key) if hybrid_key else [dict(r) for r in test_native]
        m=metrics(selected);m["pass"]=gate_metrics(m);m["training_windows"]=train_windows
        m["base_model"]=base_name;m["hybrid_key"]=hybrid_key
        m["training_selected_native_metrics"]=metrics(training_selected)
        m["training_selected_hybrid_metrics"]=metrics(hybrid_train)
        m["native_oof_metrics"]=metrics(test_native)
        m["abcd_training_metrics"]=abcd_train
        m["abcd_training_capital_eligible"]=abcd_allowed
        folds[test]=m
        fold_policies[test]={"base_model":base_name,"hybrid_key":hybrid_key,"abcd_capital_eligible":abcd_allowed}
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_model=base_pack["final"]
    final_native=base_selected_rows(base_name,final_model,rows)
    final_key=choose_hybrid_policy(final_native,ALL)
    final_selected=hybrid_metric_rows(final_native,final_key) if final_key else [dict(r) for r in final_native]
    final_abcd=metrics([r for r in final_selected if r["family"]=="ABCD"])
    final_abcd_allowed=bool(final_abcd["n"]>=ABCD_TRAIN_MIN_N and final_abcd["mean_r"]>0 and
                            final_abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and final_abcd["lcb_r"]>0)
    models_blob["models"][hybrid_name]={"type":"HYBRID_SURVIVAL_FRONTIER",
                                        "base_model":base_name,
                                        "folds":fold_policies,
                                        "final":{"base_model":base_name,"hybrid_key":final_key},
                                        "abcd_final_capital_eligible":final_abcd_allowed}
    summary["models"][hybrid_name]={"folds":folds,"pass":model_pass,
                                    "base_model":base_name,"final_hybrid_key":final_key,
                                    "final_training_metrics":metrics(final_selected),
                                    "abcd_final_training_metrics":final_abcd,
                                    "abcd_final_capital_eligible":final_abcd_allowed,
                                    "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,hybrid_name))


def with_reaction_commit_outcome(r,key):
    v=r.get("reaction_commit",{}).get(key)
    if v is None or not math.isfinite(float(v)):return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=float(v);q["reaction_commit_key"]=key
    return q

def reaction_commit_rows(xs,key,family=None,action=None):
    out=[]
    for r in xs:
        if family is not None and r["family"]!=family:continue
        if action is not None and r["action"]!=action:continue
        q=with_reaction_commit_outcome(r,key)
        if q is not None:out.append(q)
    return out

def choose_global_reaction_commit(train_rows,train_windows):
    candidates=[]
    for key in REACTION_COMMIT_KEYS:
        agg=metrics(reaction_commit_rows(train_rows,key))
        yearly=[]
        for w in train_windows:
            ym=metrics(reaction_commit_rows([r for r in train_rows if r["window"]==w],key))
            if ym["n"]>=180:yearly.append(ym)
        if agg["n"]<1200 or agg["average_rr"]<MIN_RR or len(yearly)<4:continue
        candidates.append((min(z["lcb_r"] for z in yearly),
                           min(z["mean_r"] for z in yearly),
                           agg["lcb_r"],agg["mean_r"],agg["pf_r"],agg["win_rate"],key))
    candidates.sort(reverse=True)
    return candidates[0][6] if candidates else None

def choose_hier_reaction_commit(train_rows,global_key):
    policy={}
    for fam in sorted({r["family"] for r in train_rows}):
        for action in ("REVERSAL","CONTINUATION"):
            candidates=[]
            for key in REACTION_COMMIT_KEYS:
                m=metrics(reaction_commit_rows(train_rows,key,fam,action))
                if m["n"]>=60 and m["average_rr"]>=MIN_RR:
                    candidates.append((m["lcb_r"],m["mean_r"],m["pf_r"],m["win_rate"],m["n"],key))
            candidates.sort(reverse=True)
            policy[fam+"|"+action]=candidates[0][5] if candidates else global_key
    return policy

def apply_reaction_commit_policy(xs,policy,global_key,abcd_allowed=True):
    out=[]
    for r in xs:
        if r["family"]=="ABCD" and not abcd_allowed:continue
        key=policy.get(r["family"]+"|"+r["action"],global_key) if isinstance(policy,dict) else global_key
        if not key:continue
        q=with_reaction_commit_outcome(r,key)
        if q is not None:out.append(q)
    return out

for rc_name,hierarchical in [
    ("I_REACTION_COMMIT_LADDER_GLOBAL",False),
    ("J_REACTION_COMMIT_LADDER_HIERARCHICAL",True)]:
    folds={};fold_policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        global_key=choose_global_reaction_commit(tr,train_windows)
        policy=choose_hier_reaction_commit(tr,global_key) if hierarchical else {}
        train_selected=apply_reaction_commit_policy(tr,policy,global_key,True)
        abcd_train=metrics([r for r in train_selected if r["family"]=="ABCD"])
        abcd_allowed=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                          abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        selected=apply_reaction_commit_policy(te,policy,global_key,abcd_allowed)
        m=metrics(selected);m["pass"]=gate_metrics(m);m["training_windows"]=train_windows
        m["global_route"]=global_key;m["route_policy"]=policy
        m["training_selected_metrics"]=metrics(train_selected)
        m["abcd_training_metrics"]=abcd_train;m["abcd_training_capital_eligible"]=abcd_allowed
        folds[test]=m
        fold_policies[test]={"global_route":global_key,"route_policy":policy,
                             "abcd_capital_eligible":abcd_allowed}
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_global=choose_global_reaction_commit(rows,ALL)
    final_policy=choose_hier_reaction_commit(rows,final_global) if hierarchical else {}
    final_train=apply_reaction_commit_policy(rows,final_policy,final_global,True)
    final_abcd=metrics([r for r in final_train if r["family"]=="ABCD"])
    final_abcd_allowed=bool(final_abcd["n"]>=ABCD_TRAIN_MIN_N and final_abcd["mean_r"]>0 and
                            final_abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and final_abcd["lcb_r"]>0)
    final_selected=apply_reaction_commit_policy(rows,final_policy,final_global,final_abcd_allowed)
    models_blob["models"][rc_name]={"type":"REACTION_COMMIT_LADDER",
                                    "folds":fold_policies,
                                    "final":{"global_route":final_global,"route_policy":final_policy},
                                    "abcd_final_capital_eligible":final_abcd_allowed}
    summary["models"][rc_name]={"folds":folds,"pass":model_pass,
                               "final_global_route":final_global,"final_route_policy":final_policy,
                               "final_training_metrics":metrics(final_selected),
                               "abcd_final_training_metrics":final_abcd,
                               "abcd_final_capital_eligible":final_abcd_allowed,
                               "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,rc_name))


def with_high_conviction_outcome(r,key):
    v=r.get("high_conviction",{}).get(key)
    if v is None or not math.isfinite(float(v)):return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=float(v);q["high_conviction_key"]=key
    return q

def high_conviction_rows(xs,key,family=None,action=None):
    out=[]
    for r in xs:
        if family is not None and r["family"]!=family:continue
        if action is not None and r["action"]!=action:continue
        q=with_high_conviction_outcome(r,key)
        if q is not None:out.append(q)
    return out

def choose_global_high_conviction(train_rows,train_windows):
    candidates=[]
    for key in HIGH_CONVICTION_KEYS:
        agg=metrics(high_conviction_rows(train_rows,key))
        yearly=[]
        for w in train_windows:
            ym=metrics(high_conviction_rows([r for r in train_rows if r["window"]==w],key))
            if ym["n"]>=180:yearly.append(ym)
        if agg["n"]<1200 or agg["average_rr"]<MIN_RR or len(yearly)<4:continue
        candidates.append((min(z["lcb_r"] for z in yearly),
                           min(z["mean_r"] for z in yearly),
                           min(z["win_rate"] for z in yearly),
                           agg["lcb_r"],agg["mean_r"],agg["pf_r"],agg["win_rate"],key))
    candidates.sort(reverse=True)
    return candidates[0][7] if candidates else None

def choose_hier_high_conviction(train_rows,global_key):
    policy={}
    for fam in sorted({r["family"] for r in train_rows}):
        for action in ("REVERSAL","CONTINUATION"):
            candidates=[]
            for key in HIGH_CONVICTION_KEYS:
                m=metrics(high_conviction_rows(train_rows,key,fam,action))
                if m["n"]>=50 and m["average_rr"]>=MIN_RR:
                    candidates.append((m["lcb_r"],m["mean_r"],m["win_rate"],m["pf_r"],m["n"],key))
            candidates.sort(reverse=True)
            policy[fam+"|"+action]=candidates[0][5] if candidates else global_key
    return policy

def apply_high_conviction_policy(xs,policy,global_key,abcd_allowed=True):
    out=[]
    for r in xs:
        if r["family"]=="ABCD" and not abcd_allowed:continue
        key=policy.get(r["family"]+"|"+r["action"],global_key) if isinstance(policy,dict) else global_key
        if not key:continue
        q=with_high_conviction_outcome(r,key)
        if q is not None:out.append(q)
    return out

for hc_name,hierarchical in [
    ("K_HIGH_CONVICTION_DELAYED_COMMIT_GLOBAL",False),
    ("L_HIGH_CONVICTION_DELAYED_COMMIT_HIERARCHICAL",True)]:
    folds={};fold_policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        global_key=choose_global_high_conviction(tr,train_windows)
        policy=choose_hier_high_conviction(tr,global_key) if hierarchical else {}
        train_selected=apply_high_conviction_policy(tr,policy,global_key,True)
        abcd_train=metrics([r for r in train_selected if r["family"]=="ABCD"])
        abcd_allowed=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                          abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        selected=apply_high_conviction_policy(te,policy,global_key,abcd_allowed)
        m=metrics(selected);m["pass"]=gate_metrics(m);m["training_windows"]=train_windows
        m["global_route"]=global_key;m["route_policy"]=policy
        m["training_selected_metrics"]=metrics(train_selected)
        m["abcd_training_metrics"]=abcd_train;m["abcd_training_capital_eligible"]=abcd_allowed
        folds[test]=m
        fold_policies[test]={"global_route":global_key,"route_policy":policy,
                             "abcd_capital_eligible":abcd_allowed}
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_global=choose_global_high_conviction(rows,ALL)
    final_policy=choose_hier_high_conviction(rows,final_global) if hierarchical else {}
    final_train=apply_high_conviction_policy(rows,final_policy,final_global,True)
    final_abcd=metrics([r for r in final_train if r["family"]=="ABCD"])
    final_abcd_allowed=bool(final_abcd["n"]>=ABCD_TRAIN_MIN_N and final_abcd["mean_r"]>0 and
                            final_abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and final_abcd["lcb_r"]>0)
    final_selected=apply_high_conviction_policy(rows,final_policy,final_global,final_abcd_allowed)
    models_blob["models"][hc_name]={"type":"HIGH_CONVICTION_DELAYED_COMMIT",
                                    "folds":fold_policies,
                                    "final":{"global_route":final_global,"route_policy":final_policy},
                                    "abcd_final_capital_eligible":final_abcd_allowed}
    summary["models"][hc_name]={"folds":folds,"pass":model_pass,
                               "final_global_route":final_global,"final_route_policy":final_policy,
                               "final_training_metrics":metrics(final_selected),
                               "abcd_final_training_metrics":final_abcd,
                               "abcd_final_capital_eligible":final_abcd_allowed,
                               "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,hc_name))


def with_sequential_outcome(r,key):
    v=r.get("sequential",{}).get(key)
    rr=r.get("sequential_rr",{}).get(key)
    level="125" if "S125_" in key else "150"
    state=r.get("sequential_state",{}).get(level)
    if v is None or rr is None or state is None or len(state)!=12:return None
    if not math.isfinite(float(v)) or not math.isfinite(float(rr)) or float(rr)+1e-9<MIN_RR:return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=float(v);q["sequential_key"]=key
    q["sequential_planned_rr"]=float(rr);q["sequential_level"]=level;q["sequential_state_vector"]=list(state)
    return q

def sequential_rows(xs,key,family=None,action=None):
    out=[]
    for r in xs:
        if family is not None and r["family"]!=family:continue
        if action is not None and r["action"]!=action:continue
        q=with_sequential_outcome(r,key)
        if q is not None:out.append(q)
    return out

def seq_hazard_vector(r):
    s=r.get("sequential_state_vector")
    if s is None or len(s)!=12:return None
    f=r.get("features",[])
    pre=[f[j] if j<len(f) else 0.0 for j in (25,26,29,34,35,36,37,38,39)]
    return list(s)+pre

def _seq_stat(xs):
    if not xs:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0}
    vv=[float(r["r"]) for r in xs];n=len(vv)
    sd=statistics.stdev(vv) if n>1 else 10.0
    return {"n":n,"mean":sum(vv)/n,"win":sum(v>0 for v in vv)/n,"sigma":max(.05,sd)}

def train_seq_hazard(xs,key):
    q=sequential_rows(xs,key)
    pairs=[(r,seq_hazard_vector(r)) for r in q]
    pairs=[z for z in pairs if z[1] is not None]
    q=[z[0] for z in pairs];vec=[z[1] for z in pairs]
    if not q:return {"key":key,"medians":[],"global":_seq_stat([]),"family_action":{},"bins":[]}
    p=len(vec[0]);med=[statistics.median(v[j] for v in vec) for j in range(p)]
    glob=_seq_stat(q);fa={}
    for fam in sorted({r["family"] for r in q}):
        for action in ("REVERSAL","CONTINUATION"):
            z=[r for r in q if r["family"]==fam and r["action"]==action]
            if z:fa[fam+"|"+action]=_seq_stat(z)
    bins=[]
    for j in range(p):
        lo=[r for r,v in zip(q,vec) if v[j]<med[j]]
        hi=[r for r,v in zip(q,vec) if v[j]>=med[j]]
        bins.append({"lo":_seq_stat(lo),"hi":_seq_stat(hi)})
    return {"key":key,"medians":med,"global":glob,"family_action":fa,"bins":bins}

def score_seq_hazard(model,r):
    v=seq_hazard_vector(r);g=model.get("global",{})
    if v is None or not model.get("medians") or int(g.get("n",0))<80:
        return {"score":-999.0,"mean":0.0,"win":0.0,"lcb":-999.0,"support":0}
    gm=float(g.get("mean",0.0));gw=float(g.get("win",0.0));gs=float(g.get("sigma",10.0))
    fa=model.get("family_action",{}).get(r["family"]+"|"+r["action"],{"n":0,"mean":gm,"win":gw})
    fn=int(fa.get("n",0));fw=fn/(fn+80.0)
    parent_m=gm+fw*(float(fa.get("mean",gm))-gm)
    parent_w=gw+fw*(float(fa.get("win",gw))-gw)
    ms=[];ws=[];supports=[]
    for j,x in enumerate(v):
        b=model["bins"][j]["hi" if x>=model["medians"][j] else "lo"]
        n=int(b.get("n",0));sh=n/(n+60.0)
        ms.append(parent_m+sh*(float(b.get("mean",gm))-gm))
        ws.append(parent_w+sh*(float(b.get("win",gw))-gw))
        supports.append(n)
    mean=(parent_m+sum(ms)/len(ms))/2.0
    win=max(0.0,min(1.0,(parent_w+sum(ws)/len(ws))/2.0))
    support=max(1,min([fn if fn>0 else int(g.get("n",1))]+supports))
    lcb=mean-Z*gs/math.sqrt(support)
    return {"score":lcb+.75*win,"mean":mean,"win":win,"lcb":lcb,"support":support}

def apply_seq_hazard(xs,key,model,threshold,abcd_allowed=True):
    out=[]
    for r in sequential_rows(xs,key):
        if r["family"]=="ABCD" and not abcd_allowed:continue
        z=score_seq_hazard(model,r)
        if z["score"]+1e-12<threshold:continue
        q=dict(r);q["seq_pred_mean"]=z["mean"];q["seq_pred_win"]=z["win"]
        q["seq_pred_lcb"]=z["lcb"];q["seq_support"]=z["support"];q["seq_score"]=z["score"]
        out.append(q)
    return out

def choose_seq_candidate(train_rows,train_windows,selection_quantile):
    candidates=[]
    for key in SEQUENTIAL_KEYS:
        model=train_seq_hazard(train_rows,key)
        scored=[score_seq_hazard(model,r)["score"] for r in sequential_rows(train_rows,key)]
        scored=[z for z in scored if math.isfinite(z) and z>-900]
        if not scored:continue
        threshold=quantile(scored,selection_quantile)
        selected=apply_seq_hazard(train_rows,key,model,threshold,True)
        agg=metrics(selected);yearly=[]
        for w in train_windows:
            ym=metrics([r for r in selected if r["window"]==w])
            if ym["n"]>=120:yearly.append(ym)
        if agg["n"]<700 or len(yearly)<4:continue
        worst_lcb=min(z["lcb_r"] for z in yearly);worst_mean=min(z["mean_r"] for z in yearly)
        worst_wr=min(z["win_rate"] for z in yearly);worst_rr=min(z["average_rr"] for z in yearly)
        utility=worst_lcb+.20*worst_mean+.35*worst_wr+.08*min(5.0,worst_rr)
        candidates.append((utility,worst_lcb,worst_mean,worst_wr,worst_rr,agg["n"],key,model,threshold,agg))
    candidates.sort(key=lambda z:(z[0],z[1],z[2],z[3],z[4],z[5],z[6]),reverse=True)
    return candidates[0] if candidates else None

for seq_name,selection_quantile in [
    ("M_CAUSAL_SEQ_HAZARD_KEEP90",.10),
    ("N_CAUSAL_SEQ_HAZARD_KEEP85",.15),
    ("O_CAUSAL_SEQ_HAZARD_KEEP80",.20)]:
    folds={};fold_policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        choice=choose_seq_candidate(tr,train_windows,selection_quantile)
        if choice is None:
            m=metrics([]);m["pass"]=False;m["training_windows"]=train_windows;m["route"]=None
            m["selection_quantile"]=selection_quantile;m["selection_threshold"]=None
            folds[test]=m;fold_policies[test]={"route":None,"selection_quantile":selection_quantile}
            continue
        utility,worst_lcb,worst_mean,worst_wr,worst_rr,train_n,key,model,threshold,train_agg=choice
        train_selected=apply_seq_hazard(tr,key,model,threshold,True)
        abcd_train=metrics([r for r in train_selected if r["family"]=="ABCD"])
        abcd_allowed=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                          abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        selected=apply_seq_hazard(te,key,model,threshold,abcd_allowed)
        m=metrics(selected);m["pass"]=gate_metrics(m);m["training_windows"]=train_windows
        m["route"]=key;m["selection_quantile"]=selection_quantile;m["selection_threshold"]=threshold
        m["training_selected_metrics"]=metrics(train_selected)
        m["training_worst_year_lcb"]=worst_lcb;m["training_worst_year_mean"]=worst_mean
        m["training_worst_year_win_rate"]=worst_wr;m["training_worst_year_average_rr"]=worst_rr
        m["training_route_utility"]=utility;m["abcd_training_metrics"]=abcd_train
        m["abcd_training_capital_eligible"]=abcd_allowed
        m["median_planned_route_rr"]=statistics.median([r["sequential_planned_rr"] for r in selected]) if selected else 0.0
        folds[test]=m
        fold_policies[test]={"route":key,"selection_quantile":selection_quantile,"selection_threshold":threshold,
                             "hazard_model":model,"abcd_capital_eligible":abcd_allowed}
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_choice=choose_seq_candidate(rows,ALL,selection_quantile)
    if final_choice is not None:
        _,_,_,_,_,_,fkey,fmodel,fthreshold,_=final_choice
        final_selected=apply_seq_hazard(rows,fkey,fmodel,fthreshold,True)
        final_abcd=metrics([r for r in final_selected if r["family"]=="ABCD"])
        final_abcd_allowed=bool(final_abcd["n"]>=ABCD_TRAIN_MIN_N and final_abcd["mean_r"]>0 and
                                final_abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and final_abcd["lcb_r"]>0)
        final_selected=apply_seq_hazard(rows,fkey,fmodel,fthreshold,final_abcd_allowed)
        final_policy={"route":fkey,"selection_quantile":selection_quantile,"selection_threshold":fthreshold,
                      "hazard_model":fmodel,"abcd_capital_eligible":final_abcd_allowed}
    else:
        fkey=None;final_selected=[];final_abcd=metrics([]);final_abcd_allowed=False
        final_policy={"route":None,"selection_quantile":selection_quantile}
    models_blob["models"][seq_name]={"type":"CAUSAL_FIRST_PASSAGE_SEQUENTIAL_HAZARD",
                                     "folds":fold_policies,"final":final_policy}
    summary["models"][seq_name]={"folds":folds,"pass":model_pass,
                                 "final_route":fkey,"final_training_metrics":metrics(final_selected),
                                 "abcd_final_training_metrics":final_abcd,
                                 "abcd_final_capital_eligible":final_abcd_allowed,
                                 "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,seq_name))

passers.sort(key=lambda x:(x[0],x[1]),reverse=True)
champion=passers[0][1] if passers else None
summary["v74_gate"]=champion is not None
summary["champion"]=champion
summary["champion_selection"]="HIGHEST_WORST_YEAR_CAUSAL_LCB_PER_EXPECTED_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["abcd_policy"]={"training_selected_subset_eligibility":True,"min_training_n":ABCD_TRAIN_MIN_N,
                        "min_training_pf_r":ABCD_TRAIN_MIN_PF,"mean_r_gt":0.0,"lcb95_gt":0.0,
                        "rule":"STANDALONE_ABCD_CAN_ENTER_TEST_YEAR_ONLY_IF_FROZEN_ENTRY_MODEL_SELECTED_ABCD_SUBSET_IN_PRIOR_TRAINING_WINDOWS_PROVES_POSITIVE_NATIVE_MEAN_PF_AND_LCB;_TEST_YEAR_NEVER_CONTROLS_ELIGIBILITY"}
summary["gate_semantics"]="EACH_BURNED_YEAR_N_GE_250_MEAN_R_GE_0P90_PF_R_GE_3P30_WR_GE_70PCT_AVG_RR_GE_2P30_LCB95_GT_0__ALL_ENTRY_EXIT_PROTECTION_SEQUENTIAL_ROUTE_AND_HAZARD_THRESHOLDS_TRAIN_ONLY__NO_LOOKAHEAD"
summary["positive_asset"]="A_FORMALLY_OOF_ALPHA_PLUS_PROTECTION_CHAMPION_WITH_BUFFER_ABOVE_FINAL_COMMERCIAL_TARGETS" if champion else "NO_MODEL_EARNED_VERSION_PROMOTION"

(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models_blob,separators=(",",":")))
(out/"champion.txt").write_text(champion or "")
(out/"pass.txt").write_text("true" if champion else "false")
print(json.dumps(summary,indent=2))
