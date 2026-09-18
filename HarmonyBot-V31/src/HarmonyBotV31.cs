using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBotV31 : Robot
    {
        private const string Version = "HarmonyBot V31.0 — Clean-Room Multi-Timeframe Harmonic Execution Kernel";
        private const string BotPrefix = "HB31";

        [Parameter("Symbol", DefaultValue = "XAUUSD")]
        public string SymbolName { get; set; }

        [Parameter("Trading Enabled", DefaultValue = true)]
        public bool TradingEnabled { get; set; }

        [Parameter("Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 2.0)]
        public double RiskPercent { get; set; }

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

        private DateTime _lastM15Closed = DateTime.MinValue;
        private DateTime _lastM1Closed = DateTime.MinValue;
        private DateTime _currentDay;
        private double _dayStartEquity;
        private double _equityPeak;
        private bool _dailyLocked;
        private long _candidateSeq;
        private int _executionErrors;
        private DateTime? _evaluationStartUtc;

        protected override void OnStart()
        {
            _symbol = Symbols.GetSymbol(SymbolName);
            if (_symbol == null)
            {
                Print("[V31-FATAL] SYMBOL_NOT_FOUND {0}", SymbolName);
                Stop();
                return;
            }

            _h4Bars = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _m1Bars = MarketData.GetBars(TimeFrame.Minute, SymbolName);

            if (!BarsReady())
            {
                Print("[V31-FATAL] TIMEFRAME_LOAD_FAILED H4={0} H1={1} M15={2} M1={3}",
                    Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars));
                Stop();
                return;
            }

            _londonTz = ResolveTimeZone("Europe/London", "GMT Standard Time");
            _newYorkTz = ResolveTimeZone("America/New_York", "Eastern Standard Time");
            if (_londonTz == null || _newYorkTz == null)
            {
                Print("[V31-FATAL] DST_TIMEZONE_UNAVAILABLE");
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
            _equityPeak = Account.Equity;
            ResetDaily(true);

            Positions.Closed += OnPositionClosed;

            Print("[V31-START] version={0} symbol={1} H4={2} H1={3} M15={4} M1={5} profiles={6}",
                Version, SymbolName, Count(_h4Bars), Count(_h1Bars), Count(_m15Bars), Count(_m1Bars), _profiles.Count);
            Print("[V31-TIMEFRAME-AUDIT] primaryPattern=M15 execution=M1 macro=H4 intermediate=H1 allCompletedBars=true");
            Print("[V31-SESSION-AUDIT] london={0} newYork={1} dstAware=true", _londonTz.Id, _newYorkTz.Id);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            EnsureServerProtection();
            foreach (var kv in _pipeline.OrderBy(k => k.Key))
            {
                var x = kv.Value;
                Print("[V31-PIPELINE] pattern={0} detected={1} validated={2} routed={3} prz={4} confirming={5} armed={6} executed={7} expired={8} rejected={9} invalidated={10}",
                    kv.Key, x.Detected, x.Validated, x.Routed, x.PrzWaiting, x.Confirming, x.Armed, x.Executed, x.Expired, x.Rejected, x.Invalidated);
            }
            Print("[V31-SUMMARY] candidates={0} openLedgers={1} executionErrors={2}", _candidateSeq, _positions.Count, _executionErrors);
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
                _executionErrors++;
                Print("[V31-EXCEPTION-ONBAR] {0}", ex);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDaily(false);
                UpdateRiskLocks();
                ManageOpenPosition();
            }
            catch (Exception ex)
            {
                _executionErrors++;
                Print("[V31-EXCEPTION-ONTICK] {0}", ex);
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

                    if (!PassNetRR(c.Signal, out c.SelectedTarget, out c.NetRR))
                    {
                        Reject(c, "RR_REJECTED");
                        continue;
                    }

                    c.Rank = CandidateRank(c);
                    Transition(c, CandidateState.ARMED, "CONFIRMATION_PASSED");
                    CountPipeline(c.Signal.PatternName).Armed++;
                }
            }

            TryScheduleAndExecute();
        }

        private void TryScheduleAndExecute()
        {
            if (!TradingEnabled || _dailyLocked || PeakDrawdownExceeded()) return;
            if (_evaluationStartUtc.HasValue && Server.Time.ToUniversalTime() < _evaluationStartUtc.Value) return;
            if (!IsInstitutionalSession(Server.Time.ToUniversalTime())) return;
            if (!SpreadValid()) return;
            if (OwnPositions().Any()) return;

            var armed = _candidates.Values
                .Where(c => c.State == CandidateState.ARMED && c.IsActive)
                .OrderByDescending(c => c.Rank)
                .ToList();
            if (armed.Count == 0) return;

            var winner = armed[0];
            ExecuteCandidate(winner);

            if (winner.State == CandidateState.EXECUTED)
            {
                foreach (var other in armed.Skip(1))
                    Reject(other, "SINGLE_POSITION_SCHEDULER");
            }
        }

        private void ExecuteCandidate(CandidateRecord c)
        {
            double entry = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double target = c.SelectedTarget;
            if (!GeometryValid(c.Signal.Direction, entry, stop, target))
            {
                Reject(c, "ORDER_GEOMETRY");
                return;
            }

            double slPips = PriceToPips(Math.Abs(entry - stop));
            double tpPips = PriceToPips(Math.Abs(target - entry));
            if (slPips < MinStopLossPips || tpPips <= 0)
            {
                Reject(c, "STOP_DISTANCE");
                return;
            }

            double riskAmount = Account.Equity * (RiskPercent / 100.0);
            if (Account.FreeMargin < riskAmount * MinFreeMarginRiskMultiple)
            {
                Reject(c, "MARGIN_HEADROOM");
                return;
            }

            double volume = CalculateVolume(slPips);
            if (volume <= 0)
            {
                Reject(c, "RISK_VOLUME");
                return;
            }

            TradeType tt = c.Signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            string label = BotPrefix + "|" + (_candidateSeq % 1000000).ToString(CultureInfo.InvariantCulture);
            var tr = ExecuteMarketOrder(tt, SymbolName, volume, label, slPips, tpPips);
            if (tr == null || !tr.IsSuccessful || tr.Position == null)
            {
                _executionErrors++;
                Reject(c, "ORDER_ERROR_" + (tr == null ? "NULL" : tr.Error.ToString()));
                return;
            }

            var p = tr.Position;
            _positions[p.Id] = new PositionLedger
            {
                PositionId = p.Id,
                CandidateId = c.CandidateId,
                PatternName = c.Signal.PatternName,
                Route = c.Route,
                Direction = c.Signal.Direction,
                EntryUtc = Server.Time.ToUniversalTime(),
                InitialRiskPips = slPips,
                RiskAmount = riskAmount,
                PeakR = 0,
                MaxAdverseR = 0
            };
            c.PositionId = p.Id;
            Transition(c, CandidateState.EXECUTED, "ORDER_FILLED");
            CountPipeline(c.Signal.PatternName).Executed++;
            Print("[V31-EXECUTED] cid={0} pos={1} pattern={2} tf=M15 route={3} dir={4} netRR={5:F3} slPips={6:F1} tpPips={7:F1} volume={8}",
                c.CandidateId, p.Id, c.Signal.PatternName, c.Route, c.Signal.Direction, c.NetRR, slPips, tpPips, volume);
        }

        private void ManageOpenPosition()
        {
            foreach (var p in OwnPositions().ToList())
            {
                PositionLedger l;
                if (!_positions.TryGetValue(p.Id, out l))
                {
                    double rp = p.StopLoss.HasValue ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value)) : 0;
                    if (rp <= 0) continue;
                    l = new PositionLedger
                    {
                        PositionId = p.Id,
                        CandidateId = "RECOVERED",
                        PatternName = "UNKNOWN",
                        Route = HarmonicRoute.NO_TRADE,
                        Direction = p.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell,
                        EntryUtc = p.EntryTime.ToUniversalTime(),
                        InitialRiskPips = rp,
                        RiskAmount = 0
                    };
                    _positions[p.Id] = l;
                }

                double currentR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
                if (currentR > l.PeakR) l.PeakR = currentR;
                if (-currentR > l.MaxAdverseR) l.MaxAdverseR = -currentR;

                double age = (Server.Time.ToUniversalTime() - l.EntryUtc).TotalMinutes;
                if (age >= NoMfeMinAgeMinutes && l.PeakR < NoMfeProofR && currentR <= -Math.Abs(NoMfeKillR))
                {
                    l.ExitOverride = "NO_MFE_THESIS_FAILURE";
                    var cr = ClosePosition(p);
                    if (cr == null || !cr.IsSuccessful) _executionErrors++;
                    continue;
                }

                if (l.PeakR >= BreakEvenTriggerR)
                {
                    double lockPips = l.InitialRiskPips * Math.Max(0, BreakEvenLockR);
                    double sl = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + PipsToPrice(lockPips)
                        : p.EntryPrice - PipsToPrice(lockPips);
                    ImproveStopOnly(p, sl);
                }

                if (l.PeakR >= TrailTriggerR)
                {
                    double d = l.InitialRiskPips * Math.Max(0.1, TrailDistanceR);
                    double sl = p.TradeType == TradeType.Buy ? _symbol.Bid - PipsToPrice(d) : _symbol.Ask + PipsToPrice(d);
                    ImproveStopOnly(p, sl);
                }
            }
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.SymbolName != SymbolName || string.IsNullOrWhiteSpace(p.Label) || !p.Label.StartsWith(BotPrefix, StringComparison.Ordinal))
                return;

            PositionLedger l;
            if (!_positions.TryGetValue(p.Id, out l))
            {
                Print("[V31-CLOSED] pos={0} cid=UNKNOWN net={1:F2} reason={2}", p.Id, p.NetProfit, args.Reason);
                return;
            }

            double realizedR = l.InitialRiskPips > 0 ? p.Pips / l.InitialRiskPips : 0;
            string reason = string.IsNullOrWhiteSpace(l.ExitOverride) ? args.Reason.ToString() : l.ExitOverride;
            Print("[V31-CLOSED] cid={0} pos={1} pattern={2} route={3} dir={4} exit={5} mfeR={6:F3} maeR={7:F3} realizedR={8:F3} net={9:F2}",
                l.CandidateId, p.Id, l.PatternName, l.Route, l.Direction, reason, l.PeakR, l.MaxAdverseR, realizedR, p.NetProfit);
            _positions.Remove(p.Id);
        }

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

            double invalid = bullish ? Math.Min(d.Price, przLow) - atr * p.StopBufferAtr : Math.Max(d.Price, przHigh) + atr * p.StopBufferAtr;
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

        private bool PassNetRR(PatternSignal s, out double selectedTarget, out double rr)
        {
            selectedTarget = 0; rr = 0;
            double entry = s.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double riskPips = PriceToPips(Math.Abs(entry - s.StructuralInvalidation));
            if (riskPips < MinStopLossPips) return false;
            double costs = SpreadPips() + Math.Max(0, RoundTurnCommissionPips);

            foreach (double t in new[] { s.CanonicalTarget1, s.CanonicalTarget2 })
            {
                if (!GeometryValid(s.Direction, entry, s.StructuralInvalidation, t)) continue;
                double reward = PriceToPips(Math.Abs(t - entry)) - costs;
                double candidateRr = riskPips > 0 ? reward / riskPips : 0;
                if (candidateRr >= MinimumNetRR)
                {
                    selectedTarget = t;
                    rr = candidateRr;
                    return true;
                }
            }
            return false;
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
            return Positions.Where(p => p.SymbolName == SymbolName && !string.IsNullOrWhiteSpace(p.Label) && p.Label.StartsWith(BotPrefix, StringComparison.Ordinal));
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

        private double CalculateVolume(double slPips)
        {
            if (slPips <= 0 || _symbol.PipValue <= 0) return 0;
            double risk = Account.Equity * RiskPercent / 100.0;
            double raw = risk / (slPips * _symbol.PipValue);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;
            double v = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (v < _symbol.VolumeInUnitsMin) return 0;
            return Math.Min(v, _symbol.VolumeInUnitsMax);
        }

        private void ImproveStopOnly(Position p, double proposed)
        {
            if (p == null) return;
            if (p.TradeType == TradeType.Buy)
            {
                if (proposed >= _symbol.Bid) return;
                if (p.StopLoss.HasValue && proposed <= p.StopLoss.Value) return;
            }
            else
            {
                if (proposed <= _symbol.Ask) return;
                if (p.StopLoss.HasValue && proposed >= p.StopLoss.Value) return;
            }
            var r = ModifyPosition(p, proposed, p.TakeProfit);
            if (r == null || !r.IsSuccessful) _executionErrors++;
        }

        private void EnsureServerProtection()
        {
            foreach (var p in OwnPositions())
            {
                if (p.StopLoss.HasValue && p.TakeProfit.HasValue) continue;
                PositionLedger l;
                if (!_positions.TryGetValue(p.Id, out l) || l.InitialRiskPips <= 0) continue;
                double sl = p.TradeType == TradeType.Buy ? p.EntryPrice - PipsToPrice(l.InitialRiskPips) : p.EntryPrice + PipsToPrice(l.InitialRiskPips);
                double tp = p.TradeType == TradeType.Buy ? p.EntryPrice + PipsToPrice(l.InitialRiskPips * MinimumNetRR) : p.EntryPrice - PipsToPrice(l.InitialRiskPips * MinimumNetRR);
                var r = ModifyPosition(p, sl, tp);
                if (r == null || !r.IsSuccessful) _executionErrors++;
            }
        }

        // ---------------- Candidate state / telemetry ----------------

        private string NewCandidateId(PatternSignal s)
        {
            _candidateSeq++;
            return "V31-" + _candidateSeq.ToString("D8", CultureInfo.InvariantCulture) + "-" +
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
            Print("[V31-EVENT] cid={0} pattern={1} tf={2} dir={3} state={4} route={5} conflict={6} reason={7}",
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

        private bool BarsReady()
        {
            return Count(_h4Bars) >= 230 && Count(_h1Bars) >= 230 && Count(_m15Bars) >= 360 && Count(_m1Bars) >= 50;
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
    }

    public sealed class PipelineCounter
    {
        public long Detected, Validated, Routed, PrzWaiting, Confirming, Armed, Executed, Expired, Rejected, Invalidated;
    }
}
