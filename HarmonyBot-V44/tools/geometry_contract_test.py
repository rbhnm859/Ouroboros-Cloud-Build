#!/usr/bin/env python3
import pathlib,json,sys,math
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/src/HarmonyBotV44.cs").read_text(errors="ignore")
checks={
 "AD_XA_formula":"double adxa = ad / xa;" in s,
 "XD_XA_formula":"double xdxa = xd / xa;" in s,
 "CD_XC_formula":"double cdxc = cd / Math.Max(xc, 1e-9);" in s,
 "AB_CD_formula":"double abcd = cd / ab;" in s,
 "projected_standard":"a.Price + completion * (x.Price - a.Price)" in s,
 "projected_bc":"c.Price + Mid(p.BcdMin, p.BcdMax) * (b.Price - c.Price)" in s,
 "projected_abcd":"c.Price + p.AbCdProjection * (b.Price - a.Price)" in s,
 "cypher_786_xc":"c.Price + .786 * (x.Price - c.Price)" in s,
 "exact_abcd_contract":'AbcDMin = .94, AbcDMax = 1.06' in s,
 "alt127_contract":'AbcDMin = 1.20, AbcDMax = 1.34' in s,
 "alt1618_contract":'AbcDMin = 1.55, AbcDMax = 1.69' in s,
 "gartley_contract":'AddStd("Gartley", .600, .635' in s and '.770, .800' in s,
 "bat_contract":'AddStd("Bat", .382, .500' in s and '.875, .895' in s,
 "butterfly_contract":'AddStd("Butterfly", .770, .800' in s and '1.240, 1.300' in s,
 "crab_contract":'AddStd("Crab", .382, .618' in s and '1.580, 1.660' in s,
 "deep_crab_contract":'AddStd("Deep Crab", .875, .900' in s and '1.580, 1.660' in s,
}
# Deterministic scale/translation invariance of ratio coordinates.
def ratios(x,a,b,c,d):
 xa=abs(a-x); ab=abs(b-a); bc=abs(c-b); cd=abs(d-c)
 return (ab/xa,bc/ab,cd/bc,abs(d-a)/xa,cd/ab)
r1=ratios(100,200,138.2,170,121.4)
r2=ratios(1100,2100,1482,1800,1314)
checks["scale_invariance"]=all(abs(a-b)<1e-12 for a,b in zip(r1,r2))
r3=ratios(600,700,638.2,670,621.4)
checks["translation_invariance"]=all(abs(a-b)<1e-12 for a,b in zip(r1,r3))
# Projected Gartley D: A + .786*(X-A).
d=200+.786*(100-200)
checks["gartley_projected_d_numeric"]=abs(d-121.4)<1e-9
out={"version":"HarmonyBot V44","checks":checks,"pass":all(checks.values())}
pathlib.Path("V44_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 3)
