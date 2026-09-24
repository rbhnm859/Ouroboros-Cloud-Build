#!/usr/bin/env python3
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True); rows=[]
for p in sorted(root.rglob("*.json")):
 try:d=json.load(open(p))
 except:continue
 if "basket_outcomes" in d: rows.append({k:d.get(k) for k in ["variant","window","baskets","net","pf","expectancy","max_dd_pct"]})
config={"architectures":["V51 exact","DAG single-entry","V61 current grid","front-loaded 70/20/10","conditional 60/25/15 + L3 shadow","conditional structural exit","conditional runner","pattern-native"],"right_tail_min_ratio":.80,"whole_basket_risk_max_pct":1.0,"standalone_abcd_capital":False,"fresh_used":False}
raw=json.dumps(config,sort_keys=True,separators=(",",":")).encode(); rep={"version":"HarmonyBot V62","calibration_window":"2021-2023 burned","observations":rows,"frozen_config":config,"config_sha256":hashlib.sha256(raw).hexdigest(),"status":"CALIBRATION_CONFIG_FROZEN"}
(out/"V62_CALIBRATION_MANIFEST.json").write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2))