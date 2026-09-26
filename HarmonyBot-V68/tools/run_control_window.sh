#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"
chmod +x "$C/HarmonyBot-V52/tools/"*.sh
SRC="$C/HarmonyBot-V52/output-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
DST="$C/HarmonyBot-V68/output-A_V52_EXACT_CONTROL-$WIN"
rm -rf "$DST"; mkdir -p "$DST/raw-logs"

# Immutable V52 control is executed exactly once per isolated Actions job. Re-running the
# cTrader CLI inside the same job reuses process/cache state and is not a valid dataset
# determinism test. Integrity is fail-closed on the immutable .algo SHA in the workflow,
# the parsed report contract below, and the cross-window reproduction gate downstream.
"$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"

SRC_JSON="$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json"
DST_JSON="$DST/A_V52_EXACT_CONTROL-$WIN.json"
test -s "$SRC_JSON"
cp "$SRC_JSON" "$DST_JSON"
if [ -d "$SRC/raw-logs" ]; then cp "$SRC/raw-logs/"* "$DST/raw-logs/" || true; fi

python3 - "$WIN" "$DST_JSON" "$DST/CONTROL_INTEGRITY.json" <<'PY'
import hashlib,json,sys
w,path,out=sys.argv[1:]
d=json.load(open(path))
rows=d.get("basket_outcomes")
required=("baskets","net","pf","expectancy","win_rate","max_dd_pct","engineering_clean")
missing=[k for k in required if k not in d]
valid_rows=isinstance(rows,list) and len(rows)>0
basket_match=valid_rows and int(d.get("baskets",-1))==len(rows)
clean=bool(d.get("engineering_clean",False))
payload=json.dumps(rows if isinstance(rows,list) else [],sort_keys=True,separators=(",",":"))
result={
  "window":w,
  "report_sha256":hashlib.sha256(open(path,"rb").read()).hexdigest(),
  "basket_outcomes_sha256":hashlib.sha256(payload.encode()).hexdigest(),
  "baskets":d.get("baskets"),
  "net":d.get("net"),
  "pf":d.get("pf"),
  "expectancy":d.get("expectancy"),
  "win_rate":d.get("win_rate"),
  "max_dd_pct":d.get("max_dd_pct"),
  "engineering_clean":clean,
  "summary_present":d.get("summary_present"),
  "broker_profile_present":d.get("broker_profile_present"),
  "missing_required_fields":missing,
  "basket_count_matches_outcomes":basket_match,
  "valid":not missing and valid_rows and basket_match and clean,
  "rule":"ONE_IMMUTABLE_CONTROL_RUN_PER_ISOLATED_JOB;FAIL_CLOSED_ON_REPORT_INTEGRITY;CROSS_WINDOW_GATE_OWNS_HISTORICAL_REPRODUCTION"
}
open(out,"w").write(json.dumps(result,indent=2))
if not result["valid"]:
    raise SystemExit("CONTROL_REPORT_INTEGRITY_FAIL_"+w)
PY
