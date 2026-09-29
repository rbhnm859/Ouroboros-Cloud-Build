#!/usr/bin/env python3
import json, pathlib, re, sys, math

if len(sys.argv) != 2:
    raise SystemExit("usage: validate_harmonic_contracts.py <HarmonyBotV71.cs>")

path = pathlib.Path(sys.argv[1])
src = path.read_text(errors="ignore")

def between(a, b, text=src):
    i = text.find(a)
    j = text.find(b, i + len(a))
    if i < 0 or j < 0:
        raise SystemExit(f"missing source boundary: {a!r} -> {b!r}")
    return text[i:j]

canonical = between("if (EnableCanonicalFamilyContracts)", "else\n            {")
profiles = {}
for line in canonical.splitlines():
    z = line.strip()
    if not z.startswith('AddStd("'):
        continue
    m = re.match(r'AddStd\("([^"]+)",\s*(.*)\);$', z)
    if not m:
        raise SystemExit(f"cannot parse canonical profile line: {z}")
    parts = [x.strip() for x in m.group(2).split(",")]
    if len(parts) < 8:
        raise SystemExit(f"not enough ratio fields for {m.group(1)}: {parts}")
    vals = [float(x) for x in parts[:8]]
    profiles[m.group(1)] = {
        "xab": vals[0:2], "abc": vals[2:4], "bcd": vals[4:6], "xad": vals[6:8]
    }

expected_std = ["Gartley", "Bat", "Alt Bat", "Butterfly", "Crab", "Deep Crab", "Deep Gartley", "Rat"]
special = ["Cypher", "Shark", "5-0", "AB=CD"]
if sorted(profiles) != sorted(expected_std):
    raise SystemExit(f"canonical standard profile parse mismatch: {sorted(profiles)}")

def lin(lo, hi, n=61):
    if n <= 1:
        return [(lo + hi) * .5]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]

# For a standard bullish/bearish XABCD geometry normalized to XA=1:
# XAB=r, ABC=s, BCD=t -> AD/XA = r*(1-s+s*t).
# This identity is orientation invariant and exposes contradictory ratio contracts.
def primary_witness(p):
    for r in lin(*p["xab"]):
        for s in lin(*p["abc"]):
            if r <= 0 or s <= 0:
                continue
            for q in lin(*p["xad"]):
                t = (q / r - 1.0 + s) / s
                if p["bcd"][0] - 1e-9 <= t <= p["bcd"][1] + 1e-9:
                    return {
                        "xab": r, "abc": s, "bcd": t, "xad": q,
                        "cd_over_ab": s * t
                    }
    return None

legacy_bands = {
    "Gartley": [(0.94,1.06),(1.20,1.34)],
    "Bat": [(0.94,1.06),(1.20,1.34)],
    "Alt Bat": [(1.55,1.69)],
    "Butterfly": [(0.94,1.06),(1.20,1.34),(1.55,1.69)],
    "Crab": [(1.20,1.34),(1.55,1.69)],
    "Deep Crab": [(0.94,1.06),(1.20,1.34)],
}
def legacy_hard_witness(p, name):
    bands = legacy_bands.get(name)
    if not bands:
        return primary_witness(p)
    for r in lin(*p["xab"]):
        for s in lin(*p["abc"]):
            if r <= 0 or s <= 0:
                continue
            for q in lin(*p["xad"]):
                t = (q / r - 1.0 + s) / s
                if not (p["bcd"][0] - 1e-9 <= t <= p["bcd"][1] + 1e-9):
                    continue
                cdab = s * t
                if any(lo <= cdab <= hi for lo,hi in bands):
                    return {"xab":r,"abc":s,"bcd":t,"xad":q,"cd_over_ab":cdab}
    return None

expansion = between(
    "private List<PatternSignal> V71DetectExpansionPatternCandidates",
    "private HarmonicState GetActiveHarmonicState"
)
source_checks = {
    "expansion_uses_soft_contract_twice": expansion.count("out sig, false") == 2,
    "no_expansion_hard_abcd_prefilter": "StandardFamilyAbcdCompatible(profile.Name, abcd)" not in expansion,
    "core_default_contract_preserved": "bool requireHardStandardAbcd = true" in src,
    "core_hard_abcd_still_fail_closed": "requireHardStandardAbcd && EnableCanonicalFamilyContracts" in src,
    "expansion_abcd_removed_from_identity_score": "if (includeAbcdIdentity) z.Add(CanonicalAbcdCoordinate" in src,
    "projected_prz_from_pre_d_legs": "Pure projected PRZ for Expansion" in src and "double coreLo = Math.Max(xaLo, bcLo)" in src,
    "completed_d_validates_not_defines_prz": "if (d.Price < przLow || d.Price > przHigh) return false;" in src,
    "v51_trusted_parent_pin_present": 'V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01"' in src,
    "all_special_families_declared": all((f'Name = "{x}"' in src) for x in special),
}

family = {}
for name in expected_std:
    p = profiles[name]
    pw = primary_witness(p)
    lw = legacy_hard_witness(p, name)
    family[name] = {
        "primary_contract_feasible": pw is not None,
        "primary_witness": pw,
        "legacy_hard_abcd_feasible": lw is not None,
        "legacy_hard_abcd_witness": lw,
    }

legacy_dead = sorted(name for name,z in family.items() if not z["legacy_hard_abcd_feasible"])
all_primary = all(z["primary_contract_feasible"] for z in family.values())
root_cause_reproduced = "Alt Bat" in legacy_dead and "Crab" in legacy_dead

out = {
    "version": "HarmonyBot V71",
    "audit": "FAMILY_CONTRACT_FEASIBILITY_AND_EXPANSION_IDENTITY_SEPARATION",
    "standard_families": family,
    "legacy_dead_contracts": legacy_dead,
    "root_cause_reproduced": root_cause_reproduced,
    "source_checks": source_checks,
    "primary_contracts_all_feasible": all_primary,
    "pass": all_primary and root_cause_reproduced and all(source_checks.values()),
}
pathlib.Path("V71_HARMONIC_CONTRACT_AUDIT.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
raise SystemExit(0 if out["pass"] else 2)
