#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"

case "$FAM" in
 V36_REPLAY)
   SETUP=false; CANSTD=false; PIVOT=false; TPROOF=false; RESCUE=false; DIVERSITY=false; ROUTEVETO=false
   ;;
 UNIQUE_SETUP_CORE)
   SETUP=true; CANSTD=false; PIVOT=false; TPROOF=false; RESCUE=false; DIVERSITY=true; ROUTEVETO=false
   ;;
 STABLE_ROUTE_CANONICAL)
   SETUP=true; CANSTD=true; PIVOT=false; TPROOF=true; RESCUE=false; DIVERSITY=true; ROUTEVETO=false
   ;;
 FULL_V45)
   SETUP=true; CANSTD=true; PIVOT=true; TPROOF=true; RESCUE=true; DIVERSITY=true; ROUTEVETO=false
   ;;
 *) echo "unknown V45 family $FAM"; exit 31;;
esac

C="$PWD/control"
W="$C/HarmonyBot-V45/window-$FAM-$WIN"
O="$C/HarmonyBot-V45/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V45/dist/HarmonyBot_V45_Restored_Edge_Independent_Setup_Expansion_RC.algo" "$W/seal/algo/"
N="V45-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  RETENTION=true AGING=true RECALL=true TTL=12 MAXCAND=12  SETUPID="$SETUP" CANSTD="$CANSTD" PIVOTGRAPH="$PIVOT" TPROOF="$TPROOF" M1RESCUE="$RESCUE" RESCUEBARS=3  DIVERSITY="$DIVERSITY" ROUTEVETO="$ROUTEVETO" BACKTEST_TIMEOUT_SECONDS=1800  "$C/HarmonyBot-V45/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V45/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
