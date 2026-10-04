#!/usr/bin/env python3
"""Future-aware diagnostic only: physical feasibility of the V74 action space.
No synthetic/extrapolated route outcome is permitted. Never used for training.
"""
import json,math,pathlib,sys
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS,LATE_AUCTION_KEYS

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
YEARS=["Y2021","Y2022","Y2023"]
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30
def fixed_f30(keys):
    return [k for k in keys if k.endswith("_F30")]
def early_entry_keys(keys):
    # EARLY M05/M10/M15 are post-entry management variants, not Alpha actions.
    # Use one fixed qualification management contract (M15/F30) per true entry identity.
    return [k for k in fixed_f30(keys) if k.startswith("M15_")]
KEYS={"EARLY":early_entry_keys(SEQUENTIAL_KEYS),"LATE":fixed_f30(LATE_AUCTION_KEYS)}
rows=load_rows(root,YEARS)

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def margin(m):
    if m["n"]<=0:return -999.0
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,
               m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25)

def outcome(r,key,src):
    if src=="EARLY":
        om=r.get("sequential",{});rrm=r.get("sequential_rr",{});bm=r.get("sequential_bars",{})
    else:
        om=r.get("late_auction",{});rrm=r.get("late_auction_rr",{});bm=r.get("late_auction_bars",{})
    v=om.get(key);rr=rrm.get(key)
    if v is None or rr is None:return None
    try:v=float(v);rr=float(rr)
    except:return None
    if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
    q=dict(r);q["r"]=v;q["oracle_route"]=src+"|"+key;q["oracle_rr"]=rr
    q["bars"]=int(bm.get(key,r.get("bars",1)) or 1)
    return q

def year_oracle(yr,spaces):
    best=[]
    for r in yr:
        cand=[]
        for src in spaces:
            for k in KEYS[src]:
                z=outcome(r,k,src)
                if z is not None:cand.append(z)
        if not cand:continue
        cand.sort(key=lambda z:(z["r"],z["oracle_rr"],z["oracle_route"]),reverse=True)
        best.append(cand[0])
    best.sort(key=lambda r:(r["r"],r["oracle_rr"],r["setup"]),reverse=True)
    top=best[:MIN_N];topm=metrics(top)
    first=None;scan=None
    for n in range(MIN_N,len(best)+1):
        m=metrics(best[:n])
        if first is None and gate(m):first={"n":n,"metrics":m}
        z={"n":n,"margin":margin(m),"metrics":m,"pass":gate(m)}
        if scan is None or z["margin"]>scan["margin"]:scan=z
    rc={};fc={};ac={};sc={}
    for r in top:
        rc[r["oracle_route"]]=rc.get(r["oracle_route"],0)+1
        fc[r["family"]]=fc.get(r["family"],0)+1
        ac[r["action"]]=ac.get(r["action"],0)+1
        src=r["oracle_route"].split("|",1)[0];sc[src]=sc.get(src,0)+1
    return {"available_setups":len(best),"top250":topm,"top250_pass":gate(topm),
            "any_n_ge_250_pass":first is not None,"first_passing":first,"best_gate_margin_scan":scan,
            "top250_route_counts":rc,"top250_family_counts":fc,"top250_action_counts":ac,"top250_source_counts":sc}

report={"type":"DIAGNOSTIC_FUTURE_ORACLE_ONLY","used_for_alpha_training":False,
        "synthetic_outcomes_used":False,
        "action_space":"EARLY_TRUE_ENTRY_IDENTITY_R_H_RR_PLUS_LATE_MATURITY_ACTIONS_WITH_FIXED_F30_QUALIFICATION","management_variant_selection_used":False,"early_post_entry_m_stage_selection_used":False,
        "gate":{"n":MIN_N,"mean_r":MIN_MEAN,"pf_r":MIN_PF,"win_rate":MIN_WR,"average_rr":MIN_RR,"lcb95_gt":0.0},
        "years":{}}
joint=True
for y in YEARS:
    yr=[r for r in rows if r["window"]==y]
    unified=year_oracle(yr,("EARLY","LATE"))
    early=year_oracle(yr,("EARLY",))
    late=year_oracle(yr,("LATE",))
    report["years"][y]={"unified":unified,"early_only":early,"late_only":late}
    joint=joint and bool(unified["any_n_ge_250_pass"])
report["joint_oracle_gate_3of3"]=joint
report["interpretation"]="CAUSALLY_CLEAN_ENTRY_ACTION_SPACE_FEASIBLE__SELECTOR_IS_BLOCKER" if joint else "CAUSALLY_CLEAN_ENTRY_ACTION_SPACE_INSUFFICIENT__V74_ENTRY_CONFIRMATION_REDESIGN_REQUIRED"
(out/"V74_JOINT_ORACLE_FEASIBILITY.json").write_text(json.dumps(report,indent=2))
(out/"oracle_pass.txt").write_text("true" if joint else "false")
print(json.dumps(report,indent=2))
