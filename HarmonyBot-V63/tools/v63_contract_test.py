#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V63/src/HarmonyBotV63.cs").read_text()
v=["V63_GOLDEN_V51_CONTROL","V63_V51_CONDITIONAL","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER","V63_POSITIVE_COHORT_RECOVERY","V63_OCCUPANCY_GOVERNOR"]
c={"identity":"class HarmonyBotV63" in s and 'BotPrefix = "HB63"' in s,"variants":all(x in s for x in v),"cell_router":"V63PolicyForCell" in s and "V63RegimeState" in s,"risk":"MaxValue = 1.0" in s,"no_projected_d":"TryProjectProfile" not in s}
print({"checks":c,"pass":all(c.values())});raise SystemExit(0 if all(c.values()) else 63)