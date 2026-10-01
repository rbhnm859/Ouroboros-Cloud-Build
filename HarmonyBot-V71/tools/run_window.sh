#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
EXPSHADOW=false; EXPEXEC=false; EXPGRID=false; EXPADAPRISK=false; EXPRISK=1.0; V72BIFURCATION=false; V72FAMILYNATIVE=false; V72FAILUREAUCTION=false; V72HCOG=false; V72HCAP=false; V73UNIVERSE=false; V74EXTERNAL=false; V74EMBEDDED=false
case "$VAR" in
 SHADOW_PREPASS) EXPSHADOW=true; V72BIFURCATION=true;;
 A_V51_PROTECTED_CORE) ;;
 B_V72_BIFURCATION_ALPHA) EXPSHADOW=true; EXPEXEC=true; V72BIFURCATION=true;;
 R_V72_FAMILY_NATIVE_CAUSAL) EXPSHADOW=true; V72FAMILYNATIVE=true;;
 B_V72_FAMILY_NATIVE_CAUSAL_ALPHA) EXPSHADOW=true; EXPEXEC=true; V72FAMILYNATIVE=true;;
 R_V72_FAILURE_AUCTION_CAUSAL) EXPSHADOW=true; V72FAILUREAUCTION=true;;
 R_V72_HCOG_CAUSAL) V72HCOG=true;;
 B_V72_HCOG_ALPHA) EXPEXEC=true; V72HCOG=true;;
 R_V72_HCAP_CENSUS) V72HCAP=true;;
 B_V72_HCAP_ALPHA) EXPEXEC=true; V72HCAP=true;;
 R_V73_OPPORTUNITY_UNIVERSE) V73UNIVERSE=true;;
 B_V75_FROZEN_POLICY_ALPHA) EXPEXEC=true; V73UNIVERSE=true; V74EXTERNAL=true;;
 B_V77_FROZEN_POLICY_GRID) EXPEXEC=true; EXPGRID=true; V73UNIVERSE=true; V74EXTERNAL=true;;
 B_V78_EMBEDDED_POLICY_ALPHA) EXPEXEC=true; V73UNIVERSE=true; V74EMBEDDED=true;;
 B_V78_EMBEDDED_POLICY_GRID) EXPEXEC=true; EXPGRID=true; V73UNIVERSE=true; V74EMBEDDED=true;;
 *) echo "unknown active V71/V72 variant $VAR"; exit 31;;
esac
if [[ "$V74EXTERNAL" == "true" || "$V74EMBEDDED" == "true" ]]; then
  EXPRISK="${V74_RISK_PCT:-$EXPRISK}"
fi

C="$PWD/control"; W="$C/HarmonyBot-V71/window-$VAR-$WIN"; O="$C/HarmonyBot-V71/output-$VAR-$WIN"
CUSTODY_MANIFEST="$C/HarmonyBot-V71/final/V71_BURNED_CALIBRATION_CUSTODY.json"
if [[ -z "${V71_EXPECTED_DATA_SHA256:-}" && -s "$CUSTODY_MANIFEST" ]]; then
 V71_EXPECTED_DATA_SHA256=$(python3 - "$CUSTODY_MANIFEST" "$WIN" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print(d.get("windows",{}).get(sys.argv[2],{}).get("sha256",""))
PY
 )
 export V71_EXPECTED_DATA_SHA256
