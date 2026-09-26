#!/usr/bin/env python3
import json,pathlib,sys,math,collections,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V52_EXACT_CONTROL","B_FAMILY_NATIVE","C_FAMILY_NATIVE_GRID","D_COMMERCIAL_MAX"]
W=["Y2021","Y2022","Y2023","H2024H2","H2025H1","H2025H2"]
DUR={"Y2021":1.0,"Y2022":1.0,"Y2023":1.0,"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}
TOTAL_YEARS=sum(DUR.values())
def find(name):
    xs=list(root.rglob(name))
    if not xs: raise SystemExit("missing "+name)
    return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def pctl(xs,p):
    if not xs:return 0
    z=sorted(xs); return z[max(0,min(len(z)-1,math.ceil(p*len(z))-1))]
def maxdd_dollars(rows):
    eq=peak=0.0; dd=0.0
    for r in rows:
        eq+=r["net"]; peak=max(peak,eq); dd=max(dd,peak-eq)
    return dd
def agg(v):
    wins={w:rd(v,w) for w in W}; rows=[]
    for w in W:
        for r in wins[w].get("basket_outcomes",[]):
            q=dict(r);q["window"]=w;rows.append(q)
    n=len(rows); net=sum(r["net"] for r in rows); rr=[r["r"] for r in rows if r["r"]>0]
    return {
      "baskets":n,"years":TOTAL_YEARS,"frequency":n/TOTAL_YEARS,"net":net,
      "normalized_net_1p5y":net/TOTAL_YEARS*1.5,"pf":pf(rows),"expectancy":net/n if n else 0,
      "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "max_dd_pct":max((wins[w]["max_dd_pct"] for w in W),default=0),
      "p95_winner_r":pctl(rr,.95),"max_winner_r":max(rr) if rr else 0,
      "all_windows_positive":all(wins[w]["net"]>0 for w in W),
      "engineering_clean":all(wins[w]["engineering_clean"] for w in W),
      "risk_clean":all(wins[w]["actual_basket_risk_violations"]==0 and wins[w]["margin_risk_violations"]==0 and wins[w]["stop_widening_violations"]==0 for w in W),
      "unique_thesis":len({(r["window"],r["setup"]) for r in rows})==n,
      "windows":{w:{k:wins[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean"]} for w in W},
      "_rows":rows,"_wins":wins
    }
A={v:agg(v) for v in V}
COMM={"frequency":60.0,"normalized_net_1p5y":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
V51={"frequency":38.6666666667,"normalized_net_1p5y":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
def commercial(z):
    return z["frequency"]>=COMM["frequency"] and z["normalized_net_1p5y"]>=COMM["normalized_net_1p5y"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"]
def superior(z):
    return z["frequency"]>V51["frequency"] and z["normalized_net_1p5y"]>V51["normalized_net_1p5y"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["max_dd_pct"]<=V51["max_dd_pct"]
def marginal(frm,to):
    base={(r["window"],r["setup"]):r for r in A[frm]["_rows"]}; nxt={(r["window"],r["setup"]):r for r in A[to]["_rows"]}
    added=[r for k,r in nxt.items() if k not in base]; removed=[r for k,r in base.items() if k not in nxt]
    return {"from":frm,"to":to,"delta_trades":A[to]["baskets"]-A[frm]["baskets"],"delta_net":A[to]["net"]-A[frm]["net"],
      "delta_pf":A[to]["pf"]-A[frm]["pf"],"delta_expectancy":A[to]["expectancy"]-A[frm]["expectancy"],
      "added_count":len(added),"added_net":sum(r["net"] for r in added),"added_pf":pf(added),
      "removed_count":len(removed),"removed_net":sum(r["net"] for r in removed)}
M={"B-A":marginal(V[0],V[1]),"C-B":marginal(V[1],V[2]),"D-C":marginal(V[2],V[3])}
def positive_new(m): return m["added_count"]==0 or m["added_net"]>0
grid_gate=M["C-B"]["delta_net"]>0 and A[V[2]]["pf"]>=A[V[1]]["pf"] and A[V[2]]["expectancy"]>=A[V[1]]["expectancy"] and A[V[2]]["p95_winner_r"]>0 and A[V[2]]["max_winner_r"]>=A[V[1]]["max_winner_r"] and positive_new(M["C-B"]) and A[V[2]]["risk_clean"]
exp_gate=(M["D-C"]["delta_trades"]<=0 or M["D-C"]["delta_net"]>0) and positive_new(M["D-C"]) and A[V[3]]["pf"]>=A[V[2]]["pf"] and A[V[3]]["expectancy"]>=A[V[2]]["expectancy"] and A[V[3]]["risk_clean"]
for v in V:
    A[v]["commercial_gate"]=commercial(A[v]); A[v]["v51_superiority_gate"]=superior(A[v])
# Family x Route x Window attribution
attrib=[]
for v in V:
  wins=A[v]["_wins"]
  for w in W:
    rows=wins[w].get("basket_outcomes",[]); slots=wins[w].get("slot_occupancy",[])
    keys=sorted({(r["pattern"],r["route"]) for r in rows})
    for fam,route in keys:
      rs=[r for r in rows if r["pattern"]==fam and r["route"]==route]; wins_r=[r["r"] for r in rs if r["r"]>0]
      ss=[x["occupancy_minutes"] for x in slots if x["pattern"]==fam and x["route"]==route]
      net=sum(r["net"] for r in rs)
      attrib.append({"variant":v,"window":w,"family":fam,"route":route,"count":len(rs),"net":net,"pf":pf(rs),
        "expectancy":net/len(rs),"win_rate":sum(r["net"]>0 for r in rs)/len(rs),
        "dd_contribution_dollars":maxdd_dollars(rs),"mean_mfe_r":statistics.mean([r["mfe"] for r in rs]),
        "mean_mae_r":statistics.mean([r["mae"] for r in rs]),"p95_winner_r":pctl(wins_r,.95),"max_winner_r":max(wins_r) if wins_r else 0,
        "occupancy_cost_minutes":sum(ss),"avg_occupancy_minutes":statistics.mean(ss) if ss else 0})
eligible=[]
if A[V[1]]["commercial_gate"] and A[V[1]]["v51_superiority_gate"]: eligible.append(V[1])
if A[V[2]]["commercial_gate"] and A[V[2]]["v51_superiority_gate"] and grid_gate: eligible.append(V[2])
if A[V[3]]["commercial_gate"] and A[V[3]]["v51_superiority_gate"] and grid_gate and exp_gate: eligible.append(V[3])
candidate=max(eligible,key=lambda v:(A[v]["normalized_net_1p5y"],A[v]["pf"],A[v]["expectancy"])) if eligible else None
for v in V:
    A[v].pop("_rows",None); A[v].pop("_wins",None)
front={"version":"HarmonyBot V67","stage":"DEV","duration_years":TOTAL_YEARS,"commercial_minimum":COMM,"v51_superiority":V51,
 "variants":A,"marginal":M,"grid_promotion_gate":grid_gate,"controlled_expansion_gate":exp_gate,
 "development_candidate":candidate,"decision":"DEV_CANDIDATE_PASS" if candidate else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V67_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V67_FAMILY_ROUTE_WINDOW_ATTRIBUTION.json").write_text(json.dumps(attrib,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"V67_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V67","decision":front["decision"],"candidate":candidate,"fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
