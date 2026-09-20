#!/usr/bin/env bash
set -euo pipefail
: "${1:?stage}"; : "${2:?variant}"; : "${3:?window}"; : "${4:?start}"; : "${5:?eval}"; : "${6:?end}"
STAGE="$1"; VAR="$2"; WIN="$3"; START="$4"; EVAL="$5"; END="$6"

CAN=true; FC=true; GRIDV2=true; STOP=true; JOINT=true
IDENT=true; BOUNDED=true; PRJ=false
FQ=false; FR=false; FC2=false; CTX=false; GEXEC=true
V54LIB=false; V54CORE=false; V54ECON=false; V54FGRID=false; V54SAGRID=false

case "$VAR" in
  V51_QUALITY_CORE_REPLAY)
    IDENT=false; BOUNDED=false; FC2=false; CTX=false; GEXEC=true;;
  V52_LIBERATION_CONTROL)
    IDENT=true; BOUNDED=true; FC2=false; CTX=false; GEXEC=true;;
  V54_CORE_PLUS_LIBERATION)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=true; V54LIB=true; V54CORE=true; V54ECON=false;;
  V54_FULL_ALPHA)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=true; V54LIB=true; V54CORE=true; V54ECON=true;;
  L0_ONLY)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=false; V54LIB=true; V54CORE=true; V54ECON=true;;
  LEGACY_GRID)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=true; V54LIB=true; V54CORE=true; V54ECON=true;;
  FAMILY_NATIVE_GRID)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=true; V54LIB=true; V54CORE=true; V54ECON=true; V54FGRID=true;;
  FAMILY_NATIVE_GRID_STATE_AWARE)
    IDENT=true; BOUNDED=true; FC2=true; CTX=true; GEXEC=true; V54LIB=true; V54CORE=true; V54ECON=true; V54FGRID=true; V54SAGRID=true;;
  *) echo "unknown V54 variant $VAR"; exit 31;;
esac

C="$PWD/control"
W="$C/HarmonyBot-V54/window-$STAGE-$VAR-$WIN"
O="$C/HarmonyBot-V54/output-$STAGE-$VAR-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal" "$O/raw-logs"
cp "$C/HarmonyBot-V54/dist/HarmonyBot_V54_Universal_Harmonic_Grid_Alpha_Core_RC.algo" "$W/seal/algo/"
test -s "$W/seal/data.snapshot.sha" || { echo "[V54-DATA-SNAPSHOT-MISSING] $W/seal/data.snapshot.sha"; exit 41; }
DATA_SHA=$(tr -d '[:space:]' < "$W/seal/data.snapshot.sha")
N="V54-$STAGE-$VAR-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRIDV2" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR=false ANCHORFORENSICS=true \
 IDENT="$IDENT" BOUNDED="$BOUNDED" SKIPS=2 FQUOTA=4 PRJPRZ="$PRJ" DTRUTH=true \
 FAMQUAL="$FQ" FAMROUTE="$FR" FAMCONFV2="$FC2" CTXBUS="$CTX" GRIDEXEC="$GEXEC" \
 V54LIB="$V54LIB" V54CORE="$V54CORE" V54ECON="$V54ECON" V54FGRID="$V54FGRID" V54SAGRID="$V54SAGRID" \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V54/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V54/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$STAGE-$VAR-$WIN.json" --window "$WIN" --family "$VAR" --years .5 --balance 10000 --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
