#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V54/src/HarmonyBotV54.cs").read_text(errors="ignore")
x={"liberation":"EnableUniversalHarmonicLiberationV54" in s and "V54FamilyLiberationQualityScore" in s,"core":"EnableCoreAlphaPreservationV54" in s and "V54CoreQualityEnvelope" in s and "V54ExecutionPriority" in s,"economic":"EnableExpansionEconomicGateV54" in s and "V54ExpansionEconomicAdmission" in s,"family_grid":"EnableFamilyGridAllocationV54" in s and "V54GridRiskWeight" in s,"state_grid":"EnableGridStateAwareV54" in s and "V54GridCancelMfeThreshold" in s,"rr":"MinimumNetRR" in s and "DefaultValue = 2.0" in s,"risk":"BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0" in s}
o={"version":"HarmonyBot V54","checks":x,"pass":all(x.values())};print(json.dumps(o,indent=2));raise SystemExit(0 if o["pass"] else 5)
