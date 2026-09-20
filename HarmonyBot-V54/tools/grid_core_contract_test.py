#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V54/src/HarmonyBotV54.cs").read_text(errors="ignore")
checks={
"grid_toggle":"EnableFibonacciGridExecution" in s,
"family_grid_toggle":"EnableFamilyGridAllocationV54" in s,
"state_aware_toggle":"EnableGridStateAwareV54" in s,
"family_weights":"V54GridRiskWeight" in s,
"family_depth":"V54GridMaxLegs" in s,
"state_cancel":"V54GridCancelMfeThreshold" in s and "MFE_GRID_CANCEL" in s,
"deep_leg_thesis":"DeeperLegThesisEligible" in s,
"original_levels":all(x in s for x in ["0.0, .236, .382, .618","0.0, .236, .382","0.0, .236"]),
"legacy_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s,
"whole_basket_budget":"BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0" in s,
"worst_case_guard":"WORST_CASE_BASKET_RISK" in s and "ActualBasketWorstRisk" in s,
"server_protection":"EnsureServerProtection" in s,
}
out={"version":"HarmonyBot V54","contract":"FIBONACCI_GRID_ALPHA_CORE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V54_GRID_CORE_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 6)
