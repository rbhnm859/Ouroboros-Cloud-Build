#!/usr/bin/env python3
import json,pathlib,sys,math,collections,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V52_EXACT_CONTROL","B_FAMILY_GRID_ATLAS","C_POSITIVE_THROUGHPUT","D_FAMILY_PORTFOLIO_MAX"]
W=["Y2021","Y2022","Y2023"]
FAMILIES=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def find(n):
    xs=list(root.rglob(n))
    if not xs: raise SystemExit("missing "+n)
    return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def family_stats(rows):
    out={}
    for fam in FAMILIES:
        rs=[r for r in rows if r.get("pattern")==fam]
        by={w:[r for r in rs if r.get("window")==w] for w in W}
        n=len(rs); net=sum(r["net"] for r in rs)
        positive_years=sum(sum(r["net"] for r in by[w])>0 for w in W)
        active_years=sum(len(by[w])>0 for w in W)
        out[fam]={
          "count":n,"net":net,"pf":pf(rs),"expectancy":net/n if n else 0,
          "win_rate":sum(r["net"]>0 for r in rs)/n if n else 0,
          "positive_years":positive_years,"active_years":active_years,
          "years":{w:{"count":len(by[w]),"net":sum(r["net"] for r in by[w])} for w in W}
        }
    return out
def aggregate(v):
    windows={w:rd(v,w) for w in W}; rows=[]
    for w in W:
        for r in windows[w].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    n=len(rows); net=sum(r["net"] for r in rows); fam=family_stats(rows)
    # A family is commercially meaningful only if it contributes a real positive cohort rather than
    # a one-off winner.  Calibration is burned data, so this is the legal place to enforce breadth.
    pos=[f for f,z in fam.items() if z["count"]>=5 and z["net"]>0 and z["expectancy"]>0 and z["active_years"]>=2 and z["positive_years"]>=1]
    shares={f:(fam[f]["count"]/n if n else 0) for f in FAMILIES}
    maxfam=max(shares,key=shares.get) if shares else None
    return {
      "baskets":n,"frequency":n/3.0,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
      "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "max_dd_pct":max((windows[w]["max_dd_pct"] for w in W),default=0),
      "all_years_positive":all(windows[w]["net"]>0 for w in W),
      "engineering_clean":all(windows[w]["engineering_clean"] for w in W),
      "risk_clean":all(windows[w]["actual_basket_risk_violations"]==0 and windows[w]["margin_risk_violations"]==0 and windows[w]["stop_widening_violations"]==0 for w in W),
      "unique_thesis":len({(r["window"],r["setup"]) for r in rows})==n,
      "family_positive_count":len(pos),"positive_families":pos,"all_12_families_positive":len(pos)==12,
      "family_stats":fam,"family_trade_shares":shares,"largest_family":maxfam,
      "largest_family_share":shares.get(maxfam,0) if maxfam else 0,
      "anti_concentration_pass":shares.get(maxfam,0)<=.35 if maxfam else False,
      "windows":{w:{k:windows[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean"]} for w in W},
      "_rows":rows
    }
A={v:aggregate(v) for v in V}
def marginal(a,b):
    x={(r["window"],r["setup"]):r for r in A[a]["_rows"]}; y={(r["window"],r["setup"]):r for r in A[b]["_rows"]}
    add=[r for k,r in y.items() if k not in x]; rem=[r for k,r in x.items() if k not in y]
    return {"delta_trades":A[b]["baskets"]-A[a]["baskets"],"delta_net":A[b]["net"]-A[a]["net"],
            "delta_pf":A[b]["pf"]-A[a]["pf"],"delta_expectancy":A[b]["expectancy"]-A[a]["expectancy"],
            "added_count":len(add),"added_net":sum(r["net"] for r in add),"removed_count":len(rem),"removed_net":sum(r["net"] for r in rem)}
M={"B-A":marginal(V[0],V[1]),"C-B":marginal(V[1],V[2]),"D-C":marginal(V[2],V[3])}
def calibration_gate(z):
    return z["baskets"]>=90 and z["frequency"]>=30 and z["net"]>0 and z["pf"]>=1.25 and z["expectancy"]>0 and z["all_years_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"] and z["all_12_families_positive"] and z["anti_concentration_pass"]
for v in V:
    A[v]["calibration_gate"]=calibration_gate(A[v]) if v!=V[0] else False
eligible=[v for v in V[1:] if A[v]["calibration_gate"]]
candidate=max(eligible,key=lambda v:(A[v]["family_positive_count"],A[v]["net"],A[v]["pf"],A[v]["frequency"])) if eligible else None
for v in V: A[v].pop("_rows",None)
front={"version":"HarmonyBot V68","stage":"CALIBRATION_2021_2023","variants":A,"marginal":M,
       "family_gate":{"min_trades_per_family":5,"min_active_years":2,"min_positive_years":1,"net_positive":True,"expectancy_positive":True,"required_positive_families":12,"max_single_family_share":.35,"rule":"NO_FIXED_QUOTA;EACH_FAMILY_MUST_PROVE_OWN_POSITIVE_CAPITAL_COHORT"},
       "calibration_candidate":candidate,"decision":"CALIBRATION_CANDIDATE_PASS" if candidate else "HOLD_WITH_EVIDENCE",
       "validation_used":False,"fresh_used":False}
(out/"V68_CALIBRATION_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"candidate.txt").write_text(candidate or "")
# Compact family matrix for direct review.
matrix={v:{f:A[v]["family_stats"][f] for f in FAMILIES} for v in V}
(out/"V68_FAMILY_POSITIVE_THROUGHPUT_MATRIX.json").write_text(json.dumps(matrix,indent=2))
print(json.dumps(front,indent=2))
