#!/usr/bin/env bash
set -euo pipefail
: "${1:?mode}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
MODE="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; SPREAD="${6:-1}"; BALANCE="${7:-10000}"; YEARS="${8:-0.5}"
case "$MODE" in V69_V52_EXACT_CONTROL|V69_FAMILY_STATE|V69_FAMILY_STATE_GRID) ;; *) echo "unsupported V69 mode $MODE" >&2; exit 64;; esac
C="$PWD/control"; W="$C/HarmonyBot-V69/window-$MODE-$WIN-B$BALANCE-S$SPREAD"; O="$C/HarmonyBot-V69/output-$MODE-$WIN-B$BALANCE-S$SPREAD"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V69/dist/HarmonyBot_V69_V52_Exact_Family_State_Grid_Commercial_Rebase_RC.algo" "$W/seal/algo/"
N="V69-$MODE-$WIN-B$BALANCE-S$SPREAD"
( cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE="$BALANCE" SPREAD="$SPREAD" V69MODE="$MODE" BACKTEST_TIMEOUT_SECONDS=2400 "$C/HarmonyBot-V69/tools/run_backtest.sh" )
DATA_SHA=$((cd "$W/seal/data" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | awk '{print $1}')
python3 "$C/HarmonyBot-V69/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$MODE-$WIN.json" --window "$WIN" --mode "$MODE" --years "$YEARS" --balance "$BALANCE" --spread "$SPREAD" --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
