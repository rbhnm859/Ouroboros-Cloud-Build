from pathlib import Path
s=Path("HarmonyBot-V58/src/HarmonyBotV58.cs").read_text(encoding="utf-8")
checks={
"identity":"class HarmonyBotV58" in s and 'BotPrefix = "HB58"' in s,
"risk":"[Parameter(\"Basket Risk %\", DefaultValue = 1.0" in s,
"rr":"[Parameter(\"Minimum Net RR\", DefaultValue = 2.0" in s,
"family_books":"_familyBooks" in s and "EnableV58FamilyBooks" in s,
"bounded_detector":"EnumerateBoundedPivotSequences" in s and "BuildFamilyHypothesisKey" in s,
"manifold":"V58CanonicalManifoldScore" in s and "EnableV58CanonicalManifold" in s,
"pure_prz":"V58PureProjectedPrzCenter" in s and "EnableV58PureProjectedPrz" in s,
"d_not_in_projection":"projections.Add(d.Price)" not in s,
"discrete_abcd":"V58AbcdDiscreteIdentity" in s and "1.272" in s and "1.618" in s,
"temporal_dag":"EnableV58TemporalEventDag" in s and "FirstSweepBar" in s and "FirstFailedExtensionBar" in s,
"capture":"V58-CAPTURE-CLOSED" in s and "EnableV58ExcursionCaptureLive" in s and "HybridR" in s,
"abcd_capital_off":"EnableV58AbcdStandaloneCapital" in s,
"no_v56_proxy":"ExpectedNetRProxy" not in s and "CommercialMarginProxy" not in s,
"no_grid_v4":"FamilyGridFractionsV4" not in s,
}
bad=[k for k,v in checks.items() if not v]
print({"version":"HarmonyBot V58","checks":checks,"pass":not bad})
if bad: raise SystemExit("V58 architecture contract FAIL: "+",".join(bad))
