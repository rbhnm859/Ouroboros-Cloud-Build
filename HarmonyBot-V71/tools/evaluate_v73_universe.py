#!/usr/bin/env python3
import json,math,pathlib,re,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
WINDOWS=[f"Y{y}" for y in range(2016,2024)]
MIN_CAUSAL=400
MIN_PARENT_CAUSAL=150
MIN_FAMILIES=8

outcome_rx=re.compile(
 r"\[V72-HCOG-OUTCOME\]\s+id=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+lane=(\S+)\s+"
 r"abcd=(True|False)\s+coreOverlap=(True|False)\s+r=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+"
 r"maeR=([-0-9.]+)\s+bars=(\d+)\s+result=(\S+)\s+hcapSelected=(True|False)\s+"
 r"q=([-0-9.]+)\s+lcb=([-0-9.]+)\s+hold=([-0-9.]+)\s+features=(\S+)"
)
summary_rx=re.compile(
 r"\[V73-UNIVERSE-SUMMARY\]\s+swingDepths=2,3,4,5,6,7,8\s+independentDetected=(\d+)\s+"
 r"przTouched=(\d+)\s+causalProofs=(\d+)\s+closedOutcomes=(\d+)\s+abcdPrimitive=(\d+)\s+"
 r"coreOverlapObserved=(\d+)\s+capitalExecutionUsed=False"
)

def wof(p):
 s=str(p)
 for w in WINDOWS:
  if w in s:return w
 return None

rows={w:[] for w in WINDOWS}; summaries={}
for p in root.rglob("*.log"):
 w=wof(p)
 if not w: continue
 txt=p.read_text(errors="ignore")
 sm=summary_rx.findall(txt)
 if sm:
  z=sm[-1]
  summaries[w]={"detected":int(z[0]),"prz_touched":int(z[1]),"causal_proofs":int(z[2]),
                "closed_outcomes":int(z[3]),"abcd_primitive":int(z[4]),"core_overlap":int(z[5])}
 for m in outcome_rx.finditer(txt):
  fam=m.group(3); lane=m.group(4); features=m.group(15)
  if lane not in ("HCOG_REVERSAL","HCOG_FAILURE_CONTINUATION",
                  "HCOG_ABCD_STANDALONE_REVERSAL_SHADOW","HCOG_ABCD_STANDALONE_CONTINUATION_SHADOW"): continue
  if features=="NONE": continue
  fv=[float(x) for x in features.split(",")]
  if not fv or not all(math.isfinite(x) for x in fv): continue
  rows[w].append({"id":m.group(1),"setup":m.group(2),"family":fam,"lane":lane,
                  "r":float(m.group(7)),"mfe":float(m.group(8)),"mae":float(m.group(9)),
                  "bars":int(m.group(10)),"result":m.group(11),"features":fv})

audit={}
for p in root.rglob("R_V73_OPPORTUNITY_UNIVERSE-*.json"):
 try:
  d=json.load(open(p))
 except Exception:
  continue
 w=d.get("window")
 if w in WINDOWS:audit[w]=d

manifest={"version":"HarmonyBot V73 Candidate","architecture":"MULTISCALE_FROZEN_DETECTOR_OPPORTUNITY_UNIVERSE_WITH_CANONICAL_ABCD_SUPPLY",
          "swing_depths":[2,3,4,5,6,7,8],"minimum_independent_causal_opportunities_per_year":MIN_CAUSAL,
          "minimum_parent_family_causal_opportunities_per_year":MIN_PARENT_CAUSAL,
          "minimum_visible_families_per_year":MIN_FAMILIES,"windows":{},"validation_used":False,"fresh_used":False}
all_pass=True
for w in WINDOWS:
 xs=rows[w]; ids=[x["setup"] for x in xs]; unique={x["setup"]:x for x in xs}
 parents={k:x for k,x in unique.items() if x["family"]!="ABCD"}
 fams=sorted({x["family"] for x in unique.values()})
 dup=len(ids)-len(set(ids))
 snap=str(audit.get(w,{}).get("data_snapshot_sha256",""))
 summary=summaries.get(w,{})
 valid_snapshot=bool(re.fullmatch(r"[0-9a-f]{64}",snap))
 gate=(len(unique)>=MIN_CAUSAL and len(parents)>=MIN_PARENT_CAUSAL and len(fams)>=MIN_FAMILIES and dup==0 and valid_snapshot and
       bool(summary) and summary.get("causal_proofs",0)>=len(unique) and summary.get("closed_outcomes",0)>=len(unique))
 manifest["windows"][w]={"independent_causal_opportunities":len(unique),
   "parent_family_causal_opportunities":len(parents),"standalone_abcd_causal_opportunities":len(unique)-len(parents),
   "visible_families":len(fams),"families":fams,"duplicate_setup_rows":dup,
   "data_snapshot_sha256":snap,"data_snapshot_valid":valid_snapshot,
   "summary":summary,"pass":gate}
 all_pass=all_pass and gate
manifest["v73_gate"]=all_pass
manifest["gate_semantics"]="EACH_2016_2023_YEAR_GE_400_UNIQUE_CAUSAL_OUTCOMES_INCLUDING_STANDALONE_ABCD__GE150_PARENT_FAMILY_CAUSAL__GE8_FAMILIES__ZERO_DUPLICATE__VALID_CUSTODY__ABCD_REQUIRES_SEPARATE_V74_TRAINING_PROOF_BEFORE_CAPITAL"
manifest["positive_asset"]="PROVES_PHYSICAL_HARMONIC_SUPPLY_FOR_200_INDEPENDENT_BASKETS_PER_YEAR_WITH_2X_MARGIN_WHILE_RETAINING_PARENT_DIVERSITY_AND_REQUIRING_ABCD_EMPIRICAL_CAPITAL_PROOF"
(out/"V73_OPPORTUNITY_UNIVERSE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
(out/"pass.txt").write_text("true" if all_pass else "false")
print(json.dumps(manifest,indent=2))
