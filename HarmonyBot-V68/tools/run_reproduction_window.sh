#!/usr/bin/env bash
set -euo pipefail
: "${1:?track}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
TRACK="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
C="$PWD/control"; W="$C/HarmonyBot-V68/repro-$TRACK-$WIN"; O="$C/HarmonyBot-V68/repro-out-$TRACK-$WIN"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
case "$TRACK" in
 V52_BASE)
   cp "$C/HarmonyBot-V68/dist/HarmonyBot_V52_Family_Identity_Detection_Graph_Reconstruction_RC.algo" "$W/seal/algo/"
   RUNNER="$C/HarmonyBot-V52/tools/run_backtest.sh"
   EXTRA=()
   ;;
 V68_A)
   cp "$C/HarmonyBot-V68/dist/HarmonyBot_V68_Harmonic_Family_Grid_Atlas_Positive_Throughput_Rebase.algo" "$W/seal/algo/"
   RUNNER="$C/HarmonyBot-V68/tools/run_backtest.sh"
   EXTRA=(V68CONTRACTS=false V68FRONTIER=false V68FGRID=false V68EVIDENCE=false V68EXPAND=false V68ATLAS=false V68POSITIVE=false V68SCHED=false MAXDD=10 REPORT_FLUSH_GRACE_SECONDS=8)
   ;;
 *) echo "unknown reproduction track $TRACK"; exit 31;;
esac
chmod +x "$C/HarmonyBot-V52/tools/run_backtest.sh" "$C/HarmonyBot-V68/tools/run_backtest.sh"
N="V68-REPRO-$TRACK-$WIN-B10000"
(
 cd "$W"
 env RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 BACKTEST_TIMEOUT_SECONDS=1800 "${EXTRA[@]}" "$RUNNER"
)
python3 "$C/HarmonyBot-V68/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$TRACK-$WIN.json" --window "$WIN" --family "$TRACK" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"
