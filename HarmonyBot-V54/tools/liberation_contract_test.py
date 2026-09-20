#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V54/src/HarmonyBotV54.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
"all_profiles":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
"liberation_toggle":"EnableUniversalHarmonicLiberationV54" in s,
"no_generic_floor_on_liberated_lane":"familyQualificationReason = \"LIBERATED_IDENTITY\"" in s and "qualificationPass = true" in s,
"core_lane":"PROVEN_CORE_ALPHA" in s and "V54CoreQualityEnvelope" in s,
"expansion_lane":"HARMONIC_EXPANSION_ALPHA" in s,
"core_priority":"V54ExecutionPriority" in s and "x += 2.0" in s,
"expansion_gate":"V54ExpansionEconomicAdmission" in s and "EXPANSION_ECONOMIC_REJECT" in s,
"rr_unchanged":'Minimum Net RR' in s and 'DefaultValue = 2.0' in s,
"risk_ceiling":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
"no_recovery":all(x not in s for x in ["Martingale","RecoveryGrid","Loss Averaging","DCA"]),
}
out={"version":"HarmonyBot V54","contract":"UNIVERSAL_HARMONIC_LIBERATION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V54_LIBERATION_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 5)
