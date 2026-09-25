#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V65/src/HarmonyBotV65.cs").read_text()
forbidden=["CohortRecovery","OccupancyGovernor","FrozenPolicy","FrozenRecovery","FrozenOccupancy","CELL_POLICY","POSITIVE_COHORT","Martingale","Loss Averaging","RecoveryGrid","DCA"]
checks={
 "identity":"class HarmonyBotV65" in s and 'BotPrefix = "HB65"' in s,
 "default_product":'DefaultValue = "V65_PRODUCT"' in s,
 "control_mode":'"V65_V64_CONTROL"' in s and "V65ControlEnabled" in s,
 "thesis_mode":"V65ThesisCompletionEnabled" in s and "UpdateV65ThesisCompletionEvidence" in s,
 "six_bar_contract":'DefaultValue = 6, MinValue = 6, MaxValue = 6' in s and "V65_THESIS_COMPLETION_WINDOW_EXHAUSTED" in s,
 "native_completion":"UpdateFamilyCompletionEvidence" in s and "UpdatePatternNativeM1State" in s,
 "route_proof":"RouteSpecificM1EvidencePass" in s and "V65-THESIS-COMPLETE" in s,
 "no_product_rescue":"!V65ThesisCompletionEnabled() && !confirmationPass && EnableM1RescueLane" in s,
 "v64_execution_contract":'TREND_ALIGNED_REVERSAL) return "CONDITIONAL_RUNNER"' in s and 'EXHAUSTION_REVERSAL) return "CONDITIONAL"' in s,
 "conditional_reproof":"TryArmNextConditionalLeg" in s and "DeeperLegThesisEligible" in s,
 "runner":"ConfigureV65SelectiveRunner" in s and "V65-RUNNER-SURVIVED-CANONICAL" in s,
 "risk":"ActualBasketWorstRisk" in s and '[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_research_layers":all(x not in s for x in forbidden)
}
o={"version":"HarmonyBot V65","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 65)
