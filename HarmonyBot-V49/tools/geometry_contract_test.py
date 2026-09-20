#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V49/src/HarmonyBotV49.cs").read_text(errors="ignore")
checks={
 "confirmed_d_only":"TryProjectProfile" not in s,
 "canonical_adxa":"double adxa = ad / xa;" in s and "double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "m1_primary":"ProcessNewM1Close" in s and "_m5Bars" not in s,
 "grid_frozen":"new[] { 0.0, .236, .382, .618 }" in s,
 "setup_identity":"BuildSetupGeometryKey" in s,
 "completed_bar":"LastClosedIndex" in s,
}
out={"version":"HarmonyBot V49","checks":checks,"pass":all(checks.values())}
pathlib.Path("V49_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
