#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL) CAN=false; FC=false; GRID=false; STOP=false; JOINT=false; CORRIDOR=false;;
 V50_FULL_CONTROL) CAN=false; FC=true; GRID=true; STOP=true; JOINT=false; CORRIDOR=false;;
 FAMILY_NATIVE_MATH_GEOMETRY) CAN=true; FC=true; GRID=true; STOP=true; JOINT=true; CORRIDOR=false;;
 FULL_V51_COMMERCIAL) CAN=true; FC=true; GRID=true; STOP=true; JOINT=true; CORRIDOR=true;;
 *) echo "unknown V51 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V51/window-$FAM-$WIN"; O="$C/HarmonyBot-V51/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V51/dist/HarmonyBot_V51_Family_Native_Math_Geometry_Economic_Conversion_RC.algo" "$W/seal/algo/"
N="V51-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRID" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR="$CORRIDOR" ANCHORFORENSICS=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V51/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V51/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
