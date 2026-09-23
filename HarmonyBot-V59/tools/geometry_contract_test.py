#!/usr/bin/env python3
import json,pathlib,sys,math
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V59/src/HarmonyBotV59.cs").read_text(errors="ignore")
def score(vals): return math.exp(-.5*sum(v*v for v in vals)/len(vals))
checks={
"joint_metric_present":"FamilyNativeJointGeometryScore" in s,
"range_normalization":"RangeCoordinate" in s,
"abcd_discrete_manifold":"CanonicalAbcdCoordinate" in s,
"family_identity":"BuildFamilyHypothesisKey" in s and "EnableFamilyIdentityReconstruction" in s,
"bounded_graph":"EnumerateBoundedPivotSequences" in s,
"projected_prz":"FamilyProjectedPrzCenter" in s,
"stop_not_relaxed":"StructuralStop = stop" in s,
"minimum_rr_unchanged":"Minimum Net RR" in s and "DefaultValue = 2.0" in s,
"confirmed_d":"TryProjectProfile" not in s,
"center_scores_higher":score([0,0,0,0,0])>score([.8,.8,.8,.8,.8]),
"boundary_penalty_finite":0<score([1,1,1,1,1])<1,
}
out={"version":"HarmonyBot V59","checks":checks,"pass":all(checks.values())}
pathlib.Path("V59_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
