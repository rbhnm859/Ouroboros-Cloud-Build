#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
case "$VAR" in
 B_FAMILY_NATIVE_ATLAS) EXPAND=false; SCHED=false; SURVIVAL=false; PQUEUE=false; HANDOFF=false; DECAY=false; REVALIDATE=false;;
 C_FAMILY_SURVIVAL) EXPAND=false; SCHED=false; SURVIVAL=true; PQUEUE=false; HANDOFF=false; DECAY=false; REVALIDATE=false;;
 D_COMMERCIAL_FEDERATION) EXPAND=true; SCHED=true; SURVIVAL=true; PQUEUE=true; HANDOFF=true; DECAY=true; REVALIDATE=true;;
 *) echo "unknown V69 variant $VAR"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V69/window-$VAR-$WIN"; O="$C/HarmonyBot-V69/output-$VAR-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V69/dist/HarmonyBot_V69_Family_Alpha_Federation_Commercial_Breakthrough.algo" "$W/seal/algo/"
RUNNER="$C/HarmonyBot-V69/tools/run_backtest.sh"; chmod +x "$RUNNER"; N="V69-$VAR-$WIN-B10000"
(
 cd "$W"
 env RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=true FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true PQUEUE="$PQUEUE" HANDOFF="$HANDOFF" NATIVE=false NATIVEBARS=4 \
 DECAY="$DECAY" HARDLIFE=180 REVALIDATE="$REVALIDATE" V69CONTRACTS=true V69FRONTIER=true V69FGRID=false V69EVIDENCE=true \
 V69EXPAND="$EXPAND" V69ATLAS=true V69POSITIVE=true V69SCHED="$SCHED" V69SURVIVAL="$SURVIVAL" MAXDD=6 BACKTEST_TIMEOUT_SECONDS=1800 "$RUNNER"
)
python3 "$C/HarmonyBot-V69/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$VAR-$WIN.json" --window "$WIN" --family "$VAR" --years "$YEARS" --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
