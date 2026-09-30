using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBotV71 : Robot
    {
        private const string Version = "HarmonyBot V71 — Protected Champion Core & Incremental Cross-Fit Expansion";
        private const string BotPrefix = "HB71";
        private const string V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01";

        [Parameter("Symbol", DefaultValue = "XAUUSD")]
        public new string SymbolName { get; set; }

        [Parameter("Trading Enabled", DefaultValue = true)]
        public bool TradingEnabled { get; set; }

        [Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]
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

        [Parameter("V71 Expansion Shadow", DefaultValue = false)]
        public bool EnableV71ExpansionShadow { get; set; }

        [Parameter("V71 Expansion Execution", DefaultValue = false)]
        public bool EnableV71ExpansionExecution { get; set; }

        [Parameter("V71 Expansion Grid", DefaultValue = false)]
        public bool EnableV71ExpansionGrid { get; set; }

        [Parameter("V71 Expansion Adaptive Risk", DefaultValue = false)]
        public bool EnableV71ExpansionAdaptiveRisk { get; set; }

        [Parameter("V71 Expansion Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]
        public double V71ExpansionRiskPercent { get; set; }

        [Parameter("V71 Expansion Max Candidates", DefaultValue = 24, MinValue = 8, MaxValue = 32)]
        public int V71ExpansionMaxCandidates { get; set; }

        [Parameter("V71 Family-Balanced Census", DefaultValue = true)]
        public bool EnableV71FamilyBalancedCensus { get; set; }

        [Parameter("V71 Per-Family Census Cap", DefaultValue = 6, MinValue = 2, MaxValue = 12)]
        public int V71PerFamilyCensusCap { get; set; }

        [Parameter("V71 AB=CD Census Share %", DefaultValue = 15, MinValue = 0, MaxValue = 25)]
        public int V71AbcdCensusSharePercent { get; set; }

        [Parameter("V71 Full Family Pivot Lattice", DefaultValue = true)]
        public bool EnableV71FullFamilyPivotLattice { get; set; }

        [Parameter("V71 Family-Native Confirmation", DefaultValue = true)]
        public bool EnableV71FamilyNativeConfirmation { get; set; }

        [Parameter("V71 Expansion TTL M15", DefaultValue = 16, MinValue = 4, MaxValue = 32)]
        public int V71ExpansionTtlM15Bars { get; set; }

        [Parameter("V71 Expansion Shadow Horizon M1", DefaultValue = 180, MinValue = 30, MaxValue = 720)]
        public int V71ExpansionShadowHorizonM1Bars { get; set; }

        [Parameter("V71 Edge Model Spec", DefaultValue = "")]
        public string V71EdgeModelSpec { get; set; }

        [Parameter("V71 Family Route Prior Spec", DefaultValue = "")]
        public string V71FamilyRoutePriorSpec { get; set; }

        [Parameter("V71 Allowed Family Route Spec", DefaultValue = "")]
        public string V71AllowedFamilyRouteSpec { get; set; }

        [Parameter("V71 Allowed Family Route Context Spec", DefaultValue = "")]
        public string V71AllowedFamilyRouteContextSpec { get; set; }

        [Parameter("V71 Allowed Setup Hash Spec", DefaultValue = "")]
        public string V71AllowedSetupHashSpec { get; set; }

        [Parameter("V71 Expansion Exit Policy", DefaultValue = "REACTION_2R")]
        public string V71ExpansionExitPolicy { get; set; }

        [Parameter("Enable V72 Reaction Alpha", DefaultValue = false)]
        public bool EnableV72ReactionAlpha { get; set; }

        [Parameter("V71 Edge LCB Margin", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 2.0)]
        public double V71EdgeLcbMargin { get; set; }

        [Parameter("V71 Expansion Min Edge LCB R", DefaultValue = 0.015, MinValue = 0.0, MaxValue = 1.0)]
        public double V71ExpansionMinEdgeLcbR { get; set; }

        [Parameter("V71 Model ID", DefaultValue = "NONE")]
        public string V71ModelId { get; set; }

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

        private readonly Dictionary<string, V71ExpansionCandidate> _v71Expansion = new Dictionary<string, V71ExpansionCandidate>();
        private readonly HashSet<string> _v71ExpansionExecutedSetupKeys = new HashSet<string>();
        private readonly Dictionary<string, double> _v71EdgeWeights = new Dictionary<string, double>();
        private readonly Dictionary<string, double> _v71FamilyRoutePriors = new Dictionary<string, double>();
        private readonly HashSet<string> _v71AllowedFamilyRoutes = new HashSet<string>(StringComparer.Ordinal);
        private readonly HashSet<string> _v71AllowedFamilyRouteContexts = new HashSet<string>(StringComparer.Ordinal);
        private readonly HashSet<uint> _v71AllowedSetupHashes = new HashSet<uint>();
        private readonly Dictionary<string, int> _v71FamilyTracked = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71FamilyArmed = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71FamilyCoreOverlap = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71FamilyShadowClosed = new Dictionary<string, int>();
        // Root-cause proof ledger. These counters are Shadow/research only and never
        // participate in Capital selection or V51 Core decisions.
        private readonly Dictionary<string, int> _v71ExpansionRejectAttribution = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71OracleExpected = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71OracleMatched = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _v71OracleMissed = new Dictionary<string, int>();
        private readonly Dictionary<int, int> _v71OracleLastDIndexByScale = new Dictionary<int, int>();
        private readonly HashSet<string> _v71OracleSeen = new HashSet<string>(StringComparer.Ordinal);
        private bool _v71ModelReady;
        private int _v71ExpansionDetected;
        private int _v71ExpansionArmed;
        private int _v71ExpansionExecuted;
        private int _v71ExpansionCoreBlocked;
        private int _v71ExpansionModelRejected;
        private int _v71ExpansionGridFallback;
        private int _v71ExpansionShadowClosed;
        private int _v71ExpansionRiskScaled;
        private int _v71ExpansionRiskReserveBlocked;
        private int _v71ExpansionRiskCapped;
        private double _v71ExpansionRealizedNet;
        private ulong _v71CoreExecutionFnv = 14695981039346656037UL;
        private int _v71CoreExecutionCount;

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
                Print("[V51-FATAL] SYMBOL_NOT_FOUND {0}", SymbolName);
                Stop();
                return;
            }

            _h4Bars = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _m1Bars = MarketData.GetBars(TimeFrame.Minute, SymbolName);

            if (!BarsObjectsReady())
            {
                Print("[V51-FATAL] TIMEFRAME_OBJECT_LOAD_FAILED");
                Stop();
                return;
            }

            WarmupBars(_h4Bars, 230, "H4");
            WarmupBars(_h1Bars, 230, "H1");
            WarmupBars(_m15Bars, 360, "M15");
            WarmupBars(_m1Bars, 120, "M1");

            if (!BarsReady())
                Print("[V51-WARMUP-PENDING] H4={0} H1={1} M15={2} M1={3}",
                    Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars));

            _londonTz = ResolveTimeZone("Europe/London", "GMT Standard Time");
            _newYorkTz = ResolveTimeZone("America/New_York", "Eastern Standard Time");
            if (_londonTz == null || _newYorkTz == null)
            {
                Print("[V51-FATAL] DST_TIMEZONE_UNAVAILABLE");
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
            V71ParseEdgeModel();
            _initialEquity = Account.Equity;
            _initialCapitalEligible = _initialEquity + 1e-8 >= MinimumSupportedEquity;
            _equityPeak = Account.Equity;
            ResetDaily(true);

            Positions.Closed += OnPositionClosed;
            Positions.Opened += OnPositionOpened;
            PendingOrders.Filled += OnPendingOrderFilled;

            PrintBrokerCapabilityProfile();

            Print("[V51-START] version={0} symbol={1} H4={2} H1={3} M15={4} M1={5} profiles={6}",
                Version, SymbolName, Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars), _profiles.Count);
            Print("[V51-TIMEFRAME-AUDIT] primaryPattern=M15 execution=M1 macro=H4 intermediate=H1 allCompletedBars=true");
            Print("[V51-SESSION-AUDIT] london={0} newYork={1} dstAware=true", _londonTz.Id, _newYorkTz.Id);
            Print("[V51-ALPHA-CONFIG] qualityObservation={0} legacyRegime={1} legacyEnhancedM1={2} capitalFeasibility={3} transitionVeto={4} exhaustionVeto={5} routeM1Veto={6}",
                EnableHarmonicRobustnessGate, EnableRegimeContextGate, EnableEnhancedM1Confirmation, EnableCapitalFeasibilityGate,
                EnableTransitionStateVeto, EnableExhaustionEvidenceVeto, EnableRouteSpecificM1Veto);
            Print("[V51-FREQUENCY-CONFIG] deferredRetention={0} agingPriority={1} ageBoost={2:F3} structuredRecall={3} recallGeometry={4:F3} recallPrz={5:F3} recallConfidence={6:F3}",
                EnableDeferredCandidateRetention, EnableFrequencyAgingPriority, CandidateAgeRankBoost, EnableStructuredRecallExpansion,
                RecallMinGeometry, RecallMinPrz, RecallMinConfidence);
            Print("[V51-RESTORED-KERNEL] canonicalSetup={0} canonicalStandard={1} independentPivotGraph={2} transitionProof={3} m1Rescue={4} rescueBars={5} diversityScheduler={6} executionClock=M1 projectedD=false",
                EnableCanonicalSetupIdentity, EnableCanonicalStandardCoordinates, EnableIndependentPivotGraph,
                EnableTransitionProofGate, EnableM1RescueLane, M1RescueMaxBars, EnableDiversityScheduler);
            Print("[V51-CONVERSION-ARCH] scaleRouteAdmission={0} temporalRescue={1} armedGrace={2} graceMinutes={3} preExecutionRevalidation={4}",
                EnableScaleRouteAdmission, EnableM1TemporalRescue, EnableArmedExecutionGrace, ArmedGraceMinutes,
                EnablePreExecutionGridRevalidation);
            Print("[V51-FAMILY-NATIVE] conversion={0} observation={1} principle=PATTERN_IDENTITY_NEQ_EXECUTION_IDENTITY", EnableFamilyNativeConversion, EnableFamilyNativeObservation);
            Print("[V51-COMPLETION-CONTRACT] canonicalContracts={0} familyCompletion={1} windowBars={2} provenLane=ABCD_SHARK_CYPHER_FROZEN",
                EnableCanonicalFamilyContracts, EnableFamilyCompletionContract, FamilyConfirmationWindowBars);
            Print("[V51-STRUCTURAL-GRID-CONTRACT] gridSpanV2={0} structuralInvalidationV2={1} rule=PRZ_LEGALITY_PLUS_RISK_RR_NOT_LEGACY_XA_MINSPAN",
                EnableGridSpanSemanticV2, EnableStructuralInvalidationV2);
            Print("[V51-MATH-GEOMETRY] jointGeometry={0} executionCorridor={1} entryAnchorForensics={2} rule=FAMILY_NATIVE_GEOMETRY_WITHOUT_RISK_RELAXATION",
                EnableFamilyNativeJointGeometry, EnableFamilyNativeExecutionCorridor, EnableEntryAnchorForensics);
            Print("[V51-THROUGHPUT-ARCH] persistentQueue={0} serialHandoff={1} nativeM1={2} nativeBars={3} decayRanking={4} hardLifetimeMinutes={5} alphaKernel=V46_SCALE_CONVERSION_FROZEN",
                EnablePersistentArmedQueue, EnableEventDrivenSerialHandoff, EnablePatternNativeM1Expansion,
                PatternNativeM1MaxBars, EnableOpportunityDecayRanking, ParkedHardLifetimeMinutes);
            Print("[V71-PROTECTED-CORE] trustedParent={0} expansionShadow={1} expansionExecution={2} expansionGrid={3} expansionAdaptiveRisk={4} expansionRiskCap={5:F2} model={6} modelReady={7}",
                V51TrustedParent, EnableV71ExpansionShadow, EnableV71ExpansionExecution, EnableV71ExpansionGrid,
                EnableV71ExpansionAdaptiveRisk, Math.Min(5.0, V71ExpansionRiskPercent), V71ModelId, _v71ModelReady);
            Print("[V71-INCREMENTAL-POLICY] corePreemption=true minEdgeLcbR={0:F3} familyBalancedCensus={1} perFamilyCap={2} abcdSharePct={3} allowedFamilyRoutes={4} fullPivotLattice={5} familyNativeConfirmation={6} overlapShadowVisible=true overlapCapitalBlocked=true",
                Math.Max(0, V71ExpansionMinEdgeLcbR), EnableV71FamilyBalancedCensus,
                Math.Max(2, Math.Min(12, V71PerFamilyCensusCap)), Math.Max(0, Math.Min(25, V71AbcdCensusSharePercent)),
                _v71AllowedFamilyRoutes.Count, EnableV71FullFamilyPivotLattice, EnableV71FamilyNativeConfirmation);
        }

        protected override void OnStop()
        {
            V71FinalizeExpansionShadows();
            CancelAllOwnPending("BOT_STOP");
            EnsureServerProtection();
            Positions.Closed -= OnPositionClosed;
            Positions.Opened -= OnPositionOpened;
            PendingOrders.Filled -= OnPendingOrderFilled;
            foreach (var kv in _pipeline.OrderBy(k => k.Key))
            {
                var x = kv.Value;
                Print("[V51-PIPELINE] pattern={0} detected={1} validated={2} routed={3} prz={4} confirming={5} nativeTemporalPass={6} armed={7} slotBlocked={8} parked={9} revalidated={10} revalidationRejected={11} basketPlanned={12} leg0={13} leg1={14} leg2={15} leg3={16} basketClosed={17} executed={18} expired={19} rejected={20} invalidated={21}",
                    kv.Key, x.Detected, x.Validated, x.Routed, x.PrzWaiting, x.Confirming, x.NativeTemporalPass, x.Armed,
                    x.SlotBlocked, x.Parked, x.Revalidated, x.RevalidationRejected, x.BasketPlanned,
                    x.Leg0Executed, x.Leg1Filled, x.Leg2Filled, x.Leg3Filled, x.BasketClosed, x.Executed, x.Expired, x.Rejected, x.Invalidated);
            }
            if (EnableEntryAnchorForensics)
            {
                foreach (var c in _candidates.Values.Where(x => x.Signal != null && x.CompletionAnchorPrice > 0).OrderBy(x => x.CandidateId))
                {
                    Print("[V51-ENTRY-ANCHOR-FORENSICS] cid={0} setup={1} pattern={2} route={3} scale={4} completion={5} confirm={6} retest={7} completionMfeR={8:F3} completionMaeR={9:F3} confirmMfeR={10:F3} confirmMaeR={11:F3} retestMfeR={12:F3} retestMaeR={13:F3}",
                        c.CandidateId, c.SetupKey, c.Signal.PatternName, c.Route, c.Signal.PivotScale,
                        c.CompletionAnchorPrice, c.NativeConfirmAnchorPrice, c.NativeRetestAnchorPrice,
                        c.CompletionAnchorMfeR, c.CompletionAnchorMaeR, c.NativeConfirmMfeR, c.NativeConfirmMaeR,
                        c.NativeRetestMfeR, c.NativeRetestMaeR);
                }
            }
            Print("[V51-SUMMARY] candidates={0} baskets={1} openLedgers={2} executionErrors={3} gridRiskViolations={4} duplicateGridLegs={5} orphanPendingOrders={6} stopWideningViolations={7} gapThroughInvalidations={8} gapThroughSurvivors={9} unprotectedSurvivors={10} postFillProtectionFailures={11} actualBasketRiskViolations={12} executionStateViolations={13} virtualGridFills={14} microModeBaskets={15} capitalRejectedBaskets={16} marginRiskViolations={17}",
                _candidateSeq, _baskets.Count, _positions.Count, _executionErrors, _gridRiskViolations, _duplicateGridLegs, _orphanPendingOrders, _stopWideningViolations,
                _gapThroughInvalidations, _gapThroughSurvivors, _unprotectedSurvivors, _postFillProtectionFailures, _actualBasketRiskViolations, _executionStateViolations,
                _virtualGridFills, _microModeBaskets, _capitalRejectedBaskets, _marginRiskViolations);
            Print("[V51-ALPHA-SUMMARY] qualityRejected={0} regimeRejected={1} confirmationRejected={2} capitalInfeasible={3} alphaPassed={4}",
                _alphaQualityRejected, _regimeRejected, _confirmationRejected, _capitalInfeasibleCandidates, _alphaPassed);
            Print("[V71-EXPANSION-SUMMARY] detected={0} armed={1} executed={2} coreBlocked={3} modelRejected={4} gridFallback={5} shadowClosed={6} riskScaled={7} active={8} model={9}",
                _v71ExpansionDetected, _v71ExpansionArmed, _v71ExpansionExecuted, _v71ExpansionCoreBlocked,
                _v71ExpansionModelRejected, _v71ExpansionGridFallback, _v71ExpansionShadowClosed,
                _v71ExpansionRiskScaled, _v71Expansion.Values.Count(x => x.IsActive), V71ModelId);
            foreach (var fam in _profiles.Select(x => V71FamilyKey(x.Name)).Distinct().OrderBy(x => x))
            {
                int tracked = _v71FamilyTracked.ContainsKey(fam) ? _v71FamilyTracked[fam] : 0;
                int armed = _v71FamilyArmed.ContainsKey(fam) ? _v71FamilyArmed[fam] : 0;
                int overlap = _v71FamilyCoreOverlap.ContainsKey(fam) ? _v71FamilyCoreOverlap[fam] : 0;
                int closed = _v71FamilyShadowClosed.ContainsKey(fam) ? _v71FamilyShadowClosed[fam] : 0;
                Print("[V71-FAMILY-CENSUS] family={0} tracked={1} armed={2} coreOverlap={3} shadowClosed={4}",
                    fam, tracked, armed, overlap, closed);

                int expected = _v71OracleExpected.ContainsKey(fam) ? _v71OracleExpected[fam] : 0;
                int matched = _v71OracleMatched.ContainsKey(fam) ? _v71OracleMatched[fam] : 0;
                int missed = _v71OracleMissed.ContainsKey(fam) ? _v71OracleMissed[fam] : 0;
                double recall = expected > 0 ? (double)matched / expected : 1.0;
                Print("[V71-ORACLE-CENSUS] family={0} expected={1} matched={2} missed={3} recall={4:F6}",
                    fam, expected, matched, missed, recall);
            }
            foreach (var kv in _v71ExpansionRejectAttribution.OrderBy(x => x.Key))
            {
                string[] parts = kv.Key.Split('|');
                string fam = parts.Length > 0 ? parts[0] : "UNKNOWN";
                string reason = parts.Length > 1 ? parts[1] : "UNKNOWN";
                Print("[V71-EXP-REJECT-SUMMARY] family={0} reason={1} count={2}", fam, reason, kv.Value);
            }
            int oracleExpected = _v71OracleExpected.Values.Sum();
            int oracleMatched = _v71OracleMatched.Values.Sum();
            int oracleMissed = _v71OracleMissed.Values.Sum();
            Print("[V71-ORACLE-SUMMARY] expected={0} matched={1} missed={2} perfectRecall={3}",
                oracleExpected, oracleMatched, oracleMissed, oracleMissed == 0);
            Print("[V71-CORE-PRESERVATION] executed={0} fnv64={1:X16}", _v71CoreExecutionCount, _v71CoreExecutionFnv);
            Print("[V71-PROTECTED-RISK-SUMMARY] expansionNet={0:F2} reserveBlocked={1} riskCapped={2} coreRiskPct={3:F2}",
                V71ExpansionContributionNet(), _v71ExpansionRiskReserveBlocked, _v71ExpansionRiskCapped, BasketRiskPercent);
            Print("[V51-FREQUENCY-SUMMARY] schedulerDeferred={0} schedulerRecoveredExecutions={1} structuredRecallAdmitted={2} activeDeferred={3}",
                _schedulerDeferred, _schedulerRecoveredExecutions, _structuredRecallAdmitted, _deferredCandidates.Count);
            Print("[V51-INDEPENDENT-SETUP-SUMMARY] duplicateSuppressed={0} uniqueExecuted={1} rescueAdmissions={2} transitionProofRejected={3} independentScaleCandidates={4}",
                _canonicalDuplicateSuppressed, _executedSetupKeys.Count, _m1RescueAdmissions, _transitionProofRejected, _independentScaleCandidates);
            Print("[V51-CONVERSION-SUMMARY] scaleRouteRejected={0} temporalRescueAdmissions={1} armedGraceExtended={2} preExecutionRevalidationRejected={3}",
                _scaleRouteRejected, _temporalRescueAdmissions, _armedGraceExtended, _preExecutionRevalidationRejected);
            double avgWait = _slotWaitMinutes.Count > 0 ? _slotWaitMinutes.Average() : 0;
            double medWait = Percentile(_slotWaitMinutes, .50);
            double p90Wait = Percentile(_slotWaitMinutes, .90);
            double avgOccupancy = _basketOccupancyMinutes.Count > 0 ? _basketOccupancyMinutes.Average() : 0;
            Print("[V51-THROUGHPUT-SUMMARY] slotBlocked={0} parked={1} revalidated={2} revalidationRejected={3} recoveredExecutions={4} nativeTemporalPass={5} hardLifetimeExpired={6} decayRejected={7} avgSlotWaitMin={8:F2} medianSlotWaitMin={9:F2} p90SlotWaitMin={10:F2} avgBasketOccupancyMin={11:F2} missedPositive={12} avoidedNegative={13}",
                _slotBlocked, _parkedCount, _parkedRevalidated, _parkedRevalidationRejected, _parkedRecoveredExecutions,
                _nativeTemporalPass, _hardLifetimeExpired, _opportunityDecayRejected, avgWait, medWait, p90Wait, avgOccupancy,
                _missedPositiveSetups, _avoidedNegativeSetups);
            foreach (var p in _profiles.Select(x => x.Name).Distinct().OrderBy(x => x))
            {
                int pass = _familyContractPass.ContainsKey(p) ? _familyContractPass[p] : 0;
                int reject = _familyContractWindowReject.ContainsKey(p) ? _familyContractWindowReject[p] : 0;
                Print("[V51-FAMILY-CONTRACT-SUMMARY] pattern={0} pass={1} windowReject={2}", p, pass, reject);
            }
            foreach (var kv in _gridPlanRejectReasons.OrderBy(k => k.Key))
                Print("[V51-GRID-REJECT-SUMMARY] reason={0} count={1}", kv.Key, kv.Value);
            foreach (var kv in _executionErrorReasons.OrderBy(k => k.Key))
                Print("[V51-EXECUTION-ERROR-SUMMARY] code={0} count={1}", kv.Key, kv.Value);
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
                if (EnableCanonicalSetupIdentity)
                {
                    if (_executedSetupKeys.Contains(setupKey))
                    {
                        _canonicalDuplicateSuppressed++;
                        continue;
                    }
                    string owner;
                    if (_activeSetupOwners.TryGetValue(setupKey, out owner))
                    {
                        CandidateRecord existing;
                        if (_candidates.TryGetValue(owner, out existing) && existing.IsActive)
                        {
                            _canonicalDuplicateSuppressed++;
                            continue;
                        }
                        _activeSetupOwners.Remove(setupKey);
                    }
                }

                string id = NewCandidateId(signal);
                if (_candidates.ContainsKey(id)) continue;

                var record = new CandidateRecord
                {
                    CandidateId = id,
                    SetupKey = setupKey,
                    Signal = signal,
                    State = CandidateState.DETECTED,
                    DetectedUtc = Server.Time.ToUniversalTime(),
                    ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(2, Math.Min(CandidateTtlM15Bars, signal.Profile.MaxAgeM15Bars))),
                    LastReason = "PATTERN_DETECTED"
                };
                _candidates[id] = record;
                if (EnableCanonicalSetupIdentity) _activeSetupOwners[setupKey] = id;
                CountPipeline(signal.PatternName).Detected++;
                Ledger(record, CandidateState.DETECTED, "PATTERN_DETECTED");

                if (signal.GeometryQuality < Math.Max(MinGeometryQuality, signal.Profile.MinGeometry) ||
                    signal.PrzConfluence < Math.Max(MinPrzConfluence, signal.Profile.MinPrz))
                {
                    Reject(record, "PATTERN_QUALITY");
                    continue;
                }

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
                record.Route = RouteSignal(signal, record.Conflict, regime);

                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    if (EnableRegimeContextGate) _regimeRejected++;
                    Reject(record, "ROUTER_NO_TRADE");
                    continue;
                }

                // V47 expands only genuinely independent secondary-scale setups.
                // V45 DEV showed secondary-scale AB=CD exhaustion positive in A/B/C,
                // while secondary-scale trend-aligned AB=CD was negative overall.
                if (EnableScaleRouteAdmission && signal.PivotScale != M15SwingDepth &&
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

                Print("[V51-ALPHA-CANDIDATE] cid={0} pattern={1} quality={2:F3} regime={3:F3} conflict={4} route={5} adxH1={6:F2} adxH4={7:F2} adxSlope={8:F2} atrPct={9:F3} efficiency={10:F3} capitalFeasible={11} minL0Risk={12:F4}",
                    record.CandidateId, signal.PatternName, record.AlphaQualityScore, record.RegimeScore, record.Conflict, record.Route,
                    regime.AdxH1, regime.AdxH4, regime.AdxH1Slope, regime.AtrPercentile, regime.Efficiency,
                    record.CapitalFeasible, record.CapitalMinL0Risk);

                Transition(record, CandidateState.ROUTED, "ROUTE_" + record.Route);
                CountPipeline(signal.PatternName).Routed++;
                Transition(record, CandidateState.WAIT_PRZ, "WAIT_PRZ");
                CountPipeline(signal.PatternName).PrzWaiting++;
            }

            // V71 invariant: establish the exact V51 core candidate book first.
            // Expansion is discovered only after core ownership is known, so identical setups
            // can never enter the expansion book.
            V71PreemptExpansionForCore(Server.Time.ToUniversalTime());
            if (EnableV71ExpansionShadow || EnableV71ExpansionExecution)
            {
                int expansionLimit = Math.Max(8, Math.Min(32, V71ExpansionMaxCandidates));
                int expansionPoolLimit = EnableV71FamilyBalancedCensus
                    ? Math.Max(64, Math.Min(128, expansionLimit * 4))
                    : expansionLimit;
                var expansionPool = V71DetectExpansionPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback,
                    expansionPoolLimit, "M15");
                var expansionDetected = V71SelectExpansionSignals(expansionPool, expansionLimit);
                foreach (var expansionSignal in expansionDetected)
                    V71TrackExpansionSignal(expansionSignal, h4State, h1State, regime);
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

            if (EnableV71ExpansionShadow || EnableV71ExpansionExecution)
                V71ProcessExpansionM1(i, utc);

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
                    }
                    continue;
                }

                if (c.State == CandidateState.CONFIRMING)
                {
                    if (!c.PrzTouchUtc.HasValue || utc <= c.PrzTouchUtc.Value) continue;

                    double legacyScore = M1ConfirmationScore(i, c.Signal);
                    c.ConfirmationScore = legacyScore;
                    double legacyRequired = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 0.75 : 0.60;
                    bool familyContractLane = EnableFamilyCompletionContract && IsFamilyCompletionLane(c.Signal.PatternName);
                    bool confirmationPass = false;

                    if (familyContractLane)
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
                            Event(c, "FAMILY_COMPLETION_CONTRACT_PASS_" + familyScore.ToString("F2", CultureInfo.InvariantCulture));
                        }
                        else if (c.FamilyConfirmationBarsObserved >= Math.Max(6, FamilyConfirmationWindowBars))
                        {
                            IncrementCounter(_familyContractWindowReject, c.Signal.PatternName);
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
            if (!TradingEnabled) return;
            if (!_initialCapitalEligible) return;
            DateTime now = Server.Time.ToUniversalTime();
            if (_evaluationStartUtc.HasValue && now < _evaluationStartUtc.Value) return;

            // Core ownership must be asserted before a shared account risk lock can return.
            // This lets a newly-detected V51 thesis remove an expansion basket immediately;
            // the normal V51 risk lock still governs whether the core may then execute.
            V71PreemptExpansionForCore(now);
            if (_dailyLocked || PeakDrawdownExceeded()) return;

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
                    .Select(g => g.OrderByDescending(c => EnableOpportunityDecayRanking ? OpportunityScore(c, now) : c.Rank).First());

            var armed = armedQuery
                .OrderByDescending(c => EnableOpportunityDecayRanking ? OpportunityScore(c, now) : c.Rank)
                .ToList();
            if (armed.Count == 0)
            {
                V71TryExecuteExpansion(now);
                return;
            }

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
            Print("[V51-OPPORTUNITY-LOSS] cid={0} setup={1} pattern={2} route={3} scale={4} reason={5} shadowMfeR={6:F3} shadowMaeR={7:F3} missedPositive={8} avoidedNegative={9}",
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
            if (c != null) Event(c, "GRID_PLAN_REJECT_" + reason);
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

            int routeMax = c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 4 :
                           c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 2 :
                           c.Route == HarmonicRoute.TRANSITION_REVERSAL ? (c.Regime != null && c.Regime.Efficiency >= .28 ? 3 : 2) : 0;
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
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
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

                double riskWeight = leg < p.GridRiskWeights.Length ? p.GridRiskWeights[leg] : 0;
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

            Print("[V51-GRID-PLAN] cid={0} pattern={1} route={2} logicalLegs={3} physicalDepth={4} micro={5} anchor={6} weighted={7} virtualWeighted={8} stop={9} target={10} budget={11:F2} worst={12:F2} margin={13:F2} netRR={14:F3}",
                c.CandidateId, c.Signal.PatternName, c.Route, plan.LogicalLegCount, plan.PhysicalDepth, plan.MicroCapitalMode,
                anchor, plan.ExpectedWeightedEntry, plan.VirtualWeightedEntry, stop, target, plan.BasketRiskAmount,
                plan.WorstCaseRisk, plan.EstimatedPhysicalMargin, plan.ExpectedNetRR);
            foreach (var leg in plan.Legs)
                Print("[V51-GRID-LEG-PLAN] cid={0} leg=L{1} fraction={2:F3} price={3} weight={4:F6} physical={5} volume={6} budget={7:F2} risk={8:F2} minBrokerRisk={9:F2} state={10}",
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
                        double volume = VolumeForRiskBudget(budget, slPips);
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
                double volume = VolumeForRiskBudget(l.RiskBudget, slPips);
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
            double effectivePct = Account.Equity > 0 && plan.BasketRiskAmount > 0
                ? Math.Min(5.0, Math.Max(.1, plan.BasketRiskAmount / Account.Equity * 100.0))
                : Math.Min(5.0, Math.Max(.1, BasketRiskPercent));
            double budget = equity * effectivePct / 100.0;
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
            Print("[V51-CAPITAL-COMPAT] cid={0} logicalLegs={1} riskOnlyPhysicalDepths={2}", plan.CandidateId, plan.LogicalLegCount, matrix);
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

            double volume = VolumeForRiskBudget(l0.RiskBudget, slPips);
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
            V71RecordCoreExecution(c);
            if (EnableCanonicalSetupIdentity && !c.V71Expansion && !string.IsNullOrWhiteSpace(c.SetupKey))
            {
                _executedSetupKeys.Add(c.SetupKey);
                _activeSetupOwners.Remove(c.SetupKey);
            }
            else if (c.V71Expansion && !string.IsNullOrWhiteSpace(c.SetupKey))
            {
                _v71ExpansionExecutedSetupKeys.Add(c.SetupKey);
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

                if (basket.PeakR >= GridCancelMfeR && pending.Count > 0)
                    CancelBasketPending(basket, "MFE_GRID_CANCEL");

                double age = (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes;
                if (age >= NoMfeMinAgeMinutes && basket.PeakR < NoMfeProofR && currentR <= -Math.Abs(NoMfeKillR))
                {
                    basket.ExitOverride = "NO_MFE_THESIS_FAILURE";
                    CancelBasketPending(basket, basket.ExitOverride);
                    CloseBasketPositions(basket, basket.ExitOverride);
                    continue;
                }

                double protectTriggerR = basket.Candidate != null && basket.Candidate.V72ReactionAlpha ? .50 : BreakEvenTriggerR;
                double protectLockR = basket.Candidate != null && basket.Candidate.V72ReactionAlpha ? .10 : Math.Max(0, BreakEvenLockR);
                if (basket.PeakR >= protectTriggerR)
                {
                    double span = Math.Abs(basket.AverageEntry - basket.StructuralStop);
                    double lockPrice = basket.Direction == TradeDirection.Buy
                        ? basket.AverageEntry + span * protectLockR
                        : basket.AverageEntry - span * protectLockR;
                    AdvanceBasketProtectionFrontier(basket, lockPrice,
                        basket.Candidate != null && basket.Candidate.V72ReactionAlpha ? "V72_EARLY_CAPITAL_PROTECT" : "COLLECTIVE_PROTECT");
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
            Print("[V51-PENDING-CANCEL-ALL] reason={0}", reason);
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
            return notAcceleratingAgainst;
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
                Print("[V51-POST-FILL-DEDUPE] pos={0} source={1}", p.Id, source);
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
                Print("[V51-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next=FILLED_UNVERIFIED reason=LATE_FILL_AFTER_TERMINAL_STATE",
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
            Print("[V51-POST-FILL-AUDIT] basket={0} leg=L{1} pos={2} source={3} entry={4} stop={5} target={6} actualWorst={7:F4} budget={8:F4} protected=true",
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
                Print("[V51-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next={3} reason={4}", basket == null ? "" : basket.BasketId, leg.Index, prior, next, reason);
            }
            leg.State = next;
            if (basket != null) BasketEvent(basket, "LEG_STATE_L" + leg.Index + "_" + prior + "_TO_" + next + "_" + reason);
        }

        private void PrintBrokerCapabilityProfile()
        {
            double min = _symbol.VolumeInUnitsMin;
            double marginBuy = EstimatedMargin(TradeDirection.Buy, min);
            double marginSell = EstimatedMargin(TradeDirection.Sell, min);
            Print("[V51-BROKER-PROFILE] symbol={0} equity={1:F2} freeMargin={2:F2} minVolume={3} step={4} maxVolume={5} pipValue={6} tickValue={7} minSL={8} minTP={9} minDistanceType={10} minMarginBuy={11:F2} minMarginSell={12:F2} minimumSupportedEquity={13:F2} adaptiveCapital={14} microThreshold={15:F2} initialCapitalEligible={16}",
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
                Print("[V51-LEG-CLOSED] pos={0} basket=UNKNOWN net={1:F2} reason={2}", p.Id, p.NetProfit, args.Reason);
                return;
            }

            FibonacciBasket basket = null;
            if (_baskets.TryGetValue(l.BasketId, out basket))
            {
                if (!string.IsNullOrWhiteSpace(basket.CandidateId) &&
                    basket.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                    _v71ExpansionRealizedNet += p.NetProfit;
                basket.RealizedNet += p.NetProfit;
                basket.ClosedLegs++;
                double legRealizedR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
                Print("[V51-LEG-CLOSED] basket={0} cid={1} leg=L{2} pos={3} pattern={4} route={5} dir={6} mfeR={7:F3} maeR={8:F3} realizedR={9:F3} net={10:F2} reason={11}",
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
            Print("[V51-BASKET-CLOSED] basket={0} cid={1} setup={2} pattern={3} subtype={4} route={5} dir={6} plannedLegs={7} filledLegs={8} anchor={9} avgEntry={10} entryImprovePips={11:F3} stop={12} target={13} initialRisk={14:F2} worstRisk={15:F2} mfeR={16:F3} maeR={17:F3} realizedR={18:F3} net={19:F2} reason={20}",
                basket.BasketId, basket.CandidateId, setupKey, basket.Pattern, subtype, basket.Route, basket.Direction, basket.Plan.Legs.Count, basket.FilledLegs,
                basket.EntryAnchor, basket.AverageEntry, entryImprovementPips, basket.StructuralStop, basket.CanonicalTarget,
                basket.InitialBasketRisk, basket.PlannedWorstCaseRisk, basket.PeakR, basket.MaxAdverseR, realizedR, basket.RealizedNet, reason);

            double occupancyMin = Math.Max(0, (Server.Time.ToUniversalTime() - basket.CreatedUtc).TotalMinutes);
            _basketOccupancyMinutes.Add(occupancyMin);
            Print("[V51-SLOT-OCCUPANCY] basket={0} cid={1} pattern={2} route={3} occupancyMinutes={4:F2} realizedR={5:F3} net={6:F2}",
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
            Print("[V51-BASKET-EVENT] basket={0} cid={1} pattern={2} route={3} state={4} reason={5}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, basket.State, reason);
        }

        private DateTime MinDate(DateTime a, DateTime b) { return a <= b ? a : b; }

        // ---------------- V71 protected-core incremental expansion ----------------

        private void V71ParseEdgeModel()
        {
            _v71EdgeWeights.Clear();
            _v71FamilyRoutePriors.Clear();
            _v71AllowedFamilyRoutes.Clear();
            _v71AllowedFamilyRouteContexts.Clear();
            _v71AllowedSetupHashes.Clear();
            _v71ModelReady = false;

            if (!string.IsNullOrWhiteSpace(V71EdgeModelSpec))
            {
                foreach (var part in V71EdgeModelSpec.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    var kv = part.Split(new[] { ':' }, 2);
                    double v;
                    if (kv.Length == 2 && double.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out v))
                        _v71EdgeWeights[kv[0]] = v;
                }
            }

            if (!string.IsNullOrWhiteSpace(V71FamilyRoutePriorSpec))
            {
                foreach (var part in V71FamilyRoutePriorSpec.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    var kv = part.Split(':');
                    double v;
                    if (kv.Length == 3 && double.TryParse(kv[2], NumberStyles.Float, CultureInfo.InvariantCulture, out v))
                        _v71FamilyRoutePriors[kv[0] + ":" + kv[1]] = Math.Max(-1.0, Math.Min(1.0, v));
                }
            }

            if (!string.IsNullOrWhiteSpace(V71AllowedFamilyRouteSpec))
            {
                foreach (var part in V71AllowedFamilyRouteSpec.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    string key = part.Trim();
                    if (!string.IsNullOrWhiteSpace(key)) _v71AllowedFamilyRoutes.Add(key);
                }
            }
            if (!string.IsNullOrWhiteSpace(V71AllowedFamilyRouteContextSpec))
            {
                foreach (var part in V71AllowedFamilyRouteContextSpec.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    string key = part.Trim();
                    if (!string.IsNullOrWhiteSpace(key)) _v71AllowedFamilyRouteContexts.Add(key);
                }
            }
            if (!string.IsNullOrWhiteSpace(V71AllowedSetupHashSpec))
            {
                foreach (var part in V71AllowedSetupHashSpec.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    uint v;
                    if (uint.TryParse(part.Trim(), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out v))
                        _v71AllowedSetupHashes.Add(v);
                }
            }

            bool h5 = _v71EdgeWeights.TryGetValue("h5", out var h5Flag) && h5Flag > .5;
            _v71ModelReady = h5
                ? _v71EdgeWeights.ContainsKey("i") && _v71EdgeWeights.ContainsKey("p2i") &&
                  _v71EdgeWeights.ContainsKey("shi") && _v71EdgeWeights.ContainsKey("chi")
                : _v71EdgeWeights.ContainsKey("i") && _v71EdgeWeights.ContainsKey("g") &&
                  _v71EdgeWeights.ContainsKey("prz") && _v71EdgeWeights.ContainsKey("m1") &&
                  _v71EdgeWeights.ContainsKey("rr");
        }

        private double V71W(string key)
        {
            double v;
            return _v71EdgeWeights.TryGetValue(key, out v) ? v : 0.0;
        }

        private string V71FamilyKey(string pattern)
        {
            if (pattern == "AB=CD") return "ABCD";
            if (pattern == "5-0") return "FiveZero";
            return (pattern ?? "UNKNOWN").Replace(" ", "").Replace("-", "");
        }

        private string V71RouteKey(HarmonicRoute route)
        {
            return route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? "T" :
                   route == HarmonicRoute.EXHAUSTION_REVERSAL ? "E" :
                   route == HarmonicRoute.TRANSITION_REVERSAL ? "X" : "N";
        }

        private double V71FamilyRoutePrior(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return 0;
            double v;
            string key = V71FamilyKey(e.Signal.PatternName) + ":" + V71RouteKey(e.Route);
            return _v71FamilyRoutePriors.TryGetValue(key, out v) ? v : 0.0;
        }

        private string V71RegimeContextKey(V71ExpansionCandidate e)
        {
            if (e == null) return "MIXED";
            if (e.TransitionState >= .50) return "TRANSITION";
            double mtf = V71MtfScore(e.Conflict);
            if (mtf >= .85 && e.TrendStrength >= .50) return "ALIGNED_TREND";
            if (e.Regime != null && e.Regime.ExtensionAtr >= 1.0 && mtf <= .65) return "EXHAUSTION";
            if (e.Regime != null && e.Regime.Efficiency < .30) return "RANGE";
            return "MIXED";
        }

        private bool V71FamilyRouteAllowed(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return false;
            if (EnableV72ReactionAlpha) return true;
            bool h5 = V71W("h5") > .5;
            if (_v71AllowedFamilyRoutes.Count == 0) return h5;
            string pair = V71FamilyKey(e.Signal.PatternName) + ":" + V71RouteKey(e.Route);
            if (!_v71AllowedFamilyRoutes.Contains(pair)) return false;
            if (h5 || _v71AllowedFamilyRouteContexts.Count == 0) return true;
            return _v71AllowedFamilyRouteContexts.Contains(pair + ":" + V71RegimeContextKey(e));
        }

        private bool V71SetupAllowed(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return false;
            if (_v71AllowedSetupHashes.Count == 0) return true;
            string id = V71FamilyKey(e.Signal.PatternName) + "|" + e.SetupKey;
            return _v71AllowedSetupHashes.Contains(V71StableHash32(id));
        }

        private string V71PairToken(V71ExpansionCandidate e)
        {
            return e == null || e.Signal == null ? "UNKNOWN_N" :
                V71FamilyKey(e.Signal.PatternName) + "_" + V71RouteKey(e.Route);
        }

        private double V71PairWeight(string prefix, V71ExpansionCandidate e)
        {
            return V71W(prefix + V71PairToken(e));
        }

        private double V71PairUncertainty(string prefix, V71ExpansionCandidate e, string baseKey)
        {
            double v;
            string key = prefix + V71PairToken(e);
            return _v71EdgeWeights.TryGetValue(key, out v) ? Math.Max(0, v) : Math.Max(0, V71W(baseKey));
        }

        private double V71MtfScore(MtfConflict c)
        {
            return c == MtfConflict.ALIGNED ? 1.0 :
                   c == MtfConflict.SUPPORTED ? .85 :
                   c == MtfConflict.TRANSITION ? .65 :
                   c == MtfConflict.NEUTRAL ? .55 : .25;
        }

        private HarmonicRoute V71ExpansionRoute(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (r != null && (r.Transition || conflict == MtfConflict.TRANSITION))
                return HarmonicRoute.TRANSITION_REVERSAL;
            bool opposed = r != null && r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            if (opposed && r.ExtensionAtr >= 1.0)
                return HarmonicRoute.EXHAUSTION_REVERSAL;
            return HarmonicRoute.TREND_ALIGNED_REVERSAL;
        }

        private bool V71ExpansionIntegrity(PatternSignal s)
        {
            if (s == null || s.Profile == null) return false;
            if (string.IsNullOrWhiteSpace(s.PatternName)) return false;
            if (!double.IsFinite(s.GeometryQuality) || !double.IsFinite(s.PrzConfluence) ||
                !double.IsFinite(s.Confidence) || !double.IsFinite(s.StructuralInvalidation))
                return false;
            if (s.StructuralInvalidation <= 0 || s.PrzHigh <= s.PrzLow) return false;
            return true;
        }

        private List<PatternSignal> V71SelectExpansionSignals(IEnumerable<PatternSignal> pool, int maxCandidates)
        {
            int limit = Math.Max(8, Math.Min(32, maxCandidates));
            var ordered = (pool ?? Enumerable.Empty<PatternSignal>())
                .Where(x => x != null && x.Profile != null)
                // Expansion research must preserve competing family interpretations of the
                // same XABCD geometry. Core canonical identity remains geometry-only.
                .GroupBy(x => V71FamilyKey(x.PatternName) + "|" + BuildSetupGeometryKey(x))
                .Select(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).First())
                .OrderByDescending(x => x.Confidence)
                .ThenByDescending(x => x.GeometryQuality)
                .ToList();

            if (!EnableV71FamilyBalancedCensus)
                return ordered.Take(limit).ToList();

            int familyCap = Math.Max(2, Math.Min(12, V71PerFamilyCensusCap));
            int abcdBudget = (int)Math.Floor(limit * Math.Max(0, Math.Min(25, V71AbcdCensusSharePercent)) / 100.0);
            var familyBuckets = ordered
                .Where(x => !string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                .GroupBy(x => V71FamilyKey(x.PatternName))
                .OrderBy(g => g.Key)
                .ToDictionary(
                    g => g.Key,
                    g => new Queue<PatternSignal>(g.Take(familyCap)));

            var selected = new List<PatternSignal>();
            int nonAbcdBudget = Math.Max(0, limit - abcdBudget);
            bool progressed = true;
            while (selected.Count < nonAbcdBudget && progressed)
            {
                progressed = false;
                foreach (var key in familyBuckets.Keys.OrderBy(x => x).ToList())
                {
                    Queue<PatternSignal> q = familyBuckets[key];
                    if (q.Count == 0) continue;
                    selected.Add(q.Dequeue());
                    progressed = true;
                    if (selected.Count >= nonAbcdBudget) break;
                }
            }

            if (abcdBudget > 0 && selected.Count < limit)
            {
                foreach (var x in ordered.Where(x => string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                                         .Take(Math.Min(abcdBudget, limit - selected.Count)))
                    selected.Add(x);
            }

            return selected;
        }

        private void V71TrackExpansionSignal(PatternSignal s, HarmonicState h4, HarmonicState h1, RegimeSnapshot regime)
        {
            if (!V71ExpansionIntegrity(s)) return;
            string setup = BuildSetupGeometryKey(s);
            bool coreOverlap = _executedSetupKeys.Contains(setup) || _activeSetupOwners.ContainsKey(setup);
            string id = V71FamilyKey(s.PatternName) + "|" + setup;
            if (_v71Expansion.ContainsKey(id)) return;

            var conflict = ClassifyMtfConflict(s.Direction, h4, h1);
            string fam = V71FamilyKey(s.PatternName);
            var e = new V71ExpansionCandidate
            {
                CandidateId = "V71EXP-" + V71StableHash32(id).ToString("X8", CultureInfo.InvariantCulture) + "-" +
                              s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture),
                IdentityKey = id,
                SetupKey = setup,
                Signal = s,
                Conflict = conflict,
                Regime = regime,
                Route = V71ExpansionRoute(s, conflict, regime),
                DetectedUtc = Server.Time.ToUniversalTime(),
                ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(4, Math.Min(32, V71ExpansionTtlM15Bars))),
                State = V71ExpansionState.WAIT_PRZ,
                IsActive = true,
                CoreOverlapObserved = coreOverlap,
                CapitalEligible = !coreOverlap && !string.Equals(fam, "ABCD", StringComparison.OrdinalIgnoreCase),
                AbcdRole = string.IsNullOrWhiteSpace(s.ResearchRole) ? (fam == "ABCD" ? "ABCD_STANDALONE" : "PARENT_FAMILY") : s.ResearchRole
            };
            _v71Expansion[id] = e;
            _v71ExpansionDetected++;
            IncrementCounter(_v71FamilyTracked, fam);
            if (coreOverlap) IncrementCounter(_v71FamilyCoreOverlap, fam);
            Print("[V71-EXP-DETECTED] cid={0} setup={1} family={2} subtype={3} role={4} route={5} conflict={6} coreOverlap={7} capitalEligible={8} g={9:F4} prz={10:F4} conf={11:F4}",
                e.CandidateId, e.SetupKey, fam, s.HarmonicSubtype ?? s.PatternName, e.AbcdRole,
                e.Route, e.Conflict, e.CoreOverlapObserved, e.CapitalEligible,
                s.GeometryQuality, s.PrzConfluence, s.Confidence);
        }

        private uint V71StableHash32(string value)
        {
            unchecked
            {
                uint h = 2166136261u;
                foreach (char ch in value ?? "")
                {
                    h ^= (byte)(ch & 0xFF);
                    h *= 16777619u;
                    if (ch > 0xFF)
                    {
                        h ^= (byte)((ch >> 8) & 0xFF);
                        h *= 16777619u;
                    }
                }
                return h;
            }
        }

        private void V71RefreshExpansionDecisionContext(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return;
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            var regime = BuildRegimeSnapshot();
            e.Conflict = ClassifyMtfConflict(e.Signal.Direction, h4, h1);
            e.Regime = regime;
            e.Route = V71ExpansionRoute(e.Signal, e.Conflict, regime);
        }

        private bool V71ExpansionM1Confirmation(int i, V71ExpansionCandidate e, out double score)
        {
            score = 0;
            if (e == null || e.Signal == null || i <= 2 || i >= _m1Bars.Count) return false;
            double close = _m1Bars.ClosePrices[i];
            bool structurallyAlive = e.Signal.Direction == TradeDirection.Buy
                ? close > e.Signal.StructuralInvalidation
                : close < e.Signal.StructuralInvalidation;
            if (!structurallyAlive) return false;

            if (!EnableV71FamilyNativeConfirmation)
            {
                score = M1ConfirmationScore(i, e.Signal);
                bool directional = e.Signal.Direction == TradeDirection.Buy
                    ? close > _m1Bars.OpenPrices[i] || close > _m1Bars.ClosePrices[i - 1]
                    : close < _m1Bars.OpenPrices[i] || close < _m1Bars.ClosePrices[i - 1];
                return directional && score >= .50;
            }

            if (e.NativeEvidenceState == null)
            {
                e.NativeEvidenceState = new CandidateRecord
                {
                    CandidateId = e.CandidateId + "-SHADOW-DAG",
                    SetupKey = e.SetupKey,
                    Signal = e.Signal,
                    Route = e.Route,
                    Regime = e.Regime,
                    IsActive = true
                };
            }
            e.NativeEvidenceState.Route = e.Route;
            e.NativeEvidenceState.Regime = e.Regime;
            e.NativeConfirmBars++;
            double nativeScore;
            bool pass = UpdatePatternNativeM1State(i, e.NativeEvidenceState, out nativeScore);
            score = Math.Max(nativeScore, M1ConfirmationScore(i, e.Signal));
            return pass;
        }

        private double V71AtrFit(RegimeSnapshot r)
        {
            if (r == null) return .5;
            return VClamp(1.0 - Math.Abs(r.AtrRatio - 1.0));
        }

        private double V71ExpectedEdge(V71ExpansionCandidate e)
        {
            if (!_v71ModelReady || e == null || e.Signal == null) return -999;
            string[] keys = { "g", "prz", "conf", "ts", "pv", "m1", "rr", "reg", "eff", "atr", "ext", "mtf",
                              "atp", "adx1", "adx4", "adxs", "trend", "spr", "ses", "przc", "trans" };
            double y = V71W("i");
            foreach (var key in keys) y += V71W(key) * V71FeatureValue(e, key);
            y += V71W("prior") * V71FamilyRoutePrior(e);
            return y;
        }

        private double V71ExpectedSurvival(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return .50;
            double p = V71W("si");
            string[] keys = { "g", "prz", "conf", "ts", "pv", "m1", "rr", "reg", "eff", "atr", "ext", "mtf",
                              "atp", "adx1", "adx4", "adxs", "trend", "spr", "ses", "przc", "trans" };
            foreach (var key in keys)
                p += V71W("s_" + key) * V71FeatureValue(e, key);
            if (Math.Abs(p) < 1e-12 && Math.Abs(V71W("si")) < 1e-12) return .50;
            return Math.Max(.05, Math.Min(.95, p));
        }

        private double V71FeatureValue(V71ExpansionCandidate e, string key)
        {
            if (e == null || e.Signal == null) return 0;
            if (key == "g") return VClamp(e.Signal.GeometryQuality);
            if (key == "prz") return VClamp(e.Signal.PrzConfluence);
            if (key == "conf") return VClamp(e.Signal.Confidence);
            if (key == "ts") return VClamp(e.Signal.TimeSymmetry);
            if (key == "pv") return VClamp(e.Signal.PivotQuality);
            if (key == "m1") return VClamp(e.ConfirmationScore);
            if (key == "rr") return VClamp(e.NetRR / 4.0);
            if (key == "reg") return VClamp(e.RegimeScore);
            if (key == "eff") return e.Regime == null ? 0 : VClamp(e.Regime.Efficiency);
            if (key == "atr") return V71AtrFit(e.Regime);
            if (key == "ext") return e.Regime == null ? 0 : VClamp(e.Regime.ExtensionAtr / 2.0);
            if (key == "mtf") return V71MtfScore(e.Conflict);
            if (key == "atp") return e.AtrPercentile;
            if (key == "adx1") return e.AdxH1Norm;
            if (key == "adx4") return e.AdxH4Norm;
            if (key == "adxs") return e.AdxSlopeNorm;
            if (key == "trend") return e.TrendStrength;
            if (key == "spr") return e.SpreadAtr;
            if (key == "ses") return e.SessionPhase;
            if (key == "przc") return e.PrzCompression;
            if (key == "trans") return e.TransitionState;
            return 0;
        }

        private double V71SupportDistance(V71ExpansionCandidate e)
        {
            bool h5 = V71W("h5") > .5;
            double supportRef = h5 ? V71W("support_ref") : V71W("support_max");
            if (supportRef <= 0 || supportRef >= 900) return 0;
            string[] keys = h5
                ? new[] { "rr", "atr", "atp", "adx1", "ses" }
                : new[] { "g", "prz", "m1", "rr", "reg", "eff", "atr", "ext", "atp", "trend", "spr", "ses", "przc", "trans" };
            double ss = 0;
            foreach (var key in keys)
            {
                double scale = Math.Max(.05, Math.Abs(V71W("ms_" + key)));
                double z = (V71FeatureValue(e, key) - V71W("mc_" + key)) / scale;
                ss += z * z;
            }
            return Math.Sqrt(ss / keys.Length);
        }

        private bool V71SupportEligible(V71ExpansionCandidate e, out double distance)
        {
            distance = V71SupportDistance(e);
            if (V71W("soft_support") > .5) return true;
            double supportMax = V71W("support_max");
            return supportMax <= 0 || supportMax >= 900 || distance <= supportMax + 1e-12;
        }

        private double V71H5SupportPenalty(V71ExpansionCandidate e, string scaleKey)
        {
            if (V71W("h5") <= .5) return 0;
            double extra = Math.Max(0, V71SupportDistance(e) - Math.Max(0, V71W("support_ref")));
            return Math.Max(0, V71W(scaleKey)) * extra;
        }

        private double V71ExpectedPathProbability(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return 0;
            string[] keys = { "rr", "atr", "atp", "adx1" };
            double p = V71W("p2i");
            foreach (var key in keys) p += V71W("p2_" + key) * V71FeatureValue(e, key);
            p += V71PairWeight("p2pr_", e);
            return Math.Max(.01, Math.Min(.99, p));
        }

        private double V71ExpectedPathLcb(V71ExpansionCandidate e)
        {
            double p = V71ExpectedPathProbability(e);
            double penalty = Math.Max(0, V71W("p2_base_margin")) + V71PairUncertainty("pu_", e, "p2_base_margin") +
                             V71H5SupportPenalty(e, "p2_uncertainty_scale");
            return Math.Max(0, Math.Min(.99, p - penalty));
        }

        private double V71ExpectedRunnerProbability(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return 0;
            string[] keys = { "rr", "atr", "atp", "adx1" };
            double p = V71W("ri");
            foreach (var key in keys) p += V71W("r_" + key) * V71FeatureValue(e, key);
            p += V71PairWeight("rpr_", e);
            return Math.Max(.01, Math.Min(.99, p));
        }

        private double V71ExpectedRunnerLcb(V71ExpansionCandidate e)
        {
            double p = V71ExpectedRunnerProbability(e);
            double penalty = Math.Max(0, V71W("runner_base_margin")) + V71PairUncertainty("ru_", e, "runner_base_margin") +
                             V71H5SupportPenalty(e, "p2_uncertainty_scale");
            return Math.Max(0, Math.Min(.99, p - penalty));
        }

        private double V71ExpectedCoreArrivalHazard(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return .95;
            string[] keys = { "ses", "atr", "atp", "adx1" };
            double p = V71W("chi");
            foreach (var key in keys) p += V71W("ch_" + key) * V71FeatureValue(e, key);
            p += Math.Max(0, V71W("core_hazard_margin"));
            return Math.Max(0, Math.Min(.95, p));
        }

        private double V71ExpectedSlotHoursUcb(V71ExpansionCandidate e)
        {
            double hours = V71ExpectedSlotHours(e);
            if (V71W("h5") <= .5) return hours;
            return Math.Max(.50, Math.Min(12.0, hours * Math.Exp(Math.Max(0, Math.Min(1.5, V71W("slot_margin"))))));
        }

        private double V71PathBreakEven(V71ExpansionCandidate e)
        {
            double costR = e == null ? 0 : Math.Max(0, e.ModeledCostR);
            return Math.Max(1.0 / 3.0, Math.Min(.60, (1.0 + costR) / 3.0));
        }

        private double V71ExpectedSlotHours(V71ExpansionCandidate e)
        {
            if (e == null) return 2.0;
            if (!_v71EdgeWeights.ContainsKey("shi"))
                return e.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 1.50 :
                       e.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 2.00 :
                       e.Route == HarmonicRoute.TRANSITION_REVERSAL ? 1.25 : 2.00;

            string[] keys = { "g", "prz", "conf", "ts", "pv", "m1", "rr", "reg", "eff", "atr", "ext", "mtf",
                              "atp", "adx1", "adx4", "adxs", "trend", "spr", "ses", "przc", "trans" };
            double logHours = V71W("shi");
            foreach (var key in keys) logHours += V71W("sh_" + key) * V71FeatureValue(e, key);
            return Math.Max(.50, Math.Min(12.0, Math.Exp(Math.Max(-2.0, Math.Min(3.0, logHours)))));
        }

        private double V71SessionPhase(DateTime utc)
        {
            utc = DateTime.SpecifyKind(utc, DateTimeKind.Utc);
            DateTime londonLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _londonTz);
            DateTime nyLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _newYorkTz);
            DateTime londonOpenUtc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(londonLocal.Date.AddHours(8), DateTimeKind.Unspecified), _londonTz);
            DateTime nyCloseUtc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(nyLocal.Date.AddHours(17), DateTimeKind.Unspecified), _newYorkTz);
            double span = Math.Max(1.0, (nyCloseUtc - londonOpenUtc).TotalMinutes);
            return VClamp((utc - londonOpenUtc).TotalMinutes / span);
        }

        private double V71SpreadAtr(RegimeSnapshot r)
        {
            if (r == null || r.AtrM15Pips <= 1e-9) return 1.0;
            return VClamp(CurrentSpreadPips() / r.AtrM15Pips);
        }

        private double V71PrzCompression(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || e.Regime == null || e.Regime.AtrM15Pips <= 1e-9) return 0.0;
            double widthPips = PriceToPips(Math.Max(0, e.Signal.PrzHigh - e.Signal.PrzLow));
            return VClamp(1.0 - widthPips / Math.Max(1e-9, e.Regime.AtrM15Pips));
        }

        private void V71ArmExpansion(int i, DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            double entry = e.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = e.Signal.StructuralInvalidation;
            if ((e.Signal.Direction == TradeDirection.Buy && stop >= entry) ||
                (e.Signal.Direction == TradeDirection.Sell && stop <= entry))
            {
                e.IsActive = false; e.State = V71ExpansionState.INVALIDATED; return;
            }
            if (PriceToPips(Math.Abs(entry - stop)) < MinStopLossPips)
            {
                e.IsActive = false; e.State = V71ExpansionState.REJECTED; return;
            }

            double target, netRr;
            if (!SelectCanonicalBasketTarget(e.Signal, entry, stop, out target, out netRr) || netRr < MinimumNetRR)
            {
                e.IsActive = false; e.State = V71ExpansionState.REJECTED; return;
            }
            if (EnableV72ReactionAlpha)
            {
                double risk = Math.Abs(entry - stop);
                double costPrice = PipsToPrice(ModeledCostPips());
                double reactionTarget = e.Signal.Direction == TradeDirection.Buy
                    ? entry + 2.0 * risk + costPrice
                    : entry - 2.0 * risk - costPrice;
                bool canonicalCoversReaction = e.Signal.Direction == TradeDirection.Buy
                    ? target >= reactionTarget
                    : target <= reactionTarget;
                if (!canonicalCoversReaction || !GeometryValid(e.Signal.Direction, entry, stop, reactionTarget))
                {
                    e.IsActive = false; e.State = V71ExpansionState.REJECTED; return;
                }
                target = reactionTarget;
                netRr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                        Math.Max(1e-9, PriceToPips(risk));
                if (netRr + 1e-9 < MinimumNetRR)
                {
                    e.IsActive = false; e.State = V71ExpansionState.REJECTED; return;
                }
            }

            e.EntryAnchor = entry;
            e.StructuralStop = stop;
            e.CanonicalTarget = target;
            e.RiskDistance = Math.Abs(entry - stop);
            e.TargetR = e.RiskDistance > 0 ? Math.Abs(target - entry) / e.RiskDistance : netRr;
            e.NetRR = netRr;
            e.ConfirmationScore = confirmationScore;
            e.RegimeScore = RegimeContextScore(e.Signal, e.Conflict, e.Regime);
            e.AtrPercentile = e.Regime == null ? .5 : VClamp(e.Regime.AtrPercentile);
            e.AdxH1Norm = e.Regime == null ? 0 : VClamp(e.Regime.AdxH1 / 50.0);
            e.AdxH4Norm = e.Regime == null ? 0 : VClamp(e.Regime.AdxH4 / 50.0);
            e.AdxSlopeNorm = e.Regime == null ? 0 : Math.Max(-1.0, Math.Min(1.0, e.Regime.AdxH1Slope / 10.0));
            e.TrendStrength = e.Regime == null ? 0 : VClamp(e.Regime.TrendStrength);
            e.SpreadAtr = V71SpreadAtr(e.Regime);
            e.SessionPhase = V71SessionPhase(utc);
            e.PrzCompression = V71PrzCompression(e);
            e.TransitionState = e.Regime != null && e.Regime.Transition ? 1.0 : 0.0;
            e.ArmedUtc = utc;
            e.State = V71ExpansionState.ARMED;
            e.ShadowStarted = true;
            e.ShadowPeakR = 0;
            e.ShadowProtectionR = -1.0;
            e.ModeledCostR = e.RiskDistance > 0 ? PipsToPrice(ModeledCostPips()) / e.RiskDistance : 0;
            if (EnableV72ReactionAlpha)
            {
                e.SupportEligible = true;
                e.SupportDistance = 0;
                e.EdgeMean = e.NetRR;
                e.EdgeLcb = e.NetRR;
                e.PathProbability = .50;
                e.PathLcb = 0;
                e.RunnerProbability = 0;
                e.RunnerLcb = 0;
                e.ExpectedSlotHours = e.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 1.50 :
                                      e.Route == HarmonicRoute.TRANSITION_REVERSAL ? 1.25 : 2.00;
                e.ExpectedSlotHoursUcb = e.ExpectedSlotHours;
                e.CoreArrivalHazard = 0;
                e.SurvivalProbability = .50;
                e.SlotScore = e.NetRR / Math.Max(.50, e.ExpectedSlotHours);
            }
            else
            {
                e.SupportEligible = V71SupportEligible(e, out var supportDistance);
                e.SupportDistance = supportDistance;
                e.EdgeMean = V71ExpectedEdge(e);
                if (V71W("h5") > .5)
                    e.EdgeLcb = e.EdgeMean - Math.Max(0, V71W("edge_base_margin")) -
                                V71PairUncertainty("eu_", e, "edge_base_margin") - V71H5SupportPenalty(e, "uncertainty_scale");
                else
                    e.EdgeLcb = e.EdgeMean - Math.Max(0, V71EdgeLcbMargin);
                e.PathProbability = V71ExpectedPathProbability(e);
                e.PathLcb = V71ExpectedPathLcb(e);
                e.RunnerProbability = V71ExpectedRunnerProbability(e);
                e.RunnerLcb = V71ExpectedRunnerLcb(e);
                e.ExpectedSlotHours = V71ExpectedSlotHours(e);
                e.ExpectedSlotHoursUcb = V71ExpectedSlotHoursUcb(e);
                e.CoreArrivalHazard = V71ExpectedCoreArrivalHazard(e);
                e.SurvivalProbability = V71W("h5") > .5 ? e.PathProbability : V71ExpectedSurvival(e);
                e.SlotScore = e.SupportEligible
                    ? (V71W("h5") > .5
                        ? e.EdgeLcb / Math.Max(.50, e.ExpectedSlotHoursUcb) -
                          e.CoreArrivalHazard * Math.Max(0, V71W("core_cost"))
                        : e.EdgeLcb * Math.Max(.05, Math.Min(.95, e.SurvivalProbability)) / Math.Max(.50, e.ExpectedSlotHours))
                    : double.NegativeInfinity;
            }
            _v71ExpansionArmed++;
            IncrementCounter(_v71FamilyArmed, V71FamilyKey(e.Signal.PatternName));

            Print("[V71-EXP-ARM] cid={0} setup={1} family={2} route={3} model={4} g={5:F5} prz={6:F5} conf={7:F5} ts={8:F5} pv={9:F5} m1={10:F5} rr={11:F5} reg={12:F5} eff={13:F5} atr={14:F5} ext={15:F5} mtf={16:F5} atp={17:F5} adx1={18:F5} adx4={19:F5} adxs={20:F5} trend={21:F5} spr={22:F5} ses={23:F5} przc={24:F5} trans={25:F5} prior={26:F5} edge={27:F5} lcb={28:F5} slotScore={29:F5}",
                e.CandidateId, e.SetupKey, V71FamilyKey(e.Signal.PatternName), e.Route, V71ModelId,
                VClamp(e.Signal.GeometryQuality), VClamp(e.Signal.PrzConfluence), VClamp(e.Signal.Confidence),
                VClamp(e.Signal.TimeSymmetry), VClamp(e.Signal.PivotQuality), VClamp(e.ConfirmationScore),
                VClamp(e.NetRR / 4.0), VClamp(e.RegimeScore),
                e.Regime == null ? 0 : VClamp(e.Regime.Efficiency), V71AtrFit(e.Regime),
                e.Regime == null ? 0 : VClamp(e.Regime.ExtensionAtr / 2.0), V71MtfScore(e.Conflict),
                e.AtrPercentile, e.AdxH1Norm, e.AdxH4Norm, e.AdxSlopeNorm, e.TrendStrength,
                e.SpreadAtr, e.SessionPhase, e.PrzCompression, e.TransitionState,
                V71FamilyRoutePrior(e), e.EdgeMean, e.EdgeLcb, e.SlotScore);
        }

        private DateTime V72NextM15Boundary(DateTime utc)
        {
            utc = DateTime.SpecifyKind(utc, DateTimeKind.Utc);
            int minute = (utc.Minute / 15) * 15;
            DateTime baseBar = new DateTime(utc.Year, utc.Month, utc.Day, utc.Hour, minute, 0, DateTimeKind.Utc);
            DateTime next = baseBar.AddMinutes(15);
            return next <= utc ? next.AddMinutes(15) : next;
        }

        private bool V72PreparePullbackEntry(DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            if (e == null || e.Signal == null || !e.ReactionProved) return false;
            double proof = e.ReactionProofPrice;
            double extreme = e.ReactionExtremePrice;
            double displacement = e.Signal.Direction == TradeDirection.Buy ? proof - extreme : extreme - proof;
            if (displacement <= _symbol.PipSize) return false;

            // One deterministic family-agnostic Fibonacci pullback. No selector and no tuning tree.
            double entry = e.Signal.Direction == TradeDirection.Buy
                ? proof - .618 * displacement
                : proof + .618 * displacement;
            double stop = e.Signal.StructuralInvalidation;
            if (!GeometryValid(e.Signal.Direction, entry, stop,
                    e.Signal.Direction == TradeDirection.Buy ? entry + Math.Abs(entry - stop) : entry - Math.Abs(entry - stop)))
                return false;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;

            double canonical, canonicalRr;
            if (!SelectCanonicalBasketTarget(e.Signal, entry, stop, out canonical, out canonicalRr) || canonicalRr < MinimumNetRR)
                return false;

            double costPrice = PipsToPrice(ModeledCostPips());
            double target = e.Signal.Direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            bool canonicalCovers = e.Signal.Direction == TradeDirection.Buy ? canonical >= target : canonical <= target;
            if (!canonicalCovers || !GeometryValid(e.Signal.Direction, entry, stop, target)) return false;

            double netRr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                           Math.Max(1e-9, PriceToPips(risk));
            if (netRr + 1e-9 < MinimumNetRR) return false;

            e.EntryAnchor = entry;
            e.StructuralStop = stop;
            e.CanonicalTarget = target;
            e.RiskDistance = risk;
            e.TargetR = Math.Abs(target - entry) / risk;
            e.NetRR = netRr;
            e.ConfirmationScore = confirmationScore;
            e.RegimeScore = RegimeContextScore(e.Signal, e.Conflict, e.Regime);
            e.ModeledCostR = PipsToPrice(ModeledCostPips()) / risk;
            e.PullbackExpiryUtc = MinDate(e.ExpiryUtc, V72NextM15Boundary(utc));
            if (e.PullbackExpiryUtc <= utc.AddSeconds(1)) return false;
            e.AwaitingPullbackFill = true;
            e.PullbackFilled = false;
            e.ShadowStarted = false;
            e.ArmedUtc = null;
            e.State = V71ExpansionState.ARMED;
            e.EdgeMean = e.NetRR;
            e.EdgeLcb = e.NetRR;
            e.ExpectedSlotHours = Math.Max(.25, (e.PullbackExpiryUtc - utc).TotalHours);
            e.ExpectedSlotHoursUcb = e.ExpectedSlotHours;
            e.SlotScore = e.NetRR / Math.Max(.25, e.ExpectedSlotHours);
            _v71ExpansionArmed++;
            IncrementCounter(_v71FamilyArmed, V71FamilyKey(e.Signal.PatternName));
            Print("[V72-PULLBACK-PLAN] cid={0} family={1} route={2} proof={3:F5} extreme={4:F5} entry={5:F5} stop={6:F5} target={7:F5} rr={8:F3} expiry={9:o}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Route, proof, extreme, entry, stop, target, netRr, e.PullbackExpiryUtc);
            return true;
        }

        private void V71ProcessExpansionM1(int i, DateTime utc)
        {
            foreach (var e in _v71Expansion.Values.Where(x => x.IsActive).ToList())
            {
                bool overlapNow = _executedSetupKeys.Contains(e.SetupKey) || _activeSetupOwners.ContainsKey(e.SetupKey);
                if (overlapNow && !e.CoreOverlapObserved)
                {
                    e.CoreOverlapObserved = true;
                    e.CapitalEligible = false;
                    IncrementCounter(_v71FamilyCoreOverlap, V71FamilyKey(e.Signal.PatternName));
                }

                if (utc >= e.ExpiryUtc)
                {
                    if (e.ShadowStarted && !e.ShadowFinished) V71FinalizeExpansionShadow(e, i, "TTL");
                    e.IsActive = false;
                    e.State = V71ExpansionState.EXPIRED;
                    continue;
                }

                if (!e.ShadowStarted && PatternInvalidatedBeforeEntry(e.Signal))
                {
                    e.IsActive = false;
                    e.State = V71ExpansionState.INVALIDATED;
                    continue;
                }

                if (e.State == V71ExpansionState.WAIT_PRZ)
                {
                    if (BarTouchesPrz(i, e.Signal))
                    {
                        e.PrzTouchUtc = utc;
                        e.State = V71ExpansionState.CONFIRMING;
                    }
                    continue;
                }

                if (e.State == V71ExpansionState.CONFIRMING)
                {
                    if (!e.PrzTouchUtc.HasValue || utc <= e.PrzTouchUtc.Value) continue;
                    // Research observation is intentionally independent from Core ownership.
                    // Core overlap blocks Capital, not evidence collection.
                    if (EnableV72ReactionAlpha)
                    {
                        double lo = _m1Bars.LowPrices[i], hi = _m1Bars.HighPrices[i];
                        if (!e.ReactionExtremeInitialized)
                        {
                            e.ReactionExtremePrice = e.Signal.Direction == TradeDirection.Buy ? lo : hi;
                            e.ReactionExtremeInitialized = true;
                        }
                        else if (e.Signal.Direction == TradeDirection.Buy)
                            e.ReactionExtremePrice = Math.Min(e.ReactionExtremePrice, lo);
                        else
                            e.ReactionExtremePrice = Math.Max(e.ReactionExtremePrice, hi);
                    }

                    V71RefreshExpansionDecisionContext(e);
                    double score;
                    if (V71ExpansionM1Confirmation(i, e, out score))
                    {
                        if (EnableV72ReactionAlpha)
                        {
                            e.ReactionProved = true;
                            e.ReactionProofUtc = utc;
                            e.ReactionProofPrice = _m1Bars.ClosePrices[i];
                            e.ReactionScore = score;
                            Print("[V72-REACTION-PROVED] cid={0} family={1} route={2} score={3:F3} proof={4:F5} extreme={5:F5}",
                                e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Route, score, e.ReactionProofPrice, e.ReactionExtremePrice);
                            if (!V72PreparePullbackEntry(utc, e, score))
                            {
                                e.IsActive = false;
                                e.State = V71ExpansionState.REJECTED;
                                Print("[V72-PULLBACK-REJECT] cid={0} reason=NO_LEGAL_0618_ENTRY", e.CandidateId);
                            }
                        }
                        else V71ArmExpansion(i, utc, e, score);
                    }
                    continue;
                }

                if (e.State == V71ExpansionState.ARMED && !e.ShadowFinished)
                {
                    if (EnableV72ReactionAlpha && e.AwaitingPullbackFill)
                    {
                        if (utc >= e.PullbackExpiryUtc)
                        {
                            e.IsActive = false;
                            e.State = V71ExpansionState.EXPIRED;
                            Print("[V72-PULLBACK-EXPIRE] cid={0}", e.CandidateId);
                            continue;
                        }
                        bool touched = e.Signal.Direction == TradeDirection.Buy
                            ? _m1Bars.LowPrices[i] <= e.EntryAnchor
                            : _m1Bars.HighPrices[i] >= e.EntryAnchor;
                        if (!touched) continue;

                        // Pending order existed before this completed M1 bar. Start path at planned limit price.
                        e.AwaitingPullbackFill = false;
                        e.PullbackFilled = true;
                        e.ShadowStarted = true;
                        e.ArmedUtc = utc;
                        e.ShadowPeakR = 0;
                        e.ShadowProtectionR = -1.0;
                        Print("[V72-PULLBACK-FILL-SHADOW] cid={0} entry={1:F5} utc={2:o}", e.CandidateId, e.EntryAnchor, utc);

                        bool sameBarStop = e.Signal.Direction == TradeDirection.Buy
                            ? _m1Bars.LowPrices[i] <= e.StructuralStop
                            : _m1Bars.HighPrices[i] >= e.StructuralStop;
                        bool sameBarTarget = e.Signal.Direction == TradeDirection.Buy
                            ? _m1Bars.HighPrices[i] >= e.CanonicalTarget
                            : _m1Bars.LowPrices[i] <= e.CanonicalTarget;
                        if (sameBarStop || sameBarTarget)
                        {
                            e.PathState = -2;
                            e.PathUsable = false;
                            V71FinalizeExpansionShadow(e, i, "PULLBACK_FILL_SAME_BAR_AMBIGUOUS");
                            continue;
                        }
                        continue;
                    }

                    if (!e.ShadowStarted || !e.ArmedUtc.HasValue || utc <= e.ArmedUtc.Value) continue;

                    e.ShadowBars++;
                    double high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i], close = _m1Bars.ClosePrices[i];
                    double risk = Math.Max(e.RiskDistance, _symbol.PipSize);
                    double favR = e.Signal.Direction == TradeDirection.Buy
                        ? (high - e.EntryAnchor) / risk
                        : (e.EntryAnchor - low) / risk;
                    double adverseR = e.Signal.Direction == TradeDirection.Buy
                        ? (e.EntryAnchor - low) / risk
                        : (high - e.EntryAnchor) / risk;
                    double closeR = e.Signal.Direction == TradeDirection.Buy
                        ? (close - e.EntryAnchor) / risk
                        : (e.EntryAnchor - close) / risk;
                    double priorPeak = e.ShadowPeakR;

                    // V72 payoff-preservation kernel. Protection can only have been armed
                    // by a PRIOR completed M1 bar, so this never resolves same-bar ordering
                    // with future information.
                    if (EnableV72ReactionAlpha && e.PathState == 0 && e.V72ProtectionActive)
                    {
                        double protectedR = .10;
                        double protectedPrice = e.Signal.Direction == TradeDirection.Buy
                            ? e.EntryAnchor + protectedR * risk
                            : e.EntryAnchor - protectedR * risk;
                        bool protectedExit = e.Signal.Direction == TradeDirection.Buy
                            ? low <= protectedPrice
                            : high >= protectedPrice;
                        if (protectedExit)
                        {
                            e.PathState = 2;
                            e.PathUsable = true;
                            V71FinalizeExpansionShadow(e, i, "V72_EARLY_CAPITAL_PROTECT", protectedR);
                            continue;
                        }
                    }

                    // Native-exit counterfactual is recorded once but no longer terminates
                    // the structural path study. This separates Entry Alpha from Exit Alpha.
                    if (!e.NativeExitCaptured)
                    {
                        double protectionPrice = e.Signal.Direction == TradeDirection.Buy
                            ? e.EntryAnchor + e.ShadowProtectionR * risk
                            : e.EntryAnchor - e.ShadowProtectionR * risk;
                        bool protectedStop = e.Signal.Direction == TradeDirection.Buy
                            ? low <= protectionPrice
                            : high >= protectionPrice;
                        bool target = e.Signal.Direction == TradeDirection.Buy
                            ? high >= e.CanonicalTarget
                            : low <= e.CanonicalTarget;
                        if (protectedStop)
                        {
                            e.NativeExitCaptured = true;
                            e.NativeExitR = e.ShadowProtectionR;
                            e.NativeExitResult = "V51_NATIVE_PROXY_PROTECTION";
                        }
                        else if (target)
                        {
                            e.NativeExitCaptured = true;
                            e.NativeExitR = Math.Max(0, e.TargetR);
                            e.NativeExitResult = "V51_NATIVE_PROXY_TARGET";
                        }
                        else
                        {
                            double ageMinutes = Math.Max(0, (utc - e.ArmedUtc.Value).TotalMinutes);
                            if (ageMinutes >= NoMfeMinAgeMinutes && priorPeak < NoMfeProofR && closeR <= -Math.Abs(NoMfeKillR))
                            {
                                e.NativeExitCaptured = true;
                                e.NativeExitR = Math.Max(-1.0, closeR);
                                e.NativeExitResult = "V51_NATIVE_PROXY_NO_MFE";
                            }
                        }
                    }

                    if (favR > e.ShadowPeakR)
                    {
                        e.ShadowPeakR = favR;
                        e.TimeToMfeBars = e.ShadowBars;
                    }
                    e.ShadowMfeR = Math.Max(e.ShadowMfeR, favR);
                    e.ShadowMaeR = Math.Max(e.ShadowMaeR, adverseR);
                    e.ShadowMaxGivebackR = Math.Max(e.ShadowMaxGivebackR, Math.Max(0, e.ShadowPeakR - closeR));

                    if (e.TimeTo05R < 0 && favR >= .50) e.TimeTo05R = e.ShadowBars;
                    if (e.TimeTo1R < 0 && favR >= 1.00) e.TimeTo1R = e.ShadowBars;
                    if (e.TimeTo2R < 0 && favR >= 2.00) e.TimeTo2R = e.ShadowBars;
                    if (e.TimeToStopR < 0 && adverseR >= 1.00) e.TimeToStopR = e.ShadowBars;

                    if (e.PathState == 0)
                    {
                        double targetPathR = EnableV72ReactionAlpha ? Math.Max(2.0, e.TargetR) : 2.00;
                        bool hit2 = favR >= targetPathR;
                        bool hitStop = adverseR >= 1.00;
                        if (hit2 && hitStop)
                        {
                            e.PathState = -2;
                            e.PathUsable = false;
                            V71FinalizeExpansionShadow(e, i, "PATH_AMBIGUOUS_SAME_BAR");
                            continue;
                        }
                        if (hitStop)
                        {
                            e.PathState = -1;
                            e.PathUsable = true;
                            V71FinalizeExpansionShadow(e, i, "STRUCTURAL_STOP_FIRST");
                            continue;
                        }
                        if (hit2)
                        {
                            e.PathState = 1;
                            e.PathUsable = true;
                            if (EnableV72ReactionAlpha)
                            {
                                V71FinalizeExpansionShadow(e, i, "V72_FIXED_2R_TARGET", 2.0);
                                continue;
                            }
                        }
                    }

                    if (EnableV72ReactionAlpha && !e.V72ProtectionActive && e.PathState == 0 &&
                        favR >= .50 && adverseR < 1.00)
                    {
                        e.V72ProtectionActive = true;
                        e.ShadowProtectionR = Math.Max(e.ShadowProtectionR, .10);
                    }

                    if (!e.NativeExitCaptured)
                    {
                        if (e.ShadowPeakR >= BreakEvenTriggerR)
                            e.ShadowProtectionR = Math.Max(e.ShadowProtectionR, Math.Max(0, BreakEvenLockR));
                        if (e.ShadowPeakR >= TrailTriggerR)
                        {
                            double trail = FibonacciStructureTrail(e.Signal.Direction);
                            if (trail > 0)
                            {
                                double trailR = e.Signal.Direction == TradeDirection.Buy
                                    ? (trail - e.EntryAnchor) / risk
                                    : (e.EntryAnchor - trail) / risk;
                                e.ShadowProtectionR = Math.Max(e.ShadowProtectionR, trailR);
                            }
                        }
                        e.ShadowProtectionR = Math.Min(e.ShadowProtectionR, Math.Max(0, e.TargetR));
                    }

                    if (e.ShadowBars >= Math.Max(30, V71ExpansionShadowHorizonM1Bars))
                        V71FinalizeExpansionShadow(e, i, "STRUCTURAL_HORIZON");
                }
            }

            if (_v71Expansion.Count > 16000)
            {
                foreach (var k in _v71Expansion.Where(kv => !kv.Value.IsActive && kv.Value.ShadowFinished)
                    .OrderBy(kv => kv.Value.DetectedUtc).Take(_v71Expansion.Count - 12000).Select(kv => kv.Key).ToList())
                    _v71Expansion.Remove(k);
            }
        }

        private void V71FinalizeExpansionShadow(V71ExpansionCandidate e, int i, string result, double? forcedR = null)
        {
            if (e == null || e.ShadowFinished || !e.ShadowStarted || e.RiskDistance <= 0) return;
            double close = i >= 0 && i < _m1Bars.Count ? _m1Bars.ClosePrices[i] :
                           (e.Signal.Direction == TradeDirection.Buy ? _symbol.Bid : _symbol.Ask);
            double closeR = (e.Signal.Direction == TradeDirection.Buy ? close - e.EntryAnchor : e.EntryAnchor - close) / e.RiskDistance;

            double structuralR;
            if (forcedR.HasValue) structuralR = forcedR.Value;
            else if (e.PathState == 1) structuralR = 2.0;
            else if (e.PathState == -1) structuralR = -1.0;
            else structuralR = Math.Max(-1.0, Math.Min(2.0, closeR));

            if (!e.NativeExitCaptured)
            {
                e.NativeExitCaptured = true;
                e.NativeExitR = Math.Max(-1.0, Math.Min(Math.Max(0, e.TargetR), closeR));
                e.NativeExitResult = "V51_NATIVE_PROXY_" + result;
            }

            e.ShadowOutcomeR = structuralR;
            e.ShadowFinished = true;
            e.IsActive = false;
            _v71ExpansionShadowClosed++;
            IncrementCounter(_v71FamilyShadowClosed, V71FamilyKey(e.Signal.PatternName));
            Print("[V71-EXP-SHADOW] cid={0} setup={1} family={2} role={3} route={4} coreOverlap={5} capitalEligible={6} g={7:F6} prz={8:F6} conf={9:F6} ts={10:F6} pv={11:F6} m1={12:F6} rr={13:F6} reg={14:F6} eff={15:F6} atr={16:F6} ext={17:F6} mtf={18:F6} atp={19:F6} adx1={20:F6} adx4={21:F6} adxs={22:F6} trend={23:F6} spr={24:F6} ses={25:F6} przc={26:F6} trans={27:F6} survival={28:F6} structuralR={29:F6} nativeR={30:F6} nativeResult={31} pathState={32} pathUsable={33} mfeR={34:F6} maeR={35:F6} t05={36} t1={37} t2={38} tstop={39} tmfe={40} givebackR={41:F6} result={42} bars={43} costR={44:F6} label=STRUCTURAL_PATH_PLUS_NATIVE_EXIT_COMPLETED_M1",
                e.CandidateId, e.SetupKey, V71FamilyKey(e.Signal.PatternName), e.AbcdRole, e.Route,
                e.CoreOverlapObserved, e.CapitalEligible,
                VClamp(e.Signal.GeometryQuality), VClamp(e.Signal.PrzConfluence), VClamp(e.Signal.Confidence),
                VClamp(e.Signal.TimeSymmetry), VClamp(e.Signal.PivotQuality), VClamp(e.ConfirmationScore),
                VClamp(e.NetRR / 4.0), VClamp(e.RegimeScore),
                e.Regime == null ? 0 : VClamp(e.Regime.Efficiency), V71AtrFit(e.Regime),
                e.Regime == null ? 0 : VClamp(e.Regime.ExtensionAtr / 2.0), V71MtfScore(e.Conflict),
                e.AtrPercentile, e.AdxH1Norm, e.AdxH4Norm, e.AdxSlopeNorm, e.TrendStrength,
                e.SpreadAtr, e.SessionPhase, e.PrzCompression, e.TransitionState, e.SurvivalProbability,
                structuralR, e.NativeExitR, e.NativeExitResult ?? "NONE", e.PathState, e.PathUsable,
                e.ShadowMfeR, e.ShadowMaeR, e.TimeTo05R, e.TimeTo1R, e.TimeTo2R, e.TimeToStopR,
                e.TimeToMfeBars, e.ShadowMaxGivebackR, result, e.ShadowBars, e.ModeledCostR);
        }

        private void V71FinalizeExpansionShadows()
        {
            int i = LastClosedIndex(_m1Bars);
            foreach (var e in _v71Expansion.Values.Where(x => x.ShadowStarted && !x.ShadowFinished).ToList())
                V71FinalizeExpansionShadow(e, i, "BACKTEST_END");
        }

        private bool V71CoreHasActiveThesis()
        {
            return _candidates.Values.Any(x => x.IsActive);
        }

        private void V71PreemptExpansionForCore(DateTime now)
        {
            if (!EnableV71ExpansionExecution || !V71CoreHasActiveThesis()) return;
            foreach (var basket in _baskets.Values
                .Where(b => b.IsActive && !string.IsNullOrWhiteSpace(b.CandidateId) &&
                            b.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                .ToList())
            {
                CancelBasketPending(basket, "V51_CORE_PREEMPT");
                CloseBasketPositions(basket, "V51_CORE_PREEMPT");
                bool hasPosition = OwnPositions().Any(p => LabelBasketId(p.Label) == basket.BasketId);
                bool hasPending = OwnPendingOrders().Any(o => LabelBasketId(o.Label) == basket.BasketId);
                if (!hasPosition && !hasPending)
                {
                    basket.State = FibonacciBasketState.CANCELLED;
                    basket.IsActive = false;
                }
                Print("[V71-EXP-PREEMPT] basket={0} candidate={1} coreActive={2} utc={3:o}",
                    basket.BasketId, basket.CandidateId, V71CoreHasActiveThesis(), now);
            }
        }

        private void V71RecordCoreExecution(CandidateRecord c)
        {
            if (c == null || c.V71Expansion || c.Signal == null) return;
            string token = (c.SetupKey ?? "") + "|" + c.Signal.PatternName + "|" + c.Route + "|" + c.Signal.Direction + ";";
            unchecked
            {
                foreach (char ch in token)
                {
                    _v71CoreExecutionFnv ^= (byte)(ch & 0xFF);
                    _v71CoreExecutionFnv *= 1099511628211UL;
                    if (ch > 0xFF)
                    {
                        _v71CoreExecutionFnv ^= (byte)((ch >> 8) & 0xFF);
                        _v71CoreExecutionFnv *= 1099511628211UL;
                    }
                }
            }
            _v71CoreExecutionCount++;
        }

        private double V71ExpansionContributionNet()
        {
            double open = 0;
            foreach (var p in OwnPositions())
            {
                PositionLedger ledger;
                FibonacciBasket basket;
                if (!_positions.TryGetValue(p.Id, out ledger) || string.IsNullOrWhiteSpace(ledger.BasketId) ||
                    !_baskets.TryGetValue(ledger.BasketId, out basket) || string.IsNullOrWhiteSpace(basket.CandidateId) ||
                    !basket.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                    continue;
                open += p.NetProfit;
            }
            return _v71ExpansionRealizedNet + open;
        }

        private bool V71ExpansionRiskReserveAllows(double riskPct)
        {
            double pct = Math.Min(5.0, Math.Max(.10, riskPct));
            double corePct = Math.Min(5.0, Math.Max(.10, BasketRiskPercent));
            double plannedRisk = Math.Max(0, Account.Equity) * pct / 100.0;
            double coreReserve = Math.Max(0, Account.Equity) * corePct / 100.0;
            double sleeveBudget = Math.Max(0, _initialEquity) * corePct / 100.0;
            double contribution = V71ExpansionContributionNet();

            // Expansion may spend its own accumulated profit, but it may not create a
            // cumulative loss larger than one frozen V51 core basket risk unit.
            if (contribution - plannedRisk < -sleeveBudget - 1e-8)
            {
                _v71ExpansionRiskReserveBlocked++;
                return false;
            }

            double peakBudget = Math.Max(0, _equityPeak) * Math.Max(0, MaxDrawdownPercent) / 100.0;
            double peakUsed = Math.Max(0, _equityPeak - Account.Equity);
            double peakHeadroom = Math.Max(0, peakBudget - peakUsed);
            double dayBudget = Math.Max(0, _dayStartEquity) * Math.Max(0, DailyLossLimitPercent) / 100.0;
            double dayUsed = Math.Max(0, _dayStartEquity - Account.Equity);
            double dayHeadroom = Math.Max(0, dayBudget - dayUsed);

            // Preserve enough causal headroom for the next legal V51 core basket.
            if (plannedRisk + coreReserve > peakHeadroom + 1e-8 ||
                plannedRisk + coreReserve > dayHeadroom + 1e-8)
            {
                _v71ExpansionRiskReserveBlocked++;
                return false;
            }
            return true;
        }

        private double V71ExpansionRiskFor(V71ExpansionCandidate e)
        {
            double cap = Math.Min(5.0, Math.Max(.10, V71ExpansionRiskPercent));
            double requested = 1.0;
            if (EnableV71ExpansionAdaptiveRisk)
            {
                if (e != null && e.EdgeLcb >= .15) requested = 2.0;
                if (e != null && e.EdgeLcb >= .30) requested = 3.0;
                if (e != null && e.EdgeLcb >= .50) requested = 5.0;
            }
            requested = Math.Min(cap, requested);

            // Protected-Core invariant: expansion capacity research cannot consume more
            // per basket than the frozen core risk unit before Alpha is qualified.
            double protectedCap = Math.Min(cap, Math.Min(5.0, Math.Max(.10, BasketRiskPercent)));
            double r = Math.Min(requested, protectedCap);
            if (requested > r + 1e-9) _v71ExpansionRiskCapped++;
            if (r > 1.000001) _v71ExpansionRiskScaled++;
            return r;
        }

        private double V71CandidateRiskPercent(CandidateRecord c)
        {
            if (c != null && c.V71Expansion)
                return Math.Min(5.0, Math.Max(.10, c.V71RiskPercent));
            return Math.Min(5.0, Math.Max(.10, BasketRiskPercent));
        }

        private bool V71BuildExpansionSingleLeg(CandidateRecord c)
        {
            if (c == null || c.Signal == null || c.Signal.Profile == null) return false;
            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double distance = Math.Abs(anchor - stop);
            if (PriceToPips(distance) < MinStopLossPips) return false;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(c.Signal, anchor, stop, out target, out netRr) || netRr < MinimumNetRR)
                return false;

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = distance,
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = MinDate(c.ExpiryUtc, Server.Time.ToUniversalTime().AddMinutes(Math.Max(15, c.Signal.Profile.PendingTtlMinutes))),
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold,
                CanonicalTarget = target,
                ExpectedNetRR = netRr,
                ExpectedWeightedEntry = anchor,
                VirtualWeightedEntry = anchor
            };
            if (plan.BasketRiskAmount <= 0) return false;

            double slPips = PriceToPips(distance);
            double minRisk = _symbol.VolumeInUnitsMin * _symbol.PipValue * (slPips + ModeledCostPips());
            plan.Legs.Add(new FibonacciGridLeg
            {
                Index = 0, Fraction = 0, PlannedPrice = anchor, RiskWeight = 1.0,
                RiskBudget = plan.BasketRiskAmount, MinBrokerRisk = minRisk,
                Volume = 0, PlannedRisk = 0, ModeledCost = 0, Physical = false,
                State = GridLegState.VIRTUAL_ONLY
            });
            plan.LogicalLegCount = 1;
            if (!ConfigureCapitalExecution(plan)) return false;
            if (plan.Legs.Count == 0 || !plan.Legs[0].Physical || plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) return false;

            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = netRr;
            return true;
        }

        private bool V72BuildPullbackSingleLeg(CandidateRecord c, V71ExpansionCandidate e)
        {
            if (c == null || e == null || c.Signal == null || !e.AwaitingPullbackFill) return false;
            double anchor = e.EntryAnchor;
            double stop = e.StructuralStop;
            double target = e.CanonicalTarget;
            double distance = Math.Abs(anchor - stop);
            if (PriceToPips(distance) < MinStopLossPips || e.NetRR < MinimumNetRR) return false;

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = distance,
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = e.PullbackExpiryUtc,
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold,
                CanonicalTarget = target,
                ExpectedNetRR = e.NetRR,
                ExpectedWeightedEntry = anchor,
                VirtualWeightedEntry = anchor
            };
            if (plan.BasketRiskAmount <= 0 || plan.ExpirationUtc <= Server.Time.ToUniversalTime().AddSeconds(1)) return false;
            double slPips = PriceToPips(distance);
            double minRisk = _symbol.VolumeInUnitsMin * _symbol.PipValue * (slPips + ModeledCostPips());
            plan.Legs.Add(new FibonacciGridLeg
            {
                Index = 0, Fraction = .618, PlannedPrice = anchor, RiskWeight = 1.0,
                RiskBudget = plan.BasketRiskAmount, MinBrokerRisk = minRisk,
                Volume = 0, PlannedRisk = 0, ModeledCost = 0, Physical = false,
                State = GridLegState.VIRTUAL_ONLY
            });
            plan.LogicalLegCount = 1;
            if (!ConfigureCapitalExecution(plan)) return false;
            if (plan.Legs.Count == 0 || !plan.Legs[0].Physical || plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) return false;
            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = e.NetRR;
            return true;
        }

        private bool V72SubmitPullbackSingleLeg(CandidateRecord c)
        {
            var plan = c == null ? null : c.GridPlan;
            if (plan == null || plan.Legs.Count != 1) return false;
            if (Account.FreeMargin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) return false;
            if (plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) { _gridRiskViolations++; return false; }

            string basketId = NewBasketId();
            plan.BasketId = basketId;
            var basket = new FibonacciBasket
            {
                BasketId = basketId, CandidateId = c.CandidateId, Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction, Route = c.Route, State = FibonacciBasketState.PLANNED,
                CreatedUtc = Server.Time.ToUniversalTime(), ExpirationUtc = plan.ExpirationUtc,
                EntryAnchor = plan.EntryAnchor, StructuralStop = plan.StructuralStop,
                CanonicalTarget = plan.CanonicalTarget, InitialBasketRisk = plan.BasketRiskAmount,
                PlannedWorstCaseRisk = plan.WorstCaseRisk, ProtectionFrontier = plan.StructuralStop,
                Plan = plan, Candidate = c, IsActive = true
            };
            _baskets[basketId] = basket;
            CountPipeline(c.Signal.PatternName).BasketPlanned++;
            BasketEvent(basket, "V72_PULLBACK_BASKET_PLANNED");

            var l0 = plan.Legs[0];
            if (!PlaceGridLimit(basket, l0))
            {
                basket.State = FibonacciBasketState.CANCELLED;
                basket.IsActive = false;
                return false;
            }
            basket.State = FibonacciBasketState.GRID_PENDING;
            Transition(c, CandidateState.EXECUTED, "V72_PULLBACK_LIMIT_SUBMITTED");
            if (!string.IsNullOrWhiteSpace(c.SetupKey)) _v71ExpansionExecutedSetupKeys.Add(c.SetupKey);
            BasketEvent(basket, "V72_PULLBACK_LIMIT_SUBMITTED");
            return true;
        }

        private double V71CapitalQualificationScore(V71ExpansionCandidate e)
        {
            if (e == null) return double.NegativeInfinity;
            return V71W("slot_gate") > .5 ? e.SlotScore : e.EdgeLcb;
        }

        private void V71ApplyExpansionExitPolicy(V71ExpansionCandidate e, CandidateRecord c)
        {
            if (e == null || c == null || c.GridPlan == null) return;
            string policy = (V71ExpansionExitPolicy ?? "REACTION_2R").Trim().ToUpperInvariant();
            bool runner = policy == "SELECTIVE_RUNNER" && e.RunnerLcb > Math.Max(.50, V71W("runner_gate"));
            if (runner) return;

            double entry = c.GridPlan.ExpectedWeightedEntry > 0 ? c.GridPlan.ExpectedWeightedEntry : c.GridPlan.EntryAnchor;
            double risk = Math.Abs(entry - c.GridPlan.StructuralStop);
            if (risk <= 0) return;
            double grossR = 2.0 + PipsToPrice(ModeledCostPips()) / risk;
            double target = c.Signal.Direction == TradeDirection.Buy ? entry + risk * grossR : entry - risk * grossR;
            if (!GeometryValid(c.Signal.Direction, entry, c.GridPlan.StructuralStop, target)) return;

            if (c.Signal.Direction == TradeDirection.Buy)
                target = Math.Min(target, c.GridPlan.CanonicalTarget);
            else
                target = Math.Max(target, c.GridPlan.CanonicalTarget);
            if (!GeometryValid(c.Signal.Direction, entry, c.GridPlan.StructuralStop, target)) return;

            c.GridPlan.CanonicalTarget = target;
            c.GridPlan.ExpectedNetRR = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                Math.Max(1e-9, PriceToPips(risk));
            c.SelectedTarget = target;
            c.NetRR = c.GridPlan.ExpectedNetRR;
        }

        private void V71TryExecuteExpansion(DateTime now)
        {
            if (!EnableV71ExpansionExecution || (!EnableV72ReactionAlpha && !_v71ModelReady)) return;
            if (V71CoreHasActiveThesis()) { _v71ExpansionCoreBlocked++; return; }
            if (OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)) return;
            if (!IsInstitutionalSession(now) || !SpreadValid()) return;

            var eligible = _v71Expansion.Values
                .Where(e => e.IsActive && e.State == V71ExpansionState.ARMED && !e.Executed &&
                            e.CapitalEligible && !e.CoreOverlapObserved &&
                            (EnableV72ReactionAlpha
                                ? (e.ReactionProved && e.AwaitingPullbackFill && e.NetRR >= MinimumNetRR)
                                : (V71FamilyRouteAllowed(e) && V71SetupAllowed(e) && e.SupportEligible && e.EdgeLcb > 0 &&
                                   (V71W("h5") <= .5 || e.PathLcb > V71PathBreakEven(e)) &&
                                   V71CapitalQualificationScore(e) > V71ExpansionMinEdgeLcbR && e.NetRR >= MinimumNetRR)) &&
                            !_executedSetupKeys.Contains(e.SetupKey) &&
                            !_v71ExpansionExecutedSetupKeys.Contains(e.SetupKey))
                .OrderByDescending(e => e.SlotScore)
                .ThenByDescending(e => e.EdgeLcb)
                .ToList();
            if (eligible.Count == 0)
            {
                if (_v71Expansion.Values.Any(e => e.IsActive && e.State == V71ExpansionState.ARMED &&
                    (!e.CapitalEligible || e.CoreOverlapObserved ||
                     (EnableV72ReactionAlpha
                        ? (!e.ReactionProved || !e.AwaitingPullbackFill || e.NetRR < MinimumNetRR)
                        : (!V71FamilyRouteAllowed(e) || !V71SetupAllowed(e) || !e.SupportEligible ||
                           e.EdgeLcb <= 0 || (V71W("h5") > .5 && e.PathLcb <= V71PathBreakEven(e)) ||
                           V71CapitalQualificationScore(e) <= V71ExpansionMinEdgeLcbR)))))
                    _v71ExpansionModelRejected++;
                return;
            }

            var e = eligible[0];
            double riskPct = V71ExpansionRiskFor(e);
            if (!V71ExpansionRiskReserveAllows(riskPct)) return;
            var c = new CandidateRecord
            {
                CandidateId = e.CandidateId,
                SetupKey = e.SetupKey,
                Signal = e.Signal,
                State = CandidateState.EXECUTABLE,
                IsActive = true,
                DetectedUtc = e.DetectedUtc,
                ExpiryUtc = e.ExpiryUtc,
                PrzTouchUtc = e.PrzTouchUtc,
                Conflict = e.Conflict,
                Route = e.Route,
                Regime = e.Regime,
                ConfirmationScore = e.ConfirmationScore,
                NetRR = e.NetRR,
                SelectedTarget = e.CanonicalTarget,
                V71Expansion = true,
                V72ReactionAlpha = EnableV72ReactionAlpha,
                V71RiskPercent = riskPct
            };

            bool built = EnableV72ReactionAlpha
                ? V72BuildPullbackSingleLeg(c, e)
                : (EnableV71ExpansionGrid ? TryBuildFibonacciGridPlan(c) : V71BuildExpansionSingleLeg(c));
            if (!built && !EnableV72ReactionAlpha && EnableV71ExpansionGrid)
            {
                c.GridPlan = null;
                _v71ExpansionGridFallback++;
                built = V71BuildExpansionSingleLeg(c);
            }

            if (!built || c.GridPlan == null || c.NetRR < MinimumNetRR) return;
            if (!EnableV72ReactionAlpha) V71ApplyExpansionExitPolicy(e, c);
            if (c.GridPlan == null || c.NetRR < MinimumNetRR) return;

            Print("[V71-EXP-EXECUTE] cid={0} setup={1} family={2} route={3} model={4} edge={5:F5} lcb={6:F5} slotScore={7:F5} riskPct={8:F2} grid={9}",
                e.CandidateId, e.SetupKey, V71FamilyKey(e.Signal.PatternName), e.Route, V71ModelId,
                e.EdgeMean, e.EdgeLcb, e.SlotScore, riskPct, EnableV71ExpansionGrid);

            bool submitted = EnableV72ReactionAlpha ? V72SubmitPullbackSingleLeg(c) : true;
            if (!EnableV72ReactionAlpha) ExecuteFibonacciGridPlan(c);
            if ((EnableV72ReactionAlpha && submitted) || c.State == CandidateState.EXECUTED)
            {
                e.Executed = true;
                e.IsActive = false;
                e.State = V71ExpansionState.EXECUTED;
                _v71ExpansionExecuted++;
            }
        }

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

                int start = Math.Max(0, pivots.Count - 36);
                for (int i = start; i <= pivots.Count - 5; i++)
                {
                    var x = pivots[i];
                    var a = pivots[i + 1];
                    var b = pivots[i + 2];
                    var c = pivots[i + 3];
                    var d = pivots[i + 4];

                    foreach (var profile in _profiles)
                    {
                        PatternSignal sig;
                        if (!TryMatchProfile(profile, x, a, b, c, d, atr, bars.OpenTimes[d.Index], timeframe, scale, out sig))
                            continue;
                        if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars)) continue;
                        if (scale != depth) _independentScaleCandidates++;
                        result.Add(sig);
                    }
                }
            }

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

        private bool V71SparseLegInsideEnvelope(List<PivotPoint> pivots, int left, int right)
        {
            if (pivots == null || left < 0 || right >= pivots.Count || left >= right) return false;
            double lo = Math.Min(pivots[left].Price, pivots[right].Price);
            double hi = Math.Max(pivots[left].Price, pivots[right].Price);
            double eps = Math.Max(_symbol.PipSize, (hi - lo) * 1e-9);
            for (int k = left + 1; k < right; k++)
                if (pivots[k].Price < lo - eps || pivots[k].Price > hi + eps) return false;
            return true;
        }

        private string V71AbcdResearchRole(PatternSignal s, List<PatternSignal> universe)
        {
            if (s == null || !string.Equals(V71FamilyKey(s.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                return "PARENT_FAMILY";
            string geometry = BuildSetupGeometryKey(s);
            bool sameGeometryParent = universe.Any(x => x != null &&
                !string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase) &&
                BuildSetupGeometryKey(x) == geometry);
            if (sameGeometryParent) return "ABCD_PARENT_COMPLETION";

            double mid = (s.PrzLow + s.PrzHigh) * .5;
            double half = Math.Max(_symbol.PipSize, Math.Abs(s.PrzHigh - s.PrzLow) * .5);
            bool terminalConfluence = universe.Any(x => x != null &&
                !string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase) &&
                x.Direction == s.Direction && x.PivotScale == s.PivotScale &&
                Math.Abs((x.PrzLow + x.PrzHigh) * .5 - mid) <=
                    half + Math.Max(_symbol.PipSize, Math.Abs(x.PrzHigh - x.PrzLow) * .5));
            if (terminalConfluence) return "ABCD_PRZ_CONFLUENCE";

            if ((s.HarmonicSubtype == "ABCD_EXACT" || s.HarmonicSubtype == "ABCD_NEAR_127") &&
                s.GeometryQuality >= .70 && s.PrzConfluence >= .70)
                return "ABCD_TERMINALITY";
            return "ABCD_STANDALONE";
        }

        private void V71CountExpansionReject(string pattern, string reason)
        {
            string key = V71FamilyKey(pattern) + "|" + (reason ?? "UNKNOWN");
            int n;
            _v71ExpansionRejectAttribution.TryGetValue(key, out n);
            _v71ExpansionRejectAttribution[key] = n + 1;
        }

        private bool V71ExpansionPrimaryContractPass(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            double atr, out string reason)
        {
            reason = "PASS";
            bool bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
            bool bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
            if (!bullish && !bearish) { reason = "DIRECTION_FAIL"; return false; }

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0 || atr <= 0) { reason = "DEGENERATE_LEG"; return false; }
            if (Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) < atr * .45) { reason = "LEG_TOO_SMALL"; return false; }

            double xab = ab / xa;
            double abc = bc / ab;
            double bcd = cd / bc;
            double adxa = Math.Abs(d.Price - a.Price) / xa;
            double xdxa = Math.Abs(d.Price - x.Price) / xa;
            double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;
            double abcd = cd / ab;
            double xc = Math.Abs(c.Price - x.Price);

            if (p.Mode == PatternMode.STANDARD)
            {
                if (!InRange(xab, p.XabMin, p.XabMax)) { reason = "XAB_FAIL"; return false; }
                if (!InRange(abc, p.AbcMin, p.AbcMax)) { reason = "ABC_FAIL"; return false; }
                if (!InRange(bcd, p.BcdMin, p.BcdMax)) { reason = "BCD_FAIL"; return false; }
                if (!InRange(xad, p.XadMin, p.XadMax)) { reason = "XAD_FAIL"; return false; }

                // Expansion PRZ is projected only from pre-D legs.
                double przHalf = atr * p.PrzWidthAtr;
                if (EnableFamilyNativeConversion &&
                    (p.Name == "Crab" || p.Name == "Deep Crab" || p.Name == "Butterfly" || p.Name == "Alt Bat"))
                    przHalf *= 1.20;
                else if (EnableFamilyNativeConversion)
                    przHalf *= .90;

                double xaD1 = bullish ? a.Price - p.XadMin * xa : a.Price + p.XadMin * xa;
                double xaD2 = bullish ? a.Price - p.XadMax * xa : a.Price + p.XadMax * xa;
                double bcD1 = bullish ? c.Price - p.BcdMin * bc : c.Price + p.BcdMin * bc;
                double bcD2 = bullish ? c.Price - p.BcdMax * bc : c.Price + p.BcdMax * bc;
                double coreLo = Math.Max(Math.Min(xaD1, xaD2), Math.Min(bcD1, bcD2));
                double coreHi = Math.Min(Math.Max(xaD1, xaD2), Math.Max(bcD1, bcD2));
                if (coreLo > coreHi) { reason = "PRZ_NO_INTERSECTION"; return false; }
                if (d.Price < coreLo - przHalf || d.Price > coreHi + przHalf) { reason = "D_OUTSIDE_PROJECTED_PRZ"; return false; }
                return true;
            }

            if (p.Mode == PatternMode.ABCD)
            {
                if (!InRange(abc, p.AbcMin, p.AbcMax)) { reason = "ABC_FAIL"; return false; }
                if (!InRange(bcd, p.BcdMin, p.BcdMax)) { reason = "BCD_FAIL"; return false; }
                if (!InRange(abcd, p.AbcDMin, p.AbcDMax)) { reason = "ABCD_COMPLETION_FAIL"; return false; }
                return true;
            }

            if (p.Mode == PatternMode.CYPHER)
            {
                if (!InRange(xab, .382, .618)) { reason = "XAB_FAIL"; return false; }
                double xac = xc / xa;
                if (!InRange(xac, 1.13, 1.414)) { reason = "XAC_FAIL"; return false; }
                if (!InRange(cd / Math.Max(xc, 1e-9), .70, .90)) { reason = "CD_XC_FAIL"; return false; }
                return true;
            }

            if (p.Mode == PatternMode.SHARK)
            {
                if (!InRange(abc, 1.13, 1.618)) { reason = "ABC_FAIL"; return false; }
                if (!InRange(bcd, 1.13, 2.24)) { reason = "BCD_FAIL"; return false; }
                if (!InRange(xad, .85, 1.25)) { reason = "XAD_FAIL"; return false; }
                return true;
            }

            if (p.Mode == PatternMode.FIVEZERO)
            {
                if (!InRange(xab, 1.13, 1.618)) { reason = "XAB_FAIL"; return false; }
                if (!InRange(abc, 1.618, 2.24)) { reason = "ABC_FAIL"; return false; }
                if (!InRange(bcd, .45, .65)) { reason = "BCD_FAIL"; return false; }
                return true;
            }

            reason = "UNKNOWN_MODE";
            return false;
        }

        private List<PivotPoint> V71BuildOraclePivots(Bars bars, int endIndex, int lookback, int depth)
        {
            var points = new List<PivotPoint>();
            if (bars == null || depth < 1) return points;
            int right = Math.Min(endIndex - depth, bars.Count - 1 - depth);
            int left = Math.Max(depth, right - lookback);
            for (int i = left; i <= right; i++)
            {
                double hi = bars.HighPrices[i], lo = bars.LowPrices[i];
                bool peak = true, trough = true;
                for (int off = 1; off <= depth; off++)
                {
                    if (bars.HighPrices[i - off] >= hi || bars.HighPrices[i + off] >= hi) peak = false;
                    if (bars.LowPrices[i - off] <= lo || bars.LowPrices[i + off] <= lo) trough = false;
                    if (!peak && !trough) break;
                }
                if (peak) points.Add(new PivotPoint { Index = i, Price = hi, IsHigh = true });
                if (trough) points.Add(new PivotPoint { Index = i, Price = lo, IsHigh = false });
            }

            points = points.OrderBy(z => z.Index).ToList();
            var alternating = new List<PivotPoint>();
            foreach (var p in points)
            {
                if (alternating.Count == 0) { alternating.Add(p); continue; }
                var prior = alternating[alternating.Count - 1];
                if (prior.IsHigh != p.IsHigh) { alternating.Add(p); continue; }
                bool moreExtreme = p.IsHigh ? p.Price > prior.Price : p.Price < prior.Price;
                if (moreExtreme) alternating[alternating.Count - 1] = p;
            }
            return alternating;
        }

        private bool V71OracleLegInsideEnvelope(List<PivotPoint> pivots, int left, int right)
        {
            if (pivots == null || left < 0 || right >= pivots.Count || left >= right) return false;
            double lo = Math.Min(pivots[left].Price, pivots[right].Price);
            double hi = Math.Max(pivots[left].Price, pivots[right].Price);
            double eps = Math.Max(_symbol.PipSize, Math.Abs(hi - lo) * 1e-9);
            for (int k = left + 1; k < right; k++)
            {
                double px = pivots[k].Price;
                if (px < lo - eps || px > hi + eps) return false;
            }
            return true;
        }

        private bool V71OracleContractPass(PatternProfile p, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            double atr, out TradeDirection direction)
        {
            direction = TradeDirection.Buy;
            bool bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
            bool bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
            if (!bullish && !bearish) return false;
            direction = bullish ? TradeDirection.Buy : TradeDirection.Sell;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0 || atr <= 0) return false;
            if (Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) < atr * .45) return false;

            double xab = ab / xa;
            double abc = bc / ab;
            double bcd = cd / bc;
            double adxa = Math.Abs(d.Price - a.Price) / xa;
            double xdxa = Math.Abs(d.Price - x.Price) / xa;
            double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;
            double abcd = cd / ab;
            double xc = Math.Abs(c.Price - x.Price);

            if (p.Mode == PatternMode.STANDARD)
            {
                if (!InRange(xab, p.XabMin, p.XabMax) || !InRange(abc, p.AbcMin, p.AbcMax) ||
                    !InRange(bcd, p.BcdMin, p.BcdMax) || !InRange(xad, p.XadMin, p.XadMax)) return false;

                double przHalf = atr * p.PrzWidthAtr;
                if (EnableFamilyNativeConversion &&
                    (p.Name == "Crab" || p.Name == "Deep Crab" || p.Name == "Butterfly" || p.Name == "Alt Bat"))
                    przHalf *= 1.20;
                else if (EnableFamilyNativeConversion)
                    przHalf *= .90;

                double xaD1 = bullish ? a.Price - p.XadMin * xa : a.Price + p.XadMin * xa;
                double xaD2 = bullish ? a.Price - p.XadMax * xa : a.Price + p.XadMax * xa;
                double bcD1 = bullish ? c.Price - p.BcdMin * bc : c.Price + p.BcdMin * bc;
                double bcD2 = bullish ? c.Price - p.BcdMax * bc : c.Price + p.BcdMax * bc;
                double coreLo = Math.Max(Math.Min(xaD1, xaD2), Math.Min(bcD1, bcD2));
                double coreHi = Math.Min(Math.Max(xaD1, xaD2), Math.Max(bcD1, bcD2));
                return coreLo <= coreHi && d.Price >= coreLo - przHalf && d.Price <= coreHi + przHalf;
            }

            if (p.Mode == PatternMode.ABCD)
                return InRange(abc, p.AbcMin, p.AbcMax) && InRange(bcd, p.BcdMin, p.BcdMax) && InRange(abcd, p.AbcDMin, p.AbcDMax);
            if (p.Mode == PatternMode.CYPHER)
                return InRange(xab, .382, .618) && InRange(xc / xa, 1.13, 1.414) && InRange(cd / Math.Max(xc, 1e-9), .70, .90);
            if (p.Mode == PatternMode.SHARK)
                return InRange(abc, 1.13, 1.618) && InRange(bcd, 1.13, 2.24) && InRange(xad, .85, 1.25);
            if (p.Mode == PatternMode.FIVEZERO)
                return InRange(xab, 1.13, 1.618) && InRange(abc, 1.618, 2.24) && InRange(bcd, .45, .65);
            return false;
        }

        private string V71OracleKey(string family, TradeDirection direction, DateTime completion,
            PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d, int scale)
        {
            string px(double v) { return Math.Round(v, _symbol.Digits).ToString("F" + _symbol.Digits, CultureInfo.InvariantCulture); }
            return V71FamilyKey(family) + "|" + direction + "|" + completion.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture) + "|" +
                   px(x.Price) + "|" + px(a.Price) + "|" + px(b.Price) + "|" + px(c.Price) + "|" + px(d.Price) + "|" + scale;
        }

        private string V71OracleKey(PatternSignal s)
        {
            if (s == null) return "INVALID";
            return V71OracleKey(s.PatternName, s.Direction, s.CompletionTime, s.X, s.A, s.B, s.C, s.D, s.PivotScale);
        }

        private void V71AuditExpansionDetectorRecall(Bars bars, int endIndex, int lookback, IEnumerable<PatternSignal> production)
        {
            if (!EnableV71ExpansionShadow || bars == null || endIndex < 40) return;
            double atr = Atr(bars, 14, endIndex);
            if (atr <= 0) return;

            var productionKeys = new HashSet<string>(
                (production ?? Enumerable.Empty<PatternSignal>()).Where(x => x != null).Select(V71OracleKey),
                StringComparer.Ordinal);

            foreach (int scale in new[] { 2, 3, 5, 8 })
            {
                var pivots = V71BuildOraclePivots(bars, endIndex, lookback, scale);
                if (pivots.Count < 5) continue;
                int dPos = pivots.Count - 1;
                var d = pivots[dPos];
                if (endIndex - d.Index > 8) continue;

                int prior;
                if (_v71OracleLastDIndexByScale.TryGetValue(scale, out prior) && prior == d.Index) continue;
                _v71OracleLastDIndexByScale[scale] = d.Index;

                int c0 = Math.Max(3, dPos - 5);
                for (int cPos = c0; cPos < dPos; cPos++)
                {
                    if (!V71OracleLegInsideEnvelope(pivots, cPos, dPos)) continue;
                    int b0 = Math.Max(2, cPos - 5);
                    for (int bPos = b0; bPos < cPos; bPos++)
                    {
                        if (!V71OracleLegInsideEnvelope(pivots, bPos, cPos)) continue;
                        int a0 = Math.Max(1, bPos - 5);
                        for (int aPos = a0; aPos < bPos; aPos++)
                        {
                            if (!V71OracleLegInsideEnvelope(pivots, aPos, bPos)) continue;
                            int x0 = Math.Max(0, aPos - 5);
                            for (int xPos = x0; xPos < aPos; xPos++)
                            {
                                if (dPos - xPos > 16 || !V71OracleLegInsideEnvelope(pivots, xPos, aPos)) continue;
                                var x = pivots[xPos]; var a = pivots[aPos]; var b = pivots[bPos]; var cc = pivots[cPos];
                                foreach (var profile in _profiles)
                                {
                                    if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars)) continue;
                                    TradeDirection direction;
                                    if (!V71OracleContractPass(profile, x, a, b, cc, d, atr, out direction)) continue;
                                    string key = V71OracleKey(profile.Name, direction, bars.OpenTimes[d.Index], x, a, b, cc, d, scale);
                                    if (!_v71OracleSeen.Add(key)) continue;

                                    string fam = V71FamilyKey(profile.Name);
                                    IncrementCounter(_v71OracleExpected, fam);
                                    if (productionKeys.Contains(key))
                                    {
                                        IncrementCounter(_v71OracleMatched, fam);
                                    }
                                    else
                                    {
                                        IncrementCounter(_v71OracleMissed, fam);
                                        Print("[V71-ORACLE-MISS] family={0} scale={1} dIndex={2} completion={3:O} key={4}",
                                            fam, scale, d.Index, bars.OpenTimes[d.Index], key);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        private List<PatternSignal> V71DetectExpansionPatternCandidates(Bars bars, int endIndex, int depth, int lookback, int maxCandidates, string timeframe)
        {
            var result = new List<PatternSignal>();
            if (bars == null || endIndex < 40) return result;
            double atr = Atr(bars, 14, endIndex);
            if (atr <= 0) return result;

            int[] baseScales = EnableIndependentPivotGraph && string.Equals(timeframe, "M15", StringComparison.OrdinalIgnoreCase)
                ? new[] { 2, 3, 5 }
                : new[] { Math.Max(2, depth) };

            // Fast lane preserves the verified sparse behavior. The complete lattice below
            // is authoritative for recall and includes every declared family.
            foreach (int scale in baseScales.Distinct())
            {
                var pivots = BuildConfirmedPivots(bars, endIndex, lookback, scale);
                if (pivots.Count < 5) continue;
                int[] hops = { 1, 3 };
                for (int dPos = Math.Max(4, pivots.Count - 16); dPos < pivots.Count; dPos++)
                {
                    var d = pivots[dPos];
                    if (endIndex - d.Index > 8) continue;
                    foreach (int hCD in hops)
                    foreach (int hBC in hops)
                    foreach (int hAB in hops)
                    foreach (int hXA in hops)
                    {
                        int cPos = dPos - hCD, bPos = cPos - hBC, aPos = bPos - hAB, xPos = aPos - hXA;
                        if (xPos < 0) continue;
                        if (!V71SparseLegInsideEnvelope(pivots, xPos, aPos) ||
                            !V71SparseLegInsideEnvelope(pivots, aPos, bPos) ||
                            !V71SparseLegInsideEnvelope(pivots, bPos, cPos) ||
                            !V71SparseLegInsideEnvelope(pivots, cPos, dPos)) continue;
                        var x = pivots[xPos]; var a = pivots[aPos]; var b = pivots[bPos]; var cc = pivots[cPos];
                        foreach (var profile in _profiles)
                        {
                            PatternSignal sig;
                            if (!TryMatchProfile(profile, x, a, b, cc, d, atr, bars.OpenTimes[d.Index], timeframe, scale, out sig, false)) continue;
                            if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars)) continue;
                            result.Add(sig);
                        }
                    }
                }
            }

            // Full 12-family lattice. No global top-K is allowed before family identity
            // and no AB=CD hard-veto may make a primary family unreachable.
            if (EnableV71FullFamilyPivotLattice && string.Equals(timeframe, "M15", StringComparison.OrdinalIgnoreCase))
            {
                var fullFamilies = _profiles.ToList();
                foreach (int scale in new[] { 2, 3, 5, 8 })
                {
                    var pivots = BuildConfirmedPivots(bars, endIndex, lookback, scale);
                    if (pivots.Count < 5) continue;
                    for (int dPos = Math.Max(4, pivots.Count - 18); dPos < pivots.Count; dPos++)
                    {
                        var d = pivots[dPos];
                        if (endIndex - d.Index > 8) continue;
                        int c0 = Math.Max(3, dPos - 5);
                        for (int cPos = c0; cPos < dPos; cPos++)
                        {
                            if (!V71SparseLegInsideEnvelope(pivots, cPos, dPos)) continue;
                            int b0 = Math.Max(2, cPos - 5);
                            for (int bPos = b0; bPos < cPos; bPos++)
                            {
                                if (!V71SparseLegInsideEnvelope(pivots, bPos, cPos)) continue;
                                int a0 = Math.Max(1, bPos - 5);
                                for (int aPos = a0; aPos < bPos; aPos++)
                                {
                                    if (!V71SparseLegInsideEnvelope(pivots, aPos, bPos)) continue;
                                    int x0 = Math.Max(0, aPos - 5);
                                    for (int xPos = x0; xPos < aPos; xPos++)
                                    {
                                        if (dPos - xPos > 16 || !V71SparseLegInsideEnvelope(pivots, xPos, aPos)) continue;
                                        var x = pivots[xPos]; var a = pivots[aPos]; var b = pivots[bPos]; var cc = pivots[cPos];
                                        foreach (var profile in fullFamilies)
                                        {
                                            string rejectReason;
                                            if (!V71ExpansionPrimaryContractPass(profile, x, a, b, cc, d, atr, out rejectReason))
                                            {
                                                V71CountExpansionReject(profile.Name, rejectReason);
                                                continue;
                                            }
                                            PatternSignal sig;
                                            if (!TryMatchProfile(profile, x, a, b, cc, d, atr, bars.OpenTimes[d.Index], timeframe, scale, out sig, false))
                                            {
                                                V71CountExpansionReject(profile.Name, "POST_CONTRACT_MATCH_FAIL");
                                                continue;
                                            }
                                            if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars))
                                            {
                                                V71CountExpansionReject(profile.Name, "AGE_FAIL");
                                                continue;
                                            }
                                            result.Add(sig);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Preserve competing family interpretations before any census quota.
            var familyNative = result
                .GroupBy(x => V71FamilyKey(x.PatternName) + "|" + BuildSetupGeometryKey(x) + "|" + x.PivotScale)
                .Select(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).First())
                .OrderByDescending(x => x.Confidence)
                .ThenByDescending(x => x.GeometryQuality)
                .ToList();

            foreach (var signal in familyNative)
                signal.ResearchRole = V71AbcdResearchRole(signal, familyNative);

            // Oracle compares against the pre-quota production detector, never Capital selection.
            V71AuditExpansionDetectorRecall(bars, endIndex, lookback, familyNative);

            if (!EnableV71FamilyBalancedCensus)
                return familyNative.Take(Math.Max(1, maxCandidates)).ToList();

            int perFamilyPool = Math.Max(8, Math.Min(32, Math.Max(1, maxCandidates)));
            return familyNative
                .GroupBy(x => V71FamilyKey(x.PatternName))
                .SelectMany(g => g.Take(perFamilyPool))
                .OrderByDescending(x => x.Confidence)
                .ThenByDescending(x => x.GeometryQuality)
                .ToList();
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
            double atr, DateTime completion, string timeframe, int pivotScale, out PatternSignal signal, bool requireHardStandardAbcd = true)
        {
            signal = null;
            bool bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
            bool bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
            if (!bullish && !bearish) return false;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double ad = Math.Abs(d.Price - a.Price);
            double xd = Math.Abs(d.Price - x.Price);
            double xc = Math.Abs(c.Price - x.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0 || atr <= 0) return false;
            if (Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) < atr * 0.45) return false;

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

            if (ratioOk && requireHardStandardAbcd && EnableCanonicalFamilyContracts && p.Mode == PatternMode.STANDARD)
                ratioOk = StandardFamilyAbcdCompatible(p.Name, abcd);

            if (!ratioOk) return false;

            double legacyGeometry = p.Mode == PatternMode.STANDARD
                ? (RatioScore(xab, Mid(p.XabMin, p.XabMax)) + RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) +
                   RatioScore(bcd, Mid(p.BcdMin, p.BcdMax)) + RatioScore(xad, Mid(p.XadMin, p.XadMax))) / 4.0
                : VClamp((RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) + RatioScore(bcd, Mid(p.BcdMin, p.BcdMax))) / 2.0);
            double geometry = EnableFamilyNativeJointGeometry
                ? FamilyNativeJointGeometryScore(p, xab, abc, bcd, xad, abcd, xac, requireHardStandardAbcd)
                : legacyGeometry;

            int t1 = Math.Max(1, a.Index - x.Index);
            int t2 = Math.Max(1, b.Index - a.Index);
            int t3 = Math.Max(1, c.Index - b.Index);
            int t4 = Math.Max(1, d.Index - c.Index);
            double timeSym = (Symmetry(t1, t2) + Symmetry(t2, t3) + Symmetry(t3, t4)) / 3.0;
            double pivotQuality = VClamp(Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) / (atr * 2.0));

            double expectedD = d.Price;
            double przHalf = atr * p.PrzWidthAtr;
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

            if (!requireHardStandardAbcd && p.Mode == PatternMode.STANDARD)
            {
                // Pure projected PRZ for Expansion: derive both primary completion
                // bands from X/A/B/C before D. The completed D pivot may validate
                // the projection, but can never define its own expected zone.
                double xaD1 = bullish ? a.Price - p.XadMin * xa : a.Price + p.XadMin * xa;
                double xaD2 = bullish ? a.Price - p.XadMax * xa : a.Price + p.XadMax * xa;
                double bcD1 = bullish ? c.Price - p.BcdMin * bc : c.Price + p.BcdMin * bc;
                double bcD2 = bullish ? c.Price - p.BcdMax * bc : c.Price + p.BcdMax * bc;
                double xaLo = Math.Min(xaD1, xaD2), xaHi = Math.Max(xaD1, xaD2);
                double bcLo = Math.Min(bcD1, bcD2), bcHi = Math.Max(bcD1, bcD2);
                double coreLo = Math.Max(xaLo, bcLo), coreHi = Math.Min(xaHi, bcHi);
                if (coreLo > coreHi) return false;

                przLow = coreLo - przHalf;
                przHigh = coreHi + przHalf;
                if (d.Price < przLow || d.Price > przHigh) return false;

                double projectedWidth = Math.Max(0.0, coreHi - coreLo);
                double compression = 1.0 - Math.Min(1.0, projectedWidth / Math.Max(atr * 2.0, 1e-9));
                double center = (coreLo + coreHi) * .5;
                double location = 1.0 - Math.Min(1.0, Math.Abs(d.Price - center) /
                    Math.Max(przHalf + projectedWidth * .5, 1e-9));
                przConfluence = VClamp(.60 * compression + .40 * location);
            }
            else if (p.Mode != PatternMode.STANDARD)
            {
                przConfluence = VClamp((geometry + timeSym) / 2.0);
            }

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
            return true;
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

        private double FamilyNativeJointGeometryScore(PatternProfile p, double xab, double abc, double bcd, double xad, double abcd, double xac, bool includeAbcdIdentity = true)
        {
            var z = new List<double>();
            if (p.Mode == PatternMode.STANDARD)
            {
                z.Add(RangeCoordinate(xab, p.XabMin, p.XabMax));
                z.Add(RangeCoordinate(abc, p.AbcMin, p.AbcMax));
                z.Add(RangeCoordinate(bcd, p.BcdMin, p.BcdMax));
                z.Add(RangeCoordinate(xad, p.XadMin, p.XadMax));
                if (includeAbcdIdentity) z.Add(CanonicalAbcdCoordinate(p.Name, abcd));
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
            r.AtrM15Pips = PriceToPips(Math.Max(0, atrNow));
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
                    Print("[V51-RECALL-ADMIT] pattern={0} direction={1} route={2} conflict={3} geometry={4:F3} prz={5:F3} confidence={6:F3} efficiency={7:F3} atrRatio={8:F3} extensionAtr={9:F3}",
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
                    Print("[V51-TRANSITION-PROOF-REJECT] pattern={0} conflict={1} transition={2} adxSlope={3:F2}",
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
                    Print("[V51-ROUTE-VETO] type=TRANSITION_STATE conflict={0} transition={1} adxSlope={2:F2}",
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
                    Print("[V51-ROUTE-VETO] type=EXHAUSTION_EVIDENCE extensionAtr={0:F3} adxSlope={1:F2}",
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
            Print("[V51-EXECUTION-ERROR] code={0} detail={1}", code, detail ?? "");
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

        private string NewCandidateId(PatternSignal s)
        {
            _candidateSeq++;
            return "V47-" + _candidateSeq.ToString("D8", CultureInfo.InvariantCulture) + "-" +
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
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Rejected++;
            Event(c, "REJECTED:" + reason);
        }

        private void Expire(CandidateRecord c, string reason)
        {
            c.State = CandidateState.EXPIRED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Expired++;
            Event(c, "EXPIRED:" + reason);
        }

        private void Invalidate(CandidateRecord c, string reason)
        {
            c.State = CandidateState.INVALIDATED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Invalidated++;
            Event(c, "INVALIDATED:" + reason);
        }

        private void Ledger(CandidateRecord c, CandidateState state, string reason)
        {
            double wait = c.ParkedUtc.HasValue ? Math.Max(0, (Server.Time.ToUniversalTime() - c.ParkedUtc.Value).TotalMinutes) : 0;
            Print("[V51-EVENT] cid={0} setup={1} pattern={2} subtype={3} scale={4} tf={5} dir={6} state={7} route={8} conflict={9} waitMin={10:F2} reason={11}",
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
                    Print("[V51-WARMUP-ERROR] tf={0} count={1} error={2}", name, bars.Count, ex.Message);
                    break;
                }
                loops++;
                Print("[V51-WARMUP] tf={0} added={1} count={2}", name, added, bars.Count);
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
        public string ResearchRole;
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
        public double AtrM15Pips;
        public double AtrPercentile;
        public double Efficiency;
        public double ExtensionAtr;
        public double AdxH1;
        public double AdxH4;
        public double AdxH1Slope;
        public double TrendStrength;
    }

    public enum V71ExpansionState { WAIT_PRZ, CONFIRMING, ARMED, EXECUTED, EXPIRED, REJECTED, INVALIDATED }

    public sealed class V71ExpansionCandidate
    {
        public string CandidateId, IdentityKey, SetupKey;
        public PatternSignal Signal;
        public MtfConflict Conflict;
        public HarmonicRoute Route;
        public RegimeSnapshot Regime;
        public V71ExpansionState State;
        public bool IsActive, Executed, ShadowStarted, ShadowFinished;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc, ArmedUtc, ReactionProofUtc;
        public DateTime PullbackExpiryUtc;
        public double ConfirmationScore, NetRR, RegimeScore;
        public double ReactionProofPrice, ReactionExtremePrice, ReactionScore;
        public double EntryAnchor, StructuralStop, CanonicalTarget, RiskDistance, TargetR;
        public double EdgeMean, EdgeLcb, SlotScore, ShadowOutcomeR;
        public double AtrPercentile, AdxH1Norm, AdxH4Norm, AdxSlopeNorm, TrendStrength;
        public double SpreadAtr, SessionPhase, PrzCompression, TransitionState;
        public double SupportDistance, ExpectedSlotHours, ExpectedSlotHoursUcb, SurvivalProbability = .50;
        public double ModeledCostR, PathProbability, PathLcb, RunnerProbability, RunnerLcb, CoreArrivalHazard;
        public bool SupportEligible = true;
        public bool CoreOverlapObserved, CapitalEligible = true, NativeExitCaptured, PathUsable;
        public bool ReactionProved, ReactionExtremeInitialized, AwaitingPullbackFill, PullbackFilled, V72ProtectionActive;
        public string AbcdRole = "PARENT_FAMILY", NativeExitResult;
        public double NativeExitR, ShadowPeakR, ShadowProtectionR = -1.0;
        public double ShadowMfeR, ShadowMaeR, ShadowMaxGivebackR;
        public int ShadowBars, NativeConfirmBars, PathState;
        public int TimeTo05R = -1, TimeTo1R = -1, TimeTo2R = -1, TimeToStopR = -1, TimeToMfeBars = -1;
        public CandidateRecord NativeEvidenceState;
    }

    public sealed class CandidateRecord
    {
        public string CandidateId;
        public string SetupKey;
        public PatternSignal Signal;
        public CandidateState State;
        public bool IsActive = true;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc;
        public MtfConflict Conflict = MtfConflict.NEUTRAL;
        public HarmonicRoute Route = HarmonicRoute.NO_TRADE;
        public RegimeSnapshot Regime;
        public double ConfirmationScore, NetRR, SelectedTarget, Rank;
        public double AlphaQualityScore, RegimeScore, CapitalMinL0Risk, CapitalMinL0Margin;
        public int RescueBarsObserved;
        public double RescueBestScore;
        public DateTime? ArmedUtc, ParkedUtc, ParkedHardExpiryUtc;
        public bool ArmedGraceApplied, WasParked, OpportunityTerminalLogged;
        public int NativeM1BarsObserved, NativeStage;
        public int FamilyConfirmationBarsObserved;
        public bool FamilyDirectional, FamilyReclaim, FamilyBos, FamilyRejection, FamilySweep,
                    FamilyFailedExtension, FamilyInsidePrz, FamilyDisplacement, FamilyRetest;
        public double OriginalRank, OriginalGeometry, OriginalPrzConfluence, OriginalM1Evidence, OriginalEntryAnchor, ShadowRiskDistance, ShadowMfeR, ShadowMaeR;
        public double CompletionAnchorPrice, NativeConfirmAnchorPrice, NativeRetestAnchorPrice;
        public double CompletionAnchorMfeR, CompletionAnchorMaeR, NativeConfirmMfeR, NativeConfirmMaeR, NativeRetestMfeR, NativeRetestMaeR;
        public bool TemporalDirectional, TemporalReclaim, TemporalBos1, TemporalBos2, TemporalRejection, TemporalFailedExtension, TemporalDisplacement;
        public bool CapitalFeasible;
        public bool V71Expansion;
        public bool V72ReactionAlpha;
        public double V71RiskPercent = 1.0;
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
        public string BasketId, CandidateId, Pattern, ExitOverride, ExitReason;
        public TradeDirection Direction;
        public HarmonicRoute Route;
        public FibonacciBasketState State;
        public DateTime CreatedUtc, ExpirationUtc;
        public double EntryAnchor, AverageEntry, StructuralStop, CanonicalTarget;
        public double InitialBasketRisk, PlannedWorstCaseRisk, PeakR, MaxAdverseR, RealizedNet, ProtectionFrontier;
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
