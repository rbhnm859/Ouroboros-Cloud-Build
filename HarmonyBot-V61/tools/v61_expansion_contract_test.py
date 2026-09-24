#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8"); b=s.split("private bool V61TryRatControlledExpansion",1)[1].split("private void ConfigureV61SelectiveRunner",1)[0]
assert 'sig.PatternName != "Rat"' in b
for t in ["V61RatMinGeometry","V61RatMinPrz","V61RatMinConfidence"]: assert t in b
assert 'DefaultValue = 0.72, MinValue = 0.72, MaxValue = 0.72' in s and 'DefaultValue = 0.68, MinValue = 0.68, MaxValue = 0.68' in s
print("V61 Rat-only expansion contract PASS")
