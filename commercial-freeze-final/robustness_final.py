#!/usr/bin/env python3
import argparse,glob,json,statistics,random,pathlib
ap=argparse.ArgumentParser(); ap.add_argument("--dir",required=True); ap.add_argument("--out",required=True)
a=ap.parse_args()
rows=[]
for p in glob.glob(str(pathlib.Path(a.dir)/"ROBUST-*.json")):
    x=json.load(open(p))
    if x.get("status")=="OK": rows.append(x)
by={x["window"]:x for x in rows}
expected={"BASE","QUALITY_080","QUALITY_090","QUALITY_095","QUALITY_105","QUALITY_110","QUALITY_120","SPREAD_150","COMMISSION_150","SLIPPAGE_150","COMBINED_COST"}
matrix_ok=bool(set(by)==expected and all(x["pf"]>=0.90 and x["max_dd_pct"]<=10 and x["execution_errors"]==0 for x in rows)
    and statistics.median([x["pf"] for x in rows])>1.0 and by["BASE"]["pf"]>1.0 and by["BASE"]["expectancy"]>0)
nets=by.get("BASE",{}).get("basket_nets",[])
random.seed(5656); dd95=999.0; ruin=1.0; p5_total=-1e99
if nets:
    dds=[]; totals=[]; ruins=0
    for _ in range(5000):
        eq=10000.0; peak=eq; mdd=0.0; ruined=False
        for v in random.choices(nets,k=len(nets)):
            eq+=v; peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak*100 if peak else 100)
            if eq<=0 and not ruined: ruined=True; ruins+=1
        dds.append(mdd); totals.append(eq-10000.0)
    dds.sort(); totals.sort()
    dd95=dds[int(.95*(len(dds)-1))]; p5_total=totals[int(.05*(len(totals)-1))]; ruin=ruins/5000
mc_ok=bool(dd95<=15 and ruin<=0.01)
out={"robustness_pass":bool(matrix_ok and mc_ok),"matrix_pass":matrix_ok,"monte_carlo_pass":mc_ok,
     "mc_95pct_max_dd":dd95,"mc_5pct_total_net":p5_total,"mc_risk_of_ruin":ruin,"rows":by}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
