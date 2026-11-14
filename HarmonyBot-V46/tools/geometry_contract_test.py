#!/usr/bin/env python3
import pathlib,json,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V46/src/HarmonyBotV46.cs").read_text(errors="ignore")
checks={
 "legacy_and_canonical_coordinates":"double xdxa = xd / xa;" in s and "double adxa = ad / xa;" in s,
 "switchable_completion":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "confirmed_d_only":"TryProjectProfile" not in s,
 "abcd_observation":"ABCD_EXACT" in s and "ABCD_NEAR_127" in s,
 "completed_bar":"LastClosedIndex" in s,
}
out={"version":"HarmonyBot V46","checks":checks,"pass":all(checks.values())}
pathlib.Path("V46_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
