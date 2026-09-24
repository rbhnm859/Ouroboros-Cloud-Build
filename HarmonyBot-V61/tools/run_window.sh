#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; SPREAD="${6:-1}"; BALANCE="${7:-10000}"; YEARS="${8:-0.5}"
case "$VAR" in V61_V51_EXACT_CONTROL|V61_DAG_CAPITAL_CONTROL|V61_CHAMPION_FIB_GRID|V61_GRID_REGIME_SURVIVAL|V61_COMMERCIAL_MAX) ;; *) exit 31;; esac
C="$PWD/control"; W="$C/HarmonyBot-V61/window-$VAR-$WIN-B$BALANCE-S$SPREAD"; O="$C/HarmonyBot-V61/output-$VAR-$WIN-B$BALANCE-S$SPREAD"; rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V61/dist/HarmonyBot_V61_Champion_Core_Fibonacci_Grid_Commercial_Rebase_RC.algo" "$W/seal/algo/"; N="V61-$VAR-$WIN-B$BALANCE-S$SPREAD"
( cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE="$BALANCE" SPREAD="$SPREAD" V61VARIANT="$VAR" BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V61/tools/run_backtest.sh" )
DATA_SHA=$((cd "$W/seal/data" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | awk '{print $1}')
python3 "$C/HarmonyBot-V61/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$VAR-$WIN.json" --window "$WIN" --variant "$VAR" --years "$YEARS" --balance "$BALANCE" --spread "$SPREAD" --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
