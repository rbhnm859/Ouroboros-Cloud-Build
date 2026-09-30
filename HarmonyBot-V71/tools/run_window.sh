#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
EXPSHADOW=false; EXPEXEC=false; EXPGRID=false; EXPADAPRISK=false; EXPRISK=1.0; EXPEXIT=REACTION_2R; V72REACTION=false
case "$VAR" in
 SHADOW_PREPASS) EXPSHADOW=true; V72REACTION=true;;
 A_V51_PROTECTED_CORE) ;;
 B_V72_REACTION_ALPHA) EXPSHADOW=true; EXPEXEC=true; EXPEXIT=REACTION_2R; V72REACTION=true;;
 B_H5_SINGLE_REACTION) EXPSHADOW=true; EXPEXEC=true; EXPEXIT=REACTION_2R;;
 C_H5_GRID_REACTION) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true; EXPEXIT=REACTION_2R;;
 D_H5_SINGLE_RUNNER) EXPSHADOW=true; EXPEXEC=true; EXPEXIT=SELECTIVE_RUNNER;;
 E_H5_GRID_RUNNER) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true; EXPEXIT=SELECTIVE_RUNNER;;
 B_PROTECTED_XFIT_SINGLE) EXPSHADOW=true; EXPEXEC=true; EXPEXIT=REACTION_2R;;
 C_PROTECTED_XFIT_GRID) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true; EXPEXIT=REACTION_2R;;
 D_PROTECTED_XFIT_GRID_RISK5) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true; EXPADAPRISK=true; EXPRISK=5.0;;
 *) echo "unknown V71 variant $VAR"; exit 31;;
esac

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
N="V71-$VAR-$WIN-B10000"

EDGE_MODEL_SPEC="i:0;g:0;prz:0;conf:0;ts:0;pv:0;m1:0;rr:0;reg:0;eff:0;atr:0;ext:0;mtf:0;prior:0"; EDGE_PRIOR_SPEC="UNKNOWN:N:0"; EDGE_ALLOWED_PAIRS=""; EDGE_ALLOWED_CONTEXTS=""; EDGE_ALLOWED_SETUPS=""; EDGE_LCB_MARGIN=0; EDGE_MODEL_ID="DISABLED"; EDGE_MIN_LCB=0.015
if [ "$EXPEXEC" = true ] && [ "$V72REACTION" != true ]; then
 MODEL_DIR="${MODEL_DIR:-$C/HarmonyBot-V71/model}"
 MF="$MODEL_DIR/$WIN.json"
 case "$WIN" in H2024H2|H2025H1|H2025H2) MF="$MODEL_DIR/FULL.json";; esac
 test -s "$MF"
 eval "$(python3 - "$MF" <<'PY'
import json,shlex,sys
m=json.load(open(sys.argv[1]))
for k,v in [("EDGE_MODEL_SPEC",m["spec"]),("EDGE_PRIOR_SPEC",m["family_prior_spec"]),("EDGE_ALLOWED_PAIRS",m.get("allowed_pair_spec","")),("EDGE_ALLOWED_CONTEXTS",m.get("allowed_context_spec","")),("EDGE_ALLOWED_SETUPS",m.get("allowed_setup_hash_spec","")),("EDGE_LCB_MARGIN",str(m["lcb_margin"])),("EDGE_MODEL_ID",m["model_id"]),("EDGE_MIN_LCB",str(m.get("selection_lcb_r",0.015)))]:
 print(k+"="+shlex.quote(v))
PY
 )"
fi

(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  EXPSHADOW="$EXPSHADOW" EXPEXEC="$EXPEXEC" EXPGRID="$EXPGRID" EXPADAPRISK="$EXPADAPRISK" EXPRISK="$EXPRISK"  EDGE_MODEL_SPEC="$EDGE_MODEL_SPEC" EDGE_PRIOR_SPEC="$EDGE_PRIOR_SPEC" EDGE_ALLOWED_PAIRS="$EDGE_ALLOWED_PAIRS" EDGE_ALLOWED_CONTEXTS="$EDGE_ALLOWED_CONTEXTS" EDGE_ALLOWED_SETUPS="$EDGE_ALLOWED_SETUPS" EDGE_LCB_MARGIN="$EDGE_LCB_MARGIN" EDGE_MIN_LCB="$EDGE_MIN_LCB" EDGE_MODEL_ID="$EDGE_MODEL_ID" EXP_EXIT_POLICY="$EXPEXIT" V72REACTION="$V72REACTION"  IMMUTABLE_DATA=true BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V71/tools/run_backtest.sh"
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
