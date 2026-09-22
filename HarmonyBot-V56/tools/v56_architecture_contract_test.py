from pathlib import Path
s=Path("HarmonyBot-V56/src/HarmonyBotV56.cs").read_text(encoding="utf-8")
checks={
"identity":"class HarmonyBotV56" in s and 'BotPrefix = "HB56"' in s,
"research_shadow":"RESEARCH_SHADOW" in s and "EVIDENCE_RESEARCH_SHADOW" in s,
"market_state":"EnableV56MarketStateEvidence" in s and "SessionVwap" in s and "ChoppinessNorm" in s and "TickVolumePercentile" in s,
"expected_r":"ExpectedNetRProxy" in s and "CommercialMarginProxy" in s,
"slot_cost":"CoreArrivalHazard" in s and "ExpectedRPerSlotHour" in s,
"core_priority":"ChampionCoreProtected" in s and "ThenByDescending" in s,
"abcd_strict":"V56AbcdStandaloneEvidence" in s,
"grid_v4":"EnableV56EvidenceGridV4" in s and "FamilyGridFractionsV4" in s,
"rr_immutable":'DefaultValue = 2.0' in s,
"risk_immutable":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
}
bad=[k for k,v in checks.items() if not v]
print({"version":"HarmonyBot V56","checks":checks,"pass":not bad})
if bad: raise SystemExit("V56 contract FAIL: "+",".join(bad))
