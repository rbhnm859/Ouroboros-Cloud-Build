#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"
chmod +x "$C/HarmonyBot-V52/tools/"*.sh
SRC="$C/HarmonyBot-V52/output-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
DST="$C/HarmonyBot-V68/output-A_V52_EXACT_CONTROL-$WIN"
TMP="$C/HarmonyBot-V68/control-stability-$WIN"
rm -rf "$DST" "$TMP"; mkdir -p "$DST/raw-logs" "$TMP"

# Two identical immutable-control runs on the same runner are required. If their basket
# outcomes differ, the broker/history source is not deterministic enough for causal use.
"$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"
cp "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json" "$TMP/R1.json"

"$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"
cp "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json" "$TMP/R2.json"

python3 - "$WIN" "$TMP/R1.json" "$TMP/R2.json" "$DST/DATASET_STABILITY.json" <<'PY'
import hashlib,json,sys
w,p1,p2,out=sys.argv[1:]
def fp(path):
    d=json.load(open(path))
    rows=d.get("basket_outcomes",[])
    canon=sorted(json.dumps(r,sort_keys=True,separators=(",",":")) for r in rows)
    payload=json.dumps(canon,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest(),d
h1,d1=fp(p1); h2,d2=fp(p2)
stable=h1==h2
result={
  "window":w,
  "replicate_1_sha256":h1,
  "replicate_2_sha256":h2,
  "stable":stable,
  "replicate_1":{"baskets":d1.get("baskets"),"net":d1.get("net"),"pf":d1.get("pf"),"expectancy":d1.get("expectancy")},
  "replicate_2":{"baskets":d2.get("baskets"),"net":d2.get("net"),"pf":d2.get("pf"),"expectancy":d2.get("expectancy")},
  "rule":"FAIL_CLOSED_IF_IDENTICAL_IMMUTABLE_CONTROL_RUNS_DIFFER"
}
open(out,"w").write(json.dumps(result,indent=2))
if not stable:
    raise SystemExit("DATASET_NONDETERMINISTIC_"+w)
PY

cp "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json" "$DST/A_V52_EXACT_CONTROL-$WIN.json"
if [ -d "$SRC/raw-logs" ]; then cp "$SRC/raw-logs/"* "$DST/raw-logs/" || true; fi
