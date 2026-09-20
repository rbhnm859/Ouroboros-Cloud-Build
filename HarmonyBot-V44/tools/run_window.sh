#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V43_CONTROL)
   TR=false; PH=false; RS=false; GR=false;;
 THESIS_ROUTING)
   TR=true; PH=true; RS=true; GR=false;;
 PHYSICAL_GRID)
   TR=false; PH=false; RS=false; GR=true;;
 FULL_V44)
   TR=true; PH=true; RS=true; GR=true;;
 *) echo "unknown V44 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V44/window-$FAM-$WIN"; O="$C/HarmonyBot-V44/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V44/dist/HarmonyBot_V44_Thesis_Consistent_Route_Grid_Portfolio_RC.algo" "$W/seal/algo/"
N="V44-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
 RESCUE=true OCMODEL=true FOLLOW=true THESISEXIT=true CANONICAL=true MULTISCALE=true DEDUPE=true NATIVE=true LOGICALGRID=true \
 AUCTION=true AUCTION_MINUTES=5 HYPOTHESIS=true STRUCTCTX=true TEMPORAL=true CROSSALPHA=true DENSITY=true EVENTAUCTION=true OPPLOSS=true \
 ALPHAFLOOR=0.50 ABCDTRENDFLOOR=0.62 THESISROUTING="$TR" PERSISTENCE="$PH" RESUMPTION="$RS" GRIDATTR=true GRIDRECOVERY="$GR" \
 CONTMIN=0.60 COUNTERMIN=0.60 TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 \
 "$C/HarmonyBot-V44/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V44/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" \
 --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
