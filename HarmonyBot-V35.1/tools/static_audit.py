#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V35.1/src/HarmonyBotV351.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V35.1" in s and "class HarmonyBotV351" in s and 'BotPrefix = "HB351"' in s,
 "v34_router_first":"HarmonicRoute baseRoute = RouteSignalV34" in s,
 "transition_semantics":"actualStateDisagreement = r.Transition || conflict == MtfConflict.TRANSITION" in s,
 "exhaustion_evidence":"structurallyExtended = r.ExtensionAtr >= 1.20" in s and "trendNotStrengthening = r.AdxH1Slope <= 0" in s,
 "legacy_confirmation_first":"double legacyScore = M1ConfirmationScore" in s and "legacyRequired" in s,
 "route_specific_veto":"RouteSpecificM1EvidencePass" in s and "ROUTE_SPECIFIC_M1_VETO" in s,
 "capital_gate_default_off":'[Parameter("Capital Feasibility Gate", DefaultValue = false)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "GAP_THROUGH_STRUCTURAL_INVALIDATION" in s,
 "risk_reconciliation":"ActualBasketWorstRisk" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_old_basket_prefix":'"HB34-' not in s and '"HB35-' not in s
}
out={"version":"HarmonyBot V35.1","checks":checks,"pass":all(checks.values())}
pathlib.Path("V351_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
