#!/usr/bin/env python3
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
YEARS=["Y2021","Y2022","Y2023"]
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30
BASE=[]
for k in SEQUENTIAL_KEYS:
    b=k.rsplit("_F",1)[0]
    if b not in BASE:BASE.append(b)
EVAL=[b+"_F"+f for b in BASE for f in ("00","10","20","30")]
rows=load_rows(root,YEARS)

def route_meta(key):
    return "025" if "_R025_" in key else "050"

def outcome(r,key):
    base,frac=key.rsplit("_F",1); src=key
    if frac in ("00","10"):
        k20=base+"_F20"; k30=base+"_F30"
        y20=r.get("sequential",{}).get(k20); y30=r.get("sequential",{}).get(k30)
        rr=r.get("sequential_rr",{}).get(k20); src=k20
        if y20 is None or y30 is None:return None
        d=float(y30)-float(y20); v=float(y20)-(2.0 if frac=="00" else 1.0)*d
    else:
        v=r.get("sequential",{}).get(key); rr=r.get("sequential_rr",{}).get(key)
    if v is None or rr is None:return None
    try:v=float(v);rr=float(rr)
    except Exception:return None
    if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
    q=dict(r);q["r"]=v;q["oracle_route"]=key;q["oracle_rr"]=rr
    q["bars"]=int(r.get("sequential_bars",{}).get(src,r.get("bars",1)) or 1)
    return q

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)

def margin(m):
    if m["n"]<=0:return -999.0
    vals=[m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,
          m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25]
    return min(vals)

report={"type":"DIAGNOSTIC_FUTURE_ORACLE_ONLY","used_for_alpha_training":False,
        "gate":{"n":MIN_N,"mean_r":MIN_MEAN,"pf_r":MIN_PF,"win_rate":MIN_WR,"average_rr":MIN_RR,"lcb95_gt":0.0},
        "years":{}}
joint=True
for y in YEARS:
    yr=[r for r in rows if r["window"]==y]
    best=[]
    for r in yr:
        cand=[z for k in EVAL if (z:=outcome(r,k)) is not None]
        if not cand:continue
        cand.sort(key=lambda z:(z["r"],z["oracle_rr"],z["oracle_route"]),reverse=True)
        best.append(cand[0])
    best.sort(key=lambda r:(r["r"],r["oracle_rr"],r["setup"]),reverse=True)
    top250=best[:MIN_N]; topm=metrics(top250)
    scan=[]
    best_scan=None
    for n in range(MIN_N,len(best)+1):
        m=metrics(best[:n]); gm=margin(m)
        if best_scan is None or gm>best_scan["margin"]:
            best_scan={"n":n,"margin":gm,"metrics":m,"pass":gate(m)}
        if gate(m):
            scan.append({"n":n,"metrics":m})
            break
    route_counts={};family_counts={};action_counts={}
    for r in top250:
        route_counts[r["oracle_route"]]=route_counts.get(r["oracle_route"],0)+1
        family_counts[r["family"]]=family_counts.get(r["family"],0)+1
        action_counts[r["action"]]=action_counts.get(r["action"],0)+1
    pass_any=bool(scan)
    joint=joint and pass_any
    report["years"][y]={"available_setups":len(best),"top250":topm,"top250_pass":gate(topm),
                        "any_n_ge_250_pass":pass_any,"first_passing":scan[0] if scan else None,
                        "best_gate_margin_scan":best_scan,
                        "top250_route_counts":route_counts,"top250_family_counts":family_counts,
                        "top250_action_counts":action_counts}
report["joint_oracle_gate_3of3"]=joint
report["interpretation"]="ACTION_SPACE_FEASIBLE__SELECTOR_IS_BLOCKER" if joint else "ACTION_SPACE_INFEASIBLE__PAYOFF_GEOMETRY_MUST_CHANGE"
(out/"V74_JOINT_ORACLE_FEASIBILITY.json").write_text(json.dumps(report,indent=2))
(out/"oracle_pass.txt").write_text("true" if joint else "false")
print(json.dumps(report,indent=2))
