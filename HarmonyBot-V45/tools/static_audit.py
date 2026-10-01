#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V45/src/HarmonyBotV45.cs")
s=p.read_text(errors="ignore")
patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"HarmonyBot V45" in s and "class HarmonyBotV45" in s and 'BotPrefix = "HB45"' in s,
 "restored_m1_kernel":"_m1Bars" in s and "ProcessNewM1Close" in s and "M1ConfirmationScore" in s,
 "no_m5_primary_gate":"_m5Bars" not in s and "ProcessNewM5Close" not in s,
 "no_projected_d":"ProjectedD" not in s and "TryProjectProfile" not in s,
 "legacy_replay_switch":"EnableCanonicalStandardCoordinates" in s and "double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "canonical_setup_identity":"EnableCanonicalSetupIdentity" in s and "BuildSetupGeometryKey" in s and "_executedSetupKeys" in s,
 "independent_pivot_graph":"new[] { 2, 3, 5 }" in s and "EnableIndependentPivotGraph" in s,
 "transition_proof":"EnableTransitionProofGate" in s and "actualStructuralTransition" in s,
 "m1_rescue":"EnableM1RescueLane" in s and "M1_RESCUE_ADMITTED" in s,
 "diversity_scheduler":"EnableDiversityScheduler" in s and "GroupBy(c => string.IsNullOrWhiteSpace(c.SetupKey)" in s,
 "abcd_subtype_observation":"ABCD_EXACT" in s and "ABCD_NEAR_127" in s and "ABCD_LEGACY_BROAD" in s,
 "all_12_profiles":all(('Name = "'+x+'"') in s or ('AddStd("'+x+'"') in s for x in patterns),
 "all_in_risk":"VolumeForRiskBudget" in s and "WorstCaseRisk" in s,
 "completed_bar":"LastClosedIndex" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s and "2.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V45","architecture":"RESTORED_EDGE_INDEPENDENT_SETUP_EXPANSION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V45_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
