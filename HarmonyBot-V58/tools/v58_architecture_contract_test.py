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
"temporal_dag":"EnableV58TemporalEventDag" in s and
               "Diagnostic first-occurrence timestamps are retained, but they no longer determine DAG validity." in s and
               "i > c.FamilyDagPreBar" in s and "i > c.FamilyDagConfirmBar" in s and "i > c.FamilyDagReclaimBar" in s,
"capture":"V58-CAPTURE-CLOSED" in s and "EnableV58ExcursionCaptureLive" in s and "HybridR" in s,
"abcd_capital_off":"EnableV58AbcdStandaloneCapital" in s,
"no_v56_proxy":"ExpectedNetRProxy" not in s and "CommercialMarginProxy" not in s,
"no_grid_v4":"FamilyGridFractionsV4" not in s,
}

# Temporal DAG synthetic contract: only events on bars after their predecessor may advance.
def dag_pass(sequence, stages):
    stage = 0
    predecessor_bar = -1
    for bar, events in enumerate(sequence):
        if stage >= len(stages):
            break
        if bar <= predecessor_bar:
            continue
        if any(event in events for event in stages[stage]):
            predecessor_bar = bar
            stage += 1
    return stage == len(stages)

retracement = [("rejection","failedExtension"), ("reclaim",), ("bos","displacement")]
extension = [("sweep",), ("failedExtension",), ("reclaim","insidePrz"), ("bos","displacement")]
five_zero = [("failedExtension",), ("bos",), ("retest",)]
shark = [("sweep",), ("failedExtension",), ("reclaim",), ("bos","displacement")]
abcd = [("deceleration",), ("failedExtension",), ("reclaim",), ("bos","displacement")]

temporal_regressions = {
    "retr_early_invalid_then_valid_pass": dag_pass([
        {"reclaim"}, {"rejection"}, {"reclaim"}, {"bos"}
    ], retracement),
    "retr_early_invalid_no_later_reclaim_fail": not dag_pass([
        {"reclaim"}, {"rejection"}, {"bos"}
    ], retracement),
    "extension_canonical_pass": dag_pass([
        {"sweep"}, {"failedExtension"}, {"reclaim"}, {"bos"}
    ], extension),
    "extension_post_before_reclaim_fail": not dag_pass([
        {"sweep"}, {"failedExtension"}, {"bos"}, {"reclaim"}
    ], extension),
    "same_bar_cascade_fail": not dag_pass([
        {"sweep","failedExtension","reclaim","bos"}
    ], extension),
    "shark_canonical_pass": dag_pass([
        {"sweep"}, {"failedExtension"}, {"reclaim"}, {"displacement"}
    ], shark),
    "five_zero_canonical_pass": dag_pass([
        {"failedExtension"}, {"bos"}, {"retest"}
    ], five_zero),
    "abcd_canonical_pass": dag_pass([
        {"deceleration"}, {"failedExtension"}, {"reclaim"}, {"bos"}
    ], abcd),
}
checks["temporal_dag_synthetic_regression"] = all(temporal_regressions.values())
checks["temporal_dag_no_parallel_post_latch"] = "c.FamilyDagStage >= 2 && c.FamilyDagAuxA && c.FamilyDagAuxB" not in s

bad=[k for k,v in checks.items() if not v]
print({"version":"HarmonyBot V58","checks":checks,"pass":not bad})
if bad: raise SystemExit("V58 architecture contract FAIL: "+",".join(bad))
