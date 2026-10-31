#!/usr/bin/env python3
import json,math,pathlib,statistics,sys
P=pathlib.Path(sys.argv[1]); OUT=pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True,exist_ok=True)
d=json.load(open(P)); events=d["events"]; m=d["manifest"]; W=("Y2021","Y2022","Y2023"); F=tuple(m["families"]); Z=1.645
def stat(rows):
    v=[float(x["structural_r"]) for x in rows if bool(x["path_usable"])]; n=len(v); mean=sum(v)/n if n else 0.0
    lcb=mean-Z*statistics.stdev(v)/math.sqrt(n) if n>1 else -999.0
    gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
    return {"n":n,"mean_r":mean,"pf_r":gp/gl if gl else (999.0 if gp else 0.0),
            "lcb_r":lcb,"win_rate":sum(x>0 for x in v)/n if n else 0.0}
family={}
for fam in F:
    rows=[x for x in events if x["family"]==fam and x["capital_eligible"] and not x["core_overlap"]]
    yrs={w:stat([x for x in rows if x["window"]==w]) for w in W}; pooled=stat(rows)
    family[fam]={"pooled":pooled,"years":yrs,
      "three_year_positive":all(yrs[w]["n"]>0 and yrs[w]["mean_r"]>0 and yrs[w]["pf_r"]>1 for w in W),
      "three_year_lcb_positive":all(yrs[w]["n"]>1 and yrs[w]["lcb_r"]>0 for w in W)}
counts={f:sum(1 for x in events if x["family"]==f) for f in F}; total=sum(counts.values())
shares={f:(counts[f]/total if total else 0.0) for f in F}; ordered=sorted(shares.items(),key=lambda kv:kv[1],reverse=True)
report={"schema":"HARMONYBOT_V71_FAMILY_RESOLUTION_DIAGNOSTIC_V1",
 "mode":"FALSIFICATION_ONLY_NO_SELECTOR_NO_THRESHOLD_TUNING","atlas_research_ready":bool(m.get("research_ready")),
 "eligible_definition":"capital_eligible && !core_overlap && path_usable","family":family,
 "family_event_counts":counts,"family_event_shares":shares,"top3_share":sum(v for _,v in ordered[:3]),
 "families_with_3y_positive":sum(x["three_year_positive"] for x in family.values()),
 "families_with_3y_lcb_positive":sum(x["three_year_lcb_positive"] for x in family.values()),
 "architecture_diagnosis":{"detector_failure":False,"family_resolution_not_yet_proven":True,
   "native_proxy_rejected_as_counterfactual":True,
   "next_test":"RUN_ACTUAL_FAMILY_NATIVE_CAUSAL_STATE_MACHINE_ON_BURNED_2021_2023_GRID_OFF_RISK_1PCT"},
 "capital_decision_used":False,"validation_used":False,"fresh_used":False}
(OUT/"FAMILY_RESOLUTION_DIAGNOSTIC.json").write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
