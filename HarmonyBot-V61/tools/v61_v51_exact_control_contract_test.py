#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8")
assert '[Parameter("V61 Variant", DefaultValue = "V61_V51_EXACT_CONTROL")]' in s
assert 'return string.Equals(V61Variant, "V61_V51_EXACT_CONTROL"' in s
assert "if (!V61ExactControlEnabled())\n                return UpdateV61StageAwareFamilyCompletionEvidence" in s
assert "if (record.Route == HarmonicRoute.NO_TRADE && V61CommercialMaxEnabled())" in s\nassert "V61_DAG_CAPITAL_CONTROL" in s
print("V61 exact-control static gate PASS; dynamic equivalence is enforced by immutable replay")
