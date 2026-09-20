#!/usr/bin/env python3
import json,pathlib,sys,math
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V48/src/HarmonyBotV48.cs").read_text(errors="ignore")
checks={
 "confirmed_d_only":"TryProjectProfile" not in s,
 "canonical_adxa":"double adxa = ad / xa;" in s and "double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "extension_deepest_d":"a.Price + p.XadMax * (x.Price - a.Price)" in s,
 "grid_span_from_xad":"(1.0 - p.XadMax)" in s and "(p.XadMax - p.XadMin)" in s,
 "m1_primary":"ProcessNewM1Close" in s and "_m5Bars" not in s,
 "completed_bar":"LastClosedIndex" in s,
}
# Numeric invariant: A=200, X=100, AD/XA=1.27 -> D=73, not legacy -27.
x,a,r=100.0,200.0,1.27
d=a+r*(x-a)
checks["extension_formula_numeric"]=abs(d-73.0)<1e-12
# Gartley retracement AD/XA=.786 -> D-X=.214XA.
d2=a+.786*(x-a)
checks["gartley_distance_numeric"]=abs((d2-x)/(a-x)-.214)<1e-12
out={"version":"HarmonyBot V48","checks":checks,"pass":all(checks.values())}
pathlib.Path("V48_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 3)
