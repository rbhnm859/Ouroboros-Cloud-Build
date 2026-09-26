#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); candidate=sys.argv[3]; out.mkdir(parents=True,exist_ok=True)
W=["VAL_Q1_2026","VAL_Q2_2026"]
def find(n):
    xs=list(root.rglob(n))
    if not xs: raise SystemExit("missing "+n)
    return xs[0]
xs={w:json.load(open(find(f"{candidate}-{w}.json"))) for w in W}
rows=[]
for w,x in xs.items():
    for r in x.get("basket_outcomes",[]):
        q=dict(r); q["window"]=w; rows.append(q)
net=sum(r["net"] for r in rows); gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
pf=gp/gl if gl else (999 if gp else 0); n=len(rows)
fam={}
for r in rows: fam.setdefault(r.get("pattern","UNKNOWN"),[]).append(r["net"])
active_family_net={f:sum(v) for f,v in fam.items()}
z={"version":"HarmonyBot V69","candidate":candidate,"stage":"VALIDATION_2026_H1","baskets":n,"net":net,"pf":pf,
   "expectancy":net/n if n else 0,"win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
   "max_dd_pct":max(x["max_dd_pct"] for x in xs.values()),"all_windows_positive":all(x["net"]>0 for x in xs.values()),
   "engineering_clean":all(x["engineering_clean"] for x in xs.values()),
   "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["stop_widening_violations"]==0 for x in xs.values()),
   "unique_thesis":len({(r["window"],r["setup"]) for r in rows})==n,
   "active_family_net":active_family_net,"no_active_family_negative":all(v>=0 for v in active_family_net.values()),
   "windows":{w:{k:xs[w][k] for k in ["baskets","net","pf","expectancy","win_rate","max_dd_pct","engineering_clean"]} for w in W}}
z["pass"]=n>0 and z["all_windows_positive"] and z["pf"]>=2.0 and z["expectancy"]>=20.0 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6.0 and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"] and z["no_active_family_negative"]
(out/"V69_VALIDATION_DECISION.json").write_text(json.dumps(z,indent=2))
(out/"pass.txt").write_text("true" if z["pass"] else "false")
print(json.dumps(z,indent=2))
