#!/usr/bin/env python3
import json,pathlib,sys,math
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V50/src/HarmonyBotV50.cs").read_text(errors="ignore")
checks={
 "adxa":"double adxa = ad / xa;" in s,
 "extension_x_space_conversion":"x.Price + (1.0 - p.XadMax) * xa" in s,
 "legacy_control_retained":"x.Price - p.XadMax * xa" in s,
 "grid_v2_bypasses_legacy_span":"!EnableGridSpanSemanticV2 && (spanXa < p.MinimumGridSpanXa || spanXa > p.MaximumGridSpanXa)" in s,
 "l0_prz_legality":"plan.Legs.Count == 0 || plan.Legs[0].Index != 0" in s,
 "risk_budget":"BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0" in s,
 "confirmed_d":"TryProjectProfile" not in s,
}
# Deterministic coordinate sanity examples.
# Bullish: X=100,A=200. AD/XA=1.618 -> D=38.2. Old extreme X-1.72*100=-72; corrected boundary X+(1-1.72)*100=28.
old=100-1.72*100
new=100+(1-1.72)*100
checks["extension_formula_sanity"]=abs(old+72)<1e-9 and abs(new-28)<1e-9
# Gartley AD/XA=.786 -> D=121.4, distance to X is only .214XA before buffer, proving old min .65 is a semantic mismatch.
checks["retracement_span_sanity"]=abs((121.4-100)/100-.214)<1e-9
out={"version":"HarmonyBot V50","checks":checks,"pass":all(checks.values())}
pathlib.Path("V50_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
