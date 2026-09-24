#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True); rows=[]
for p in root.rglob("*.json"):
 try:d=json.load(open(p))
 except:continue
 if "basket_outcomes" in d: rows.append(d)
ok=len(rows)==6 and all(x["engineering_clean"] and x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["baskets"]>0 and x["net"]>0 and x["pf"]>1 and x["expectancy"]>0 for x in rows)
rep={"version":"HarmonyBot V61","validation_rows":rows,"validation_pass":ok,"no_tuning":True,"fresh_used":False}; (out/"V61_VALIDATION_GATE.json").write_text(json.dumps(rep,indent=2)); (out/"validation.out").write_text("true" if ok else "false"); print(json.dumps(rep,indent=2))
if not ok: raise SystemExit("V61 validation HOLD")
