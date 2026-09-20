#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL) FC=false; GRID=false; STOP=false;;
 FAMILY_COMPLETION_ONLY) FC=true; GRID=false; STOP=false;;
 GRID_SEMANTIC_V2) FC=true; GRID=true; STOP=false;;
 FULL_V50_COMMERCIAL) FC=true; GRID=true; STOP=true;;
 *) echo "unknown V50 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V50/window-$FAM-$WIN"; O="$C/HarmonyBot-V50/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V50/dist/HarmonyBot_V50_Pattern_Native_Structural_Grid_Contract_RC.algo" "$W/seal/algo/"
N="V50-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  FAMNATIVE=false FAMOBS=true CANCONTRACT=false FAMCONF="$FC" GRIDV2="$GRID" STOPV2="$STOP"  PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false  BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V50/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V50/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
