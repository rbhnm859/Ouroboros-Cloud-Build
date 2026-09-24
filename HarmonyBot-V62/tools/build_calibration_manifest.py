#!/usr/bin/env python3
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);rows=[]
for f in root.rglob("*.json"):
 try:d=json.load(open(f))
 except:continue
 if "basket_outcomes" in d:rows.append(d)
frozen={"version":"HarmonyBot V62","calibration_period":"2021-2023","architecture":"A-H preregistered causal matrix","variants":sorted({x.get("variant","") for x in rows}),"conditional_grid":{"weights":[.60,.25,.15],"levels":[0,.236,.382],"l3_0618":"shadow_only","target_basis":"primary_L0_anchor"},"front_loaded":{"weights":[.70,.20,.10],"levels":[0,.236,.382]},"runner":{"canonical_l0":.45,"runner_l0":.15,"deep":[.25,.15],"minimum_r":3.0,"independent_lifecycle":True},"pattern_native":{"capital_evidence":["Rat","Shark","Cypher","5-0"],"abcd_standalone":False},"right_tail_min_ratio":.80,"risk":{"basket_risk_pct":1.0,"min_net_rr":2.0},"fresh_used":False}
frozen["manifest_sha256"]=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
(out/"V62_CALIBRATION_FREEZE.json").write_text(json.dumps({"frozen":frozen,"calibration_rows":rows},indent=2));print(json.dumps(frozen,indent=2))
