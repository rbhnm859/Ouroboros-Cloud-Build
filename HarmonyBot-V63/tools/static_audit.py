#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V63/src/HarmonyBotV63.cs").read_text()
checks={"identity":"class HarmonyBotV63" in s and 'BotPrefix = "HB63"' in s,
"default":'DefaultValue = "V63_CONDITIONAL_EXECUTION"' in s,
"risk":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
"v51_completion":"V63 preserves immutable V51 completion semantics" in s,
"cell_router":"V63PolicyFor" in s and "R1_TREND_EXPANSION" in s and "R2_TREND_EXHAUSTION" in s and "R3_COMPRESSION" in s and "R4_TRANSITION" in s,
"cohort":"V63TryPositiveCohortRecovery" in s,
"occupancy":"V63_OCCUPANCY_DECAY" in s,
"runner":"V63PolicyUsesRunner" in s and "V63-RUNNER-SURVIVED-CANONICAL" in s,
"right_tail":"V63-L3-SHADOW" in s,
"single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
"no_projected_d":"TryProjectProfile" not in s,
"prohibited":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"])}
o={"version":"HarmonyBot V63","checks":checks,"pass":all(checks.values())}; print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 2)