#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V36_REPLAY)
   SETUP=false; CAN=false; PIV=false; TP=false; R=false; DIV=false; SR=false; TR=false; AG=false; RV=false
   ;;
 STABLE_CORE)
   SETUP=true; CAN=true; PIV=false; TP=true; R=false; DIV=true; SR=false; TR=false; AG=false; RV=false
   ;;
 SCALE_CONVERSION)
   SETUP=true; CAN=true; PIV=true; TP=true; R=false; DIV=true; SR=true; TR=false; AG=false; RV=false
   ;;
 FULL_V46)
   SETUP=true; CAN=true; PIV=true; TP=true; R=true; DIV=true; SR=true; TR=true; AG=true; RV=true
   ;;
 *) echo "unknown V46 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V46/window-$FAM-$WIN"; O="$C/HarmonyBot-V46/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V46/dist/HarmonyBot_V46_Restored_Alpha_Execution_Conversion_RC.algo" "$W/seal/algo/"
N="V46-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  RETENTION=true AGING=true RECALL=true TTL=12 MAXCAND=12 SETUPID="$SETUP" CANSTD="$CAN" PIVOTGRAPH="$PIV" TPROOF="$TP"  M1RESCUE="$R" RESCUEBARS=3 DIVERSITY="$DIV" SCALEROUTE="$SR" TEMPRESCUE="$TR" ARMEDGRACE="$AG" GRACEMIN=90  REVALIDATE="$RV" ROUTEVETO=false BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V46/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V46/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
