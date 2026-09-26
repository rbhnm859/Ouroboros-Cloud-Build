#!/usr/bin/env python3
import json,pathlib,sys,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V67 — V52 Throughput Core Family-Native Grid Commercial Rebase" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_parent":"BuildFamilyHypothesisKey" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
 "family_router":"V67FamilyNativeRoute" in s and "V67FamilyDetectorPriority" in s and "V67FamilyEvidencePrior" in s,
 "family_completion":"EnableV67FamilyNativeCompletion" in s and "UpdateFamilyCompletionEvidence" in s and "IsFamilyCompletionLane" in s,
 "abcd_not_primary":"EnableV67AbcdStandaloneCapital" in s and 'DefaultValue = false' in s and "_v67AbcdStandaloneSuppressed" in s,
 "family_grid":"EnableV67FamilyAwareGrid" in s and "V67FamilyGridWeights" in s and "ConfigureFibonacciGridProfiles" in s,
 "grid_levels":all(x in s for x in [".236",".382",".618"]),
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s and "ActualBasketWorstRisk" in s,
 "prevented_vs_actual":"_preventedRiskRejections" in s and "_actualBasketRiskViolations" in s,
 "rr_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "completed_bars":"allCompletedBars=true" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_year_alpha":all(x not in s for x in ["YearGate","DateGate","FutureOutcome","ForwardMfe","ForwardMae"]),
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_FAMILY_NATIVE_GRID_COMMERCIAL_REBASE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 67)
