#!/usr/bin/env bash
set -euo pipefail
: "${CTRADER_PASSWORD:?}"; : "${CTRADER_CTID:?}"; : "${CTRADER_ACCOUNT:?}"
: "${CANDIDATE:?}"; : "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${END_DATE:?}"; : "${EVAL_DATE:?}"

ALGO="${ALGO:-seal/algo/HarmonyBotPro_commercial_convergence_rc.algo}"
CAPITAL="${CAPITAL:-10000}"
DATA_MODE="${DATA_MODE:-m1}"
SMALL="${SMALL:-false}"
SPREAD="${SPREAD:-1}"
COMMISSION="${COMMISSION:-35}"
SLIPPAGE="${SLIPPAGE:-30}"
THRESH_SCALE="${THRESH_SCALE:-1.0}"

case "$CANDIDATE" in
  A) MODE=1; KILL=0.85 ;;
  B) MODE=2; KILL=0.85 ;;
  C) MODE=3; KILL=0.70 ;;
  *) echo "unknown candidate $CANDIDATE"; exit 2 ;;
esac

ABS_HIGH=$(python3 - <<PY
print(1.30*float("$THRESH_SCALE"))
PY
)
REL_HIGH=$(python3 - <<PY
print(1.30*float("$THRESH_SCALE"))
PY
)

if [ "$SMALL" = "true" ]; then
  RISK=1.40
  SMALL_ARGS="--SmallAccountMode=true --SmallAccountMinSLPips=25 --V291SmallAccountTacticalExecution=true --V291TacticalBudgetUse=0.98 --V291RequireMicroConfirmation=true --V291MinTacticalRR=2.0 --V292FastSmallAccountExecution=true --V292MicroPivotBars=2 --V292MicroPivotAtrBuffer=0.04 --V292EnableCapitalCapStop=true --V292EnableEarlyTrigger=true --V292EarlyTriggerMinQuality=0.66 --V292EarlyTriggerMaxPrzAtr=0.95 --V292MicroBodyMinAtr=0.02 --V292WickBodyConfirmRatio=0.25"
else
  RISK=1.0
  SMALL_ARGS="--SmallAccountMode=false --V291SmallAccountTacticalExecution=false --V292FastSmallAccountExecution=false --V292EnableCapitalCapStop=false --V292EnableEarlyTrigger=false"
fi

mkdir -p seal/{reports,logs,data,audit}
docker pull ghcr.io/spotware/ctrader-console:5.9.11 >/dev/null
printf '%s' "$CTRADER_PASSWORD" > seal/ctrader.pwd
chmod 600 seal/ctrader.pwd
docker run --rm -v "$PWD/seal:/work" ghcr.io/spotware/ctrader-console:5.9.11 accounts --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd > seal/accounts.json
ACCT=$(python3 - <<'PY'
import json,os
a=json.load(open('seal/accounts.json',encoding='utf-8-sig')); e=os.environ['CTRADER_ACCOUNT'].strip()
m=next((x for x in a if str(x.get('Number',''))==e or str(x.get('Id',''))==e),None)
if not m or m.get('Broker','').lower()!='fxpro' or m.get('Live') is not False or m.get('DepositCurrency')!='USD' or int(m.get('Leverage',0))!=500:
    raise SystemExit('FxPro demo USD 1:500 account mismatch')
print(m['Number'])
PY
)

CNAME="cc-$(echo "$RUN_NAME" | tr '[:upper:]_' '[:lower:]-')-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
docker run --name "$CNAME" -v "$PWD/seal:/work" ghcr.io/spotware/ctrader-console:5.9.11 backtest "/work/${ALGO#seal/}"   --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd --account="$ACCT"   --symbol=XAUUSD --period=m1 --start="$START_DATE" --end="$END_DATE" --balance="$CAPITAL" --data-mode="$DATA_MODE" --data-dir=/work/data   --commission="$COMMISSION" --spread="$SPREAD" --SymbolName=XAUUSD --RiskPercent="$RISK" --MaxSlippagePips="$SLIPPAGE" --MaxDrawdown=10 --MinStopLossPips=100   $SMALL_ARGS   --SessionStart=8 --SessionEnd=22 --DstAwareInstitutionalSession=false --MinAtrPrice=0.5   --V294AllowBuy=false --V294AllowSell=true --EnableFibGrid=true --EnableAltBat=true --EnableFiveZero=true --MinRR=2   --GridProfitFib=1.618 --GridStopFib=1.618 --GridCooldownMinutes=240 --MinPrzConfluence=0.55 --MinGeometryQuality=0.52   --GridBreakevenTriggerR=0.15 --GridTrailTriggerR=0.35 --GridScaleOutR=0.50   --V295ThesisGuard=true --V295NoMfeKillR="$KILL" --V295MinFavorableProofR=0.15 --V295MinInvalidationAgeMinutes=2   --CommercialConvergenceMode="$MODE" --CommercialAbsHighAtr="$ABS_HIGH" --CommercialAtrBaselineBars=240 --CommercialHighAtrRatio="$REL_HIGH"   --EnableCapitalAwarePrecisionEntry=true --PrecisionPrzMaxDistanceAtr=0.45 --PrecisionMaxWaitAtr=1.25 --CapitalSafetyHeadroom=0.98 --CapGridStopToRiskBudget=true   --EvaluationStartUtcIso="$EVAL_DATE" --V29PersistentPrzQueue=true --V29PendingMaxBars=90 --V29PendingGlobalMax=12 --V29PendingPerPatternMax=3   --V29PendingMinCompositeQuality=0.58 --V29PendingTriggerMaxPrzAtr=0.85 --V29HighQualityPrzBonusAtr=0.35 --V29CandidateReplacementMargin=0.03   --V29WarmupSeedPending=true --V29MaxOrderAttemptsPerCandidate=3   --report="/work/reports/$RUN_NAME.html" --report-json="/work/reports/$RUN_NAME.json" > "seal/logs/$RUN_NAME.log" 2>&1 &
PID=$!
DONE=0
for ((i=0;i<14400;i+=5)); do
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
if [ "$DONE" != 1 ]; then
  echo "BACKTEST_FAILED $RUN_NAME"
  exit 20
fi
