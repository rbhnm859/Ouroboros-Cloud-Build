#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8"); b=s.split("private void ConfigureV61SelectiveRunner",1)[1].split("private double V61LegTarget",1)[0]
assert "EXHAUSTION_REVERSAL) return" in b and "Math.Abs(x.RiskWeight - .30)" in b and ".15" in b and ".30" in b
assert "VolumeForRiskBudget" not in b and "ExecuteMarketOrder" not in b and "PlaceLimitOrder" not in b
assert "leg.RunnerEligible = true" in b and "leg.RunnerTarget = target" in b
print("V61 selective runner no-added-risk contract PASS")

assert "protectionTarget = V61LegTarget" in s
