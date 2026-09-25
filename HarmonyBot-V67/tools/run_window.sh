#!/usr/bin/env bash
set -euo pipefail
: "${1:?mode}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
MODE="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; SPREAD="${6:-1}"; BALANCE="${7:-10000}"; YEARS="${8:-0.5}"
case "$MODE" in V67_CONTROL|V67_PRODUCT) ;; *) echo "unsupported V67 mode $MODE" >&2; exit 64;; esac
C="$PWD/control"; W="$C/HarmonyBot-V67/window-$MODE-$WIN-B$BALANCE-S$SPREAD"; O="$C/HarmonyBot-V67/output-$MODE-$WIN-B$BALANCE-S$SPREAD"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V67/dist/HarmonyBot_V67_V52_Throughput_Family_Native_Commercial_Rebase_RC.algo" "$W/seal/algo/"
N="V67-$MODE-$WIN-B$BALANCE-S$SPREAD"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE="$BALANCE" SPREAD="$SPREAD" V67MODE="$MODE"  FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true  IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true  PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false  BACKTEST_TIMEOUT_SECONDS=2400 "$C/HarmonyBot-V67/tools/run_backtest.sh"
)
DATA_SHA=$((cd "$W/seal/data" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | awk '{print $1}')
python3 "$C/HarmonyBot-V67/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$MODE-$WIN.json" --window "$WIN" --family "$MODE" --years "$YEARS" --balance "$BALANCE" --spread "$SPREAD" --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
