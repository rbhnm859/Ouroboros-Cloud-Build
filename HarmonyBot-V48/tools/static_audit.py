#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V48/src/HarmonyBotV48.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V48" in s and "class HarmonyBotV48" in s and 'BotPrefix = "HB47"' in s,
 "frozen_confirmed_d_m1":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s and "_m5Bars" not in s,
 "canonical_standard":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "scale_route_frozen":"SECONDARY_SCALE_ABCD_ROUTE_REJECT" in s and "EnableScaleRouteAdmission" in s,
 "queue_states":all(x in s for x in ["SLOT_BLOCKED","PARKED","REVALIDATING","EXECUTABLE"]),
 "parked_no_reserved_risk":"PARKED_NO_BROKER_ORDER_NO_RESERVED_RISK" in s and "c.GridPlan = null;" in s,
 "hard_lifetime":"ParkedHardLifetimeMinutes" in s and "HARD_LIFETIME_EXPIRED" in s,
 "serial_handoff":"EnableEventDrivenSerialHandoff" in s and "TryScheduleAndExecute();" in s,
 "mandatory_revalidation":"RevalidateCandidateForExecution" in s and "winner.GridPlan = null;" in s,
 "remaining_rr":"c.NetRR < MinimumNetRR" in s,
 "pattern_native_m1":"UpdatePatternNativeM1State" in s and "PatternNativeM1MaxBars" in s,
 "decay_ranking":"OpportunityScore" in s and "PriceDriftPenalty".lower() not in s.lower() or True,
 "shadow_ledger":"V48-OPPORTUNITY-LOSS" in s and "ShadowMfeR" in s and "ShadowMaeR" in s,
 "slot_occupancy":"V48-SLOT-OCCUPANCY" in s and "_basketOccupancyMinutes" in s,
 "setup_dedupe":"_executedSetupKeys" in s and "EnableCanonicalSetupIdentity" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s and "2.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
# Fix expression precedence in one audit key explicitly.
checks["decay_ranking"]="OpportunityScore" in s and "priceDriftPenalty" in s and "thesisAgePenalty" in s and "marginBurdenPenalty" in s
out={"version":"HarmonyBot V48","architecture":"PATTERN_FAMILY_NATIVE_CONVERSION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V48_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
