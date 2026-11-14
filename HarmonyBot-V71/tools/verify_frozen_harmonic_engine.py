#!/usr/bin/env python3
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1])
s=p.read_text(errors="strict")
start_marker="// ---------------- Harmonic engine ----------------"
end_marker="// ---------------- MTF conflict / regime / router ----------------"
a=s.find(start_marker); b=s.find(end_marker,a+1)
if a<0 or b<=a:
    raise SystemExit("frozen harmonic engine markers missing")
region=s[a:b]
actual=hashlib.sha256(region.encode()).hexdigest()
expected="508ea578b6605be3fadfdcdf5ab5d315bf854e15dc30abc6904d67d7e3af5f94"
expected_len=50068
out={"policy":"FROZEN_HARMONIC_ENGINE_CHANGE_ONLY_REVALIDATION",
     "sha256":actual,"expected_sha256":expected,
     "length":len(region),"expected_length":expected_len,
     "pass":actual==expected and len(region)==expected_len}
pathlib.Path("V71_FROZEN_HARMONIC_ENGINE_GUARD.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 73)
