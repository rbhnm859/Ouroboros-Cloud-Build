#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
      "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"]
def one(n):
 xs=list(root.rglob(n))
 if len(xs)!=1:raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
 return json.load(open(xs[0]))
B={w:one(f"V75_BASELINE-{w}.json") for w in W}; C={w:one(f"V76_SLOT-{w}.json") for w in W}
windows={}; ok=True
for w in W:
 b,c=B[w],C[w]; viol={k:int(c.get(k,0) or 0) for k in VIOL}
 gate=(c.get("engineering_clean",False) and all(v==0 for v in viol.values()) and
       int(c.get("baskets",0))>=200 and float(c.get("net",0))>0 and
       float(c.get("net",0))>=float(b.get("net",0))-1e-8 and
       float(c.get("pf",0))>=float(b.get("pf",0))-1e-9 and
       float(c.get("expectancy",0))>=float(b.get("expectancy",0))-1e-8 and
       float(c.get("max_dd_pct",999))<=float(b.get("max_dd_pct",999))+1e-9)
 windows[w]={"pass":gate,"baseline":{"baskets":b.get("baskets",0),"net":b.get("net",0),"pf":b.get("pf",0),
             "expectancy":b.get("expectancy",0),"max_dd_pct":b.get("max_dd_pct",0)},
             "slot_optimized":{"baskets":c.get("baskets",0),"net":c.get("net",0),"pf":c.get("pf",0),
             "expectancy":c.get("expectancy",0),"max_dd_pct":c.get("max_dd_pct",0)},"violations":viol}
 ok=ok and gate
m={"version":"HarmonyBot V76 Candidate","architecture":"CONSERVATIVE_EDGE_PER_EXPECTED_SLOT_HOUR_SCHEDULER",
   "windows":windows,"v76_gate":ok,
   "gate_semantics":"EACH_BURNED_YEAR_GE200_INDEPENDENT_BASKETS_POSITIVE_NET_AND_NO_NET_PF_EXPECTANCY_DD_REGRESSION_VS_V75",
   "positive_asset":"PROVES_MAXACTIVEBASKET1_CAN_SUPPORT_200PLUS_YEAR_WITHOUT_ECONOMIC_REGRESSION" if ok else "THROUGHPUT_GATE_NOT_PROVEN",
   "validation_used":False,"fresh_used":False}
(out/"V76_SLOT_EFFICIENCY_MANIFEST.json").write_text(json.dumps(m,indent=2));(out/"pass.txt").write_text("true" if ok else "false")
print(json.dumps(m,indent=2))
