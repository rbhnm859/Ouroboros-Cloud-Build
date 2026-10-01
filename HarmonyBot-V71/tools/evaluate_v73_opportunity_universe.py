#!/usr/bin/env python3
import json,pathlib,re,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
windows=["Y2016","Y2017","Y2018","Y2019","Y2020","Y2021","Y2022","Y2023"]
summary_re=re.compile(r"\[V72-HCOG-SUMMARY\].*?detected=(\d+).*?proofs=(\d+).*?armed=(\d+).*?failureArmed=(\d+).*?closed=(\d+).*?coreOverlapAtEntry=(\d+).*?capitalQueued=(\d+)")
ou_re=re.compile(r"\[V73-OU2-SUMMARY\].*?calls=(\d+).*?raw=(\d+).*?deduped=(\d+).*?duplicateSuppressed=(\d+)")
res={}
for w in windows:
 logs=[p for p in root.rglob("*.log") if w in str(p)]
 if not logs:
  res[w]={"pass":False,"reason":"MISSING_LOG","detected":0}; continue
 txt="\n".join(p.read_text(errors="ignore") for p in logs)
 hs=list(summary_re.finditer(txt)); os=list(ou_re.finditer(txt))
 if not hs or not os:
  res[w]={"pass":False,"reason":"MISSING_SUMMARY","detected":0}; continue
 h=hs[-1]; o=os[-1]
 detected=int(h.group(1)); capital=int(h.group(7))
 res[w]={"detected":detected,"proofs":int(h.group(2)),"armed":int(h.group(3)),
         "failure_armed":int(h.group(4)),"closed":int(h.group(5)),"core_overlap_at_entry":int(h.group(6)),
         "capital_queued":capital,"detector_calls":int(o.group(1)),"raw_candidates":int(o.group(2)),
         "deduped_candidates":int(o.group(3)),"duplicate_suppressed":int(o.group(4)),
         "pass":bool(detected>=400 and capital==0)}
training=windows[:5]; burned=windows[5:]
training_ready=all(res[w]["pass"] for w in training)
burned_supply_ready=all(res[w]["pass"] for w in burned)
manifest={"version":"V73_OPPORTUNITY_UNIVERSE_2","purpose":"PHYSICAL_SUPPLY_AND_GOVERNED_TRAINING_CUSTODY",
 "training_windows":training,"burned_windows":burned,"minimum_independent_opportunities_per_year":400,
 "windows":res,"training_ready":training_ready,"burned_supply_ready":burned_supply_ready,
 "v73_gate":bool(training_ready and burned_supply_ready),
 "capital_execution_used":False,"validation_used":False,"fresh_used":False,
 "promotion_semantics":"PASS_ONLY_IF_EVERY_2016_2023_YEAR_HAS_GE_400_DEDUPED_HARMONIC_CAUSAL_OPPORTUNITIES_AND_ZERO_CAPITAL_QUEUE",
 "next_stage":"V74_ALPHA_TOURNAMENT" if training_ready and burned_supply_ready else "V73_ROOT_CAUSE_ONLY_NO_FORMAL_VERSION_PROMOTION"}
(out/"V73_OPPORTUNITY_UNIVERSE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
