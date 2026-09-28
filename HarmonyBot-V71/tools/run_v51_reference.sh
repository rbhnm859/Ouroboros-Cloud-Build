#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"; W="$C/HarmonyBot-V71/reference-window-$WIN"; O="$C/HarmonyBot-V71/reference-output-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V71/reference/HarmonyBot_V51_Family_Native_Math_Geometry_Economic_Conversion_RC.algo" "$W/seal/algo/"
N="V51-REFERENCE-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=true ANCHORFORENSICS=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 ALGO="seal/algo/HarmonyBot_V51_Family_Native_Math_Geometry_Economic_Conversion_RC.algo" \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V51/tools/run_backtest.sh"
)
test -s "$W/seal/logs/$N.log"; test -s "$W/seal/reports/$N.json"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"; cp "$W/seal/reports/$N.json" "$O/raw-report.json"
python3 "$C/HarmonyBot-V71/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/V51_REFERENCE-$WIN.json" --window "$WIN" --variant "V51_REFERENCE" --years "$YEARS" --balance 10000
