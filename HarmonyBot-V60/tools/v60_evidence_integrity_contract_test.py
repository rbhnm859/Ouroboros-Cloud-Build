#!/usr/bin/env python3
from pathlib import Path
SRC=Path("HarmonyBot-V60/src/HarmonyBotV60.cs").read_text(encoding="utf-8")
ALPHA=Path("HarmonyBot-V60/tools/build_v60_alpha_manifest.py").read_text(encoding="utf-8")
DENSITY=Path("HarmonyBot-V60/tools/family_opportunity_density.py").read_text(encoding="utf-8")
for token in ["UnderlyingGeometryId","CapitalThesisId","[V60-CONVEX-CLOSED]","setup={1}","PriorM1PeakR"]:
    assert token in SRC, f"missing evidence-integrity source token: {token}"
for token in ["V60_RESEARCH_CONTINUE_PATTERN_QUALITY","V60_RESEARCH_CONTINUE_ROUTER_NO_TRADE",
              "V60_ABCD_NESTED_PARENT_CONFLUENCE_ONLY","SECONDARY_SCALE_ABCD_ROUTE_RESEARCH_ONLY",
              "conv_rx","unique_capital_geometries","C1","C2","C3","AB=CD"]:
    assert token in ALPHA, f"missing cluster-aware Alpha evidence token: {token}"
assert "[V60-FAMILY-CONTRACT-SUMMARY]" in DENSITY
assert '"temporal_pass"' in DENSITY
print("V60 Evidence Integrity Gate0 contract PASS")
