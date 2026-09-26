#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V52_EXACT_CONTROL","B_FAMILY_NATIVE_ATLAS","C_FAMILY_SURVIVAL","D_COMMERCIAL_FEDERATION"]; W=["Y2021","Y2022","Y2023"]
F=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def find(n):
 x=list(root.rglob(n))
 if not x: raise SystemExit("missing "+n)
 return x[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
def pf(rs):
 gp=sum(float(r["net"]) for r in rs if float(r["net"])>0); gl=-sum(float(r["net"]) for r in rs if float(r["net"])<0)
 return gp/gl if gl else (999 if gp else 0)
def agg(v):
 ws={w:rd(v,w) for w in W}; rows=[]
 for w in W:
  for r in ws[w].get("basket_outcomes",[]): q=dict(r); q["window"]=w; rows.append(q)
 n=len(rows); fam={}
 for f in F:
  rs=[r for r in rows if r.get("pattern")==f]; by={w:[r for r in rs if r["window"]==w] for w in W}; net=sum(float(r["net"]) for r in rs)
  fam[f]={"count":len(rs),"net":net,"pf":pf(rs),"expectancy":net/len(rs) if rs else 0,"active_years":sum(bool(by[w]) for w in W),"positive_years":sum(sum(float(r["net"]) for r in by[w])>0 for w in W)}
 pos=[f for f,z in fam.items() if z["count"]>=5 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>1 and z["active_years"]>=2 and z["positive_years"]>=1]
 shares={f:(fam[f]["count"]/n if n else 0) for f in F}; largest=max(shares,key=shares.get) if n else None
 zero=("execution_errors","grid_risk_violations","actual_basket_risk_violations","margin_risk_violations","stop_widening_violations","duplicate_grid_legs","orphan_pending_orders","unprotected_survivors","post_fill_protection_failures","execution_state_violations")
 z={"baskets":n,"frequency":n/3,"net":sum(float(r["net"]) for r in rows),"pf":pf(rows),"expectancy":sum(float(r["net"]) for r in rows)/n if n else 0,"win_rate":sum(float(r["net"])>0 for r in rows)/n if n else 0,"max_dd_pct":max(float(ws[w].get("max_dd_pct",0)) for w in W),"all_years_positive":all(float(ws[w].get("net",0))>0 for w in W),"engineering_clean":all(bool(ws[w].get("engineering_clean",False)) for w in W),"risk_clean":all(all(int(ws[w].get(k,0) or 0)==0 for k in zero) for w in W),"unique_thesis":len({(r["window"],r.get("setup")) for r in rows})==n,"positive_families":pos,"family_positive_count":len(pos),"all_12_families_positive":len(pos)==12,"family_stats":fam,"largest_family":largest,"largest_family_share":shares.get(largest,0) if largest else 0,"anti_concentration_pass":shares.get(largest,0)<=.35 if largest else False,"windows":{w:{k:ws[w].get(k) for k in ("baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean")} for w in W},"_rows":rows}
 return z
A={v:agg(v) for v in V}
def marg(a,b):
 x={(r["window"],r.get("setup")):r for r in A[a]["_rows"]}; y={(r["window"],r.get("setup")):r for r in A[b]["_rows"]}
 add=[r for k,r in y.items() if k not in x]; rem=[r for k,r in x.items() if k not in y]
 return {"delta_trades":A[b]["baskets"]-A[a]["baskets"],"delta_net":A[b]["net"]-A[a]["net"],"delta_pf":A[b]["pf"]-A[a]["pf"],"delta_expectancy":A[b]["expectancy"]-A[a]["expectancy"],"added_count":len(add),"added_net":sum(float(r["net"]) for r in add),"removed_count":len(rem),"removed_net":sum(float(r["net"]) for r in rem)}
def gate(z):
 return z["baskets"]>=180 and z["frequency"]>=60 and z["net"]>0 and z["pf"]>=1.75 and z["expectancy"]>=20 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6 and z["all_years_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"] and z["all_12_families_positive"] and z["anti_concentration_pass"]
for v in V: A[v]["calibration_gate"]=False if v=="A_V52_EXACT_CONTROL" else gate(A[v])
eligible=[v for v in ("C_FAMILY_SURVIVAL","D_COMMERCIAL_FEDERATION") if A[v]["calibration_gate"]]
candidate=max(eligible,key=lambda v:(A[v]["pf"],A[v]["expectancy"],A[v]["net"],A[v]["frequency"])) if eligible else None
marginal={"B-A":marg(V[0],V[1]),"C-B":marg(V[1],V[2]),"D-C":marg(V[2],V[3])}
for v in V: A[v].pop("_rows",None)
front={"version":"HarmonyBot V69 — Family Alpha Federation Commercial Breakthrough","stage":"BURNED_CALIBRATION_2021_2023","variants":A,"marginal":marginal,"family_gate":{"min_trades_per_family":5,"min_active_years":2,"min_positive_years":1,"net_positive":True,"expectancy_positive":True,"pf_above_one":True,"required_positive_families":12,"max_single_family_share":.35,"rule":"NO_FIXED_QUOTA;EACH_FAMILY_MUST_PROVE_OWN_POSITIVE_CAPITAL_COHORT"},"calibration_candidate":candidate,"decision":"FREEZE_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE","validation_used":False,"fresh_used":False}
(out/"V69_CALIBRATION_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"V69_FAMILY_MATRIX.json").write_text(json.dumps({v:A[v]["family_stats"] for v in V},indent=2)); (out/"candidate.txt").write_text(candidate or ""); print(json.dumps(front,indent=2))
