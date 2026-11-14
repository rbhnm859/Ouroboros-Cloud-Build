#!/usr/bin/env python3
import json,math,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); stage=sys.argv[3].upper()
total_years=float(sys.argv[4]); windows=[x for x in sys.argv[5].split(",") if x]
out.mkdir(parents=True,exist_ok=True)
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
      "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"]
def one(n):
 xs=list(root.rglob(n))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
 return json.load(open(xs[0]))
def fp(x):
 z=x.get("core_execution_fingerprint")
 return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None
def sig(rows):return {(r["setup"],r["pattern"],r["route"]) for r in rows}
per_year=total_years/len(windows)
required_return=((2.5**per_year)-1.0)*100.0
required_trades=math.ceil(200*per_year)
required_months=math.ceil(11*per_year-1e-12)
res={}; ok=True
for w in windows:
 ref=one(f"V51_REFERENCE-{w}.json"); c=one(f"CANDIDATE-{w}.json")
 core=(ref.get("data_snapshot_sha256")==c.get("data_snapshot_sha256"))
 a,b=fp(ref),fp(c)
 if a is not None and b is not None: core=core and a==b
 else: core=core and sig(ref.get("core_basket_outcomes",[]))==sig(c.get("core_basket_outcomes",[]))
 viol={k:int(c.get(k,0) or 0) for k in VIOL}
 gate=(core and c.get("engineering_clean",False) and all(v==0 for v in viol.values()) and
       float(c.get("return_pct",0))>=required_return and
       float(c.get("net",0))>=float(c.get("starting_balance",10000))*required_return/100.0 and
       float(c.get("pf",0))>=3.0 and float(c.get("max_dd_pct",999))<=10.0 and
       float(c.get("win_rate",0))>=.68 and int(c.get("baskets",0))>=required_trades and
       bool(c.get("log_basket_telemetry_complete",False)) and
       float(c.get("average_realized_rr",0))>=2.2 and
       int(c.get("active_months",0))>=round(12*per_year) and
       int(c.get("positive_months",0))>=required_months and
       float(c.get("net",0))>float(ref.get("net",0)))
 res[w]={"pass":gate,"core_displacement_zero":core,"required_return_pct":required_return,
         "required_independent_baskets":required_trades,"required_profitable_months":required_months,
         "candidate":{"return_pct":c.get("return_pct",0),"net":c.get("net",0),"pf":c.get("pf",0),
                      "max_dd_pct":c.get("max_dd_pct",0),"win_rate":c.get("win_rate",0),"baskets":c.get("baskets",0),
                      "average_realized_rr":c.get("average_realized_rr",0),"active_months":c.get("active_months",0),
                      "positive_months":c.get("positive_months",0),"expectancy":c.get("expectancy",0)},
         "control_net":ref.get("net",0),"violations":viol}
 ok=ok and gate
m={"version":f"HarmonyBot {stage}","stage":stage,"windows":windows,"years":total_years,
   "commercial_hard_targets":{"annual_return_pct":150,"net_multiple":1.5,"pf":3.0,"max_dd_pct":10.0,
                              "win_rate":.68,"independent_baskets_per_year":200,"average_realized_rr":2.2,
                              "profitable_months_per_year":11},
   "window_equivalent":{"required_return_pct":required_return,"required_trades":required_trades,"required_profitable_months":required_months},
   "window_results":res,"gate":ok,
   "validation_used":stage in ("VALIDATION","FRESH"),"fresh_used":stage=="FRESH"}
(out/f"{stage}_COMMERCIAL_MANIFEST.json").write_text(json.dumps(m,indent=2));(out/"pass.txt").write_text("true" if ok else "false")
print(json.dumps(m,indent=2))
