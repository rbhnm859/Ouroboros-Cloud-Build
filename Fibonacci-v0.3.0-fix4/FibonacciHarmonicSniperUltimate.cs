using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class FibonacciHarmonicSniperUltimate : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = false, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "FHSU", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Enabled Patterns", DefaultValue = "CORE", Group = "Patterns")]
        public string EnabledPatterns { get; set; }

        [Parameter("Custom Pattern Ratios", DefaultValue = "", Group = "Patterns")]
        public string CustomPatternRatios { get; set; }

        [Parameter("Min Pattern Score %", DefaultValue = 85.0, MinValue = 50.0, MaxValue = 100.0, Group = "Patterns")]
        public double MinPatternScore { get; set; }

        [Parameter("Ratio Tolerance %", DefaultValue = 6.0, MinValue = 0.0, MaxValue = 25.0, Group = "Patterns")]
        public double RatioTolerancePercent { get; set; }

        [Parameter("Pivot Left Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback Bars", DefaultValue = 500, MinValue = 100, MaxValue = 5000, Group = "Pivots")]
        public int PivotLookback { get; set; }

        [Parameter("Max Pattern Age Bars", DefaultValue = 12, MinValue = 1, MaxValue = 100, Group = "Pivots")]
        public int MaxPatternAgeBars { get; set; }

        [Parameter("Min XA Size (pips)", DefaultValue = 0.0, MinValue = 0.0, Group = "Filters")]
        public double MinXaPips { get; set; }

        [Parameter("EMA Filter Mode", DefaultValue = TrendFilterMode.ScoreOnly, Group = "Filters")]
        public TrendFilterMode EmaFilterMode { get; set; }

        [Parameter("EMA Period", DefaultValue = 50, MinValue = 2, MaxValue = 500, Group = "Filters")]
        public int EmaPeriod { get; set; }

        [Parameter("Require EMA Slope", DefaultValue = true, Group = "Filters")]
        public bool RequireEmaSlope { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 2, MaxValue = 200, Group = "Filters")]
        public int AtrPeriod { get; set; }

        [Parameter("Min ATR (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Filters")]
        public double MinAtrPips { get; set; }

        [Parameter("Max Spread (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Filters")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Candle Confirmation", DefaultValue = true, Group = "Confirmation")]
        public bool UseCandleConfirmation { get; set; }

        [Parameter("Confirmation Move ATR", DefaultValue = 0.10, MinValue = 0.0, MaxValue = 2.0, Group = "Confirmation")]
        public double ConfirmationMoveAtr { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 1.50, MinValue = 0.1, MaxValue = 10.0, Group = "Confirmation")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Confirmation Mode", DefaultValue = EntryConfirmationMode.Balanced, Group = "Confirmation")]
        public EntryConfirmationMode ConfirmationMode { get; set; }

        [Parameter("Min Score Advantage", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 50.0, Group = "Confirmation")]
        public double MinScoreAdvantage { get; set; }

        [Parameter("Risk Mode", DefaultValue = RiskSizingMode.RiskPercentEquity, Group = "Risk")]
        public RiskSizingMode RiskMode { get; set; }

        [Parameter("Fixed Lots", DefaultValue = 0.01, MinValue = 0.0, Group = "Risk")]
        public double FixedLots { get; set; }

        [Parameter("Risk % Equity", DefaultValue = 1.0, MinValue = 0.01, MaxValue = 20.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Fixed Risk Cash", DefaultValue = 1.0, MinValue = 0.01, Group = "Risk")]
        public double FixedRiskCash { get; set; }

        [Parameter("SL ATR Buffer", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 5.0, Group = "Risk")]
        public double SlAtrBuffer { get; set; }

        [Parameter("Min Stop (pips)", DefaultValue = 1.0, MinValue = 0.1, Group = "Risk")]
        public double MinStopPips { get; set; }

        [Parameter("Max Stop (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Risk")]
        public double MaxStopPips { get; set; }

        [Parameter("TP Mode", DefaultValue = TakeProfitMode.Fib618AD, Group = "Risk")]
        public TakeProfitMode TpMode { get; set; }

        [Parameter("Fallback RR", DefaultValue = 1.80, MinValue = 0.5, MaxValue = 20.0, Group = "Risk")]
        public double FallbackRiskReward { get; set; }

        [Parameter("Minimum RR", DefaultValue = 1.50, MinValue = 0.2, MaxValue = 20.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, MaxValue = 20, Group = "Limits")]
        public int MaxOpenPositions { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 6, MinValue = 1, MaxValue = 100, Group = "Limits")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Daily Loss % (0=off)", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 100.0, Group = "Limits")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Cooldown Bars", DefaultValue = 3, MinValue = 0, MaxValue = 500, Group = "Limits")]
        public int CooldownBars { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }

        [Parameter("Reject Insufficient Fib Target", DefaultValue = true, Group = "Risk")]
        public bool RejectInsufficientFibTarget { get; set; }

        private readonly Dictionary<string, int> _diagnostics = new Dictionary<string, int>();
        private bool Reject(string reason)
        {
            if (!_diagnostics.ContainsKey(reason)) _diagnostics[reason] = 0;
            _diagnostics[reason]++;
            return false;
        }
        private AverageTrueRange _atr;
        private ExponentialMovingAverage _ema;
        private List<PatternDefinition> _patterns;
        private DateTime _day;
        private double _dayStartEquity;
        private int _tradesToday;
        private int _lastTradeBar = -1000000;
        private int _lastBullishDIndex = -1;
        private int _lastBearishDIndex = -1;
        private readonly HashSet<string> _consumedSignals = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<long, string> _positionPattern = new Dictionary<long, string>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);

        protected override void OnStart()
        {
            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);
            _patterns = PatternLibrary.Create();
            AddCustomPatterns(CustomPatternRatios);
            _patterns = _patterns.Where(IsPatternEnabled).ToList();
            Print("VERSION v0.3.0-fix4");
            ResetDay();
            Positions.Closed += OnPositionClosed;

            Print("FHSU started | Symbol={0} | TimeFrame={1} | Patterns={2} | Trading={3}", SymbolName, TimeFrame, _patterns.Count, TradingEnabled);
            Print("Pattern selector: CORE = canonical set, ALL = entire database, or comma separated names.");
        }

        protected override void OnBarClosed()
        {
            if (Bars.Count < Math.Max(100, PivotLeft + PivotRight + 20))
                return;

            if (Server.Time.Date != _day)
                ResetDay();

            if (!PassGlobalLimits())
            {
                Reject("global_limits");
                return;
            }

            var pivots = BuildConfirmedPivots();
            if (pivots.Count < 5)
                return;

            PatternMatch best = FindBestPattern(pivots);
            if (best == null)
            {
                Reject("no_candidate_or_conflict");
                return;
            }


            if (DebugLogging)
                Print("[PATTERN] {0} {1} score={2:F1}% D={3} ratios XB={4:F3} AC={5:F3} BD={6:F3} XD={7:F3}",
                    best.Definition.Name, best.Direction, best.Score, best.D.Price,
                    best.Xb, best.Ac, best.Bd, best.Xd);

            if (!TradingEnabled)
                return;

            ExecutePatternTrade(best);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            foreach (var item in _diagnostics) Print("[DIAG] {0}={1}", item.Key, item.Value);
            foreach (var kv in _stats.OrderBy(k => k.Key))
            {
                var s = kv.Value;
                Print("[STATS] {0}: trades={1} wins={2} losses={3} net={4:F2} winrate={5:F1}%",
                    kv.Key, s.Trades, s.Wins, s.Losses, s.NetProfit, s.Trades == 0 ? 0 : 100.0 * s.Wins / s.Trades);
            }
        }

        private void ResetDay()
        {
            _day = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _tradesToday = 0;
        }

        private bool PassGlobalLimits()
        {
            if (_tradesToday >= MaxTradesPerDay)
                return false;

            if (Bars.Count - 1 - _lastTradeBar < CooldownBars)
                return false;

            int ownOpen = 0;
            foreach (var p in Positions)
                if (p.SymbolName == SymbolName && p.Label == BotLabel)
                    ownOpen++;
            if (ownOpen >= MaxOpenPositions)
                return false;

            if (MaxDailyLossPercent > 0 && _dayStartEquity > 0)
            {
                double dd = 100.0 * (_dayStartEquity - Account.Equity) / _dayStartEquity;
                if (dd >= MaxDailyLossPercent)
                    return false;
            }

            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
                return false;

            double atrPips = _atr.Result.LastValue / Symbol.PipSize;
            if (MinAtrPips > 0 && atrPips < MinAtrPips)
                return false;

            return true;
        }

        private List<PivotPoint> BuildConfirmedPivots()
        {
            var pivots = new List<PivotPoint>();
            int latestConfirmed = Bars.Count - 1 - PivotRight;
            int first = Math.Max(PivotLeft, Bars.Count - PivotLookback);

            for (int i = first; i <= latestConfirmed; i++)
            {
                bool isHigh = true;
                bool isLow = true;

                for (int j = 1; j <= PivotLeft; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i - j]) isHigh = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i - j]) isLow = false;
                }
                for (int j = 1; j <= PivotRight; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i + j]) isHigh = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i + j]) isLow = false;
                }

                if (isHigh && !isLow)
                    AddAlternatingPivot(pivots, new PivotPoint(i, Bars.HighPrices[i], PivotKind.High));
                else if (isLow && !isHigh)
                    AddAlternatingPivot(pivots, new PivotPoint(i, Bars.LowPrices[i], PivotKind.Low));
            }

            const int maxPivots = 80;
            if (pivots.Count > maxPivots)
                pivots = pivots.GetRange(pivots.Count - maxPivots, maxPivots);
            return pivots;
        }

        private void AddAlternatingPivot(List<PivotPoint> pivots, PivotPoint next)
        {
            if (pivots.Count == 0)
            {
                pivots.Add(next);
                return;
            }

            var last = pivots[pivots.Count - 1];
            if (last.Kind != next.Kind)
            {
                pivots.Add(next);
                return;
            }

            bool replace = next.Kind == PivotKind.High ? next.Price > last.Price : next.Price < last.Price;
            if (replace)
                pivots[pivots.Count - 1] = next;
        }

        private PatternMatch FindBestPattern(List<PivotPoint> pivots)
        {
            var candidates = new List<PatternMatch>();
            int firstWindow = Math.Max(0, pivots.Count - 20);

            for (int i = firstWindow; i <= pivots.Count - 5; i++)
            {
                var x = pivots[i];
                var a = pivots[i + 1];
                var b = pivots[i + 2];
                var c = pivots[i + 3];
                var d = pivots[i + 4];

                TradeType? direction = GetDirection(x, a, b, c, d);
                if (!direction.HasValue)
                    continue;

                int age = Bars.Count - 1 - d.Index;
                if (age < 0 || age > MaxPatternAgeBars)
                    continue;

                if (direction == TradeType.Buy && d.Index == _lastBullishDIndex)
                    continue;
                if (direction == TradeType.Sell && d.Index == _lastBearishDIndex)
                    continue;

                double xa = Math.Abs(a.Price - x.Price);
                double ab = Math.Abs(b.Price - a.Price);
                double bc = Math.Abs(c.Price - b.Price);
                double cd = Math.Abs(d.Price - c.Price);
                if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0)
                    continue;

                if (MinXaPips > 0 && xa / Symbol.PipSize < MinXaPips)
                    continue;

                double xb = ab / xa;
                double ac = bc / ab;
                double bd = cd / bc;
                double xd = Math.Abs(a.Price - d.Price) / xa;
                double cdAb = cd / ab;

                foreach (var def in _patterns)
                {
                    if (!IsPatternEnabled(def))
                        continue;

                    double score = def.Score(xb, ac, bd, xd, cdAb, RatioTolerancePercent);
                    if (score < MinPatternScore)
                        continue;

                    var match = new PatternMatch(def, direction.Value, x, a, b, c, d, score, xb, ac, bd, xd, cdAb);
                    match.TrendAligned = IsTrendAligned(match.Direction);
                    match.FinalScore = Math.Min(100.0, match.Score + (EmaFilterMode != TrendFilterMode.Off && match.TrendAligned ? 5.0 : 0.0));
                    if (EmaFilterMode == TrendFilterMode.Strict && !match.TrendAligned)
                        continue;
                    if (EmaFilterMode == TrendFilterMode.ConfirmOnly && !match.TrendAligned)
                        continue;
                    if (_consumedSignals.Contains(match.SignalKey))
                        continue;
                    if (!PassConfirmation(match))
                        continue;
                    if (RejectInsufficientFibTarget && TpMode != TakeProfitMode.RiskReward)
                    {
                        double entry = match.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                        double stop = match.Direction == TradeType.Buy
                            ? match.D.Price - _atr.Result.LastValue * SlAtrBuffer
                            : match.D.Price + _atr.Result.LastValue * SlAtrBuffer;
                        double sl = (match.Direction == TradeType.Buy ? entry - stop : stop - entry) / Symbol.PipSize;
                        if (sl <= 0 || double.IsNaN(sl) || double.IsInfinity(sl))
                            continue;
                        sl = Math.Max(sl, MinStopPips);
                        double tp = CalculateTakeProfitPips(match, entry, sl);
                        if (tp < sl * MinimumRiskReward)
                        {
                            Reject("fib_target_insufficient");
                            continue;
                        }
                    }
                    candidates.Add(match);
                }
            }

            if (candidates.Count == 0)
                return null;

            var ordered = candidates.OrderByDescending(m => m.FinalScore).ThenByDescending(m => m.D.Index).ToList();
            PatternMatch best = ordered[0];
            PatternMatch opposite = ordered.FirstOrDefault(m => m.Direction != best.Direction && Math.Abs(m.D.Index - best.D.Index) <= MaxPatternAgeBars);
            if (opposite != null && best.FinalScore - opposite.FinalScore < MinScoreAdvantage)
            {
                if (DebugLogging)
                    Print("[SKIP CONFLICT] {0} {1:F1}% vs {2} {3:F1}%", best.Definition.Name, best.FinalScore, opposite.Definition.Name, opposite.FinalScore);
                return null;
            }
            return best;
        }

        private bool IsTrendAligned(TradeType direction)
        {
            int last = Bars.Count - 1;
            double close = Bars.ClosePrices[last];
            double ema = _ema.Result[last];
            bool slopeUp = ema > _ema.Result.Last(1);
            bool slopeDown = ema < _ema.Result.Last(1);
            if (direction == TradeType.Buy)
                return close > ema && (!RequireEmaSlope || slopeUp);
            return close < ema && (!RequireEmaSlope || slopeDown);
        }

        private TradeType? GetDirection(PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d)
        {
            bool bullish = x.Kind == PivotKind.Low && a.Kind == PivotKind.High && b.Kind == PivotKind.Low && c.Kind == PivotKind.High && d.Kind == PivotKind.Low;
            bool bearish = x.Kind == PivotKind.High && a.Kind == PivotKind.Low && b.Kind == PivotKind.High && c.Kind == PivotKind.Low && d.Kind == PivotKind.High;
            if (bullish) return TradeType.Buy;
            if (bearish) return TradeType.Sell;
            return null;
        }

        private bool IsPatternEnabled(PatternDefinition def)
        {
            string selector = (EnabledPatterns ?? "CORE").Trim();
            if (selector.Equals("ALL", StringComparison.OrdinalIgnoreCase))
                return true;
            if (selector.Equals("CORE", StringComparison.OrdinalIgnoreCase))
                return def.IsCore;

            string[] parts = selector.Split(new[] { ',', ';', '|' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string p in parts)
            {
                string s = p.Trim();
                if (s.Equals(def.Name, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private bool PassConfirmation(PatternMatch m)
        {
            int last = Bars.Count - 1;
            double close = Bars.ClosePrices[last];
            double open = Bars.OpenPrices[last];
            double atr = _atr.Result.LastValue;
            if (double.IsNaN(atr) || double.IsInfinity(atr) || atr <= 0)
                return Reject("confirmation_gate_1");

            // A confirmed pivot can be invalidated before its entry confirmation.
            for (int i = m.D.Index + 1; i <= last; i++)
                if ((m.Direction == TradeType.Buy && Bars.LowPrices[i] < m.D.Price) ||
                    (m.Direction == TradeType.Sell && Bars.HighPrices[i] > m.D.Price))
                    return Reject("D_invalidated");

            double distance = Math.Abs(close - m.D.Price);
            if (distance > atr * MaxEntryDistanceAtr)
                return Reject("confirmation_gate_2");

            if (ConfirmationMode == EntryConfirmationMode.Aggressive)
            {
                if ((m.Direction == TradeType.Buy && close <= m.D.Price) ||
                    (m.Direction == TradeType.Sell && close >= m.D.Price))
                    return Reject("D_side");
                return (EmaFilterMode != TrendFilterMode.Strict && EmaFilterMode != TrendFilterMode.ConfirmOnly)
                    || m.TrendAligned || Reject("EMA");
            }

            if (m.Direction == TradeType.Buy)
            {
                if (close < m.D.Price + atr * ConfirmationMoveAtr)
                    return Reject("confirmation_gate_3");
                if (UseCandleConfirmation && close <= open)
                    return Reject("confirmation_gate_4");
            }
            else
            {
                if (close > m.D.Price - atr * ConfirmationMoveAtr)
                    return Reject("confirmation_gate_5");
                if (UseCandleConfirmation && close >= open)
                    return Reject("confirmation_gate_6");
            }

            if ((EmaFilterMode == TrendFilterMode.ConfirmOnly || EmaFilterMode == TrendFilterMode.Strict) && !m.TrendAligned)
                return Reject("confirmation_gate_7");

            if (ConfirmationMode == EntryConfirmationMode.Conservative)
            {
                double previousHigh = Bars.HighPrices[last - 1];
                double previousLow = Bars.LowPrices[last - 1];
                if (m.Direction == TradeType.Buy && close <= previousHigh)
                    return Reject("confirmation_gate_8");
                if (m.Direction == TradeType.Sell && close >= previousLow)
                    return Reject("confirmation_gate_9");
            }
            return true;
        }

        private void ExecutePatternTrade(PatternMatch m)
        {
            // Respect same-symbol exposure even if another instance uses another label.
            if (Positions.Any(p => p.SymbolName == SymbolName && p.TradeType != m.Direction) ||
                PendingOrders.Any(p => p.SymbolName == SymbolName && p.TradeType != m.Direction))
            {
                Reject("opposite_exposure");
                return;
            }
            double atr = _atr.Result.LastValue;
            double entry = m.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            double slPrice = m.Direction == TradeType.Buy
                ? m.D.Price - atr * SlAtrBuffer
                : m.D.Price + atr * SlAtrBuffer;

            double stopDistance = m.Direction == TradeType.Buy ? entry - slPrice : slPrice - entry;
            if (double.IsNaN(stopDistance) || double.IsInfinity(stopDistance) || stopDistance <= 0)
            {
                Reject("invalid_stop_side");
                return;
            }
            double slPips = stopDistance / Symbol.PipSize;
            if (slPips < MinStopPips)
                slPips = MinStopPips;
            if (MaxStopPips > 0 && slPips > MaxStopPips)
            {
                if (DebugLogging)
                    Print("[SKIP] Stop {0:F1}p exceeds maximum {1:F1}p.", slPips, MaxStopPips);
                return;
            }

            double tpPips = CalculateTakeProfitPips(m, entry, slPips);
            if (tpPips < slPips * MinimumRiskReward)
            {
                if (RejectInsufficientFibTarget && TpMode != TakeProfitMode.RiskReward)
                {
                    Reject("fib_target_insufficient");
                    return;
                }
                tpPips = slPips * FallbackRiskReward;
            }
            if (tpPips < slPips * MinimumRiskReward)
                return;

            double volume = CalculateVolume(slPips);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Reject("volume_below_min");
                if (DebugLogging)
                    Print("[SKIP] Calculated volume {0} is below minimum {1}.", volume, Symbol.VolumeInUnitsMin);
                return;
            }

            var result = ExecuteMarketOrder(m.Direction, SymbolName, volume, BotLabel, slPips, tpPips, m.Definition.Name, false);
            if (!result.IsSuccessful)
            {
                Print("[ORDER FAIL] {0} {1} error={2}", m.Definition.Name, m.Direction, result.Error);
                return;
            }

            if (result.Position == null || !result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[PROTECTION FAIL] Position opened without complete SL/TP; closing immediately.");
                if (result.Position != null)
                    ClosePosition(result.Position);
                return;
            }

            _tradesToday++;
            _lastTradeBar = Bars.Count - 1;
            if (m.Direction == TradeType.Buy) _lastBullishDIndex = m.D.Index;
            else _lastBearishDIndex = m.D.Index;
            _consumedSignals.Add(m.SignalKey);

            _positionPattern[result.Position.Id] = m.Definition.Name;
            if (!_stats.ContainsKey(m.Definition.Name))
                _stats[m.Definition.Name] = new PatternStats();
            _stats[m.Definition.Name].Trades++;

            Print("[OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",
                m.Definition.Name, m.Direction, m.Score, volume, slPips, tpPips, tpPips / slPips);
        }

        private double CalculateVolume(double slPips)
        {
            double raw;
            if (RiskMode == RiskSizingMode.FixedLots)
            {
                raw = Symbol.QuantityToVolumeInUnits(FixedLots);
            }
            else
            {
                double amount = RiskMode == RiskSizingMode.FixedRiskCash
                    ? FixedRiskCash
                    : Account.Equity * RiskPercent / 100.0;
                raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            }

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;

            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            if (RiskMode != RiskSizingMode.FixedLots)
            {
                double budget = RiskMode == RiskSizingMode.FixedRiskCash ? FixedRiskCash : Account.Equity * RiskPercent / 100.0;
                double estimated = Symbol.AmountRisked(raw, slPips);
                if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + 1e-8)
                {
                    Reject("risk_budget_exceeded");
                    Print("[RISK REJECT] volume={0} estimated={1:F4} budget={2:F4} min={3} pipValue={4}", raw, estimated, budget, Symbol.VolumeInUnitsMin, Symbol.PipValue);
                    return 0;
                }
            }
            return raw;
        }

        private double CalculateTakeProfitPips(PatternMatch m, double entry, double slPips)
        {
            if (TpMode == TakeProfitMode.RiskReward)
                return slPips * FallbackRiskReward;

            double target;
            if (TpMode == TakeProfitMode.PointC)
                target = m.C.Price;
            else if (TpMode == TakeProfitMode.PointA)
                target = m.A.Price;
            else
            {
                double ad = Math.Abs(m.A.Price - m.D.Price);
                double fib = TpMode == TakeProfitMode.Fib382AD ? 0.382 : 0.618;
                target = m.Direction == TradeType.Buy ? m.D.Price + ad * fib : m.D.Price - ad * fib;
            }

            double distance = m.Direction == TradeType.Buy ? target - entry : entry - target;
            if (distance <= 0)
                return RejectInsufficientFibTarget ? 0 : slPips * FallbackRiskReward;
            return distance / Symbol.PipSize;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p.Label != BotLabel || p.SymbolName != SymbolName)
                return;

            string name;
            if (!_positionPattern.TryGetValue(p.Id, out name))
                name = string.IsNullOrWhiteSpace(p.Comment) ? "Unknown" : p.Comment;

            if (!_stats.ContainsKey(name))
                _stats[name] = new PatternStats();
            var s = _stats[name];
            s.NetProfit += p.NetProfit;
            if (p.NetProfit > 0) s.Wins++;
            else if (p.NetProfit < 0) s.Losses++;
            _positionPattern.Remove(p.Id);

            if (DebugLogging)
                Print("[CLOSE] {0} net={1:F2} reason={2}", name, p.NetProfit, args.Reason);
        }

        private void AddCustomPatterns(string text)
        {
            if (string.IsNullOrWhiteSpace(text))
                return;

            // Format: Name|xbMin|xbMax|acMin|acMax|bdMin|bdMax|xdMin|xdMax ; next pattern ...
            string[] records = text.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string record in records)
            {
                string[] f = record.Split('|');
                if (f.Length != 9)
                    continue;

                double xb1, xb2, ac1, ac2, bd1, bd2, xd1, xd2;
                if (!double.TryParse(f[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out xb1) ||
                    !double.TryParse(f[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out xb2) ||
                    !double.TryParse(f[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out ac1) ||
                    !double.TryParse(f[4], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out ac2) ||
                    !double.TryParse(f[5], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out bd1) ||
                    !double.TryParse(f[6], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out bd2) ||
                    !double.TryParse(f[7], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out xd1) ||
                    !double.TryParse(f[8], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out xd2))
                    continue;

                _patterns.Add(new PatternDefinition(f[0].Trim(), xb1, xb2, ac1, ac2, bd1, bd2, xd1, xd2, false));
            }
        }

        public enum RiskSizingMode
        {
            FixedLots,
            RiskPercentEquity,
            FixedRiskCash
        }

        public enum TakeProfitMode
        {
            RiskReward,
            Fib382AD,
            Fib618AD,
            PointC,
            PointA
        }

        public enum EntryConfirmationMode
        {
            Aggressive,
            Balanced,
            Conservative
        }

        public enum TrendFilterMode
        {
            Off,
            ScoreOnly,
            ConfirmOnly,
            Strict
        }

        private enum PivotKind { High, Low }

        private sealed class PivotPoint
        {
            public PivotPoint(int index, double price, PivotKind kind) { Index = index; Price = price; Kind = kind; }
            public int Index { get; private set; }
            public double Price { get; private set; }
            public PivotKind Kind { get; private set; }
        }

        private sealed class PatternMatch
        {
            public PatternMatch(PatternDefinition definition, TradeType direction, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
                double score, double xb, double ac, double bd, double xd, double cdAb)
            {
                Definition = definition; Direction = direction; X = x; A = a; B = b; C = c; D = d;
                Score = score; Xb = xb; Ac = ac; Bd = bd; Xd = xd; CdAb = cdAb;
                FinalScore = score;
            }
            public PatternDefinition Definition { get; private set; }
            public TradeType Direction { get; private set; }
            public PivotPoint X { get; private set; }
            public PivotPoint A { get; private set; }
            public PivotPoint B { get; private set; }
            public PivotPoint C { get; private set; }
            public PivotPoint D { get; private set; }
            public double Score { get; private set; }
            public double Xb { get; private set; }
            public double Ac { get; private set; }
            public double Bd { get; private set; }
            public double Xd { get; private set; }
            public double CdAb { get; private set; }
            public bool TrendAligned { get; set; }
            public double FinalScore { get; set; }
            public string SignalKey { get { return Definition.Name + "|" + Direction + "|" + D.Index; } }
        }

        private sealed class PatternStats
        {
            public int Trades;
            public int Wins;
            public int Losses;
            public double NetProfit;
        }

        private sealed class PatternDefinition
        {
            public PatternDefinition(string name, double xbMin, double xbMax, double acMin, double acMax,
                double bdMin, double bdMax, double xdMin, double xdMax, bool isCore,
                double cdAbMin = 0.0, double cdAbMax = 0.0)
            {
                Name = name; XbMin = xbMin; XbMax = xbMax; AcMin = acMin; AcMax = acMax;
                BdMin = bdMin; BdMax = bdMax; XdMin = xdMin; XdMax = xdMax; IsCore = isCore;
                CdAbMin = cdAbMin; CdAbMax = cdAbMax;
            }

            public string Name { get; private set; }
            public double XbMin { get; private set; }
            public double XbMax { get; private set; }
            public double AcMin { get; private set; }
            public double AcMax { get; private set; }
            public double BdMin { get; private set; }
            public double BdMax { get; private set; }
            public double XdMin { get; private set; }
            public double XdMax { get; private set; }
            public double CdAbMin { get; private set; }
            public double CdAbMax { get; private set; }
            public bool IsCore { get; private set; }

            public double Score(double xb, double ac, double bd, double xd, double cdAb, double tolerancePercent)
            {
                var scores = new List<double>
                {
                    ScoreRule(xb, XbMin, XbMax, tolerancePercent),
                    ScoreRule(ac, AcMin, AcMax, tolerancePercent),
                    ScoreRule(bd, BdMin, BdMax, tolerancePercent),
                    ScoreRule(xd, XdMin, XdMax, tolerancePercent)
                };
                if (CdAbMin > 0 && CdAbMax > 0)
                    scores.Add(ScoreRule(cdAb, CdAbMin, CdAbMax, tolerancePercent));
                if (scores.Any(v => v <= 0))
                    return 0;
                return scores.Average();
            }

            private static double ScoreRule(double value, double min, double max, double tolPct)
            {
                if (min <= 0 && max <= 0)
                    return 100;
                if (max < min)
                {
                    double t = min; min = max; max = t;
                }

                if (Math.Abs(max - min) < 1e-12)
                {
                    double target = min;
                    double allowed = Math.Max(target * tolPct / 100.0, 1e-9);
                    double error = Math.Abs(value - target);
                    if (error > allowed) return 0;
                    return 100.0 * (1.0 - error / allowed);
                }

                if (value >= min && value <= max)
                    return 100;

                double lowerTol = Math.Max(min * tolPct / 100.0, 1e-9);
                double upperTol = Math.Max(max * tolPct / 100.0, 1e-9);
                if (value < min)
                {
                    double d = min - value;
                    if (d > lowerTol) return 0;
                    return 100.0 * (1.0 - d / lowerTol);
                }
                else
                {
                    double d = value - max;
                    if (d > upperTol) return 0;
                    return 100.0 * (1.0 - d / upperTol);
                }
            }
        }

        private static class PatternLibrary
        {
            public static List<PatternDefinition> Create()
            {
                var p = new List<PatternDefinition>();
                Action<string,double,double,double,double,double,double,double,double,bool> add =
                    (n,xb1,xb2,ac1,ac2,bd1,bd2,xd1,xd2,core) => p.Add(new PatternDefinition(n,xb1,xb2,ac1,ac2,bd1,bd2,xd1,xd2,core));

                // Canonical / commonly used families
                add("Gartley",0.618,0.618,0.382,0.886,1.272,1.618,0.786,0.786,true);
                add("Bat",0.382,0.500,0.382,0.886,1.618,2.618,0.886,0.886,true);
                add("Alt Bat",0.382,0.382,0.382,0.886,2.000,3.618,1.128,1.128,true);
                add("Butterfly",0.786,0.786,0.382,0.886,1.618,2.618,1.272,1.618,true);
                add("Crab",0.382,0.618,0.382,0.886,2.240,3.618,1.618,1.618,true);
                add("Deep Crab",0.886,0.886,0.382,0.886,2.618,3.618,1.618,1.618,true);
                add("Shark 1",0.382,0.618,1.128,1.618,1.618,2.236,0.886,0.886,true);
                add("Shark 2",0.382,0.618,1.128,1.618,1.618,2.236,1.128,1.128,true);
                add("New Cypher",0.382,0.618,1.414,2.140,1.272,2.000,0.786,0.786,true);
                add("Nen Star",0.382,0.618,1.414,2.140,1.272,2.000,1.272,1.272,true);
                add("5-0",1.128,1.618,1.500,2.236,0.500,0.618,0.400,0.618,true);
                add("3 Drives",1.272,1.618,0.618,0.786,1.272,1.618,1.618,2.618,true);
                p.Add(new PatternDefinition("ABCD",0.128,3.618,0.382,0.886,1.128,2.618,0.128,7.618,true,0.95,1.05));
                p.Add(new PatternDefinition("Reciprocal ABCD",0.128,3.618,0.382,0.886,0.382,0.886,0.128,7.618,true,0.618,1.618));

                // Extended / Max / Swan / 121 / community database
                add("Max Bat",0.382,0.618,0.382,0.886,1.272,2.618,0.886,0.886,false);
                add("Max Gartley",0.382,0.618,0.382,0.886,1.128,2.236,0.618,0.786,false);
                add("Max Butterfly",0.618,0.886,0.382,0.886,1.272,2.618,1.272,1.618,false);
                add("Butterfly 113",0.786,1.000,0.618,1.000,1.128,1.618,1.128,1.128,false);
                add("Alt Shark 1",0.446,0.618,0.618,0.886,1.618,2.618,1.128,1.128,false);
                add("Alt Shark 2",0.446,0.618,0.618,0.886,1.618,2.618,0.886,0.886,false);
                add("Leonardo",0.500,0.500,0.382,0.886,1.128,2.618,0.786,0.786,false);
                add("Navarro 200",0.382,0.786,0.886,1.128,0.886,3.618,0.886,1.128,false);
                add("121",0.500,0.786,1.128,3.618,0.382,0.786,0.382,0.786,false);
                add("White Swan",0.382,0.786,2.000,4.237,0.500,0.886,0.238,0.886,false);
                add("Black Swan",1.382,2.618,0.236,0.500,1.128,2.000,1.128,2.618,false);
                add("Sea Pony",0.128,3.618,0.382,0.500,1.618,2.618,0.618,3.618,false);
                add("Partizan",0.128,3.618,0.382,0.382,1.618,1.618,0.618,3.618,false);
                add("Partizan 2",0.128,3.618,1.128,1.618,1.618,2.236,0.618,3.618,false);
                add("Partizan 2.1",0.128,3.618,1.128,1.128,1.618,1.618,0.618,3.618,false);
                add("Partizan 2.2",0.128,3.618,1.128,1.128,2.236,2.236,0.618,3.618,false);
                add("Partizan 2.3",0.128,3.618,0.618,1.618,1.618,1.618,0.618,3.618,false);
                add("Partizan 2.4",0.128,3.618,1.618,1.618,2.236,2.236,0.618,3.618,false);
                add("Henry-David",0.128,2.000,0.440,0.618,0.618,0.886,0.618,1.618,false);
                add("Strong Henry-David",0.128,2.618,0.440,0.618,0.618,0.886,0.618,1.618,false);
                add("David VM1",0.128,1.618,0.382,0.382,1.618,1.618,0.618,3.618,false);
                add("David VM2",1.618,3.618,0.382,0.382,1.618,1.618,0.618,7.618,false);
                add("SNORM",0.900,1.100,0.900,1.100,0.900,1.100,0.618,1.618,false);
                add("Poruchik",0.128,3.618,0.382,2.618,1.000,1.000,0.618,3.618,false);
                add("Kane",0.685,0.685,0.382,0.886,0.0,0.0,1.460,1.460,false);
                add("Garfly",0.618,0.618,0.382,0.886,1.618,2.240,1.272,1.272,false);
                add("May-00",1.128,1.618,1.618,2.236,0.500,0.618,0.500,0.618,false);

                add("Total 1",0.382,0.786,0.382,0.886,1.272,2.618,0.786,0.886,false);
                add("Total 2",0.382,0.786,0.382,0.886,1.618,3.618,1.128,1.618,false);
                add("Total 3",0.276,0.618,1.128,2.618,1.272,2.618,0.618,0.886,false);
                add("Total 4",0.382,0.786,1.128,2.618,1.618,2.618,1.128,1.272,false);
                add("Total",0.276,0.786,0.382,2.618,1.272,3.618,0.618,1.618,false);

                // Anti families
                add("Anti Gartley",0.618,0.786,1.128,2.618,1.618,1.618,1.272,1.272,false);
                add("Anti Bat",0.382,0.618,1.128,2.618,2.000,2.618,1.128,1.128,false);
                add("Anti Alt Bat",0.236,0.500,1.128,2.618,2.618,2.618,0.886,0.886,false);
                add("Anti Butterfly",0.382,0.618,1.128,2.618,1.272,1.272,0.618,0.786,false);
                add("Anti Crab",0.276,0.446,1.128,2.618,1.618,2.618,0.618,0.618,false);
                add("Anti Deep Crab",0.236,0.382,1.128,2.618,1.128,1.128,0.618,0.618,false);
                add("Anti New Cypher",0.500,0.786,0.467,0.707,1.618,2.618,1.272,1.272,false);
                add("Anti Nen Star",0.500,0.786,0.467,0.707,1.618,2.618,0.786,0.786,false);
                add("Anti 3 Drives",0.618,0.786,1.272,1.618,0.618,0.786,0.130,0.886,false);
                add("Anti 121",1.272,2.000,0.500,0.786,1.272,2.000,1.272,2.618,false);

                // BG / NN ratio families often found in large harmonic databases
                add("BG1",0.128,0.886,0.618,0.618,1.618,1.618,1.000,1.000,false);
                add("BG2",0.128,0.886,0.707,0.707,1.414,1.414,1.000,1.000,false);
                add("BG3",0.128,0.886,0.786,0.786,1.272,1.272,1.000,1.000,false);
                add("BG4",0.128,0.886,0.886,0.886,1.128,1.128,1.000,1.000,false);
                add("BG5",0.128,0.886,0.500,0.500,2.000,2.000,1.000,1.000,false);
                add("BG6",0.128,0.886,0.382,0.382,2.618,2.618,1.000,1.000,false);
                add("BG7",0.128,0.886,0.854,0.854,1.171,1.171,1.000,1.000,false);
                add("BG8",0.128,0.886,0.886,0.886,1.128,1.128,1.000,1.000,false);
                add("121 BG",0.500,0.577,1.128,1.733,0.618,0.707,0.447,0.786,false);

                add("NN Gartley",0.618,0.618,0.382,0.886,1.128,1.618,0.786,0.786,false);
                add("NN Bat",0.382,0.500,0.382,0.886,1.618,2.618,0.886,0.886,false);
                add("NN Alt Bat",0.382,0.382,0.382,0.886,2.000,4.236,1.128,1.128,false);
                add("NN Crab",0.382,0.618,0.382,0.886,2.236,4.236,1.618,1.618,false);
                add("NN Deep Crab",0.886,0.886,0.382,0.886,2.618,4.236,1.618,1.618,false);
                add("NN Anti Gartley",0.618,0.786,1.128,2.618,1.618,1.618,1.272,1.272,false);
                add("NN Anti Bat",0.382,0.618,1.128,2.618,2.000,2.618,1.128,1.128,false);
                add("NN Anti Alt Bat",0.236,0.500,1.128,2.618,2.618,2.618,0.886,0.886,false);
                add("NN Anti Butterfly",0.382,0.618,1.128,2.618,1.272,1.272,0.618,0.786,false);
                add("NN Anti Crab",0.236,0.447,1.128,2.618,1.128,2.618,0.618,0.618,false);
                add("NN Anti Deep Crab",0.236,0.382,1.128,2.618,1.128,1.128,0.618,0.618,false);
                add("NN Leo",0.500,0.500,0.382,0.886,1.128,2.618,0.786,0.786,false);
                add("NN Anti Leo",0.382,0.886,1.128,2.618,2.000,2.000,1.272,1.272,false);
                add("NN Total 1",0.382,0.786,0.382,0.886,1.272,2.618,0.786,0.886,false);
                add("NN Total 2",0.382,0.786,0.382,0.886,1.618,4.236,1.128,1.618,false);
                add("NN Total 3",0.236,0.618,1.128,2.618,1.272,2.618,0.618,0.886,false);
                add("NN Total 4",0.382,0.786,1.128,2.618,1.618,2.618,1.128,1.272,false);
                add("NN Total",0.236,0.786,0.382,2.618,1.272,4.236,0.618,1.618,false);
                add("NN Black Swan",1.382,2.618,0.236,0.500,1.128,2.000,1.128,2.618,false);
                add("NN White Swan",0.382,0.724,2.000,4.236,0.500,0.886,0.382,0.886,false);

                return p;
            }
        }
    }
}

