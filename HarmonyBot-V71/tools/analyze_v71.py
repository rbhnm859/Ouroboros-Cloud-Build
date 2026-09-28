#!/usr/bin/env python3
import json,pathlib,sys,statistics,collections,datetime
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V70_TRUTH_CONTROL","B_NEGATIVE_LANE_SUPPRESSED","C_SELECTIVE_ALPHA_RECALL","D_FAMILY_NATIVE_GRID_AMPLIFIER"]
CAL=["Y2021","Y2022","Y2023"]; DEV=["H2024H2","H2025H1","H2025H2"]; ALL=CAL+DEV
DUR={"Y2021":1.0,"Y2022":1.0,"Y2023":1.0,"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}
STARTING_BALANCE=10000.0
CONTROL_REF={
"Y2021":{"baskets":164,"net":1561.19,"pf":1.2388820883190013},
"Y2022":{"baskets":144,"net":530.86,"pf":1.0756123581182229},
"Y2023":{"baskets":58,"net":-777.03,"pf":0.713987566117117},
"H2024H2":{"baskets":65,"net":355.52,"pf":1.1473694682562052},
"H2025H1":{"baskets":70,"net":-121.39,"pf":0.9519022751226315},
"H2025H2":{"baskets":15,"net":-884.85,"pf":0.32696695874406717}}

def find(name):
    xs=list(root.rglob(name))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
    return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
R={(v,w):rd(v,w) for v in V for w in ALL}
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def realized_rr(rows):
    wins=[r.get("r") for r in rows if isinstance(r.get("r"),(int,float)) and r.get("r")>0]
    losses=[r.get("r") for r in rows if isinstance(r.get("r"),(int,float)) and r.get("r")<0]
    cov=(len(wins)+len(losses))/len(rows) if rows else 0
    rr=(statistics.mean(wins)/abs(statistics.mean(losses))) if wins and losses and statistics.mean(losses)!=0 else 0
    return rr,cov
def month_key(v):
    if not isinstance(v,(int,float)) or v<=0:return None
    try:
        sec=v/1000.0 if v>1e11 else v
        d=datetime.datetime.utcfromtimestamp(sec); return f"{d.year:04d}-{d.month:02d}"
    except:return None
def monthly(rows):
    m=collections.defaultdict(float)
    for r in rows:
        k=month_key(r.get("entry_time"))
        if k:m[k]+=r["net"]
    ks=sorted(m); latest=ks[-12:] if len(ks)>=12 else ks
    return {"months_observed":len(ks),"latest_12_months":latest,"profitable_latest_12":sum(m[k]>0 for k in latest),"monthly_net":dict(sorted(m.items()))}
def aggregate(v,windows):
    rows=[]
    for w in windows:
        for r in R[(v,w)].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    years=sum(DUR[w] for w in windows); n=len(rows); net=sum(r["net"] for r in rows)
    rr,rrcov=realized_rr(rows); mon=monthly(rows)
    return {"baskets":n,"years":years,"frequency":n/years if years else 0,"net":net,"pf":pf(rows),
      "expectancy":net/n if n else 0,"win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "max_dd_pct":max((R[(v,w)]["max_dd_pct"] for w in windows),default=0),
      "positive_windows":sum(R[(v,w)]["net"]>0 for w in windows),"all_windows_positive":all(R[(v,w)]["net"]>0 for w in windows),
      "engineering_clean":all(R[(v,w)]["engineering_clean"] for w in windows),
      "risk_clean":all(R[(v,w)]["actual_basket_risk_violations"]==0 and R[(v,w)]["margin_risk_violations"]==0 and R[(v,w)]["stop_widening_violations"]==0 for w in windows),
      "identity_clean":all(R[(v,w)]["identity_clean"] and abs(R[(v,w)]["canonical_family_coverage"]-1.0)<=1e-12 for w in windows),
      "realized_rr":rr,"realized_rr_coverage":rrcov,"profitable_months_latest_12":mon["profitable_latest_12"],"months_observed":mon["months_observed"],
      "simple_annualized_return_pct":(net/STARTING_BALANCE/years*100.0) if years else 0,
      "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean","identity_clean"]} for w in windows},
      "_rows":rows,"_monthly":mon}
def cohort(rows,fams):
    z=[r for r in rows if r.get("family_id") in fams]
    return {"baskets":len(z),"net":sum(r["net"] for r in z),"pf":pf(z),"expectancy":sum(r["net"] for r in z)/len(z) if z else 0}
def key(r): return (r.get("window",""),r.get("canonical_setup",""),r.get("family_id",""),r.get("route",""))
def marginal(fr,to,windows):
    a=aggregate(fr,windows); b=aggregate(to,windows); x={key(r):r for r in a["_rows"]}; y={key(r):r for r in b["_rows"]}
    added=[r for k,r in y.items() if k not in x]; removed=[r for k,r in x.items() if k not in y]; common=[(x[k],y[k]) for k in x.keys()&y.keys()]
    return {"from":fr,"to":to,"delta_baskets":b["baskets"]-a["baskets"],"delta_net":b["net"]-a["net"],"delta_pf":b["pf"]-a["pf"],"delta_expectancy":b["expectancy"]-a["expectancy"],
      "positive_delta_windows":sum(R[(to,w)]["net"]>R[(fr,w)]["net"] for w in windows),
      "added_count":len(added),"added_net":sum(r["net"] for r in added),"added_pf":pf(added),
      "removed_count":len(removed),"removed_net":sum(r["net"] for r in removed),"removed_pf":pf(removed),
      "matched_net_delta":sum(y0["net"]-x0["net"] for x0,y0 in common)}
def counters(v,windows):
    keys=["suppressed_legacy_lanes","selective_quality_recalls","selective_route_recalls","grid_amplified_plans"]
    return {k:sum(int(R[(v,w)].get(k,0)) for w in windows) for k in keys}
