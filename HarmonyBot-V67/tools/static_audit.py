#!/usr/bin/env python3
import json,pathlib,sys,re
s=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"HarmonyBot V67 — V52 Throughput Core Family-Native Grid Commercial Rebase" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_parent":"BuildFamilyHypothesisKey" in s and "EnableFamilyIdentityReconstruction" in s and "EnableBoundedPivotGraph" in s,
 "all_12_families":all(('"' + f + '"') in s for f in families),
 "family_native_quality":"V67FamilyQualityEligible" in s,
 "family_native_routes":"V67FamilyRouteSignal" in s,
 "family_completion":"UpdateFamilyCompletionEvidence" in s and 'p == "Shark"' in s and 'p == "Cypher"' in s and 'p == "AB=CD"' in s,
 "abcd_deconcentration":"V67_ABCD_BROAD_SHADOW_ONLY" in s and "V67AllowBroadAbcdCapital" in s,
 "family_fair_scheduler":"V67FamilyFairSchedulerEnabled" in s and "GroupBy(c => c.Signal != null ? c.Signal.PatternName" in s,
 "family_grid":"ConfigureV67FamilyGridProfiles" in s and "V67SetGrid" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s and "BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0" in s,
 "rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "completed_bars":"allCompletedBars=true" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_FAMILY_NATIVE_GRID_COMMERCIAL_REBASE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 67)
