#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V49/src/HarmonyBotV49.cs").read_text(errors="ignore")
checks={
 "confirmed_d_primary":"TryProjectProfile" not in s and "_m5Bars" not in s,
 "m15_thesis_m1_execution":"_m15Bars" in s and "_m1Bars" in s and "ProcessNewM1Close" in s,
 "standard_coordinate_contract":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "fib_grid_frozen":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s and "2.0 / 7.0" in s,
 "order_independent_native":"UpdateV49EvidenceSet" in s and "V49EvidenceWindowBars" in s and "NativeStage" in s,
 "counterfactual_timing":"CfTwoRUtc" in s and "CfSlUtc" in s and "AMBIGUOUS_SAME_BAR" in s,
}
out={"version":"HarmonyBot V49","contract":"HARMONIC_FAMILY_CONFIRMATION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V49_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
