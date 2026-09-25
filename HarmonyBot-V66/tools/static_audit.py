#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V66/src/HarmonyBotV66.cs").read_text()
forbidden=["CohortRecovery","OccupancyGovernor","FrozenPolicy","FrozenRecovery","FrozenOccupancy","CELL_POLICY","POSITIVE_COHORT","Martingale","Loss Averaging","RecoveryGrid","DCA"]
checks={
 "identity":"class HarmonyBotV66" in s and 'BotPrefix = "HB66"' in s,
 "default_product":'DefaultValue = "V66_PRODUCT"' in s,
 "control_mode":'"V66_V64_CONTROL"' in s and "V66ControlEnabled" in s,
 "evidence_engine":"V66EvidenceEngineEnabled" in s and "UpdateV66EvidenceAccumulator" in s,
 "six_bar_contract":'DefaultValue = 6, MinValue = 6, MaxValue = 6' in s and "V66_EVIDENCE_WINDOW_EXHAUSTED" in s,
 "unordered_evidence":"FamilyReclaim |=" in s and "FamilyBos |=" in s and "FamilyFailedExtension |=" in s and "V66Deceleration |=" in s,
 "family_route_sets":'p == "AB=CD"' in s and 'p == "Shark" || p == "5-0"' in s and 'p == "Cypher"' in s,
 "no_product_rescue":"!V66EvidenceEngineEnabled() && !confirmationPass && EnableM1RescueLane" in s,
 "v64_execution_contract":'TREND_ALIGNED_REVERSAL) return "CONDITIONAL_RUNNER"' in s and 'EXHAUSTION_REVERSAL) return "CONDITIONAL"' in s,
 "conditional_reproof":"TryArmNextConditionalLeg" in s and "DeeperLegThesisEligible" in s,
 "runner":"ConfigureV66SelectiveRunner" in s and "V66-RUNNER-SURVIVED-CANONICAL" in s,
 "risk":"ActualBasketWorstRisk" in s and '[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_research_layers":all(x not in s for x in forbidden)
}
o={"version":"HarmonyBot V66","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 66)
