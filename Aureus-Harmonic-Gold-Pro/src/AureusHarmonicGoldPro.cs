using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class AureusHarmonicGoldPro : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }
        [Parameter("Bot Label", DefaultValue = "AUREUS_XAUUSD", Group = "General")]
        public string BotLabel { get; set; }
        [Parameter("Require XAUUSD Symbol", DefaultValue = true, Group = "General")]
        public bool RequireXauUsd { get; set; }

        [Parameter("Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 3.0, Group = "Risk")]
        public double RiskPercent { get; set; }
        [Parameter("Min Net RR", DefaultValue = 1.75, MinValue = 1.0, MaxValue = 8.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }
        [Parameter("SL ATR Buffer", DefaultValue = 0.18, MinValue = 0.0, MaxValue = 2.0, Group = "Risk")]
        public double StopAtrBuffer { get; set; }
        [Parameter("Breakeven At R", DefaultValue = 1.00, MinValue = 0.5, MaxValue = 5.0, Group = "Risk")]
        public double BreakEvenAtR { get; set; }
        [Parameter("Trail Start R", DefaultValue = 1.75, MinValue = 0.5, MaxValue = 8.0, Group = "Risk")]
        public double TrailStartR { get; set; }
        [Parameter("Trail ATR", DefaultValue = 1.20, MinValue = 0.2, MaxValue = 5.0, Group = "Risk")]
        public double TrailAtrMultiplier { get; set; }

        [Parameter("Daily Loss %", DefaultValue = 2.5, MinValue = 0.0, MaxValue = 20.0, Group = "Risk Governor")]
        public double MaxDailyLossPercent { get; set; }
        [Parameter("Weekly Loss %", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 30.0, Group = "Risk Governor")]
        public double MaxWeeklyLossPercent { get; set; }
        [Parameter("Monthly Loss %", DefaultValue = 8.0, MinValue = 0.0, MaxValue = 40.0, Group = "Risk Governor")]
        public double MaxMonthlyLossPercent { get; set; }
        [Parameter("Peak Drawdown Kill %", DefaultValue = 15.0, MinValue = 1.0, MaxValue = 50.0, Group = "Risk Governor")]
        public double MaxPeakDrawdownPercent { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 3, MinValue = 1, MaxValue = 20, Group = "Limits")]
        public int MaxTradesPerDay { get; set; }
        [Parameter("Cooldown Bars", DefaultValue = 4, MinValue = 0, MaxValue = 100, Group = "Limits")]
        public int CooldownBars { get; set; }

        [Parameter("Pivot Left", DefaultValue = 3, MinValue = 2, MaxValue = 20, Group = "Patterns")]
        public int PivotLeft { get; set; }
        [Parameter("Pivot Right", DefaultValue = 3, MinValue = 2, MaxValue = 20, Group = "Patterns")]
        public int PivotRight { get; set; }
        [Parameter("Pivot Lookback", DefaultValue = 650, MinValue = 120, MaxValue = 5000, Group = "Patterns")]
        public int PivotLookback { get; set; }
        [Parameter("Max Pivot Skip", DefaultValue = 3, MinValue = 0, MaxValue = 8, Group = "Patterns")]
        public int MaxPivotSkip { get; set; }
        [Parameter("Max M15 Pattern Age", DefaultValue = 3, MinValue = 0, MaxValue = 30, Group = "Patterns")]
        public int MaxM15PatternAge { get; set; }
        [Parameter("Max H1 Pattern Age", DefaultValue = 6, MinValue = 0, MaxValue = 60, Group = "Patterns")]
        public int MaxH1PatternAge { get; set; }
        [Parameter("Max H4 Pattern Age", DefaultValue = 4, MinValue = 0, MaxValue = 40, Group = "Patterns")]
        public int MaxH4PatternAge { get; set; }
        [Parameter("Min Pattern Score %", DefaultValue = 80.0, MinValue = 65.0, MaxValue = 100.0, Group = "Patterns")]
        public double MinPatternScore { get; set; }
        [Parameter("Ratio Tolerance %", DefaultValue = 5.0, MinValue = 1.0, MaxValue = 15.0, Group = "Patterns")]
        public double RatioTolerancePercent { get; set; }
        [Parameter("Max Entry Distance ATR", DefaultValue = 1.50, MinValue = 0.25, MaxValue = 5.0, Group = "Patterns")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Require Higher-TF Agreement", DefaultValue = false, Group = "MTF")]
        public bool RequireHigherTimeframeAgreement { get; set; }
        [Parameter("Higher-TF Min Score %", DefaultValue = 78.0, MinValue = 65.0, MaxValue = 100.0, Group = "MTF")]
        public double HigherTimeframeMinScore { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 60.0, MinValue = 0.0, Group = "Execution")]
        public double MaxSpreadPips { get; set; }
        [Parameter("Execution Reserve (pips)", DefaultValue = 6.0, MinValue = 0.0, Group = "Execution")]
        public double ExecutionReservePips { get; set; }
        [Parameter("ATR Period", DefaultValue = 14, MinValue = 5, MaxValue = 100, Group = "Execution")]
        public int AtrPeriod { get; set; }
        [Parameter("Min ATR M15 (pips)", DefaultValue = 120.0, MinValue = 0.0, Group = "Execution")]
        public double MinAtrPips { get; set; }
        [Parameter("Max ATR Shock x Median", DefaultValue = 3.0, MinValue = 1.0, MaxValue = 10.0, Group = "Execution")]
        public double MaxAtrShockMultiple { get; set; }
        [Parameter("Manual News Blackout UTC", DefaultValue = "", Group = "Execution")]
        public string ManualNewsBlackoutUtc { get; set; }
        [Parameter("Debug Logging", DefaultValue = true, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }

        private Bars _m15;
        private Bars _h1;
        private Bars _h4;
        private AverageTrueRange _atrM15;
        private readonly HashSet<string> _evaluatedSignals = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<long, double> _initialRiskPrice = new Dictionary<long, double>();
        private readonly Dictionary<string, int> _patternDetections = new Dictionary<string, int>(StringComparer.Ordinal);
        private List<PatternDefinition> _patterns;
        private DateTime _day;
        private DateTime _weekAnchor;
        private int _monthKey;
        private double _dayStartEquity;
        private double _weekStartEquity;
        private double _monthStartEquity;
        private double _equityHighWater;
        private int _tradesToday;
        private int _lastTradeBar = -1000000;
        private bool _entryInFlight;
        private bool _killed;
        private long _m15Candidates;
        private long _mtfBlocks;
        private long _distanceBlocks;
        private long _rrBlocks;
        private long _riskBlocks;
        private long _exposureBlocks;
        private long _openedTrades;

        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _h4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _atrM15 = Indicators.AverageTrueRange(_m15, AtrPeriod, MovingAverageType.Exponential);
            _patterns = PatternLibrary.Create();
            ResetPeriodAnchors(true);
            _equityHighWater = Account.Equity;
            Positions.Closed += OnPositionClosed;
            foreach (var position in Positions.Where(p => p.SymbolName == SymbolName && p.Label == BotLabel))
            {
                double risk = ParseInitialRiskFromComment(position.Comment);
                if (risk > 0)
                    _initialRiskPrice[position.Id] = risk;
            }
            Print("AUREUS v1.1 | Symbol={0} TF={1} Trading={2}", SymbolName, TimeFrame, TradingEnabled);
            Print("Confirmed harmonic entries only. H1/H4: opposite=veto, same=confluence, absent=neutral.");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            Print("[DIAG] candidates={0} mtfBlocks={1} distanceBlocks={2} rrBlocks={3} riskBlocks={4} exposureBlocks={5} opened={6}",
                _m15Candidates, _mtfBlocks, _distanceBlocks, _rrBlocks, _riskBlocks, _exposureBlocks, _openedTrades);
            foreach (var kv in _patternDetections.OrderBy(k => k.Key))
                Print("[DIAG PATTERN] {0}={1}", kv.Key, kv.Value);
        }

        protected override void OnBarClosed()
        {
            if (_killed || !TradingEnabled)
                return;
            if (RequireXauUsd && !NormalizeSymbol(SymbolName).Contains("XAUUSD"))
            {
                if (DebugLogging) Print("[BLOCK] Symbol {0} is not XAUUSD.", SymbolName);
                return;
            }
            if (TimeFrame != TimeFrame.Minute15)
            {
                if (DebugLogging) Print("[BLOCK] Attach this cBot to XAUUSD M15. Current TF={0}", TimeFrame);
                return;
            }

            ResetPeriodAnchors(false);
            UpdateEquityKillSwitch();
            if (!PassRiskGovernor() || !PassExecutionFilters())
                return;
            if (_m15.Count < 160 || _h1.Count < 160 || _h4.Count < 160)
                return;

            PatternMatch m15 = FindBestPattern(_m15, MaxM15PatternAge, MinPatternScore);
            if (m15 == null || _evaluatedSignals.Contains(m15.SignalKey))
                return;

            _m15Candidates++;
            CountPattern(m15.Definition.Code);
            PatternMatch h1 = FindBestPattern(_h1, MaxH1PatternAge, HigherTimeframeMinScore);
            PatternMatch h4 = FindBestPattern(_h4, MaxH4PatternAge, HigherTimeframeMinScore);

            if (!ResolveTimeframeConflict(m15, h1, h4))
            {
                _mtfBlocks++;
                _evaluatedSignals.Add(m15.SignalKey);
                return;
            }

            double atr = _atrM15.Result.LastValue;
            double entry = m15.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            if (!IsFinitePositive(atr) || Math.Abs(entry - m15.D.Price) > atr * MaxEntryDistanceAtr)
            {
                _distanceBlocks++;
                _evaluatedSignals.Add(m15.SignalKey);
                if (DebugLogging) Print("[BLOCK] Pattern {0} expired away from D/PRZ.", m15.Definition.Code);
                return;
            }

            if (_tradesToday >= MaxTradesPerDay || _m15.Count - 1 - _lastTradeBar < CooldownBars)
            {
                _evaluatedSignals.Add(m15.SignalKey);
                return;
            }

            if (HasAnySameSymbolExposure())
            {
                _exposureBlocks++;
                _evaluatedSignals.Add(m15.SignalKey);
                if (DebugLogging) Print("[BLOCK] Existing same-symbol exposure prevents duplicate or hedge.");
                return;
            }

            _evaluatedSignals.Add(m15.SignalKey);
            ExecutePatternTrade(m15);
        }

        protected override void OnTick()
        {
            if (_atrM15 == null)
                return;
            foreach (var p in Positions.Where(x => x.SymbolName == SymbolName && x.Label == BotLabel).ToArray())
                ManagePosition(p);
        }

        private void ExecutePatternTrade(PatternMatch m)
        {
            if (_entryInFlight || HasAnySameSymbolExposure())
                return;
            _entryInFlight = true;
            try
            {
                double atr = _atrM15.Result.LastValue;
                if (!IsFinitePositive(atr)) return;
                double entry = m.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                double structuralExtreme = m.Direction == TradeType.Buy ? Math.Min(m.X.Price, m.D.Price) : Math.Max(m.X.Price, m.D.Price);
                double slPrice = m.Direction == TradeType.Buy ? structuralExtreme - atr * StopAtrBuffer : structuralExtreme + atr * StopAtrBuffer;
                double stopDistance = m.Direction == TradeType.Buy ? entry - slPrice : slPrice - entry;
                if (!IsFinitePositive(stopDistance)) { _riskBlocks++; return; }
                double slPips = stopDistance / Symbol.PipSize;
                if (slPips <= ExecutionReservePips) { _riskBlocks++; return; }

                double targetPrice = m.Direction == TradeType.Buy
                    ? m.D.Price + Math.Abs(m.A.Price - m.D.Price) * 0.618
                    : m.D.Price - Math.Abs(m.A.Price - m.D.Price) * 0.618;
                double tpDistance = m.Direction == TradeType.Buy ? targetPrice - entry : entry - targetPrice;
                if (!IsFinitePositive(tpDistance)) { _rrBlocks++; return; }
                double tpPips = tpDistance / Symbol.PipSize;
                double netRr = (tpPips - ExecutionReservePips) / (slPips + ExecutionReservePips);
                if (netRr < MinimumRiskReward)
                {
                    _rrBlocks++;
                    if (DebugLogging) Print("[BLOCK] {0} Fibonacci target net RR {1:F2} < {2:F2}", m.Definition.Code, netRr, MinimumRiskReward);
                    return;
                }

                double riskCash = Account.Equity * RiskPercent / 100.0;
                double volume = Symbol.VolumeForFixedRisk(riskCash, slPips + ExecutionReservePips, RoundingMode.Down);
                volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
                if (!IsFinitePositive(volume) || volume < Symbol.VolumeInUnitsMin) { _riskBlocks++; return; }
                if (volume > Symbol.VolumeInUnitsMax) volume = Symbol.VolumeInUnitsMax;
                double estimatedRisk = Symbol.AmountRisked(volume, slPips + ExecutionReservePips);
                if (!IsFinitePositive(estimatedRisk) || estimatedRisk > riskCash * 1.001)
                {
                    _riskBlocks++;
                    if (DebugLogging) Print("[BLOCK] Risk budget check failed estimated={0:F2} budget={1:F2}", estimatedRisk, riskCash);
                    return;
                }

                string comment = string.Format(System.Globalization.CultureInfo.InvariantCulture,
                    "{0}|risk={1:F8}|score={2:F1}", m.Definition.Code, stopDistance, m.Score);
                TradeResult result = ExecuteMarketOrder(m.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment, false);
                if (!result.IsSuccessful || result.Position == null)
                {
                    Print("[ORDER FAIL] {0}", result.Error);
                    return;
                }
                if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
                {
                    Print("[PROTECTION FAIL] Closing unprotected position {0}.", result.Position.Id);
                    ClosePosition(result.Position);
                    return;
                }

                _initialRiskPrice[result.Position.Id] = stopDistance;
                _lastTradeBar = _m15.Count - 1;
                _tradesToday++;
                _openedTrades++;
                Print("[OPEN] {0} {1} score={2:F1} vol={3} SL={4:F1}p TP={5:F1}p netRR={6:F2}",
                    m.Definition.Code, m.Direction, m.Score, volume, slPips, tpPips, netRr);
            }
            finally { _entryInFlight = false; }
        }

        private void ManagePosition(Position p)
        {
            double initialRisk;
            if (!_initialRiskPrice.TryGetValue(p.Id, out initialRisk) || !IsFinitePositive(initialRisk))
            {
                initialRisk = ParseInitialRiskFromComment(p.Comment);
                if (!IsFinitePositive(initialRisk)) return;
                _initialRiskPrice[p.Id] = initialRisk;
            }
            double favorable = p.TradeType == TradeType.Buy ? Symbol.Bid - p.EntryPrice : p.EntryPrice - Symbol.Ask;
            if (favorable <= 0) return;
            double r = favorable / initialRisk;
            double desired = p.StopLoss.HasValue ? p.StopLoss.Value : double.NaN;

            if (r >= BreakEvenAtR)
            {
                double be = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + Symbol.PipSize * ExecutionReservePips
                    : p.EntryPrice - Symbol.PipSize * ExecutionReservePips;
                if (double.IsNaN(desired) || (p.TradeType == TradeType.Buy && be > desired) || (p.TradeType == TradeType.Sell && be < desired))
                    desired = be;
            }
            if (r >= TrailStartR)
            {
                double atr = _atrM15.Result.LastValue;
                if (IsFinitePositive(atr))
                {
                    double trail = p.TradeType == TradeType.Buy ? Symbol.Bid - atr * TrailAtrMultiplier : Symbol.Ask + atr * TrailAtrMultiplier;
                    if (p.TradeType == TradeType.Buy && (double.IsNaN(desired) || trail > desired)) desired = trail;
                    if (p.TradeType == TradeType.Sell && (double.IsNaN(desired) || trail < desired)) desired = trail;
                }
            }
            if (double.IsNaN(desired)) return;
            bool improves = !p.StopLoss.HasValue ||
                (p.TradeType == TradeType.Buy && desired > p.StopLoss.Value + Symbol.TickSize) ||
                (p.TradeType == TradeType.Sell && desired < p.StopLoss.Value - Symbol.TickSize);
            if (!improves) return;
            TradeResult mod = ModifyPosition(p, desired, p.TakeProfit);
            if (!mod.IsSuccessful && DebugLogging) Print("[MODIFY FAIL] pid={0} err={1}", p.Id, mod.Error);
        }

        private bool ResolveTimeframeConflict(PatternMatch m15, PatternMatch h1, PatternMatch h4)
        {
            int agreements = 0;
            if (h1 != null)
            {
                if (h1.Direction != m15.Direction)
                {
                    if (DebugLogging) Print("[MTF BLOCK] H1 opposite {0} vs M15 {1}", h1.Direction, m15.Direction);
                    return false;
                }
                agreements++;
            }
            if (h4 != null)
            {
                if (h4.Direction != m15.Direction)
                {
                    if (DebugLogging) Print("[MTF BLOCK] H4 opposite {0} vs M15 {1}", h4.Direction, m15.Direction);
                    return false;
                }
                agreements++;
            }
            if (RequireHigherTimeframeAgreement && agreements == 0)
            {
                if (DebugLogging) Print("[MTF BLOCK] No same-direction H1/H4 harmonic confluence.");
                return false;
            }
            return true;
        }

        private PatternMatch FindBestPattern(Bars bars, int maxAgeAfterConfirmation, double minScore)
        {
            List<PivotPoint> pivots = BuildConfirmedPivots(bars);
            if (pivots.Count < 5) return null;
            PatternMatch best = null;
            int dMin = Math.Max(4, pivots.Count - 14);
            int skip = Math.Max(0, MaxPivotSkip);
            for (int iD = pivots.Count - 1; iD >= dMin; iD--)
            {
                PivotPoint d = pivots[iD];
                int age = bars.Count - 1 - d.Index - PivotRight;
                if (age < 0 || age > maxAgeAfterConfirmation) continue;
                int cFloor = Math.Max(3, iD - 1 - skip);
                for (int iC = iD - 1; iC >= cFloor; iC--)
                {
                    int bFloor = Math.Max(2, iC - 1 - skip);
                    for (int iB = iC - 1; iB >= bFloor; iB--)
                    {
                        int aFloor = Math.Max(1, iB - 1 - skip);
                        for (int iA = iB - 1; iA >= aFloor; iA--)
                        {
                            int xFloor = Math.Max(0, iA - 1 - skip);
                            for (int iX = iA - 1; iX >= xFloor; iX--)
                            {
                                PivotPoint x = pivots[iX];
                                PivotPoint a = pivots[iA];
                                PivotPoint b = pivots[iB];
                                PivotPoint c = pivots[iC];
                                TradeType? direction = GetDirection(x, a, b, c, d);
                                if (!direction.HasValue) continue;
                                double xa = Math.Abs(a.Price - x.Price);
                                double ab = Math.Abs(b.Price - a.Price);
                                double bc = Math.Abs(c.Price - b.Price);
                                double cd = Math.Abs(d.Price - c.Price);
                                if (!IsFinitePositive(xa) || !IsFinitePositive(ab) || !IsFinitePositive(bc) || !IsFinitePositive(cd)) continue;
                                double bXa = ab / xa;
                                double cAb = bc / ab;
                                double dXa = Math.Abs(a.Price - d.Price) / xa;
                                double cdBc = cd / bc;
                                double cdAb = cd / ab;
                                foreach (PatternDefinition def in _patterns)
                                {
                                    double score = def.Score(bXa, cAb, dXa, cdBc, cdAb, RatioTolerancePercent);
                                    if (score < minScore) continue;
                                    PatternMatch match = new PatternMatch(def, direction.Value, x, a, b, c, d, score, bars.OpenTimes[d.Index]);
                                    if (best == null || match.Score > best.Score + 0.0001 ||
                                        (Math.Abs(match.Score - best.Score) <= 0.0001 && match.D.Index > best.D.Index))
                                        best = match;
                                }
                            }
                        }
                    }
                }
            }
            return best;
        }

        private List<PivotPoint> BuildConfirmedPivots(Bars bars)
        {
            var pivots = new List<PivotPoint>();
            int latestConfirmed = bars.Count - 1 - PivotRight;
            int first = Math.Max(PivotLeft, bars.Count - PivotLookback);
            for (int i = first; i <= latestConfirmed; i++)
            {
                bool high = true;
                bool low = true;
                for (int j = 1; j <= PivotLeft; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i - j]) high = false;
                    if (bars.LowPrices[i] >= bars.LowPrices[i - j]) low = false;
                }
                for (int j = 1; j <= PivotRight; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i + j]) high = false;
                    if (bars.LowPrices[i] >= bars.LowPrices[i + j]) low = false;
                }
                if (high && !low) AddAlternating(pivots, new PivotPoint(i, bars.HighPrices[i], PivotKind.High));
                else if (low && !high) AddAlternating(pivots, new PivotPoint(i, bars.LowPrices[i], PivotKind.Low));
            }
            if (pivots.Count > 120) pivots = pivots.GetRange(pivots.Count - 120, 120);
            return pivots;
        }

        private void AddAlternating(List<PivotPoint> pivots, PivotPoint next)
        {
            if (pivots.Count == 0) { pivots.Add(next); return; }
            PivotPoint last = pivots[pivots.Count - 1];
            if (last.Kind != next.Kind) { pivots.Add(next); return; }
            bool replace = next.Kind == PivotKind.High ? next.Price > last.Price : next.Price < last.Price;
            if (replace) pivots[pivots.Count - 1] = next;
        }

        private TradeType? GetDirection(PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d)
        {
            bool bullish = x.Kind == PivotKind.Low && a.Kind == PivotKind.High && b.Kind == PivotKind.Low && c.Kind == PivotKind.High && d.Kind == PivotKind.Low;
            bool bearish = x.Kind == PivotKind.High && a.Kind == PivotKind.Low && b.Kind == PivotKind.High && c.Kind == PivotKind.Low && d.Kind == PivotKind.High;
            if (bullish) return TradeType.Buy;
            if (bearish) return TradeType.Sell;
            return null;
        }

        private bool PassExecutionFilters()
        {
            if (!IsWithinLondonToNewYorkWindow(Server.Time) || IsManualNewsBlackout(Server.Time)) return false;
            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips) return false;
            double atr = _atrM15.Result.LastValue;
            if (!IsFinitePositive(atr)) return false;
            double atrPips = atr / Symbol.PipSize;
            if (MinAtrPips > 0 && atrPips < MinAtrPips) return false;
            double median = MedianAtr(64);
            if (median > 0 && MaxAtrShockMultiple > 1 && atr > median * MaxAtrShockMultiple) return false;
            return true;
        }

        private bool PassRiskGovernor()
        {
            if (_killed || _tradesToday >= MaxTradesPerDay) return false;
            if (MaxDailyLossPercent > 0 && LossPercent(_dayStartEquity, Account.Equity) >= MaxDailyLossPercent) return false;
            if (MaxWeeklyLossPercent > 0 && LossPercent(_weekStartEquity, Account.Equity) >= MaxWeeklyLossPercent) return false;
            if (MaxMonthlyLossPercent > 0 && LossPercent(_monthStartEquity, Account.Equity) >= MaxMonthlyLossPercent) return false;
            return true;
        }

        private void UpdateEquityKillSwitch()
        {
            if (Account.Equity > _equityHighWater) _equityHighWater = Account.Equity;
            if (MaxPeakDrawdownPercent <= 0 || _equityHighWater <= 0) return;
            double dd = 100.0 * (_equityHighWater - Account.Equity) / _equityHighWater;
            if (dd >= MaxPeakDrawdownPercent)
            {
                _killed = true;
                Print("[KILL] Peak-to-equity drawdown {0:F2}% >= {1:F2}%. New entries disabled.", dd, MaxPeakDrawdownPercent);
            }
        }

        private void ResetPeriodAnchors(bool force)
        {
            DateTime now = Server.Time;
            DateTime monday = now.Date.AddDays(-(((int)now.DayOfWeek + 6) % 7));
            int monthKey = now.Year * 100 + now.Month;
            if (force || now.Date != _day) { _day = now.Date; _dayStartEquity = Account.Equity; _tradesToday = 0; }
            if (force || monday != _weekAnchor) { _weekAnchor = monday; _weekStartEquity = Account.Equity; }
            if (force || monthKey != _monthKey) { _monthKey = monthKey; _monthStartEquity = Account.Equity; }
        }

        private bool HasAnySameSymbolExposure()
        {
            return Positions.Any(p => p.SymbolName == SymbolName) || PendingOrders.Any(o => o.SymbolName == SymbolName);
        }

        private double MedianAtr(int count)
        {
            int available = Math.Min(count, _m15.Count - 2);
            if (available < 10) return 0;
            var values = new List<double>(available);
            for (int i = 1; i <= available; i++)
            {
                double value = _atrM15.Result.Last(i);
                if (IsFinitePositive(value)) values.Add(value);
            }
            if (values.Count < 10) return 0;
            values.Sort();
            int mid = values.Count / 2;
            return values.Count % 2 == 0 ? (values[mid - 1] + values[mid]) / 2.0 : values[mid];
        }

        private bool IsWithinLondonToNewYorkWindow(DateTime utc)
        {
            if (utc.DayOfWeek == DayOfWeek.Saturday || utc.DayOfWeek == DayOfWeek.Sunday) return false;
            int londonOpenUtc = IsUkDst(utc.Date) ? 7 : 8;
            int newYorkCloseUtc = IsUsDst(utc.Date) ? 21 : 22;
            double hour = utc.Hour + utc.Minute / 60.0;
            return hour >= londonOpenUtc && hour < newYorkCloseUtc;
        }
        private static bool IsUkDst(DateTime date)
        {
            DateTime start = LastSunday(date.Year, 3);
            DateTime end = LastSunday(date.Year, 10);
            return date >= start && date < end;
        }
        private static bool IsUsDst(DateTime date)
        {
            DateTime start = NthSunday(date.Year, 3, 2);
            DateTime end = NthSunday(date.Year, 11, 1);
            return date >= start && date < end;
        }
        private static DateTime LastSunday(int year, int month)
        {
            DateTime d = new DateTime(year, month, DateTime.DaysInMonth(year, month));
            while (d.DayOfWeek != DayOfWeek.Sunday) d = d.AddDays(-1);
            return d;
        }
        private static DateTime NthSunday(int year, int month, int n)
        {
            DateTime d = new DateTime(year, month, 1);
            while (d.DayOfWeek != DayOfWeek.Sunday) d = d.AddDays(1);
            return d.AddDays(7 * (n - 1));
        }

        private bool IsManualNewsBlackout(DateTime utc)
        {
            if (string.IsNullOrWhiteSpace(ManualNewsBlackoutUtc)) return false;
            string[] windows = ManualNewsBlackoutUtc.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string window in windows)
            {
                string[] pair = window.Trim().Split('/');
                if (pair.Length != 2) continue;
                DateTime start;
                DateTime end;
                if (!DateTime.TryParse(pair[0].Trim(), out start) || !DateTime.TryParse(pair[1].Trim(), out end)) continue;
                start = DateTime.SpecifyKind(start, DateTimeKind.Utc);
                end = DateTime.SpecifyKind(end, DateTimeKind.Utc);
                if (utc >= start && utc <= end) return true;
            }
            return false;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != BotLabel) return;
            _initialRiskPrice.Remove(p.Id);
            Print("[CLOSE] id={0} net={1:F2} pips={2:F1}", p.Id, p.NetProfit, p.Pips);
        }

        private void CountPattern(string name)
        {
            int count;
            _patternDetections.TryGetValue(name, out count);
            _patternDetections[name] = count + 1;
        }
        private static double LossPercent(double start, double current)
        {
            if (start <= 0 || current >= start) return 0;
            return 100.0 * (start - current) / start;
        }
        private static string NormalizeSymbol(string symbol)
        {
            if (string.IsNullOrWhiteSpace(symbol)) return "";
            return new string(symbol.ToUpperInvariant().Where(char.IsLetterOrDigit).ToArray());
        }
        private static bool IsFinitePositive(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value) && value > 0;
        }
        private static double ParseInitialRiskFromComment(string comment)
        {
            if (string.IsNullOrWhiteSpace(comment)) return 0;
            foreach (string token in comment.Split('|'))
            {
                if (!token.StartsWith("risk=", StringComparison.OrdinalIgnoreCase)) continue;
                double value;
                if (double.TryParse(token.Substring(5), System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out value)) return value;
            }
            return 0;
        }

        private enum PivotKind { High, Low }
        private sealed class PivotPoint
        {
            public int Index { get; private set; }
            public double Price { get; private set; }
            public PivotKind Kind { get; private set; }
            public PivotPoint(int index, double price, PivotKind kind) { Index = index; Price = price; Kind = kind; }
        }

        private sealed class PatternMatch
        {
            public PatternDefinition Definition { get; private set; }
            public TradeType Direction { get; private set; }
            public PivotPoint X { get; private set; }
            public PivotPoint A { get; private set; }
            public PivotPoint B { get; private set; }
            public PivotPoint C { get; private set; }
            public PivotPoint D { get; private set; }
            public double Score { get; private set; }
            public DateTime DTime { get; private set; }
            public string SignalKey
            {
                get
                {
                    return string.Format(System.Globalization.CultureInfo.InvariantCulture,
                        "{0}|{1}|{2:O}|{3}|{4}|{5}|{6}|{7}", Definition.Code, Direction, DTime,
                        X.Index, A.Index, B.Index, C.Index, D.Index);
                }
            }
            public PatternMatch(PatternDefinition definition, TradeType direction, PivotPoint x, PivotPoint a,
                PivotPoint b, PivotPoint c, PivotPoint d, double score, DateTime dTime)
            {
                Definition = definition; Direction = direction; X = x; A = a; B = b; C = c; D = d; Score = score; DTime = dTime;
            }
        }

        private sealed class RatioRule
        {
            public double Min { get; private set; }
            public double Max { get; private set; }
            public double Weight { get; private set; }
            public RatioRule(double min, double max, double weight) { Min = min; Max = max; Weight = weight; }
            public double Score(double value, double tolerancePercent)
            {
                if (double.IsNaN(value) || double.IsInfinity(value)) return 0;
                double center = (Min + Max) / 2.0;
                double tolerance = Math.Max(Math.Abs(center) * tolerancePercent / 100.0, 0.000001);
                double lo = Min - tolerance;
                double hi = Max + tolerance;
                if (value < lo || value > hi) return 0;
                if (Math.Abs(Max - Min) < 0.000001)
                {
                    double distance = Math.Abs(value - center);
                    return Math.Max(70.0, 100.0 - 30.0 * distance / tolerance);
                }
                if (value >= Min && value <= Max)
                {
                    double halfWidth = Math.Max((Max - Min) / 2.0, 0.000001);
                    double normalized = Math.Abs(value - center) / halfWidth;
                    return Math.Max(90.0, 100.0 - 10.0 * normalized);
                }
                double outside = value < Min ? Min - value : value - Max;
                return Math.Max(70.0, 90.0 - 20.0 * outside / tolerance);
            }
        }

        private sealed class PatternDefinition
        {
            public string Code { get; private set; }
            public RatioRule B_XA { get; private set; }
            public RatioRule C_AB { get; private set; }
            public RatioRule D_XA { get; private set; }
            public RatioRule CD_BC { get; private set; }
            public RatioRule CD_AB { get; private set; }
            public PatternDefinition(string code, RatioRule bXa, RatioRule cAb, RatioRule dXa, RatioRule cdBc, RatioRule cdAb)
            {
                Code = code; B_XA = bXa; C_AB = cAb; D_XA = dXa; CD_BC = cdBc; CD_AB = cdAb;
            }
            public double Score(double bXa, double cAb, double dXa, double cdBc, double cdAb, double tolerance)
            {
                double s1 = B_XA.Score(bXa, tolerance);
                double s2 = C_AB.Score(cAb, tolerance);
                double s3 = D_XA.Score(dXa, tolerance);
                double s4 = CD_BC.Score(cdBc, tolerance);
                double s5 = CD_AB.Score(cdAb, tolerance);
                if (s1 <= 0 || s2 <= 0 || s3 <= 0 || s4 <= 0 || s5 <= 0) return 0;
                double weighted = s1 * B_XA.Weight + s2 * C_AB.Weight + s3 * D_XA.Weight + s4 * CD_BC.Weight + s5 * CD_AB.Weight;
                double weights = B_XA.Weight + C_AB.Weight + D_XA.Weight + CD_BC.Weight + CD_AB.Weight;
                return weighted / weights;
            }
        }

        private static class PatternLibrary
        {
            public static List<PatternDefinition> Create()
            {
                return new List<PatternDefinition>
                {
                    new PatternDefinition("H1_GARTLEY",
                        new RatioRule(0.618, 0.618, 1.40), new RatioRule(0.382, 0.886, 0.75),
                        new RatioRule(0.786, 0.786, 1.60), new RatioRule(1.130, 1.618, 0.90), new RatioRule(1.000, 1.270, 0.85)),
                    new PatternDefinition("H2_BAT",
                        new RatioRule(0.382, 0.500, 1.25), new RatioRule(0.382, 0.886, 0.75),
                        new RatioRule(0.886, 0.886, 1.70), new RatioRule(1.618, 2.618, 0.90), new RatioRule(1.000, 1.270, 0.85)),
                    new PatternDefinition("H3_BFLY",
                        new RatioRule(0.786, 0.786, 1.40), new RatioRule(0.382, 0.886, 0.75),
                        new RatioRule(1.270, 1.270, 1.70), new RatioRule(1.618, 2.618, 0.90), new RatioRule(1.000, 1.270, 0.85)),
                    new PatternDefinition("H4_CRAB",
                        new RatioRule(0.382, 0.618, 1.15), new RatioRule(0.382, 0.886, 0.75),
                        new RatioRule(1.618, 1.618, 1.80), new RatioRule(2.240, 3.618, 0.90), new RatioRule(1.000, 1.618, 0.75)),
                    new PatternDefinition("H5_DEEP",
                        new RatioRule(0.886, 0.886, 1.50), new RatioRule(0.382, 0.886, 0.75),
                        new RatioRule(1.618, 1.618, 1.80), new RatioRule(2.240, 3.618, 0.90), new RatioRule(1.000, 1.618, 0.75))
                };
            }
        }
    }
}
