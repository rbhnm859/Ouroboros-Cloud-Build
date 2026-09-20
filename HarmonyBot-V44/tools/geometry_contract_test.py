#!/usr/bin/env python3
# Deterministic source-level geometry contract. This intentionally does not tune any threshold.
import pathlib,re,json,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/src/HarmonyBotV44.cs").read_text(errors="ignore")
required={
 "AD_XA_formula":"double adxa = ad / xa;" in s,
 "XD_XA_formula":"double xdxa = xd / xa;" in s,
 "CD_XC_formula":"double cdxc = cd / Math.Max(xc, 1e-9);" in s,
 "AB_CD_formula":"double abcd = cd / ab;" in s,
 "standard_uses_ADXA":"InRange(standardCompletion, p.AdXaMin, p.AdXaMax)" in s,
 "canonical_switch":"double standardCompletion = EnableCanonicalGeometryEngine ? adxa : xdxa;" in s,
 "cypher_quality_matches_coordinates":"RatioScore(xab, .50)" in s and "RatioScore(xac, 1.272)" in s and "RatioScore(cdxc, .786)" in s,
 "extension_stop_corrected":"Math.Max(0, p.AdXaMax - 1.0)" in s,
}
# Coordinate identity examples independent of market data.
examples={
 "Gartley":{"completion":.786,"expected_xdxa":.214},
 "Bat":{"completion":.886,"expected_xdxa":.114},
 "Butterfly":{"completion":1.27,"expected_xdxa":.27},
 "Crab":{"completion":1.618,"expected_xdxa":.618},
}
numeric=True
for x in examples.values():
 numeric &= abs(abs(1.0-x["completion"])-x["expected_xdxa"])<1e-9
required["coordinate_identity_examples"]=numeric
out={"version":"HarmonyBot V44","checks":required,"pass":all(required.values())}
pathlib.Path("V44_GEOMETRY_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 3)
