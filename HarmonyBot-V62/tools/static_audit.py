#!/usr/bin/env python3
import pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text()
need=[
"namespace cAlgo.Robots","public class HarmonyBotV62 : Robot","AccessRights = AccessRights.None",
"TimeFrame.Hour4","TimeFrame.Hour","TimeFrame.Minute15","TimeFrame.Minute",
"BasketRiskPercent","MaxValue = 1.0","V62_V51_EXACT_CONTROL","V62_DAG_SINGLE_ENTRY",
"V62_CURRENT_V61_GRID","V62_FRONT_LOADED_GRID","V62_CONDITIONAL_GRID",
"V62_CONDITIONAL_STRUCTURAL_EXIT","V62_CONDITIONAL_RUNNER","V62_PATTERN_NATIVE",
"V62-L3-SHADOW","V62-CONDITIONAL-LEG-CHECK","V62-ECONOMIC-ATTRIBUTION","V62-LEG-ECON",
"ActualBasketWorstRisk","PostFillSafetyKernel","EnsureServerProtection","projectedD=false"
]
missing=[x for x in need if x not in s]
if missing: raise SystemExit("STATIC_AUDIT_FAIL "+repr(missing))
print("STATIC_AUDIT_PASS")
