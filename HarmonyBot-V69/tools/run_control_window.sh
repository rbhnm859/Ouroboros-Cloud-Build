#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"; C="$PWD/control"
chmod +x "$C/HarmonyBot-V52/tools/"*.sh
SRC="$C/HarmonyBot-V52/output-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
DST="$C/HarmonyBot-V69/output-A_V52_EXACT_CONTROL-$WIN"
rm -rf "$DST"; mkdir -p "$DST/raw-logs"
"$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"
SRC_JSON="$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json"; DST_JSON="$DST/A_V52_EXACT_CONTROL-$WIN.json"
test -s "$SRC_JSON"; cp "$SRC_JSON" "$DST_JSON"
if [ -d "$SRC/raw-logs" ]; then cp "$SRC/raw-logs/"* "$DST/raw-logs/" || true; fi
python3 - "$WIN" "$DST_JSON" "$DST/CONTROL_INTEGRITY.json" <<'PY'
import hashlib,json,sys
w,path,out=sys.argv[1:]; d=json.load(open(path)); rows=d.get("basket_outcomes")
req=("baskets","net","pf","expectancy","win_rate","max_dd_pct","engineering_clean")
missing=[k for k in req if k not in d]; valid=isinstance(rows,list) and len(rows)>0
match=valid and int(d.get("baskets",-1))==len(rows)
zero=("execution_errors","grid_risk_violations","actual_basket_risk_violations","margin_risk_violations","stop_widening_violations","duplicate_grid_legs","orphan_pending_orders","unprotected_survivors","post_fill_protection_failures","execution_state_violations")
clean=bool(d.get("engineering_clean",False)) and all(int(d.get(k,0) or 0)==0 for k in zero)
payload=json.dumps(rows if isinstance(rows,list) else [],sort_keys=True,separators=(",",":"))
r={"window":w,"report_sha256":hashlib.sha256(open(path,"rb").read()).hexdigest(),"basket_outcomes_sha256":hashlib.sha256(payload.encode()).hexdigest(),"baskets":d.get("baskets"),"engineering_clean":clean,"missing_required_fields":missing,"basket_count_matches_outcomes":match,"hard_zero":{k:d.get(k,0) for k in zero},"valid":not missing and valid and match and clean,"rule":"IMMUTABLE_BINARY_SHA;ONE_ISOLATED_CONTROL_RUN;REPORT_INTEGRITY;CROSS_WINDOW_REFERENCE_GATE"}
open(out,"w").write(json.dumps(r,indent=2))
if not r["valid"]: raise SystemExit("CONTROL_REPORT_INTEGRITY_FAIL_"+w)
PY
