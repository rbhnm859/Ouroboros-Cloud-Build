#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); candidate=sys.argv[3]; out.mkdir(parents=True,exist_ok=True)
xs=list(root.rglob(f"{candidate}-FRESH_2020H1.json"))
if not xs: raise SystemExit("missing fresh result")
x=json.load(open(xs[0])); rows=x.get("basket_outcomes",[]); n=len(rows)
fam={}
for r in rows: fam.setdefault(r.get("pattern","UNKNOWN"),[]).append(r["net"])
active_family_net={f:sum(v) for f,v in fam.items()}
z={"version":"HarmonyBot V69","candidate":candidate,"stage":"FRESH_2020H1","baskets":n,"net":x["net"],"pf":x["pf"],"expectancy":x["expectancy"],"win_rate":x["win_rate"],"max_dd_pct":x["max_dd_pct"],
   "engineering_clean":x["engineering_clean"],"risk_clean":x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["stop_widening_violations"]==0,
   "unique_thesis":x.get("unique_setups",n)==n,"active_family_net":active_family_net,"no_active_family_negative":all(v>=0 for v in active_family_net.values())}
z["pass"]=n>0 and z["net"]>0 and z["pf"]>=1.5 and z["expectancy"]>0 and z["max_dd_pct"]<=6.0 and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"] and z["no_active_family_negative"]
(out/"V69_FRESH_DECISION.json").write_text(json.dumps(z,indent=2))
(out/"pass.txt").write_text("true" if z["pass"] else "false")
print(json.dumps(z,indent=2))
