#!/usr/bin/env python3
import json,pathlib,sys,re
s=pathlib.Path(sys.argv[1]).read_text()
checks={
 "identity":"class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_control":"V67_V52_CONTROL" in s and "V67ProductEnabled" in s,
 "family_route_contract":"V67FamilyRouteEligible" in s,
 "parent_abcd_suppression":"PARENT_FAMILY_SUPPRESSED" in s and "V67SuppressParentAbcd" in s,
 "family_native_confirmation":"V67_FAMILY_NATIVE_CONFIRM" in s and "UpdatePatternNativeM1State" in s,
 "grid_normalization":"V67NormalizeGridRisk" in s and "INVALID_GRID_WEIGHT_SUM" in s,
 "whole_basket_risk":'Basket Risk %' in s and "ActualBasketWorstRisk" in s,
 "minimum_rr":'Minimum Net RR' in s and "MinimumNetRR" in s,
 "no_lookahead":"allCompletedBars=true" in s,
 "single_basket":"TryScheduleAndExecute" in s and "slotBusy" in s,
 "no_future_features":all(x not in s for x in ["FutureOutcome","ForwardMfe","ForwardMae","YearGate","DateGate"]),
 "no_recovery_logic":all(x not in s.lower() for x in ["martingale","loss averaging"])
}
o={"version":"HarmonyBot V67","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2))
raise SystemExit(0 if o["pass"] else 67)
