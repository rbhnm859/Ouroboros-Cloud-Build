#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"

# V43 ablations are preregistered. No threshold sweep.
case "$FAM" in
 V42_CONTROL)
   HYP=false; STRUCT=false; TEMP=false; CROSS=false; DENS=false; EVA=false; OPP=true
   ;;
 CONDITIONAL_ALPHA)
   HYP=true; STRUCT=true; TEMP=true; CROSS=false; DENS=false; EVA=false; OPP=true
   ;;
 ALPHA_AUCTION)
   HYP=true; STRUCT=true; TEMP=true; CROSS=true; DENS=true; EVA=false; OPP=true
   ;;
 FULL_V43)
   HYP=true; STRUCT=true; TEMP=true; CROSS=true; DENS=true; EVA=true; OPP=true
   ;;
 *) echo "unknown V43 family $FAM"; exit 31;;
esac

C="$PWD/control"
W="$C/HarmonyBot-V43/window-$FAM-$WIN"
O="$C/HarmonyBot-V43/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V43/dist/HarmonyBot_V43_Cross_Regime_Positive_Alpha_Portfolio_RC.algo" "$W/seal/algo/"
N="V43-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
 RESCUE=true OCMODEL=true FOLLOW=true THESISEXIT=true \
 CANONICAL=true MULTISCALE=true DEDUPE=true NATIVE=true LOGICALGRID=true AUCTION=true AUCTION_MINUTES=5 \
 HYPOTHESIS="$HYP" STRUCTCTX="$STRUCT" TEMPORAL="$TEMP" CROSSALPHA="$CROSS" DENSITY="$DENS" EVENTAUCTION="$EVA" OPPLOSS="$OPP" \
 ALPHAFLOOR=0.50 ABCDTRENDFLOOR=0.62 TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 \
 "$C/HarmonyBot-V43/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V43/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" \
 --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
