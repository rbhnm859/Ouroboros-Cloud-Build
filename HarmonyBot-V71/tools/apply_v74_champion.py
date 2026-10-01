#!/usr/bin/env python3
import json,pathlib,sys
from v74_model_lib import load_rows,predict,pred_protection,PROTECTION_KEYS,fnv64_utf16

root=pathlib.Path(sys.argv[1]); tournament=pathlib.Path(sys.argv[2]); models_path=pathlib.Path(sys.argv[3])
window=sys.argv[4]; out=pathlib.Path(sys.argv[5]); out.mkdir(parents=True,exist_ok=True)
tm=json.load(open(tournament)); mb=json.load(open(models_path)); champ=tm.get("champion")
if not champ: raise SystemExit("no frozen V74 champion")
rows=load_rows(root,[window])
if not rows: raise SystemExit(f"no census rows for {window}")
pack=mb["models"][champ]
fold_meta=tm.get("models",{}).get(champ,{}).get("folds",{}).get(window,{})
is_rcr=str(pack.get("type","")).upper()=="REACTION_CONFIRMED_REENTRY" or champ.startswith(("D_REACTION_CONFIRMED_REENTRY","E_REACTION_CONFIRMED_REENTRY"))

selected=[]
if is_rcr:
    policy=pack.get("folds",{}).get(window,pack.get("final",{}))
    global_route=policy.get("global_route")
    route_policy=policy.get("route_policy",{}) or {}
    abcd_allowed=bool(policy.get("abcd_capital_eligible",
                      fold_meta.get("abcd_training_capital_eligible",
                      pack.get("abcd_final_capital_eligible",False))))
    for r in rows:
        reaction_key=route_policy.get(r["family"]+"|"+r["action"],global_route)
        if not reaction_key: continue
        if r["family"]=="ABCD" and not abcd_allowed: continue
        h=fnv64_utf16(r["setup"])
        selected.append({"setup":r["setup"],"hash":h,"family":r["family"],"action":r["action"],
                         "pred_mean":0.0,"pred_win":0.0,"pred_lcb":1.0,"pred_hold":180.0,
                         "support":0,"protection_key":"NONE","reaction_key":reaction_key,
                         "protection_pred_delta":0.0,"protection_lcb_delta":0.0})
else:
    model=pack["folds"].get(window,pack["final"])
    protection=pack.get("protection_folds",{}).get(window,pack.get("protection_final",{}))
    abcd_allowed=bool(fold_meta.get("abcd_training_capital_eligible",
                      pack.get("abcd_final_capital_eligible",
                               tm.get("models",{}).get(champ,{}).get("abcd_final_capital_eligible",False))))
    for r in rows:
        z=predict(champ,model,r)
        if not z.get("selected"):continue
        if r["family"]=="ABCD" and not abcd_allowed: continue
        h=fnv64_utf16(r["setup"])
        protection_key="NONE"; protection_delta=0.0; protection_lcb=-999.0
        for key in PROTECTION_KEYS:
            if key not in r.get("milestones",{}): continue
            pm=protection.get(key)
            if not pm: continue
            pz=pred_protection(pm,r)
            if pz.get("protect"):
                protection_key=key
                protection_delta=float(pz.get("delta",0.0))
                protection_lcb=float(pz.get("lcb",-999.0))
                break
        selected.append({"setup":r["setup"],"hash":h,"family":r["family"],"action":r["action"],
                         "pred_mean":float(z.get("mean",0.0)),"pred_win":float(z.get("win",0.0)),
                         "pred_lcb":float(z.get("lcb",-999.0)),"pred_hold":float(z.get("hold",180.0)),
                         "support":int(z.get("support",0)),"protection_key":protection_key,
                         "reaction_key":"NONE",
                         "protection_pred_delta":protection_delta,"protection_lcb_delta":protection_lcb})

# One setup can only be selected once. No test-year outcome field participates in selection.
best={}
for r in selected:
    if r["hash"] not in best or (r["pred_lcb"],r["pred_mean"])>(best[r["hash"]]["pred_lcb"],best[r["hash"]]["pred_mean"]):
        best[r["hash"]]=r
selected=sorted(best.values(),key=lambda x:x["hash"])
if not selected: raise SystemExit(f"frozen V74 champion selected zero opportunities for {window}")
(out/"allowed_hashes.txt").write_text(";".join(x["hash"] for x in selected))
(out/"utility_map.txt").write_text(";".join(f'{x["hash"]}={x["pred_lcb"]:.12g}' for x in selected))
(out/"hold_map.txt").write_text(";".join(f'{x["hash"]}={max(1.0,x["pred_hold"]):.12g}' for x in selected))
(out/"protection_map.txt").write_text(";".join(f'{x["hash"]}={x["protection_key"]}' for x in selected))
(out/"reaction_map.txt").write_text(";".join(f'{x["hash"]}={x["reaction_key"]}' for x in selected if x.get("reaction_key") not in (None,"","NONE")))
manifest={"version":"HarmonyBot V74 Frozen Policy","champion":champ,"window":window,
          "model_source":"OOF_FOLD" if window in pack.get("folds",{}) else "FROZEN_FINAL_2016_2023",
          "selected_n":len(selected),"abcd_capital_allowed":abcd_allowed,"selected":selected,
          "outcome_fields_used_for_selection":False,
          "selection_inputs":"TRAINING_ONLY_RCR_ROUTE_FAMILY_ACTION" if is_rcr else "PRE_ENTRY_40D_FEATURES_FAMILY_ACTION_PLUS_COMPLETED_BAR_MILESTONE_PROTECTION",
          "capital_entry_semantics":"DEFER_UNTIL_COMPLETED_BAR_REACTION_RETRACE_RECLAIM" if is_rcr else "FROZEN_NATIVE_ENTRY",
          "protection_activation":"NEXT_COMPLETED_M1_BAR_AFTER_SELECTED_MILESTONE",
          "validation_used":window.startswith("Q1") or window.startswith("Q2"),
          "fresh_used":window.startswith("Q3")}
(out/"V74_POLICY.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:manifest[k] for k in ["champion","window","model_source","selected_n","capital_entry_semantics"]},indent=2))
