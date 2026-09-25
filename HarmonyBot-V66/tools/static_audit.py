#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
checks={
"identity":"class HarmonyBotV66" in s and 'BotPrefix = "HB65"' in s,
"alpha_truth":"V66AlphaTruthScore" in s and "V66AlphaTruthEligible" in s,
"pre_entry":"record.AlphaTruthScore = V66AlphaTruthScore" in s,
"regimes":all(x in s for x in ['"SHOCK"','"TRANSITION"','"DIRECTIONAL"','"CHOP"','"BALANCED"']),
"no_future_features":all(x not in s for x in ["FutureOutcome","ForwardMfe","ForwardMae","YearGate","DateGate"]),
"fixed_execution":all(x in s for x in ["V66RouteGridContract","ConfigureV66SelectiveRunner","DeeperLegThesisEligible"]),
"risk":"ActualBasketWorstRisk" in s and '[Parameter("Basket Risk %", DefaultValue = 1.0' in s,
"alpha_reject":"ALPHA_TRUTH_REGIME_REJECT" in s
}
o={"version":"HarmonyBot V66","checks":checks,"pass":all(checks.values())};print(json.dumps(o,indent=2));raise SystemExit(0 if o["pass"] else 65)
