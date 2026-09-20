#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL) RET=false; EXT=false;;
 RETRACEMENT_ACTIVATION) RET=true; EXT=false;;
 EXTENSION_ACTIVATION) RET=false; EXT=true;;
 FULL_V48_FAMILY_PORTFOLIO) RET=true; EXT=true;;
 *) echo "unknown V48 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V48/window-$FAM-$WIN"; O="$C/HarmonyBot-V48/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V48/dist/HarmonyBot_V48_Harmonic_Family_Specialization_Dormant_Alpha_RC.algo" "$W/seal/algo/"
N="V48-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false RETRACT="$RET" EXTEND="$EXT"  BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V48/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V48/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
