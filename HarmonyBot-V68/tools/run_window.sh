#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
case "$VAR" in
 A_V52_EXACT_CONTROL)
   FAMNATIVE=false; CONTRACTS=false; FRONTIER=false; FGRID=false; EVIDENCE=false; EXPAND=false; ATLAS=false; POSITIVE=false; SCHED=false
   PQUEUE=false; HANDOFF=false; DECAY=false; REVALIDATE=false; MAXDD=10; CONTROL=V52;;
 B_FAMILY_GRID_ATLAS)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=true; FGRID=false; EVIDENCE=true; EXPAND=false; ATLAS=true; POSITIVE=false; SCHED=false
   PQUEUE=false; HANDOFF=false; DECAY=false; REVALIDATE=false; MAXDD=6; CONTROL=V68;;
 C_POSITIVE_THROUGHPUT)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=true; FGRID=false; EVIDENCE=true; EXPAND=false; ATLAS=true; POSITIVE=true; SCHED=false
   PQUEUE=false; HANDOFF=false; DECAY=false; REVALIDATE=false; MAXDD=6; CONTROL=V68;;
 D_FAMILY_PORTFOLIO_MAX)
   FAMNATIVE=true; CONTRACTS=true; FRONTIER=true; FGRID=false; EVIDENCE=true; EXPAND=true; ATLAS=true; POSITIVE=true; SCHED=true
   PQUEUE=true; HANDOFF=true; DECAY=true; REVALIDATE=true; MAXDD=6; CONTROL=V68;;
 *) echo "unknown V68 variant $VAR"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V68/window-$VAR-$WIN"; O="$C/HarmonyBot-V68/output-$VAR-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
if [ "$CONTROL" = "V52" ]; then
  cp "$C/HarmonyBot-V68/dist/HarmonyBot_V52_Family_Identity_Detection_Graph_Reconstruction_RC.algo" "$W/seal/algo/"
  RUNNER="$C/HarmonyBot-V52/tools/run_backtest.sh"
else
  cp "$C/HarmonyBot-V68/dist/HarmonyBot_V68_Harmonic_Family_Grid_Atlas_Positive_Throughput_Rebase.algo" "$W/seal/algo/"
  RUNNER="$C/HarmonyBot-V68/tools/run_backtest.sh"
fi
chmod +x "$RUNNER"
N="V68-$VAR-$WIN-B10000"
(
 cd "$W"
 if [ "$CONTROL" = "V52" ]; then
   env RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
   FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
   IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
   PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
   BACKTEST_TIMEOUT_SECONDS=1800 "$RUNNER"
 else
   env RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
   FAMNATIVE="$FAMNATIVE" FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
   IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
   PQUEUE="$PQUEUE" HANDOFF="$HANDOFF" NATIVE=false NATIVEBARS=4 DECAY="$DECAY" HARDLIFE=180 REVALIDATE="$REVALIDATE" \
   V68CONTRACTS="$CONTRACTS" V68FRONTIER="$FRONTIER" V68FGRID="$FGRID" V68EVIDENCE="$EVIDENCE" V68EXPAND="$EXPAND" \
   V68ATLAS="$ATLAS" V68POSITIVE="$POSITIVE" V68SCHED="$SCHED" MAXDD="$MAXDD" \
   BACKTEST_TIMEOUT_SECONDS=1800 "$RUNNER"
 fi
)
python3 "$C/HarmonyBot-V68/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$VAR-$WIN.json" --window "$WIN" --family "$VAR" --years "$YEARS" --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
