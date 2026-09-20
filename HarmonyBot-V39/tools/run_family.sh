#!/usr/bin/env bash
set -euo pipefail
: "${1:?family}"; : "${2:?regimeSelector}"; : "${3:?routeSpecialization}"; : "${4:?stressQuarantine}"
FAM="$1"; REGIMESEL="$2"; ROUTESPEC="$3"; STRESSQ="$4"
C="$PWD/control"
W="$C/HarmonyBot-V39/work-$FAM"
O="$C/HarmonyBot-V39/output-$FAM"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$O/raw-logs"
cp "$C/HarmonyBot-V39/dist/HarmonyBot_V39_Regime_Conditioned_Harmonic_Portfolio_RC.algo" "$W/seal/algo/"
run(){
  local suf=$1 st=$2 ev=$3 en=$4 years=$5
  local n="V39-${FAM}-${suf}-B10000"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [V39-FAMILY] START $n"
  (
    cd "$W"
    RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE=10000 \
    RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
    REGIMESEL="$REGIMESEL" ROUTESPEC="$ROUTESPEC" STRESSQ="$STRESSQ" \
    TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V39/tools/run_backtest.sh"
  )
  python3 "$C/HarmonyBot-V39/tools/audit_report.py" \
    --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/$FAM-$suf.json" \
    --window "$suf" --family "$FAM" --years "$years" --balance 10000
  cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [V39-FAMILY] DONE $n"
}
run A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 .5
run B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 .5
run C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 .5
rm -f "$W/seal/ctrader.pwd" "$W/seal/accounts.json"
