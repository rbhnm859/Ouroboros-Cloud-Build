#!/usr/bin/env python3
import json,pathlib,sys
from v74_model_lib import load_rows,predict,fnv64_utf16

root=pathlib.Path(sys.argv[1]); tournament=pathlib.Path(sys.argv[2]); models_path=pathlib.Path(sys.argv[3])
window=sys.argv[4]; out=pathlib.Path(sys.argv[5]); out.mkdir(parents=True,exist_ok=True)
tm=json.load(open(tournament)); mb=json.load(open(models_path)); champ=tm.get("champion")
if not champ: raise SystemExit("no frozen V74 champion")
rows=load_rows(root,[window])
if not rows: raise SystemExit(f"no census rows for {window}")
pack=mb["models"][champ]
model=pack["folds"].get(window,pack["final"])
selected=[]
for r in rows:
    z=predict(champ,model,r)
    if not z.get("selected"):continue
    h=fnv64_utf16(r["setup"])
    selected.append({"setup":r["setup"],"hash":h,"family":r["family"],"action":r["action"],
                     "pred_mean":float(z.get("mean",0.0)),"pred_win":float(z.get("win",0.0)),
                     "pred_lcb":float(z.get("lcb",-999.0)),"pred_hold":float(z.get("hold",180.0)),
                     "support":int(z.get("support",0))})
# One setup can only be selected once even if future telemetry carries multiple representations.
best={}
for r in selected:
    if r["hash"] not in best or (r["pred_lcb"],r["pred_mean"])>(best[r["hash"]]["pred_lcb"],best[r["hash"]]["pred_mean"]):
        best[r["hash"]]=r
selected=sorted(best.values(),key=lambda x:x["hash"])
if not selected: raise SystemExit(f"frozen V74 champion selected zero opportunities for {window}")
(out/"allowed_hashes.txt").write_text(";".join(x["hash"] for x in selected))
(out/"utility_map.txt").write_text(";".join(f'{x["hash"]}={x["pred_lcb"]:.12g}' for x in selected))
(out/"hold_map.txt").write_text(";".join(f'{x["hash"]}={max(1.0,x["pred_hold"]):.12g}' for x in selected))
manifest={"version":"HarmonyBot V74 Frozen Policy","champion":champ,"window":window,
          "model_source":"OOF_FOLD" if window in pack["folds"] else "FROZEN_FINAL_2016_2023",
          "selected_n":len(selected),"selected":selected,
          "outcome_fields_used_for_selection":False,
          "selection_inputs":"PRE_ENTRY_FEATURES_FAMILY_ACTION_ONLY",
          "validation_used":window.startswith("Q1") or window.startswith("Q2"),
          "fresh_used":window.startswith("Q3")}
(out/"V74_POLICY.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:manifest[k] for k in ["champion","window","model_source","selected_n"]},indent=2))
