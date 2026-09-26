#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"
chmod +x "$C/HarmonyBot-V52/tools/"*.sh
SRC="$C/HarmonyBot-V52/output-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
DST="$C/HarmonyBot-V69/output-A_V52_EXACT_CONTROL-$WIN"
TMP="$C/HarmonyBot-V69/control-stability-$WIN"
VW="$C/HarmonyBot-V52/window-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
VN="V52-FAMILY_IDENTITY_RECONSTRUCTION-$WIN-B10000"
rm -rf "$DST" "$TMP"; mkdir -p "$DST/raw-logs" "$TMP"

run_rep () {
  local tag="$1"
  # V69 re-entrancy fix: a repeated V52 run must never inherit a completed report from
  # the previous replicate. The history data cache is retained, but report/log state is isolated.
  rm -f "$VW/seal/reports/$VN.json" "$VW/seal/reports/$VN.html" "$VW/seal/logs/$VN.log"
  "$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"
  test -s "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json"
  cp "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json" "$TMP/$tag.json"
}

run_rep R1
run_rep R2

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
stable=h1==h2 and d1.get("baskets",0)>0 and d2.get("baskets",0)>0
result={
 "window":w,"replicate_1_sha256":h1,"replicate_2_sha256":h2,"stable":stable,
 "replicate_1":{k:d1.get(k) for k in ("baskets","net","pf","expectancy","win_rate","max_dd_pct")},
 "replicate_2":{k:d2.get(k) for k in ("baskets","net","pf","expectancy","win_rate","max_dd_pct")},
 "rule":"FAIL_CLOSED_IF_NONZERO_IDENTICAL_IMMUTABLE_CONTROL_REPLICATES_DIFFER"
}
open(out,"w").write(json.dumps(result,indent=2))
if not stable: raise SystemExit("DATASET_NONDETERMINISTIC_OR_EMPTY_"+w)
PY

cp "$TMP/R2.json" "$DST/A_V52_EXACT_CONTROL-$WIN.json"
if [ -d "$SRC/raw-logs" ]; then cp "$SRC/raw-logs/"* "$DST/raw-logs/" || true; fi
