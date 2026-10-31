#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V49/src/HarmonyBotV49.cs").read_text(errors="ignore")
checks={
 "adxa":"double adxa = ad / xa;" in s,
 "confirmed_d":"TryProjectProfile" not in s,
 "gartley_b":'AddStd("Gartley", .600, .636' in s,
 "bat_bc":'1.618, 2.618, .875, .895' in s,
 "alt_bat":'AddStd("Alt Bat", .300, .395' in s and '1.10, 1.16' in s,
 "butterfly":'AddStd("Butterfly", .770, .800' in s and '1.24, 1.30' in s,
 "crab":'AddStd("Crab", .382, .618' in s and '2.24, 3.618, 1.58, 1.66' in s,
 "deep_crab":'AddStd("Deep Crab", .875, .900' in s and '1.58, 1.66' in s,
 "abcd_compatibility":"StandardFamilyAbcdCompatible" in s and "alt1618" in s,
}
out={"version":"HarmonyBot V49","checks":checks,"pass":all(checks.values())}
pathlib.Path("V49_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
