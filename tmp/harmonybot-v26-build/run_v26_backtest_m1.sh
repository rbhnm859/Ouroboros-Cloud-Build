#!/usr/bin/env bash
set -euo pipefail
LABEL="$1"
START="$2"
END="$3"
DATA_MODE="${4:-m1}"
SPREAD="${5:-17.14}"
ACCOUNT="$(cat backtest/secure/account)"
OUT="HarmonyBotPro-v26-XAUUSD-M15-100-${LABEL}-FxPro-Live500-${DATA_MODE}"
docker run --rm \
  -v "$PWD/backtest:/work" \
  -e "CTID=$CTRADER_CTID" \
  -e 'PWD-FILE=/work/secure/pwd' \
  -e "ACCOUNT=$ACCOUNT" \
  ghcr.io/spotware/ctrader-console:5.9.11 \
  backtest /work/HarmonyBotPro_v26_Mobile.algo --environment-variables \
  --broker=FxPro --symbol=XAUUSD --period=m15 \
  --start="$START" --end="$END" \
  --balance=100 --data-mode="$DATA_MODE" --commission=35 --spread="$SPREAD" \
  --SymbolName=XAUUSD \
  --RiskPercent=1.5 --MaxDrawdown=10.0 --DailyLossLimitPercent=4.0 --WeeklyLossLimitPercent=8.0 \
  --MonthlyTargetPercent=12.0 --RiskAfterMonthlyTarget=0.5 --CloseAllOnDailyLock=false \
  --AutoReprotectOnStart=true --EmergencySlAtrMult=2.0 --EmergencyTpRR=2.0 \
  --MaxConsecutiveLosses=3 --ConsecutiveLossCooldownMin=60 --MarginBufferPercent=20.0 \
  --SmallAccountMode=true --SmallAccountThreshold=100.0 --SmallAccountMinSLPips=25.0 --SmallAccountMinTPPips=50.0 \
  --AllowMinVolumeFallback=true --MinVolumeRiskCapPercent=5.0 --MicroMinVolumeRiskCapPercent=10.0 \
  --MaxNotionalToEquityRatio=500.0 \
  --SessionStart=8 --SessionEnd=22 --MTFEnabled=true --H4FilterEnabled=false --PatternConfidence=0.72 \
  --MaxConcurrentTrades=3 --MaxSameDirectionTrades=1 --AntiHedge=true --MaxTradesPerDay=4 --CooldownMinutes=10 \
  --AtrPeriod=14 --SlAtrMult=1.2 --TpCdMult=1.0 --MinRR=2.0 --UseCostAdjustedRR=true \
  --MaxSpreadPips=35.0 --MinStopLossPips=100.0 --MinTakeProfitPips=200.0 --MinStopDistancePips=15.0 \
  --MinAtrPrice=3.0 --MaxSlippagePips=30.0 \
  --SwingDepth=5 --SwingLookback=200 --PivotScanCount=14 --MinLegAtrRatio=0.8 \
  --EnableGartley=true --EnableBat=true --EnableButterfly=true --EnableCrab=true --EnableCypher=true \
  --EnableRat=true --EnableDeepGartley=true --EnableAltBat=false --EnableDeepCrab=true \
  --EnableABCD=true --EnableShark=true --EnableFiveZero=false \
  --GlobalMinScore=0.55 --ConsensusBonus=1.12 --FibTolerance=0.05 --MaxEntryDeviationAtr=0.5 \
  --MaxTradesPerPatternPercent=50 --AutoDisableLosing=true --AutoDisableWinRate=50.0 \
  --SlUpdateStepPips=2.0 --SlUpdateCooldownSec=5 --BreakEvenTriggerPips=100.0 --BreakEvenOffsetPips=10.0 \
  --TrailingTriggerPips=150.0 --TrailingDistancePips=90.0 --EnablePartialTP=true --Tp1RR=1.0 --Tp1ClosePercent=60.0 \
  --BlockNewsWindow=true --BlockedWindowsGMT='12:25-12:45;14:25-14:45' \
  --EnableFibGrid=true --GridMaxLevels=5 \
  --GridLevelFibs='0.382,0.618,0.786,1.0,1.272,1.618,2.618,4.236' \
  --GridSizeFibs='1,1,2,3,5,8,13,21' \
  --GridProfitFib=0.618 --GridStopFib=2.618 --GridMaxTotalRiskPercent=10.0 --GridCooldownMinutes=15 \
  --GridMinStepPips=20.0 --GridOnlyWithTrend=true --GridUseGoldenMath=true --GridGoldenRiskConvergence=true \
  --GridGoldenTrailCompression=true --GridBreakevenTriggerR=0.25 --GridBreakevenLockPips=5.0 \
  --GridTrailTriggerR=0.5 --GridTrailDistanceFib=0.382 --GridScaleOutEnabled=true --GridScaleOutR=0.618 \
  --GridScaleOutPercent=38.2 --GridMaxAddsPerDay=6 --GridVolatilityAdapt=true --GridDrawdownScaleRisk=true \
  --report="/work/reports/${OUT}.html" --report-json="/work/reports/${OUT}.json" \
  | tee "backtest/reports/${OUT}.console.txt"
