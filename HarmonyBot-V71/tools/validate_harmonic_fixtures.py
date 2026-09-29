#!/usr/bin/env python3
import json, math, pathlib, re, sys
if len(sys.argv)!=2: raise SystemExit("usage: validate_harmonic_fixtures.py <HarmonyBotV71.cs>")
src=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
def section(a,b):
 i=src.find(a); j=src.find(b,i+len(a))
 if i<0 or j<0: raise SystemExit("source boundary missing")
 return src[i:j]
canon=section("if (EnableCanonicalFamilyContracts)","else\n            {")
profiles={}
for line in canon.splitlines():
 z=line.strip()
 if not z.startswith('AddStd("'): continue
 m=re.match(r'AddStd\("([^"]+)",\s*(.*)\);$',z)
 if not m: raise SystemExit("profile parse failed: "+z)
 v=[float(x.strip()) for x in m.group(2).split(",")[:8]]
 profiles[m.group(1)]={"xab":v[0:2],"abc":v[2:4],"bcd":v[4:6],"xad":v[6:8]}
expected=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat"]
if sorted(profiles)!=sorted(expected): raise SystemExit("standard family set mismatch")
def inside(x,r): return r[0]-1e-9<=x<=r[1]+1e-9
def geom(r,s,t): return r*(1-s+s*t)
def witness(p,n=121):
 for i in range(n):
  r=p["xab"][0]+(p["xab"][1]-p["xab"][0])*i/(n-1)
  for j in range(n):
   s=p["abc"][0]+(p["abc"][1]-p["abc"][0])*j/(n-1)
   if r<=0 or s<=0: continue
   for k in range(n):
    q=p["xad"][0]+(p["xad"][1]-p["xad"][0])*k/(n-1)
    t=(q/r-1+s)/s
    if inside(t,p["bcd"]): return (r,s,t,q)
 return None
def standard_match(p,w):
 r,s,t,q=w
 return inside(r,p["xab"]) and inside(s,p["abc"]) and inside(t,p["bcd"]) and inside(q,p["xad"]) and abs(geom(r,s,t)-q)<1e-8
families={}
for name in expected:
 p=profiles[name]; w=witness(p)
 if not w: families[name]={"positive":False}; continue
 pos=standard_match(p,w)
 eps=1e-4
 negs={
  "xab_low": standard_match(p,(p["xab"][0]-eps,w[1],w[2],geom(p["xab"][0]-eps,w[1],w[2]))),
  "abc_low": standard_match(p,(w[0],p["abc"][0]-eps,w[2],geom(w[0],p["abc"][0]-eps,w[2]))),
  "bcd_high": standard_match(p,(w[0],w[1],p["bcd"][1]+eps,geom(w[0],w[1],p["bcd"][1]+eps))),
  "xad_high": standard_match(p,(w[0],w[1],w[2],p["xad"][1]+eps))
 }
 families[name]={"positive":pos,"witness":{"xab":w[0],"abc":w[1],"bcd":w[2],"xad":w[3]},"negative_mutations_rejected":all(not x for x in negs.values()),"negative_raw":negs}
source_contract={
 "soft_expansion_calls": src.count("out sig, false")>=2,
 "hard_core_default": "bool requireHardStandardAbcd = true" in src,
 "hard_abcd_scoped": "ratioOk && requireHardStandardAbcd && EnableCanonicalFamilyContracts" in src,
 "abcd_identity_scoped": "if (includeAbcdIdentity) z.Add(CanonicalAbcdCoordinate" in src,
 "projected_prz": "Pure projected PRZ for Expansion" in src,
 "d_validation_only": "if (d.Price < przLow || d.Price > przHigh) return false;" in src,
 "completed_bar_core": "LastClosedIndex" in src,
 "trusted_v51_pin": 'V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01"' in src
}
special_declared={x:(f'Name = "{x}"' in src) for x in ["Cypher","Shark","5-0","AB=CD"]}
out={"audit":"V71_SYNTHETIC_CANONICAL_FIXTURE_FAIL_CLOSED","standard_families":families,"special_declared":special_declared,"source_contract":source_contract}
out["positive_pass"]=all(x.get("positive") for x in families.values())
out["negative_pass"]=all(x.get("negative_mutations_rejected") for x in families.values())
out["pass"]=out["positive_pass"] and out["negative_pass"] and all(source_contract.values()) and all(special_declared.values())
pathlib.Path("V71_HARMONIC_FIXTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
