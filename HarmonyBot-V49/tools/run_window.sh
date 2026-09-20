#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL) FN=false; FO=false; NATIVE=false; PQ=false; HO=false; DEC=false; RV=false;;
 NATIVE_CONFIRMATION_ONLY) FN=false; FO=true; NATIVE=true; PQ=false; HO=false; DEC=false; RV=false;;
 NATIVE_CONFIRMATION_QUEUE) FN=false; FO=true; NATIVE=true; PQ=true; HO=true; DEC=false; RV=true;;
 FULL_V49_COMMERCIAL) FN=false; FO=true; NATIVE=true; PQ=true; HO=true; DEC=true; RV=true;;
 *) echo "unknown V49 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V49/window-$FAM-$WIN"; O="$C/HarmonyBot-V49/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V49/dist/HarmonyBot_V49_Pattern_Native_Confirmation_Arbitration_RC.algo" "$W/seal/algo/"
N="V49-$FAM-$WIN-B10000"
(cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  FAMNATIVE="$FN" FAMOBS="$FO" PQUEUE="$PQ" HANDOFF="$HO" NATIVE="$NATIVE" NATIVEBARS=4 DECAY="$DEC" HARDLIFE=180 REVALIDATE="$RV"  BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V49/tools/run_backtest.sh")
python3 "$C/HarmonyBot-V49/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
