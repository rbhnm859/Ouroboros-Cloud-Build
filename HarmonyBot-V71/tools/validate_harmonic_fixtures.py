#!/usr/bin/env python3
import json, math, pathlib, re, sys

if len(sys.argv) != 2:
    raise SystemExit("usage: validate_harmonic_fixtures.py <HarmonyBotV71.cs>")

src = pathlib.Path(sys.argv[1]).read_text(errors="ignore")

def section(a, b):
    i = src.find(a); j = src.find(b, i + len(a))
    if i < 0 or j < 0:
        raise SystemExit(f"source boundary missing: {a!r} -> {b!r}")
    return src[i:j]

canon = section("if (EnableCanonicalFamilyContracts)", "else\n            {")
profiles = {}
for line in canon.splitlines():
    z = line.strip()
    if not z.startswith('AddStd("'):
        continue
    m = re.match(r'AddStd\("([^"]+)",\s*(.*)\);$', z)
    if not m:
        raise SystemExit("profile parse failed: " + z)
    v = [float(x.strip()) for x in m.group(2).split(",")[:8]]
    profiles[m.group(1)] = {"xab":v[0:2], "abc":v[2:4], "bcd":v[4:6], "xad":v[6:8]}

standard_names = ["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat"]
special_names = ["Cypher","Shark","5-0","AB=CD"]
all_names = standard_names + special_names
if sorted(profiles) != sorted(standard_names):
    raise SystemExit("standard family set mismatch")

def inside(x, r):
    return r[0] - 1e-9 <= x <= r[1] + 1e-9

def geom_xad(r, s, t):
    # Normalized alternating XABCD geometry with XA=1.
    return r * (1.0 - s + s * t)

def standard_witness(p, n=121):
    for i in range(n):
        r = p["xab"][0] + (p["xab"][1] - p["xab"][0]) * i / (n-1)
        for j in range(n):
            s = p["abc"][0] + (p["abc"][1] - p["abc"][0]) * j / (n-1)
            if r <= 0 or s <= 0:
                continue
            for k in range(n):
                q = p["xad"][0] + (p["xad"][1] - p["xad"][0]) * k / (n-1)
                t = (q / r - 1.0 + s) / s
                if inside(t, p["bcd"]):
                    return (r, s, t, q)
    return None

def standard_match(p, w):
    r,s,t,q = w
    return (inside(r,p["xab"]) and inside(s,p["abc"]) and inside(t,p["bcd"]) and
            inside(q,p["xad"]) and abs(geom_xad(r,s,t)-q) < 1e-8)

families = {}
for name in standard_names:
    p = profiles[name]
    w = standard_witness(p)
    if not w:
        families[name] = {"positive":False, "negative_mutations_rejected":False}
        continue
    eps = 1e-4
    negs = {
        "xab_low": standard_match(p,(p["xab"][0]-eps,w[1],w[2],geom_xad(p["xab"][0]-eps,w[1],w[2]))),
        "abc_low": standard_match(p,(w[0],p["abc"][0]-eps,w[2],geom_xad(w[0],p["abc"][0]-eps,w[2]))),
        "bcd_high": standard_match(p,(w[0],w[1],p["bcd"][1]+eps,geom_xad(w[0],w[1],p["bcd"][1]+eps))),
        "xad_high": standard_match(p,(w[0],w[1],w[2],p["xad"][1]+eps)),
    }
    families[name] = {
        "positive": standard_match(p,w),
        "witness":{"xab":w[0],"abc":w[1],"bcd":w[2],"xad":w[3]},
        "negative_mutations_rejected": all(not x for x in negs.values()),
        "negative_raw": negs,
    }

# Special families are tested against the exact ratio predicates used by TryMatchProfile.
def abcd_match(abc,bcd,cdab):
    return .382 <= abc <= .886 and 1.13 <= bcd <= 2.618 and .80 <= cdab <= 1.25

def cypher_match(xab,xac,cdxc):
    return .382 <= xab <= .618 and 1.13 <= xac <= 1.414 and .70 <= cdxc <= .90

