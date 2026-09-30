#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL)
   PQ=false; HO=false; NA=false; DE=false; RV=false
   ;;
 QUEUE_RECOVERY)
   PQ=true; HO=true; NA=false; DE=false; RV=true
   ;;
 NATIVE_M1_EXPANSION)
   PQ=false; HO=false; NA=true; DE=false; RV=false
   ;;
 FULL_V47_COMMERCIAL)
   PQ=true; HO=true; NA=true; DE=true; RV=true
   ;;
 *) echo "unknown V47 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V47/window-$FAM-$WIN"; O="$C/HarmonyBot-V47/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V47/dist/HarmonyBot_V47_Alpha_Preserving_Throughput_Serial_Opportunity_RC.algo" "$W/seal/algo/"
N="V47-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  PQUEUE="$PQ" HANDOFF="$HO" NATIVE="$NA" NATIVEBARS=4 DECAY="$DE" HARDLIFE=180 REVALIDATE="$RV"  BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V47/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V47/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
