#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V46_SCALE_CONTROL) CF=false; NL=false; EX=false;;
 COUNTERFACTUAL_NATIVE_CONFIRM) CF=true; NL=false; EX=false;;
 PROVEN_PLUS_NATIVE_LANES) CF=true; NL=true; EX=false;;
 FULL_V49_COMMERCIAL) CF=true; NL=true; EX=true;;
 *) echo "unknown V49 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V49/window-$FAM-$WIN"; O="$C/HarmonyBot-V49/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V49/dist/HarmonyBot_V49_Harmonic_Family_Confirmation_Kernel_RC.algo" "$W/seal/algo/"
N="V49-$FAM-$WIN-B10000"
(cd "$W"; RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 CFAUDIT="$CF" NATIVELANES="$NL" EXTNATIVE="$EX" EVIDENCEBARS=12 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V49/tools/run_backtest.sh")
python3 "$C/HarmonyBot-V49/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" \
 --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