def clean(z): return z["engineering_clean"] and z["risk_clean"] and z["identity_clean"]

control_reproduction={}
for w,ref in CONTROL_REF.items():
    x=R[(V[0],w)]
    control_reproduction[w]=bool(x["baskets"]==ref["baskets"] and abs(x["net"]-ref["net"])<=0.02 and abs(x["pf"]-ref["pf"])<=1e-9 and x["engineering_clean"] and x["identity_clean"])
control_gate=all(control_reproduction.values())

A={v:{"calibration":aggregate(v,CAL),"dev":aggregate(v,DEV),"counters_calibration":counters(v,CAL),"counters_dev":counters(v,DEV)} for v in V}
base_protected=cohort(A[V[0]]["dev"]["_rows"],{"Rat","Shark"})
for v in V:
    p=cohort(A[v]["dev"]["_rows"],{"Rat","Shark"}); A[v]["protected_rat_shark"]=p
    A[v]["protected_vs_control_no_harm"]=p["net"]+0.05>=base_protected["net"] and p["pf"]+0.0005>=base_protected["pf"]

M={"B-A":marginal(V[0],V[1],DEV),"C-B":marginal(V[1],V[2],DEV),"D-C":marginal(V[2],V[3],DEV)}
B_GATE=control_gate and M["B-A"]["delta_net"]>0 and M["B-A"]["delta_pf"]>0 and M["B-A"]["delta_expectancy"]>0 and M["B-A"]["removed_count"]>0 and M["B-A"]["removed_net"]<0 and M["B-A"]["added_count"]==0 and M["B-A"]["positive_delta_windows"]>=2 and A[V[1]]["protected_vs_control_no_harm"] and clean(A[V[1]]["dev"])
C_GATE=B_GATE and M["C-B"]["delta_net"]>0 and M["C-B"]["delta_pf"]>=-1e-12 and M["C-B"]["delta_expectancy"]>=-1e-12 and M["C-B"]["added_count"]>0 and M["C-B"]["added_net"]>0 and M["C-B"]["added_pf"]>1 and M["C-B"]["positive_delta_windows"]>=2 and A[V[2]]["protected_vs_control_no_harm"] and clean(A[V[2]]["dev"])
cprot=A[V[2]]["protected_rat_shark"]; dprot=A[V[3]]["protected_rat_shark"]
D_PROTECTED_NO_HARM=dprot["net"]+0.05>=cprot["net"] and dprot["pf"]+0.0005>=cprot["pf"]
D_GATE=C_GATE and M["D-C"]["delta_net"]>0 and M["D-C"]["delta_pf"]>=-1e-12 and M["D-C"]["delta_expectancy"]>=-1e-12 and M["D-C"]["positive_delta_windows"]>=2 and A[V[3]]["counters_dev"]["grid_amplified_plans"]>0 and D_PROTECTED_NO_HARM and clean(A[V[3]]["dev"])

def breakthrough(z,gate): return bool(gate and z["net"]>0 and z["pf"]>=1.10 and z["expectancy"]>0 and z["max_dd_pct"]<=10 and z["positive_windows"]>=2 and clean(z))
candidate=None
for v,g in [(V[3],D_GATE),(V[2],C_GATE),(V[1],B_GATE)]:
    if breakthrough(A[v]["dev"],g): candidate=v; break
def final_target(z):
    return {"return_ge_100":z["simple_annualized_return_pct"]>=100,"pf_ge_2_5":z["pf"]>=2.5,"max_dd_le_10":z["max_dd_pct"]<=10,
      "win_rate_ge_65":z["win_rate"]>=.65,"trades_ge_200y":z["frequency"]>=200,
      "realized_rr_ge_2":z["realized_rr_coverage"]>=.80 and z["realized_rr"]>=2,
      "profitable_months_ge_10_of_12":z["months_observed"]>=12 and z["profitable_months_latest_12"]>=10,
      "net_profit_ge_100pct_initial_annualized":z["simple_annualized_return_pct"]>=100}
for v in V:
    A[v]["dev"]["final_v80_target_dev_only"]=final_target(A[v]["dev"])
    A[v]["calibration"].pop("_rows",None); A[v]["dev"].pop("_rows",None); A[v]["calibration"].pop("_monthly",None); A[v]["dev"].pop("_monthly",None)
decision="BREAKTHROUGH_PASS" if candidate else "HOLD_WITH_EVIDENCE"
front={"version":"HarmonyBot V71","stage":"SELECTIVE_CAUSAL_ALPHA_GRID_DEV","control_reproduction_gate":control_gate,"control_reproduction":control_reproduction,
 "calibration_windows":CAL,"promotion_dev_windows":DEV,"validation_used":False,"fresh_used":False,"variants":A,"marginal":M,
 "gates":{"B_negative_lane_suppression":B_GATE,"C_selective_recall":C_GATE,"D_grid_amplifier":D_GATE,"D_protected_no_harm_vs_C":D_PROTECTED_NO_HARM},
 "breakthrough_candidate":candidate,"decision":decision,
 "final_v80_targets":{"return_pct":100,"pf":2.5,"max_dd_pct":10,"win_rate":.65,"frequency":200,"realized_rr":2.0,"profitable_months_12":10,"net_pct_initial":100},
 "governance":{"validation_locked":True,"fresh_locked":True,"no_minor_version_promotion":True,"grid_role":"FAMILY_NATIVE_PROFIT_AMPLIFIER_NOT_FILTER"}}
(out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V71_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V71","decision":decision,"candidate":candidate,"validation_used":False,"fresh_used":False},indent=2))
(out/"candidate.txt").write_text(candidate or "")
print(json.dumps(front,indent=2))
