#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
case "$VAR" in
 A_V52_EXACT_CONTROL)
   FAMNATIVE=false; CONTRACTS=false; FRONTIER=false; FGRID=false; EVIDENCE=false; EXPAND=false
   PQUEUE=false; HANDOFF=false; NATIVE=false; DECAY=false; REVALIDATE=false; MAXDD=10;;
 B_FAMILY_EVIDENCE_OVERLAY)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=false; FGRID=false; EVIDENCE=true; EXPAND=false
   PQUEUE=false; HANDOFF=false; NATIVE=false; DECAY=false; REVALIDATE=false; MAXDD=6;;
 C_OVERLAY_FAMILY_GRID)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=false; FGRID=true; EVIDENCE=true; EXPAND=false
   PQUEUE=false; HANDOFF=false; NATIVE=false; DECAY=false; REVALIDATE=false; MAXDD=6;;
 D_OVERLAY_GRID_SCHEDULER)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=false; FGRID=true; EVIDENCE=true; EXPAND=false
   PQUEUE=true; HANDOFF=true; NATIVE=false; DECAY=true; REVALIDATE=true; MAXDD=6;;
 *) echo "unknown V68 variant $VAR"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V68/window-$VAR-$WIN"; O="$C/HarmonyBot-V68/output-$VAR-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V68/dist/HarmonyBot_V68_Family_Evidence_Overlay_Grid_Throughput_Recovery.algo" "$W/seal/algo/"
N="V68-$VAR-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE="$FAMNATIVE" FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
 PQUEUE="$PQUEUE" HANDOFF="$HANDOFF" NATIVE="$NATIVE" NATIVEBARS=4 DECAY="$DECAY" HARDLIFE=180 REVALIDATE="$REVALIDATE" \
 V68CONTRACTS="$CONTRACTS" V68FRONTIER="$FRONTIER" V68FGRID="$FGRID" V68EVIDENCE="$EVIDENCE" V68EXPAND="$EXPAND" MAXDD="$MAXDD" \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V68/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V68/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$VAR-$WIN.json" --window "$WIN" --family "$VAR" --years "$YEARS" --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"
