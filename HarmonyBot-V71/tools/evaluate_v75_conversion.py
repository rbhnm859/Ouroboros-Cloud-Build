#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
      "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"]
def one(name):
 xs=list(root.rglob(name))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
 return json.load(open(xs[0]))
def fp(x):
 z=x.get("core_execution_fingerprint")
 return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None
def sig(rows):return {(r["setup"],r["pattern"],r["route"]) for r in rows}
def pfr(rows):
 gp=sum(float(r.get("r",0)) for r in rows if float(r.get("r",0))>0)
 gl=-sum(float(r.get("r",0)) for r in rows if float(r.get("r",0))<0)
 return gp/gl if gl else (999.0 if gp else 0.0)
REF={w:one(f"V51_REFERENCE-{w}.json") for w in W}
C={w:one(f"V75_BASELINE-{w}.json") for w in W}
window={}; allpass=True
for w in W:
 r,c=REF[w],C[w]
 core=(r.get("data_snapshot_sha256")==c.get("data_snapshot_sha256"))
 a,b=fp(r),fp(c)
 if a is not None and b is not None: core=core and a==b
 else: core=core and sig(r.get("core_basket_outcomes",[]))==sig(c.get("core_basket_outcomes",[]))
 exp=c.get("expansion_basket_outcomes",[]); em=c.get("expansion_metrics",{})
 er=[float(x.get("r",0)) for x in exp]
 meanr=sum(er)/len(er) if er else 0.0
 viol={k:int(c.get(k,0) or 0) for k in VIOL}
 gate=(core and c.get("engineering_clean",False) and all(v==0 for v in viol.values()) and
       float(c.get("net",0))>0 and int(c.get("baskets",0))>=60 and
       float(em.get("net",0))>0 and float(em.get("pf",0))>1.0 and meanr>0)
 window[w]={"pass":gate,"core_displacement_zero":core,"baskets":c.get("baskets",0),
            "net":c.get("net",0),"pf":c.get("pf",0),"expectancy":c.get("expectancy",0),
            "max_dd_pct":c.get("max_dd_pct",0),"expansion":em,"expansion_mean_realized_r":meanr,
            "expansion_pf_r":pfr(exp),"violations":viol}
 allpass=allpass and gate
m={"version":"HarmonyBot V75 Candidate","architecture":"FROZEN_OOF_POLICY_REAL_CTRADER_ECONOMIC_CONVERSION",
   "windows":window,"v75_gate":allpass,
   "gate_semantics":"EACH_BURNED_YEAR_CORE_ZERO_ENGINEERING_CLEAN_ZERO_VIOLATIONS_TOTAL_NET_GT0_BASKETS_GE60_EXPANSION_NET_GT0_EXPANSION_PF_GT1_EXPANSION_MEAN_REALIZED_R_GT0",
   "positive_asset":"PROVES_RESEARCH_ALPHA_SURVIVES_BROKER_COST_AND_EXECUTION" if allpass else "ECONOMIC_CONVERSION_NOT_PROVEN",
   "validation_used":False,"fresh_used":False}
(out/"V75_CAPITAL_CONVERSION_MANIFEST.json").write_text(json.dumps(m,indent=2));(out/"pass.txt").write_text("true" if allpass else "false")
print(json.dumps(m,indent=2))
