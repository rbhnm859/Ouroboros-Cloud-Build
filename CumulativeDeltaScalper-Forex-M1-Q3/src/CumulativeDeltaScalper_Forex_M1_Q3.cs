using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum ForexM1RiskMode
    {
        FixedMoneyRisk = 0,
        RiskPercent = 1,
        FixedLots = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_Forex_M1_Q3 : Robot
    {
        private const string Prefix = "[CDS-FX-M1-Q3] ";

        [Parameter("Bot Label", DefaultValue = "CDS_FX_M1_Q3", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Allowed FX", DefaultValue = "AUTO", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Min Ticks / Bar", DefaultValue = 12, MinValue = 1, Group = "Microstructure")]
        public int MinTicksPerBar { get; set; }

        [Parameter("Imbalance Trigger", DefaultValue = 0.20, MinValue = 0.05, MaxValue = 0.95, Step = 0.05, Group = "Microstructure")]
        public double ImbalanceTrigger { get; set; }

        [Parameter("Signal Score Threshold", DefaultValue = 0.62, MinValue = 0.40, MaxValue = 0.95, Step = 0.01, Group = "Signal")]
        public double SignalScoreThreshold { get; set; }

        [Parameter("HTF EMA Period", DefaultValue = 50, MinValue = 10, Group = "Signal")]
        public int HtfEmaPeriod { get; set; }

        [Parameter("Momentum Lookback", DefaultValue = 3, MinValue = 1, MaxValue = 10, Group = "Signal")]
        public int MomentumLookback { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 5, Group = "Execution")]
        public int AtrPeriod { get; set; }

        [Parameter("Max Spread Pips", DefaultValue = 1.5, MinValue = 0.1, Step = 0.1, Group = "Execution")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Max Spread / ATR", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 1.0, Step = 0.05, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Session Start UTC", DefaultValue = 6, MinValue = 0, MaxValue = 23, Group = "Execution")]
        public int SessionStartHourUtc { get; set; }

        [Parameter("Session End UTC", DefaultValue = 17, MinValue = 0, MaxValue = 23, Group = "Execution")]
        public int SessionEndHourUtc { get; set; }

        [Parameter("Risk Mode", DefaultValue = ForexM1RiskMode.FixedMoneyRisk, Group = "Risk")]
        public ForexM1RiskMode RiskMode { get; set; }

        [Parameter("Fixed Money Risk", DefaultValue = 1.0, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Risk %", DefaultValue = 1.0, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Fixed Lots", DefaultValue = 0.01, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedLots { get; set; }

        [Parameter("Max Lots", DefaultValue = 0.05, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double MaxLots { get; set; }

        [Parameter("SL ATR Mult", DefaultValue = 1.0, MinValue = 0.3, Step = 0.1, Group = "Risk")]
        public double StopAtrMultiplier { get; set; }

        [Parameter("Base R:R", DefaultValue = 1.25, MinValue = 0.5, MaxValue = 4.0, Step = 0.05, Group = "Risk")]
        public double BaseRiskReward { get; set; }

        [Parameter("Hard Actual Loss Cap", DefaultValue = true, Group = "Risk")]
        public bool UseHardActualLossCap { get; set; }

        [Parameter("Max Actual Loss Money", DefaultValue = 1.0, MinValue = 0.05, Step = 0.05, Group = "Risk")]
        public double MaxActualLossMoney { get; set; }

        [Parameter("Max Daily Loss Money", DefaultValue = 3.0, MinValue = 0.0, Step = 0.1, Group = "Protection")]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Max Daily Trades", DefaultValue = 8, MinValue = 1, Group = "Protection")]
        public int MaxDailyTrades { get; set; }

        [Parameter("Loss Cooldown Min", DefaultValue = 5, MinValue = 0, Group = "Protection")]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Use Breakeven", DefaultValue = true, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven At R", DefaultValue = 0.8, MinValue = 0.2, Step = 0.1, Group = "Exit")]
        public double BreakevenAtR { get; set; }

        private Bars _m5Bars;
        private Bars _m15Bars;
        private AverageTrueRange _atr;
        private ExponentialMovingAverage _m15Ema;

        private double _prevBid;
        private int _upTicks;
        private int _downTicks;
        private int _flatTicks;
        private int _closedUpTicks;
        private int _closedDownTicks;
        private int _closedFlatTicks;
        private DateTime _lastProcessedBarTime = DateTime.MinValue;
        private DateTime _currentDay;
        private DateTime _lastLossTime = DateTime.MinValue;
        private int _dailyTradeCount;
        private double _dailyClosedPnl;
        private double _openInitialRiskPips;
        private bool _breakevenApplied;

        protected override void OnStart()
        {
            if (!ValidateSymbol())
            {
                Print(Prefix + "Unsupported symbol. Q3 is Forex-only: EURUSD, GBPUSD, USDJPY, AUDUSD.");
                Stop();
                return;
            }

            if (TimeFrame != TimeFrame.Minute)
            {
                Print(Prefix + "Q3 is M1-first and only executes on M1.");
                Stop();
                return;
            }

            _m5Bars = MarketData.GetBars(TimeFrame.Minute5);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
            _m15Ema = Indicators.ExponentialMovingAverage(_m15Bars.ClosePrices, HtfEmaPeriod);
            _prevBid = Symbol.Bid;
            _currentDay = Server.Time.Date;
            Positions.Closed += OnPositionClosed;
            Debug("started " + SymbolName + " M1 Forex-specialized Q3");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
        }

        protected override void OnTick()
        {
            ResetDailyIfNeeded();
            double bid = Symbol.Bid;
            if (bid > _prevBid) _upTicks++;
            else if (bid < _prevBid) _downTicks++;
            else _flatTicks++;
            _prevBid = bid;

            Position p = FindPosition();
            if (p == null) return;

            if (UseHardActualLossCap && p.NetProfit <= -MaxActualLossMoney)
            {
                ClosePosition(p);
                return;
            }

            if (UseBreakeven && !_breakevenApplied)
                TryBreakeven(p);
        }

        protected override void OnBar()
        {
            ResetDailyIfNeeded();
            FinalizeTickImbalance();

            DateTime barTime = Bars.OpenTimes.LastValue;
            if (barTime == _lastProcessedBarTime) return;
            _lastProcessedBarTime = barTime;

            if (FindPosition() != null) return;
            if (!IsSessionOpen()) return;
            if (_dailyTradeCount >= MaxDailyTrades) return;
            if (MaxDailyLossMoney > 0 && _dailyClosedPnl <= -MaxDailyLossMoney) return;
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) return;

            double atrPips = ClosedAtrPips();
            if (atrPips <= 0) return;

            double spreadPips = SpreadPips();
            if (spreadPips > MaxSpreadPips) return;
            if (spreadPips / atrPips > MaxSpreadAtrRatio) return;

            int direction;
            double score;
            if (!BuildSignal(out direction, out score)) return;
            if (score < SignalScoreThreshold) return;

            OpenTrade(direction, atrPips, score);
        }

        private void FinalizeTickImbalance()
        {
            _closedUpTicks = _upTicks;
            _closedDownTicks = _downTicks;
            _closedFlatTicks = _flatTicks;
            _upTicks = 0;
            _downTicks = 0;
            _flatTicks = 0;
        }

        private bool BuildSignal(out int direction, out double score)
        {
            direction = 0;
            score = 0;

            int totalDirectional = _closedUpTicks + _closedDownTicks;
            int totalTicks = totalDirectional + _closedFlatTicks;
            if (totalTicks < MinTicksPerBar || totalDirectional <= 0) return false;

            double imbalance = (_closedUpTicks - _closedDownTicks) / (double)totalDirectional;
            if (Math.Abs(imbalance) < ImbalanceTrigger) return false;
            direction = imbalance > 0 ? 1 : -1;

            double imbalanceScore = Clamp01((Math.Abs(imbalance) - ImbalanceTrigger) / Math.Max(0.01, 1.0 - ImbalanceTrigger));
            double trendScore = TrendScore(direction);
            double momentumScore = MomentumScore(direction);
            double volatilityScore = VolatilityScore();
            double executionScore = ExecutionScore();

            score = 0.30 * imbalanceScore +
                    0.25 * trendScore +
                    0.20 * momentumScore +
                    0.15 * volatilityScore +
                    0.10 * executionScore;

            Debug("signal dir=" + direction + " imbalance=" + imbalance.ToString("F2") + " score=" + score.ToString("F2") +
                  " ti=" + imbalanceScore.ToString("F2") + " tr=" + trendScore.ToString("F2") +
                  " mom=" + momentumScore.ToString("F2") + " vol=" + volatilityScore.ToString("F2") +
                  " exe=" + executionScore.ToString("F2"));
            return true;
        }

        private double TrendScore(int direction)
        {
            int n = _m15Bars.ClosePrices.Count - 2;
            if (n < 3 || n >= _m15Ema.Result.Count) return 0;
            double close = _m15Bars.ClosePrices[n];
            double emaNow = _m15Ema.Result[n];
            double emaPrev = _m15Ema.Result[n - 2];
            bool priceAligned = direction > 0 ? close > emaNow : close < emaNow;
            bool slopeAligned = direction > 0 ? emaNow > emaPrev : emaNow < emaPrev;
            if (priceAligned && slopeAligned) return 1.0;
            if (priceAligned || slopeAligned) return 0.5;
            return 0.0;
        }

        private double MomentumScore(int direction)
        {
            int n = _m5Bars.ClosePrices.Count - 2;
            int old = n - MomentumLookback;
            if (old < 0) return 0;
            double delta = _m5Bars.ClosePrices[n] - _m5Bars.ClosePrices[old];
            if (Math.Abs(delta) < Symbol.PipSize * 0.2) return 0.5;
            bool aligned = direction > 0 ? delta > 0 : delta < 0;
            return aligned ? 1.0 : 0.0;
        }

        private double VolatilityScore()
        {
            double atrPips = ClosedAtrPips();
            if (atrPips <= 0) return 0;
            if (atrPips >= 2.0 && atrPips <= 8.0) return 1.0;
            if (atrPips >= 1.0 && atrPips <= 12.0) return 0.6;
            return 0.2;
        }

        private double ExecutionScore()
        {
            double atrPips = ClosedAtrPips();
            if (atrPips <= 0) return 0;
            double ratio = SpreadPips() / atrPips;
            if (ratio <= 0.15) return 1.0;
            if (ratio <= 0.25) return 0.7;
            if (ratio <= MaxSpreadAtrRatio) return 0.4;
            return 0.0;
        }

        private void OpenTrade(int direction, double atrPips, double score)
        {
            double slPips = Math.Max(0.5, atrPips * StopAtrMultiplier);
            double rr = BaseRiskReward;
            double tpPips = slPips * rr;
            double volume = ResolveVolume(slPips);
            if (volume < Symbol.VolumeInUnitsMin) return;

            TradeType type = direction > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful)
            {
                Debug("entry failed: " + result.Error);
                return;
            }

            _dailyTradeCount++;
            _openInitialRiskPips = slPips;
            _breakevenApplied = false;
            Debug("opened " + type + " score=" + score.ToString("F2") + " sl=" + slPips.ToString("F1") + " tp=" + tpPips.ToString("F1"));
        }

        private double ResolveVolume(double slPips)
        {
            double volume;
            if (RiskMode == ForexM1RiskMode.FixedLots)
            {
                volume = Symbol.QuantityToVolumeInUnits(Math.Min(FixedLots, MaxLots));
            }
            else
            {
                double riskMoney = RiskMode == ForexM1RiskMode.RiskPercent
                    ? Account.Balance * RiskPercent / 100.0
                    : FixedMoneyRisk;
                if (UseHardActualLossCap && MaxActualLossMoney > 0)
                    riskMoney = Math.Min(riskMoney, MaxActualLossMoney * 0.85);
                volume = Symbol.VolumeForFixedRisk(riskMoney, slPips, RoundingMode.Down);
                volume = Math.Min(volume, Symbol.QuantityToVolumeInUnits(MaxLots));
            }
            return Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
        }

        private void TryBreakeven(Position p)
        {
            double riskPips = _openInitialRiskPips > 0 ? _openInitialRiskPips : ClosedAtrPips() * StopAtrMultiplier;
            if (riskPips <= 0) return;
            double profitPips = p.TradeType == TradeType.Buy
                ? (Symbol.Bid - p.EntryPrice) / Symbol.PipSize
                : (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;
            if (profitPips < BreakevenAtR * riskPips) return;

            double newSl = p.TradeType == TradeType.Buy
                ? p.EntryPrice + 0.1 * Symbol.PipSize
                : p.EntryPrice - 0.1 * Symbol.PipSize;
            TradeResult r = ModifyPosition(p, newSl, p.TakeProfit);
            if (r.IsSuccessful) _breakevenApplied = true;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != TradeLabel) return;
            _dailyClosedPnl += p.NetProfit;
            if (p.NetProfit < 0) _lastLossTime = Server.Time;
            _openInitialRiskPips = 0;
            _breakevenApplied = false;
        }

        private Position FindPosition()
        {
            return Positions.FirstOrDefault(p => p.SymbolName == SymbolName && p.Label == TradeLabel);
        }

        private bool ValidateSymbol()
        {
            string s = SymbolName.ToUpperInvariant();
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "AUTO" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            if (allowed != "AUTO" && allowed != "*") return s.StartsWith(allowed);
            return s.StartsWith("EURUSD") || s.StartsWith("GBPUSD") || s.StartsWith("USDJPY") || s.StartsWith("AUDUSD");
        }

        private bool IsSessionOpen()
        {
            int h = Server.Time.Hour;
            if (SessionStartHourUtc <= SessionEndHourUtc)
                return h >= SessionStartHourUtc && h < SessionEndHourUtc;
            return h >= SessionStartHourUtc || h < SessionEndHourUtc;
        }

        private double ClosedAtrPips()
        {
            int i = Bars.ClosePrices.Count - 2;
            if (i < 0 || i >= _atr.Result.Count) return 0;
            return _atr.Result[i] / Symbol.PipSize;
        }

        private double SpreadPips()
        {
            return (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private void ResetDailyIfNeeded()
        {
            if (Server.Time.Date == _currentDay) return;
            _currentDay = Server.Time.Date;
            _dailyTradeCount = 0;
            _dailyClosedPnl = 0;
        }

        private static double Clamp01(double x)
        {
            return Math.Max(0.0, Math.Min(1.0, x));
        }

        private void Debug(string message)
        {
            if (DebugLogging) Print(Prefix + message);
        }
    }
}
