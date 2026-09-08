// GQ_Session_Scalper_v2
// Independent implementation based on the open-source GQ Session Scalper.
// This source is designed for cTrader Automate and intentionally does not
// contain credentials, tokens, OTPs, grid, martingale, DCA, recovery,
// hedging, or loss-averaging logic.

using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GQ_Session_Scalper_v2 : Robot
    {
        private const string BotLabel = "GQ-Session-Scalper-v2";

        [Parameter("Session Start (HH:mm)", Group = "Session", DefaultValue = "08:00")]
        public string SessionStart { get; set; }

        [Parameter("Session End (HH:mm)", Group = "Session", DefaultValue = "16:00")]
        public string SessionEnd { get; set; }

        [Parameter("Risk Per Trade (%)", Group = "Risk", DefaultValue = 0.50, MinValue = 0.01, MaxValue = 5.0, Step = 0.01)]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Max Daily Loss (%)", Group = "Risk", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 20.0, Step = 0.1)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Consecutive Losses", Group = "Risk", DefaultValue = 3, MinValue = 1, MaxValue = 20)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("EMA Period", Group = "Entry", DefaultValue = 21, MinValue = 2, MaxValue = 200)]
        public int EMAPeriod { get; set; }

        [Parameter("Momentum Period", Group = "Entry", DefaultValue = 14, MinValue = 2, MaxValue = 100)]
        public int MomentumPeriod { get; set; }

        [Parameter("Momentum Threshold", Group = "Entry", DefaultValue = 100.0, MinValue = 0.0, MaxValue = 200.0)]
        public double MomentumThreshold { get; set; }

        [Parameter("Pullback ATR Fraction", Group = "Entry", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Step = 0.05)]
        public double PullbackAtrFraction { get; set; }

        [Parameter("Trend EMA Fast", Group = "Higher-Timeframe Trend", DefaultValue = 50, MinValue = 2, MaxValue = 200)]
        public int TrendFastPeriod { get; set; }

        [Parameter("Trend EMA Slow", Group = "Higher-Timeframe Trend", DefaultValue = 200, MinValue = 10, MaxValue = 500)]
        public int TrendSlowPeriod { get; set; }

        [Parameter("Trend TimeFrame", Group = "Higher-Timeframe Trend", DefaultValue = "Hour")]
        public TimeFrame TrendTimeFrame { get; set; }

        [Parameter("ATR Period", Group = "Volatility", DefaultValue = 14, MinValue = 2, MaxValue = 100)]
        public int ATRPeriod { get; set; }

        [Parameter("ATR SL Multiplier", Group = "Volatility", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 5.0, Step = 0.1)]
        public double AtrSlMultiplier { get; set; }

        [Parameter("Minimum SL (pips)", Group = "Volatility", DefaultValue = 5.0, MinValue = 1.0, MaxValue = 100.0, Step = 0.5)]
        public double MinimumSlPips { get; set; }

        [Parameter("TP R Multiple", Group = "Trade Management", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 5.0, Step = 0.1)]
        public double TpRMultiple { get; set; }

        [Parameter("Breakeven Trigger (R)", Group = "Trade Management", DefaultValue = 1.0, MinValue = 0.25, MaxValue = 5.0, Step = 0.05)]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Offset (pips)", Group = "Trade Management", DefaultValue = 0.2, MinValue = 0.0, MaxValue = 10.0, Step = 0.1)]
        public double BreakevenOffsetPips { get; set; }

        [Parameter("Trailing Trigger (R)", Group = "Trade Management", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 10.0, Step = 0.1)]
        public double TrailingTriggerR { get; set; }

        [Parameter("Trailing ATR Multiplier", Group = "Trade Management", DefaultValue = 1.0, MinValue = 0.25, MaxValue = 5.0, Step = 0.1)]
        public double TrailingAtrMultiplier { get; set; }

        [Parameter("Cooldown (minutes)", Group = "Trade Management", DefaultValue = 30, MinValue = 0, MaxValue = 1440)]
        public int CooldownMinutes { get; set; }

        [Parameter("Maximum Spread (pips)", Group = "Costs", DefaultValue = 1.5, MinValue = 0.1, MaxValue = 100.0, Step = 0.1)]
        public double MaximumSpreadPips { get; set; }

        [Parameter("Estimated Slippage (pips)", Group = "Costs", DefaultValue = 0.2, MinValue = 0.0, MaxValue = 10.0, Step = 0.1)]
        public double EstimatedSlippagePips { get; set; }

        [Parameter("Commission Per Lot / Round Turn", Group = "Costs", DefaultValue = 7.0, MinValue = 0.0, MaxValue = 100.0, Step = 0.5)]
        public double CommissionPerLot { get; set; }

        private ExponentialMovingAverage _entryEma;
        private Momentum _momentum;
        private AverageTrueRange _atr;
        private Bars _trendBars;
        private ExponentialMovingAverage _trendFast;
        private ExponentialMovingAverage _trendSlow;
        private TimeSpan _sessionStart;
        private TimeSpan _sessionEnd;
        private DateTime _riskDate;
        private double _dayStartEquity;
        private int _consecutiveLosses;
        private DateTime _lastEntryTime = DateTime.MinValue;
        private DateTime _lastSignalBar = DateTime.MinValue;
        private bool _stoppedForRisk;

        protected override void OnStart()
        {
            try
            {
                if (EMAPeriod < 2 || TrendFastPeriod < 2 || TrendSlowPeriod <= TrendFastPeriod ||
                    ATRPeriod < 2 || RiskPerTradePercent <= 0 || TpRMultiple <= 0)
                    throw new ArgumentException("Invalid parameter relationship.");

                _entryEma = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EMAPeriod);
                _momentum = Indicators.Momentum(Bars.ClosePrices, MomentumPeriod);
                _atr = Indicators.AverageTrueRange(ATRPeriod, MovingAverageType.Exponential);

                _trendBars = MarketData.GetBars(TrendTimeFrame);
                _trendFast = Indicators.ExponentialMovingAverage(_trendBars.ClosePrices, TrendFastPeriod);
                _trendSlow = Indicators.ExponentialMovingAverage(_trendBars.ClosePrices, TrendSlowPeriod);

                if (!TimeSpan.TryParse(SessionStart, out _sessionStart))
                    _sessionStart = new TimeSpan(8, 0, 0);
                if (!TimeSpan.TryParse(SessionEnd, out _sessionEnd))
                    _sessionEnd = new TimeSpan(16, 0, 0);

                _riskDate = Server.Time.Date;
                _dayStartEquity = Account.Equity;
                _consecutiveLosses = 0;
                _stoppedForRisk = false;
                Print("{0} started on {1}; source data and costs must be verified for the broker.", BotLabel, SymbolName);
            }
            catch (Exception ex)
            {
                Print("START_ERROR: {0}", ex.Message);
                Stop();
            }
        }

        // Entry evaluation is deliberately bar-close based. No entry is placed
        // from OnTick, preventing duplicate intrabar signals and repaint-like use.
        protected override void OnBarClosed()
        {
            try
            {
                ResetDailyRiskIfNeeded();
                ManageOpenPosition();

                if (!CanTradeNow())
                    return;

                var signalBar = Bars.LastBar.OpenTime;
                if (signalBar == _lastSignalBar)
                    return;
                _lastSignalBar = signalBar;

                if (Bars.Count < Math.Max(Math.Max(EMAPeriod, ATRPeriod), MomentumPeriod) + 5)
                    return;
                if (_trendBars.Count < TrendSlowPeriod + 5)
                    return;
                if (HasManagedPosition())
                    return;

                double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
                if (spreadPips > MaximumSpreadPips)
                    return;

                var signal = GetSignal();
                if (signal == null)
                    return;

                double atrPips = _atr.Result.Last(0) / Symbol.PipSize;
                double stopLossPips = Math.Max(MinimumSlPips, atrPips * AtrSlMultiplier);
                if (!IsFinitePositive(stopLossPips))
                    return;

                double volume = CalculateRiskBasedVolume(stopLossPips);
                if (volume < Symbol.VolumeInUnitsMin)
                {
                    Print("VOLUME_REJECTED: risk budget is below broker minimum volume.");
                    return;
                }

                ExecuteEntry(signal.Value, volume, stopLossPips);
            }
            catch (Exception ex)
            {
                Print("BAR_CLOSE_ERROR: {0}", ex.Message);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDailyRiskIfNeeded();
                ManageOpenPosition();
            }
            catch (Exception ex)
            {
                Print("TICK_MANAGEMENT_ERROR: {0}", ex.Message);
            }
        }

        private TradeType? GetSignal()
        {
            double close = Bars.ClosePrices.Last(0);
            double previousClose = Bars.ClosePrices.Last(1);
            double ema = _entryEma.Result.Last(0);
            double previousEma = _entryEma.Result.Last(1);
            double momentum = _momentum.Result.Last(0);
            double atr = _atr.Result.Last(0);
            double trendFast = _trendFast.Result.Last(1);
            double trendSlow = _trendSlow.Result.Last(1);
            double previousTrendFast = _trendFast.Result.Last(2);
            double previousTrendSlow = _trendSlow.Result.Last(2);

            bool trendUp = trendFast > trendSlow && trendFast > previousTrendFast;
            bool trendDown = trendFast < trendSlow && trendFast < previousTrendFast;
            bool pullback = Math.Abs(close - ema) <= atr * PullbackAtrFraction ||
                            (Bars.HighPrices.Last(0) >= ema && Bars.LowPrices.Last(0) <= ema);

            bool bullishMomentum = momentum > MomentumThreshold && close > previousClose;
            bool bearishMomentum = momentum < MomentumThreshold && close < previousClose;
            bool bullishDirection = close > ema && ema > previousEma;
            bool bearishDirection = close < ema && ema < previousEma;

            if (trendUp && pullback && bullishMomentum && bullishDirection)
                return TradeType.Buy;
            if (trendDown && pullback && bearishMomentum && bearishDirection)
                return TradeType.Sell;
            return null;
        }

        private double CalculateRiskBasedVolume(double stopLossPips)
        {
            // cTrader performs the contract-size/currency conversion here.
            // Rounding down prevents the broker-normalized volume from
            // exceeding the declared percentage risk.
            double normalized = Symbol.VolumeForProportionalRisk(
                RiskType.Equity, RiskPerTradePercent, stopLossPips, RoundingMode.Down);
            if (!IsFinitePositive(normalized))
                return 0;
            normalized = Math.Min(normalized, Symbol.VolumeInUnitsMax);
            return Math.Max(0, normalized);
        }

        private void ExecuteEntry(TradeType tradeType, double volume, double stopLossPips)
        {
            if (HasManagedPosition() || _stoppedForRisk)
                return;

            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (spreadPips + EstimatedSlippagePips > MaximumSpreadPips)
            {
                Print("COST_FILTER: spread plus slippage exceeds configured maximum.");
                return;
            }

            double takeProfitPips = stopLossPips * TpRMultiple;
            var result = ExecuteMarketOrder(tradeType, SymbolName, volume, BotLabel,
                stopLossPips, takeProfitPips,
                "completed-bar; risk-based; no-hedging");

            if (!result.IsSuccessful || result.Position == null)
            {
                Print("ENTRY_ERROR: {0}", result.Error);
                return;
            }

            _lastEntryTime = Server.Time;
            Print("ENTRY: {0}, volume={1}, SL={2:F1} pips, TP={3:F1} pips",
                tradeType, volume, stopLossPips, takeProfitPips);
        }

        private void ManageOpenPosition()
        {
            var position = Positions.FirstOrDefault(p => p.SymbolName == SymbolName && p.Label == BotLabel);
            if (position == null)
                return;

            double initialRiskPips = Math.Abs(position.EntryPrice - (position.StopLoss ?? position.EntryPrice)) / Symbol.PipSize;
            if (!IsFinitePositive(initialRiskPips))
                return;

            double favorablePips = position.TradeType == TradeType.Buy
                ? (Symbol.Bid - position.EntryPrice) / Symbol.PipSize
                : (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
            double rMultiple = favorablePips / initialRiskPips;
            double atrPips = _atr.Result.Last(0) / Symbol.PipSize;

            if (rMultiple >= BreakevenTriggerR)
            {
                double breakeven = position.TradeType == TradeType.Buy
                    ? position.EntryPrice + BreakevenOffsetPips * Symbol.PipSize
                    : position.EntryPrice - BreakevenOffsetPips * Symbol.PipSize;
                TryImproveStop(position, breakeven);
            }

            if (rMultiple >= TrailingTriggerR && IsFinitePositive(atrPips))
            {
                double trailing = position.TradeType == TradeType.Buy
                    ? Symbol.Bid - atrPips * TrailingAtrMultiplier * Symbol.PipSize
                    : Symbol.Ask + atrPips * TrailingAtrMultiplier * Symbol.PipSize;
                TryImproveStop(position, trailing);
            }
        }

        private void TryImproveStop(Position position, double candidateStop)
        {
            if (!IsFinitePositive(candidateStop))
                return;

            bool improves = !position.StopLoss.HasValue ||
                (position.TradeType == TradeType.Buy && candidateStop > position.StopLoss.Value) ||
                (position.TradeType == TradeType.Sell && candidateStop < position.StopLoss.Value);
            if (!improves)
                return;

            var modify = ModifyPosition(position, candidateStop, position.TakeProfit);
            if (!modify.IsSuccessful)
                Print("STOP_UPDATE_ERROR: {0}", modify.Error);
        }

        protected override void OnPositionClosed(PositionClosedEventArgs args)
        {
            var position = args.Position;
            if (position.Label != BotLabel || position.SymbolName != SymbolName)
                return;

            if (position.NetProfit < 0)
                _consecutiveLosses++;
            else if (position.NetProfit > 0)
                _consecutiveLosses = 0;
            Print("CLOSE: net={0:F2}, consecutive losses={1}", position.NetProfit, _consecutiveLosses);
        }

        private bool CanTradeNow()
        {
            if (_stoppedForRisk || !IsInSession(Server.Time))
                return false;
            if (HasManagedPosition())
                return false;
            if (_lastEntryTime != DateTime.MinValue &&
                Server.Time - _lastEntryTime < TimeSpan.FromMinutes(CooldownMinutes))
                return false;
            if (_consecutiveLosses >= MaxConsecutiveLosses)
                return false;

            double dailyLoss = (_dayStartEquity - Account.Equity) / Math.Max(1.0, _dayStartEquity) * 100.0;
            if (dailyLoss >= MaxDailyLossPercent)
            {
                _stoppedForRisk = true;
                Print("DAILY_RISK_STOP: {0:F2}% loss reached.", dailyLoss);
                return false;
            }
            return true;
        }

        private bool HasManagedPosition()
        {
            // One managed position per symbol/label: no hedging and no stacking.
            return Positions.Count(p => p.SymbolName == SymbolName && p.Label == BotLabel) > 0;
        }

        private bool IsInSession(DateTime time)
        {
            TimeSpan current = time.TimeOfDay;
            return _sessionStart <= _sessionEnd
                ? current >= _sessionStart && current <= _sessionEnd
                : current >= _sessionStart || current <= _sessionEnd;
        }

        private void ResetDailyRiskIfNeeded()
        {
            if (Server.Time.Date == _riskDate)
                return;
            _riskDate = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _consecutiveLosses = 0;
            _stoppedForRisk = false;
        }

        private static bool IsFinitePositive(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value) && value > 0;
        }
    }
}