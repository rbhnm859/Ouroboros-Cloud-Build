#!/usr/bin/env bash
set -euo pipefail
: "${CTRADER_PASSWORD:?}"; : "${CTRADER_CTID:?}"; : "${CTRADER_ACCOUNT:?}"
: "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${END_DATE:?}"; : "${EVAL_DATE:?}"; : "${BALANCE:?}"
ALGO="${ALGO:-seal/algo/HarmonyBot_V351_MonotonicAlpha_CapitalStudy.algo}"
IMAGE="${CTRADER_IMAGE:-ghcr.io/spotware/ctrader-console:5.9.11}"
BACKTEST_TIMEOUT_SECONDS="${BACKTEST_TIMEOUT_SECONDS:-2700}"
mkdir -p seal/{reports,logs,data}
printf '%s' "$CTRADER_PASSWORD" > seal/ctrader.pwd
chmod 600 seal/ctrader.pwd
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull "$IMAGE" >/dev/null

docker run --rm -v "$PWD/seal:/work" "$IMAGE" accounts \
  --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd > seal/accounts.json
ACCT=$(python3 - <<'PY'
import json,os
a=json.load(open('seal/accounts.json',encoding='utf-8-sig')); e=os.environ['CTRADER_ACCOUNT'].strip()
m=next((x for x in a if str(x.get('Number',''))==e or str(x.get('Id',''))==e),None)
if not m or m.get('Broker','').lower()!='fxpro' or m.get('Live') is not False or m.get('DepositCurrency')!='USD' or int(m.get('Leverage',0))!=500:
    raise SystemExit('FxPro demo USD 1:500 mismatch')
print(m['Number'])
PY
)

CNAME="v351-capital-$(echo "$RUN_NAME"|tr '[:upper:]_' '[:lower:]-')-$GITHUB_RUN_ID"
docker run --name "$CNAME" -v "$PWD/seal:/work" "$IMAGE" backtest "/work/${ALGO#seal/}" \
  --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd --account="$ACCT" \
  --symbol=XAUUSD --period=m1 --start="$START_DATE" --end="$END_DATE" --balance="$BALANCE" \
  --data-mode=m1 --data-dir=/work/data --commission=35 --spread=1 \
  --SymbolName=XAUUSD --TradingEnabled=true --BasketRiskPercent=1.0 --AdaptiveCapitalMode=true \
  --MinimumSupportedEquity=100 --MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3 \
  --MaxSpreadPips=60 --RoundTurnCommissionPips=0.5 --SlippageStressPips=0.3 --MinimumNetRR=2.0 --MinStopLossPips=10 \
  --MinFreeMarginRiskMultiple=5 --M15SwingDepth=3 --M15SwingLookback=320 --H1SwingDepth=3 --H4SwingDepth=2 \
  --PortfolioMaxCandidates=8 --CandidateTtlM15Bars=8 --MinGeometryQuality=0.55 --MinPrzConfluence=0.55 \
  --EnableHarmonicRobustnessGate=false --EnableRegimeContextGate=false --EnableEnhancedM1Confirmation=false \
  --EnableCapitalFeasibilityGate=true --EnableTransitionStateVeto=false --EnableExhaustionEvidenceVeto=true \
  --EnableRouteSpecificM1Veto=false --GridCancelMfeR=0.50 --NoMfeProofR=0.15 --NoMfeKillR=0.80 --NoMfeMinAgeMinutes=3 \
  --BreakEvenTriggerR=1.0 --BreakEvenLockR=0.10 --TrailTriggerR=1.50 --TrailDistanceR=0.75 \
  --EvaluationStartUtcIso="$EVAL_DATE" --report="/work/reports/$RUN_NAME.html" --report-json="/work/reports/$RUN_NAME.json" \
  --exit-on-stop > "seal/logs/$RUN_NAME.log" 2>&1 &
PID=$!; DONE=0
printf '[V351-CAPITAL-WATCHDOG] run=%s pid=%s timeoutSeconds=%s balance=%s\n' "$RUN_NAME" "$PID" "$BACKTEST_TIMEOUT_SECONDS" "$BALANCE"
for ((i=0;i<BACKTEST_TIMEOUT_SECONDS;i+=5)); do
  if (( i % 60 == 0 )); then echo "[V351-CAPITAL-WATCHDOG] run=$RUN_NAME elapsedSeconds=$i status=running"; fi
  if test -s "seal/reports/$RUN_NAME.json" && python3 - <<PY
import json
m=json.load(open("seal/reports/$RUN_NAME.json",encoding="utf-8-sig")).get("main",{})
raise SystemExit(0 if "endingEquity" in m and "netProfit" in m else 1)
PY
  then DONE=1; break; fi
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  sleep 5
done

docker stop --time 3 "$CNAME" >/dev/null 2>&1 || true
docker rm -f "$CNAME" >/dev/null 2>&1 || true
wait "$PID" 2>/dev/null || true
rm -f seal/ctrader.pwd seal/accounts.json

test "$DONE" = 1 || {
  echo "[V351-CAPITAL-WATCHDOG-FAIL] run=$RUN_NAME"
  tail -400 "seal/logs/$RUN_NAME.log" || true
  exit 20
}
echo "[V351-CAPITAL-WATCHDOG] run=$RUN_NAME status=complete"
