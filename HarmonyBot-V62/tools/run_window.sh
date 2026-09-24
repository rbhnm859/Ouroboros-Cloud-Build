#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; SPREAD="${6:-1}"; BALANCE="${7:-10000}"; YEARS="${8:-0.5}"
case "$VAR" in
  V62_V51_EXACT_CONTROL|V62_DAG_SINGLE_ENTRY|V62_CURRENT_V61_GRID|V62_FRONT_LOADED_GRID|V62_CONDITIONAL_GRID|V62_CONDITIONAL_STRUCTURAL_EXIT|V62_CONDITIONAL_RUNNER|V62_PATTERN_NATIVE) ;;
  *) echo "unsupported V62 variant: $VAR" >&2; exit 31;;
esac
C="$PWD/control"
W="$C/HarmonyBot-V62/window-$VAR-$WIN-B$BALANCE-S$SPREAD"
O="$C/HarmonyBot-V62/output-$VAR-$WIN-B$BALANCE-S$SPREAD"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V62/dist/HarmonyBot_V62_Alpha_Preserving_Execution_Opportunity_Engine_RC.algo" "$W/seal/algo/"
N="V62-$VAR-$WIN-B$BALANCE-S$SPREAD"
( cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE="$BALANCE" SPREAD="$SPREAD" V62VARIANT="$VAR" BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V62/tools/run_backtest.sh" )
DATA_SHA=$((cd "$W/seal/data" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | awk '{print $1}')
python3 "$C/HarmonyBot-V62/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$VAR-$WIN.json" --window "$WIN" --variant "$VAR" --years "$YEARS" --balance "$BALANCE" --spread "$SPREAD" --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
