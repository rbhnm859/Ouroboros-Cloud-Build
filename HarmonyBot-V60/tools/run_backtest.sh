#!/usr/bin/env bash
set -euo pipefail
: "${CTRADER_PASSWORD:?}"; : "${CTRADER_CTID:?}"; : "${CTRADER_ACCOUNT:?}"
: "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${END_DATE:?}"; : "${EVAL_DATE:?}"
BALANCE="${BALANCE:-10000}"
TRADING="${TRADING:-true}"; FAMILYBOOKS="${FAMILYBOOKS:-true}"; SHADOW="${SHADOW:-true}"; CALADMIT="${CALADMIT:-false}"; FAMREP="${FAMREP:-true}"; RESEARCHCONT="${RESEARCHCONT:-true}"; MANIFOLD="${MANIFOLD:-true}"; PUREPRZ="${PUREPRZ:-true}"; DAG="${DAG:-true}"; CAPRESEARCH="${CAPRESEARCH:-true}"; CAPLIVE="${CAPLIVE:-false}"; MATCHED="${MATCHED:-true}"; PROJERR="${PROJERR:-0.55}"; MSIG="${MSIG:-1.0}"
ABCDLIVE="${ABCDLIVE:-false}"; V60GRID="${V60GRID:-true}"; V60VARIANT="${V60VARIANT:-CORE_L0_BASELINE}"; V60ADAPTIVE="${V60ADAPTIVE:-false}"; V60CONVEX="${V60CONVEX:-true}"; V60RUNNER="${V60RUNNER:-true}"; V60RUNNERFRAC="${V60RUNNERFRAC:-0.25}"; V60CLUSTER="${V60CLUSTER:-true}"; V60SURFACE="${V60SURFACE:-true}"; V60SCHED="${V60SCHED:-true}"; CALMIN="${CALMIN:-0.0}"; CALMAN="${CALMAN:-}"
[ -n "$CALMAN" ] || CALMAN="NONE"
PQUEUE="${PQUEUE:-false}"; HANDOFF="${HANDOFF:-false}"; NATIVE="${NATIVE:-false}"
NATIVEBARS="${NATIVEBARS:-4}"; DECAY="${DECAY:-false}"; HARDLIFE="${HARDLIFE:-180}"; FAMNATIVE="${FAMNATIVE:-false}"; FAMOBS="${FAMOBS:-true}"; CANCONTRACT="${CANCONTRACT:-false}"; FAMCONF="${FAMCONF:-false}"; GRIDV2="${GRIDV2:-false}"; STOPV2="${STOPV2:-false}"
REVALIDATE="${REVALIDATE:-false}"; JOINT="${JOINT:-false}"; CORRIDOR="${CORRIDOR:-false}"; ANCHORFORENSICS="${ANCHORFORENSICS:-true}"
IDENT="${IDENT:-false}"; BOUNDED="${BOUNDED:-false}"; SKIPS="${SKIPS:-2}"; FQUOTA="${FQUOTA:-4}"; PRJPRZ="${PRJPRZ:-false}"; DTRUTH="${DTRUTH:-true}"
ALGO="${ALGO:-seal/algo/HarmonyBot_V60_Harmonic_Alpha_Conversion_Fibonacci_Grid_Convex_Capture_RC.algo}"
IMAGE="${CTRADER_IMAGE:-ghcr.io/spotware/ctrader-console:5.9.11}"
BACKTEST_TIMEOUT_SECONDS="${BACKTEST_TIMEOUT_SECONDS:-2700}"
mkdir -p seal/{reports,logs,data}
if [ ! -s seal/ctrader.pwd ]; then printf '%s' "$CTRADER_PASSWORD" > seal/ctrader.pwd; chmod 600 seal/ctrader.pwd; fi
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull "$IMAGE" >/dev/null
if [ ! -s seal/accounts.json ]; then
 docker run --rm -v "$PWD/seal:/work" "$IMAGE" accounts --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd > seal/accounts.json
