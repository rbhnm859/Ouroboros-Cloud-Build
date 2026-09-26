#!/usr/bin/env python3
import pathlib,sys,json,re
s=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
checks={
 "detect_many_execute_one":"FAMILY_QUOTA_SELECTED" in s and "BuildFamilyHypothesisKey" in s,
 "bounded_graph":"EnumerateBoundedPivotSequences" in s,
 "abcd_quota_cap":'g.Key == "AB=CD" ? 1 : quota' in s,
 "family_priority":"V67FamilyDetectorPriority" in s,
 "canonical_duplicate":"UNDERLYING_ALREADY_EXECUTED" in s and "FAMILY_HYPOTHESIS_DUPLICATE_SUPPRESSED" in s,
 "detector_truth":"V67-DETECTOR-TRUTH" in s and "DetectorTruth" in s,
}
o={"contract":"V67_DETECTOR","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 69)
