#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"
case "$FAM" in
 V41_REPLAY) CANONICAL=false; MULTISCALE=false; DEDUPE=false; NATIVE=false; LOGICALGRID=false; AUCTION=false; RESCUE=false; OCMODEL=false; FOLLOW=false; THESISEXIT=false;;
 CANONICAL_GEOMETRY) CANONICAL=true; MULTISCALE=true; DEDUPE=true; NATIVE=false; LOGICALGRID=true; AUCTION=false; RESCUE=false; OCMODEL=false; FOLLOW=false; THESISEXIT=false;;
 PATTERN_NATIVE) CANONICAL=true; MULTISCALE=true; DEDUPE=true; NATIVE=true; LOGICALGRID=true; AUCTION=false; RESCUE=false; OCMODEL=false; FOLLOW=true; THESISEXIT=true;;
 FULL_V42) CANONICAL=true; MULTISCALE=true; DEDUPE=true; NATIVE=true; LOGICALGRID=true; AUCTION=true; RESCUE=true; OCMODEL=true; FOLLOW=true; THESISEXIT=true;;
 *) echo "unknown V42 family $FAM"; exit 31;;
esac
C="$PWD/control"; W="$C/HarmonyBot-V42/window-$FAM-$WIN"; O="$C/HarmonyBot-V42/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V42/dist/HarmonyBot_V42_Canonical_Harmonic_Opportunity_Engine_RC.algo" "$W/seal/algo/"
N="V42-$FAM-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
 RESCUE="$RESCUE" OCMODEL="$OCMODEL" FOLLOW="$FOLLOW" THESISEXIT="$THESISEXIT" \
 CANONICAL="$CANONICAL" MULTISCALE="$MULTISCALE" DEDUPE="$DEDUPE" NATIVE="$NATIVE" LOGICALGRID="$LOGICALGRID" AUCTION="$AUCTION" AUCTION_MINUTES=5 \
 TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V42/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V42/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" \
 --window "$WIN" --family "$FAM" --years .5 --balance 10000
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
