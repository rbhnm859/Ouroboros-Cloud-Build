#!/usr/bin/env python3
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,TRAINERS,predict

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

models_blob={"architecture":"V74_ALPHA_TOURNAMENT_CAUSAL_STATE_40D","models":{}}
summary={"version":"HarmonyBot V74 Candidate","architecture":"CAUSAL_STATE_40D_FIXED_TRAINING_QUANTILE_TOURNAMENT",
         "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
         "selection_policy":{"training_score_quantile":SELECTION_QUANTILE,
                             "test_year_never_sets_threshold":True,
                             "pre_entry_features_only":True},
         "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
                 "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
         "models":{},"validation_used":False,"fresh_used":False}

passers=[]
for name,trainer in TRAINERS.items():
    folds={}; fold_models={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows]
        te=[r for r in rows if r["window"]==test]
        model=trainer(tr)
        threshold,training_selected=calibrate_threshold(name,model,tr)
        fold_models[test]=model
        abcd_train=metrics([r for r in training_selected if r["family"]=="ABCD"])
        abcd_training_capital_eligible=bool(abcd_train["n"]>=ABCD_TRAIN_MIN_N and abcd_train["mean_r"]>0 and
                                            abcd_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_train["lcb_r"]>0)
        selected=[]
        for r in te:
            z=predict(name,model,r)
            if not z.get("selected"):continue
            if r["family"]=="ABCD" and not abcd_training_capital_eligible:continue
            q=dict(r); q.update({"pred_mean":z.get("mean",0.0),"pred_win":z.get("win",0.0),
                                 "pred_lcb":z.get("lcb",-999.0),"pred_hold":z.get("hold",180.0),
                                 "support":z.get("support",0),"score":z.get("score",-999.0)})
            selected.append(q)
        m=metrics(selected)
        m["pass"]=bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                       m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
        m["training_windows"]=train_windows
        m["selection_threshold"]=threshold
        m["training_selected_metrics"]=metrics(training_selected)
        m["abcd_training_metrics"]=abcd_train
        m["abcd_training_capital_eligible"]=abcd_training_capital_eligible
        m["abcd_oof_selected_metrics"]=metrics([r for r in selected if r["family"]=="ABCD"])
        folds[test]=m
    model_pass=all(folds[w]["pass"] for w in BURNED)
    worst_lcb=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    score=worst_lcb/max(.25,avg_hold)
    final_model=trainer(rows)
    final_threshold,final_training_selected=calibrate_threshold(name,final_model,rows)
    abcd_final_train=metrics([r for r in final_training_selected if r["family"]=="ABCD"])
    abcd_final_eligible=bool(abcd_final_train["n"]>=ABCD_TRAIN_MIN_N and abcd_final_train["mean_r"]>0 and
                             abcd_final_train["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd_final_train["lcb_r"]>0)
    final_model["abcd_training_capital_eligible"]=abcd_final_eligible
    models_blob["models"][name]={"folds":fold_models,"final":final_model,
                                  "abcd_final_capital_eligible":abcd_final_eligible}
    summary["models"][name]={"folds":folds,"pass":model_pass,
                              "final_selection_threshold":final_threshold,
                              "final_training_selected_metrics":metrics(final_training_selected),
                              "abcd_final_training_metrics":abcd_final_train,
                              "abcd_final_capital_eligible":abcd_final_eligible,
                              "champion_score_worst_lcb_per_slot_hour":score}
    if model_pass:passers.append((score,name))

passers.sort(key=lambda x:(x[0],x[1]),reverse=True)
champion=passers[0][1] if passers else None
summary["v74_gate"]=champion is not None
summary["champion"]=champion
summary["champion_selection"]="HIGHEST_WORST_YEAR_LCB_PER_EXPECTED_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["abcd_policy"]={"training_selected_subset_eligibility":True,"min_training_n":ABCD_TRAIN_MIN_N,
                        "min_training_pf_r":ABCD_TRAIN_MIN_PF,"mean_r_gt":0.0,"lcb95_gt":0.0,
                        "rule":"STANDALONE_ABCD_CAN_ENTER_TEST_YEAR_ONLY_IF_THE_FROZEN_MODEL_SELECTED_ABCD_SUBSET_IN_PRIOR_TRAINING_WINDOWS_PROVES_POSITIVE_MEAN_PF_AND_LCB;_TEST_YEAR_NEVER_CONTROLS_ELIGIBILITY"}
summary["gate_semantics"]="EACH_BURNED_YEAR_N_GE_250_MEAN_R_GE_0P90_PF_R_GE_3P30_WR_GE_70PCT_AVG_RR_GE_2P30_LCB95_GT_0__FIXED_TRAINING_SCORE_QUANTILE__ABCD_SUBSET_REQUIRES_PRIOR_TRAINING_PROOF"
summary["positive_asset"]="A_FORMALLY_OOF_ALPHA_CHAMPION_WITH_BUFFER_ABOVE_FINAL_COMMERCIAL_TARGETS" if champion else "NO_MODEL_EARNED_VERSION_PROMOTION"

(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models_blob,separators=(",",":")))
(out/"champion.txt").write_text(champion or "")
(out/"pass.txt").write_text("true" if champion else "false")
print(json.dumps(summary,indent=2))