fi
ACCT=$(python3 - <<'PY'
import json,os
a=json.load(open('seal/accounts.json',encoding='utf-8-sig')); e=os.environ['CTRADER_ACCOUNT'].strip()
m=next((x for x in a if str(x.get('Number',''))==e or str(x.get('Id',''))==e),None)
if not m or m.get('Broker','').lower()!='fxpro' or m.get('Live') is not False or m.get('DepositCurrency')!='USD' or int(m.get('Leverage',0))!=500:
 raise SystemExit('FxPro demo USD 1:500 mismatch')
print(m['Number'])
PY
)
CNAME="v60-$(echo "$RUN_NAME"|tr '[:upper:]_' '[:lower:]-')-$GITHUB_RUN_ID"
docker run --name "$CNAME" -v "$PWD/seal:/work" "$IMAGE" backtest "/work/${ALGO#seal/}"  --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd --account="$ACCT" --symbol=XAUUSD --period=m1  --start="$START_DATE" --end="$END_DATE" --balance="$BALANCE" --data-mode=m1 --data-dir=/work/data --commission=35 --spread="${SPREAD:-1}"  --SymbolName=XAUUSD --TradingEnabled="$TRADING" --BasketRiskPercent=1.0 --AdaptiveCapitalMode=true --MinimumSupportedEquity=100  --MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3 --MaxSpreadPips=60 --RoundTurnCommissionPips=0.5  --SlippageStressPips=0.3 --MinimumNetRR=2.0 --MinStopLossPips=10 --MinFreeMarginRiskMultiple=5  --M15SwingDepth=3 --M15SwingLookback=320 --H1SwingDepth=3 --H4SwingDepth=2 --PortfolioMaxCandidates=12 --CandidateTtlM15Bars=12  --MinGeometryQuality=0.55 --MinPrzConfluence=0.55 --EnableHarmonicRobustnessGate=false --EnableRegimeContextGate=false  --EnableEnhancedM1Confirmation=false --EnableCapitalFeasibilityGate=false --EnableTransitionStateVeto=false  --EnableExhaustionEvidenceVeto=true --EnableRouteSpecificM1Veto=false  --EnableDeferredCandidateRetention=true --EnableFrequencyAgingPriority=true --CandidateAgeRankBoost=0.08  --EnableStructuredRecallExpansion=true --RecallMinGeometry=0.72 --RecallMinPrz=0.72 --RecallMinConfidence=0.68  --EnableCanonicalSetupIdentity=true --EnableCanonicalStandardCoordinates=true --EnableIndependentPivotGraph=true  --EnableTransitionProofGate=true --EnableM1RescueLane=false --M1RescueMaxBars=3 --EnableDiversityScheduler=true  --EnableScaleRouteAdmission=true --EnableM1TemporalRescue=false --EnableArmedExecutionGrace=false --ArmedGraceMinutes=90  --EnablePreExecutionGridRevalidation="$REVALIDATE"  --EnablePersistentArmedQueue="$PQUEUE" --EnableEventDrivenSerialHandoff="$HANDOFF"  --EnablePatternNativeM1Expansion="$NATIVE" --PatternNativeM1MaxBars="$NATIVEBARS"  --EnableOpportunityDecayRanking="$DECAY" --ParkedHardLifetimeMinutes="$HARDLIFE" --EnableFamilyNativeConversion="$FAMNATIVE" --EnableFamilyNativeObservation="$FAMOBS" --EnableCanonicalFamilyContracts="$CANCONTRACT" --EnableFamilyCompletionContract="$FAMCONF" --FamilyConfirmationWindowBars=6 --EnableGridSpanSemanticV2="$GRIDV2" --EnableStructuralInvalidationV2="$STOPV2" --EnableFamilyNativeJointGeometry="$JOINT" --EnableFamilyNativeExecutionCorridor="$CORRIDOR" --EnableEntryAnchorForensics="$ANCHORFORENSICS" --EnableFamilyIdentityReconstruction="$IDENT" --EnableBoundedPivotGraph="$BOUNDED" --MaxMicroPivotSkips="$SKIPS" --FamilyDetectionQuota="$FQUOTA" --EnableFamilyNativeProjectedPrz="$PRJPRZ" --EnableDetectorTruthLedger="$DTRUTH" --EnableV60FamilyBooks="$FAMILYBOOKS" --EnableV60CanonicalManifold="$MANIFOLD" --EnableV60PureProjectedPrz="$PUREPRZ" --EnableV60TemporalEventDag="$DAG" --EnableV60ExcursionCaptureResearch="$CAPRESEARCH" --EnableV60ExcursionCaptureLive="$CAPLIVE" --EnableV60MatchedControlAttribution="$MATCHED" --V60MaxProjectionErrorAtr="$PROJERR" --V60ManifoldSigma="$MSIG" --EnableV60UniversalResearchContinuation="$RESEARCHCONT" --EnableV60VirtualParallelExecution="$SHADOW" --EnableV60CalibratedCapitalAdmission="$CALADMIT" --EnableV60FamilyRepresentativeArbitration="$FAMREP" --EnableV60AbcdStandaloneCapital="$ABCDLIVE" --EnableV60GridExecution="$V60GRID" --V60Variant="$V60VARIANT" --EnableV60AdaptiveFibonacciGrid="$V60ADAPTIVE" --EnableV60ConvexCaptureResearch="$V60CONVEX" --EnableV60RunnerResearch="$V60RUNNER" --V60RunnerFraction="$V60RUNNERFRAC" --EnableV60ClusterAwareEvidence="$V60CLUSTER" --EnableV60ContinuousAlphaSurface="$V60SURFACE" --EnableV60OpportunityCostScheduler="$V60SCHED" --V60MinCalibratedLowerBoundR="$CALMIN" --V60CalibrationManifest="$CALMAN"  --GridCancelMfeR=0.50 --NoMfeProofR=0.15 --NoMfeKillR=0.80 --NoMfeMinAgeMinutes=3  --BreakEvenTriggerR=1.0 --BreakEvenLockR=0.10 --TrailTriggerR=1.50 --TrailDistanceR=0.75  --EvaluationStartUtcIso="$EVAL_DATE" --report="/work/reports/$RUN_NAME.html" --report-json="/work/reports/$RUN_NAME.json" --exit-on-stop  > "seal/logs/$RUN_NAME.log" 2>&1 &
PID=$!; DONE=0
echo "[V60-WATCHDOG] run=$RUN_NAME pid=$PID timeoutSeconds=$BACKTEST_TIMEOUT_SECONDS"
for ((i=0;i<BACKTEST_TIMEOUT_SECONDS;i+=5)); do
 if (( i % 60 == 0 )); then echo "[V60-WATCHDOG] run=$RUN_NAME elapsedSeconds=$i status=running"; fi
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
test "$DONE" = 1 || { echo "[V60-WATCHDOG-FAIL] run=$RUN_NAME"; tail -400 "seal/logs/$RUN_NAME.log" || true; exit 20; }
echo "[V60-WATCHDOG] run=$RUN_NAME status=complete"
