#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
CAN=true; FC=true; GRID=true; STOP=true; JOINT=true; CORRIDOR=false
RESEARCH=false; EXPANSION=false; GRIDV4=false
case "$FAM" in
 V51_CHAMPION_CONTROL) RESEARCH=false; EXPANSION=false; GRIDV4=false;;
 V55_CORE_PARITY) RESEARCH=true; EXPANSION=false; GRIDV4=false;;
 V55_CORE_PLUS_EXPANSION) RESEARCH=true; EXPANSION=true; GRIDV4=false;;
 V55_FULL_GRID_V4) RESEARCH=true; EXPANSION=true; GRIDV4=true;;
 *) echo "unknown V55 variant $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V55/window-$FAM-$WIN"; O="$C/HarmonyBot-V55/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V55/dist/HarmonyBot_V55_Champion_Core_Universal_Evidence_Admission_RC.algo" "$W/seal/algo/"
test -s "$W/seal/data.snapshot.sha" || { echo "[V55-DATA-SNAPSHOT-MISSING] $W/seal/data.snapshot.sha"; exit 41; }
DATA_SHA=$(tr -d '[:space:]' < "$W/seal/data.snapshot.sha")
N="V55-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRID" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR="$CORRIDOR" ANCHORFORENSICS=true \
 RESEARCH="$RESEARCH" EXPANSION="$EXPANSION" RBOUNDED=true RMICRO=2 RQUOTA=4 GRIDV4="$GRIDV4" EXPRR=2.5 \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V55/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V55/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000 --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