fi
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
DATA_SEED="${V71_DATA_SEED_DIR:-}"
if [ -n "$DATA_SEED" ]; then
 test -d "$DATA_SEED" || { echo "[V71-DATA-SEED-FAIL] variant=$VAR window=$WIN reason=MISSING_SEED path=$DATA_SEED"; exit 42; }
 cp -a "$DATA_SEED"/. "$W/seal/data/"
 DATA_FILES=$(find "$W/seal/data" -type f | wc -l | tr -d " ")
 test "$DATA_FILES" -gt 0 || { echo "[V71-DATA-SEED-FAIL] variant=$VAR window=$WIN reason=EMPTY_SEED"; exit 43; }
 DATA_HASH=$(cd "$W/seal/data" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
 if [[ -n "${V71_EXPECTED_DATA_SHA256:-}" && "$DATA_HASH" != "$V71_EXPECTED_DATA_SHA256" ]]; then
  echo "[V71-DATA-CUSTODY-FAIL] variant=$VAR window=$WIN stage=pre expected=$V71_EXPECTED_DATA_SHA256 actual=$DATA_HASH"
  exit 45
 fi
 printf "%s\n" "$DATA_HASH" > "$O/DATA_SNAPSHOT_SHA256.txt"
 printf "%s\n" "$DATA_FILES" > "$O/DATA_SNAPSHOT_FILE_COUNT.txt"
 echo "[V71-DATA-SEED] variant=$VAR window=$WIN files=$DATA_FILES sha256=$DATA_HASH"
else
 echo "[V71-DATA-SEED-FAIL] variant=$VAR window=$WIN reason=UNSEEDED_GOVERNED_RUN"
 exit 44
fi
cp "$C/HarmonyBot-V71/dist/HarmonyBot_V71_Protected_Champion_Core_Incremental_Alpha.algo" "$W/seal/algo/"

HCAP_REV_MODEL="${HCAP_REV_MODEL:-}"
HCAP_CONT_MODEL="${HCAP_CONT_MODEL:-}"
if [[ "$VAR" == "B_V72_HCAP_ALPHA" ]]; then
  M=""
  for q in "$C/HarmonyBot-V71/model/HCAP_MANIFEST.json" "$C/HarmonyBot-V71/payoff/HCAP_MANIFEST.json"; do
    if [[ -s "$q" ]]; then M="$q"; break; fi
  done
  [[ -n "$M" ]] || { echo "[HCAP-MODEL-FAIL] missing HCAP_MANIFEST.json"; exit 49; }
  if [[ "$WIN" =~ ^Y202[123]$ ]]; then
    HCAP_REV_MODEL=$(python3 - "$M" "$WIN" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); print(d["folds"][sys.argv[2]]["reversal_model"])
PY
)
    HCAP_CONT_MODEL=$(python3 - "$M" "$WIN" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); print(d["folds"][sys.argv[2]]["continuation_model"])
PY
)
  else
    HCAP_REV_MODEL=$(python3 - "$M" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); print(d["final_models"]["reversal"])
PY
)
    HCAP_CONT_MODEL=$(python3 - "$M" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); print(d["final_models"]["continuation"])
PY
)
  fi
  [[ -n "$HCAP_REV_MODEL" && -n "$HCAP_CONT_MODEL" ]] || { echo "[HCAP-MODEL-FAIL] empty model"; exit 50; }
fi

N="V71-$VAR-$WIN-B10000"

(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  EXPSHADOW="$EXPSHADOW" EXPEXEC="$EXPEXEC" EXPGRID="$EXPGRID" EXPADAPRISK="$EXPADAPRISK" EXPRISK="$EXPRISK" V72BIFURCATION="$V72BIFURCATION" V72FAMILYNATIVE="$V72FAMILYNATIVE" V72FAILUREAUCTION="$V72FAILUREAUCTION" V72HCOG="$V72HCOG" V72HCAP="$V72HCAP" V73UNIVERSE="$V73UNIVERSE" V74EXTERNAL="$V74EXTERNAL" V74EMBEDDED="$V74EMBEDDED" V74_ALLOWED_HASHES="${V74_ALLOWED_HASHES:-}" V74_POLICY_UTILITY="${V74_POLICY_UTILITY:-}" V74_POLICY_HOLD="${V74_POLICY_HOLD:-}" V74_POLICY_PROTECTION="${V74_POLICY_PROTECTION:-}" HCAP_REV_MODEL="$HCAP_REV_MODEL" HCAP_CONT_MODEL="$HCAP_CONT_MODEL"  IMMUTABLE_DATA=true BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V71/tools/run_backtest.sh"
)
test -s "$W/seal/logs/$N.log"; test -s "$W/seal/reports/$N.json"
POST_DATA_HASH=$(cd "$W/seal/data" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
if [[ "$POST_DATA_HASH" != "$DATA_HASH" ]]; then
 echo "[V71-DATA-CUSTODY-FAIL] variant=$VAR window=$WIN stage=post pre=$DATA_HASH actual=$POST_DATA_HASH"
 exit 46
fi
if [[ -n "${V71_EXPECTED_DATA_SHA256:-}" && "$POST_DATA_HASH" != "$V71_EXPECTED_DATA_SHA256" ]]; then
 echo "[V71-DATA-CUSTODY-FAIL] variant=$VAR window=$WIN stage=post expected=$V71_EXPECTED_DATA_SHA256 actual=$POST_DATA_HASH"
 exit 47
fi
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"; cp "$W/seal/reports/$N.json" "$O/raw-report.json"
python3 "$C/HarmonyBot-V71/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$VAR-$WIN.json" --window "$WIN" --variant "$VAR" --years "$YEARS" --balance 10000 --data-snapshot "$O/DATA_SNAPSHOT_SHA256.txt"
