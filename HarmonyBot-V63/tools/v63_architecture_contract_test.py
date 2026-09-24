#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V63/src/HarmonyBotV63.cs").read_text()
v=["V63_GOLDEN_V51_CONTROL","V63_V51_CONDITIONAL","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER","V63_POSITIVE_COHORT_RECOVERY","V63_OCCUPANCY_GOVERNOR"]
c={"variants":all(x in s for x in v),"abcd_shadow":"V63_ABCD_STANDALONE_CAPITAL_OFF" in s,"depth":"V63-DEPTH-EVIDENCE" in s,"regime":"V63RegimeState" in s,"cell":"V63-CELL-POLICY" in s,"runner":"RUNNER" in s,"risk":"Basket Risk %" in s}
print({"checks":c,"pass":all(c.values())}); raise SystemExit(0 if all(c.values()) else 2)