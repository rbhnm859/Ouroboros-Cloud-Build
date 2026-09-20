using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBotV54 : Robot
    {
        private const string Version = "HarmonyBot V54 — Universal Harmonic Liberation & Fibonacci Grid Alpha Core";
        private const string BotPrefix = "HB54";

        [Parameter("Symbol", DefaultValue = "XAUUSD")]
        public new string SymbolName { get; set; }

        [Parameter("Trading Enabled", DefaultValue = true)]
        public bool TradingEnabled { get; set; }

        [Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]
        public double BasketRiskPercent { get; set; }

        [Parameter("Adaptive Capital Mode", DefaultValue = true)]
        public bool AdaptiveCapitalMode { get; set; }

        [Parameter("Minimum Supported Equity", DefaultValue = 100.0, MinValue = 50.0, MaxValue = 1000.0)]
        public double MinimumSupportedEquity { get; set; }

        [Parameter("Micro Capital Threshold", DefaultValue = 500.0, MinValue = 100.0, MaxValue = 2000.0)]
        public double MicroCapitalThreshold { get; set; }

        [Parameter("Grid Cancel MFE R", DefaultValue = 0.50, MinValue = 0.20, MaxValue = 1.0)]
        public double GridCancelMfeR { get; set; }

        [Parameter("Slippage Stress Pips", DefaultValue = 0.30, MinValue = 0.0, MaxValue = 20.0)]
        public double SlippageStressPips { get; set; }

        [Parameter("Max Drawdown %", DefaultValue = 10.0, MinValue = 1.0, MaxValue = 20.0)]
        public double MaxDrawdownPercent { get; set; }

        [Parameter("Daily Loss Limit %", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 10.0)]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Max Spread Pips", DefaultValue = 60.0, MinValue = 1.0, MaxValue = 300.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Commission RT Pips", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 100.0)]
        public double RoundTurnCommissionPips { get; set; }

        [Parameter("Minimum Net RR", DefaultValue = 2.0, MinValue = 1.0, MaxValue = 5.0)]
        public double MinimumNetRR { get; set; }

        [Parameter("Min SL Pips", DefaultValue = 10.0, MinValue = 1.0, MaxValue = 1000.0)]
        public double MinStopLossPips { get; set; }

        [Parameter("Min Free Margin Headroom", DefaultValue = 5.0, MinValue = 1.0, MaxValue = 20.0)]
        public double MinFreeMarginRiskMultiple { get; set; }

        [Parameter("M15 Swing Depth", DefaultValue = 3, MinValue = 2, MaxValue = 8)]
        public int M15SwingDepth { get; set; }

        [Parameter("M15 Swing Lookback", DefaultValue = 320, MinValue = 100, MaxValue = 1200)]
        public int M15SwingLookback { get; set; }

        [Parameter("H1 Swing Depth", DefaultValue = 3, MinValue = 2, MaxValue = 8)]
        public int H1SwingDepth { get; set; }

        [Parameter("H4 Swing Depth", DefaultValue = 2, MinValue = 2, MaxValue = 6)]
        public int H4SwingDepth { get; set; }

        [Parameter("Portfolio Max Candidates", DefaultValue = 8, MinValue = 2, MaxValue = 12)]
        public int PortfolioMaxCandidates { get; set; }

        [Parameter("Candidate TTL M15 Bars", DefaultValue = 8, MinValue = 2, MaxValue = 24)]
        public int CandidateTtlM15Bars { get; set; }

        [Parameter("Min Geometry", DefaultValue = 0.55, MinValue = 0.30, MaxValue = 0.90)]
        public double MinGeometryQuality { get; set; }

        [Parameter("Min PRZ", DefaultValue = 0.55, MinValue = 0.30, MaxValue = 0.90)]
        public double MinPrzConfluence { get; set; }

        [Parameter("Enhanced Harmonic Quality", DefaultValue = true)]
        public bool EnableHarmonicRobustnessGate { get; set; }

        [Parameter("Regime Context Gate", DefaultValue = true)]
        public bool EnableRegimeContextGate { get; set; }

        [Parameter("Enhanced M1 Confirmation", DefaultValue = true)]
        public bool EnableEnhancedM1Confirmation { get; set; }

        [Parameter("Capital Feasibility Gate", DefaultValue = false)]
        public bool EnableCapitalFeasibilityGate { get; set; }

        [Parameter("Transition State Veto", DefaultValue = true)]
        public bool EnableTransitionStateVeto { get; set; }

        [Parameter("Exhaustion Evidence Veto", DefaultValue = true)]
        public bool EnableExhaustionEvidenceVeto { get; set; }

        [Parameter("Route-Specific M1 Veto", DefaultValue = true)]
        public bool EnableRouteSpecificM1Veto { get; set; }

        [Parameter("Deferred Candidate Retention", DefaultValue = true)]
        public bool EnableDeferredCandidateRetention { get; set; }

        [Parameter("Frequency Aging Priority", DefaultValue = true)]
        public bool EnableFrequencyAgingPriority { get; set; }

        [Parameter("Candidate Age Rank Boost", DefaultValue = 0.08, MinValue = 0.0, MaxValue = 0.20)]
        public double CandidateAgeRankBoost { get; set; }

        [Parameter("Structured Recall Expansion", DefaultValue = false)]
        public bool EnableStructuredRecallExpansion { get; set; }

        [Parameter("Recall Min Geometry", DefaultValue = 0.72, MinValue = 0.60, MaxValue = 0.90)]
        public double RecallMinGeometry { get; set; }

        [Parameter("Recall Min PRZ", DefaultValue = 0.72, MinValue = 0.60, MaxValue = 0.90)]
        public double RecallMinPrz { get; set; }

        [Parameter("Recall Min Confidence", DefaultValue = 0.68, MinValue = 0.55, MaxValue = 0.90)]
        public double RecallMinConfidence { get; set; }

        [Parameter("Canonical Setup Identity", DefaultValue = true)]
        public bool EnableCanonicalSetupIdentity { get; set; }

        [Parameter("Canonical Standard Coordinates", DefaultValue = true)]
        public bool EnableCanonicalStandardCoordinates { get; set; }

        [Parameter("Independent Pivot Graph", DefaultValue = true)]
        public bool EnableIndependentPivotGraph { get; set; }

        [Parameter("Transition Proof Gate", DefaultValue = true)]
        public bool EnableTransitionProofGate { get; set; }

        [Parameter("M1 Rescue Lane", DefaultValue = true)]
        public bool EnableM1RescueLane { get; set; }

        [Parameter("M1 Rescue Max Bars", DefaultValue = 3, MinValue = 1, MaxValue = 5)]
        public int M1RescueMaxBars { get; set; }

        [Parameter("Diversity Scheduler", DefaultValue = true)]
        public bool EnableDiversityScheduler { get; set; }

        [Parameter("Scale-Route Admission", DefaultValue = true)]
        public bool EnableScaleRouteAdmission { get; set; }

        [Parameter("M1 Temporal Rescue", DefaultValue = true)]
        public bool EnableM1TemporalRescue { get; set; }

        [Parameter("Armed Execution Grace", DefaultValue = true)]
        public bool EnableArmedExecutionGrace { get; set; }

        [Parameter("Armed Grace Minutes", DefaultValue = 90, MinValue = 15, MaxValue = 180)]
        public int ArmedGraceMinutes { get; set; }

        [Parameter("Pre-Execution Grid Revalidation", DefaultValue = true)]
        public bool EnablePreExecutionGridRevalidation { get; set; }

        [Parameter("Persistent Armed Queue", DefaultValue = true)]
        public bool EnablePersistentArmedQueue { get; set; }

        [Parameter("Event-Driven Serial Handoff", DefaultValue = true)]
        public bool EnableEventDrivenSerialHandoff { get; set; }

        [Parameter("Pattern-Native M1 Expansion", DefaultValue = true)]
        public bool EnablePatternNativeM1Expansion { get; set; }

        [Parameter("Pattern-Native M1 Max Bars", DefaultValue = 4, MinValue = 3, MaxValue = 4)]
        public int PatternNativeM1MaxBars { get; set; }

        [Parameter("Opportunity Decay Ranking", DefaultValue = true)]
        public bool EnableOpportunityDecayRanking { get; set; }

        [Parameter("Parked Hard Lifetime Minutes", DefaultValue = 180, MinValue = 180, MaxValue = 180)]
        public int ParkedHardLifetimeMinutes { get; set; }

        [Parameter("Family-Native Conversion", DefaultValue = true)]
        public bool EnableFamilyNativeConversion { get; set; }

        [Parameter("Family-Native Observation", DefaultValue = true)]
        public bool EnableFamilyNativeObservation { get; set; }

        [Parameter("Canonical Family Contracts", DefaultValue = false)]
        public bool EnableCanonicalFamilyContracts { get; set; }

        [Parameter("Family Completion Contract", DefaultValue = false)]
        public bool EnableFamilyCompletionContract { get; set; }

        [Parameter("Family Confirmation Window Bars", DefaultValue = 6, MinValue = 6, MaxValue = 6)]
        public int FamilyConfirmationWindowBars { get; set; }

        [Parameter("Grid Span Semantic V2", DefaultValue = false)]
        public bool EnableGridSpanSemanticV2 { get; set; }

        [Parameter("Structural Invalidation V2", DefaultValue = false)]
        public bool EnableStructuralInvalidationV2 { get; set; }

        [Parameter("Family-Native Joint Geometry", DefaultValue = false)]
        public bool EnableFamilyNativeJointGeometry { get; set; }

        [Parameter("Family-Native Execution Corridor", DefaultValue = false)]
        public bool EnableFamilyNativeExecutionCorridor { get; set; }

        [Parameter("Entry Anchor Forensics", DefaultValue = true)]
        public bool EnableEntryAnchorForensics { get; set; }

        [Parameter("Family Identity Reconstruction", DefaultValue = false)]
        public bool EnableFamilyIdentityReconstruction { get; set; }

        [Parameter("Bounded Pivot Graph", DefaultValue = false)]
        public bool EnableBoundedPivotGraph { get; set; }

        [Parameter("Max Micro Pivot Skips", DefaultValue = 2, MinValue = 0, MaxValue = 2)]
        public int MaxMicroPivotSkips { get; set; }

        [Parameter("Family Detection Quota", DefaultValue = 4, MinValue = 1, MaxValue = 8)]
        public int FamilyDetectionQuota { get; set; }

        [Parameter("Family Projected PRZ", DefaultValue = false)]
        public bool EnableFamilyNativeProjectedPrz { get; set; }

        [Parameter("Detector Truth Ledger", DefaultValue = true)]
        public bool EnableDetectorTruthLedger { get; set; }

        [Parameter("Family Native Qualification V2", DefaultValue = false)]
        public bool EnableFamilyNativeQualificationV2 { get; set; }

        [Parameter("Family Native Router V2", DefaultValue = false)]
        public bool EnableFamilyNativeRouterV2 { get; set; }

        [Parameter("Family Native Confirmation V2", DefaultValue = false)]
        public bool EnableFamilyNativeConfirmationV2 { get; set; }

        [Parameter("Orthogonal Context Feature Bus", DefaultValue = false)]
        public bool EnableOrthogonalContextFeatureBus { get; set; }

        [Parameter("Fibonacci Grid Execution", DefaultValue = true)]
        public bool EnableFibonacciGridExecution { get; set; }

        [Parameter("Universal Harmonic Liberation V54", DefaultValue = false)]
        public bool EnableUniversalHarmonicLiberationV54 { get; set; }

        [Parameter("Core Alpha Preservation V54", DefaultValue = false)]
        public bool EnableCoreAlphaPreservationV54 { get; set; }

        [Parameter("Expansion Economic Gate V54", DefaultValue = false)]
        public bool EnableExpansionEconomicGateV54 { get; set; }

        [Parameter("Family Grid Allocation V54", DefaultValue = false)]
        public bool EnableFamilyGridAllocationV54 { get; set; }

        [Parameter("State Aware Grid Core V54", DefaultValue = false)]
        public bool EnableGridStateAwareV54 { get; set; }

        [Parameter("Min Harmonic Robustness", DefaultValue = 0.56, MinValue = 0.40, MaxValue = 0.80)]
        public double MinHarmonicRobustness { get; set; }

        [Parameter("No-MFE Proof R", DefaultValue = 0.15, MinValue = 0.05, MaxValue = 0.40)]
        public double NoMfeProofR { get; set; }

        [Parameter("No-MFE Kill R", DefaultValue = 0.80, MinValue = 0.50, MaxValue = 1.20)]
        public double NoMfeKillR { get; set; }

        [Parameter("No-MFE Min Age Minutes", DefaultValue = 3.0, MinValue = 1.0, MaxValue = 30.0)]
        public double NoMfeMinAgeMinutes { get; set; }

        [Parameter("BreakEven Trigger R", DefaultValue = 1.0, MinValue = 0.8, MaxValue = 2.0)]
        public double BreakEvenTriggerR { get; set; }

        [Parameter("BreakEven Lock R", DefaultValue = 0.10, MinValue = 0.0, MaxValue = 0.50)]
        public double BreakEvenLockR { get; set; }

        [Parameter("Trail Trigger R", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 3.0)]
        public double TrailTriggerR { get; set; }

        [Parameter("Trail Distance R", DefaultValue = 0.75, MinValue = 0.30, MaxValue = 1.50)]
        public double TrailDistanceR { get; set; }

        [Parameter("Evaluation Start UTC", DefaultValue = "")]
        public string EvaluationStartUtcIso { get; set; }

        private Symbol _symbol;
        private Bars _h4Bars;
        private Bars _h1Bars;
        private Bars _m15Bars;
        private Bars _m1Bars;
        private TimeZoneInfo _londonTz;
        private TimeZoneInfo _newYorkTz;

        private readonly List<PatternProfile> _profiles = new List<PatternProfile>();
        private readonly Dictionary<string, CandidateRecord> _candidates = new Dictionary<string, CandidateRecord>();
        private readonly Dictionary<long, PositionLedger> _positions = new Dictionary<long, PositionLedger>();
        private readonly Dictionary<string, PipelineCounter> _pipeline = new Dictionary<string, PipelineCounter>();
        private readonly Dictionary<string, FibonacciBasket> _baskets = new Dictionary<string, FibonacciBasket>();
        private long _basketSeq;
        private int _gridRiskViolations;
        private int _duplicateGridLegs;
        private int _orphanPendingOrders;
        private int _stopWideningViolations = 0;
        private int _gapThroughInvalidations;
        private int _gapThroughSurvivors;
        private int _unprotectedSurvivors;
        private int _postFillProtectionFailures;
        private int _actualBasketRiskViolations;
        private int _executionStateViolations;
        private int _virtualGridFills;
        private int _microModeBaskets;
        private int _capitalRejectedBaskets;
        private int _marginRiskViolations;
        private int _alphaQualityRejected;
        private int _regimeRejected;
        private int _confirmationRejected;
        private int _capitalInfeasibleCandidates;
        private int _alphaPassed;
        private int _schedulerDeferred;
        private int _schedulerRecoveredExecutions;
        private int _structuredRecallAdmitted;
        private readonly HashSet<string> _deferredCandidates = new HashSet<string>();
        private readonly HashSet<long> _postFillValidated = new HashSet<long>();
        private readonly HashSet<long> _postFillInProgress = new HashSet<long>();
        private readonly Dictionary<string, string> _activeSetupOwners = new Dictionary<string, string>();
        private readonly HashSet<string> _executedSetupKeys = new HashSet<string>();
        private int _canonicalDuplicateSuppressed;
        private int _m1RescueAdmissions;
        private int _transitionProofRejected;
        private int _independentScaleCandidates;
        private int _scaleRouteRejected;
        private int _temporalRescueAdmissions;
        private int _armedGraceExtended;
        private int _preExecutionRevalidationRejected;
        private readonly HashSet<string> _parkedCandidateIds = new HashSet<string>();
        private readonly List<double> _slotWaitMinutes = new List<double>();
        private readonly List<double> _basketOccupancyMinutes = new List<double>();
        private int _slotBlocked;
        private int _parkedCount;
        private int _parkedRevalidated;
        private int _parkedRevalidationRejected;
        private int _parkedRecoveredExecutions;
        private int _nativeTemporalPass;
        private int _hardLifetimeExpired;
        private int _opportunityDecayRejected;
        private int _missedPositiveSetups;
        private int _avoidedNegativeSetups;

        private readonly Dictionary<string, int> _familyContractPass = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _familyContractWindowReject = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _gridPlanRejectReasons = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _detectorTruth = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _conversionTruth = new Dictionary<string, int>();

        private DateTime _lastM15Closed = DateTime.MinValue;
        private DateTime _lastM1Closed = DateTime.MinValue;
        private DateTime _currentDay;
        private double _dayStartEquity;
        private double _equityPeak;
        private bool _dailyLocked;
        private long _candidateSeq;
        private int _executionErrors;
        private readonly Dictionary<string, int> _executionErrorReasons = new Dictionary<string, int>();
        private DateTime? _evaluationStartUtc;
        private double _initialEquity;
        private bool _initialCapitalEligible;

        protected override void OnStart()
        {
            _symbol = Symbols.GetSymbol(SymbolName);
            if (_symbol == null)
            {
                Print("[V54-FATAL] SYMBOL_NOT_FOUND {0}", SymbolName);
                Stop();
                return;
            }

            _h4Bars = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _m1Bars = MarketData.GetBars(TimeFrame.Minute, SymbolName);

            if (!BarsObjectsReady())
            {
                Print("[V54-FATAL] TIMEFRAME_OBJECT_LOAD_FAILED");
                Stop();
                return;
            }

            WarmupBars(_h4Bars, 230, "H4");
            WarmupBars(_h1Bars, 230, "H1");
            WarmupBars(_m15Bars, 360, "M15");
            WarmupBars(_m1Bars, 120, "M1");

            if (!BarsReady())
                Print("[V54-WARMUP-PENDING] H4={0} H1={1} M15={2} M1={3}",
                    Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars));

            _londonTz = ResolveTimeZone("Europe/London", "GMT Standard Time");
            _newYorkTz = ResolveTimeZone("America/New_York", "Eastern Standard Time");
            if (_londonTz == null || _newYorkTz == null)
            {
                Print("[V54-FATAL] DST_TIMEZONE_UNAVAILABLE");
                Stop();
                return;
            }

            if (!string.IsNullOrWhiteSpace(EvaluationStartUtcIso))
            {
                DateTime parsed;
                if (DateTime.TryParse(EvaluationStartUtcIso, CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal, out parsed))
                    _evaluationStartUtc = parsed;
            }

            BuildPatternProfiles();
            _initialEquity = Account.Equity;
            _initialCapitalEligible = _initialEquity + 1e-8 >= MinimumSupportedEquity;
            _equityPeak = Account.Equity;
            ResetDaily(true);

            Positions.Closed += OnPositionClosed;
            Positions.Opened += OnPositionOpened;
            PendingOrders.Filled += OnPendingOrderFilled;

            PrintBrokerCapabilityProfile();

            Print("[V54-START] version={0} symbol={1} H4={2} H1={3} M15={4} M1={5} profiles={6}",
                Version, SymbolName, Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars), _profiles.Count);
            Print("[V54-TIMEFRAME-AUDIT] primaryPattern=M15 execution=M1 macro=H4 intermediate=H1 allCompletedBars=true");
            Print("[V54-SESSION-AUDIT] london={0} newYork={1} dstAware=true", _londonTz.Id, _newYorkTz.Id);
            Print("[V54-ALPHA-CONFIG] qualityObservation={0} legacyRegime={1} legacyEnhancedM1={2} capitalFeasibility={3} transitionVeto={4} exhaustionVeto={5} routeM1Veto={6}",
                EnableHarmonicRobustnessGate, EnableRegimeContextGate, EnableEnhancedM1Confirmation, EnableCapitalFeasibilityGate,
                EnableTransitionStateVeto, EnableExhaustionEvidenceVeto, EnableRouteSpecificM1Veto);
            Print("[V54-FREQUENCY-CONFIG] deferredRetention={0} agingPriority={1} ageBoost={2:F3} structuredRecall={3} recallGeometry={4:F3} recallPrz={5:F3} recallConfidence={6:F3}",
                EnableDeferredCandidateRetention, EnableFrequencyAgingPriority, CandidateAgeRankBoost, EnableStructuredRecallExpansion,
                RecallMinGeometry, RecallMinPrz, RecallMinConfidence);
            Print("[V54-RESTORED-KERNEL] canonicalSetup={0} canonicalStandard={1} independentPivotGraph={2} transitionProof={3} m1Rescue={4} rescueBars={5} diversityScheduler={6} executionClock=M1 projectedD=false",
                EnableCanonicalSetupIdentity, EnableCanonicalStandardCoordinates, EnableIndependentPivotGraph,
                EnableTransitionProofGate, EnableM1RescueLane, M1RescueMaxBars, EnableDiversityScheduler);
            Print("[V54-CONVERSION-ARCH] scaleRouteAdmission={0} temporalRescue={1} armedGrace={2} graceMinutes={3} preExecutionRevalidation={4}",
                EnableScaleRouteAdmission, EnableM1TemporalRescue, EnableArmedExecutionGrace, ArmedGraceMinutes,
                EnablePreExecutionGridRevalidation);
            Print("[V54-FAMILY-NATIVE] conversion={0} observation={1} principle=PATTERN_IDENTITY_NEQ_EXECUTION_IDENTITY", EnableFamilyNativeConversion, EnableFamilyNativeObservation);
            Print("[V54-COMPLETION-CONTRACT] canonicalContracts={0} familyCompletion={1} windowBars={2} provenLane=ABCD_SHARK_CYPHER_FROZEN",
                EnableCanonicalFamilyContracts, EnableFamilyCompletionContract, FamilyConfirmationWindowBars);
            Print("[V54-STRUCTURAL-GRID-CONTRACT] gridSpanV2={0} structuralInvalidationV2={1} rule=PRZ_LEGALITY_PLUS_RISK_RR_NOT_LEGACY_XA_MINSPAN",
                EnableGridSpanSemanticV2, EnableStructuralInvalidationV2);
            Print("[V54-MATH-GEOMETRY] jointGeometry={0} executionCorridor={1} entryAnchorForensics={2} rule=FAMILY_NATIVE_GEOMETRY_WITHOUT_RISK_RELAXATION",
                EnableFamilyNativeJointGeometry, EnableFamilyNativeExecutionCorridor, EnableEntryAnchorForensics);
            Print("[V54-DETECTOR-ARCH] identityReconstruction={0} boundedPivotGraph={1} maxMicroSkips={2} familyQuota={3} projectedPrz={4} truthLedger={5} rule=DETECT_MANY_EXECUTE_ONE",
                EnableFamilyIdentityReconstruction, EnableBoundedPivotGraph, MaxMicroPivotSkips, FamilyDetectionQuota,
                EnableFamilyNativeProjectedPrz, EnableDetectorTruthLedger);
            Print("[V54-ARCH] liberation={0} corePreservation={1} expansionEconomicGate={2} familyGrid={3} stateAwareGrid={4} gridExecution={5} rule=CORE_ALPHA_PRESERVED_EXPANSION_MUST_EARN_ADMISSION",
                EnableUniversalHarmonicLiberationV54, EnableCoreAlphaPreservationV54, EnableExpansionEconomicGateV54,
                EnableFamilyGridAllocationV54, EnableGridStateAwareV54, EnableFibonacciGridExecution);
            Print("[V54-CONVERSION-ARCH-V2] qualification={0} router={1} confirmation={2} contextBus={3} gridExecution={4} rule=FAMILY_NATIVE_POST_DETECTOR_CAUSAL_ISOLATION",
                EnableFamilyNativeQualificationV2, EnableFamilyNativeRouterV2, EnableFamilyNativeConfirmationV2,
                EnableOrthogonalContextFeatureBus, EnableFibonacciGridExecution);
            Print("[V54-THROUGHPUT-ARCH] persistentQueue={0} serialHandoff={1} nativeM1={2} nativeBars={3} decayRanking={4} hardLifetimeMinutes={5} alphaKernel=V46_SCALE_CONVERSION_FROZEN",
                EnablePersistentArmedQueue, EnableEventDrivenSerialHandoff, EnablePatternNativeM1Expansion,
                PatternNativeM1MaxBars, EnableOpportunityDecayRanking, ParkedHardLifetimeMinutes);
        }

        protected override void OnStop()
        {
            CancelAllOwnPending("BOT_STOP");
            EnsureServerProtection();
            Positions.Closed -= OnPositionClosed;
            Positions.Opened -= OnPositionOpened;
            PendingOrders.Filled -= OnPendingOrderFilled;
            foreach (var kv in _pipeline.OrderBy(k => k.Key))
            {
                var x = kv.Value;
                Print("[V54-PIPELINE] pattern={0} detected={1} validated={2} routed={3} prz={4} confirming={5} nativeTemporalPass={6} armed={7} slotBlocked={8} parked={9} revalidated={10} revalidationRejected={11} basketPlanned={12} leg0={13} leg1={14} leg2={15} leg3={16} basketClosed={17} executed={18} expired={19} rejected={20} invalidated={21}",
                    kv.Key, x.Detected, x.Validated, x.Routed, x.PrzWaiting, x.Confirming, x.NativeTemporalPass, x.Armed,
                    x.SlotBlocked, x.Parked, x.Revalidated, x.RevalidationRejected, x.BasketPlanned,
                    x.Leg0Executed, x.Leg1Filled, x.Leg2Filled, x.Leg3Filled, x.BasketClosed, x.Executed, x.Expired, x.Rejected, x.Invalidated);
            }
            if (EnableEntryAnchorForensics)
            {
                foreach (var c in _candidates.Values.Where(x => x.Signal != null && x.CompletionAnchorPrice > 0).OrderBy(x => x.CandidateId))
                {
                    Print("[V54-ENTRY-ANCHOR-FORENSICS] cid={0} setup={1} pattern={2} route={3} scale={4} completion={5} confirm={6} retest={7} completionMfeR={8:F3} completionMaeR={9:F3} confirmMfeR={10:F3} confirmMaeR={11:F3} retestMfeR={12:F3} retestMaeR={13:F3}",
                        c.CandidateId, c.SetupKey, c.Signal.PatternName, c.Route, c.Signal.PivotScale,
                        c.CompletionAnchorPrice, c.NativeConfirmAnchorPrice, c.NativeRetestAnchorPrice,
                        c.CompletionAnchorMfeR, c.CompletionAnchorMaeR, c.NativeConfirmMfeR, c.NativeConfirmMaeR,
                        c.NativeRetestMfeR, c.NativeRetestMaeR);
                }
            }
            if (EnableDetectorTruthLedger)
            {
                foreach (var kv in _detectorTruth.OrderBy(x => x.Key))
                {
                    int sep = kv.Key.IndexOf("::", StringComparison.Ordinal);
                    string pattern = sep >= 0 ? kv.Key.Substring(0, sep) : "UNKNOWN";
                    string stage = sep >= 0 ? kv.Key.Substring(sep + 2) : kv.Key;
                    Print("[V54-DETECTOR-TRUTH] pattern={0} stage={1} count={2}", pattern, stage, kv.Value);
                }
            }
            foreach (var kv in _conversionTruth.OrderBy(x => x.Key))
            {
                int sep = kv.Key.IndexOf("::", StringComparison.Ordinal);
                string pattern = sep >= 0 ? kv.Key.Substring(0, sep) : "UNKNOWN";
                string stage = sep >= 0 ? kv.Key.Substring(sep + 2) : kv.Key;
                Print("[V54-CONVERSION-TRUTH] pattern={0} stage={1} count={2}", pattern, stage, kv.Value);
            }
            Print("[V54-GRID-CAUSAL-MODE] enabled={0} rule=GRID_CHANGES_ENTRY_DISTRIBUTION_NOT_SIGNAL_THESIS", EnableFibonacciGridExecution);
            Print("[V54-SUMMARY] candidates={0} baskets={1} openLedgers={2} executionErrors={3} gridRiskViolations={4} duplicateGridLegs={5} orphanPendingOrders={6} stopWideningViolations={7} gapThroughInvalidations={8} gapThroughSurvivors={9} unprotectedSurvivors={10} postFillProtectionFailures={11} actualBasketRiskViolations={12} executionStateViolations={13} virtualGridFills={14} microModeBaskets={15} capitalRejectedBaskets={16} marginRiskViolations={17}",
                _candidateSeq, _baskets.Count, _positions.Count, _executionErrors, _gridRiskViolations, _duplicateGridLegs, _orphanPendingOrders, _stopWideningViolations,
                _gapThroughInvalidations, _gapThroughSurvivors, _unprotectedSurvivors, _postFillProtectionFailures, _actualBasketRiskViolations, _executionStateViolations,
                _virtualGridFills, _microModeBaskets, _capitalRejectedBaskets, _marginRiskViolations);
            Print("[V54-ALPHA-SUMMARY] qualityRejected={0} regimeRejected={1} confirmationRejected={2} capitalInfeasible={3} alphaPassed={4}",
                _alphaQualityRejected, _regimeRejected, _confirmationRejected, _capitalInfeasibleCandidates, _alphaPassed);
            Print("[V54-FREQUENCY-SUMMARY] schedulerDeferred={0} schedulerRecoveredExecutions={1} structuredRecallAdmitted={2} activeDeferred={3}",
                _schedulerDeferred, _schedulerRecoveredExecutions, _structuredRecallAdmitted, _deferredCandidates.Count);
            Print("[V54-INDEPENDENT-SETUP-SUMMARY] duplicateSuppressed={0} uniqueExecuted={1} rescueAdmissions={2} transitionProofRejected={3} independentScaleCandidates={4}",
                _canonicalDuplicateSuppressed, _executedSetupKeys.Count, _m1RescueAdmissions, _transitionProofRejected, _independentScaleCandidates);
            Print("[V54-CONVERSION-SUMMARY] scaleRouteRejected={0} temporalRescueAdmissions={1} armedGraceExtended={2} preExecutionRevalidationRejected={3}",
                _scaleRouteRejected, _temporalRescueAdmissions, _armedGraceExtended, _preExecutionRevalidationRejected);
            double avgWait = _slotWaitMinutes.Count > 0 ? _slotWaitMinutes.Average() : 0;
            double medWait = Percentile(_slotWaitMinutes, .50);
            double p90Wait = Percentile(_slotWaitMinutes, .90);
            double avgOccupancy = _basketOccupancyMinutes.Count > 0 ? _basketOccupancyMinutes.Average() : 0;
            Print("[V54-THROUGHPUT-SUMMARY] slotBlocked={0} parked={1} revalidated={2} revalidationRejected={3} recoveredExecutions={4} nativeTemporalPass={5} hardLifetimeExpired={6} decayRejected={7} avgSlotWaitMin={8:F2} medianSlotWaitMin={9:F2} p90SlotWaitMin={10:F2} avgBasketOccupancyMin={11:F2} missedPositive={12} avoidedNegative={13}",
                _slotBlocked, _parkedCount, _parkedRevalidated, _parkedRevalidationRejected, _parkedRecoveredExecutions,
                _nativeTemporalPass, _hardLifetimeExpired, _opportunityDecayRejected, avgWait, medWait, p90Wait, avgOccupancy,
                _missedPositiveSetups, _avoidedNegativeSetups);
            foreach (var p in _profiles.Select(x => x.Name).Distinct().OrderBy(x => x))
            {
                int pass = _familyContractPass.ContainsKey(p) ? _familyContractPass[p] : 0;
                int reject = _familyContractWindowReject.ContainsKey(p) ? _familyContractWindowReject[p] : 0;
                Print("[V54-FAMILY-CONTRACT-SUMMARY] pattern={0} pass={1} windowReject={2}", p, pass, reject);
            }
            foreach (var kv in _gridPlanRejectReasons.OrderBy(k => k.Key))
                Print("[V54-GRID-REJECT-SUMMARY] reason={0} count={1}", kv.Key, kv.Value);
            foreach (var kv in _executionErrorReasons.OrderBy(k => k.Key))
                Print("[V54-EXECUTION-ERROR-SUMMARY] code={0} count={1}", kv.Key, kv.Value);
        }

        protected override void OnBar()
        {
            try
            {
                if (!BarsReady()) return;
                ResetDaily(false);
                UpdateRiskLocks();

                ProcessNewM15Close();
                ProcessNewM1Close();
            }
            catch (Exception ex)
            {
                RecordExecutionError("EXCEPTION_ONBAR", ex.GetType().Name + ":" + ex.Message);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDaily(false);
                UpdateRiskLocks();
                ReconcileAndManageBaskets();
            }
            catch (Exception ex)
            {
                RecordExecutionError("EXCEPTION_ONTICK", ex.GetType().Name + ":" + ex.Message);
            }
        }

        private void ProcessNewM15Close()
        {
            int i = LastClosedIndex(_m15Bars);
            if (i < 50) return;
            DateTime t = _m15Bars.OpenTimes[i];
            if (t <= _lastM15Closed) return;
            _lastM15Closed = t;

            double atr = Atr(_m15Bars, 14, i);
            if (atr <= 0) return;

            var h4State = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1State = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            var regime = BuildRegimeSnapshot();
            var detected = DetectPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback, PortfolioMaxCandidates, "M15");

            foreach (var signal in detected)
            {
                string setupKey = BuildSetupGeometryKey(signal);
                string identityKey = EnableFamilyIdentityReconstruction ? BuildFamilyHypothesisKey(signal) : setupKey;
                if (EnableCanonicalSetupIdentity)
                {
                    if (_executedSetupKeys.Contains(setupKey))
                    {
                        _canonicalDuplicateSuppressed++;
                        DetectorTruth(signal.PatternName, "UNDERLYING_ALREADY_EXECUTED");
                        continue;
                    }
                    string owner;
                    if (_activeSetupOwners.TryGetValue(identityKey, out owner))
                    {
                        CandidateRecord existing;
                        if (_candidates.TryGetValue(owner, out existing) && existing.IsActive)
                        {
                            _canonicalDuplicateSuppressed++;
                            DetectorTruth(signal.PatternName, "FAMILY_HYPOTHESIS_DUPLICATE_SUPPRESSED");
                            continue;
                        }
                        _activeSetupOwners.Remove(identityKey);
                    }
                }

                string id = NewCandidateId(signal);
                if (_candidates.ContainsKey(id)) continue;

                var record = new CandidateRecord
                {
                    CandidateId = id,
                    SetupKey = setupKey,
                    IdentityKey = identityKey,
                    Signal = signal,
                    State = CandidateState.DETECTED,
                    DetectedUtc = Server.Time.ToUniversalTime(),
                    ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(2, Math.Min(CandidateTtlM15Bars, signal.Profile.MaxAgeM15Bars))),
                    LastReason = "PATTERN_DETECTED"
                };
                _candidates[id] = record;
                if (EnableCanonicalSetupIdentity) _activeSetupOwners[identityKey] = id;
                CountPipeline(signal.PatternName).Detected++;
                Ledger(record, CandidateState.DETECTED, "PATTERN_DETECTED");

                record.IsProvenCoreAlpha = EnableCoreAlphaPreservationV54 && V54CoreQualityEnvelope(signal);
                record.AlphaLane = record.IsProvenCoreAlpha ? "PROVEN_CORE_ALPHA" : "HARMONIC_EXPANSION_ALPHA";

                double familyQualificationScore;
                string familyQualificationReason;
                bool qualificationPass;
                if (EnableUniversalHarmonicLiberationV54)
                {
                    familyQualificationScore = V54FamilyLiberationQualityScore(signal);
                    familyQualificationReason = "LIBERATED_IDENTITY";
                    qualificationPass = true;
                    ConversionTruth(signal.PatternName, "LIBERATION_IDENTITY_PASS");
                }
                else if (EnableFamilyNativeQualificationV2)
                    qualificationPass = FamilyNativeQualificationPass(signal, out familyQualificationScore, out familyQualificationReason);
                else
                {
                    familyQualificationScore = .5 * signal.GeometryQuality + .5 * signal.PrzConfluence;
                    familyQualificationReason = "LEGACY_QUALITY";
                    qualificationPass = signal.GeometryQuality >= Math.Max(MinGeometryQuality, signal.Profile.MinGeometry) &&
                                        signal.PrzConfluence >= Math.Max(MinPrzConfluence, signal.Profile.MinPrz);
                }
                record.FamilyQualificationScore = familyQualificationScore;
                if (!qualificationPass)
                {
                    ConversionTruth(signal.PatternName, "QUALIFICATION_REJECT_" + familyQualificationReason);
                    Reject(record, "PATTERN_QUALITY");
                    continue;
                }
                ConversionTruth(signal.PatternName, "QUALIFICATION_PASS");

                record.AlphaQualityScore = HarmonicRobustnessScore(signal);
                if (EnableHarmonicRobustnessGate && !HarmonicRobustnessEligible(signal, record.AlphaQualityScore))
                {
                    _alphaQualityRejected++;
                    Event(record, "HARMONIC_ROBUSTNESS_OBSERVATION_ONLY");
                }

                Transition(record, CandidateState.VALIDATED, "PATTERN_VALIDATED");
                CountPipeline(signal.PatternName).Validated++;

                record.Conflict = ClassifyMtfConflict(signal.Direction, h4State, h1State);
                record.Regime = regime;
                record.RegimeScore = RegimeContextScore(signal, record.Conflict, regime);
                record.Context = EnableOrthogonalContextFeatureBus ? BuildOrthogonalContextFeatureBus(signal, regime) : null;
                record.ContextScore = EnableOrthogonalContextFeatureBus ? FamilyContextScore(signal, record.Context, regime) : .50;
                if (EnableUniversalHarmonicLiberationV54)
                {
                    var legacyRoute = RouteSignal(signal, record.Conflict, regime);
                    if (record.IsProvenCoreAlpha && legacyRoute != HarmonicRoute.NO_TRADE)
                    {
                        record.Route = legacyRoute;
                        record.AlphaLane = "PROVEN_CORE_ALPHA";
                        ConversionTruth(signal.PatternName, "CORE_ROUTE_PRESERVED");
                    }
                    else
                    {
                        record.IsProvenCoreAlpha = false;
                        record.AlphaLane = "HARMONIC_EXPANSION_ALPHA";
                        record.Route = RouteSignalFamilyNativeV54(signal, record.Conflict, regime, record.Context, record.ContextScore);
                    }
                }
                else
                    record.Route = EnableFamilyNativeRouterV2
                        ? RouteSignalFamilyNativeV2(signal, record.Conflict, regime, record.Context, record.ContextScore)
                        : RouteSignal(signal, record.Conflict, regime);

                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    if (EnableRegimeContextGate) _regimeRejected++;
                    ConversionTruth(signal.PatternName, "ROUTE_REJECT");
                    Reject(record, "ROUTER_NO_TRADE");
                    continue;
                }
                ConversionTruth(signal.PatternName, "ROUTE_PASS_" + record.Route);

                // V47 expands only genuinely independent secondary-scale setups.
                // V45 DEV showed secondary-scale AB=CD exhaustion positive in A/B/C,
                // while secondary-scale trend-aligned AB=CD was negative overall.
                if (!EnableUniversalHarmonicLiberationV54 && EnableScaleRouteAdmission && signal.PivotScale != M15SwingDepth &&
                    signal.PatternName == "AB=CD" && record.Route != HarmonicRoute.EXHAUSTION_REVERSAL)
                {
                    _scaleRouteRejected++;
                    Reject(record, "SECONDARY_SCALE_ABCD_ROUTE_REJECT");
                    continue;
                }

                if (EnableCapitalFeasibilityGate)
                {
                    double minL0Risk, minL0Margin;
                    record.CapitalFeasible = CapitalFeasibilityEligible(record, out minL0Risk, out minL0Margin);
                    record.CapitalMinL0Risk = minL0Risk;
                    record.CapitalMinL0Margin = minL0Margin;
                    if (!record.CapitalFeasible)
                    {
                        _capitalInfeasibleCandidates++;
                        Reject(record, "CAPITAL_INFEASIBLE_PRECHECK");
                        continue;
                    }
                }
                else record.CapitalFeasible = true;

                Print("[V54-ALPHA-CANDIDATE] cid={0} pattern={1} lane={13} familyQuality={14:F3} quality={2:F3} regime={3:F3} conflict={4} route={5} adxH1={6:F2} adxH4={7:F2} adxSlope={8:F2} atrPct={9:F3} efficiency={10:F3} capitalFeasible={11} minL0Risk={12:F4}",
                    record.CandidateId, signal.PatternName, record.AlphaQualityScore, record.RegimeScore, record.Conflict, record.Route,
                    regime.AdxH1, regime.AdxH4, regime.AdxH1Slope, regime.AtrPercentile, regime.Efficiency,
                    record.CapitalFeasible, record.CapitalMinL0Risk, record.AlphaLane, record.FamilyQualificationScore);

                Transition(record, CandidateState.ROUTED, "ROUTE_" + record.Route);
                CountPipeline(signal.PatternName).Routed++;
                Transition(record, CandidateState.WAIT_PRZ, "WAIT_PRZ");
                CountPipeline(signal.PatternName).PrzWaiting++;
            }

            TrimCandidateBook();
        }

        private void ProcessNewM1Close()
        {
            int i = LastClosedIndex(_m1Bars);
            if (i < 10) return;
            DateTime t = _m1Bars.OpenTimes[i];
            if (t <= _lastM1Closed) return;
            _lastM1Closed = t;
            DateTime utc = DateTime.SpecifyKind(t, DateTimeKind.Utc);

            foreach (var c in _candidates.Values.Where(x => x.IsActive).ToList())
            {
                UpdateOpportunityShadow(c, i);
                if (EnableEntryAnchorForensics) UpdateEntryAnchorForensics(c, i);

                bool queuedState = c.State == CandidateState.SLOT_BLOCKED || c.State == CandidateState.PARKED ||
                                   c.State == CandidateState.REVALIDATING || c.State == CandidateState.EXECUTABLE;
                if (queuedState && EnablePersistentArmedQueue)
                {
                    if (c.ParkedHardExpiryUtc.HasValue && utc >= c.ParkedHardExpiryUtc.Value)
                    {
                        _hardLifetimeExpired++;
                        MarkOpportunityTerminal(c, "HARD_LIFETIME_EXPIRED");
                        Expire(c, "HARD_LIFETIME_EXPIRED");
                        continue;
                    }
                    if (!IsInstitutionalSession(utc))
                    {
                        MarkOpportunityTerminal(c, "SESSION_EXPIRED");
                        Expire(c, "SESSION_EXPIRED");
                        continue;
                    }
                }
                else if (utc >= c.ExpiryUtc)
                {
                    Expire(c, "TTL_EXPIRED");
                    continue;
                }

                if (PatternInvalidatedBeforeEntry(c.Signal))
                {
                    MarkOpportunityTerminal(c, "STRUCTURAL_INVALIDATION");
                    Invalidate(c, "STRUCTURAL_INVALIDATION");
                    continue;
                }

                if (c.State == CandidateState.WAIT_PRZ)
                {
                    if (BarTouchesPrz(i, c.Signal))
                    {
                        c.PrzTouchUtc = utc;
                        if (EnableEntryAnchorForensics && c.CompletionAnchorPrice <= 0)
                            c.CompletionAnchorPrice = c.Signal.D.Price;
                        Transition(c, CandidateState.CONFIRMING, "PRZ_RETEST");
                        CountPipeline(c.Signal.PatternName).Confirming++;
                        ConversionTruth(c.Signal.PatternName, "PRZ_TOUCH");
                    }
                    continue;
                }

                if (c.State == CandidateState.CONFIRMING)
                {
                    if (!c.PrzTouchUtc.HasValue || utc <= c.PrzTouchUtc.Value) continue;

                    double legacyScore = M1ConfirmationScore(i, c.Signal);
                    c.ConfirmationScore = legacyScore;
                    double legacyRequired = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 0.75 : 0.60;
                    bool v53NativeLane = EnableFamilyNativeConfirmationV2 &&
                                         (!EnableCoreAlphaPreservationV54 || !c.IsProvenCoreAlpha) &&
                                         IsV54FamilyNativeConfirmationLane(c.Signal.PatternName);
                    bool familyContractLane = v53NativeLane || (EnableFamilyCompletionContract && IsFamilyCompletionLane(c.Signal.PatternName));
                    bool confirmationPass = false;

                    if (v53NativeLane)
                    {
                        c.FamilyConfirmationBarsObserved++;
                        double familyScore;
                        confirmationPass = UpdateFamilyNativeConfirmationV2(i, c, out familyScore);
                        c.ConfirmationScore = Math.Max(c.ConfirmationScore, familyScore);
                        if (confirmationPass)
                        {
                            IncrementCounter(_familyContractPass, c.Signal.PatternName);
                            ConversionTruth(c.Signal.PatternName, "CONFIRMATION_PASS_V2");
                            Event(c, "FAMILY_NATIVE_CONFIRMATION_V2_PASS_" + familyScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                        else if (c.FamilyConfirmationBarsObserved >= FamilyNativeConfirmationWindowLimit(c.Signal.PatternName))
                        {
                            IncrementCounter(_familyContractWindowReject, c.Signal.PatternName);
                            ConversionTruth(c.Signal.PatternName, "CONFIRMATION_WINDOW_REJECT_V2");
                            Reject(c, "FAMILY_NATIVE_CONFIRMATION_V2_WINDOW_EXHAUSTED");
                            continue;
                        }
                    }
                    else if (familyContractLane)
                    {
                        c.FamilyConfirmationBarsObserved++;
                        double familyScore;
                        confirmationPass = UpdateFamilyCompletionEvidence(i, c, out familyScore);
                        c.ConfirmationScore = Math.Max(c.ConfirmationScore, familyScore);
                        if (EnableEntryAnchorForensics && c.FamilyRetest && c.NativeRetestAnchorPrice <= 0)
                            c.NativeRetestAnchorPrice = _m1Bars.ClosePrices[i];
                        if (confirmationPass)
                        {
                            IncrementCounter(_familyContractPass, c.Signal.PatternName);
                            ConversionTruth(c.Signal.PatternName, "CONFIRMATION_PASS_LEGACY_FAMILY");
                            Event(c, "FAMILY_COMPLETION_CONTRACT_PASS_" + familyScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                        else if (c.FamilyConfirmationBarsObserved >= Math.Max(6, FamilyConfirmationWindowBars))
                        {
                            IncrementCounter(_familyContractWindowReject, c.Signal.PatternName);
                            ConversionTruth(c.Signal.PatternName, "CONFIRMATION_WINDOW_REJECT_LEGACY");
                            Reject(c, "FAMILY_COMPLETION_WINDOW_EXHAUSTED");
                            continue;
                        }
                    }
                    else confirmationPass = legacyScore >= legacyRequired;

                    if (!familyContractLane && !confirmationPass && EnablePatternNativeM1Expansion)
                    {
                        c.NativeM1BarsObserved++;
                        double nativeScore;
                        if (c.NativeM1BarsObserved <= Math.Max(3, Math.Min(4, PatternNativeM1MaxBars)) &&
                            UpdatePatternNativeM1State(i, c, out nativeScore))
                        {
                            c.ConfirmationScore = Math.Max(c.ConfirmationScore, nativeScore);
                            confirmationPass = true;
                            _nativeTemporalPass++;
                            CountPipeline(c.Signal.PatternName).NativeTemporalPass++;
                            Event(c, "PATTERN_NATIVE_M1_PASS_" + nativeScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                    }

                    if (!confirmationPass && EnableM1RescueLane)
                    {
                        c.RescueBarsObserved++;
                        double enhanced = EnhancedM1ConfirmationScore(i, c.Signal, c.Route, c.Regime);
                        c.RescueBestScore = Math.Max(c.RescueBestScore, enhanced);
                        bool evidencePass = RouteSpecificM1EvidencePass(i, c.Signal, c.Route);
                        double rescueThreshold = EnhancedM1Threshold(c.Route);
                        confirmationPass = c.RescueBarsObserved <= Math.Max(1, M1RescueMaxBars) &&
                                           enhanced >= rescueThreshold && evidencePass;
                        if (confirmationPass)
                        {
                            c.ConfirmationScore = enhanced;
                            _m1RescueAdmissions++;
                            Event(c, "M1_RESCUE_ADMITTED_" + enhanced.ToString("F2", CultureInfo.InvariantCulture));
                        }

                        if (!confirmationPass && EnableM1TemporalRescue &&
                            c.RescueBarsObserved <= Math.Max(1, M1RescueMaxBars))
                        {
                            double temporalScore;
                            if (UpdateM1TemporalEvidence(i, c, out temporalScore))
                            {
                                c.ConfirmationScore = Math.Max(c.ConfirmationScore, temporalScore);
                                confirmationPass = true;
                                _temporalRescueAdmissions++;
                                Event(c, "M1_TEMPORAL_RESCUE_ADMITTED_" + temporalScore.ToString("F2", CultureInfo.InvariantCulture));
                            }
                        }
                    }

                    if (!confirmationPass)
                    {
                        Event(c, "LEGACY_CONFIRMATION_FAILED_" + legacyScore.ToString("F2", CultureInfo.InvariantCulture));
                        continue;
                    }

                    if (EnableEntryAnchorForensics && c.NativeConfirmAnchorPrice <= 0)
                        c.NativeConfirmAnchorPrice = _m1Bars.ClosePrices[i];

                    if (EnableRouteSpecificM1Veto && !RouteSpecificM1EvidencePass(i, c.Signal, c.Route))
                    {
                        _confirmationRejected++;
                        Event(c, "ROUTE_SPECIFIC_M1_VETO");
                        continue;
                    }

                    if (!TryBuildFibonacciGridPlan(c))
                    {
                        Reject(c, "FIB_GRID_PLAN_REJECTED");
                        continue;
                    }
                    ConversionTruth(c.Signal.PatternName, "ECONOMIC_PLAN_PASS");

                    if (EnableExpansionEconomicGateV54 && !V54ExpansionEconomicAdmission(c))
                    {
                        ConversionTruth(c.Signal.PatternName, "EXPANSION_ECONOMIC_REJECT");
                        Reject(c, "EXPANSION_ECONOMIC_QUALITY");
                        continue;
                    }
                    ConversionTruth(c.Signal.PatternName, c.IsProvenCoreAlpha ? "CORE_ECONOMIC_PASS" : "EXPANSION_ECONOMIC_PASS");

                    c.Rank = CandidateRank(c);
                    _alphaPassed++;
                    c.ArmedUtc = utc;
                    if (EnableArmedExecutionGrace)
                    {
                        DateTime graceExpiry = utc.AddMinutes(Math.Max(15, ArmedGraceMinutes));
                        if (graceExpiry > c.ExpiryUtc)
                        {
                            c.ExpiryUtc = graceExpiry;
                            c.ArmedGraceApplied = true;
                            _armedGraceExtended++;
                        }
                    }
                    Transition(c, CandidateState.ARMED, "CONFIRMATION_PASSED_GRID_PREPLANNED");
                    CountPipeline(c.Signal.PatternName).Armed++;
                }
            }

            TryScheduleAndExecute();
        }

        private void TryScheduleAndExecute()
        {
            if (!TradingEnabled || _dailyLocked || PeakDrawdownExceeded()) return;
            if (!_initialCapitalEligible) return;
            DateTime now = Server.Time.ToUniversalTime();
            if (_evaluationStartUtc.HasValue && now < _evaluationStartUtc.Value) return;

            bool slotBusy = OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive);
            if (slotBusy)
            {
                if (EnablePersistentArmedQueue) ParkArmedCandidates(now);
                return;
            }

            if (!IsInstitutionalSession(now) || !SpreadValid())
            {
                if (EnablePersistentArmedQueue) SweepParkedHardValidity(now);
                return;
            }

            if (EnablePersistentArmedQueue)
                RevalidateParkedQueue(now);

            var executableStates = EnablePersistentArmedQueue
                ? new[] { CandidateState.ARMED, CandidateState.EXECUTABLE }
                : new[] { CandidateState.ARMED };

            var armedQuery = _candidates.Values
                .Where(c => executableStates.Contains(c.State) && c.IsActive && c.GridPlan != null &&
                            (!EnableCanonicalSetupIdentity || !_executedSetupKeys.Contains(c.SetupKey)));

            if (EnableDiversityScheduler)
                armedQuery = armedQuery.GroupBy(c => string.IsNullOrWhiteSpace(c.SetupKey) ? c.CandidateId : c.SetupKey)
                    .Select(g => g.OrderByDescending(c => V54ExecutionPriority(c, now)).First());

            var armed = armedQuery
                .OrderByDescending(c => V54ExecutionPriority(c, now))
                .ToList();
            if (armed.Count == 0) return;

            var winner = armed[0];

            if (EnablePreExecutionGridRevalidation || (EnablePersistentArmedQueue && winner.WasParked))
            {
                winner.GridPlan = null;
                Transition(winner, CandidateState.REVALIDATING, "PRE_EXECUTION_REVALIDATION");
                if (!RevalidateCandidateForExecution(winner, now, true))
                {
                    _preExecutionRevalidationRejected++;
                    _parkedRevalidationRejected += winner.WasParked ? 1 : 0;
                    CountPipeline(winner.Signal.PatternName).RevalidationRejected++;
                    MarkOpportunityTerminal(winner, "PRE_EXECUTION_REVALIDATION_FAILED");
                    Reject(winner, "PRE_EXECUTION_REVALIDATION_FAILED");
                    return;
                }
                CountPipeline(winner.Signal.PatternName).Revalidated++;
                Transition(winner, CandidateState.EXECUTABLE, "REVALIDATED_EXECUTABLE");
                winner.Rank = CandidateRank(winner);
            }

            ExecuteFibonacciGridPlan(winner);

            if (winner.State == CandidateState.EXECUTED)
            {
                ConversionTruth(winner.Signal.PatternName, "EXECUTED");
                if (winner.WasParked && winner.ParkedUtc.HasValue)
                {
                    double wait = Math.Max(0, (now - winner.ParkedUtc.Value).TotalMinutes);
                    _slotWaitMinutes.Add(wait);
                    _parkedRecoveredExecutions++;
                    Event(winner, "PARKED_RECOVERED_EXECUTION_WAIT_" + wait.ToString("F1", CultureInfo.InvariantCulture));
                }
                _parkedCandidateIds.Remove(winner.CandidateId);
                if (_deferredCandidates.Remove(winner.CandidateId))
                    _schedulerRecoveredExecutions++;

                foreach (var other in armed.Skip(1))
                {
                    if (EnablePersistentArmedQueue)
                    {
                        ParkCandidate(other, now, "SERIAL_SLOT_DEFERRED");
                    }
                    else if (EnableDeferredCandidateRetention)
                    {
                        if (_deferredCandidates.Add(other.CandidateId))
                            _schedulerDeferred++;
                        Event(other, "SCHEDULER_DEFERRED_KEEP_ALIVE");
                    }
                    else
                    {
                        Reject(other, "SINGLE_BASKET_SCHEDULER");
                    }
                }
            }
        }

        private void ParkArmedCandidates(DateTime now)
        {
            foreach (var c in _candidates.Values.Where(x => x.IsActive && x.State == CandidateState.ARMED).ToList())
                ParkCandidate(c, now, "SLOT_BLOCKED");
        }

        private void ParkCandidate(CandidateRecord c, DateTime now, string reason)
        {
            if (c == null || !c.IsActive || c.State == CandidateState.EXECUTED) return;
            if (!c.ParkedUtc.HasValue)
            {
                c.ParkedUtc = now;
                c.ParkedHardExpiryUtc = c.ArmedUtc.HasValue
                    ? c.ArmedUtc.Value.AddMinutes(Math.Max(180, ParkedHardLifetimeMinutes))
                    : now.AddMinutes(Math.Max(180, ParkedHardLifetimeMinutes));
                c.OriginalRank = c.Rank;
                c.OriginalGeometry = c.Signal.GeometryQuality;
                c.OriginalPrzConfluence = c.Signal.PrzConfluence;
                c.OriginalM1Evidence = c.ConfirmationScore;
                c.OriginalEntryAnchor = c.GridPlan != null ? c.GridPlan.EntryAnchor : (c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid);
                c.ShadowRiskDistance = Math.Max(Math.Abs(c.OriginalEntryAnchor - c.Signal.StructuralInvalidation), _symbol.PipSize);
                c.WasParked = true;
                _parkedCount++;
                CountPipeline(c.Signal.PatternName).Parked++;
            }
            _slotBlocked++;
            CountPipeline(c.Signal.PatternName).SlotBlocked++;
            c.GridPlan = null;
            _parkedCandidateIds.Add(c.CandidateId);
            Transition(c, CandidateState.SLOT_BLOCKED, reason);
            Transition(c, CandidateState.PARKED, "PARKED_NO_BROKER_ORDER_NO_RESERVED_RISK");
        }

        private void SweepParkedHardValidity(DateTime now)
        {
            foreach (var c in _candidates.Values.Where(x => x.IsActive && (x.State == CandidateState.PARKED || x.State == CandidateState.SLOT_BLOCKED)).ToList())
            {
                if (!HardThesisValid(c, now, false, out string reason))
                {
                    MarkOpportunityTerminal(c, reason);
                    if (reason == "STRUCTURAL_INVALIDATION" || reason == "MTF_HARD_CONFLICT") Invalidate(c, reason);
                    else Expire(c, reason);
                }
            }
        }

        private void RevalidateParkedQueue(DateTime now)
        {
            foreach (var c in _candidates.Values
                .Where(x => x.IsActive && (x.State == CandidateState.PARKED || x.State == CandidateState.SLOT_BLOCKED))
                .OrderByDescending(x => EnableOpportunityDecayRanking ? OpportunityScore(x, now) : x.Rank)
                .ToList())
            {
                Transition(c, CandidateState.REVALIDATING, "SLOT_RELEASE_REVALIDATION");
                if (!RevalidateCandidateForExecution(c, now, false))
                {
                    _parkedRevalidationRejected++;
                    CountPipeline(c.Signal.PatternName).RevalidationRejected++;
                    MarkOpportunityTerminal(c, "PARKED_REVALIDATION_REJECTED");
                    Reject(c, "PARKED_REVALIDATION_REJECTED");
                    continue;
                }
                _parkedRevalidated++;
                CountPipeline(c.Signal.PatternName).Revalidated++;
                c.Rank = CandidateRank(c);
                Transition(c, CandidateState.EXECUTABLE, "PARKED_REVALIDATED");
            }
        }

        private bool RevalidateCandidateForExecution(CandidateRecord c, DateTime now, bool finalCheck)
        {
            if (!HardThesisValid(c, now, true, out string reason))
            {
                Event(c, "REVALIDATION_HARD_FAIL_" + reason);
                return false;
            }
            c.GridPlan = null;
            if (!TryBuildFibonacciGridPlan(c)) return false;
            if (c.NetRR < MinimumNetRR) return false;
            if (c.GridPlan == null || c.GridPlan.WorstCaseRisk > c.GridPlan.BasketRiskAmount + 1e-8) return false;
            if (Account.FreeMargin < c.GridPlan.BasketRiskAmount * MinFreeMarginRiskMultiple) return false;
            if (finalCheck && !SpreadValid()) return false;
            return true;
        }

        private bool HardThesisValid(CandidateRecord c, DateTime now, bool requireTradableSession, out string reason)
        {
            reason = "";
            if (c == null || c.Signal == null || !c.IsActive) { reason = "INACTIVE"; return false; }
            if (EnableCanonicalSetupIdentity && _executedSetupKeys.Contains(c.SetupKey)) { reason = "SETUP_ALREADY_EXECUTED"; return false; }
            if (c.ParkedHardExpiryUtc.HasValue && now >= c.ParkedHardExpiryUtc.Value) { reason = "HARD_LIFETIME_EXPIRED"; return false; }
            if (requireTradableSession && !IsInstitutionalSession(now)) { reason = "SESSION_EXPIRED"; return false; }
            if (PatternInvalidatedBeforeEntry(c.Signal)) { reason = "STRUCTURAL_INVALIDATION"; return false; }
            double px = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            if (c.Signal.Direction == TradeDirection.Buy && px >= c.Signal.CanonicalTarget1) { reason = "TARGET_ALREADY_REACHED"; return false; }
            if (c.Signal.Direction == TradeDirection.Sell && px <= c.Signal.CanonicalTarget1) { reason = "TARGET_ALREADY_REACHED"; return false; }
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            if (ClassifyMtfConflict(c.Signal.Direction, h4, h1) == MtfConflict.CONFLICT &&
                c.Route != HarmonicRoute.EXHAUSTION_REVERSAL) { reason = "MTF_HARD_CONFLICT"; return false; }
            if (_dailyLocked || PeakDrawdownExceeded()) { reason = "RISK_LOCK"; return false; }
            if (!SpreadValid()) { reason = "SPREAD_INVALID"; return false; }
            return true;
        }

        private void UpdateEntryAnchorForensics(CandidateRecord c, int i)
        {
            if (c == null || c.Signal == null || i < 0 || i >= _m1Bars.Count) return;
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.CompletionAnchorPrice, i, ref c.CompletionAnchorMfeR, ref c.CompletionAnchorMaeR);
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.NativeConfirmAnchorPrice, i, ref c.NativeConfirmMfeR, ref c.NativeConfirmMaeR);
            UpdateAnchorExcursion(c.Signal.Direction, c.Signal.StructuralInvalidation, c.NativeRetestAnchorPrice, i, ref c.NativeRetestMfeR, ref c.NativeRetestMaeR);
        }

        private void UpdateAnchorExcursion(TradeDirection direction, double stop, double anchor, int i, ref double mfeR, ref double maeR)
        {
            if (anchor <= 0) return;
            double risk = Math.Abs(anchor - stop);
            if (risk <= _symbol.PipSize) return;
            double fav, adv;
            if (direction == TradeDirection.Buy)
            {
                fav = (_m1Bars.HighPrices[i] - anchor) / risk;
                adv = (anchor - _m1Bars.LowPrices[i]) / risk;
            }
            else
            {
                fav = (anchor - _m1Bars.LowPrices[i]) / risk;
                adv = (_m1Bars.HighPrices[i] - anchor) / risk;
            }
            mfeR = Math.Max(mfeR, fav);
            maeR = Math.Max(maeR, adv);
        }

        private double OpportunityScore(CandidateRecord c, DateTime now)
        {
            if (c == null || c.Signal == null) return -999;
            double conservativeAlpha = VClamp(.35 * c.AlphaQualityScore + .25 * c.Signal.GeometryQuality +
                                              .20 * c.Signal.PrzConfluence + .20 * c.ConfirmationScore);
            double remainingRr = VClamp(c.NetRR / 3.0);
            double ageMin = c.ParkedUtc.HasValue ? Math.Max(0, (now - c.ParkedUtc.Value).TotalMinutes) : 0;
            double freshness = Math.Exp(-ageMin / 120.0);
            double evidence = VClamp(c.ConfirmationScore);
            double routeReliability = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? .88 :
                                      c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? .90 : .82;
            double expectedSlotMinutes = c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 90.0 :
                                         c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 120.0 : 75.0;
            double drift = c.OriginalEntryAnchor > 0 ? Math.Abs((c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - c.OriginalEntryAnchor) /
                           Math.Max(c.ShadowRiskDistance, _symbol.PipSize) : 0;
            double priceDriftPenalty = Math.Min(.35, drift * .18);
            double thesisAgePenalty = Math.Min(.30, ageMin / Math.Max(180.0, ParkedHardLifetimeMinutes) * .30);
            double structuralDistancePenalty = Math.Min(.25, Math.Abs((c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - c.Signal.D.Price) /
                                                     Math.Max(c.ShadowRiskDistance, _symbol.PipSize) * .10);
            double spreadPenalty = Math.Min(.20, CurrentSpreadPips() / Math.Max(1.0, MaxSpreadPips) * .20);
            double marginBurdenPenalty = Account.FreeMargin > 0 && c.GridPlan != null
                ? Math.Min(.20, c.GridPlan.EstimatedPhysicalMargin / Math.Max(Account.FreeMargin, 1.0) * .20) : 0;
            double density = conservativeAlpha * Math.Max(.10, remainingRr) * Math.Max(.10, freshness) *
                             Math.Max(.10, evidence) * routeReliability / Math.Max(1.0, expectedSlotMinutes / 60.0);
            return density - priceDriftPenalty - thesisAgePenalty - structuralDistancePenalty - spreadPenalty - marginBurdenPenalty;
        }

        private void UpdateOpportunityShadow(CandidateRecord c, int i)
        {
            if (c == null || !c.WasParked || c.ShadowRiskDistance <= 0 || i < 0 || i >= _m1Bars.Count) return;
            double fav, adv;
            if (c.Signal.Direction == TradeDirection.Buy)
            {
                fav = (_m1Bars.HighPrices[i] - c.OriginalEntryAnchor) / c.ShadowRiskDistance;
                adv = (c.OriginalEntryAnchor - _m1Bars.LowPrices[i]) / c.ShadowRiskDistance;
            }
            else
            {
                fav = (c.OriginalEntryAnchor - _m1Bars.LowPrices[i]) / c.ShadowRiskDistance;
                adv = (_m1Bars.HighPrices[i] - c.OriginalEntryAnchor) / c.ShadowRiskDistance;
            }
            c.ShadowMfeR = Math.Max(c.ShadowMfeR, fav);
            c.ShadowMaeR = Math.Max(c.ShadowMaeR, adv);
        }

        private void MarkOpportunityTerminal(CandidateRecord c, string reason)
        {
            if (c == null || !c.WasParked || c.OpportunityTerminalLogged) return;
            c.OpportunityTerminalLogged = true;
            bool missedPositive = c.ShadowMfeR >= 1.0 && c.ShadowMfeR > c.ShadowMaeR;
            bool avoidedNegative = c.ShadowMaeR >= 1.0 && c.ShadowMaeR > c.ShadowMfeR;
            if (missedPositive) _missedPositiveSetups++;
            if (avoidedNegative) _avoidedNegativeSetups++;
            Print("[V54-OPPORTUNITY-LOSS] cid={0} setup={1} pattern={2} route={3} scale={4} reason={5} shadowMfeR={6:F3} shadowMaeR={7:F3} missedPositive={8} avoidedNegative={9}",
                c.CandidateId, c.SetupKey, c.Signal.PatternName, c.Route, c.Signal.PivotScale, reason,
                c.ShadowMfeR, c.ShadowMaeR, missedPositive, avoidedNegative);
        }

        private double Percentile(List<double> values, double p)
        {
            if (values == null || values.Count == 0) return 0;
            var x = values.OrderBy(v => v).ToList();
            double pos = (x.Count - 1) * VClamp(p);
            int lo = (int)Math.Floor(pos), hi = (int)Math.Ceiling(pos);
            if (lo == hi) return x[lo];
            return x[lo] + (x[hi] - x[lo]) * (pos - lo);
        }

        private bool GridPlanReject(CandidateRecord c, string reason)
        {
            if (string.IsNullOrWhiteSpace(reason)) reason = "UNKNOWN";
            int n; _gridPlanRejectReasons.TryGetValue(reason, out n); _gridPlanRejectReasons[reason] = n + 1;
            if (c != null)
            {
                Event(c, "GRID_PLAN_REJECT_" + reason);
                if (c.Signal != null) ConversionTruth(c.Signal.PatternName, "ECONOMIC_PLAN_REJECT_" + reason);
            }
            return false;
        }

        private bool TryBuildFibonacciGridPlan(CandidateRecord c)
        {
            var p = c.Signal.Profile;
            if (p == null || !p.GridEnabled) return GridPlanReject(c, "PROFILE_DISABLED");
            if (!_initialCapitalEligible) return GridPlanReject(c, "INITIAL_CAPITAL");

            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double distance = c.Signal.Direction == TradeDirection.Buy ? anchor - stop : stop - anchor;
            if (distance <= PipsToPrice(MinStopLossPips)) return GridPlanReject(c, "STOP_DISTANCE");

            double xa = Math.Abs(c.Signal.A.Price - c.Signal.X.Price);
            double spanXa = xa > 0 ? distance / xa : 999;
            double executionUnit = distance;
            if (EnableFamilyNativeExecutionCorridor)
            {
                executionUnit = Math.Abs(c.Signal.D.Price - stop);
                if (!double.IsFinite(executionUnit) || executionUnit <= PipsToPrice(MinStopLossPips))
                    return GridPlanReject(c, "INVALID_NATIVE_EXECUTION_CORRIDOR");
            }
            if (!EnableGridSpanSemanticV2 && (spanXa < p.MinimumGridSpanXa || spanXa > p.MaximumGridSpanXa)) return GridPlanReject(c, "LEGACY_XA_SPAN");
            if (EnableGridSpanSemanticV2 && (!double.IsFinite(spanXa) || spanXa <= 0)) return GridPlanReject(c, "INVALID_RISK_XA");

            int routeMax = !EnableFibonacciGridExecution ? 1 :
                           c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 4 :
                           c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 2 :
                           c.Route == HarmonicRoute.TRANSITION_REVERSAL ? (c.Regime != null && c.Regime.Efficiency >= .28 ? 3 : 2) : 0;
            if (EnableFamilyGridAllocationV54)
                routeMax = V54GridMaxLegs(c.Signal.PatternName, routeMax, p.MaximumGridLegs);
            int maxLegs = Math.Min(Math.Min(routeMax, p.MaximumGridLegs), p.GridFractions.Length);
            if (maxLegs <= 0) return GridPlanReject(c, "ROUTE_LEGS");

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = executionUnit,
                BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = MinDate(c.ExpiryUtc, Server.Time.ToUniversalTime().AddMinutes(p.PendingTtlMinutes)),
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold
            };
            if (plan.BasketRiskAmount <= 0) return GridPlanReject(c, "RISK_BUDGET");

            double przTol = Math.Max(c.Signal.PrzHigh - c.Signal.PrzLow, executionUnit * p.GridStructuralTolerance);
            double legalLow = c.Signal.PrzLow - przTol;
            double legalHigh = c.Signal.PrzHigh + przTol;

            for (int leg = 0; leg < maxLegs; leg++)
            {
                double fraction = p.GridFractions[leg];
                if (fraction < -1e-9 || fraction > .6180001) continue;
                double price = c.Signal.Direction == TradeDirection.Buy ? anchor - fraction * executionUnit : anchor + fraction * executionUnit;
                if (price < legalLow || price > legalHigh) continue;

                double riskWeight = !EnableFibonacciGridExecution ? 1.0 :
                                    EnableFamilyGridAllocationV54 ? V54GridRiskWeight(c.Signal.PatternName, leg, maxLegs) :
                                    (leg < p.GridRiskWeights.Length ? p.GridRiskWeights[leg] : 0);
                double slPips = PriceToPips(Math.Abs(price - stop));
                if (slPips < MinStopLossPips || riskWeight <= 0) continue;

                double minVolume = _symbol.VolumeInUnitsMin;
                double minRisk = minVolume * _symbol.PipValue * (slPips + ModeledCostPips());
                plan.Legs.Add(new FibonacciGridLeg
                {
                    Index = leg,
                    Fraction = fraction,
                    PlannedPrice = price,
                    RiskWeight = riskWeight,
                    RiskBudget = plan.BasketRiskAmount * riskWeight,
                    MinBrokerRisk = minRisk,
                    Volume = 0,
                    PlannedRisk = 0,
                    ModeledCost = 0,
                    Physical = false,
                    State = GridLegState.VIRTUAL_ONLY
                });
            }

            if (plan.Legs.Count == 0 || plan.Legs[0].Index != 0) return GridPlanReject(c, "NO_LEGAL_L0_IN_PRZ");
            plan.LogicalLegCount = plan.Legs.Count;

            if (!ConfigureCapitalExecution(plan))
            {
                _capitalRejectedBaskets++;
                return GridPlanReject(c, "CAPITAL_EXECUTION");
            }

            var physical = plan.Legs.Where(x => x.Physical && x.Volume > 0).ToList();
            if (physical.Count == 0 || physical[0].Index != 0) return GridPlanReject(c, "NO_PHYSICAL_L0");

            double totalVolume = physical.Sum(l => l.Volume);
            plan.ExpectedWeightedEntry = physical.Sum(l => l.PlannedPrice * l.Volume) / totalVolume;

            double virtualDen = plan.Legs.Sum(l => l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9));
            plan.VirtualWeightedEntry = virtualDen > 0
                ? plan.Legs.Sum(l => l.PlannedPrice * (l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9))) / virtualDen
                : plan.ExpectedWeightedEntry;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(c.Signal, plan.ExpectedWeightedEntry, plan.StructuralStop, out target, out netRr))
                return GridPlanReject(c, "TARGET_RR");

            plan.CanonicalTarget = target;
            plan.ExpectedNetRR = netRr;
            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = netRr;

            Print("[V54-GRID-PLAN] cid={0} pattern={1} route={2} logicalLegs={3} physicalDepth={4} micro={5} anchor={6} weighted={7} virtualWeighted={8} stop={9} target={10} budget={11:F2} worst={12:F2} margin={13:F2} netRR={14:F3}",
                c.CandidateId, c.Signal.PatternName, c.Route, plan.LogicalLegCount, plan.PhysicalDepth, plan.MicroCapitalMode,
                anchor, plan.ExpectedWeightedEntry, plan.VirtualWeightedEntry, stop, target, plan.BasketRiskAmount,
                plan.WorstCaseRisk, plan.EstimatedPhysicalMargin, plan.ExpectedNetRR);
            foreach (var leg in plan.Legs)
                Print("[V54-GRID-LEG-PLAN] cid={0} leg=L{1} fraction={2:F3} price={3} weight={4:F6} physical={5} volume={6} budget={7:F2} risk={8:F2} minBrokerRisk={9:F2} state={10}",
                    c.CandidateId, leg.Index, leg.Fraction, leg.PlannedPrice, leg.RiskWeight, leg.Physical, leg.Volume,
                    leg.RiskBudget, leg.PlannedRisk, leg.MinBrokerRisk, leg.State);

            PrintCapitalCompatibilityMatrix(plan);
            return true;
        }

        private bool ConfigureCapitalExecution(FibonacciGridPlan plan)
        {
            foreach (var l in plan.Legs)
            {
                l.Physical = false;
                l.Volume = 0;
                l.PlannedRisk = 0;
                l.ModeledCost = 0;
                l.State = GridLegState.VIRTUAL_ONLY;
            }

            if (plan.MicroCapitalMode)
            {
                for (int depth = plan.Legs.Count; depth >= 1; depth--)
                {
                    var prefix = plan.Legs.Take(depth).ToList();
                    double weightSum = prefix.Sum(x => x.RiskWeight);
                    if (weightSum <= 0) continue;
                    double worst = 0, margin = 0;
                    var vols = new Dictionary<int, double>();
                    bool feasible = true;

                    foreach (var l in prefix)
                    {
                        double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                        double budget = plan.BasketRiskAmount * l.RiskWeight / weightSum;
                        double volume = !EnableFibonacciGridExecution
                            ? VolumeForRiskBudgetIncludingCost(budget, slPips)
                            : VolumeForRiskBudget(budget, slPips);
                        if (volume <= 0) { feasible = false; break; }

                        double risk = volume * _symbol.PipValue * slPips;
                        double cost = volume * _symbol.PipValue * ModeledCostPips();
                        worst += risk + cost;
                        margin += EstimatedMargin(plan.Direction, volume);
                        vols[l.Index] = volume;
                    }

                    if (!feasible || worst > plan.BasketRiskAmount + 1e-8) continue;
                    if (Account.FreeMargin - margin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) continue;

                    foreach (var l in prefix)
                    {
                        double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                        l.RiskBudget = plan.BasketRiskAmount * l.RiskWeight / weightSum;
                        l.Volume = vols[l.Index];
                        l.PlannedRisk = l.Volume * _symbol.PipValue * slPips;
                        l.ModeledCost = l.Volume * _symbol.PipValue * ModeledCostPips();
                        l.Physical = true;
                        l.State = GridLegState.PLANNED;
                    }
                    plan.PhysicalDepth = depth;
                    plan.WorstCaseRisk = worst;
                    plan.EstimatedPhysicalMargin = margin;
                    _microModeBaskets++;
                    return true;
                }
                return false;
            }

            double cumulative = 0, totalMargin = 0;
            int physicalDepth = 0;
            foreach (var l in plan.Legs)
            {
                double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                l.RiskBudget = plan.BasketRiskAmount * l.RiskWeight;
                double volume = !EnableFibonacciGridExecution
                    ? VolumeForRiskBudgetIncludingCost(l.RiskBudget, slPips)
                    : VolumeForRiskBudget(l.RiskBudget, slPips);
                if (volume <= 0) continue;

                double risk = volume * _symbol.PipValue * slPips;
                double cost = volume * _symbol.PipValue * ModeledCostPips();
                if (cumulative + risk + cost > plan.BasketRiskAmount + 1e-8) continue;

                l.Volume = volume;
                l.PlannedRisk = risk;
                l.ModeledCost = cost;
                l.Physical = true;
                l.State = GridLegState.PLANNED;
                cumulative += risk + cost;
                totalMargin += EstimatedMargin(plan.Direction, volume);
                if (l.Index == physicalDepth) physicalDepth++;
            }

            plan.PhysicalDepth = physicalDepth;
            plan.WorstCaseRisk = cumulative;
            plan.EstimatedPhysicalMargin = totalMargin;
            return plan.Legs[0].Physical && plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8 &&
                   Account.FreeMargin - totalMargin >= plan.BasketRiskAmount * MinFreeMarginRiskMultiple;
        }

        private double EstimatedMargin(TradeDirection direction, double volume)
        {
            try
            {
                return _symbol.GetEstimatedMargin(direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell, volume);
            }
            catch { return 0; }
        }

        private int EstimateRiskOnlyPhysicalDepth(FibonacciGridPlan plan, double equity)
        {
            double budget = equity * BasketRiskPercent / 100.0;
            if (budget <= 0) return 0;
            for (int depth = plan.Legs.Count; depth >= 1; depth--)
            {
                var prefix = plan.Legs.Take(depth).ToList();
                double ws = prefix.Sum(x => x.RiskWeight);
                if (ws <= 0) continue;
                double worst = 0;
                bool ok = true;
                foreach (var l in prefix)
                {
                    double slPips = PriceToPips(Math.Abs(l.PlannedPrice - plan.StructuralStop));
                    double legBudget = budget * l.RiskWeight / ws;
                    double v = VolumeForRiskBudget(legBudget, slPips);
                    if (v <= 0) { ok = false; break; }
                    worst += v * _symbol.PipValue * (slPips + ModeledCostPips());
                }
                if (ok && worst <= budget + 1e-8) return depth;
            }
            return 0;
        }

        private void PrintCapitalCompatibilityMatrix(FibonacciGridPlan plan)
        {
            double[] equities = { 100, 150, 200, 300, 500, 1000 };
            string matrix = string.Join(",", equities.Select(e =>
                e.ToString("F0", CultureInfo.InvariantCulture) + ":" + EstimateRiskOnlyPhysicalDepth(plan, e)));
            Print("[V54-CAPITAL-COMPAT] cid={0} logicalLegs={1} riskOnlyPhysicalDepths={2}", plan.CandidateId, plan.LogicalLegCount, matrix);
        }

        private void ExecuteFibonacciGridPlan(CandidateRecord c)
        {
            var plan = c.GridPlan;
            if (plan == null || plan.Legs.Count == 0) { Reject(c, "GRID_PLAN_MISSING"); return; }
            if (Account.FreeMargin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) { Reject(c, "MARGIN_HEADROOM"); return; }
            if (plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8)
            {
                _gridRiskViolations++;
                Reject(c, "WORST_CASE_BASKET_RISK");
                return;
            }

            string basketId = NewBasketId();
            plan.BasketId = basketId;
            var basket = new FibonacciBasket
            {
                BasketId = basketId,
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                State = FibonacciBasketState.PLANNED,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = plan.ExpirationUtc,
                EntryAnchor = plan.EntryAnchor,
                StructuralStop = plan.StructuralStop,
                CanonicalTarget = plan.CanonicalTarget,
                InitialBasketRisk = plan.BasketRiskAmount,
                PlannedWorstCaseRisk = plan.WorstCaseRisk,
                ProtectionFrontier = plan.StructuralStop,
                Plan = plan,
                Candidate = c,
                IsActive = true
            };
            _baskets[basketId] = basket;
            CountPipeline(c.Signal.PatternName).BasketPlanned++;
            BasketEvent(basket, "BASKET_PLANNED");

            var l0 = plan.Legs.First(x => x.Index == 0);
            string l0Label = GridLabel(basketId, 0);
            if (LegAlreadyExists(l0Label))
            {
                _duplicateGridLegs++;
                basket.State = FibonacciBasketState.CANCELLED;
                basket.IsActive = false;
                Reject(c, "DUPLICATE_L0");
                return;
            }

            double marketEntry = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double slPips = PriceToPips(Math.Abs(marketEntry - plan.StructuralStop));
            double tpPips = PriceToPips(Math.Abs(plan.CanonicalTarget - marketEntry));
            if (!BrokerProtectionDistancesValid(c.Signal.Direction, marketEntry, plan.StructuralStop, plan.CanonicalTarget))
            {
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_BROKER_MIN_DISTANCE");
                return;
            }

            double volume = !EnableFibonacciGridExecution
                ? VolumeForRiskBudgetIncludingCost(l0.RiskBudget, slPips)
                : VolumeForRiskBudget(l0.RiskBudget, slPips);
            if (volume <= 0)
            {
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_RISK_VOLUME");
                return;
            }

            double otherWorst = plan.Legs.Where(x => x.Index != 0 && x.Physical).Sum(x => x.PlannedRisk + x.ModeledCost);
            double l0Worst = volume * _symbol.PipValue * (slPips + ModeledCostPips());
            if (otherWorst + l0Worst > plan.BasketRiskAmount + 1e-8)
            {
                _gridRiskViolations++;
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, "L0_SLIPPAGE_RISK_RECHECK");
                return;
            }

            TransitionLegState(basket, l0, GridLegState.SUBMITTING, "L0_SUBMITTING");
            TradeType tt = c.Signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            var tr = ExecuteMarketOrder(tt, SymbolName, volume, l0Label, slPips, tpPips);
            if (tr == null || !tr.IsSuccessful || tr.Position == null)
            {
                string code = "L0_ORDER_" + (tr == null ? "NULL" : tr.Error.ToString());
                RecordExecutionError(code, "basket=" + basket.BasketId);
                basket.State = FibonacciBasketState.RISK_REJECTED;
                basket.IsActive = false;
                Reject(c, code);
                return;
            }

            l0.Volume = volume;
            l0.PositionId = tr.Position.Id;
            if (!PositionStillExists(tr.Position.Id))
            {
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            if (!_postFillValidated.Contains(tr.Position.Id))
                PostFillSafetyKernel(tr.Position, "L0_RESULT");
            if (!_postFillValidated.Contains(tr.Position.Id))
            {
                basket.ExitOverride = "L0_POST_FILL_NOT_VALIDATED";
                CancelBasketPending(basket, basket.ExitOverride);
                if (PositionStillExists(tr.Position.Id))
                    FailClosePosition(tr.Position, basket, basket.ExitOverride);
                if (PositionStillExists(tr.Position.Id))
                    _unprotectedSurvivors++;
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            if (!PositionStillExists(tr.Position.Id))
            {
                basket.State = FibonacciBasketState.INVALIDATED;
                basket.IsActive = false;
                Invalidate(c, "L0_FAIL_CLOSED_POST_FILL");
                return;
            }
            basket.State = FibonacciBasketState.LEG0_EXECUTED;
            if (!_positions.ContainsKey(tr.Position.Id)) RegisterFilledPosition(basket, l0, tr.Position);
            RecordLegFillTelemetry(basket, l0);
            CountPipeline(c.Signal.PatternName).Leg0Executed++;
            BasketEvent(basket, "LEG0_EXECUTED");
            Transition(c, CandidateState.EXECUTED, "FIB_GRID_LEG0_FILLED");
            if (EnableCanonicalSetupIdentity && !string.IsNullOrWhiteSpace(c.SetupKey))
            {
                _executedSetupKeys.Add(c.SetupKey);
                _activeSetupOwners.Remove(string.IsNullOrWhiteSpace(c.IdentityKey) ? c.SetupKey : c.IdentityKey);
                foreach (var other in _candidates.Values.Where(x => x.CandidateId != c.CandidateId && x.IsActive && x.SetupKey == c.SetupKey).ToList())
                    Reject(other, "UNDERLYING_GEOMETRY_EXECUTED_BY_" + c.Signal.PatternName);
            }
            CountPipeline(c.Signal.PatternName).Executed++;

            foreach (var leg in plan.Legs.Where(x => x.Index > 0))
            {
                if (!leg.Physical) continue;
                if (!DeeperLegThesisEligible(basket, leg))
                {
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "DEEPER_LEG_THESIS_REJECT");
                    continue;
                }
                if (PlaceGridLimit(basket, leg))
                    basket.State = FibonacciBasketState.GRID_PENDING;
            }
        }

        private bool PlaceGridLimit(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (!leg.Physical || leg.Volume <= 0) return false;
            string label = GridLabel(basket.BasketId, leg.Index);
            if (LegAlreadyExists(label))
            {
                _duplicateGridLegs++;
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_DUPLICATE");
                BasketEvent(basket, "GRID_LEG_DUPLICATE_L" + leg.Index);
                return false;
            }

            if ((basket.Direction == TradeDirection.Buy && leg.PlannedPrice >= _symbol.Ask) ||
                (basket.Direction == TradeDirection.Sell && leg.PlannedPrice <= _symbol.Bid))
            {
                TransitionLegState(basket, leg, GridLegState.CANCELLED, "GRID_LEG_PRICE_CROSSED_BEFORE_SUBMIT");
                BasketEvent(basket, "GRID_LEG_PRICE_CROSSED_BEFORE_SUBMIT_L" + leg.Index);
                return false;
            }

            double slPips = PriceToPips(Math.Abs(leg.PlannedPrice - basket.StructuralStop));
            double tpPips = PriceToPips(Math.Abs(basket.CanonicalTarget - leg.PlannedPrice));
            if (slPips < MinStopLossPips || tpPips <= 0)
            {
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_GEOMETRY_REJECT");
                BasketEvent(basket, "GRID_LEG_GEOMETRY_REJECT_L" + leg.Index);
                return false;
            }

            if (!BrokerProtectionDistancesValid(basket.Direction, leg.PlannedPrice, basket.StructuralStop, basket.CanonicalTarget))
            {
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_BROKER_MIN_DISTANCE");
                BasketEvent(basket, "GRID_LEG_BROKER_MIN_DISTANCE_L" + leg.Index);
                return false;
            }

            double liveFilledRisk = CurrentFilledStructuralRisk(basket);
            double livePendingRisk = CurrentPendingStructuralRisk(basket);
            double nextWorst = liveFilledRisk + livePendingRisk + leg.PlannedRisk + leg.ModeledCost;
            if (nextWorst > basket.InitialBasketRisk + 1e-8)
            {
                TransitionLegState(basket, leg, GridLegState.RISK_REJECTED, "LIVE_FILLED_RISK_REJECT");
                BasketEvent(basket, "LIVE_FILLED_RISK_REJECT_L" + leg.Index);
                return false;
            }

            DateTime nowUtc = Server.Time.ToUniversalTime();
            if (basket.ExpirationUtc <= nowUtc.AddSeconds(1))
            {
                TransitionLegState(basket, leg, GridLegState.EXPIRED, "PENDING_TTL_NOT_STRICTLY_FUTURE");
                return false;
            }

            TransitionLegState(basket, leg, GridLegState.SUBMITTING, "LIMIT_SUBMITTING");
            TradeType tt = basket.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            var tr = PlaceLimitOrder(tt, SymbolName, leg.Volume, leg.PlannedPrice, label,
                basket.StructuralStop, basket.CanonicalTarget, ProtectionType.Absolute, basket.ExpirationUtc,
                GridComment(basket, leg.Index), false);
            if (tr == null || !tr.IsSuccessful || tr.PendingOrder == null)
            {
                string code = "GRID_LEG_ORDER_" + (tr == null ? "NULL" : tr.Error.ToString());
                RecordExecutionError(code, "basket=" + basket.BasketId + ";leg=L" + leg.Index);
                TransitionLegState(basket, leg, GridLegState.REJECTED, "GRID_LEG_SUBMIT_FAILED_" + code);
                BasketEvent(basket, "GRID_LEG_SUBMIT_FAILED_L" + leg.Index + "_" + code);
                return false;
            }

            leg.PendingOrderId = tr.PendingOrder.Id;
            if (leg.State == GridLegState.SUBMITTING)
                TransitionLegState(basket, leg, GridLegState.SUBMITTED, "GRID_LEG_SUBMITTED");
            else
                BasketEvent(basket, "LIMIT_SUBMIT_RETURN_AFTER_EVENT_L" + leg.Index + "_STATE_" + leg.State);
            return leg.State == GridLegState.SUBMITTED || leg.State == GridLegState.FILLED_UNVERIFIED || leg.State == GridLegState.PROTECTED;
        }

        private bool SelectCanonicalBasketTarget(PatternSignal s, double weightedEntry, double stop, out double target, out double netRr)
        {
            target = 0; netRr = 0;
            double riskPips = PriceToPips(Math.Abs(weightedEntry - stop));
            if (riskPips < MinStopLossPips) return false;

            double[] targets = s.Profile != null && s.Profile.CanonicalTargetPolicy == "T2_PREFERRED"
                ? new[] { s.CanonicalTarget2, s.CanonicalTarget1 }
                : new[] { s.CanonicalTarget1, s.CanonicalTarget2 };

            foreach (double t in targets)
            {
                if (!GeometryValid(s.Direction, weightedEntry, stop, t)) continue;
                double rewardPips = PriceToPips(Math.Abs(t - weightedEntry)) - ModeledCostPips();
                double rr = riskPips > 0 ? rewardPips / riskPips : 0;
                if (rr >= MinimumNetRR)
                {
                    target = t;
                    netRr = rr;
                    return true;
                }
            }
            return false;
        }

        private double VolumeForRiskBudget(double riskBudget, double slPips)
        {
            if (riskBudget <= 0 || slPips <= 0 || _symbol.PipValue <= 0) return 0;
            double raw = riskBudget / (slPips * _symbol.PipValue);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;
            double v = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (v < _symbol.VolumeInUnitsMin) return 0;
            return Math.Min(v, _symbol.VolumeInUnitsMax);
        }

        private double VolumeForRiskBudgetIncludingCost(double riskBudget, double slPips)
        {
            double totalRiskPips = slPips + ModeledCostPips();
            if (riskBudget <= 0 || totalRiskPips <= 0 || _symbol.PipValue <= 0) return 0;
            double raw = riskBudget / (totalRiskPips * _symbol.PipValue);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;
            double v = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (v < _symbol.VolumeInUnitsMin) return 0;
            return Math.Min(v, _symbol.VolumeInUnitsMax);
        }

        private double ModeledCostPips()
        {
            return Math.Max(0, SpreadPips()) + Math.Max(0, RoundTurnCommissionPips) + Math.Max(0, SlippageStressPips);
        }

        private void ReconcileAndManageBaskets()
        {
            ReconcileGridFills();
            CancelInvalidPendingOrders();
            RevalidatePendingExposureGovernor();

            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                UpdateVirtualGridState(basket);
                var positions = OwnPositions().Where(p => LabelBasketId(p.Label) == basket.BasketId).ToList();
                var pending = OwnPendingOrders().Where(o => LabelBasketId(o.Label) == basket.BasketId).ToList();

                if (positions.Count == 0)
                {
                    if (pending.Count == 0 && basket.State != FibonacciBasketState.PLANNED)
                        CloseBasketLedger(basket, "NO_OPEN_LEGS");
                    continue;
                }

                basket.State = pending.Count > 0 ? FibonacciBasketState.PARTIALLY_FILLED : FibonacciBasketState.BASKET_ACTIVE;
                basket.FilledLegs = Math.Max(basket.FilledLegs, positions.Count);
                basket.AverageEntry = WeightedAverageEntry(positions);

                foreach (var p in positions)
                {
                    PositionLedger legLedger;
                    if (!_positions.TryGetValue(p.Id, out legLedger) || legLedger.InitialRiskPips <= 0) continue;
                    double legR = p.Pips / legLedger.InitialRiskPips;
                    if (legR > legLedger.PeakR) legLedger.PeakR = legR;
                    if (-legR > legLedger.MaxAdverseR) legLedger.MaxAdverseR = -legR;
                }

                double currentNet = positions.Sum(p => p.NetProfit);
                double currentR = basket.InitialBasketRisk > 0 ? (basket.RealizedNet + currentNet) / basket.InitialBasketRisk : 0;
                if (currentR > basket.PeakR) basket.PeakR = currentR;
                if (-currentR > basket.MaxAdverseR) basket.MaxAdverseR = -currentR;

                double gridCancelThreshold = EnableGridStateAwareV54 ? V54GridCancelMfeThreshold(basket) : GridCancelMfeR;
                if (basket.PeakR >= gridCancelThreshold && pending.Count > 0)
                    CancelBasketPending(basket, "MFE_GRID_CANCEL");

                double age = (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes;
                if (age >= NoMfeMinAgeMinutes && basket.PeakR < NoMfeProofR && currentR <= -Math.Abs(NoMfeKillR))
                {
                    basket.ExitOverride = "NO_MFE_THESIS_FAILURE";
                    CancelBasketPending(basket, basket.ExitOverride);
                    CloseBasketPositions(basket, basket.ExitOverride);
                    continue;
                }

                if (basket.PeakR >= BreakEvenTriggerR)
                {
                    double span = Math.Abs(basket.AverageEntry - basket.StructuralStop);
                    double lockPrice = basket.Direction == TradeDirection.Buy
                        ? basket.AverageEntry + span * Math.Max(0, BreakEvenLockR)
                        : basket.AverageEntry - span * Math.Max(0, BreakEvenLockR);
                    AdvanceBasketProtectionFrontier(basket, lockPrice, "COLLECTIVE_PROTECT");
                }

                if (basket.PeakR >= TrailTriggerR)
                {
                    double trail = FibonacciStructureTrail(basket.Direction);
                    if (trail > 0) AdvanceBasketProtectionFrontier(basket, trail, "FIB_382_STRUCTURE_TRAIL");
                }
            }
        }

        private void ReconcileGridFills()
        {
            foreach (var p in OwnPositions().ToList())
            {
                string basketId = LabelBasketId(p.Label);
                int legIndex = LabelLegIndex(p.Label);
                FibonacciBasket basket;
                if (string.IsNullOrWhiteSpace(basketId) || !_baskets.TryGetValue(basketId, out basket))
                {
                    _orphanPendingOrders++;
                    continue;
                }

                var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == legIndex);
                if (leg == null)
                {
                    _orphanPendingOrders++;
                    continue;
                }

                if (!_postFillValidated.Contains(p.Id))
                    PostFillSafetyKernel(p, "RECONCILE");
                if (!_postFillValidated.Contains(p.Id))
                {
                    if (PositionStillExists(p.Id))
                    {
                        basket.ExitOverride = "RECONCILE_POST_FILL_NOT_VALIDATED";
                        FailClosePosition(p, basket, basket.ExitOverride);
                        if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    }
                    continue;
                }
                if (!PositionStillExists(p.Id)) continue;

                if (!_positions.ContainsKey(p.Id))
                    RegisterFilledPosition(basket, leg, p);
                RecordLegFillTelemetry(basket, leg);
            }

            foreach (var o in OwnPendingOrders().ToList())
            {
                string basketId = LabelBasketId(o.Label);
                if (string.IsNullOrWhiteSpace(basketId) || !_baskets.ContainsKey(basketId))
                {
                    _orphanPendingOrders++;
                    var r = CancelPendingOrder(o);
                    if ((r == null || !r.IsSuccessful) && PendingOrderStillExists(o.Id))
                        RecordExecutionError("ORPHAN_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()), "order=" + o.Id);
                }
            }
        }

        private void RegisterFilledPosition(FibonacciBasket basket, FibonacciGridLeg leg, Position p)
        {
            if (_positions.ContainsKey(p.Id)) return;
            double initialRiskPips = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
            _positions[p.Id] = new PositionLedger
            {
                PositionId = p.Id,
                CandidateId = basket.CandidateId,
                PatternName = basket.Pattern,
                Route = basket.Route,
                Direction = basket.Direction,
                EntryUtc = p.EntryTime.ToUniversalTime(),
                InitialRiskPips = initialRiskPips,
                RiskAmount = p.VolumeInUnits * _symbol.PipValue * initialRiskPips,
                PeakR = 0,
                MaxAdverseR = 0,
                BasketId = basket.BasketId,
                LegIndex = leg.Index
            };
        }

        private void CancelInvalidPendingOrders()
        {
            DateTime now = Server.Time.ToUniversalTime();
            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                string reason = null;
                if (now >= basket.ExpirationUtc) reason = "CANDIDATE_TTL_EXPIRED";
                else if (_dailyLocked) reason = "DAILY_RISK_LOCK";
                else if (PeakDrawdownExceeded()) reason = "MAX_DRAWDOWN_LOCK";
                else if (!IsInstitutionalSession(now)) reason = "SESSION_EXPIRED";
                else if (BasketStructuralInvalidated(basket)) reason = "STRUCTURAL_INVALIDATION";
                else if (BasketHardConflict(basket)) reason = "MTF_HARD_CONFLICT";

                if (reason == null) continue;

                CancelBasketPending(basket, reason);

                if (!OwnPositions().Any(p => LabelBasketId(p.Label) == basket.BasketId))
                {
                    basket.State = reason == "SESSION_EXPIRED" ? FibonacciBasketState.SESSION_EXPIRED :
                                   reason == "STRUCTURAL_INVALIDATION" ? FibonacciBasketState.INVALIDATED :
                                   reason == "CANDIDATE_TTL_EXPIRED" ? FibonacciBasketState.EXPIRED : FibonacciBasketState.CANCELLED;
                    basket.IsActive = false;
                }
            }
        }

        private bool BasketStructuralInvalidated(FibonacciBasket basket)
        {
            return basket.Direction == TradeDirection.Buy ? _symbol.Bid <= basket.StructuralStop : _symbol.Ask >= basket.StructuralStop;
        }

        private bool BasketHardConflict(FibonacciBasket basket)
        {
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            return ClassifyMtfConflict(basket.Direction, h4, h1) == MtfConflict.CONFLICT &&
                   basket.Route != HarmonicRoute.EXHAUSTION_REVERSAL;
        }

        private void CancelBasketPending(FibonacciBasket basket, string reason)
        {
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                var r = CancelPendingOrder(o);
                if (r == null || !r.IsSuccessful)
                {
                    if (PendingOrderStillExists(o.Id))
                        RecordExecutionError("GRID_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()),
                            "basket=" + basket.BasketId + ";order=" + o.Id + ";reason=" + reason);
                    else
                        BasketEvent(basket, "GRID_CANCEL_RACE_BENIGN_ORDER_" + o.Id);
                    continue;
                }

                var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == LabelLegIndex(o.Label));
                if (leg != null && (leg.State == GridLegState.SUBMITTED || leg.State == GridLegState.SUBMITTING)) TransitionLegState(basket, leg, GridLegState.CANCELLED, "PENDING_CANCELLED_" + reason);
                BasketEvent(basket, "GRID_LEG_CANCELLED_" + reason + "_L" + LabelLegIndex(o.Label));
            }
        }

        private void CancelAllOwnPending(string reason)
        {
            foreach (var o in OwnPendingOrders().ToList())
            {
                var r = CancelPendingOrder(o);
                if ((r == null || !r.IsSuccessful) && PendingOrderStillExists(o.Id))
                    RecordExecutionError("STOP_CANCEL_FAILED_" + (r == null ? "NULL" : r.Error.ToString()), "order=" + o.Id + ";reason=" + reason);
            }
            Print("[V54-PENDING-CANCEL-ALL] reason={0}", reason);
        }

        private void CloseBasketPositions(FibonacciBasket basket, string reason)
        {
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                PositionLedger l;
                if (_positions.TryGetValue(p.Id, out l)) l.ExitOverride = reason;
                var r = ClosePosition(p);
                if ((r == null || !r.IsSuccessful) && PositionStillExists(p.Id))
                    RecordExecutionError("CLOSE_FAILED_" + (r == null ? "NULL" : r.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
            }
        }

        private void AdvanceBasketProtectionFrontier(FibonacciBasket basket, double proposal, string reason)
        {
            if (proposal <= 0) return;
            double frontier = basket.ProtectionFrontier;
            double next = frontier <= 0 ? proposal :
                (basket.Direction == TradeDirection.Buy ? Math.Max(frontier, proposal) : Math.Min(frontier, proposal));

            // Never generate a widening proposal. Structural stop is the initial floor/ceiling.
            if (basket.Direction == TradeDirection.Buy)
                next = Math.Max(next, basket.StructuralStop);
            else
                next = Math.Min(next, basket.StructuralStop);

            bool advanced = frontier <= 0 || (basket.Direction == TradeDirection.Buy ? next > frontier + _symbol.TickSize : next < frontier - _symbol.TickSize);
            if (!advanced) return;

            basket.ProtectionFrontier = next;
            bool anyApplied = false;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
            {
                if (TargetTooCloseForProtectionUpdate(p))
                {
                    BasketEvent(basket, "FRONTIER_SKIP_TARGET_PROXIMITY_POS_" + p.Id);
                    continue;
                }

                double brokerSafe = BrokerSafeStop(p.TradeType, next);
                if (brokerSafe <= 0) continue;

                bool improves = !p.StopLoss.HasValue ||
                    (p.TradeType == TradeType.Buy ? brokerSafe > p.StopLoss.Value + _symbol.TickSize : brokerSafe < p.StopLoss.Value - _symbol.TickSize);
                if (!improves) continue;

                var r = p.ModifyStopLossPrice(brokerSafe);
                if (r == null || !r.IsSuccessful)
                {
                    if (!PositionStillExists(p.Id) || TargetTooCloseForProtectionUpdate(p))
                    {
                        BasketEvent(basket, "FRONTIER_MODIFY_RACE_BENIGN_POS_" + p.Id);
                        continue;
                    }

                    double retryStop = BrokerSafeStop(p.TradeType, next);
                    bool retryImproves = retryStop > 0 && (!p.StopLoss.HasValue ||
                        (p.TradeType == TradeType.Buy ? retryStop > p.StopLoss.Value + _symbol.TickSize : retryStop < p.StopLoss.Value - _symbol.TickSize));
                    TradeResult retry = retryImproves ? p.ModifyStopLossPrice(retryStop) : null;
                    if (retry != null && retry.IsSuccessful)
                    {
                        anyApplied = true;
                        BasketEvent(basket, "FRONTIER_RETRY_SUCCESS_POS_" + p.Id);
                        continue;
                    }

                    if (!PositionStillExists(p.Id) || TargetTooCloseForProtectionUpdate(p))
                    {
                        BasketEvent(basket, "FRONTIER_RETRY_RACE_BENIGN_POS_" + p.Id);
                        continue;
                    }

                    RecordExecutionError("FRONTIER_STOP_FAILED_" + (retry != null ? retry.Error.ToString() : (r == null ? "NULL" : r.Error.ToString())),
                        "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
                    continue;
                }
                anyApplied = true;
            }

            if (anyApplied)
            {
                basket.State = FibonacciBasketState.BASKET_PROTECTED;
                BasketEvent(basket, "PROTECTION_FRONTIER_ADVANCED_" + reason);
            }
        }

        private double BrokerSafeStop(TradeType tradeType, double proposed)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double minDistance = BrokerMinimumDistancePrice(reference, true);
            double spreadPrice = Math.Max(0, _symbol.Ask - _symbol.Bid);
            double safety = Math.Max(_symbol.TickSize * 4.0, Math.Max(minDistance + _symbol.TickSize * 2.0, spreadPrice * 2.0 + _symbol.TickSize * 2.0));
            double safe = tradeType == TradeType.Buy
                ? Math.Min(proposed, reference - safety)
                : Math.Max(proposed, reference + safety);
            if (tradeType == TradeType.Buy && safe >= reference) return 0;
            if (tradeType == TradeType.Sell && safe <= reference) return 0;
            if (_symbol.Digits >= 0)
                return Math.Round(safe, _symbol.Digits, MidpointRounding.AwayFromZero);
            return safe;
        }

        private bool TargetTooCloseForProtectionUpdate(Position p)
        {
            if (p == null || !p.TakeProfit.HasValue) return false;
            double reference = p.TradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double gap = p.TradeType == TradeType.Buy ? p.TakeProfit.Value - reference : reference - p.TakeProfit.Value;
            if (gap <= 0) return true;
            double spreadPrice = Math.Max(0, _symbol.Ask - _symbol.Bid);
            double minTp = BrokerMinimumDistancePrice(reference, false);
            double raceBuffer = Math.Max(_symbol.TickSize * 4.0, Math.Max(minTp + _symbol.TickSize * 2.0, spreadPrice * 2.0 + _symbol.TickSize * 2.0));
            return gap <= raceBuffer;
        }

        private bool DeeperLegThesisEligible(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (leg.Index <= 0) return true;
            if (BasketStructuralInvalidated(basket) || BasketHardConflict(basket)) return false;
            if (_dailyLocked || PeakDrawdownExceeded() || !IsInstitutionalSession(Server.Time.ToUniversalTime())) return false;

            // Causal eligibility only: no historical PF/hour/date lookup and no new Fibonacci levels.
            int i = LastClosedIndex(_m1Bars);
            if (i < 3) return false;
            double close = _m1Bars.ClosePrices[i];
            double prev = _m1Bars.ClosePrices[i - 1];
            double impulse = basket.Direction == TradeDirection.Buy ? close - prev : prev - close;
            bool notAcceleratingAgainst = impulse >= -PipsToPrice(Math.Max(1.0, SpreadPips()));
            if (!notAcceleratingAgainst) return false;
            if (EnableGridStateAwareV54 && basket.Candidate != null)
            {
                var candidate = basket.Candidate;
                if (!candidate.IsProvenCoreAlpha && candidate.EconomicQualityScore > 0 && candidate.EconomicQualityScore < .65 && leg.Index >= 2)
                    return false;
                if ((basket.Pattern == "AB=CD" || basket.Pattern == "Rat") && leg.Index >= 3)
                    return false;
            }
            return true;
        }

        private double CurrentFilledStructuralRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
                risk += p.VolumeInUnits * _symbol.PipValue * d;
            }
            return risk;
        }

        private double CurrentPendingStructuralRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(o.TargetPrice - basket.StructuralStop));
                risk += o.VolumeInUnits * _symbol.PipValue * d + o.VolumeInUnits * _symbol.PipValue * ModeledCostPips();
            }
            return risk;
        }

        private double FibonacciStructureTrail(TradeDirection direction)
        {
            int end = LastClosedIndex(_m1Bars);
            if (end < 20) return 0;
            int start = Math.Max(1, end - 20);
            double hi = double.MinValue, lo = double.MaxValue;

            for (int i = start; i <= end; i++)
            {
                hi = Math.Max(hi, _m1Bars.HighPrices[i]);
                lo = Math.Min(lo, _m1Bars.LowPrices[i]);
            }

            if (hi <= lo) return 0;
            return direction == TradeDirection.Buy
                ? hi - .382 * (hi - lo)
                : lo + .382 * (hi - lo);
        }

        private void OnPositionOpened(PositionOpenedEventArgs args)
        {
            if (args == null || args.Position == null) return;
            PostFillSafetyKernel(args.Position, "POSITIONS_OPENED");
        }

        private void OnPendingOrderFilled(PendingOrderFilledEventArgs args)
        {
            if (args == null || args.Position == null) return;
            PostFillSafetyKernel(args.Position, "PENDING_FILLED");
        }

        private void PostFillSafetyKernel(Position p, string source)
        {
            if (p == null || p.SymbolName != SymbolName || string.IsNullOrWhiteSpace(p.Label) ||
                !p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal)) return;
            if (_postFillValidated.Contains(p.Id)) return;
            if (!_postFillInProgress.Add(p.Id))
            {
                Print("[V54-POST-FILL-DEDUPE] pos={0} source={1}", p.Id, source);
                return;
            }

            try
            {
                PostFillSafetyKernelCore(p, source);
            }
            finally
            {
                _postFillInProgress.Remove(p.Id);
            }
        }

        private void PostFillSafetyKernelCore(Position p, string source)
        {
            string basketId = LabelBasketId(p.Label);
            int legIndex = LabelLegIndex(p.Label);
            FibonacciBasket basket;
            if (string.IsNullOrWhiteSpace(basketId) || !_baskets.TryGetValue(basketId, out basket))
            {
                _orphanPendingOrders++;
                return;
            }
            var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == legIndex);
            if (leg == null)
            {
                _orphanPendingOrders++;
                return;
            }

            if (leg.State == GridLegState.FAIL_CLOSED)
            {
                FailClosePosition(p, basket, "REPEAT_POST_FILL_AFTER_FAIL_CLOSED");
                return;
            }

            if (leg.State == GridLegState.CANCELLED || leg.State == GridLegState.EXPIRED ||
                leg.State == GridLegState.REJECTED || leg.State == GridLegState.RISK_REJECTED)
            {
                _executionStateViolations++;
                basket.ExitOverride = "LATE_FILL_AFTER_TERMINAL_STATE_" + leg.State;
                Print("[V54-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next=FILLED_UNVERIFIED reason=LATE_FILL_AFTER_TERMINAL_STATE",
                    basket.BasketId, leg.Index, leg.State);
                CancelBasketPending(basket, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                return;
            }

            TransitionLegState(basket, leg, GridLegState.FILLED_UNVERIFIED, "POST_FILL_" + source);
            leg.PositionId = p.Id;
            if (!_positions.ContainsKey(p.Id)) RegisterFilledPosition(basket, leg, p);

            bool entryCross = basket.Direction == TradeDirection.Buy
                ? p.EntryPrice <= basket.StructuralStop
                : p.EntryPrice >= basket.StructuralStop;
            bool marketCross = BasketStructuralInvalidated(basket);
            if (entryCross || marketCross)
            {
                _gapThroughInvalidations++;
                basket.ExitOverride = "GAP_THROUGH_STRUCTURAL_INVALIDATION";
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                CancelBasketPending(basket, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (PositionStillExists(p.Id)) _gapThroughSurvivors++;
                else _positions.Remove(p.Id);
                return;
            }

            double actualWorst = ActualBasketWorstRisk(basket);
            if (actualWorst > basket.InitialBasketRisk + 1e-8)
            {
                _actualBasketRiskViolations++;
                basket.ExitOverride = "ACTUAL_FILL_RISK_BUDGET_BREACH";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (!PositionStillExists(p.Id)) _positions.Remove(p.Id);
                return;
            }

            if (!EnsurePostFillProtection(p, basket))
            {
                basket.ExitOverride = "POST_FILL_PROTECTION_FAIL_CLOSED";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                else _positions.Remove(p.Id);
                return;
            }

            if (Account.FreeMargin < basket.InitialBasketRisk * MinFreeMarginRiskMultiple)
            {
                _marginRiskViolations++;
                basket.ExitOverride = "POST_FILL_MARGIN_HEADROOM";
                CancelBasketPending(basket, basket.ExitOverride);
                TransitionLegState(basket, leg, GridLegState.FAIL_CLOSED, basket.ExitOverride);
                FailClosePosition(p, basket, basket.ExitOverride);
                if (!PositionStillExists(p.Id)) _positions.Remove(p.Id);
                return;
            }

            _postFillValidated.Add(p.Id);
            TransitionLegState(basket, leg, GridLegState.PROTECTED, "POST_FILL_PROTECTED");
            Print("[V54-POST-FILL-AUDIT] basket={0} leg=L{1} pos={2} source={3} entry={4} stop={5} target={6} actualWorst={7:F4} budget={8:F4} protected=true",
                basket.BasketId, leg.Index, p.Id, source, p.EntryPrice, basket.StructuralStop, basket.CanonicalTarget, actualWorst, basket.InitialBasketRisk);
        }

        private bool EnsurePostFillProtection(Position p, FibonacciBasket basket)
        {
            bool stopAcceptable = p.StopLoss.HasValue &&
                (p.TradeType == TradeType.Buy ? p.StopLoss.Value + _symbol.TickSize >= basket.StructuralStop
                                              : p.StopLoss.Value - _symbol.TickSize <= basket.StructuralStop);
            bool tpAcceptable = p.TakeProfit.HasValue &&
                (p.TradeType == TradeType.Buy ? p.TakeProfit.Value > p.EntryPrice : p.TakeProfit.Value < p.EntryPrice);

            if (!stopAcceptable)
            {
                if (!BrokerStopDistanceValid(p.TradeType, basket.StructuralStop))
                {
                    _postFillProtectionFailures++;
                    return false;
                }
                var rs = p.ModifyStopLossPrice(basket.StructuralStop);
                if (rs == null || !rs.IsSuccessful)
                {
                    _postFillProtectionFailures++;
                    RecordExecutionError("POST_FILL_SL_" + (rs == null ? "NULL" : rs.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id);
                    return false;
                }
            }

            var live = Positions.FirstOrDefault(x => x.Id == p.Id);
            if (live == null || !live.StopLoss.HasValue)
            {
                _postFillProtectionFailures++;
                return false;
            }

            if (!tpAcceptable)
            {
                if (!BrokerTargetDistanceValid(p.TradeType, basket.CanonicalTarget))
                {
                    _postFillProtectionFailures++;
                    return false;
                }
                var rt = live.ModifyTakeProfitPrice(basket.CanonicalTarget);
                if (rt == null || !rt.IsSuccessful)
                {
                    _postFillProtectionFailures++;
                    RecordExecutionError("POST_FILL_TP_" + (rt == null ? "NULL" : rt.Error.ToString()),
                        "basket=" + basket.BasketId + ";position=" + p.Id);
                    return false;
                }
            }

            live = Positions.FirstOrDefault(x => x.Id == p.Id);
            return live != null && live.StopLoss.HasValue && live.TakeProfit.HasValue;
        }

        private bool BrokerTargetDistanceValid(TradeType tradeType, double target)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Ask : _symbol.Bid;
            double minTp = BrokerMinimumDistancePrice(reference, false);
            return tradeType == TradeType.Buy
                ? target > reference && target - reference + 1e-12 >= minTp
                : target < reference && reference - target + 1e-12 >= minTp;
        }

        private void FailClosePosition(Position p, FibonacciBasket basket, string reason)
        {
            var r = ClosePosition(p);
            if ((r == null || !r.IsSuccessful) && PositionStillExists(p.Id))
                RecordExecutionError("FAIL_CLOSE_" + (r == null ? "NULL" : r.Error.ToString()),
                    "basket=" + basket.BasketId + ";position=" + p.Id + ";reason=" + reason);
        }

        private double ActualBasketWorstRisk(FibonacciBasket basket)
        {
            double risk = 0;
            foreach (var p in OwnPositions().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                bool validSide = basket.Direction == TradeDirection.Buy ? p.EntryPrice > basket.StructuralStop : p.EntryPrice < basket.StructuralStop;
                if (!validSide) return double.MaxValue;
                double d = PriceToPips(Math.Abs(p.EntryPrice - basket.StructuralStop));
                risk += p.VolumeInUnits * _symbol.PipValue * (d + ModeledCostPips());
            }
            foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId))
            {
                double d = PriceToPips(Math.Abs(o.TargetPrice - basket.StructuralStop));
                risk += o.VolumeInUnits * _symbol.PipValue * (d + ModeledCostPips());
            }
            return risk;
        }

        private void RecordLegFillTelemetry(FibonacciBasket basket, FibonacciGridLeg leg)
        {
            if (leg.FillCounted) return;
            if (leg.State != GridLegState.PROTECTED || leg.PositionId <= 0 || !_postFillValidated.Contains(leg.PositionId))
            {
                _executionStateViolations++;
                BasketEvent(basket, "FILL_TELEMETRY_WITHOUT_PROTECTION_L" + leg.Index);
                return;
            }
            leg.FillCounted = true;
            basket.FilledLegs = Math.Max(basket.FilledLegs, basket.Plan.Legs.Count(x => x.FillCounted));
            if (leg.Index == 1) CountPipeline(basket.Pattern).Leg1Filled++;
            if (leg.Index == 2) CountPipeline(basket.Pattern).Leg2Filled++;
            if (leg.Index == 3) CountPipeline(basket.Pattern).Leg3Filled++;
            BasketEvent(basket, "GRID_LEG_FILLED_L" + leg.Index);
        }

        private void UpdateVirtualGridState(FibonacciBasket basket)
        {
            if (basket == null || !basket.IsActive || BasketStructuralInvalidated(basket)) return;
            foreach (var leg in basket.Plan.Legs.Where(x => !x.Physical && x.State == GridLegState.VIRTUAL_ONLY).ToList())
            {
                bool touched = basket.Direction == TradeDirection.Buy ? _symbol.Ask <= leg.PlannedPrice : _symbol.Bid >= leg.PlannedPrice;
                if (!touched) continue;
                if (!DeeperLegThesisEligible(basket, leg))
                {
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "VIRTUAL_THESIS_REJECT");
                    continue;
                }
                _virtualGridFills++;
                TransitionLegState(basket, leg, GridLegState.VIRTUAL_FILLED, "VIRTUAL_GRID_FILLED");
            }
        }

        private void RevalidatePendingExposureGovernor()
        {
            foreach (var basket in _baskets.Values.Where(b => b.IsActive).ToList())
            {
                foreach (var o in OwnPendingOrders().Where(x => LabelBasketId(x.Label) == basket.BasketId).ToList())
                {
                    int index = LabelLegIndex(o.Label);
                    var leg = basket.Plan.Legs.FirstOrDefault(x => x.Index == index);
                    if (leg == null || !leg.Physical) continue;
                    if (DeeperLegThesisEligible(basket, leg)) continue;

                    var r = CancelPendingOrder(o);
                    if (r == null || !r.IsSuccessful)
                    {
                        if (PendingOrderStillExists(o.Id))
                            RecordExecutionError("EXPOSURE_GOVERNOR_CANCEL_" + (r == null ? "NULL" : r.Error.ToString()),
                                "basket=" + basket.BasketId + ";order=" + o.Id);
                        continue;
                    }
                    TransitionLegState(basket, leg, GridLegState.CANCELLED, "EXPOSURE_GOVERNOR");
                }
            }
        }

        private void TransitionLegState(FibonacciBasket basket, FibonacciGridLeg leg, GridLegState next, string reason)
        {
            GridLegState prior = leg.State;
            bool allowed =
                prior == next ||
                (prior == GridLegState.PLANNED && (next == GridLegState.SUBMITTING || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED || next == GridLegState.REJECTED || next == GridLegState.RISK_REJECTED ||
                    next == GridLegState.VIRTUAL_ONLY)) ||
                (prior == GridLegState.SUBMITTING && (next == GridLegState.SUBMITTED || next == GridLegState.FILLED_UNVERIFIED ||
                    next == GridLegState.REJECTED || next == GridLegState.FAIL_CLOSED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED)) ||
                (prior == GridLegState.SUBMITTED && (next == GridLegState.FILLED_UNVERIFIED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.FILLED_UNVERIFIED && (next == GridLegState.PROTECTED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.PROTECTED && next == GridLegState.FAIL_CLOSED) ||
                (prior == GridLegState.VIRTUAL_ONLY && (next == GridLegState.VIRTUAL_FILLED || next == GridLegState.CANCELLED ||
                    next == GridLegState.EXPIRED));
            if (!allowed)
            {
                _executionStateViolations++;
                Print("[V54-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next={3} reason={4}", basket == null ? "" : basket.BasketId, leg.Index, prior, next, reason);
            }
            leg.State = next;
            if (basket != null) BasketEvent(basket, "LEG_STATE_L" + leg.Index + "_" + prior + "_TO_" + next + "_" + reason);
        }

        private void PrintBrokerCapabilityProfile()
        {
            double min = _symbol.VolumeInUnitsMin;
            double marginBuy = EstimatedMargin(TradeDirection.Buy, min);
            double marginSell = EstimatedMargin(TradeDirection.Sell, min);
            Print("[V54-BROKER-PROFILE] symbol={0} equity={1:F2} freeMargin={2:F2} minVolume={3} step={4} maxVolume={5} pipValue={6} tickValue={7} minSL={8} minTP={9} minDistanceType={10} minMarginBuy={11:F2} minMarginSell={12:F2} minimumSupportedEquity={13:F2} adaptiveCapital={14} microThreshold={15:F2} initialCapitalEligible={16}",
                SymbolName, Account.Equity, Account.FreeMargin, _symbol.VolumeInUnitsMin, _symbol.VolumeInUnitsStep, _symbol.VolumeInUnitsMax,
                _symbol.PipValue, _symbol.TickValue, _symbol.MinStopLossDistance, _symbol.MinTakeProfitDistance, _symbol.MinDistanceType,
                marginBuy, marginSell, MinimumSupportedEquity, AdaptiveCapitalMode, MicroCapitalThreshold, _initialCapitalEligible);
        }

        private double WeightedAverageEntry(List<Position> positions)
        {
            double volume = positions.Sum(p => p.VolumeInUnits);
            return volume > 0 ? positions.Sum(p => p.EntryPrice * p.VolumeInUnits) / volume : 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.SymbolName != SymbolName || string.IsNullOrWhiteSpace(p.Label) || !p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal))
                return;

            PositionLedger l;
            if (!_positions.TryGetValue(p.Id, out l))
            {
                Print("[V54-LEG-CLOSED] pos={0} basket=UNKNOWN net={1:F2} reason={2}", p.Id, p.NetProfit, args.Reason);
                return;
            }

            FibonacciBasket basket = null;
            if (_baskets.TryGetValue(l.BasketId, out basket))
            {
                basket.RealizedNet += p.NetProfit;
                basket.ClosedLegs++;
                double legRealizedR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
                Print("[V54-LEG-CLOSED] basket={0} cid={1} leg=L{2} pos={3} pattern={4} route={5} dir={6} mfeR={7:F3} maeR={8:F3} realizedR={9:F3} net={10:F2} reason={11}",
                    basket.BasketId, basket.CandidateId, l.LegIndex, p.Id, basket.Pattern, basket.Route, basket.Direction,
                    l.PeakR, l.MaxAdverseR, legRealizedR, p.NetProfit, args.Reason);

                if (args.Reason.ToString().IndexOf("TakeProfit", StringComparison.OrdinalIgnoreCase) >= 0)
                    CancelBasketPending(basket, "CANONICAL_TARGET_REACHED");
            }

            _positions.Remove(p.Id);
            _postFillValidated.Remove(p.Id);

            if (basket != null &&
                !OwnPositions().Any(x => LabelBasketId(x.Label) == basket.BasketId) &&
                !OwnPendingOrders().Any(x => LabelBasketId(x.Label) == basket.BasketId))
                CloseBasketLedger(basket, string.IsNullOrWhiteSpace(basket.ExitOverride) ? args.Reason.ToString() : basket.ExitOverride);
        }

        private void CloseBasketLedger(FibonacciBasket basket, string reason)
        {
            if (!basket.IsActive) return;
            basket.IsActive = false;
            basket.State = FibonacciBasketState.CLOSED;
            basket.ExitReason = reason;

            double realizedR = basket.InitialBasketRisk > 0 ? basket.RealizedNet / basket.InitialBasketRisk : 0;
            CountPipeline(basket.Pattern).BasketClosed++;
            BasketEvent(basket, "BASKET_CLOSED_" + reason);

            double entryImprovementPips = basket.AverageEntry > 0
                ? PriceToPips(basket.Direction == TradeDirection.Buy ? basket.EntryAnchor - basket.AverageEntry : basket.AverageEntry - basket.EntryAnchor)
                : 0;
            string setupKey = basket.Candidate != null ? basket.Candidate.SetupKey : "";
            string subtype = basket.Candidate != null && basket.Candidate.Signal != null ? basket.Candidate.Signal.HarmonicSubtype : basket.Pattern;
            Print("[V54-BASKET-CLOSED] basket={0} cid={1} setup={2} pattern={3} subtype={4} route={5} dir={6} plannedLegs={7} filledLegs={8} anchor={9} avgEntry={10} entryImprovePips={11:F3} stop={12} target={13} initialRisk={14:F2} worstRisk={15:F2} mfeR={16:F3} maeR={17:F3} realizedR={18:F3} net={19:F2} reason={20}",
                basket.BasketId, basket.CandidateId, setupKey, basket.Pattern, subtype, basket.Route, basket.Direction, basket.Plan.Legs.Count, basket.FilledLegs,
                basket.EntryAnchor, basket.AverageEntry, entryImprovementPips, basket.StructuralStop, basket.CanonicalTarget,
                basket.InitialBasketRisk, basket.PlannedWorstCaseRisk, basket.PeakR, basket.MaxAdverseR, realizedR, basket.RealizedNet, reason);

            double occupancyMin = Math.Max(0, (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes);
            _basketOccupancyMinutes.Add(occupancyMin);
            Print("[V54-SLOT-OCCUPANCY] basket={0} cid={1} pattern={2} route={3} occupancyMinutes={4:F2} realizedR={5:F3} net={6:F2}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, occupancyMin, realizedR, basket.RealizedNet);

            if (EnableEventDrivenSerialHandoff)
                TryScheduleAndExecute();
        }

        private IEnumerable<PendingOrder> OwnPendingOrders()
        {
            return PendingOrders.Where(o => o.SymbolName == SymbolName &&
                !string.IsNullOrWhiteSpace(o.Label) && o.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal));
        }

        private bool LegAlreadyExists(string label)
        {
            return OwnPositions().Any(p => p.Label == label) || OwnPendingOrders().Any(o => o.Label == label);
        }

        private string NewBasketId()
        {
            _basketSeq++;
            return BotPrefix + "-" + SymbolName + "-" + Server.Time.ToUniversalTime().ToString("yyyyMMdd", CultureInfo.InvariantCulture) + "-" +
                   _basketSeq.ToString("D6", CultureInfo.InvariantCulture);
        }

        private string GridLabel(string basketId, int legIndex)
        {
            return BotPrefix + "|" + basketId + "|L" + legIndex;
        }

        private string GridComment(FibonacciBasket basket, int legIndex)
        {
            return "cid=" + basket.CandidateId + ";basket=" + basket.BasketId + ";leg=L" + legIndex +
                   ";pattern=" + basket.Pattern + ";tf=M15;route=" + basket.Route;
        }

        private string LabelBasketId(string label)
        {
            if (string.IsNullOrWhiteSpace(label)) return null;
            var p = label.Split('|');
            return p.Length >= 3 && p[0] == BotPrefix ? p[1] : null;
        }

        private int LabelLegIndex(string label)
        {
            if (string.IsNullOrWhiteSpace(label)) return -1;
            var p = label.Split('|');
            if (p.Length < 3 || !p[2].StartsWith("L", StringComparison.Ordinal)) return -1;
            int x;
            return int.TryParse(p[2].Substring(1), out x) ? x : -1;
        }

        private void BasketEvent(FibonacciBasket basket, string reason)
        {
            Print("[V54-BASKET-EVENT] basket={0} cid={1} pattern={2} route={3} state={4} reason={5}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, basket.State, reason);
        }

        private DateTime MinDate(DateTime a, DateTime b) { return a <= b ? a : b; }

        // ---------------- Harmonic engine ----------------

        private List<PatternSignal> DetectPatternCandidates(Bars bars, int endIndex, int depth, int lookback, int maxCandidates, string timeframe)
        {
            var result = new List<PatternSignal>();
            if (bars == null || endIndex < 40) return result;
            double atr = Atr(bars, 14, endIndex);
            if (atr <= 0) return result;

            int[] scales = EnableIndependentPivotGraph && string.Equals(timeframe, "M15", StringComparison.OrdinalIgnoreCase)
                ? new[] { 2, 3, 5 }
                : new[] { Math.Max(2, depth) };

            foreach (int scale in scales.Distinct())
            {
                var pivots = BuildConfirmedPivots(bars, endIndex, lookback, scale);
                if (pivots.Count < 5) continue;
                int start = Math.Max(0, pivots.Count - (EnableFamilyIdentityReconstruction ? 28 : 36));

                IEnumerable<PivotSequence> sequences;
                if (EnableFamilyIdentityReconstruction && EnableBoundedPivotGraph && string.Equals(timeframe, "M15", StringComparison.OrdinalIgnoreCase))
                    sequences = EnumerateBoundedPivotSequences(pivots, start, Math.Max(0, Math.Min(2, MaxMicroPivotSkips)));
                else
                    sequences = Enumerable.Range(start, Math.Max(0, pivots.Count - 4 - start))
                        .Select(k => new PivotSequence { X = pivots[k], A = pivots[k + 1], B = pivots[k + 2], C = pivots[k + 3], D = pivots[k + 4] });

                foreach (var seq in sequences)
                {
                    foreach (var profile in _profiles)
                    {
                        DetectorTruth(profile.Name, "TOPOLOGY_ATTEMPT");
                        PatternSignal sig;
                        if (!TryMatchProfile(profile, seq.X, seq.A, seq.B, seq.C, seq.D, atr, bars.OpenTimes[seq.D.Index], timeframe, scale, out sig))
                            continue;
                        if (endIndex - seq.D.Index > Math.Max(2, profile.MaxAgeM15Bars))
                        {
                            DetectorTruth(profile.Name, "AGE_REJECT");
                            continue;
                        }
                        if (scale != depth) _independentScaleCandidates++;
                        result.Add(sig);
                    }
                }
            }

            if (!EnableFamilyIdentityReconstruction)
            {
                var ordered = result.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality);
                if (EnableCanonicalSetupIdentity)
                    ordered = ordered.GroupBy(BuildSetupGeometryKey)
                        .Select(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).First())
                        .OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality);

                return ordered
                    .GroupBy(x => x.PatternName + "|" + x.Direction + "|" + x.CompletionTime.ToString("O") + "|" + x.PivotScale)
                    .Select(g => g.First())
                    .Take(Math.Max(1, maxCandidates))
                    .ToList();
            }

            var hypotheses = result
                .GroupBy(BuildFamilyHypothesisKey)
                .Select(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).First())
                .ToList();

            int quota = Math.Max(1, FamilyDetectionQuota);
            var fair = hypotheses
                .GroupBy(x => x.PatternName)
                .SelectMany(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).Take(quota))
                .OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality)
                .Take(Math.Max(maxCandidates, _profiles.Count * quota))
                .ToList();

            foreach (var x in fair) DetectorTruth(x.PatternName, "FAMILY_QUOTA_SELECTED");
            return fair;
        }

        private IEnumerable<PivotSequence> EnumerateBoundedPivotSequences(List<PivotPoint> pivots, int start, int maxTotalSkips)
        {
            int n = pivots.Count;
            for (int ix = start; ix <= n - 5; ix++)
            for (int ia = ix + 1; ia <= Math.Min(n - 4, ix + 3); ia++)
            for (int ib = ia + 1; ib <= Math.Min(n - 3, ia + 3); ib++)
            for (int ic = ib + 1; ic <= Math.Min(n - 2, ib + 3); ic++)
            for (int id = ic + 1; id <= Math.Min(n - 1, ic + 3); id++)
            {
                int skips = (ia - ix - 1) + (ib - ia - 1) + (ic - ib - 1) + (id - ic - 1);
                if (skips > maxTotalSkips) continue;
                yield return new PivotSequence { X = pivots[ix], A = pivots[ia], B = pivots[ib], C = pivots[ic], D = pivots[id] };
            }
        }

        private HarmonicState GetActiveHarmonicState(Bars bars, int depth, int lookback, int maxAge)
        {
            int i = LastClosedIndex(bars);
            if (i < 40) return HarmonicState.Neutral;
            var xs = DetectPatternCandidates(bars, i, depth, lookback, 4, bars.TimeFrame.ToString());
            var best = xs.Where(x => i - x.D.Index <= maxAge).OrderByDescending(x => x.Confidence).FirstOrDefault();
            if (best == null) return HarmonicState.Neutral;
            return best.Direction == TradeDirection.Buy ? HarmonicState.Bullish : HarmonicState.Bearish;
        }

        private bool TryMatchProfile(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            double atr, DateTime completion, string timeframe, int pivotScale, out PatternSignal signal)
        {
            signal = null;
            bool bullish, bearish;
            if (EnableFamilyIdentityReconstruction)
            {
                if (!TryFamilyTopology(p, x, a, b, c, d, out bullish, out bearish))
                {
                    DetectorTruth(p.Name, "TOPOLOGY_REJECT");
                    return false;
                }
                DetectorTruth(p.Name, "TOPOLOGY_MATCH");
            }
            else
            {
                bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
                bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
                if (!bullish && !bearish) return false;
            }

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double ad = Math.Abs(d.Price - a.Price);
            double xd = Math.Abs(d.Price - x.Price);
            double xc = Math.Abs(c.Price - x.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0 || atr <= 0) return false;
            double legFloorAtr = EnableFamilyIdentityReconstruction ? FamilyLegFloorAtr(p) : .45;
            if (Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) < atr * legFloorAtr)
            {
                DetectorTruth(p.Name, "LEG_SCALE_PRECHECK_REJECT");
                return false;
            }

            double xab = ab / xa;
            double abc = bc / ab;
            double bcd = cd / bc;
            double xdxa = xd / xa;
            double adxa = ad / xa;
            double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;
            double abcd = cd / ab;
            double xac = xc / xa;

            bool ratioOk;
            if (p.Mode == PatternMode.ABCD)
                ratioOk = InRange(abc, p.AbcMin, p.AbcMax) && InRange(bcd, p.BcdMin, p.BcdMax) && InRange(abcd, p.AbcDMin, p.AbcDMax);
            else if (p.Mode == PatternMode.CYPHER)
                ratioOk = InRange(xab, .382, .618) && InRange(xac, 1.13, 1.414) && InRange(cd / Math.Max(xc, 1e-9), .70, .90);
            else if (p.Mode == PatternMode.SHARK)
                ratioOk = InRange(abc, 1.13, 1.618) && InRange(bcd, 1.13, 2.24) && InRange(xad, .85, 1.25);
            else if (p.Mode == PatternMode.FIVEZERO)
                ratioOk = InRange(xab, 1.13, 1.618) && InRange(abc, 1.618, 2.24) && InRange(bcd, .45, .65);
            else
                ratioOk = InRange(xab, p.XabMin, p.XabMax) && InRange(abc, p.AbcMin, p.AbcMax) &&
                          InRange(bcd, p.BcdMin, p.BcdMax) && InRange(xad, p.XadMin, p.XadMax);

            if (ratioOk && EnableCanonicalFamilyContracts && p.Mode == PatternMode.STANDARD)
            {
                bool componentOk = StandardFamilyAbcdCompatible(p.Name, abcd);
                if (!EnableFamilyIdentityReconstruction) ratioOk = componentOk;
                else if (!componentOk) DetectorTruth(p.Name, "ABCD_COMPONENT_SHADOW_MISMATCH");
            }

            if (!ratioOk)
            {
                DetectorTruth(p.Name, "RATIO_IDENTITY_REJECT");
                return false;
            }
            DetectorTruth(p.Name, "RATIO_IDENTITY_PASS");

            double legacyGeometry = p.Mode == PatternMode.STANDARD
                ? (RatioScore(xab, Mid(p.XabMin, p.XabMax)) + RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) +
                   RatioScore(bcd, Mid(p.BcdMin, p.BcdMax)) + RatioScore(xad, Mid(p.XadMin, p.XadMax))) / 4.0
                : VClamp((RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) + RatioScore(bcd, Mid(p.BcdMin, p.BcdMax))) / 2.0);
            double geometry = EnableFamilyNativeJointGeometry
                ? FamilyNativeJointGeometryScore(p, xab, abc, bcd, xad, abcd, xac)
                : legacyGeometry;

            int t1 = Math.Max(1, a.Index - x.Index);
            int t2 = Math.Max(1, b.Index - a.Index);
            int t3 = Math.Max(1, c.Index - b.Index);
            int t4 = Math.Max(1, d.Index - c.Index);
            double timeSym = (Symmetry(t1, t2) + Symmetry(t2, t3) + Symmetry(t3, t4)) / 3.0;
            double pivotQuality = VClamp(Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) / (atr * 2.0));

            double projectionSpread = 0;
            double expectedD = EnableFamilyIdentityReconstruction && EnableFamilyNativeProjectedPrz
                ? FamilyProjectedPrzCenter(p, x, a, b, c, d, bullish, out projectionSpread)
                : d.Price;
            if (!(EnableFamilyIdentityReconstruction && EnableFamilyNativeProjectedPrz)) projectionSpread = 0;
            double przHalf = Math.Max(atr * p.PrzWidthAtr, projectionSpread);
            if (EnableFamilyIdentityReconstruction && EnableFamilyNativeProjectedPrz)
                przHalf = Math.Max(przHalf, Math.Abs(d.Price - expectedD) + atr * .05);
            // V48 family-native PRZ width: do not change pattern identity ratios; only execution geometry.
            if (EnableFamilyNativeConversion)
            {
                if (p.Mode == PatternMode.STANDARD)
                    przHalf *= (p.Name == "Crab" || p.Name == "Deep Crab" || p.Name == "Butterfly" || p.Name == "Alt Bat") ? 1.20 : 0.90;
                else if (p.Mode == PatternMode.SHARK || p.Mode == PatternMode.FIVEZERO)
                    przHalf *= 1.25;
                else if (p.Mode == PatternMode.CYPHER)
                    przHalf *= 0.95;
            }
            double przLow = expectedD - przHalf;
            double przHigh = expectedD + przHalf;
            double przConfluence = VClamp(1.0 - Math.Abs(xad - Mid(p.XadMin, p.XadMax)) / Math.Max(.15, p.XadMax - p.XadMin + .05));
            if (p.Mode != PatternMode.STANDARD) przConfluence = VClamp((geometry + timeSym) / 2.0);

            double invalid = PatternStructuralInvalidation(p, x, a, b, c, d, bullish);
            double nativeBase = cd;
            if (EnableFamilyNativeConversion)
            {
                if (p.Mode == PatternMode.CYPHER || p.Mode == PatternMode.SHARK) nativeBase = Math.Max(xc, cd);
                else if (p.Mode == PatternMode.FIVEZERO) nativeBase = bc;
                else if (p.Mode == PatternMode.STANDARD && (p.Name == "Crab" || p.Name == "Deep Crab" || p.Name == "Butterfly" || p.Name == "Alt Bat")) nativeBase = Math.Max(cd, xa * .50);
            }
            double target1 = bullish ? d.Price + nativeBase * p.Target1Cd : d.Price - nativeBase * p.Target1Cd;
            double target2 = bullish ? d.Price + nativeBase * p.Target2Cd : d.Price - nativeBase * p.Target2Cd;
            double confidence = VClamp(0.45 * geometry + 0.25 * przConfluence + 0.15 * timeSym + 0.15 * pivotQuality);

            signal = new PatternSignal
            {
                PatternName = p.Name,
                Profile = p,
                Direction = bullish ? TradeDirection.Buy : TradeDirection.Sell,
                X = x, A = a, B = b, C = c, D = d, PivotScale = pivotScale,
                Xab = xab, Abc = abc, Bcd = bcd, Xad = xad, AdXa = adxa, XdXa = xdxa, AbCd = abcd,
                HarmonicSubtype = p.Mode == PatternMode.ABCD ? AbcdSubtype(abcd) : p.Name,
                PrzLow = przLow, PrzHigh = przHigh,
                GeometryQuality = geometry,
                PrzConfluence = przConfluence,
                TimeSymmetry = timeSym,
                PivotQuality = pivotQuality,
                Confidence = confidence,
                StructuralInvalidation = invalid,
                CanonicalTarget1 = target1,
                CanonicalTarget2 = target2,
                CompletionTime = DateTime.SpecifyKind(completion, DateTimeKind.Utc),
                Timeframe = timeframe
            };
            DetectorTruth(p.Name, "FAMILY_HYPOTHESIS_CREATED");
            return true;
        }

        private void DetectorTruth(string pattern, string stage)
        {
            if (!EnableDetectorTruthLedger) return;
            if (string.IsNullOrWhiteSpace(pattern)) pattern = "UNKNOWN";
            if (string.IsNullOrWhiteSpace(stage)) stage = "UNKNOWN";
            string key = pattern + "::" + stage;
            int n;
            _detectorTruth.TryGetValue(key, out n);
            _detectorTruth[key] = n + 1;
        }

        private double FamilyLegFloorAtr(PatternProfile p)
        {
            if (p == null) return .45;
            if (p.Mode == PatternMode.ABCD) return .35;
            if (p.Mode == PatternMode.STANDARD)
            {
                if (p.Name == "Gartley" || p.Name == "Bat" || p.Name == "Deep Gartley" || p.Name == "Rat") return .25;
                return .30;
            }
            return .30;
        }

        private bool TryFamilyTopology(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            out bool bullish, out bool bearish)
        {
            bullish = false; bearish = false;
            if (p == null) return false;

            if (p.Mode == PatternMode.SHARK || p.Mode == PatternMode.FIVEZERO)
            {
                bullish = a.IsHigh && !b.IsHigh && c.IsHigh && !d.IsHigh;
                bearish = !a.IsHigh && b.IsHigh && !c.IsHigh && d.IsHigh;
                return bullish || bearish;
            }

            bullish = !x.IsHigh && a.IsHigh && !b.IsHigh && c.IsHigh && !d.IsHigh;
            bearish = x.IsHigh && !a.IsHigh && b.IsHigh && !c.IsHigh && d.IsHigh;
            if (!bullish && !bearish)
            {
                bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
                bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
            }
            return bullish || bearish;
        }

        private double NearestAbcdProjection(string pattern, double observed)
        {
            double[] centers;
            if (pattern == "Alt Bat") centers = new[] { 1.618 };
            else if (pattern == "Crab") centers = new[] { 1.27, 1.618 };
            else if (pattern == "Deep Crab") centers = new[] { 1.0, 1.27 };
            else if (pattern == "Butterfly") centers = new[] { 1.0, 1.27, 1.618 };
            else if (pattern == "Gartley" || pattern == "Bat") centers = new[] { 1.0, 1.27 };
            else centers = new[] { 1.0, 1.27, 1.618 };
            return centers.OrderBy(v => Math.Abs(v - observed)).First();
        }

        private double FamilyProjectedPrzCenter(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            bool bullish, out double halfSpread)
        {
            double xa = Math.Max(Math.Abs(a.Price - x.Price), _symbol.PipSize);
            double ab = Math.Max(Math.Abs(b.Price - a.Price), _symbol.PipSize);
            double bc = Math.Max(Math.Abs(c.Price - b.Price), _symbol.PipSize);
            double observedAbcd = Math.Abs(d.Price - c.Price) / ab;
            double sign = bullish ? -1.0 : 1.0;
            var projections = new List<double>();

            if (p.Mode == PatternMode.STANDARD)
            {
                projections.Add(a.Price + sign * Mid(p.XadMin, p.XadMax) * xa);
                projections.Add(c.Price + sign * Mid(p.BcdMin, p.BcdMax) * bc);
                projections.Add(c.Price + sign * NearestAbcdProjection(p.Name, observedAbcd) * ab);
            }
            else if (p.Mode == PatternMode.ABCD)
                projections.Add(c.Price + sign * NearestAbcdProjection("AB=CD", observedAbcd) * ab);
            else if (p.Mode == PatternMode.CYPHER)
                projections.Add(c.Price + sign * .80 * Math.Max(Math.Abs(c.Price - x.Price), _symbol.PipSize));
            else if (p.Mode == PatternMode.SHARK)
            {
                projections.Add(a.Price + sign * Mid(p.XadMin, p.XadMax) * xa);
                projections.Add(c.Price + sign * Mid(p.BcdMin, p.BcdMax) * bc);
            }
            else
                projections.Add(c.Price + sign * Mid(p.BcdMin, p.BcdMax) * bc);

            projections.Add(d.Price);
            projections.Sort();
            double center = projections.Count % 2 == 1 ? projections[projections.Count / 2]
                : .5 * (projections[projections.Count / 2 - 1] + projections[projections.Count / 2]);
            halfSpread = Math.Max(_symbol.PipSize, .5 * (projections.Last() - projections.First()));
            return center;
        }

        private double RangeCoordinate(double value, double lo, double hi)
        {
            double half = Math.Max((hi - lo) * .5, 1e-9);
            return (value - Mid(lo, hi)) / half;
        }

        private double CanonicalAbcdCoordinate(string pattern, double value)
        {
            double[] centers;
            if (pattern == "Alt Bat") centers = new[] { 1.618 };
            else if (pattern == "Crab") centers = new[] { 1.27, 1.618 };
            else if (pattern == "Deep Crab") centers = new[] { 1.0, 1.27 };
            else if (pattern == "Butterfly") centers = new[] { 1.0, 1.27, 1.618 };
            else if (pattern == "Gartley" || pattern == "Bat") centers = new[] { 1.0, 1.27 };
            else centers = new[] { 1.0, 1.27, 1.618 };
            return centers.Min(x => Math.Abs(value - x) / Math.Max(.08, x * .08));
        }

        private double FamilyNativeJointGeometryScore(PatternProfile p, double xab, double abc, double bcd, double xad, double abcd, double xac)
        {
            var z = new List<double>();
            if (p.Mode == PatternMode.STANDARD)
            {
                z.Add(RangeCoordinate(xab, p.XabMin, p.XabMax));
                z.Add(RangeCoordinate(abc, p.AbcMin, p.AbcMax));
                z.Add(RangeCoordinate(bcd, p.BcdMin, p.BcdMax));
                z.Add(RangeCoordinate(xad, p.XadMin, p.XadMax));
                z.Add(CanonicalAbcdCoordinate(p.Name, abcd));
            }
            else if (p.Mode == PatternMode.ABCD)
            {
                z.Add(RangeCoordinate(abc, p.AbcMin, p.AbcMax));
                z.Add(RangeCoordinate(bcd, p.BcdMin, p.BcdMax));
                z.Add(RangeCoordinate(abcd, p.AbcDMin, p.AbcDMax));
            }
            else if (p.Mode == PatternMode.CYPHER)
            {
                z.Add(RangeCoordinate(xab, .382, .618));
                z.Add(RangeCoordinate(xac, 1.13, 1.414));
            }
            else if (p.Mode == PatternMode.SHARK)
            {
                z.Add(RangeCoordinate(abc, 1.13, 1.618));
                z.Add(RangeCoordinate(bcd, 1.13, 2.24));
                z.Add(RangeCoordinate(xad, .85, 1.25));
            }
            else
            {
                z.Add(RangeCoordinate(xab, 1.13, 1.618));
                z.Add(RangeCoordinate(abc, 1.618, 2.24));
                z.Add(RangeCoordinate(bcd, .45, .65));
            }
            double q = z.Count > 0 ? z.Sum(v => v * v) / z.Count : 99;
            return VClamp(Math.Exp(-.50 * q));
        }

        private bool StandardFamilyAbcdCompatible(string pattern, double cdOverAb)
        {
            bool exact = cdOverAb >= .94 && cdOverAb <= 1.06;
            bool alt127 = cdOverAb >= 1.20 && cdOverAb <= 1.34;
            bool alt1618 = cdOverAb >= 1.55 && cdOverAb <= 1.69;
            if (pattern == "Gartley") return exact || alt127;
            if (pattern == "Bat") return exact || alt127;
            if (pattern == "Alt Bat") return alt1618;
            if (pattern == "Butterfly") return exact || alt127 || alt1618;
            if (pattern == "Crab") return alt127 || alt1618;
            if (pattern == "Deep Crab") return exact || alt127;
            return true;
        }

        private string AbcdSubtype(double cdOverAb)
        {
            if (cdOverAb >= .94 && cdOverAb <= 1.06) return "ABCD_EXACT";
            if (cdOverAb >= 1.20 && cdOverAb <= 1.34) return "ABCD_NEAR_127";
            if (cdOverAb >= 1.55 && cdOverAb <= 1.69) return "ABCD_ALT_1618";
            return "ABCD_LEGACY_BROAD";
        }

        private List<PivotPoint> BuildConfirmedPivots(Bars bars, int endIndex, int lookback, int depth)
        {
            var raw = new List<PivotPoint>();
            int last = Math.Min(endIndex - depth, bars.Count - 1 - depth);
            int start = Math.Max(depth, last - lookback);
            for (int i = start; i <= last; i++)
            {
                bool hi = true, lo = true;
                for (int j = i - depth; j <= i + depth; j++)
                {
                    if (j == i) continue;
                    if (bars.HighPrices[j] >= bars.HighPrices[i]) hi = false;
                    if (bars.LowPrices[j] <= bars.LowPrices[i]) lo = false;
                    if (!hi && !lo) break;
                }
                if (hi) raw.Add(new PivotPoint { Index = i, Price = bars.HighPrices[i], IsHigh = true });
                if (lo) raw.Add(new PivotPoint { Index = i, Price = bars.LowPrices[i], IsHigh = false });
            }

            raw = raw.OrderBy(x => x.Index).ToList();
            var compressed = new List<PivotPoint>();
            foreach (var p in raw)
            {
                if (compressed.Count == 0) { compressed.Add(p); continue; }
                var lastP = compressed[compressed.Count - 1];
                if (lastP.IsHigh == p.IsHigh)
                {
                    if ((p.IsHigh && p.Price > lastP.Price) || (!p.IsHigh && p.Price < lastP.Price))
                        compressed[compressed.Count - 1] = p;
                }
                else compressed.Add(p);
            }
            return compressed;
        }

        private void BuildPatternProfiles()
        {
            _profiles.Clear();
            if (EnableCanonicalFamilyContracts)
            {
                AddStd("Gartley", .600, .636, .382, .886, 1.13, 1.618, .770, .800, .12, .18, .618, 1.00, 8, .55, .55);
                AddStd("Bat", .382, .500, .382, .886, 1.618, 2.618, .875, .895, .13, .18, .618, 1.00, 8, .55, .55);
                AddStd("Alt Bat", .300, .395, .382, .886, 2.0, 3.618, 1.10, 1.16, .13, .20, .618, 1.00, 7, .58, .58);
                AddStd("Butterfly", .770, .800, .382, .886, 1.618, 2.618, 1.24, 1.30, .14, .20, .618, 1.00, 7, .58, .58);
                AddStd("Crab", .382, .618, .382, .886, 2.24, 3.618, 1.58, 1.66, .15, .22, .618, 1.00, 6, .60, .60);
                AddStd("Deep Crab", .875, .900, .382, .886, 2.0, 3.618, 1.58, 1.66, .15, .22, .618, 1.00, 6, .60, .60);
                AddStd("Deep Gartley", .70, .82, .382, .886, 1.13, 2.0, .82, .95, .13, .20, .618, 1.00, 7, .58, .58);
                AddStd("Rat", .50, .82, .382, .886, 1.272, 2.618, .88, 1.13, .14, .20, .618, 1.00, 7, .58, .58);
            }
            else
            {
                AddStd("Gartley", .55, .70, .382, .886, 1.13, 1.618, .72, .82, .12, .18, .618, 1.00, 8, .55, .55);
                AddStd("Bat", .382, .52, .382, .886, 1.13, 2.618, .84, .92, .13, .18, .618, 1.00, 8, .55, .55);
                AddStd("Alt Bat", .35, .43, .382, .886, 2.0, 3.618, 1.05, 1.18, .13, .20, .618, 1.00, 7, .58, .58);
                AddStd("Butterfly", .75, .82, .382, .886, 1.618, 2.618, 1.22, 1.35, .14, .20, .618, 1.00, 7, .58, .58);
                AddStd("Crab", .382, .65, .382, .886, 2.24, 3.618, 1.55, 1.72, .15, .22, .618, 1.00, 6, .60, .60);
                AddStd("Deep Crab", .82, .90, .382, .886, 2.0, 3.618, 1.55, 1.72, .15, .22, .618, 1.00, 6, .60, .60);
                AddStd("Deep Gartley", .70, .82, .382, .886, 1.13, 2.0, .82, .95, .13, .20, .618, 1.00, 7, .58, .58);
                AddStd("Rat", .50, .82, .382, .886, 1.272, 2.618, .88, 1.13, .14, .20, .618, 1.00, 7, .58, .58);
            }
            _profiles.Add(new PatternProfile { Name = "Cypher", Mode = PatternMode.CYPHER, AbcMin = 1.13, AbcMax = 1.414, BcdMin = .70, BcdMax = .90, XadMin = .70, XadMax = .90, PrzWidthAtr = .12, StopBufferAtr = .18, Target1Cd = .50, Target2Cd = .886, MaxAgeM15Bars = 6, MinGeometry = .60, MinPrz = .60 });
            _profiles.Add(new PatternProfile { Name = "Shark", Mode = PatternMode.SHARK, AbcMin = 1.13, AbcMax = 1.618, BcdMin = 1.13, BcdMax = 2.24, XadMin = .85, XadMax = 1.25, PrzWidthAtr = .14, StopBufferAtr = .20, Target1Cd = .50, Target2Cd = .886, MaxAgeM15Bars = 6, MinGeometry = .60, MinPrz = .60 });
            _profiles.Add(new PatternProfile { Name = "5-0", Mode = PatternMode.FIVEZERO, AbcMin = 1.618, AbcMax = 2.24, BcdMin = .45, BcdMax = .65, XadMin = .8, XadMax = 1.3, PrzWidthAtr = .14, StopBufferAtr = .20, Target1Cd = .50, Target2Cd = 1.00, MaxAgeM15Bars = 6, MinGeometry = .60, MinPrz = .60 });
            _profiles.Add(new PatternProfile { Name = "AB=CD", Mode = PatternMode.ABCD, AbcMin = .382, AbcMax = .886, BcdMin = 1.13, BcdMax = 2.618, AbcDMin = .80, AbcDMax = 1.25, XadMin = .5, XadMax = 1.5, PrzWidthAtr = .12, StopBufferAtr = .18, Target1Cd = .618, Target2Cd = 1.00, MaxAgeM15Bars = 8, MinGeometry = .55, MinPrz = .55 });
            ConfigureFibonacciGridProfiles();
        }

        private void AddStd(string name, double xab1, double xab2, double abc1, double abc2, double bcd1, double bcd2,
            double xad1, double xad2, double przAtr, double stopAtr, double t1, double t2, int age, double minGeom, double minPrz)
        {
            _profiles.Add(new PatternProfile
            {
                Name = name, Mode = PatternMode.STANDARD,
                XabMin = xab1, XabMax = xab2, AbcMin = abc1, AbcMax = abc2, BcdMin = bcd1, BcdMax = bcd2,
                XadMin = xad1, XadMax = xad2, PrzWidthAtr = przAtr, StopBufferAtr = stopAtr,
                Target1Cd = t1, Target2Cd = t2, MaxAgeM15Bars = age, MinGeometry = minGeom, MinPrz = minPrz
            });
        }


        private void ConfigureFibonacciGridProfiles()
        {
            ConfigureGrid("Gartley", new[] { 0.0, .236, .382, .618 }, 4, .65, 1.05, .65, 90, .030, "PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Bat", new[] { 0.0, .236, .382, .618 }, 4, .75, 1.10, .65, 90, .025, "DEEP_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Alt Bat", new[] { 0.0, .236, .382 }, 3, .02, .35, .42, 75, .030, "EXTENSION_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Butterfly", new[] { 0.0, .236, .382 }, 3, .02, .35, .42, 75, .035, "EXTENSION_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Crab", new[] { 0.0, .236 }, 2, .02, .40, .26, 60, .030, "EXTREME_PRZ_CONFIRM", "T2_PREFERRED");
            ConfigureGrid("Deep Crab", new[] { 0.0, .236 }, 2, .02, .40, .26, 60, .030, "EXTREME_PRZ_CONFIRM", "T2_PREFERRED");
            ConfigureGrid("Cypher", new[] { 0.0, .236, .382 }, 3, .02, .60, .42, 75, .050, "XC_RETRACE_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Shark", new[] { 0.0, .236 }, 2, .02, .60, .26, 60, .050, "EXTREME_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("5-0", new[] { 0.0, .236 }, 2, .02, .60, .26, 60, .050, "REVERSAL_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("AB=CD", new[] { 0.0, .236, .382, .618 }, 4, .02, .80, .65, 90, .050, "ABCD_COMPLETION_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Deep Gartley", new[] { 0.0, .236, .382 }, 3, .70, 1.20, .42, 75, .030, "DEEP_PRZ_CONFIRM", "T1_THEN_T2");
            ConfigureGrid("Rat", new[] { 0.0, .236, .382 }, 3, .02, 1.40, .42, 75, .035, "RATIO_PRZ_CONFIRM", "T1_THEN_T2");
        }

        private void ConfigureGrid(string name, double[] fractions, int maxLegs, double minSpanXa, double maxSpanXa,
            double tolerance, int ttlMinutes, double stopFibBuffer, string anchorRule, string targetPolicy)
        {
            var p = _profiles.FirstOrDefault(x => x.Name == name);
            if (p == null) return;
            p.GridEnabled = true;
            p.GridFractions = fractions;
            p.MaximumGridLegs = maxLegs;
            p.GridRiskWeights = new[] { 3.0 / 7.0, 2.0 / 7.0, 1.0 / 7.0, 1.0 / 7.0 };
            p.GridAnchorRule = anchorRule;
            p.MinimumGridSpanXa = minSpanXa;
            p.MaximumGridSpanXa = maxSpanXa;
            p.GridStructuralTolerance = tolerance;
            p.PendingTtlMinutes = ttlMinutes;
            p.StructuralStopFibBuffer = stopFibBuffer;
            p.CanonicalTargetPolicy = targetPolicy;
        }

        private double PatternStructuralInvalidation(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d, bool bullish)
        {
            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double buffer = Math.Max(_symbol.PipSize * MinStopLossPips, Math.Max(xa, cd) * Math.Max(.01, p.StructuralStopFibBuffer));

            if (p.Mode == PatternMode.STANDARD)
            {
                if (p.XadMax <= 1.0)
                    return bullish ? x.Price - buffer : x.Price + buffer;

                double extreme;
                if (EnableStructuralInvalidationV2)
                {
                    // AD/XA is measured from A. Convert its terminal coordinate back to X-space:
                    // bullish D = X + (1-r)*XA; bearish D = X - (1-r)*XA.
                    extreme = bullish ? x.Price + (1.0 - p.XadMax) * xa
                                      : x.Price - (1.0 - p.XadMax) * xa;
                }
                else
                {
                    // Legacy formula retained only for exact control reproduction.
                    extreme = bullish ? x.Price - p.XadMax * xa : x.Price + p.XadMax * xa;
                }
                return bullish ? extreme - buffer : extreme + buffer;
            }

            if (p.Mode == PatternMode.ABCD)
            {
                double fibBuffer = Math.Max(buffer, ab * .118);
                return bullish ? d.Price - fibBuffer : d.Price + fibBuffer;
            }

            if (p.Mode == PatternMode.CYPHER)
            {
                double fibBuffer = Math.Max(buffer, Math.Abs(c.Price - x.Price) * .118);
                return bullish ? d.Price - fibBuffer : d.Price + fibBuffer;
            }

            if (p.Mode == PatternMode.SHARK || p.Mode == PatternMode.FIVEZERO)
            {
                double fibBuffer = Math.Max(buffer, cd * .118);
                return bullish ? d.Price - fibBuffer : d.Price + fibBuffer;
            }

            return bullish ? d.Price - buffer : d.Price + buffer;
        }

        // ---------------- MTF conflict / regime / router ----------------

        private MtfConflict ClassifyMtfConflict(TradeDirection direction, HarmonicState h4, HarmonicState h1)
        {
            int same = 0, opposite = 0, neutral = 0;
            foreach (var s in new[] { h4, h1 })
            {
                if (s == HarmonicState.Neutral) neutral++;
                else if ((direction == TradeDirection.Buy && s == HarmonicState.Bullish) ||
                         (direction == TradeDirection.Sell && s == HarmonicState.Bearish)) same++;
                else opposite++;
            }
            if (same == 2) return MtfConflict.ALIGNED;
            if (same == 1 && neutral == 1) return MtfConflict.SUPPORTED;
            if (same == 1 && opposite == 1) return MtfConflict.TRANSITION;
            if (opposite == 2) return MtfConflict.CONFLICT;
            return MtfConflict.NEUTRAL;
        }

        private RegimeSnapshot BuildRegimeSnapshot()
        {
            int h4 = LastClosedIndex(_h4Bars);
            int h1 = LastClosedIndex(_h1Bars);
            int m15 = LastClosedIndex(_m15Bars);
            var r = new RegimeSnapshot();

            double h4e50 = Ema(_h4Bars.ClosePrices, 50, h4);
            double h4e200 = Ema(_h4Bars.ClosePrices, 200, h4);
            double h4e50Prev = Ema(_h4Bars.ClosePrices, 50, Math.Max(1, h4 - 3));
            double h1e50 = Ema(_h1Bars.ClosePrices, 50, h1);
            double h1e200 = Ema(_h1Bars.ClosePrices, 200, h1);
            double h1e50Prev = Ema(_h1Bars.ClosePrices, 50, Math.Max(1, h1 - 4));

            int h4Dir = TrendVote(h4e50, h4e200, h4e50 - h4e50Prev);
            int h1Dir = TrendVote(h1e50, h1e200, h1e50 - h1e50Prev);
            int sum = h4Dir + h1Dir;
            r.TrendDirection = sum > 0 ? TradeDirection.Buy : sum < 0 ? TradeDirection.Sell : TradeDirection.Neutral;
            r.Transition = h4Dir != 0 && h1Dir != 0 && h4Dir != h1Dir;

            double atrNow = Atr(_m15Bars, 14, m15);
            double atrBase = RollingAtrMean(_m15Bars, 14, m15, 120);
            r.AtrRatio = atrBase > 0 ? atrNow / atrBase : 1.0;
            r.AtrPercentile = AtrPercentile(_m15Bars, 14, m15, 120);
            r.Efficiency = EfficiencyRatio(_m15Bars.ClosePrices, m15, 20);
            r.AdxH1 = Adx(_h1Bars, 14, h1);
            r.AdxH4 = Adx(_h4Bars, 14, h4);
            double adxH1Prev = Adx(_h1Bars, 14, Math.Max(30, h1 - 4));
            r.AdxH1Slope = r.AdxH1 - adxH1Prev;
            r.TrendStrength = VClamp(((r.AdxH1 + r.AdxH4) * 0.5) / 40.0);
            double refEma = h1e50;
            double h1Atr = Atr(_h1Bars, 14, h1);
            r.ExtensionAtr = h1Atr > 0 ? Math.Abs(_h1Bars.ClosePrices[h1] - refEma) / h1Atr : 0;
            return r;
        }

        private HarmonicRoute RouteSignalV34(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            bool trendAligned = r.TrendDirection == s.Direction;
            bool trendOpposed = r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            bool strong = s.GeometryQuality >= .68 && s.PrzConfluence >= .68 && s.Confidence >= .64;
            bool exhaustion = trendOpposed && r.ExtensionAtr >= 1.20 && strong && r.AtrRatio <= 1.80;
            bool transition = conflict == MtfConflict.TRANSITION || r.Transition || r.TrendDirection == TradeDirection.Neutral;

            if ((conflict == MtfConflict.ALIGNED || conflict == MtfConflict.SUPPORTED || conflict == MtfConflict.NEUTRAL) &&
                trendAligned && r.Efficiency >= .18 && r.AtrRatio >= .55 && r.AtrRatio <= 1.75)
                return HarmonicRoute.TREND_ALIGNED_REVERSAL;

            if (exhaustion && (conflict != MtfConflict.CONFLICT || (s.GeometryQuality >= .75 && s.PrzConfluence >= .75)))
                return HarmonicRoute.EXHAUSTION_REVERSAL;

            if (transition && strong && r.AtrRatio >= .50 && r.AtrRatio <= 1.80)
                return HarmonicRoute.TRANSITION_REVERSAL;

            return HarmonicRoute.NO_TRADE;
        }


        private HarmonicRoute StructuredRecallRoute(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (s == null || r == null) return HarmonicRoute.NO_TRADE;
            if (conflict == MtfConflict.CONFLICT) return HarmonicRoute.NO_TRADE;
            if (s.GeometryQuality < RecallMinGeometry || s.PrzConfluence < RecallMinPrz || s.Confidence < RecallMinConfidence)
                return HarmonicRoute.NO_TRADE;
            if (r.AtrRatio < .55 || r.AtrRatio > 1.75 || r.Efficiency < .14)
                return HarmonicRoute.NO_TRADE;

            bool aligned = r.TrendDirection == s.Direction;
            bool opposed = r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            bool transition = r.Transition || conflict == MtfConflict.TRANSITION || r.TrendDirection == TradeDirection.Neutral;

            if (aligned && (conflict == MtfConflict.ALIGNED || conflict == MtfConflict.SUPPORTED || conflict == MtfConflict.NEUTRAL))
                return HarmonicRoute.TREND_ALIGNED_REVERSAL;

            if (opposed && r.ExtensionAtr >= 1.00 && r.AdxH1Slope <= .50)
                return HarmonicRoute.EXHAUSTION_REVERSAL;

            if (transition && r.AdxH1Slope <= 1.00)
                return HarmonicRoute.TRANSITION_REVERSAL;

            return HarmonicRoute.NO_TRADE;
        }

        private HarmonicRoute RouteSignal(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            HarmonicRoute baseRoute = RouteSignalV34(s, conflict, r);
            if (baseRoute == HarmonicRoute.NO_TRADE && EnableStructuredRecallExpansion)
            {
                baseRoute = StructuredRecallRoute(s, conflict, r);
                if (baseRoute != HarmonicRoute.NO_TRADE)
                {
                    _structuredRecallAdmitted++;
                    Print("[V54-RECALL-ADMIT] pattern={0} direction={1} route={2} conflict={3} geometry={4:F3} prz={5:F3} confidence={6:F3} efficiency={7:F3} atrRatio={8:F3} extensionAtr={9:F3}",
                        s.PatternName, s.Direction, baseRoute, conflict, s.GeometryQuality, s.PrzConfluence, s.Confidence,
                        r.Efficiency, r.AtrRatio, r.ExtensionAtr);
                }
            }
            if (baseRoute == HarmonicRoute.NO_TRADE)
                return HarmonicRoute.NO_TRADE;

            if (baseRoute == HarmonicRoute.TRANSITION_REVERSAL && EnableTransitionProofGate)
            {
                bool actualStructuralTransition = r.Transition || conflict == MtfConflict.TRANSITION;
                if (!actualStructuralTransition)
                {
                    _transitionProofRejected++;
                    Print("[V54-TRANSITION-PROOF-REJECT] pattern={0} conflict={1} transition={2} adxSlope={3:F2}",
                        s.PatternName, conflict, r.Transition, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            if (baseRoute == HarmonicRoute.TRANSITION_REVERSAL && EnableTransitionStateVeto)
            {
                bool actualStateDisagreement = r.Transition || conflict == MtfConflict.TRANSITION;
                bool trendNotStrengthening = r.AdxH1Slope <= 0;
                if (!(actualStateDisagreement && trendNotStrengthening))
                {
                    _regimeRejected++;
                    Print("[V54-ROUTE-VETO] type=TRANSITION_STATE conflict={0} transition={1} adxSlope={2:F2}",
                        conflict, r.Transition, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            if (baseRoute == HarmonicRoute.EXHAUSTION_REVERSAL && EnableExhaustionEvidenceVeto)
            {
                bool structurallyExtended = r.ExtensionAtr >= 1.20;
                bool trendNotStrengthening = r.AdxH1Slope <= 0;
                if (!(structurallyExtended && trendNotStrengthening))
                {
                    _regimeRejected++;
                    Print("[V54-ROUTE-VETO] type=EXHAUSTION_EVIDENCE extensionAtr={0:F3} adxSlope={1:F2}",
                        r.ExtensionAtr, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            return baseRoute;
        }

        private double HarmonicRobustnessScore(PatternSignal s)
        {
            if (s == null) return 0;
            return VClamp(.35 * s.GeometryQuality + .25 * s.PrzConfluence +
                          .20 * s.TimeSymmetry + .20 * s.PivotQuality);
        }

        private bool HarmonicRobustnessEligible(PatternSignal s, double score)
        {
            if (s == null) return false;
            if (score < MinHarmonicRobustness) return false;
            // Prevent a strong ratio fit from fully compensating for weak temporal/pivot structure.
            if (s.TimeSymmetry < .25 || s.PivotQuality < .25) return false;
            return true;
        }

        private double RegimeContextScore(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (s == null || r == null) return 0;
            double mtf = conflict == MtfConflict.ALIGNED ? 1.0 :
                         conflict == MtfConflict.SUPPORTED ? .85 :
                         conflict == MtfConflict.TRANSITION ? .65 :
                         conflict == MtfConflict.NEUTRAL ? .60 : .30;
            double directionFit = r.TrendDirection == s.Direction ? 1.0 :
                                  r.TrendDirection == TradeDirection.Neutral ? .65 : .35;
            double volHealth = 1.0 - Math.Min(1.0, Math.Abs(r.AtrPercentile - .55) / .55);
            double persistence = VClamp(.55 * r.Efficiency + .45 * r.TrendStrength);
            return VClamp(.30 * mtf + .25 * directionFit + .20 * volHealth + .25 * persistence);
        }

        private void ConversionTruth(string pattern, string stage)
        {
            if (string.IsNullOrWhiteSpace(pattern)) pattern = "UNKNOWN";
            if (string.IsNullOrWhiteSpace(stage)) stage = "UNKNOWN";
            string key = pattern + "::" + stage;
            int n; _conversionTruth.TryGetValue(key, out n); _conversionTruth[key] = n + 1;
        }

        private bool FamilyNativeQualificationPass(PatternSignal s, out double score, out string reason)
        {
            score = 0; reason = "UNKNOWN";
            if (s == null || s.Profile == null) { reason = "NULL"; return false; }
            string p = s.PatternName ?? "";
            bool retracement = p == "Gartley" || p == "Bat" || p == "Deep Gartley" || p == "Rat";
            bool extension = p == "Alt Bat" || p == "Butterfly" || p == "Crab" || p == "Deep Crab";
            if (p == "Shark" || p == "Cypher")
            {
                score = .50 * s.GeometryQuality + .50 * s.PrzConfluence;
                bool legacy = s.GeometryQuality >= Math.Max(MinGeometryQuality, s.Profile.MinGeometry) &&
                              s.PrzConfluence >= Math.Max(MinPrzConfluence, s.Profile.MinPrz);
                reason = legacy ? "PROVEN_LANE" : "PROVEN_LANE_FLOOR";
                return legacy;
            }
            double minG=.44, minP=.40, minScore=.56;
            if (retracement)
            {
                score=.36*s.GeometryQuality+.30*s.PrzConfluence+.16*s.TimeSymmetry+.18*s.PivotQuality;
                minG=.42; minP=.40; minScore=.56;
            }
            else if (extension)
            {
                score=.28*s.GeometryQuality+.37*s.PrzConfluence+.10*s.TimeSymmetry+.25*s.PivotQuality;
                minG=.38; minP=.35; minScore=.54;
            }
            else if (p == "5-0")
            {
                score=.30*s.GeometryQuality+.24*s.PrzConfluence+.16*s.TimeSymmetry+.30*s.PivotQuality;
                minG=.40; minP=.38; minScore=.55;
            }
            else
            {
                score=.40*s.GeometryQuality+.25*s.PrzConfluence+.15*s.TimeSymmetry+.20*s.PivotQuality;
                minG=.44; minP=.40; minScore=.56;
            }
            if (s.GeometryQuality < minG) { reason="GEOMETRY_FLOOR"; return false; }
            if (s.PrzConfluence < minP) { reason="PRZ_FLOOR"; return false; }
            if (score < minScore) { reason="JOINT_SCORE"; return false; }
            reason="PASS"; return true;
        }

        private OrthogonalContextFeatures BuildOrthogonalContextFeatureBus(PatternSignal s, RegimeSnapshot r)
        {
            var f=new OrthogonalContextFeatures();
            int m15=LastClosedIndex(_m15Bars), m1=LastClosedIndex(_m1Bars);
            double a0=Atr(_m15Bars,14,m15), a4=Atr(_m15Bars,14,Math.Max(30,m15-4));
            f.AtrExpansion=a4>0?VClamp(.5+.5*Math.Tanh((a0/a4-1.0)*3.0)):.5;
            var av=new List<double>();
            for(int k=0;k<12;k++){int q=m15-k;if(q<30)break;double x=Atr(_m15Bars,14,q);if(x>0)av.Add(x);}
            if(av.Count>2){double mean=av.Average();double variance=av.Sum(x=>(x-mean)*(x-mean))/av.Count;f.AtrVolOfVol=mean>0?Math.Sqrt(variance)/mean:0;}
            f.MicroEfficiency=m1>=25?EfficiencyRatio(_m1Bars.ClosePrices,m1,20):.5;
            int h1=LastClosedIndex(_h1Bars); double h1atr=Atr(_h1Bars,14,h1), minDist=double.MaxValue;
            for(int k=0;k<40&&h1-k>=1;k++){int q=h1-k;minDist=Math.Min(minDist,Math.Abs(s.D.Price-_h1Bars.HighPrices[q]));minDist=Math.Min(minDist,Math.Abs(s.D.Price-_h1Bars.LowPrices[q]));}
            f.HtfLiquidityDistanceAtr=h1atr>0&&minDist<double.MaxValue?minDist/h1atr:9;
            f.LiquidityProximity=VClamp(1.0-f.HtfLiquidityDistanceAtr/3.0);
            int lo=Math.Max(0,m15-63); double hiPx=double.MinValue,loPx=double.MaxValue;
            for(int q=lo;q<=m15;q++){hiPx=Math.Max(hiPx,_m15Bars.HighPrices[q]);loPx=Math.Min(loPx,_m15Bars.LowPrices[q]);}
            double range=Math.Max(hiPx-loPx,_symbol.PipSize),px=_m15Bars.ClosePrices[m15];
            f.RangeExtreme=s.Direction==TradeDirection.Buy?VClamp((hiPx-px)/range):VClamp((px-loPx)/range);
            f.Stability=VClamp(1.0-f.AtrVolOfVol/.40);
            return f;
        }

        private double FamilyContextScore(PatternSignal s, OrthogonalContextFeatures f, RegimeSnapshot r)
        {
            if(s==null||f==null)return .5;
            string p=s.PatternName??"";
            bool extension=p=="Alt Bat"||p=="Butterfly"||p=="Crab"||p=="Deep Crab";
            bool retracement=p=="Gartley"||p=="Bat"||p=="Deep Gartley"||p=="Rat";
            if(extension)return VClamp(.30*f.RangeExtreme+.25*f.LiquidityProximity+.20*f.AtrExpansion+.15*f.MicroEfficiency+.10*f.Stability);
            if(retracement)return VClamp(.25*f.MicroEfficiency+.25*f.Stability+.20*f.LiquidityProximity+.15*f.RangeExtreme+.15*f.AtrExpansion);
            if(p=="AB=CD")return VClamp(.30*f.MicroEfficiency+.20*f.Stability+.20*f.LiquidityProximity+.15*f.RangeExtreme+.15*f.AtrExpansion);
            return VClamp(.25*f.MicroEfficiency+.20*f.Stability+.20*f.LiquidityProximity+.20*f.RangeExtreme+.15*f.AtrExpansion);
        }

        private HarmonicRoute RouteSignalFamilyNativeV2(PatternSignal s, MtfConflict conflict, RegimeSnapshot r, OrthogonalContextFeatures f, double contextScore)
        {
            if(s==null||r==null)return HarmonicRoute.NO_TRADE;
            string p=s.PatternName??"";
            if(p=="Shark"||p=="Cypher")return RouteSignal(s,conflict,r);
            if(contextScore<.38)return HarmonicRoute.NO_TRADE;
            bool aligned=r.TrendDirection==s.Direction;
            bool opposed=r.TrendDirection!=TradeDirection.Neutral&&r.TrendDirection!=s.Direction;
            bool transition=r.Transition||conflict==MtfConflict.TRANSITION||r.TrendDirection==TradeDirection.Neutral;
            bool retracement=p=="Gartley"||p=="Bat"||p=="Deep Gartley"||p=="Rat";
            bool extension=p=="Alt Bat"||p=="Butterfly"||p=="Crab"||p=="Deep Crab";
            if(p=="AB=CD"){var q=RouteSignal(s,conflict,r);return q!=HarmonicRoute.NO_TRADE&&contextScore>=.44?q:HarmonicRoute.NO_TRADE;}
            if(extension)
            {
                if(conflict==MtfConflict.CONFLICT&&!(r.ExtensionAtr>=1.10&&contextScore>=.52))return HarmonicRoute.NO_TRADE;
                if(r.ExtensionAtr>=.65||(f!=null&&f.RangeExtreme>=.70))return HarmonicRoute.EXHAUSTION_REVERSAL;
                if(transition&&contextScore>=.44)return HarmonicRoute.TRANSITION_REVERSAL;
                return HarmonicRoute.NO_TRADE;
            }
            if(retracement)
            {
                if(aligned&&conflict!=MtfConflict.CONFLICT)return HarmonicRoute.TREND_ALIGNED_REVERSAL;
                if(transition&&contextScore>=.42)return HarmonicRoute.TRANSITION_REVERSAL;
                if(opposed&&(r.ExtensionAtr>=.80||(f!=null&&f.RangeExtreme>=.72)))return HarmonicRoute.EXHAUSTION_REVERSAL;
                return HarmonicRoute.NO_TRADE;
            }
            if(p=="5-0")
            {
                if(transition&&contextScore>=.42)return HarmonicRoute.TRANSITION_REVERSAL;
                if(opposed&&r.ExtensionAtr>=.70&&contextScore>=.42)return HarmonicRoute.EXHAUSTION_REVERSAL;
                return HarmonicRoute.NO_TRADE;
            }
            return RouteSignal(s,conflict,r);
        }

        private bool IsV54FamilyNativeConfirmationLane(string pattern)
        {
            return pattern=="Gartley"||pattern=="Bat"||pattern=="Alt Bat"||pattern=="Butterfly"||pattern=="Crab"||
                   pattern=="Deep Crab"||pattern=="Deep Gartley"||pattern=="Rat"||pattern=="5-0"||pattern=="AB=CD";
        }

        private int FamilyNativeConfirmationWindowLimit(string pattern)
        {
            if(pattern=="Crab"||pattern=="Deep Crab"||pattern=="Butterfly"||pattern=="Alt Bat")return 10;
            if(pattern=="5-0")return 10;
            if(pattern=="Deep Gartley"||pattern=="Rat")return 9;
            if(pattern=="Gartley"||pattern=="Bat")return 8;
            if(pattern=="AB=CD")return 7;
            return 6;
        }

        private bool UpdateFamilyNativeConfirmationV2(int i, CandidateRecord c, out double score)
        {
            score=0;if(i<3||i>=_m1Bars.Count||c==null||c.Signal==null)return false;
            var s=c.Signal;double o=_m1Bars.OpenPrices[i],cl=_m1Bars.ClosePrices[i],h=_m1Bars.HighPrices[i],l=_m1Bars.LowPrices[i];
            double pc=_m1Bars.ClosePrices[i-1],ph=_m1Bars.HighPrices[i-1],pl=_m1Bars.LowPrices[i-1];
            double body=Math.Max(Math.Abs(cl-o),_symbol.PipSize),prevBody=Math.Max(Math.Abs(_m1Bars.ClosePrices[i-1]-_m1Bars.OpenPrices[i-1]),_symbol.PipSize),atr=Atr(_m1Bars,14,i);
            bool buy=s.Direction==TradeDirection.Buy,directional=buy?cl>o:cl<o,reclaim=buy?(cl>s.PrzLow&&cl>=pc):(cl<s.PrzHigh&&cl<=pc),
                 bos=buy?cl>ph:cl<pl,rejection=buy?Math.Max(0,Math.Min(o,cl)-l)>=body*.45:Math.Max(0,h-Math.Max(o,cl))>=body*.45,
                 sweep=buy?l<pl:h>ph,failedExtension=buy?(l<pl&&cl>pl):(h>ph&&cl<ph),
                 insidePrz=cl>=Math.Min(s.PrzLow,s.PrzHigh)&&cl<=Math.Max(s.PrzLow,s.PrzHigh),displacement=atr>0&&body>=atr*.25,
                 retest=insidePrz||Math.Abs(cl-(s.PrzLow+s.PrzHigh)*.5)<=Math.Max(atr*.30,_symbol.PipSize),deceleration=body<=prevBody*.90;
            c.FamilyDirectional|=directional;c.FamilyReclaim|=reclaim;c.FamilyBos|=bos;c.FamilyRejection|=rejection;c.FamilySweep|=sweep;
            c.FamilyFailedExtension|=failedExtension;c.FamilyInsidePrz|=insidePrz;c.FamilyDisplacement|=displacement;c.FamilyRetest|=retest;c.FamilyDeceleration|=deceleration;
            string p=s.PatternName??"";bool retracement=p=="Gartley"||p=="Bat"||p=="Deep Gartley"||p=="Rat";bool extension=p=="Alt Bat"||p=="Butterfly"||p=="Crab"||p=="Deep Crab";
            if(retracement){score=(c.FamilyReclaim?.25:0)+((c.FamilyRejection||c.FamilyFailedExtension)?.20:0)+(c.FamilyBos?.20:0)+(c.FamilyDisplacement?.15:0)+(c.FamilyRetest?.10:0)+(c.FamilyDirectional?.10:0);return c.FamilyReclaim&&(c.FamilyRejection||c.FamilyFailedExtension)&&(c.FamilyBos||c.FamilyDisplacement)&&score>=.58;}
            if(extension){double sw=(p=="Crab"||p=="Deep Crab")?.10:.15;score=(c.FamilySweep?sw:0)+(c.FamilyFailedExtension?.25:0)+((c.FamilyReclaim||c.FamilyInsidePrz)?.20:0)+((c.FamilyBos||c.FamilyDisplacement)?.20:0)+(c.FamilyRetest?.10:0)+(c.FamilyDirectional?.10:0);bool terminal=(p=="Crab"||p=="Deep Crab")?(c.FamilySweep||c.FamilyInsidePrz):c.FamilySweep;return terminal&&c.FamilyFailedExtension&&(c.FamilyReclaim||c.FamilyInsidePrz)&&(c.FamilyBos||c.FamilyDisplacement)&&score>=.55;}
            if(p=="5-0"){score=(c.FamilyFailedExtension?.20:0)+(c.FamilyBos?.25:0)+(c.FamilyRetest?.20:0)+(c.FamilyDirectional?.15:0)+(c.FamilyDisplacement?.20:0);return c.FamilyFailedExtension&&c.FamilyBos&&c.FamilyRetest&&c.FamilyDirectional&&score>=.65;}
            if(p=="AB=CD"){score=(c.FamilyDeceleration?.15:0)+((c.FamilyRejection||c.FamilyFailedExtension)?.20:0)+(c.FamilyDirectional?.20:0)+((c.FamilyBos||c.FamilyDisplacement)?.25:0)+(c.FamilyReclaim?.20:0);return (c.FamilyDeceleration||c.FamilyRejection||c.FamilyFailedExtension)&&c.FamilyDirectional&&(c.FamilyBos||c.FamilyDisplacement)&&c.FamilyReclaim&&score>=.60;}
            return false;
        }

        private bool CapitalFeasibilityEligible(CandidateRecord c, out double minL0Risk, out double minL0Margin)
        {
            minL0Risk = 0;
            minL0Margin = 0;
            if (c == null || c.Signal == null || _symbol == null) return false;
            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            if ((c.Signal.Direction == TradeDirection.Buy && stop >= anchor) ||
                (c.Signal.Direction == TradeDirection.Sell && stop <= anchor))
                return false;

            double slPips = PriceToPips(Math.Abs(anchor - stop));
            if (slPips < MinStopLossPips) return false;
            double minVolume = _symbol.VolumeInUnitsMin;
            if (minVolume <= 0) return false;
            minL0Risk = minVolume * _symbol.PipValue * (slPips + ModeledCostPips());
            minL0Margin = EstimatedMargin(c.Signal.Direction, minVolume);
            double budget = Account.Equity * BasketRiskPercent / 100.0;
            if (minL0Risk > budget + 1e-8) return false;
            if (Account.FreeMargin - minL0Margin < budget * MinFreeMarginRiskMultiple) return false;
            return true;
        }

        private bool RouteSpecificM1EvidencePass(int i, PatternSignal s, HarmonicRoute route)
        {
            if (i < 3 || i >= _m1Bars.Count) return false;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);

            bool reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                reclaim = c > s.PrzLow && c >= pc;
                bos1 = c > ph1;
                bos2 = c > ph2;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl1 && c > pl1;
            }
            else
            {
                reclaim = c < s.PrzHigh && c <= pc;
                bos1 = c < pl1;
                bos2 = c < pl2;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph1 && c < ph1;
            }

            if (route == HarmonicRoute.TRANSITION_REVERSAL)
                return reclaim && bos2 && rejection;
            if (route == HarmonicRoute.EXHAUSTION_REVERSAL)
                return reclaim && rejection && (failedExtension || bos1);
            return reclaim && (bos1 || failedExtension);
        }

        private bool IsFamilyCompletionLane(string pattern)
        {
            return pattern == "Gartley" || pattern == "Bat" || pattern == "Alt Bat" ||
                   pattern == "Butterfly" || pattern == "Crab" || pattern == "Deep Crab" ||
                   pattern == "Deep Gartley" || pattern == "Rat" || pattern == "5-0";
        }

        private void IncrementCounter(Dictionary<string, int> map, string key)
        {
            if (string.IsNullOrWhiteSpace(key)) key = "UNKNOWN";
            int n; map.TryGetValue(key, out n); map[key] = n + 1;
        }

        private bool UpdateFamilyCompletionEvidence(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || i >= _m1Bars.Count || c == null || c.Signal == null) return false;
            var sig = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);
            bool buy = sig.Direction == TradeDirection.Buy;
            bool directional = buy ? cl > o : cl < o;
            bool reclaim = buy ? (cl > sig.PrzLow && cl >= pc) : (cl < sig.PrzHigh && cl <= pc);
            bool bos = buy ? cl > ph : cl < pl;
            bool rejection = buy ? Math.Max(0, Math.Min(o, cl) - l) >= body * .5 : Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
            bool sweep = buy ? l < pl : h > ph;
            bool failedExtension = buy ? (l < pl && cl > pl) : (h > ph && cl < ph);
            bool insidePrz = cl >= Math.Min(sig.PrzLow, sig.PrzHigh) && cl <= Math.Max(sig.PrzLow, sig.PrzHigh);
            bool displacement = atr > 0 && body >= atr * .30;
            bool retest = insidePrz || Math.Abs(cl - (sig.PrzLow + sig.PrzHigh) * .5) <= Math.Max(atr * .25, _symbol.PipSize);

            c.FamilyDirectional |= directional; c.FamilyReclaim |= reclaim; c.FamilyBos |= bos;
            c.FamilyRejection |= rejection; c.FamilySweep |= sweep; c.FamilyFailedExtension |= failedExtension;
            c.FamilyInsidePrz |= insidePrz; c.FamilyDisplacement |= displacement; c.FamilyRetest |= retest;

            string p = sig.PatternName ?? "";
            bool retracement = p == "Gartley" || p == "Bat" || p == "Deep Gartley" || p == "Rat";
            bool extension = p == "Alt Bat" || p == "Butterfly" || p == "Crab" || p == "Deep Crab";
            if (retracement)
            {
                score = (c.FamilyReclaim ? .30 : 0) + ((c.FamilyRejection || c.FamilyFailedExtension) ? .25 : 0) +
                        (c.FamilyBos ? .25 : 0) + (c.FamilyDisplacement ? .20 : 0);
                return c.FamilyReclaim && (c.FamilyRejection || c.FamilyFailedExtension) &&
                       (c.FamilyBos || c.FamilyDisplacement) && score >= .75;
            }
            if (extension)
            {
                score = (c.FamilySweep ? .20 : 0) + (c.FamilyFailedExtension ? .25 : 0) +
                        ((c.FamilyReclaim || c.FamilyInsidePrz) ? .25 : 0) +
                        (c.FamilyBos ? .20 : 0) + (c.FamilyDisplacement ? .10 : 0);
                return c.FamilySweep && c.FamilyFailedExtension && (c.FamilyReclaim || c.FamilyInsidePrz) &&
                       (c.FamilyBos || c.FamilyDisplacement) && score >= .75;
            }
            if (p == "5-0")
            {
                score = (c.FamilyFailedExtension ? .25 : 0) + (c.FamilyBos ? .30 : 0) +
                        (c.FamilyRetest ? .25 : 0) + (c.FamilyDirectional ? .20 : 0);
                return c.FamilyFailedExtension && c.FamilyBos && c.FamilyRetest && c.FamilyDirectional && score >= .80;
            }
            return false;
        }

        private bool UpdatePatternNativeM1State(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || c == null || c.Signal == null) return false;
            var s = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i], h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double prevBody = Math.Max(Math.Abs(_m1Bars.ClosePrices[i - 1] - _m1Bars.OpenPrices[i - 1]), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);
            bool bullish = s.Direction == TradeDirection.Buy;
            bool directional = bullish ? cl > o : cl < o;
            bool reclaim = bullish ? (cl > s.PrzLow && cl >= pc) : (cl < s.PrzHigh && cl <= pc);
            bool bos = bullish ? cl > ph : cl < pl;
            bool rejection = bullish ? Math.Max(0, Math.Min(o, cl) - l) >= body * .5 : Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
            bool failedExtension = bullish ? (l < pl && cl > pl) : (h > ph && cl < ph);
            bool sweep = bullish ? l < pl : h > ph;
            bool insidePrz = cl >= Math.Min(s.PrzLow, s.PrzHigh) && cl <= Math.Max(s.PrzLow, s.PrzHigh);
            bool displacement = atr > 0 && body >= atr * .30;
            bool deceleration = body <= prevBody * .85;
            bool retest = insidePrz || Math.Abs(cl - (s.PrzLow + s.PrzHigh) * .5) <= Math.Max(atr * .25, _symbol.PipSize);

            string p = s.PatternName ?? "";
            bool retracement = p == "Gartley" || p == "Bat" || p == "Deep Gartley" || p == "Rat";
            bool extension = p == "Alt Bat" || p == "Butterfly" || p == "Crab" || p == "Deep Crab";
            bool abcd = p == "AB=CD";
            bool transition = p == "Shark" || p == "5-0";
            bool cypher = p == "Cypher";

            if (retracement)
            {
                int prior = c.NativeStage;
                if (prior == 0 && rejection) c.NativeStage = 1;
                else if (prior == 1 && reclaim) c.NativeStage = 2;
                else if (prior == 2 && bos) c.NativeStage = 3;
                else if (prior == 3 && displacement) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (extension)
            {
                int prior = c.NativeStage;
                if (prior == 0 && sweep) c.NativeStage = 1;
                else if (prior == 1 && failedExtension) c.NativeStage = 2;
                else if (prior == 2 && insidePrz) c.NativeStage = 3;
                else if (prior == 3 && bos) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (abcd)
            {
                int prior = c.NativeStage;
                if (prior == 0 && deceleration) c.NativeStage = 1;
                else if (prior == 1 && failedExtension) c.NativeStage = 2;
                else if (prior == 2 && directional && displacement) c.NativeStage = 3;
                else if (prior == 3 && bos) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (transition)
            {
                int prior = c.NativeStage;
                if (prior == 0 && failedExtension) c.NativeStage = 1;
                else if (prior == 1 && bos) c.NativeStage = 2;
                else if (prior == 2 && retest) c.NativeStage = 3;
                else if (prior == 3 && directional) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (cypher)
            {
                int prior = c.NativeStage;
                if (prior == 0 && rejection) c.NativeStage = 1;
                else if (prior == 1 && reclaim) c.NativeStage = 2;
                else if (prior == 2 && bos) c.NativeStage = 3;
                else if (prior == 3 && displacement) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }

            score = 0;
            return false;
        }

        private bool UpdateM1TemporalEvidence(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || i >= _m1Bars.Count || c == null || c.Signal == null) return false;
            var s = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);

            bool directional, reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = cl > o;
                reclaim = cl > s.PrzLow && cl >= pc;
                bos1 = cl > ph1;
                bos2 = cl > ph2;
                rejection = Math.Max(0, Math.Min(o, cl) - l) >= body * .5;
                failedExtension = l < pl1 && cl > pl1;
            }
            else
            {
                directional = cl < o;
                reclaim = cl < s.PrzHigh && cl <= pc;
                bos1 = cl < pl1;
                bos2 = cl < pl2;
                rejection = Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
                failedExtension = h > ph1 && cl < ph1;
            }
            bool displacement = atr > 0 && body >= atr * .30;

            c.TemporalDirectional |= directional;
            c.TemporalReclaim |= reclaim;
            c.TemporalBos1 |= bos1;
            c.TemporalBos2 |= bos2;
            c.TemporalRejection |= rejection;
            c.TemporalFailedExtension |= failedExtension;
            c.TemporalDisplacement |= displacement;

            score = (c.TemporalDirectional ? .10 : 0) + (c.TemporalReclaim ? .20 : 0) +
                    (c.TemporalBos1 ? .20 : 0) + (c.TemporalBos2 ? .10 : 0) +
                    (c.TemporalRejection ? .15 : 0) + (c.TemporalFailedExtension ? .15 : 0) +
                    (c.TemporalDisplacement ? .10 : 0);

            if (c.Route == HarmonicRoute.EXHAUSTION_REVERSAL)
                return c.TemporalReclaim && c.TemporalRejection &&
                       (c.TemporalFailedExtension || c.TemporalBos1) && score >= .60;
            if (c.Route == HarmonicRoute.TRANSITION_REVERSAL)
                return c.TemporalReclaim && c.TemporalBos2 && c.TemporalRejection && score >= .65;
            return c.TemporalReclaim && (c.TemporalBos1 || c.TemporalFailedExtension) &&
                   c.TemporalDirectional && score >= .55;
        }

        private double EnhancedM1ConfirmationScore(int i, PatternSignal s, HarmonicRoute route, RegimeSnapshot regime)
        {
            if (i < 3 || i >= _m1Bars.Count) return 0;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);

            bool directional, reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = c > o;
                reclaim = c > s.PrzLow && c >= pc;
                bos1 = c > ph1;
                bos2 = c > ph2;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl1 && c > pl1;
            }
            else
            {
                directional = c < o;
                reclaim = c < s.PrzHigh && c <= pc;
                bos1 = c < pl1;
                bos2 = c < pl2;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph1 && c < ph1;
            }

            bool displacement = atr > 0 && body >= atr * .30;
            double score = (directional ? .15 : 0) + (reclaim ? .15 : 0) +
                           (bos1 ? .20 : 0) + (bos2 ? .15 : 0) +
                           (rejection ? .15 : 0) + (failedExtension ? .10 : 0) +
                           (displacement ? .10 : 0);

            // Counter-trend exhaustion requires actual rejection/structure evidence, not candle color alone.
            if (route == HarmonicRoute.EXHAUSTION_REVERSAL && !(rejection && (bos1 || failedExtension)))
                score = Math.Min(score, .55);
            return VClamp(score);
        }

        private double EnhancedM1Threshold(HarmonicRoute route)
        {
            return route == HarmonicRoute.EXHAUSTION_REVERSAL ? .70 :
                   route == HarmonicRoute.TRANSITION_REVERSAL ? .65 : .55;
        }

        private double DirectionalIndex(Bars bars, int period, int end)
        {
            if (bars == null || end < period + 1 || end >= bars.Count) return 0;
            double trSum = 0, plusSum = 0, minusSum = 0;
            int start = Math.Max(1, end - period + 1);
            for (int i = start; i <= end; i++)
            {
                double up = bars.HighPrices[i] - bars.HighPrices[i - 1];
                double down = bars.LowPrices[i - 1] - bars.LowPrices[i];
                double plusDm = up > down && up > 0 ? up : 0;
                double minusDm = down > up && down > 0 ? down : 0;
                double prevClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(bars.HighPrices[i] - bars.LowPrices[i],
                    Math.Max(Math.Abs(bars.HighPrices[i] - prevClose), Math.Abs(bars.LowPrices[i] - prevClose)));
                trSum += tr; plusSum += plusDm; minusSum += minusDm;
            }
            if (trSum <= 0) return 0;
            double plusDi = 100.0 * plusSum / trSum;
            double minusDi = 100.0 * minusSum / trSum;
            double den = plusDi + minusDi;
            return den > 0 ? 100.0 * Math.Abs(plusDi - minusDi) / den : 0;
        }

        private double Adx(Bars bars, int period, int end)
        {
            if (bars == null || end < period * 2 || end >= bars.Count) return 0;
            int start = Math.Max(period + 1, end - period + 1);
            double sum = 0; int n = 0;
            for (int i = start; i <= end; i++)
            {
                double dx = DirectionalIndex(bars, period, i);
                if (dx < 0) continue;
                sum += dx; n++;
            }
            return n > 0 ? sum / n : 0;
        }

        // ---------------- M1 confirmation / scheduler ----------------

        private bool BarTouchesPrz(int i, PatternSignal s)
        {
            if (i < 0 || i >= _m1Bars.Count) return false;
            return _m1Bars.HighPrices[i] >= s.PrzLow && _m1Bars.LowPrices[i] <= s.PrzHigh;
        }

        private double M1ConfirmationScore(int i, PatternSignal s)
        {
            if (i < 2 || i >= _m1Bars.Count) return 0;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i], h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double po = _m1Bars.OpenPrices[i - 1], pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);
            bool directional, reclaim, bos, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = c > o;
                reclaim = c > s.PrzLow && c >= pc;
                bos = c > ph;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl && c > pl;
            }
            else
            {
                directional = c < o;
                reclaim = c < s.PrzHigh && c <= pc;
                bos = c < pl;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph && c < ph;
            }
            return (directional ? .20 : 0) + (reclaim ? .20 : 0) + (bos ? .30 : 0) + (rejection ? .15 : 0) + (failedExtension ? .15 : 0);
        }

        private double CandidateRank(CandidateRecord c)
        {
            double mtf = c.Conflict == MtfConflict.ALIGNED ? 1.0 :
                         c.Conflict == MtfConflict.SUPPORTED ? .85 :
                         c.Conflict == MtfConflict.TRANSITION ? .70 :
                         c.Conflict == MtfConflict.NEUTRAL ? .60 : .40;
            double regime = VClamp(.45 * c.Regime.Efficiency + .25 * (1.0 - Math.Min(1.0, Math.Abs(c.Regime.AtrRatio - 1.0))) +
                                   .30 * Math.Min(1.0, c.Regime.ExtensionAtr / 2.0));
            double baseRank = .25 * c.Signal.GeometryQuality + .15 * c.Signal.PrzConfluence + .15 * mtf + .15 * regime +
                              .15 * c.ConfirmationScore + .15 * VClamp(c.NetRR / 3.0);
            if (!EnableFrequencyAgingPriority || CandidateAgeRankBoost <= 0) return baseRank;
            double ttl = Math.Max(60.0, (c.ExpiryUtc - c.DetectedUtc).TotalSeconds);
            double age = Math.Max(0.0, (Server.Time.ToUniversalTime() - c.DetectedUtc).TotalSeconds);
            double ageFrac = VClamp(age / ttl);
            return baseRank + CandidateAgeRankBoost * ageFrac;
        }

        private double CurrentSpreadPips()
        {
            return PriceToPips(Math.Max(0, _symbol.Ask - _symbol.Bid));
        }

        // ---------------- Risk / session / safety ----------------

        private bool IsInstitutionalSession(DateTime utc)
        {
            utc = DateTime.SpecifyKind(utc, DateTimeKind.Utc);
            DateTime londonLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _londonTz);
            DateTime nyLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _newYorkTz);
            DateTime londonOpenLocal = DateTime.SpecifyKind(londonLocal.Date.AddHours(8), DateTimeKind.Unspecified);
            DateTime nyCloseLocal = DateTime.SpecifyKind(nyLocal.Date.AddHours(17), DateTimeKind.Unspecified);
            DateTime londonOpenUtc = TimeZoneInfo.ConvertTimeToUtc(londonOpenLocal, _londonTz);
            DateTime nyCloseUtc = TimeZoneInfo.ConvertTimeToUtc(nyCloseLocal, _newYorkTz);
            return utc >= londonOpenUtc && utc < nyCloseUtc;
        }

        private TimeZoneInfo ResolveTimeZone(string iana, string windows)
        {
            try { return TimeZoneInfo.FindSystemTimeZoneById(iana); }
            catch { try { return TimeZoneInfo.FindSystemTimeZoneById(windows); } catch { return null; } }
        }

        private IEnumerable<Position> OwnPositions()
        {
            return Positions.Where(p => p.SymbolName == SymbolName && !string.IsNullOrWhiteSpace(p.Label) && p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal));
        }

        private void ResetDaily(bool force)
        {
            DateTime d = Server.Time.ToUniversalTime().Date;
            if (!force && d == _currentDay) return;
            _currentDay = d;
            _dayStartEquity = Account.Equity;
            _dailyLocked = false;
        }

        private void UpdateRiskLocks()
        {
            if (Account.Equity > _equityPeak) _equityPeak = Account.Equity;
            if (_dayStartEquity > 0)
            {
                double dd = 100.0 * (_dayStartEquity - Account.Equity) / _dayStartEquity;
                if (dd >= DailyLossLimitPercent) _dailyLocked = true;
            }
        }

        private bool PeakDrawdownExceeded()
        {
            if (_equityPeak <= 0) return false;
            return 100.0 * (_equityPeak - Account.Equity) / _equityPeak >= MaxDrawdownPercent;
        }

        private bool SpreadValid() { return SpreadPips() <= MaxSpreadPips; }
        private double SpreadPips() { return _symbol.PipSize > 0 ? (_symbol.Ask - _symbol.Bid) / _symbol.PipSize : 99999; }

        private void EnsureServerProtection()
        {
            foreach (var p in OwnPositions())
            {
                if (p.StopLoss.HasValue && p.TakeProfit.HasValue) continue;

                PositionLedger l;
                FibonacciBasket basket;
                if (!_positions.TryGetValue(p.Id, out l) ||
                    string.IsNullOrWhiteSpace(l.BasketId) ||
                    !_baskets.TryGetValue(l.BasketId, out basket))
                    continue;

                TradeType tt = p.TradeType;
                TradeDirection direction = tt == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;
                if (!BrokerStopDistanceValid(tt, basket.StructuralStop) || !BrokerTargetDistanceValid(tt, basket.CanonicalTarget))
                {
                    basket.ExitOverride = "SERVER_PROTECTION_DISTANCE_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    continue;
                }

                TradeResult rs = p.StopLoss.HasValue ? null : p.ModifyStopLossPrice(basket.StructuralStop);
                if (rs != null && !rs.IsSuccessful)
                {
                    RecordExecutionError("SERVER_SL_FAILED_" + rs.Error, "basket=" + basket.BasketId + ";position=" + p.Id);
                    basket.ExitOverride = "SERVER_PROTECTION_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    continue;
                }
                var live = Positions.FirstOrDefault(x => x.Id == p.Id);
                TradeResult rt = live != null && !live.TakeProfit.HasValue ? live.ModifyTakeProfitPrice(basket.CanonicalTarget) : null;
                if (rt != null && !rt.IsSuccessful)
                {
                    RecordExecutionError("SERVER_TP_FAILED_" + rt.Error, "basket=" + basket.BasketId + ";position=" + p.Id);
                    basket.ExitOverride = "SERVER_PROTECTION_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                }
            }
        }

        private void RecordExecutionError(string code, string detail)
        {
            _executionErrors++;
            if (string.IsNullOrWhiteSpace(code)) code = "UNKNOWN";
            int n;
            _executionErrorReasons.TryGetValue(code, out n);
            _executionErrorReasons[code] = n + 1;
            Print("[V54-EXECUTION-ERROR] code={0} detail={1}", code, detail ?? "");
        }

        private bool PendingOrderStillExists(long id)
        {
            return PendingOrders.Any(o => o.Id == id);
        }

        private bool PositionStillExists(long id)
        {
            return Positions.Any(p => p.Id == id);
        }

        private double BrokerMinimumDistancePrice(double referencePrice, bool stopLoss)
        {
            double d = stopLoss ? _symbol.MinStopLossDistance : _symbol.MinTakeProfitDistance;
            if (d <= 0) return 0;
            if (_symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return d * _symbol.PipSize;
            return Math.Abs(referencePrice) * d / 100.0;
        }

        private bool BrokerProtectionDistancesValid(TradeDirection direction, double entry, double stop, double target)
        {
            if (!GeometryValid(direction, entry, stop, target)) return false;
            double minSl = BrokerMinimumDistancePrice(entry, true);
            double minTp = BrokerMinimumDistancePrice(entry, false);
            return Math.Abs(entry - stop) + 1e-12 >= minSl &&
                   Math.Abs(target - entry) + 1e-12 >= minTp;
        }

        private bool BrokerStopDistanceValid(TradeType tradeType, double proposedStop)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double minSl = BrokerMinimumDistancePrice(reference, true);
            return tradeType == TradeType.Buy
                ? proposedStop < reference && reference - proposedStop + 1e-12 >= minSl
                : proposedStop > reference && proposedStop - reference + 1e-12 >= minSl;
        }

        // ---------------- Candidate state / telemetry ----------------

        private string BuildSetupGeometryKey(PatternSignal s)
        {
            if (s == null) return "INVALID";
            string px(double v) { return Math.Round(v, _symbol.Digits).ToString("F" + _symbol.Digits, CultureInfo.InvariantCulture); }
            return s.Direction + "|" + s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture) + "|" +
                   px(s.X.Price) + "|" + px(s.A.Price) + "|" + px(s.B.Price) + "|" + px(s.C.Price) + "|" + px(s.D.Price);
        }

        private string BuildFamilyHypothesisKey(PatternSignal s)
        {
            if (s == null) return "INVALID";
            return BuildSetupGeometryKey(s) + "|" + (s.PatternName ?? "UNKNOWN") + "|" + s.PivotScale.ToString(CultureInfo.InvariantCulture);
        }

        private string NewCandidateId(PatternSignal s)
        {
            _candidateSeq++;
            return "V54-" + _candidateSeq.ToString("D8", CultureInfo.InvariantCulture) + "-" +
                   s.PatternName.Replace(" ", "") + "-" + s.Direction + "-" + s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture);
        }

        private void Transition(CandidateRecord c, CandidateState next, string reason)
        {
            CandidateState prior = c.State;
            c.State = next;
            c.LastReason = reason;
            Event(c, prior + "->" + next + ":" + reason);
        }

        private void Reject(CandidateRecord c, string reason)
        {
            c.State = CandidateState.REJECTED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(string.IsNullOrWhiteSpace(c.IdentityKey) ? c.SetupKey : c.IdentityKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Rejected++;
            Event(c, "REJECTED:" + reason);
        }

        private void Expire(CandidateRecord c, string reason)
        {
            c.State = CandidateState.EXPIRED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(string.IsNullOrWhiteSpace(c.IdentityKey) ? c.SetupKey : c.IdentityKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Expired++;
            Event(c, "EXPIRED:" + reason);
        }

        private void Invalidate(CandidateRecord c, string reason)
        {
            c.State = CandidateState.INVALIDATED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(string.IsNullOrWhiteSpace(c.IdentityKey) ? c.SetupKey : c.IdentityKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Invalidated++;
            Event(c, "INVALIDATED:" + reason);
        }

        private void Ledger(CandidateRecord c, CandidateState state, string reason)
        {
            double wait = c.ParkedUtc.HasValue ? Math.Max(0, (Server.Time.ToUniversalTime() - c.ParkedUtc.Value).TotalMinutes) : 0;
            Print("[V54-EVENT] cid={0} setup={1} pattern={2} subtype={3} scale={4} tf={5} dir={6} state={7} route={8} conflict={9} waitMin={10:F2} reason={11}",
                c.CandidateId, c.SetupKey ?? "", c.Signal.PatternName, c.Signal.HarmonicSubtype ?? c.Signal.PatternName,
                c.Signal.PivotScale, c.Signal.Timeframe, c.Signal.Direction, state, c.Route, c.Conflict, wait, reason);
        }

        private void Event(CandidateRecord c, string reason)
        {
            Ledger(c, c.State, reason);
        }

        private PipelineCounter CountPipeline(string pattern)
        {
            PipelineCounter x;
            if (!_pipeline.TryGetValue(pattern, out x))
            {
                x = new PipelineCounter();
                _pipeline[pattern] = x;
            }
            return x;
        }

        private void TrimCandidateBook()
        {
            if (_candidates.Count <= 2000) return;
            foreach (var k in _candidates.Where(kv => !kv.Value.IsActive).OrderBy(kv => kv.Value.DetectedUtc).Take(_candidates.Count - 1500).Select(kv => kv.Key).ToList())
                _candidates.Remove(k);
        }

        private bool PatternInvalidatedBeforeEntry(PatternSignal s)
        {
            return s.Direction == TradeDirection.Buy ? _symbol.Bid <= s.StructuralInvalidation : _symbol.Ask >= s.StructuralInvalidation;
        }

        // ---------------- Math ----------------

        private bool BarsObjectsReady()
        {
            return _h4Bars != null && _h1Bars != null && _m15Bars != null && _m1Bars != null;
        }

        private void WarmupBars(Bars bars, int minimum, string name)
        {
            if (bars == null) return;
            int loops = 0;
            while (bars.Count < minimum && loops < 32)
            {
                int added = 0;
                try { added = bars.LoadMoreHistory(); }
                catch (Exception ex)
                {
                    Print("[V54-WARMUP-ERROR] tf={0} count={1} error={2}", name, bars.Count, ex.Message);
                    break;
                }
                loops++;
                Print("[V54-WARMUP] tf={0} added={1} count={2}", name, added, bars.Count);
                if (added <= 0) break;
            }
        }

        private bool BarsReady()
        {
            return BarsObjectsReady() && Count(_h4Bars) >= 230 && Count(_h1Bars) >= 230 && Count(_m15Bars) >= 360 && Count(_m1Bars) >= 50;
        }

        private int Count(Bars b) { return b == null ? 0 : b.Count; }
        private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }
        private double PriceToPips(double d) { return _symbol.PipSize > 0 ? d / _symbol.PipSize : 0; }
        private double PipsToPrice(double p) { return p * _symbol.PipSize; }
        private bool InRange(double x, double a, double b) { return x >= a && x <= b; }
        private double Mid(double a, double b) { return (a + b) / 2.0; }
        private double VClamp(double x) { return Math.Max(0, Math.Min(1, x)); }
        private double RatioScore(double x, double ideal) { return ideal <= 0 ? 0 : VClamp(1.0 - Math.Abs(x - ideal) / ideal); }
        private double Symmetry(double a, double b) { return a <= 0 || b <= 0 ? 0 : Math.Min(a, b) / Math.Max(a, b); }

        private bool GeometryValid(TradeDirection d, double entry, double sl, double tp)
        {
            return d == TradeDirection.Buy ? sl < entry && entry < tp : tp < entry && entry < sl;
        }

        private double Atr(Bars bars, int period, int end)
        {
            if (bars == null || end < period + 1 || end >= bars.Count) return 0;
            double sum = 0;
            for (int i = end - period + 1; i <= end; i++)
            {
                double h = bars.HighPrices[i], l = bars.LowPrices[i], pc = bars.ClosePrices[i - 1];
                sum += Math.Max(h - l, Math.Max(Math.Abs(h - pc), Math.Abs(l - pc)));
            }
            return sum / period;
        }

        private double RollingAtrMean(Bars bars, int period, int end, int lookback)
        {
            int start = Math.Max(period + 1, end - lookback + 1);
            double sum = 0; int n = 0;
            for (int i = start; i <= end; i++)
            {
                double a = Atr(bars, period, i);
                if (a > 0) { sum += a; n++; }
            }
            return n > 0 ? sum / n : 0;
        }

        private double AtrPercentile(Bars bars, int period, int end, int lookback)
        {
            double now = Atr(bars, period, end);
            if (now <= 0) return .5;
            int start = Math.Max(period + 1, end - lookback + 1), n = 0, below = 0;
            for (int i = start; i <= end; i++)
            {
                double a = Atr(bars, period, i);
                if (a <= 0) continue;
                n++; if (a <= now) below++;
            }
            return n > 0 ? (double)below / n : .5;
        }

        private double Ema(DataSeries s, int period, int end)
        {
            if (s == null || end <= 0 || end >= s.Count) return 0;
            int start = Math.Max(0, end - period * 6);
            double k = 2.0 / (period + 1.0), ema = s[start];
            for (int i = start + 1; i <= end; i++) ema = s[i] * k + ema * (1.0 - k);
            return ema;
        }

        private int TrendVote(double fast, double slow, double slope)
        {
            if (fast > slow && slope > 0) return 1;
            if (fast < slow && slope < 0) return -1;
            return 0;
        }

        private double EfficiencyRatio(DataSeries s, int end, int period)
        {
            if (s == null || end < period || end >= s.Count) return 0;
            double net = Math.Abs(s[end] - s[end - period]), path = 0;
            for (int i = end - period + 1; i <= end; i++) path += Math.Abs(s[i] - s[i - 1]);
            return path > 0 ? VClamp(net / path) : 0;
        }
    }

    public enum TradeDirection { Neutral, Buy, Sell }
    public enum HarmonicState { Neutral, Bullish, Bearish }
    public enum MtfConflict { NEUTRAL, ALIGNED, SUPPORTED, TRANSITION, CONFLICT }
    public enum HarmonicRoute { NO_TRADE, TREND_ALIGNED_REVERSAL, EXHAUSTION_REVERSAL, TRANSITION_REVERSAL }
    public enum CandidateState { DETECTED, VALIDATED, ROUTED, WAIT_PRZ, CONFIRMING, ARMED, SLOT_BLOCKED, PARKED, REVALIDATING, EXECUTABLE, EXECUTED, EXPIRED, REJECTED, INVALIDATED }
    public enum PatternMode { STANDARD, ABCD, CYPHER, SHARK, FIVEZERO }

    public sealed class PatternProfile
    {
        public string Name;
        public PatternMode Mode;
        public double XabMin, XabMax, AbcMin, AbcMax, BcdMin, BcdMax, XadMin, XadMax, AbcDMin, AbcDMax;
        public double PrzWidthAtr, StopBufferAtr, Target1Cd, Target2Cd;
        public int MaxAgeM15Bars;
        public double MinGeometry, MinPrz;
        public bool GridEnabled;
        public double[] GridFractions = new double[0];
        public int MaximumGridLegs;
        public double[] GridRiskWeights = new double[0];
        public string GridAnchorRule;
        public double MinimumGridSpanXa, MaximumGridSpanXa, GridStructuralTolerance, StructuralStopFibBuffer;
        public int PendingTtlMinutes;
        public string CanonicalTargetPolicy;
    }

    public sealed class PivotSequence
    {
        public PivotPoint X, A, B, C, D;
    }

    public sealed class PivotPoint
    {
        public int Index;
        public double Price;
        public bool IsHigh;
    }

    public sealed class PatternSignal
    {
        public string PatternName;
        public PatternProfile Profile;
        public TradeDirection Direction;
        public PivotPoint X, A, B, C, D;
        public int PivotScale;
        public double Xab, Abc, Bcd, Xad, AdXa, XdXa, AbCd;
        public string HarmonicSubtype;
        public double PrzLow, PrzHigh;
        public double GeometryQuality, PrzConfluence, TimeSymmetry, PivotQuality, Confidence;
        public double StructuralInvalidation, CanonicalTarget1, CanonicalTarget2;
        public DateTime CompletionTime;
        public string Timeframe;
    }

    public sealed class RegimeSnapshot
    {
        public TradeDirection TrendDirection;
        public bool Transition;
        public double AtrRatio;
        public double AtrPercentile;
        public double Efficiency;
        public double ExtensionAtr;
        public double AdxH1;
        public double AdxH4;
        public double AdxH1Slope;
        public double TrendStrength;
    }

    public sealed class OrthogonalContextFeatures
    {
        public double AtrExpansion, AtrVolOfVol, MicroEfficiency, HtfLiquidityDistanceAtr, LiquidityProximity, RangeExtreme, Stability;
    }

    public sealed class CandidateRecord
    {
        public string CandidateId;
        public string SetupKey;
        public string IdentityKey;
        public PatternSignal Signal;
        public CandidateState State;
        public bool IsActive = true;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc;
        public MtfConflict Conflict = MtfConflict.NEUTRAL;
        public HarmonicRoute Route = HarmonicRoute.NO_TRADE;
        public RegimeSnapshot Regime;
        public OrthogonalContextFeatures Context;
        public string AlphaLane = "LEGACY";
        public bool IsProvenCoreAlpha;
        public double ConfirmationScore, NetRR, SelectedTarget, Rank;
        public double AlphaQualityScore, RegimeScore, ContextScore, FamilyQualificationScore, EconomicQualityScore, CapitalMinL0Risk, CapitalMinL0Margin;
        public int RescueBarsObserved;
        public double RescueBestScore;
        public DateTime? ArmedUtc, ParkedUtc, ParkedHardExpiryUtc;
        public bool ArmedGraceApplied, WasParked, OpportunityTerminalLogged;
        public int NativeM1BarsObserved, NativeStage;
        public int FamilyConfirmationBarsObserved;
        public bool FamilyDirectional, FamilyReclaim, FamilyBos, FamilyRejection, FamilySweep,
                    FamilyFailedExtension, FamilyInsidePrz, FamilyDisplacement, FamilyRetest, FamilyDeceleration;
        public double OriginalRank, OriginalGeometry, OriginalPrzConfluence, OriginalM1Evidence, OriginalEntryAnchor, ShadowRiskDistance, ShadowMfeR, ShadowMaeR;
        public double CompletionAnchorPrice, NativeConfirmAnchorPrice, NativeRetestAnchorPrice;
        public double CompletionAnchorMfeR, CompletionAnchorMaeR, NativeConfirmMfeR, NativeConfirmMaeR, NativeRetestMfeR, NativeRetestMaeR;
        public bool TemporalDirectional, TemporalReclaim, TemporalBos1, TemporalBos2, TemporalRejection, TemporalFailedExtension, TemporalDisplacement;
        public bool CapitalFeasible;
        public FibonacciGridPlan GridPlan;
        public long PositionId;
        public string LastReason;
    }

    public sealed class PositionLedger
    {
        public long PositionId;
        public string CandidateId;
        public string PatternName;
        public HarmonicRoute Route;
        public TradeDirection Direction;
        public DateTime EntryUtc;
        public double InitialRiskPips;
        public double RiskAmount;
        public double PeakR;
        public double MaxAdverseR;
        public string ExitOverride;
        public string BasketId;
        public int LegIndex;
    }

    public enum GridLegState { PLANNED, SUBMITTING, SUBMITTED, FILLED_UNVERIFIED, PROTECTED, VIRTUAL_ONLY, VIRTUAL_FILLED, FAIL_CLOSED, CANCELLED, EXPIRED, REJECTED, RISK_REJECTED }
    public enum FibonacciBasketState { PLANNED, LEG0_EXECUTED, GRID_PENDING, PARTIALLY_FILLED, BASKET_ACTIVE, BASKET_PROTECTED, CLOSED, CANCELLED, EXPIRED, INVALIDATED, RISK_REJECTED, MARGIN_REJECTED, SESSION_EXPIRED }

    public sealed class FibonacciGridLeg
    {
        public int Index;
        public double Fraction, PlannedPrice, RiskWeight, RiskBudget, Volume, PlannedRisk, ModeledCost, MinBrokerRisk;
        public long PendingOrderId, PositionId;
        public bool Physical, FillCounted;
        public GridLegState State;
    }

    public sealed class FibonacciGridPlan
    {
        public string CandidateId, BasketId, Pattern;
        public TradeDirection Direction;
        public HarmonicRoute Route;
        public DateTime CreatedUtc, ExpirationUtc;
        public double EntryAnchor, StructuralStop, GridDistance, CanonicalTarget, ExpectedWeightedEntry;
        public double BasketRiskAmount, WorstCaseRisk, ExpectedNetRR, VirtualWeightedEntry, EstimatedPhysicalMargin;
        public int LogicalLegCount, PhysicalDepth;
        public bool MicroCapitalMode;
        public readonly List<FibonacciGridLeg> Legs = new List<FibonacciGridLeg>();
    }

    public sealed class FibonacciBasket
    {
        public string BasketId, CandidateId, Pattern, ExitOverride, ExitReason, AlphaLane = "LEGACY";
        public TradeDirection Direction;
        public HarmonicRoute Route;
        public FibonacciBasketState State;
        public DateTime CreatedUtc, ExpirationUtc;
        public double EntryAnchor, AverageEntry, StructuralStop, CanonicalTarget;
        public double InitialBasketRisk, PlannedWorstCaseRisk, PeakR, MaxAdverseR, RealizedNet, ProtectionFrontier, EconomicQualityScore;
        public int FilledLegs, ClosedLegs;
        public bool IsActive;
        public FibonacciGridPlan Plan;
        public CandidateRecord Candidate;
    }

    public sealed class PipelineCounter
    {
        public long Detected, Validated, Routed, PrzWaiting, Confirming, NativeTemporalPass, Armed, SlotBlocked, Parked, Revalidated, RevalidationRejected, BasketPlanned;
        public long Leg0Executed, Leg1Filled, Leg2Filled, Leg3Filled, BasketClosed;
        public long Executed, Expired, Rejected, Invalidated;
    }
}
