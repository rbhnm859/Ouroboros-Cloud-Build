#!/usr/bin/env python3
import pathlib,json,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V45/src/HarmonyBotV45.cs").read_text(errors="ignore")
checks={
 "legacy_xdxa_available":"double xdxa = xd / xa;" in s,
 "canonical_adxa_available":"double adxa = ad / xa;" in s,
 "switchable_standard_completion":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "abcd_ratio":"double abcd = cd / ab;" in s and "AbCd = abcd" in s,
 "cypher_xc":"double xac = xc / xa;" in s,
 "confirmed_d_only":"TryProjectProfile" not in s,
 "scale_invariant_setup_key":"px(s.X.Price)" in s and "px(s.D.Price)" in s,
}
def ratios(x,a,b,c,d):
 xa=abs(a-x); ab=abs(b-a); bc=abs(c-b); cd=abs(d-c)
 return ab/xa,bc/ab,cd/bc,abs(d-a)/xa,abs(d-x)/xa,cd/ab
r1=ratios(100,200,138.2,170,121.4); r2=ratios(1000,2000,1382,1700,1214)
checks["ratio_scale_invariance"]=all(abs(a-b)<1e-12 for a,b in zip(r1,r2))
out={"version":"HarmonyBot V45","checks":checks,"pass":all(checks.values())}
pathlib.Path("V45_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 3)
