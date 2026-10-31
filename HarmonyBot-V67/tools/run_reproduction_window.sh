#!/usr/bin/env bash
set -euo pipefail
: "${1:?track}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
TRACK="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
C="$PWD/control"; W="$C/HarmonyBot-V67/repro-$TRACK-$WIN"; O="$C/HarmonyBot-V67/repro-out-$TRACK-$WIN"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
case "$TRACK" in
 V52_BASE)
   cp "$C/HarmonyBot-V67/dist/HarmonyBot_V52_Family_Identity_Detection_Graph_Reconstruction_RC.algo" "$W/seal/algo/"
   RUNNER="$C/HarmonyBot-V52/tools/run_backtest.sh"
   EXTRA=()
   ;;
 V67_A)
   cp "$C/HarmonyBot-V67/dist/HarmonyBot_V67_Family_Native_Throughput_Grid_Commercial_Rebase.algo" "$W/seal/algo/"
   RUNNER="$C/HarmonyBot-V67/tools/run_backtest.sh"
   EXTRA=(V67CONTRACTS=false V67FRONTIER=false V67FGRID=false V67EVIDENCE=false V67EXPAND=false MAXDD=10 REPORT_FLUSH_GRACE_SECONDS=8)
   ;;
 *) echo "unknown reproduction track $TRACK"; exit 31;;
esac
chmod +x "$C/HarmonyBot-V52/tools/run_backtest.sh" "$C/HarmonyBot-V67/tools/run_backtest.sh"
N="V67-REPRO-$TRACK-$WIN-B10000"
(
 cd "$W"
 env RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 BACKTEST_TIMEOUT_SECONDS=1800 "${EXTRA[@]}" "$RUNNER"
)
python3 "$C/HarmonyBot-V67/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$TRACK-$WIN.json" --window "$WIN" --family "$TRACK" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"
