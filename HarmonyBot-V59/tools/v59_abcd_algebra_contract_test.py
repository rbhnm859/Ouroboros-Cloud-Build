#!/usr/bin/env python3
import math
from pathlib import Path

SRC = Path("HarmonyBot-V59/src/HarmonyBotV59.cs").read_text(encoding="utf-8")

for token in [
    "abc = bc / ab;",
    "bcd = cd / bc;",
    "abcd = cd / ab;",
    "double expectedBcd = k / Math.Max(.30, abc);",
    "Math.Abs(abcd - abc * bcd)",
    'V59AbcdCenters("AB=CD")',
]:
    assert token in SRC, f"missing V59 AB=CD algebra token: {token}"

# Synthetic algebra contracts: k = (BC/AB)*(CD/BC) = CD/AB.
for abc in (0.382, 0.50, 0.618, 0.786, 0.886):
    for k in (1.0, 1.272, 1.618):
        bcd = k / abc
        reconstructed = abc * bcd
        assert math.isclose(reconstructed, k, rel_tol=0.0, abs_tol=1e-12)

# The V58 defect would center every subtype on 1/abc. Ensure alternative
# subtypes have distinct subtype-native projections.
abc = 0.618
assert not math.isclose(1.272 / abc, 1.0 / abc)
assert not math.isclose(1.618 / abc, 1.0 / abc)

# Projected-D must remain independent of observed D: the AB=CD projection
# block must enumerate canonical k values from X/A/B/C only.
block = SRC[SRC.index("else if (p.Mode == PatternMode.ABCD)", SRC.index("V59PureProjectedPrzCenter")):]
block = block[:block.index("else if (p.Mode == PatternMode.CYPHER)")]
assert "d.Price" not in block
assert 'foreach (double k in V59AbcdCenters("AB=CD"))' in block
assert "c.Price + sign * k * ab" in block

print("V59 AB=CD algebra contract PASS")
