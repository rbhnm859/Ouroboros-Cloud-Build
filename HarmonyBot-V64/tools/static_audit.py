#!/usr/bin/env python3
import json,pathlib,sys
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V64/src/HarmonyBotV64.cs")
s=p.read_text()
forbidden=["CohortRecovery","OccupancyGovernor","FrozenPolicy","FrozenRecovery","FrozenOccupancy","CELL_POLICY","POSITIVE_COHORT","UpdateV64StageAwareFamilyCompletionEvidence","V64DagStage","V64DagAnchorBar","TryProjectProfile","Martingale","Loss Averaging","RecoveryGrid","DCA"]
checks={
 "identity":"class HarmonyBotV64" in s and 'BotPrefix = "HB64"' in s,
 "product_default":'DefaultValue = "V64_PRODUCT"' in s,
 "two_modes":'"V64_PRODUCT"' in s and '"V64_V51_CONTROL"' in s and "V64ModeValid" in s,
 "three_layer_contract":"V64PolicyFor" in s and "V64RouteGridContract" in s,
 "trend_conditional_runner":'TREND_ALIGNED_REVERSAL) return "CONDITIONAL_RUNNER"' in s,
 "exhaustion_conditional":'EXHAUSTION_REVERSAL) return "CONDITIONAL"' in s,
 "transition_single":'return "SINGLE";' in s,
 "conditional_reproof":"DeeperLegThesisEligible" in s and "V64-CONDITIONAL-LEG-CHECK" in s,
 "runner":"ConfigureV64SelectiveRunner" in s and "V64-RUNNER-SURVIVED-CANONICAL" in s,
 "l3_shadow":"V64-L3-SHADOW" in s and "fraction=0.618" in s,
 "risk":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s and "ActualBasketWorstRisk" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_research_layers":all(x not in s for x in forbidden)
}
o={"version":"HarmonyBot V64","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 64)
