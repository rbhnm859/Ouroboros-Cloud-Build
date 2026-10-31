#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]; RISKS=[1,2,3,5]; MODES=["SINGLE","GRID"]
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
REF={w:one(f"V51_REFERENCE-{w}.json") for w in W}
configs={}
for risk in RISKS:
 for mode in MODES:
  per={}; hard=True; total_net=0.0
  for w in W:
   c=one(f"V77_{mode}_R{risk}_{w}.json"); r=REF[w]
   core=(r.get("data_snapshot_sha256")==c.get("data_snapshot_sha256"))
   a,b=fp(r),fp(c)
   if a is not None and b is not None: core=core and a==b
   else: core=core and sig(r.get("core_basket_outcomes",[]))==sig(c.get("core_basket_outcomes",[]))
   viol={k:int(c.get(k,0) or 0) for k in VIOL}
   h=(core and c.get("engineering_clean",False) and all(v==0 for v in viol.values()) and
      float(c.get("return_pct",0))>=150.0 and
      float(c.get("net",0))>=float(c.get("starting_balance",10000))*1.50 and
      float(c.get("pf",0))>=3.0 and float(c.get("max_dd_pct",999))<=7.5 and
      float(c.get("win_rate",0))>=.68 and int(c.get("baskets",0))>=200 and
      bool(c.get("log_basket_telemetry_complete",False)) and
      float(c.get("average_realized_rr",0))>=2.2 and
      int(c.get("active_months",0))>=12 and int(c.get("positive_months",0))>=11)
   per[w]={"pass":h,"core_displacement_zero":core,"return_pct":c.get("return_pct",0),"net":c.get("net",0),
           "pf":c.get("pf",0),"max_dd_pct":c.get("max_dd_pct",0),"win_rate":c.get("win_rate",0),
           "baskets":c.get("baskets",0),"average_realized_rr":c.get("average_realized_rr",0),
           "active_months":c.get("active_months",0),"positive_months":c.get("positive_months",0),
           "expectancy":c.get("expectancy",0),"violations":viol}
   hard=hard and h; total_net+=float(c.get("net",0))
  configs[f"{mode}_R{risk}"]={"mode":mode,"risk_pct":risk,"windows":per,"hard_target_3of3":hard,"total_net":total_net}

# Grid may only qualify if it is Pareto-non-regressive to single at the same risk.
for risk in RISKS:
 s=configs[f"SINGLE_R{risk}"]; g=configs[f"GRID_R{risk}"]
 pareto=True
 for w in W:
  a=s["windows"][w]; b=g["windows"][w]
  pareto=pareto and (b["net"]>=a["net"]-1e-8 and b["pf"]>=a["pf"]-1e-9 and
                     b["expectancy"]>=a["expectancy"]-1e-8 and b["max_dd_pct"]<=a["max_dd_pct"]+1e-9)
 g["grid_pareto_vs_single"]=pareto
 g["eligible"]=bool(g["hard_target_3of3"] and pareto)
 s["eligible"]=bool(s["hard_target_3of3"])

eligible=[v for v in configs.values() if v.get("eligible")]
eligible.sort(key=lambda x:(x["risk_pct"],-x["total_net"],0 if x["mode"]=="GRID" else 1))
chosen=eligible[0] if eligible else None
m={"version":"HarmonyBot V77 Candidate","architecture":"FIXED_CAPACITY_SWEEP_PLUS_FAMILY_NATIVE_GRID_PARETO",
   "risk_tiers_pct":RISKS,"internal_dd_design_ceiling_pct":7.5,
   "commercial_targets":{"annual_return_pct":150,"net_multiple":1.5,"pf":3.0,"win_rate":.68,
                         "independent_baskets":200,"average_realized_rr":2.2,"profitable_months":11},
   "configs":configs,"v77_gate":chosen is not None,
   "selected":None if chosen is None else {"mode":chosen["mode"],"risk_pct":chosen["risk_pct"],"total_net":chosen["total_net"]},
   "selection_rule":"LOWEST_RISK_TIER_THAT_PASSES_ALL_3_BURNED_YEARS;_GRID_ONLY_IF_PARETO_NONREGRESSIVE;WITHIN_TIER_HIGHER_TOTAL_NET",
   "positive_asset":"PROVES_A_FIXED_CAPACITY_CONFIGURATION_CAN_HIT_ALL_COMMERCIAL_TARGETS_WITH_7P5PCT_INTERNAL_DD_BUFFER" if chosen else "NO_CAPACITY_CONFIGURATION_EARNED_DEV_ACCESS",
   "validation_used":False,"fresh_used":False}
(out/"V77_CAPACITY_MANIFEST.json").write_text(json.dumps(m,indent=2));(out/"pass.txt").write_text("true" if chosen else "false")
print(json.dumps(m,indent=2))
