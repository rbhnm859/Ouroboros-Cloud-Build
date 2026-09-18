#!/usr/bin/env bash
set -euo pipefail
BAL="${1:?balance required}"
case "$BAL" in 100|150|200|300|500|1000) ;; *) echo "unsupported balance: $BAL"; exit 2;; esac
C="$PWD/control"; S="$C/HarmonyBot-V351-Capital-Study"; W="$S/work-$BAL"; O="$S/output-$BAL"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$O/raw-logs"
STAGE="BOOT"
progress(){ printf '%s [V351-CAPITAL-PROGRESS] balance=%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BAL" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT
cd "$C"
progress "START frozen EXHAUSTION_VETO_ONLY capital compatibility"
python3 HarmonyBot-V35.1/tools/static_audit.py HarmonyBot-V35.1/src/HarmonyBotV351.cs
cp V351_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V35.1/HarmonyBotV351.csproj
dotnet build HarmonyBot-V35.1/HarmonyBotV351.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V351_CAPITAL_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V351_CAPITAL_BUILD.log"
ALGO=$(find HarmonyBot-V35.1/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V351_MonotonicAlpha_CapitalStudy.algo"
sha256sum HarmonyBot-V35.1/src/HarmonyBotV351.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"
cp "$S/PROTOCOL.md" "$O/CAPITAL_COMPATIBILITY_PROTOCOL.md"

run(){
  local suf=$1 st=$2 ev=$3 en=$4
  local n="V351-CAPITAL-${BAL}-${suf}"
  STAGE="$n"; progress "START stage=$n"
  (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE="$BAL" BACKTEST_TIMEOUT_SECONDS=2700 "$S/run_capital_backtest.sh")
  python3 "$S/audit_capital.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" \
    --out "$O/capital-${BAL}-${suf}.json" --window "$suf" --balance "$BAL" --years .5
  cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
  progress "DONE stage=$n"
}
run A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021
run B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021
run C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022
progress "COMPLETE balance=$BAL"
