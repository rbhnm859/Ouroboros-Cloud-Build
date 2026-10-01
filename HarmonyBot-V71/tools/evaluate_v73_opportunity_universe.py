#!/usr/bin/env python3
import json, pathlib, re, statistics, sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
windows=("Y2021","Y2022","Y2023")
summary_rx=re.compile(r"\[V72-HCOG-SUMMARY\].*?detected=(\d+).*?proofs=(\d+).*?armed=(\d+).*?failureArmed=(\d+).*?closed=(\d+).*?coreOverlapAtEntry=(\d+).*?abcdPrimitive=(\d+)")
outcome_rx=re.compile(r"\[V72-HCOG-OUTCOME\]\s+id=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+lane=(\S+)")
per={}
for w in windows:
    logs=[p for p in root.rglob("*.log") if w in str(p)]
    if not logs: raise SystemExit(f"missing census log {w}")
    detected=proofs=armed=failure=closed=overlap=abcd=0; keys=set(); families={}
    for p in logs:
        t=p.read_text(errors="ignore")
        ms=list(summary_rx.finditer(t))
        if ms:
            m=ms[-1]; detected+=int(m.group(1)); proofs+=int(m.group(2)); armed+=int(m.group(3)); failure+=int(m.group(4)); closed+=int(m.group(5)); overlap+=int(m.group(6)); abcd+=int(m.group(7))
        for m in outcome_rx.finditer(t):
            key=m.group(2); keys.add(key); families[m.group(3)]=families.get(m.group(3),0)+1
    per[w]={"raw_detected":detected,"causal_proofs":proofs,"reversal_armed":armed,"failure_armed":failure,
            "closed_counterfactual":closed,"unique_setup_outcomes":len(keys),"core_overlap_at_entry":overlap,
            "abcd_primitive":abcd,"family_outcomes":families}
# V73 is a supply/information gate, never a profitability selector.
# Require a 2x safety margin over the 200/year commercial trade target.
supply_floor=400
gate=all(per[w]["raw_detected"]>=supply_floor and per[w]["unique_setup_outcomes"]>=200 for w in windows)
manifest={"version":"HarmonyBot V73 Candidate","architecture":"OPPORTUNITY_UNIVERSE_2",
 "purpose":"SUPPLY_AND_INFORMATION_CAPACITY_ONLY_NO_PNL_SELECTION",
 "commercial_trade_target_per_year":200,"raw_supply_floor_per_year":supply_floor,
 "required_unique_counterfactual_outcomes_per_year":200,"windows":per,
 "gate":gate,"detector_mutated":False,"capital_execution_used":False,
 "validation_used":False,"fresh_used":False,
 "next_stage":"V74_ALPHA_TOURNAMENT" if gate else "V73_SUPPLY_RECONSTRUCTION_REQUIRED",
 "failure_policy":"NO_FORMAL_VERSION_PROMOTION_ON_FAIL__NO_THRESHOLD_RESCUE"}
(out/"V73_OPPORTUNITY_UNIVERSE_GATE.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
