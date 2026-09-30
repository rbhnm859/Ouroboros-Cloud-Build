using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public partial class HarmonyBotV71 : Robot
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

        [Parameter("Enable V72 Bifurcation Alpha", DefaultValue = false)]
        public bool EnableV72BifurcationAlpha { get; set; }

        [Parameter("Enable V72 Family-Native Causal Alpha", DefaultValue = false)]
        public bool EnableV72FamilyNativeCausalAlpha { get; set; }

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
        private int _v71ExpansionDetected;
        private int _v71ExpansionArmed;
        private int _v71ExpansionExecuted;
        private int _v71ExpansionCoreBlocked;
        private int _v71ExpansionEligibilityRejected;
        private int _v71ExpansionGridFallback;
        private int _v71ExpansionShadowClosed;
        private readonly HashSet<string> _v72PayoffSeen = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<string, V72PayoffAccumulator> _v72PayoffCensus = new Dictionary<string, V72PayoffAccumulator>();
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

        // Protected V51 runtime/capital lifecycle is isolated in
        // Architecture/HarmonyBotV71.ProtectedCore.cs. Physical separation only:
        // protected-core priority, candidate ownership, grid, risk and execution semantics
        // remain byte-for-byte behaviorally governed by exact replay.

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
        // Post-detector context/family resolution, safety and telemetry/math have been
        // moved to Architecture partials. The marker above remains in this file because
        // it is the immutable end-boundary of the frozen harmonic-engine hash region.
        // No runtime semantics are changed by this physical extraction.
    }

}
