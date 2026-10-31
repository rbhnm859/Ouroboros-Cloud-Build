#!/usr/bin/env python3
import json,pathlib,sys,math,statistics,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V69_CONTROL","B_HARD_VETO_RATIONALIZED","C_FAMILY_ROUTE_RECONSTRUCTED","D_OPPORTUNITY_COST"]
CAL=["Y2021","Y2022","Y2023"]; DEV=["H2024H2","H2025H1","H2025H2"]
DUR={"Y2021":1.0,"Y2022":1.0,"Y2023":1.0,"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}
V51={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}

def find(name):
    xs=list(root.rglob(name))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
    return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
R={(v,w):rd(v,w) for v in V for w in CAL+DEV}
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def aggregate(v,windows):
    rows=[]
    for w in windows:
        for r in R[(v,w)].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    years=sum(DUR[w] for w in windows); n=len(rows); net=sum(r["net"] for r in rows)
    return {
      "baskets":n,"years":years,"frequency":n/years if years else 0,"net":net,"pf":pf(rows),
      "expectancy":net/n if n else 0,"win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "max_dd_pct":max((R[(v,w)]["max_dd_pct"] for w in windows),default=0),
      "all_windows_positive":all(R[(v,w)]["net"]>0 for w in windows),
      "engineering_clean":all(R[(v,w)]["engineering_clean"] for w in windows),
      "risk_clean":all(R[(v,w)]["actual_basket_risk_violations"]==0 and R[(v,w)]["margin_risk_violations"]==0 and R[(v,w)]["stop_widening_violations"]==0 for w in windows),
      "identity_clean":all(R[(v,w)]["identity_clean"] and abs(R[(v,w)]["canonical_family_coverage"]-1.0)<=1e-12 for w in windows),
      "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean","identity_clean"]} for w in windows},
      "_rows":rows
    }
def cohort(rows,families):
    z=[r for r in rows if r.get("family_id") in families]
    return {"baskets":len(z),"net":sum(r["net"] for r in z),"pf":pf(z),"expectancy":sum(r["net"] for r in z)/len(z) if z else 0}
def key(r):
    return (r.get("window",""),r.get("canonical_setup",""),r.get("family_id",""),r.get("route",""))
def marginal(fr,to,windows):
    a=aggregate(fr,windows); b=aggregate(to,windows)
    x={key(r):r for r in a["_rows"]}; y={key(r):r for r in b["_rows"]}
    added=[r for k,r in y.items() if k not in x]; removed=[r for k,r in x.items() if k not in y]
    common=[(x[k],y[k]) for k in x.keys()&y.keys()]
    return {"from":fr,"to":to,
      "delta_baskets":b["baskets"]-a["baskets"],"delta_net":b["net"]-a["net"],"delta_pf":b["pf"]-a["pf"],"delta_expectancy":b["expectancy"]-a["expectancy"],
      "added_count":len(added),"added_net":sum(r["net"] for r in added),"added_pf":pf(added),
      "removed_count":len(removed),"removed_net":sum(r["net"] for r in removed),"removed_pf":pf(removed),
      "matched_net_delta":sum(y["net"]-x["net"] for x,y in common)}

A={v:{"calibration":aggregate(v,CAL),"dev":aggregate(v,DEV)} for v in V}
control_protected=cohort(A[V[0]]["dev"]["_rows"],{"Rat","Shark"})
for v in V:
    p=cohort(A[v]["dev"]["_rows"],{"Rat","Shark"})
    A[v]["protected_rat_shark"]=p
    A[v]["protected_do_no_harm"]=p["net"]+0.05>=control_protected["net"] and p["pf"]+0.0005>=control_protected["pf"]

M={
 "B-A":marginal(V[0],V[1],DEV),
 "C-B":marginal(V[1],V[2],DEV),
 "D-C":marginal(V[2],V[3],DEV)
}

def commercial(z):
    return z["baskets"]<=90 and z["frequency"]<=60 and z["net"]>=1800 and z["pf"]>=2 and z["expectancy"]>=20 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6 and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["identity_clean"]
def superior(z):
    return z["frequency"]>V51["frequency"] and z["net"]>V51["net"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["max_dd_pct"]<=V51["max_dd_pct"]

for v in V:
    z=A[v]["dev"]; z["commercial_gate"]=commercial(z); z["v51_superiority_gate"]=superior(z)

gate_c=M["C-B"]["delta_net"]>0 and M["C-B"]["delta_pf"]>=-1e-12 and M["C-B"]["delta_expectancy"]>=-1e-12 and M["C-B"]["added_count"]>0 and M["C-B"]["added_net"]>0 and A[V[2]]["protected_do_no_harm"] and A[V[2]]["dev"]["engineering_clean"] and A[V[2]]["dev"]["risk_clean"]
gate_d=M["D-C"]["delta_net"]>0 and M["D-C"]["delta_pf"]>=-1e-12 and M["D-C"]["delta_expectancy"]>=-1e-12 and A[V[3]]["protected_do_no_harm"] and A[V[3]]["dev"]["engineering_clean"] and A[V[3]]["dev"]["risk_clean"]

filters={}
shadow_by_reason={}
for v in V:
    f=collections.defaultdict(lambda:{"observed":0,"pass":0,"blocked":0,"converted_to_observation":0})
    sr=collections.defaultdict(list)
    for w in CAL+DEV:
        d=R[(v,w)]
        for name,x in d.get("filter_evidence",{}).items():
            for k in f[name]: f[name][k]+=int(x.get(k,0))
        for x in d.get("shadow_outcomes",[]):
            sr[(x.get("family_id","Unknown"),x.get("terminal_reason","UNKNOWN"))].append(float(x.get("outcome_r",0)))
    filters[v]=dict(f)
    shadow_by_reason[v]=[{"family_id":k[0],"terminal_reason":k[1],"count":len(xs),"mean_r":statistics.mean(xs),"pf_r":pf([{"net":x} for x in xs])} for k,xs in sorted(sr.items()) if xs]

candidate=None
if gate_c and A[V[2]]["dev"]["commercial_gate"] and A[V[2]]["dev"]["v51_superiority_gate"]: candidate=V[2]
if gate_d and A[V[3]]["dev"]["commercial_gate"] and A[V[3]]["dev"]["v51_superiority_gate"]: candidate=V[3]

for v in V:
    A[v]["calibration"].pop("_rows",None); A[v]["dev"].pop("_rows",None)

decision="DEV_CANDIDATE_PASS" if candidate else "HOLD_WITH_EVIDENCE"
front={"version":"HarmonyBot V70","stage":"CAUSAL_ADMISSION_DEV","calibration_windows":CAL,"promotion_dev_windows":DEV,
 "fresh_used":False,"validation_used":False,"grid_changed":False,"exit_changed":False,
 "variants":A,"marginal":M,"c_family_route_gate":gate_c,"d_opportunity_cost_gate":gate_d,
 "development_candidate":candidate,"decision":decision,"v51_superiority_reference":V51}
(out/"V70_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V70_FILTER_MARGINAL_EVIDENCE.json").write_text(json.dumps({"filters":filters,"shadow_by_terminal_reason":shadow_by_reason},indent=2))
(out/"V70_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V70","decision":decision,"candidate":candidate,"validation_used":False,"fresh_used":False},indent=2))
(out/"candidate.txt").write_text(candidate or "")
print(json.dumps(front,indent=2))
