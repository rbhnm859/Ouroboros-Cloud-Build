#!/usr/bin/env python3
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True); rows=[]
for p in sorted(root.rglob("*.json")):
 try:d=json.load(open(p))
 except:continue
 if "basket_outcomes" in d: rows.append({"variant":d.get("variant"),"window":d.get("window"),"baskets":d.get("baskets"),"net":d.get("net"),"pf":d.get("pf"),"expectancy":d.get("expectancy"),"max_dd_pct":d.get("max_dd_pct")})
config={"grid":{"Trend":[0,.236,.382,.618],"TrendWeights":[.40,.30,.20,.10],"Exhaustion":[0,.236],"ExhaustionWeights":[.65,.35],"Transition":[0,.236,.382],"TransitionWeights":[.50,.30,.20]},"regime_threshold":.65,"rat":{"geometry":.72,"prz":.72,"confidence":.68},"runner":{"minimum_r":3.0,"exhaustion":False},"standalone_abcd_capital":False}; raw=json.dumps(config,sort_keys=True,separators=(",",":")).encode()
rep={"version":"HarmonyBot V61","calibration_window":"2021-2023 burned","temporal_folds":["C1","C2","C3"],"observations":rows,"frozen_config":config,"config_sha256":hashlib.sha256(raw).hexdigest(),"fresh_used":False,"status":"CALIBRATION_CONFIG_FROZEN"}; (out/"V61_CALIBRATION_MANIFEST.json").write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2))
