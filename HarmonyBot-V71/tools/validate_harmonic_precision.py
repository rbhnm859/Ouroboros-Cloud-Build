#!/usr/bin/env python3
import json,pathlib,re,sys
from harmonic_precision_contract import CANONICAL_5DP,DETECTION_ENVELOPES_5DP,contract_audit

if len(sys.argv)!=2:
    raise SystemExit("usage: validate_harmonic_precision.py <HarmonyBotV71.cs>")
src=pathlib.Path(sys.argv[1]).read_text(errors="strict")

def between(a,b):
    i=src.find(a);j=src.find(b,i+len(a))
    if i<0 or j<0:raise SystemExit("precision audit source boundary missing")
    return src[i:j]

canon=between("if (EnableCanonicalFamilyContracts)","else\n            {")
parsed={}
for line in canon.splitlines():
    z=line.strip()
    if not z.startswith('AddStd("'):continue
    m=re.match(r'AddStd\("([^"]+)",\s*(.*)\);$',z)
    if not m:raise SystemExit("precision audit profile parse failed: "+z)
    v=[float(x.strip()) for x in m.group(2).split(",")[:8]]
    key=m.group(1).replace(" ","")
    parsed[key]={"xab":tuple(v[0:2]),"abc":tuple(v[2:4]),"bcd":tuple(v[4:6]),"xad":tuple(v[6:8])}

issues=[]
for fam,expected in DETECTION_ENVELOPES_5DP.items():
    got=parsed.get(fam)
    if got is None:
        issues.append({"family":fam,"reason":"MISSING_STANDARD_PROFILE"});continue
    for leg,band in expected.items():
        gv=got.get(leg)
        if gv is None or any(abs(float(gv[i])-float(band[i]))>0.000005 for i in (0,1)):
            issues.append({"family":fam,"leg":leg,"reason":"DETECTION_ENVELOPE_DRIFT",
                           "expected":[round(x,5) for x in band],
                           "actual":None if gv is None else [round(x,5) for x in gv]})

special_checks={
 "Cypher": all(x in src for x in ("InRange(xab, .382, .618)","InRange(xc / xa, 1.13, 1.414)","InRange(cd / Math.Max(xc, 1e-9), .70, .90)")),
 "Shark": all(x in src for x in ("InRange(abc, 1.13, 1.618)","InRange(bcd, 1.13, 2.24)","InRange(xad, .85, 1.25)")),
 "FiveZero": all(x in src for x in ("InRange(xab, 1.13, 1.618)","InRange(abc, 1.618, 2.24)","InRange(bcd, .45, .65)")),
 "ABCD": all(x in src for x in ("InRange(abc, p.AbcMin, p.AbcMax)","InRange(bcd, p.BcdMin, p.BcdMax)","InRange(abcd, p.AbcDMin, p.AbcDMax)"))
}
for fam,ok in special_checks.items():
    if not ok:issues.append({"family":fam,"reason":"SPECIAL_FAMILY_PREDICATE_DRIFT"})

base=contract_audit()
keys=sorted(CANONICAL_5DP)
expected_keys=sorted(["Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"])
if keys!=expected_keys:issues.append({"reason":"TWELVE_FAMILY_REGISTRY_MISMATCH","actual":keys})

formatted={
 fam:{leg:[f"{x:.5f}" for x in vals] for leg,vals in spec.items()}
 for fam,spec in CANONICAL_5DP.items()
}
out={
 "audit":"V74_FIVE_DECIMAL_HARMONIC_GEOMETRY_CONTRACT",
 "precision_decimals":5,
 "families":len(CANONICAL_5DP),
 "canonical_anchors_5dp":formatted,
 "base_contract":base,
 "source_special_checks":special_checks,
 "issues":issues,
 "pass":base["pass"] and not issues
}
pathlib.Path("V74_HARMONIC_PRECISION_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 74)
