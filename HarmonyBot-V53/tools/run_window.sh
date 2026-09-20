#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
CAN=true; FC=true; GRIDV2=true; STOP=true; JOINT=true; IDENT=true; BOUNDED=true; PRJ=false
FQ=false; FR=false; FC2=false; CTX=false; GEXEC=true
case "$FAM" in
 V52_CONTROL_NOGRID) GEXEC=false;;
 V52_CONTROL_GRID) GEXEC=true;;
 V53_CONVERSION_NOGRID) FQ=true; FR=true; FC2=true; CTX=true; GEXEC=false;;
 V53_CONVERSION_GRID) FQ=true; FR=true; FC2=true; CTX=true; GEXEC=true;;
 *) echo "unknown V53 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V53/window-$FAM-$WIN"; O="$C/HarmonyBot-V53/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V53/dist/HarmonyBot_V53_Family_Native_Conversion_Grid_Causal_RC.algo" "$W/seal/algo/"
N="V53-$FAM-$WIN-B10000"
( cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRIDV2" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR=false ANCHORFORENSICS=true IDENT="$IDENT" BOUNDED="$BOUNDED" SKIPS=2 FQUOTA=4 PRJPRZ="$PRJ" DTRUTH=true FAMQUAL="$FQ" FAMROUTE="$FR" FAMCONFV2="$FC2" CTXBUS="$CTX" GRIDEXEC="$GEXEC" PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V53/tools/run_backtest.sh" )
python3 "$C/HarmonyBot-V53/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
