#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
: "${6:?rescue}"; : "${7:?opportunityCost}"; : "${8:?followThrough}"; : "${9:?thesisExit}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; RESCUE="$6"; OCMODEL="$7"; FOLLOW="$8"; THESISEXIT="$9"
C="$PWD/control"
W="$C/HarmonyBot-V41/window-$FAM-$WIN"
O="$C/HarmonyBot-V41/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V41/dist/HarmonyBot_V41_Marginal_Alpha_Pattern_Portfolio_RC.algo" "$W/seal/algo/"
N="V41-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
 RESCUE="$RESCUE" OCMODEL="$OCMODEL" FOLLOW="$FOLLOW" THESISEXIT="$THESISEXIT" \
 TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V41/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V41/tools/audit_report.py" \
 --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" \
 --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
