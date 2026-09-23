#!/usr/bin/env python3
from pathlib import Path

SRC = Path("HarmonyBot-V59/src/HarmonyBotV59.cs").read_text(encoding="utf-8")

required = [
    "EnableV59MinimalCoordinateManifold",
    "EnableV59OpportunityDensityLedger",
    "EnableV59HierarchicalPartialPooling",
    "V59FamilyEffectiveSampleSupport",
    "V59CanonicalManifoldScore",
    "familyConstraint",
    "MAXIMIZE_RESEARCH_SUPPLY_WITHOUT_RELAXING_CAPITAL_RISK",
]
for token in required:
    assert token in SRC, f"missing V59 architecture token: {token}"

fn = SRC[SRC.index("private double V59CanonicalManifoldScore"):]
fn = fn[:fn.index("private bool StandardFamilyAbcdCompatible")]
std = fn[fn.index("if (p.Mode == PatternMode.STANDARD)"):]
std = std[:std.index("else if (p.Mode == PatternMode.ABCD)")]

# Independent coordinates are counted directly; dependent XAD and AB/CD are
# aggregated into one family-constraint residual instead of two free dimensions.
assert "z.Add(RangeCoordinate(xab" in std
assert "z.Add(RangeCoordinate(abc" in std
assert "z.Add(RangeCoordinate(bcd" in std
assert "z.Add(familyConstraint)" in std
assert "z.Add(RangeCoordinate(xad" not in std
assert "z.Add(CanonicalAbcdCoordinate" not in std

# Safety gates must survive the rebase.
for token in [
    'Basket Risk %',
    'Minimum Net RR',
    'MaxActiveBasket',
    'EnableV59AbcdStandaloneCapital',
]:
    assert token in SRC

print("V59 minimal-coordinate/opportunity-density contract PASS")
