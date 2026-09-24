#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V63/src/HarmonyBotV63.cs").read_text()
variants=["V63_CONDITIONAL_EXECUTION","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER","V63_POSITIVE_COHORT_RECOVERY","V63_OCCUPANCY_GOVERNOR"]
checks={"variants":all(x in s for x in variants),"v51_supply":"return UpdateV63StageAwareFamilyCompletionEvidence" not in s,"conditional":".60,.25,.15" in s and ".70,.30" in s,"policy":"Family" not in s or "V63PolicyFor" in s,"recovery":"V63-COHORT-RECOVERY" in s,"occupancy":"V63-OCCUPANCY-RELEASE" in s,"runner":"SINGLE_RUNNER" in s and "CONDITIONAL_RUNNER" in s,"risk":"ActualBasketWorstRisk" in s and "basket.InitialBasketRisk + 1e-8" in s}
print({"version":"HarmonyBot V63","checks":checks,"pass":all(checks.values())}); raise SystemExit(0 if all(checks.values()) else 2)