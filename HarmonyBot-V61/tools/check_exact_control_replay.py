#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
def load(prefix,w):
 xs=list(root.rglob(f"{prefix}-{w}.json"))
 if not xs: raise SystemExit("missing "+prefix+" "+w)
 return json.load(open(xs[0]))
def agg(prefix):
 rows=[load(prefix,w) for w in "ABC"]; b=[x for r in rows for x in r.get("basket_outcomes",[])]; v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0)); n=len(b)
 return {"baskets":n,"net":sum(v),"pf":gp/gl if gl else 999,"expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,"max_dd_pct":max(r["max_dd_pct"] for r in rows),"windows_positive":all(r["net"]>0 for r in rows),"engineering_clean":all(r["engineering_clean"] for r in rows)}
expected={"baskets":58,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}; v51=agg("FAMILY_NATIVE_MATH_GEOMETRY"); v61=agg("V61_V51_EXACT_CONTROL")
def near(z): return z["baskets"]==58 and abs(z["net"]-expected["net"])<=.30 and abs(z["pf"]-expected["pf"])<=.006 and abs(z["expectancy"]-expected["expectancy"])<=.08 and abs(z["win_rate"]-expected["win_rate"])<=.002 and abs(z["max_dd_pct"]-expected["max_dd_pct"])<=.02 and z["windows_positive"] and z["engineering_clean"]
equiv=v51["baskets"]==v61["baskets"] and abs(v51["net"]-v61["net"])<=.05 and abs(v51["pf"]-v61["pf"])<=.001 and abs(v51["expectancy"]-v61["expectancy"])<=.02 and abs(v51["win_rate"]-v61["win_rate"])<=.0005 and abs(v51["max_dd_pct"]-v61["max_dd_pct"])<=.01; ok=near(v51) and near(v61) and equiv
rep={"version":"HarmonyBot V61","expected_v51":expected,"immutable_v51":v51,"v61_exact_control":v61,"dynamic_equivalence":equiv,"pass":ok}; (out/"V61_V51_EXACT_CONTROL_REPLAY.json").write_text(json.dumps(rep,indent=2)); (out/"replay.out").write_text("true" if ok else "false"); print(json.dumps(rep,indent=2))
if not ok: raise SystemExit("V61 exact-control replay mismatch")
