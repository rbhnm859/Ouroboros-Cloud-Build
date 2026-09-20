#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
CAN=true; FC=true; GRIDV2=true; STOP=true; JOINT=true; IDENT=true; BOUNDED=true; PRJ=false
FQ=false; FR=false; FC2=false; CTX=false; GEXEC=true
case "$FAM" in
 V51_QUALITY_CORE_REPLAY) FQ=false; FR=false; FC2=false; CTX=false; GEXEC=true; LIBERATE=false; COREKEEP=false; GRIDV3=false; STATEGRID=false; IDENT=false; BOUNDED=false;;
 V52_LIBERATION_CONTROL) FQ=false; FR=false; FC2=false; CTX=false; GEXEC=true; LIBERATE=false; COREKEEP=false; GRIDV3=false; STATEGRID=false; IDENT=true; BOUNDED=true;;
 V54_LIBERATION_LEGACY_GRID) FQ=true; FR=true; FC2=true; CTX=true; GEXEC=true; LIBERATE=true; COREKEEP=true; GRIDV3=false; STATEGRID=false;;
 V54_LIBERATION_GRID_V3) FQ=true; FR=true; FC2=true; CTX=true; GEXEC=true; LIBERATE=true; COREKEEP=true; GRIDV3=true; STATEGRID=true;;
 *) echo "unknown V54 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V54/window-$FAM-$WIN"; O="$C/HarmonyBot-V54/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V54/dist/HarmonyBot_V54_Universal_Harmonic_Liberation_Grid_Alpha_Core_RC.algo" "$W/seal/algo/"
N="V54-$FAM-$WIN-B10000"
test -s "$W/seal/data.snapshot.sha" || { echo "[V54-DATA-SNAPSHOT-MISSING] $W/seal/data.snapshot.sha"; exit 41; }
DATA_SHA=$(tr -d '[:space:]' < "$W/seal/data.snapshot.sha")
( cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRIDV2" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR=false ANCHORFORENSICS=true IDENT="$IDENT" BOUNDED="$BOUNDED" SKIPS=2 FQUOTA=4 PRJPRZ="$PRJ" DTRUTH=true FAMQUAL="$FQ" FAMROUTE="$FR" FAMCONFV2="$FC2" CTXBUS="$CTX" GRIDEXEC="$GEXEC" LIBERATE="$LIBERATE" COREKEEP="$COREKEEP" GRIDV3="$GRIDV3" STATEGRID="$STATEGRID" PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V54/tools/run_backtest.sh" )
python3 "$C/HarmonyBot-V54/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000 --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