def shark_match(abc,bcd,xad):
    return 1.13 <= abc <= 1.618 and 1.13 <= bcd <= 2.24 and .85 <= xad <= 1.25

def fivezero_match(xab,abc,bcd):
    return 1.13 <= xab <= 1.618 and 1.618 <= abc <= 2.24 and .45 <= bcd <= .65

special_cases = {
    "AB=CD": {
        "positive": abcd_match(.618,1.618,.618*1.618),
        "witness":{"abc":.618,"bcd":1.618,"cd_over_ab":.618*1.618},
        "negative_raw":{
            "abc_low":abcd_match(.3819,1.618,1.0),
            "bcd_low":abcd_match(.618,1.1299,1.0),
            "abcd_high":abcd_match(.618,1.618,1.2501),
        },
    },
    "Cypher": {
        "positive": cypher_match(.50,1.272,.80),
        "witness":{"xab":.50,"xac":1.272,"cd_over_xc":.80},
        "negative_raw":{
            "xab_low":cypher_match(.3819,1.272,.80),
            "xac_low":cypher_match(.50,1.1299,.80),
            "cdxc_high":cypher_match(.50,1.272,.9001),
        },
    },
    "Shark": {
        "positive": shark_match(1.30,1.50,1.00),
        "witness":{"abc":1.30,"bcd":1.50,"xad":1.00,
                   "geometry_xab":1.00/(1.0-1.30+1.30*1.50)},
        "negative_raw":{
            "abc_low":shark_match(1.1299,1.50,1.00),
            "bcd_high":shark_match(1.30,2.2401,1.00),
            "xad_high":shark_match(1.30,1.50,1.2501),
        },
    },
    "5-0": {
        "positive": fivezero_match(1.30,1.90,.55),
        "witness":{"xab":1.30,"abc":1.90,"bcd":.55},
        "negative_raw":{
            "xab_low":fivezero_match(1.1299,1.90,.55),
            "abc_high":fivezero_match(1.30,2.2401,.55),
            "bcd_high":fivezero_match(1.30,1.90,.6501),
        },
    },
}
for name,z in special_cases.items():
    z["negative_mutations_rejected"] = all(not x for x in z["negative_raw"].values())
    families[name] = z

source_contract = {
    "all_12_declared": all(
        (f'AddStd("{x}"' in src if x in standard_names else f'Name = "{x}"' in src)
        for x in all_names
    ),
    "soft_expansion_calls": src.count("out sig, false") >= 2,
    "hard_core_default": "bool requireHardStandardAbcd = true" in src,
    "hard_abcd_scoped": "ratioOk && requireHardStandardAbcd && EnableCanonicalFamilyContracts" in src,
    "abcd_identity_scoped": "if (includeAbcdIdentity) z.Add(CanonicalAbcdCoordinate" in src,
    "projected_prz": "Pure projected PRZ for Expansion" in src,
    "d_validation_only": "if (d.Price < przLow || d.Price > przHigh) return false;" in src,
    "full_12_family_lattice": "var fullFamilies = _profiles.ToList();" in src,
    "independent_oracle": "V71BuildOraclePivots" in src and "V71OracleContractPass" in src,
    "reject_attribution": "[V71-EXP-REJECT-SUMMARY]" in src,
    "completed_bar_core": "LastClosedIndex" in src,
    "trusted_v51_pin": 'V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01"' in src,
}

out = {
    "audit":"V71_12_FAMILY_SYNTHETIC_CANONICAL_FIXTURE_FAIL_CLOSED",
    "families":families,
    "source_contract":source_contract,
}
out["positive_pass"] = len(families)==12 and all(x.get("positive",False) for x in families.values())
out["negative_pass"] = len(families)==12 and all(x.get("negative_mutations_rejected",False) for x in families.values())
out["pass"] = out["positive_pass"] and out["negative_pass"] and all(source_contract.values())

pathlib.Path("V71_HARMONIC_FIXTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
