#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
variants=["V62_V51_EXACT_CONTROL","V62_DAG_SINGLE_ENTRY","V62_CURRENT_V61_GRID","V62_FRONT_LOADED_GRID","V62_CONDITIONAL_GRID","V62_CONDITIONAL_STRUCTURAL_EXIT","V62_CONDITIONAL_RUNNER","V62_PATTERN_NATIVE"]
checks={"variants":all(x in s for x in variants),"frontload":".70, .20, .10" in s,"conditional":".60, .25, .15, 0.0" in s,"reproof":"RouteSpecificM1EvidencePass(i, basket.Candidate.Signal, basket.Route)" in s,"runner":"V62_RUNNER_DETACHED_AFTER_CANONICAL_TP" in s,"risk":"ActualBasketWorstRisk" in s,"abcd_off":"V62_ABCD_STANDALONE_CAPITAL_OFF" in s}
print({"version":"HarmonyBot V62","checks":checks,"pass":all(checks.values())}); raise SystemExit(0 if all(checks.values()) else 2)