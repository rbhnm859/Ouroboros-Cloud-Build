#!/usr/bin/env python3
import json,sys,pathlib,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V35/src/HarmonyBotV35.cs")
s=p.read_text(errors="ignore")
checks={
 "v35_identity":"HarmonyBot V35.0" in s and "class HarmonyBotV35" in s and 'BotPrefix = "HB35"' in s,
 "v34_post_fill_kernel":"PostFillSafetyKernel" in s and "GAP_THROUGH_STRUCTURAL_INVALIDATION" in s,
 "actual_fill_risk":"ActualBasketWorstRisk" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"EnsurePostFillProtection" in s and "ModifyStopLossPrice" in s and "ModifyTakeProfitPrice" in s,
 "state_machine":"TransitionLegState" in s and "STATE-VIOLATION" in s,
 "anti_hedge_single_basket":"OwnPositions().Any() || OwnPendingOrders().Any()" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "harmonic_quality":"HarmonicRobustnessScore" in s and "HarmonicRobustnessEligible" in s,
 "regime_context":"RegimeContextScore" in s and "AdxH1" in s and "AtrPercentile" in s and "Efficiency" in s,
 "enhanced_m1":"EnhancedM1ConfirmationScore" in s and "EnhancedM1Threshold" in s,
 "capital_precheck":"CapitalFeasibilityEligible" in s and "CAPITAL_INFEASIBLE_PRECHECK" in s,
 "no_recovery_words":not any(x in s for x in ["Martingale", "LossAveraging", "RecoveryLot", "HedgeRecovery"])
}
out={"version":"HarmonyBot V35.0","checks":checks,"pass":all(checks.values())}
pathlib.Path("V35_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
