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

        [Parameter("Bot Label", DefaultValue = "FHSU-RC1", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Require XAU Symbol", DefaultValue = true, Group = "General")]
        public bool RequireXauSymbol { get; set; }

        [Parameter("Min Recommended Balance", DefaultValue = 3000.0, MinValue = 0.0, Group = "General")]
        public double MinRecommendedBalance { get; set; }

        [Parameter("Enabled Patterns", DefaultValue = "CORE", Group = "Patterns")]
        public string EnabledPatterns { get; set; }

        [Parameter("Min Pattern Score %", DefaultValue = 88.0, MinValue = 60.0, MaxValue = 100.0, Group = "Patterns")]
        public double MinPatternScore { get; set; }

        [Parameter("Ratio Tolerance %", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 20.0, Group = "Patterns")]
        public double RatioTolerancePercent { get; set; }

        [Parameter("Pivot Left Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]
        public int PivotRight { get; set; }

        [Parameter("Seed Lookback Bars", DefaultValue = 800, MinValue = 100, MaxValue = 5000, Group = "Pivots")]
        public int SeedLookbackBars { get; set; }

        [Parameter("Max Pattern Age Bars", DefaultValue = 10, MinValue = 1, MaxValue = 100, Group = "Pivots")]
        public int MaxPatternAgeBars { get; set; }

        [Parameter("Min XA Size (pips)", DefaultValue = 0.0, MinValue = 0.0, Group = "Pivots")]
        public double MinXaPips { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 2, MaxValue = 200, Group = "Regime")]
        public int AtrPeriod { get; set; }

        [Parameter("Regime Time Frame", DefaultValue = "Hour", Group = "Regime")]
        public TimeFrame RegimeTimeFrame { get; set; }

        [Parameter("Regime EMA Period", DefaultValue = 50, MinValue = 5, MaxValue = 500, Group = "Regime")]
        public int RegimeEmaPeriod { get; set; }

        [Parameter("Regime Filter", DefaultValue = RegimeFilterMode.ScoreOnly, Group = "Regime")]
        public RegimeFilterMode RegimeFilter { get; set; }

        [Parameter("Require Regime EMA Slope", DefaultValue = true, Group = "Regime")]
        public bool RequireRegimeSlope { get; set; }

        [Parameter("Trend Score Bonus", DefaultValue = 4.0, MinValue = 0.0, MaxValue = 20.0, Group = "Regime")]
        public double TrendScoreBonus { get; set; }

        [Parameter("Min ATR / Price % (0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Regime")]
        public double MinAtrPricePercent { get; set; }

        [Parameter("Max ATR / Price % (0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Regime")]
        public double MaxAtrPricePercent { get; set; }

        [Parameter("Max Spread / ATR", DefaultValue = 0.15, MinValue = 0.0, MaxValue = 1.0, Group = "Execution")]
        public double MaxSpreadAtrFraction { get; set; }

        [Parameter("Use UTC Session", DefaultValue = true, Group = "Session")]
        public bool UseUtcSession { get; set; }

        [Parameter("Session Start Hour", DefaultValue = 6, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int SessionStartHour { get; set; }

        [Parameter("Session End Hour", DefaultValue = 20, MinValue = 0, MaxValue = 24, Group = "Session")]
        public int SessionEndHour { get; set; }

        [Parameter("Friday Stop Hour", DefaultValue = 18, MinValue = 0, MaxValue = 24, Group = "Session")]
        public int FridayStopHour { get; set; }

        [Parameter("Candle Confirmation", DefaultValue = true, Group = "Entry")]
        public bool UseCandleConfirmation { get; set; }

        [Parameter("Confirmation Move ATR", DefaultValue = 0.08, MinValue = 0.0, MaxValue = 2.0, Group = "Entry")]
        public double ConfirmationMoveAtr { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 0.90, MinValue = 0.1, MaxValue = 10.0, Group = "Entry")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Min Opposite Score Advantage", DefaultValue = 4.0, MinValue = 0.0, MaxValue = 30.0, Group = "Entry")]
        public double MinOppositeScoreAdvantage { get; set; }

        [Parameter("Risk Mode", DefaultValue = RiskSizingMode.RiskPercentEquity, Group = "Risk")]
        public RiskSizingMode RiskMode { get; set; }

        [Parameter("Base Risk % Equity", DefaultValue = 0.75, MinValue = 0.05, MaxValue = 5.0, Group = "Risk")]
        public double BaseRiskPercent { get; set; }

        [Parameter("High Quality Risk %", DefaultValue = 1.00, MinValue = 0.05, MaxValue = 5.0, Group = "Risk")]
        public double HighQualityRiskPercent { get; set; }

        [Parameter("High Quality Score", DefaultValue = 94.0, MinValue = 70.0, MaxValue = 100.0, Group = "Risk")]
        public double HighQualityScore { get; set; }

        [Parameter("Fixed Risk Cash", DefaultValue = 20.0, MinValue = 0.01, Group = "Risk")]
        public double FixedRiskCash { get; set; }

        [Parameter("Fixed Lots", DefaultValue = 0.01, MinValue = 0.0, Group = "Risk")]
        public double FixedLots { get; set; }

        [Parameter("SL ATR Buffer", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 5.0, Group = "Risk")]
        public double SlAtrBuffer { get; set; }

        [Parameter("Min Stop (pips)", DefaultValue = 1.0, MinValue = 0.1, Group = "Risk")]
        public double MinStopPips { get; set; }

        [Parameter("Max Stop (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Risk")]
        public double MaxStopPips { get; set; }

        [Parameter("Take Profit Mode", DefaultValue = TakeProfitMode.AdaptiveFib, Group = "Exit")]
        public TakeProfitMode TpMode { get; set; }

        [Parameter("Minimum Net RR", DefaultValue = 1.50, MinValue = 0.5, MaxValue = 10.0, Group = "Exit")]
        public double MinimumNetRiskReward { get; set; }

        [Parameter("Fallback RR", DefaultValue = 1.80, MinValue = 0.5, MaxValue = 10.0, Group = "Exit")]
        public double FallbackRiskReward { get; set; }

        [Parameter("Runner Score", DefaultValue = 94.0, MinValue = 70.0, MaxValue = 100.0, Group = "Exit")]
        public double RunnerScore { get; set; }

        [Parameter("Execution Cost Reserve (pips)", DefaultValue = 40.0, MinValue = 0.0, Group = "Execution")]
        public double ExecutionCostReservePips { get; set; }

        [Parameter("Enable Break Even", DefaultValue = true, Group = "Exit")]
        public bool EnableBreakEven { get; set; }

        [Parameter("Break Even Trigger R", DefaultValue = 1.00, MinValue = 0.5, MaxValue = 5.0, Group = "Exit")]
        public double BreakEvenTriggerR { get; set; }

        [Parameter("Break Even Offset (pips)", DefaultValue = 2.0, MinValue = 0.0, Group = "Exit")]
        public double BreakEvenOffsetPips { get; set; }

        [Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, MaxValue = 5, Group = "Limits")]
        public int MaxOpenPositions { get; set; }

        [Parameter("Block Any Same-Symbol Exposure", DefaultValue = true, Group = "Limits")]
        public bool BlockAnySameSymbolExposure { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 3, MinValue = 1, MaxValue = 20, Group = "Limits")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Daily Drawdown %", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 20.0, Group = "Limits")]
        public double MaxDailyDrawdownPercent { get; set; }

        [Parameter("Runtime Peak Drawdown %", DefaultValue = 12.0, MinValue = 0.0, MaxValue = 50.0, Group = "Limits")]
        public double MaxRuntimePeakDrawdownPercent { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 3, MinValue = 0, MaxValue = 20, Group = "Limits")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Cooldown Bars", DefaultValue = 4, MinValue = 0, MaxValue = 100, Group = "Limits")]
        public int CooldownBars { get; set; }

        [Parameter("Debug Logging", DefaultValue = false, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }

        private AverageTrueRange _atr;
        private Bars _regimeBars;
        private ExponentialMovingAverage _regimeEma;
        private IncrementalPivotEngine _pivotEngine;
        private HarmonicPatternEngine _patternEngine;
        private DateTime _day;
        private double _dayStartBalanceEstimate;
        private double _runtimePeakEquity;
        private int _tradesToday;
        private int _consecutiveLosses;
        private int _lastTradeBar = -1000000;

        private readonly HashSet<string> _consumedSignals = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<int, double> _positionInitialRiskPips = new Dictionary<int, double>();
        private readonly Dictionary<int, string> _positionPattern = new Dictionary<int, string>();
        private readonly Dictionary<int, int> _breakEvenAttemptBar = new Dictionary<int, int>();
        private readonly HashSet<int> _breakEvenDone = new HashSet<int>();
        private readonly Dictionary<string, int> _diagnostics = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);

        protected override void OnStart()
        {
            Print("VERSION v0.4.0-store-rc1");

            if (RequireXauSymbol && SymbolName.IndexOf("XAU", StringComparison.OrdinalIgnoreCase) < 0)
            {
                Print("[STOP] This release candidate is designed for XAU symbols. Current symbol={0}", SymbolName);
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);
            _regimeBars = MarketData.GetBars(RegimeTimeFrame, SymbolName);
            _regimeEma = Indicators.ExponentialMovingAverage(_regimeBars.ClosePrices, RegimeEmaPeriod);
            _pivotEngine = new IncrementalPivotEngine(Bars, PivotLeft, PivotRight, SeedLookbackBars, 120);
            _pivotEngine.Seed();
            _patternEngine = new HarmonicPatternEngine();
            _runtimePeakEquity = Account.Equity;
            RebuildDailyState();
            RehydrateOpenPositions();

            Positions.Closed += OnPositionClosed;

            if (MinRecommendedBalance > 0 && Account.Balance < MinRecommendedBalance)
                Print("[BALANCE WARNING] Balance={0:F2}; research recommendation={1:F2}. Risk sizing will still reject trades that exceed budget.", Account.Balance, MinRecommendedBalance);

            Print("FHSU Store RC1 started | Symbol={0} TF={1} RegimeTF={2} Trading={3}", SymbolName, TimeFrame, RegimeTimeFrame, TradingEnabled);
        }

        protected override void OnBarClosed()
        {
            if (_pivotEngine == null || Bars.Count < Math.Max(100, PivotLeft + PivotRight + 20))
                return;

            _pivotEngine.Update();
            UpdateRuntimePeak();

            if (Server.Time.Date != _day)
                RebuildDailyState();

            if (!PassGlobalLimits())
                return;

            List<PatternMatch> raw = _patternEngine.FindCandidates(
                _pivotEngine.Pivots,
                Bars.Count,
                MaxPatternAgeBars,
                EnabledPatterns,
                MinPatternScore,
                RatioTolerancePercent,
                10);

            if (raw.Count == 0)
            {
                Reject("no_pattern");
                return;
            }

            var eligible = new List<TradePlan>();
            foreach (var match in raw)
            {
                if (_consumedSignals.Contains(match.SignalKey))
                    continue;

                if (!PassMinimumXa(match))
                    continue;

                match.TrendAligned = IsRegimeAligned(match.Direction);
                if (RegimeFilter == RegimeFilterMode.Strict && !match.TrendAligned)
                {
                    Reject("regime_mismatch");
                    continue;
                }

                match.FinalScore = Math.Min(100.0, match.BaseScore + (match.TrendAligned ? TrendScoreBonus : 0.0));

                if (!PassEntryConfirmation(match))
                    continue;

                TradePlan plan;
                if (!TryBuildTradePlan(match, out plan))
                    continue;

                eligible.Add(plan);
            }

            if (eligible.Count == 0)
            {
                Reject("no_eligible_plan");
                return;
            }

            var ordered = eligible.OrderByDescending(x => x.Match.FinalScore).ThenByDescending(x => x.Match.D.Index).ToList();
            TradePlan best = ordered[0];
            TradePlan opposite = ordered.FirstOrDefault(x => x.Match.Direction != best.Match.Direction && Math.Abs(x.Match.D.Index - best.Match.D.Index) <= MaxPatternAgeBars);
            if (opposite != null && best.Match.FinalScore - opposite.Match.FinalScore < MinOppositeScoreAdvantage)
            {
                Reject("opposite_conflict");
                if (DebugLogging)
                    Print("[SKIP CONFLICT] {0} {1:F1} vs {2} {3:F1}", best.Match.Definition.Name, best.Match.FinalScore, opposite.Match.Definition.Name, opposite.Match.FinalScore);
                return;
            }

            if (DebugLogging)
                Print("[PLAN] {0} {1} base={2:F1} final={3:F1} trend={4} SL={5:F1} TP={6:F1} netRR={7:F2}",
                    best.Match.Definition.Name, best.Match.Direction, best.Match.BaseScore, best.Match.FinalScore, best.Match.TrendAligned,
                    best.StopPips, best.TakeProfitPips, best.NetRiskReward);

            if (!TradingEnabled)
                return;

            ExecuteTrade(best);
        }

        protected override void OnTick()
        {
            UpdateRuntimePeak();
            ManageBreakEven();
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            foreach (var kv in _diagnostics.OrderBy(x => x.Key))
                Print("[DIAG] {0}={1}", kv.Key, kv.Value);

            foreach (var kv in _stats.OrderBy(x => x.Key))
            {
                PatternStats s = kv.Value;
                Print("[STATS] {0}: trades={1} wins={2} losses={3} net={4:F2} winrate={5:F1}%",
                    kv.Key, s.Trades, s.Wins, s.Losses, s.NetProfit, s.Trades == 0 ? 0 : 100.0 * s.Wins / s.Trades);
            }
        }

        private void RebuildDailyState()
        {
            _day = Server.Time.Date;
            var todayAll = History.Where(x => x.ClosingTime.Date == _day).ToArray();
            double todayNet = todayAll.Sum(x => x.NetProfit);
            _dayStartBalanceEstimate = Math.Max(0.01, Account.Balance - todayNet);

            var own = todayAll
                .Where(x => x.Label == BotLabel && x.SymbolName == SymbolName)
                .OrderBy(x => x.ClosingTime)
                .ToArray();

            _tradesToday = own.Select(x => x.PositionId).Distinct().Count();
            _consecutiveLosses = 0;
            for (int i = own.Length - 1; i >= 0; i--)
            {
                if (own[i].NetProfit < 0)
                    _consecutiveLosses++;
                else if (own[i].NetProfit > 0)
                    break;
            }

            var last = History.FindLast(BotLabel, SymbolName);
            if (last != null)
            {
                int index = Bars.OpenTimes.GetIndexByTime(last.EntryTime);
                if (index >= 0)
                    _lastTradeBar = index;
            }

            Print("[DAY] {0:yyyy-MM-dd} startBalance~{1:F2} trades={2} lossStreak={3}", _day, _dayStartBalanceEstimate, _tradesToday, _consecutiveLosses);
        }

        private void RehydrateOpenPositions()
        {
            foreach (var p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (p.StopLoss.HasValue)
                {
                    double risk = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Symbol.PipSize;
                    if (risk > 0)
                        _positionInitialRiskPips[p.Id] = risk;
                }
                _positionPattern[p.Id] = string.IsNullOrWhiteSpace(p.Comment) ? "Recovered" : p.Comment;
            }
        }

        private bool PassGlobalLimits()
        {
            if (_tradesToday >= MaxTradesPerDay)
                return Reject("max_trades_day");

            if (MaxConsecutiveLosses > 0 && _consecutiveLosses >= MaxConsecutiveLosses)
                return Reject("loss_streak_halt");

            if (Bars.Count - 1 - _lastTradeBar < CooldownBars)
                return Reject("cooldown");

            if (!PassSession())
                return Reject("session");

            int ownOpen = Positions.FindAll(BotLabel, SymbolName).Length;
            if (ownOpen >= MaxOpenPositions)
                return Reject("max_positions");

            if (BlockAnySameSymbolExposure)
            {
                if (Positions.Any(p => p.SymbolName == SymbolName) || PendingOrders.Any(p => p.SymbolName == SymbolName))
                    return Reject("same_symbol_exposure");
            }

            if (MaxDailyDrawdownPercent > 0 && _dayStartBalanceEstimate > 0)
            {
                double dd = 100.0 * (_dayStartBalanceEstimate - Account.Equity) / _dayStartBalanceEstimate;
                if (dd >= MaxDailyDrawdownPercent)
                    return Reject("daily_drawdown");
            }

            if (MaxRuntimePeakDrawdownPercent > 0 && _runtimePeakEquity > 0)
            {
                double dd = 100.0 * (_runtimePeakEquity - Account.Equity) / _runtimePeakEquity;
                if (dd >= MaxRuntimePeakDrawdownPercent)
                    return Reject("runtime_peak_drawdown");
            }

            double atr = _atr.Result.LastValue;
            if (double.IsNaN(atr) || double.IsInfinity(atr) || atr <= 0)
                return Reject("invalid_atr");

            double spread = Symbol.Ask - Symbol.Bid;
            if (MaxSpreadAtrFraction > 0 && spread / atr > MaxSpreadAtrFraction)
                return Reject("spread_atr");

            double price = Math.Max(Symbol.Bid, Symbol.PipSize);
            double atrPct = 100.0 * atr / price;
            if (MinAtrPricePercent > 0 && atrPct < MinAtrPricePercent)
                return Reject("atr_too_low");
            if (MaxAtrPricePercent > 0 && atrPct > MaxAtrPricePercent)
                return Reject("atr_too_high");

            return true;
        }

        private bool PassSession()
        {
            if (Server.Time.DayOfWeek == DayOfWeek.Friday && FridayStopHour < 24 && Server.Time.Hour >= FridayStopHour)
                return false;

            if (!UseUtcSession)
                return true;

            int hour = Server.Time.Hour;
            int start = Math.Max(0, Math.Min(23, SessionStartHour));
            int end = Math.Max(0, Math.Min(24, SessionEndHour));
            if (start == end || end == 24 && start == 0)
                return true;
            if (start < end)
                return hour >= start && hour < end;
            return hour >= start || hour < end;
        }

        private bool PassMinimumXa(PatternMatch m)
        {
            if (MinXaPips <= 0)
                return true;
            double xaPips = Math.Abs(m.A.Price - m.X.Price) / Symbol.PipSize;
            return xaPips >= MinXaPips || Reject("xa_too_small");
        }

        private bool IsRegimeAligned(TradeType direction)
        {
            if (RegimeFilter == RegimeFilterMode.Off)
                return false;
            if (_regimeBars == null || _regimeBars.Count < RegimeEmaPeriod + 3)
                return false;

            int i = _regimeBars.Count - 2;
            if (i < 2)
                return false;

            double close = _regimeBars.ClosePrices[i];
            double ema = _regimeEma.Result[i];
            double previousEma = _regimeEma.Result[i - 1];
            bool slopeUp = ema > previousEma;
            bool slopeDown = ema < previousEma;

            if (direction == TradeType.Buy)
                return close > ema && (!RequireRegimeSlope || slopeUp);
            return close < ema && (!RequireRegimeSlope || slopeDown);
        }

        private bool PassEntryConfirmation(PatternMatch m)
        {
            int last = Bars.Count - 1;
            double atr = _atr.Result.LastValue;
            if (last <= m.D.Index || atr <= 0 || double.IsNaN(atr) || double.IsInfinity(atr))
                return Reject("confirmation_invalid");

            for (int i = m.D.Index + 1; i <= last; i++)
            {
                if (m.Direction == TradeType.Buy && Bars.LowPrices[i] < m.D.Price)
                    return Reject("D_invalidated");
                if (m.Direction == TradeType.Sell && Bars.HighPrices[i] > m.D.Price)
                    return Reject("D_invalidated");
            }

            double close = Bars.ClosePrices[last];
            double open = Bars.OpenPrices[last];
            if (Math.Abs(close - m.D.Price) > atr * MaxEntryDistanceAtr)
                return Reject("entry_too_far");

            if (m.Direction == TradeType.Buy)
            {
                if (close < m.D.Price + atr * ConfirmationMoveAtr)
                    return Reject("buy_reversal_weak");
                if (UseCandleConfirmation && close <= open)
                    return Reject("buy_candle");
            }
            else
            {
                if (close > m.D.Price - atr * ConfirmationMoveAtr)
                    return Reject("sell_reversal_weak");
                if (UseCandleConfirmation && close >= open)
                    return Reject("sell_candle");
            }

            return true;
        }

        private bool TryBuildTradePlan(PatternMatch m, out TradePlan plan)
        {
            plan = null;
            double atr = _atr.Result.LastValue;
            double entry = m.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            double stopPrice = m.Direction == TradeType.Buy
                ? m.D.Price - atr * SlAtrBuffer
                : m.D.Price + atr * SlAtrBuffer;

            double stopPips = (m.Direction == TradeType.Buy ? entry - stopPrice : stopPrice - entry) / Symbol.PipSize;
            if (double.IsNaN(stopPips) || double.IsInfinity(stopPips) || stopPips <= 0)
                return Reject("invalid_stop");

            stopPips = Math.Max(stopPips, MinStopPips);
            if (MaxStopPips > 0 && stopPips > MaxStopPips)
                return Reject("stop_too_wide");

            double tpPips = CalculateTakeProfitPips(m, entry, stopPips);
            if (tpPips <= 0)
                return Reject("invalid_target");

            double denominator = stopPips + ExecutionCostReservePips;
            double numerator = tpPips - ExecutionCostReservePips;
            if (denominator <= 0 || numerator <= 0)
                return Reject("costs_consume_reward");

            double netRr = numerator / denominator;
            if (netRr < MinimumNetRiskReward)
                return Reject("net_rr_low");

            plan = new TradePlan(m, entry, stopPips, tpPips, netRr);
            return true;
        }

        private double CalculateTakeProfitPips(PatternMatch m, double entry, double stopPips)
        {
            if (TpMode == TakeProfitMode.RiskReward)
                return stopPips * FallbackRiskReward;

            double ad = Math.Abs(m.A.Price - m.D.Price);
            double fib382Price = m.Direction == TradeType.Buy ? m.D.Price + ad * 0.382 : m.D.Price - ad * 0.382;
            double fib618Price = m.Direction == TradeType.Buy ? m.D.Price + ad * 0.618 : m.D.Price - ad * 0.618;
            double pointCPrice = m.C.Price;

            if (TpMode == TakeProfitMode.Fib382AD)
                return TargetDistancePips(m.Direction, entry, fib382Price);
            if (TpMode == TakeProfitMode.Fib618AD)
                return TargetDistancePips(m.Direction, entry, fib618Price);
            if (TpMode == TakeProfitMode.PointC)
                return TargetDistancePips(m.Direction, entry, pointCPrice);

            double conservative = TargetDistancePips(m.Direction, entry, fib382Price);
            double runner = TargetDistancePips(m.Direction, entry, fib618Price);
            bool runnerQualified = m.TrendAligned && m.FinalScore >= RunnerScore;

            if (runnerQualified && runner > conservative)
                return runner;
            return conservative;
        }

        private double TargetDistancePips(TradeType direction, double entry, double target)
        {
            double distance = direction == TradeType.Buy ? target - entry : entry - target;
            return distance > 0 ? distance / Symbol.PipSize : 0.0;
        }

        private void ExecuteTrade(TradePlan plan)
        {
            if (BlockAnySameSymbolExposure && (Positions.Any(p => p.SymbolName == SymbolName) || PendingOrders.Any(p => p.SymbolName == SymbolName)))
            {
                Reject("same_symbol_exposure_race");
                return;
            }

            double riskPercent;
            double budget;
            double volume = CalculateVolume(plan, out riskPercent, out budget);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Reject("volume_below_min");
                double minimumRisk = Symbol.AmountRisked(Symbol.VolumeInUnitsMin, plan.StopPips + ExecutionCostReservePips);
                Print("[RISK SKIP] minVolume={0} requires~{1:F2} risk; budget={2:F2}; score={3:F1}", Symbol.VolumeInUnitsMin, minimumRisk, budget, plan.Match.FinalScore);
                return;
            }

            string comment = plan.Match.Definition.Name + "|Q=" + plan.Match.FinalScore.ToString("F1", System.Globalization.CultureInfo.InvariantCulture);
            var result = ExecuteMarketOrder(plan.Match.Direction, SymbolName, volume, BotLabel, plan.StopPips, plan.TakeProfitPips, comment, false);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ORDER FAIL] {0} {1} error={2}", plan.Match.Definition.Name, plan.Match.Direction, result.Error);
                Reject("order_fail");
                return;
            }

            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[PROTECTION FAIL] Position {0} opened without complete SL/TP; closing immediately.", result.Position.Id);
                ClosePosition(result.Position);
                Reject("protection_fail");
                return;
            }

            _tradesToday++;
            _lastTradeBar = Bars.Count - 1;
            _consumedSignals.Add(plan.Match.SignalKey);
            _positionInitialRiskPips[result.Position.Id] = plan.StopPips;
            _positionPattern[result.Position.Id] = plan.Match.Definition.Name;

            PatternStats stats;
            if (!_stats.TryGetValue(plan.Match.Definition.Name, out stats))
            {
                stats = new PatternStats();
                _stats[plan.Match.Definition.Name] = stats;
            }
            stats.Trades++;

            Print("[OPEN] {0} {1} Q={2:F1} volume={3} riskPct={4:F2} budget={5:F2} SL={6:F1} TP={7:F1} netRR={8:F2}",
                plan.Match.Definition.Name, plan.Match.Direction, plan.Match.FinalScore, volume, riskPercent, budget,
                plan.StopPips, plan.TakeProfitPips, plan.NetRiskReward);
        }

        private double CalculateVolume(TradePlan plan, out double riskPercent, out double budget)
        {
            riskPercent = 0.0;
            budget = 0.0;
            double raw;

            if (RiskMode == RiskSizingMode.FixedLots)
            {
                raw = Symbol.QuantityToVolumeInUnits(FixedLots);
            }
            else
            {
                if (RiskMode == RiskSizingMode.FixedRiskCash)
                {
                    budget = FixedRiskCash;
                }
                else
                {
                    bool highQuality = plan.Match.TrendAligned && plan.Match.FinalScore >= HighQualityScore;
                    riskPercent = highQuality ? Math.Max(BaseRiskPercent, HighQualityRiskPercent) : BaseRiskPercent;
                    budget = Account.Equity * riskPercent / 100.0;
                }

                raw = Symbol.VolumeForFixedRisk(budget, plan.StopPips + ExecutionCostReservePips, RoundingMode.Down);
            }

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;

            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;

            if (RiskMode != RiskSizingMode.FixedLots)
            {
                double estimated = Symbol.AmountRisked(raw, plan.StopPips + ExecutionCostReservePips);
                if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + 1e-8)
                {
                    Reject("risk_budget_exceeded");
                    return 0;
                }
            }

            return raw;
        }

        private void ManageBreakEven()
        {
            if (!EnableBreakEven)
                return;

            foreach (var p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (_breakEvenDone.Contains(p.Id))
                    continue;

                double initialRisk;
                if (!_positionInitialRiskPips.TryGetValue(p.Id, out initialRisk) || initialRisk <= 0)
                {
                    if (!p.StopLoss.HasValue)
                        continue;
                    initialRisk = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Symbol.PipSize;
                    if (initialRisk <= 0)
                        continue;
                    _positionInitialRiskPips[p.Id] = initialRisk;
                }

                double profitPips = p.TradeType == TradeType.Buy
                    ? (Symbol.Bid - p.EntryPrice) / Symbol.PipSize
                    : (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;

                if (profitPips < initialRisk * BreakEvenTriggerR)
                    continue;

                int attemptedBar;
                if (_breakEvenAttemptBar.TryGetValue(p.Id, out attemptedBar) && attemptedBar == Bars.Count - 1)
                    continue;
                _breakEvenAttemptBar[p.Id] = Bars.Count - 1;

                double newStop = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + BreakEvenOffsetPips * Symbol.PipSize
                    : p.EntryPrice - BreakEvenOffsetPips * Symbol.PipSize;

                if (p.StopLoss.HasValue)
                {
                    if (p.TradeType == TradeType.Buy && p.StopLoss.Value >= newStop)
                    {
                        _breakEvenDone.Add(p.Id);
                        continue;
                    }
                    if (p.TradeType == TradeType.Sell && p.StopLoss.Value <= newStop)
                    {
                        _breakEvenDone.Add(p.Id);
                        continue;
                    }
                }

                double marketDistancePips = p.TradeType == TradeType.Buy
                    ? (Symbol.Bid - newStop) / Symbol.PipSize
                    : (newStop - Symbol.Ask) / Symbol.PipSize;
                if (marketDistancePips <= Math.Max(1.0, ExecutionCostReservePips * 0.25))
                    continue;

                var modify = p.ModifyStopLossPrice(newStop);
                if (modify.IsSuccessful)
                {
                    _breakEvenDone.Add(p.Id);
                    if (DebugLogging)
                        Print("[BE] position={0} stop={1}", p.Id, newStop);
                }
                else if (DebugLogging)
                {
                    Print("[BE FAIL] position={0} error={1}", p.Id, modify.Error);
                }
            }
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.Label != BotLabel || p.SymbolName != SymbolName)
                return;

            if (p.NetProfit < 0)
                _consecutiveLosses++;
            else if (p.NetProfit > 0)
                _consecutiveLosses = 0;

            string pattern;
            if (!_positionPattern.TryGetValue(p.Id, out pattern))
            {
                pattern = string.IsNullOrWhiteSpace(p.Comment) ? "Unknown" : p.Comment.Split('|')[0];
            }

            PatternStats stats;
            if (!_stats.TryGetValue(pattern, out stats))
            {
                stats = new PatternStats();
                _stats[pattern] = stats;
            }
            stats.NetProfit += p.NetProfit;
            if (p.NetProfit > 0)
                stats.Wins++;
            else if (p.NetProfit < 0)
                stats.Losses++;

            _positionInitialRiskPips.Remove(p.Id);
            _positionPattern.Remove(p.Id);
            _breakEvenAttemptBar.Remove(p.Id);
            _breakEvenDone.Remove(p.Id);
            UpdateRuntimePeak();

            if (DebugLogging)
                Print("[CLOSE] {0} net={1:F2} reason={2} streak={3}", pattern, p.NetProfit, args.Reason, _consecutiveLosses);
        }

        private void UpdateRuntimePeak()
        {
            if (Account.Equity > _runtimePeakEquity)
                _runtimePeakEquity = Account.Equity;
        }

        private bool Reject(string reason)
        {
            int count;
            _diagnostics.TryGetValue(reason, out count);
            _diagnostics[reason] = count + 1;
            return false;
        }

        public enum RiskSizingMode
        {
            FixedLots,
            RiskPercentEquity,
            FixedRiskCash
        }

        public enum RegimeFilterMode
        {
            Off,
            ScoreOnly,
            Strict
        }

        public enum TakeProfitMode
        {
            AdaptiveFib,
            Fib382AD,
            Fib618AD,
            PointC,
            RiskReward
        }

        private sealed class TradePlan
        {
            public TradePlan(PatternMatch match, double entryPrice, double stopPips, double takeProfitPips, double netRiskReward)
            {
                Match = match;
                EntryPrice = entryPrice;
                StopPips = stopPips;
                TakeProfitPips = takeProfitPips;
                NetRiskReward = netRiskReward;
            }

            public PatternMatch Match { get; private set; }
            public double EntryPrice { get; private set; }
            public double StopPips { get; private set; }
            public double TakeProfitPips { get; private set; }
            public double NetRiskReward { get; private set; }
        }

        private sealed class PatternStats
        {
            public int Trades;
            public int Wins;
            public int Losses;
            public double NetProfit;
        }
    }
}
