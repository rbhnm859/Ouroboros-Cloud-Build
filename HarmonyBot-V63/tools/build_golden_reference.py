#!/usr/bin/env python3
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
rows=[]
for w in "ABC":
 xs=list(root.rglob(f"FAMILY_NATIVE_MATH_GEOMETRY-{w}.json"))
 if not xs: raise SystemExit("missing golden "+w)
 rows.append(json.load(open(xs[0])))
b=[x for r in rows for x in r.get("basket_outcomes",[])]; v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0)); n=len(b)
g={"version":"V51_GOLDEN_DEV","source_blob":"be800fc0ff2a1ca83282af818abdfb6e945a512f","windows":{"A":rows[0],"B":rows[1],"C":rows[2]},"baskets":n,"frequency":n/1.5,"net":sum(v),"pf":gp/gl if gl else 999,"expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,"max_dd_pct":max(r["max_dd_pct"] for r in rows),"all_windows_positive":all(r["net"]>0 for r in rows),"unique_setups":len({x["setup"] for x in b}),"engineering_clean":all(r["engineering_clean"] for r in rows),"risk_clean":all(r.get("actual_basket_risk_violations",0)==0 and r.get("margin_risk_violations",0)==0 for r in rows)}
raw=json.dumps(g,sort_keys=True,separators=(",",":")).encode();g["reference_sha256"]=hashlib.sha256(raw).hexdigest()
(out/"V63_GOLDEN_DEV_REFERENCE.json").write_text(json.dumps(g,indent=2));print(json.dumps(g,indent=2))