using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBotV34 : Robot
    {
        private const string Version = "HarmonyBot V34.0 — Clean Execution & Adaptive Capital Architecture";
        private const string BotPrefix = "HB34";

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
        private readonly HashSet<long> _postFillValidated = new HashSet<long>();

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
                Print("[V34-FATAL] SYMBOL_NOT_FOUND {0}", SymbolName);
                Stop();
                return;
            }

            _h4Bars = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _m1Bars = MarketData.GetBars(TimeFrame.Minute, SymbolName);

            if (!BarsObjectsReady())
            {
                Print("[V34-FATAL] TIMEFRAME_OBJECT_LOAD_FAILED");
                Stop();
                return;
            }

            WarmupBars(_h4Bars, 230, "H4");
            WarmupBars(_h1Bars, 230, "H1");
            WarmupBars(_m15Bars, 360, "M15");
            WarmupBars(_m1Bars, 120, "M1");

            if (!BarsReady())
                Print("[V34-WARMUP-PENDING] H4={0} H1={1} M15={2} M1={3}",
                    Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars));

            _londonTz = ResolveTimeZone("Europe/London", "GMT Standard Time");
            _newYorkTz = ResolveTimeZone("America/New_York", "Eastern Standard Time");
            if (_londonTz == null || _newYorkTz == null)
            {
                Print("[V34-FATAL] DST_TIMEZONE_UNAVAILABLE");
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

            Print("[V34-START] version={0} symbol={1} H4={2} H1={3} M15={4} M1={5} profiles={6}",
                Version, SymbolName, Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars), _profiles.Count);
            Print("[V34-TIMEFRAME-AUDIT] primaryPattern=M15 execution=M1 macro=H4 intermediate=H1 allCompletedBars=true");
            Print("[V34-SESSION-AUDIT] london={0} newYork={1} dstAware=true", _londonTz.Id, _newYorkTz.Id);
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
                Print("[V34-PIPELINE] pattern={0} detected={1} validated={2} routed={3} prz={4} confirming={5} armed={6} basketPlanned={7} leg0={8} leg1={9} leg2={10} leg3={11} basketClosed={12} executed={13} expired={14} rejected={15} invalidated={16}",
                    kv.Key, x.Detected, x.Validated, x.Routed, x.PrzWaiting, x.Confirming, x.Armed, x.BasketPlanned,
                    x.Leg0Executed, x.Leg1Filled, x.Leg2Filled, x.Leg3Filled, x.BasketClosed, x.Executed, x.Expired, x.Rejected, x.Invalidated);
            }
            Print("[V34-SUMMARY] candidates={0} baskets={1} openLedgers={2} executionErrors={3} gridRiskViolations={4} duplicateGridLegs={5} orphanPendingOrders={6} stopWideningViolations={7} gapThroughInvalidations={8} gapThroughSurvivors={9} unprotectedSurvivors={10} postFillProtectionFailures={11} actualBasketRiskViolations={12} executionStateViolations={13} virtualGridFills={14} microModeBaskets={15} capitalRejectedBaskets={16} marginRiskViolations={17}",
                _candidateSeq, _baskets.Count, _positions.Count, _executionErrors, _gridRiskViolations, _duplicateGridLegs, _orphanPendingOrders, _stopWideningViolations,
                _gapThroughInvalidations, _gapThroughSurvivors, _unprotectedSurvivors, _postFillProtectionFailures, _actualBasketRiskViolations, _executionStateViolations,
                _virtualGridFills, _microModeBaskets, _capitalRejectedBaskets, _marginRiskViolations);
            foreach (var kv in _executionErrorReasons.OrderBy(k => k.Key))
                Print("[V34-EXECUTION-ERROR-SUMMARY] code={0} count={1}", kv.Key, kv.Value);
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
                string id = NewCandidateId(signal);
                if (_candidates.ContainsKey(id)) continue;

                var record = new CandidateRecord
                {
                    CandidateId = id,
                    Signal = signal,
                    State = CandidateState.DETECTED,
                    DetectedUtc = Server.Time.ToUniversalTime(),
                    ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(2, Math.Min(CandidateTtlM15Bars, signal.Profile.MaxAgeM15Bars))),
                    LastReason = "PATTERN_DETECTED"
                };
                _candidates[id] = record;
                CountPipeline(signal.PatternName).Detected++;
                Ledger(record, CandidateState.DETECTED, "PATTERN_DETECTED");

                if (signal.GeometryQuality < Math.Max(MinGeometryQuality, signal.Profile.MinGeometry) ||
                    signal.PrzConfluence < Math.Max(MinPrzConfluence, signal.Profile.MinPrz))
                {
                    Reject(record, "PATTERN_QUALITY");
                    continue;
                }

                Transition(record, CandidateState.VALIDATED, "PATTERN_VALIDATED");
                CountPipeline(signal.PatternName).Validated++;

                record.Conflict = ClassifyMtfConflict(signal.Direction, h4State, h1State);
                record.Route = RouteSignal(signal, record.Conflict, regime);
                record.Regime = regime;

                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    Reject(record, "ROUTER_NO_TRADE");
                    continue;
                }

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
                if (utc >= c.ExpiryUtc)
                {
                    Expire(c, "TTL_EXPIRED");
                    continue;
                }

                if (PatternInvalidatedBeforeEntry(c.Signal))
                {
                    Invalidate(c, "STRUCTURAL_INVALIDATION");
                    continue;
                }

                if (c.State == CandidateState.WAIT_PRZ)
                {
                    if (BarTouchesPrz(i, c.Signal))
                    {
                        c.PrzTouchUtc = utc;
                        Transition(c, CandidateState.CONFIRMING, "PRZ_RETEST");
                        CountPipeline(c.Signal.PatternName).Confirming++;
                    }
                    continue;
                }

                if (c.State == CandidateState.CONFIRMING)
                {
                    if (!c.PrzTouchUtc.HasValue || utc <= c.PrzTouchUtc.Value) continue;

                    double score = M1ConfirmationScore(i, c.Signal);
                    c.ConfirmationScore = score;
                    double required = c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 0.75 : 0.60;
                    if (score < required)
                    {
                        Event(c, "CONFIRMATION_FAILED_" + score.ToString("F2", CultureInfo.InvariantCulture));
                        continue;
                    }

                    if (!TryBuildFibonacciGridPlan(c))
                    {
                        Reject(c, "FIB_GRID_PLAN_REJECTED");
                        continue;
                    }

                    c.Rank = CandidateRank(c);
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
            if (_evaluationStartUtc.HasValue && Server.Time.ToUniversalTime() < _evaluationStartUtc.Value) return;
            if (!IsInstitutionalSession(Server.Time.ToUniversalTime())) return;
            if (!SpreadValid()) return;
            if (OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)) return;

            var armed = _candidates.Values
                .Where(c => c.State == CandidateState.ARMED && c.IsActive && c.GridPlan != null)
                .OrderByDescending(c => c.Rank)
                .ToList();
            if (armed.Count == 0) return;

            var winner = armed[0];
            ExecuteFibonacciGridPlan(winner);

            if (winner.State == CandidateState.EXECUTED)
                foreach (var other in armed.Skip(1))
                    Reject(other, "SINGLE_BASKET_SCHEDULER");
        }

        private bool TryBuildFibonacciGridPlan(CandidateRecord c)
        {
            var p = c.Signal.Profile;
            if (p == null || !p.GridEnabled) return false;
            if (!_initialCapitalEligible) return false;

            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double distance = c.Signal.Direction == TradeDirection.Buy ? anchor - stop : stop - anchor;
            if (distance <= PipsToPrice(MinStopLossPips)) return false;

            double xa = Math.Abs(c.Signal.A.Price - c.Signal.X.Price);
            double spanXa = xa > 0 ? distance / xa : 999;
            if (spanXa < p.MinimumGridSpanXa || spanXa > p.MaximumGridSpanXa) return false;

            int routeMax = c.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL ? 4 :
                           c.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? 2 :
                           c.Route == HarmonicRoute.TRANSITION_REVERSAL ? (c.Regime != null && c.Regime.Efficiency >= .28 ? 3 : 2) : 0;
            int maxLegs = Math.Min(Math.Min(routeMax, p.MaximumGridLegs), p.GridFractions.Length);
            if (maxLegs <= 0) return false;

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = distance,
                BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = MinDate(c.ExpiryUtc, Server.Time.ToUniversalTime().AddMinutes(p.PendingTtlMinutes)),
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold
            };
            if (plan.BasketRiskAmount <= 0) return false;

            double przTol = Math.Max(c.Signal.PrzHigh - c.Signal.PrzLow, distance * p.GridStructuralTolerance);
            double legalLow = c.Signal.PrzLow - przTol;
            double legalHigh = c.Signal.PrzHigh + przTol;

            for (int leg = 0; leg < maxLegs; leg++)
            {
                double fraction = p.GridFractions[leg];
                if (fraction < -1e-9 || fraction > .6180001) continue;
                double price = c.Signal.Direction == TradeDirection.Buy ? anchor - fraction * distance : anchor + fraction * distance;
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

            if (plan.Legs.Count == 0 || plan.Legs[0].Index != 0) return false;
            plan.LogicalLegCount = plan.Legs.Count;

            if (!ConfigureCapitalExecution(plan))
            {
                _capitalRejectedBaskets++;
                return false;
            }

            var physical = plan.Legs.Where(x => x.Physical && x.Volume > 0).ToList();
            if (physical.Count == 0 || physical[0].Index != 0) return false;

            double totalVolume = physical.Sum(l => l.Volume);
            plan.ExpectedWeightedEntry = physical.Sum(l => l.PlannedPrice * l.Volume) / totalVolume;

            double virtualDen = plan.Legs.Sum(l => l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9));
            plan.VirtualWeightedEntry = virtualDen > 0
                ? plan.Legs.Sum(l => l.PlannedPrice * (l.RiskWeight / Math.Max(PriceToPips(Math.Abs(l.PlannedPrice - stop)), 1e-9))) / virtualDen
                : plan.ExpectedWeightedEntry;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(c.Signal, plan.ExpectedWeightedEntry, plan.StructuralStop, out target, out netRr))
                return false;

            plan.CanonicalTarget = target;
            plan.ExpectedNetRR = netRr;
            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = netRr;

            Print("[V34-GRID-PLAN] cid={0} pattern={1} route={2} logicalLegs={3} physicalDepth={4} micro={5} anchor={6} weighted={7} virtualWeighted={8} stop={9} target={10} budget={11:F2} worst={12:F2} margin={13:F2} netRR={14:F3}",
                c.CandidateId, c.Signal.PatternName, c.Route, plan.LogicalLegCount, plan.PhysicalDepth, plan.MicroCapitalMode,
                anchor, plan.ExpectedWeightedEntry, plan.VirtualWeightedEntry, stop, target, plan.BasketRiskAmount,
                plan.WorstCaseRisk, plan.EstimatedPhysicalMargin, plan.ExpectedNetRR);
            foreach (var leg in plan.Legs)
                Print("[V34-GRID-LEG-PLAN] cid={0} leg=L{1} fraction={2:F3} price={3} weight={4:F6} physical={5} volume={6} budget={7:F2} risk={8:F2} minBrokerRisk={9:F2} state={10}",
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
            Print("[V34-CAPITAL-COMPAT] cid={0} logicalLegs={1} riskOnlyPhysicalDepths={2}", plan.CandidateId, plan.LogicalLegCount, matrix);
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
                leg.State = GridLegState.REJECTED;
                BasketEvent(basket, "GRID_LEG_DUPLICATE_L" + leg.Index);
                return false;
            }

            if ((basket.Direction == TradeDirection.Buy && leg.PlannedPrice >= _symbol.Ask) ||
                (basket.Direction == TradeDirection.Sell && leg.PlannedPrice <= _symbol.Bid))
            {
                leg.State = GridLegState.CANCELLED;
                BasketEvent(basket, "GRID_LEG_PRICE_CROSSED_BEFORE_SUBMIT_L" + leg.Index);
                return false;
            }

            double slPips = PriceToPips(Math.Abs(leg.PlannedPrice - basket.StructuralStop));
            double tpPips = PriceToPips(Math.Abs(basket.CanonicalTarget - leg.PlannedPrice));
            if (slPips < MinStopLossPips || tpPips <= 0)
            {
                leg.State = GridLegState.REJECTED;
                BasketEvent(basket, "GRID_LEG_GEOMETRY_REJECT_L" + leg.Index);
                return false;
            }

            if (!BrokerProtectionDistancesValid(basket.Direction, leg.PlannedPrice, basket.StructuralStop, basket.CanonicalTarget))
            {
                leg.State = GridLegState.REJECTED;
                BasketEvent(basket, "GRID_LEG_BROKER_MIN_DISTANCE_L" + leg.Index);
                return false;
            }

            double liveFilledRisk = CurrentFilledStructuralRisk(basket);
            double livePendingRisk = CurrentPendingStructuralRisk(basket);
            double nextWorst = liveFilledRisk + livePendingRisk + leg.PlannedRisk + leg.ModeledCost;
            if (nextWorst > basket.InitialBasketRisk + 1e-8)
            {
                leg.State = GridLegState.RISK_REJECTED;
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
                leg.State = GridLegState.REJECTED;
                BasketEvent(basket, "GRID_LEG_SUBMIT_FAILED_L" + leg.Index + "_" + code);
                return false;
            }

            leg.PendingOrderId = tr.PendingOrder.Id;
            TransitionLegState(basket, leg, GridLegState.SUBMITTED, "GRID_LEG_SUBMITTED");
            return true;
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
            Print("[V34-PENDING-CANCEL-ALL] reason={0}", reason);
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
            Print("[V34-POST-FILL-AUDIT] basket={0} leg=L{1} pos={2} source={3} entry={4} stop={5} target={6} actualWorst={7:F4} budget={8:F4} protected=true",
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
            leg.FillCounted = true;
            leg.State = GridLegState.PROTECTED;
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
                (prior == GridLegState.PLANNED && (next == GridLegState.SUBMITTING || next == GridLegState.CANCELLED || next == GridLegState.VIRTUAL_ONLY)) ||
                (prior == GridLegState.SUBMITTING && (next == GridLegState.SUBMITTED || next == GridLegState.FILLED_UNVERIFIED || next == GridLegState.REJECTED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.SUBMITTED && (next == GridLegState.FILLED_UNVERIFIED || next == GridLegState.CANCELLED || next == GridLegState.EXPIRED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.FILLED_UNVERIFIED && (next == GridLegState.PROTECTED || next == GridLegState.FAIL_CLOSED)) ||
                (prior == GridLegState.PROTECTED && next == GridLegState.FAIL_CLOSED) ||
                (prior == GridLegState.VIRTUAL_ONLY && (next == GridLegState.VIRTUAL_FILLED || next == GridLegState.CANCELLED)) ||
                prior == GridLegState.RISK_REJECTED || prior == GridLegState.REJECTED || prior == GridLegState.CANCELLED || prior == GridLegState.EXPIRED || prior == GridLegState.FAIL_CLOSED || prior == GridLegState.VIRTUAL_FILLED;
            if (!allowed)
            {
                _executionStateViolations++;
                Print("[V34-STATE-VIOLATION] basket={0} leg=L{1} prior={2} next={3} reason={4}", basket == null ? "" : basket.BasketId, leg.Index, prior, next, reason);
            }
            leg.State = next;
            if (basket != null) BasketEvent(basket, "LEG_STATE_L" + leg.Index + "_" + prior + "_TO_" + next + "_" + reason);
        }

        private void PrintBrokerCapabilityProfile()
        {
            double min = _symbol.VolumeInUnitsMin;
            double marginBuy = EstimatedMargin(TradeDirection.Buy, min);
            double marginSell = EstimatedMargin(TradeDirection.Sell, min);
            Print("[V34-BROKER-PROFILE] symbol={0} equity={1:F2} freeMargin={2:F2} minVolume={3} step={4} maxVolume={5} pipValue={6} tickValue={7} minSL={8} minTP={9} minDistanceType={10} minMarginBuy={11:F2} minMarginSell={12:F2} minimumSupportedEquity={13:F2} adaptiveCapital={14} microThreshold={15:F2} initialCapitalEligible={16}",
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
                Print("[V34-LEG-CLOSED] pos={0} basket=UNKNOWN net={1:F2} reason={2}", p.Id, p.NetProfit, args.Reason);
                return;
            }

            FibonacciBasket basket = null;
            if (_baskets.TryGetValue(l.BasketId, out basket))
            {
                basket.RealizedNet += p.NetProfit;
                basket.ClosedLegs++;
                double legRealizedR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
                Print("[V34-LEG-CLOSED] basket={0} cid={1} leg=L{2} pos={3} pattern={4} route={5} dir={6} mfeR={7:F3} maeR={8:F3} realizedR={9:F3} net={10:F2} reason={11}",
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
            Print("[V34-BASKET-CLOSED] basket={0} cid={1} pattern={2} route={3} dir={4} plannedLegs={5} filledLegs={6} anchor={7} avgEntry={8} entryImprovePips={9:F3} stop={10} target={11} initialRisk={12:F2} worstRisk={13:F2} mfeR={14:F3} maeR={15:F3} realizedR={16:F3} net={17:F2} reason={18}",
                basket.BasketId, basket.CandidateId, basket.Pattern, basket.Route, basket.Direction, basket.Plan.Legs.Count, basket.FilledLegs,
                basket.EntryAnchor, basket.AverageEntry, entryImprovementPips, basket.StructuralStop, basket.CanonicalTarget,
                basket.InitialBasketRisk, basket.PlannedWorstCaseRisk, basket.PeakR, basket.MaxAdverseR, realizedR, basket.RealizedNet, reason);
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
            return "HB34-" + SymbolName + "-" + Server.Time.ToUniversalTime().ToString("yyyyMMdd", CultureInfo.InvariantCulture) + "-" +
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
            Print("[V34-BASKET-EVENT] basket={0} cid={1} pattern={2} route={3} state={4} reason={5}",
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

            var pivots = BuildConfirmedPivots(bars, endIndex, lookback, depth);
            if (pivots.Count < 5) return result;

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
                    if (!TryMatchProfile(profile, x, a, b, c, d, atr, bars.OpenTimes[d.Index], timeframe, out sig))
                        continue;
                    if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars)) continue;
                    result.Add(sig);
                }
            }

            return result
                .OrderByDescending(s => s.Confidence)
                .ThenByDescending(s => s.GeometryQuality)
                .GroupBy(s => s.PatternName + "|" + s.Direction + "|" + s.CompletionTime.ToString("O"))
                .Select(g => g.First())
                .Take(Math.Max(1, maxCandidates))
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
            double atr, DateTime completion, string timeframe, out PatternSignal signal)
        {
            signal = null;
            bool bullish = a.Price > x.Price && b.Price < a.Price && c.Price > b.Price && d.Price < c.Price;
            bool bearish = a.Price < x.Price && b.Price > a.Price && c.Price < b.Price && d.Price > c.Price;
            if (!bullish && !bearish) return false;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double xd = Math.Abs(d.Price - x.Price);
            double xc = Math.Abs(c.Price - x.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0 || atr <= 0) return false;
            if (Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) < atr * 0.45) return false;

            double xab = ab / xa;
            double abc = bc / ab;
            double bcd = cd / bc;
            double xad = xd / xa;
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

            if (!ratioOk) return false;

            double geometry = p.Mode == PatternMode.STANDARD
                ? (RatioScore(xab, Mid(p.XabMin, p.XabMax)) + RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) +
                   RatioScore(bcd, Mid(p.BcdMin, p.BcdMax)) + RatioScore(xad, Mid(p.XadMin, p.XadMax))) / 4.0
                : VClamp((RatioScore(abc, Mid(p.AbcMin, p.AbcMax)) + RatioScore(bcd, Mid(p.BcdMin, p.BcdMax))) / 2.0);

            int t1 = Math.Max(1, a.Index - x.Index);
            int t2 = Math.Max(1, b.Index - a.Index);
            int t3 = Math.Max(1, c.Index - b.Index);
            int t4 = Math.Max(1, d.Index - c.Index);
            double timeSym = (Symmetry(t1, t2) + Symmetry(t2, t3) + Symmetry(t3, t4)) / 3.0;
            double pivotQuality = VClamp(Math.Min(Math.Min(xa, ab), Math.Min(bc, cd)) / (atr * 2.0));

            double expectedD = bullish ? d.Price : d.Price;
            double przHalf = atr * p.PrzWidthAtr;
            double przLow = expectedD - przHalf;
            double przHigh = expectedD + przHalf;
            double przConfluence = VClamp(1.0 - Math.Abs(xad - Mid(p.XadMin, p.XadMax)) / Math.Max(.15, p.XadMax - p.XadMin + .05));
            if (p.Mode != PatternMode.STANDARD) przConfluence = VClamp((geometry + timeSym) / 2.0);

            double invalid = PatternStructuralInvalidation(p, x, a, b, c, d, bullish);
            double target1 = bullish ? d.Price + cd * p.Target1Cd : d.Price - cd * p.Target1Cd;
            double target2 = bullish ? d.Price + cd * p.Target2Cd : d.Price - cd * p.Target2Cd;
            double confidence = VClamp(0.45 * geometry + 0.25 * przConfluence + 0.15 * timeSym + 0.15 * pivotQuality);

            signal = new PatternSignal
            {
                PatternName = p.Name,
                Profile = p,
                Direction = bullish ? TradeDirection.Buy : TradeDirection.Sell,
                X = x, A = a, B = b, C = c, D = d,
                Xab = xab, Abc = abc, Bcd = bcd, Xad = xad,
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
            AddStd("Gartley", .55, .70, .382, .886, 1.13, 1.618, .72, .82, .12, .18, .618, 1.00, 8, .55, .55);
            AddStd("Bat", .382, .52, .382, .886, 1.13, 2.618, .84, .92, .13, .18, .618, 1.00, 8, .55, .55);
            AddStd("Alt Bat", .35, .43, .382, .886, 2.0, 3.618, 1.05, 1.18, .13, .20, .618, 1.00, 7, .58, .58);
            AddStd("Butterfly", .75, .82, .382, .886, 1.618, 2.618, 1.22, 1.35, .14, .20, .618, 1.00, 7, .58, .58);
            AddStd("Crab", .382, .65, .382, .886, 2.24, 3.618, 1.55, 1.72, .15, .22, .618, 1.00, 6, .60, .60);
            AddStd("Deep Crab", .82, .90, .382, .886, 2.0, 3.618, 1.55, 1.72, .15, .22, .618, 1.00, 6, .60, .60);
            AddStd("Deep Gartley", .70, .82, .382, .886, 1.13, 2.0, .82, .95, .13, .20, .618, 1.00, 7, .58, .58);
            AddStd("Rat", .50, .82, .382, .886, 1.272, 2.618, .88, 1.13, .14, .20, .618, 1.00, 7, .58, .58);

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

                double extreme = bullish ? x.Price - p.XadMax * xa : x.Price + p.XadMax * xa;
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
            double refEma = h1e50;
            double h1Atr = Atr(_h1Bars, 14, h1);
            r.ExtensionAtr = h1Atr > 0 ? Math.Abs(_h1Bars.ClosePrices[h1] - refEma) / h1Atr : 0;
            return r;
        }

        private HarmonicRoute RouteSignal(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
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
            return .25 * c.Signal.GeometryQuality + .15 * c.Signal.PrzConfluence + .15 * mtf + .15 * regime + .15 * c.ConfirmationScore + .15 * VClamp(c.NetRR / 3.0);
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
            Print("[V34-EXECUTION-ERROR] code={0} detail={1}", code, detail ?? "");
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

        private string NewCandidateId(PatternSignal s)
        {
            _candidateSeq++;
            return "V34-" + _candidateSeq.ToString("D8", CultureInfo.InvariantCulture) + "-" +
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
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Rejected++;
            Event(c, "REJECTED:" + reason);
        }

        private void Expire(CandidateRecord c, string reason)
        {
            c.State = CandidateState.EXPIRED;
            c.IsActive = false;
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Expired++;
            Event(c, "EXPIRED:" + reason);
        }

        private void Invalidate(CandidateRecord c, string reason)
        {
            c.State = CandidateState.INVALIDATED;
            c.IsActive = false;
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Invalidated++;
            Event(c, "INVALIDATED:" + reason);
        }

        private void Ledger(CandidateRecord c, CandidateState state, string reason)
        {
            Print("[V34-EVENT] cid={0} pattern={1} tf={2} dir={3} state={4} route={5} conflict={6} reason={7}",
                c.CandidateId, c.Signal.PatternName, c.Signal.Timeframe, c.Signal.Direction, state, c.Route, c.Conflict, reason);
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
                    Print("[V34-WARMUP-ERROR] tf={0} count={1} error={2}", name, bars.Count, ex.Message);
                    break;
                }
                loops++;
                Print("[V34-WARMUP] tf={0} added={1} count={2}", name, added, bars.Count);
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
    public enum CandidateState { DETECTED, VALIDATED, ROUTED, WAIT_PRZ, CONFIRMING, ARMED, EXECUTED, EXPIRED, REJECTED, INVALIDATED }
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
        public double Xab, Abc, Bcd, Xad;
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
    }

    public sealed class CandidateRecord
    {
        public string CandidateId;
        public PatternSignal Signal;
        public CandidateState State;
        public bool IsActive = true;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc;
        public MtfConflict Conflict = MtfConflict.NEUTRAL;
        public HarmonicRoute Route = HarmonicRoute.NO_TRADE;
        public RegimeSnapshot Regime;
        public double ConfirmationScore, NetRR, SelectedTarget, Rank;
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
        public long Detected, Validated, Routed, PrzWaiting, Confirming, Armed, BasketPlanned;
        public long Leg0Executed, Leg1Filled, Leg2Filled, Leg3Filled, BasketClosed;
        public long Executed, Expired, Rejected, Invalidated;
    }
}
