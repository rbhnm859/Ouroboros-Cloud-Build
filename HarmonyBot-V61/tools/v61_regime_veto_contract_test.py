#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8"); b=s.split("private bool V61RegimeSurvivalPass",1)[1].split("private bool V61TryRatControlledExpansion",1)[0]
for t in ["AtrPercentile","Efficiency","TrendStrength","ExtensionAtr","ConfirmationScore","CurrentSpreadPips","PrzHigh","PrzLow"]: assert t in b,t
for bad in ["ShadowMfe","ShadowMae","[i + 1]","[i+1]"]: assert bad not in b,bad
assert 'Reject(c, "V61_REGIME_SURVIVAL_VETO")' in s
print("V61 veto-only regime survival contract PASS")
