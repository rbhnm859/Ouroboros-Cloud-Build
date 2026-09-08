using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public enum BreakoutRiskBase { Balance, Equity }
    public enum BreakoutStopMode { OppositeSide, BarRangeMultiple, AtrMultiple }
    public enum BreakoutTpMode { RiskReward, BarRangeMultiple, AtrMultiple }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class BarBreakoutTrading : Robot
    {
        [Parameter("Label", DefaultValue = "BarBreakoutTrading", Group = "General")]
        public string Label { get; set; }

        [Parameter("Enable Trading", DefaultValue = true, Group = "General")]
        public bool EnableTrading { get; set; }

        [Parameter("Breakout Lookback Bars", DefaultValue = 1, MinValue = 1, Group = "Breakout")]
        public int BreakoutLookbackBars { get; set; }

        [Parameter("Breakout Buffer (pips)", DefaultValue = 0.2, MinValue = 0.0, Group = "Breakout")]
        public double BreakoutBufferPips { get; set; }

        [Parameter("Minimum Breakout Distance (pips)", DefaultValue = 0.1, MinValue = 0.0, Group = "Breakout")]
        public double MinimumBreakoutDistancePips { get; set; }

        [Parameter("Minimum Bar Range (pips)", DefaultValue = 2.0, MinValue = 0.0, Group = "Breakout")]
        public double MinimumBarRangePips { get; set; }

        [Parameter("Maximum Bar Range (pips, 0=off)", DefaultValue = 120.0, MinValue = 0.0, Group = "Breakout")]
        public double MaximumBarRangePips { get; set; }

        [Parameter("Enable Buy Breakout", DefaultValue = true, Group = "Breakout")]
        public bool EnableBuyBreakout { get; set; }

        [Parameter("Enable Sell Breakout", DefaultValue = true, Group = "Breakout")]
        public bool EnableSellBreakout { get; set; }

        [Parameter("Risk Per Trade %", DefaultValue = 0.5, MinValue = 0.01, MaxValue = 20.0, Group = "Risk")]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Risk Base", DefaultValue = BreakoutRiskBase.Equity, Group = "Risk")]
        public BreakoutRiskBase RiskBase { get; set; }

        [Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, Group = "Risk")]
        public int MaxOpenPositions { get; set; }

        [Parameter("Max Trades Per Day", DefaultValue = 8, MinValue = 1, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Maximum Daily Loss % (0=off)", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 100.0, Group = "Risk")]
        public double MaximumDailyLossPercent { get; set; }

        [Parameter("Maximum Equity Drawdown % (0=off)", DefaultValue = 20.0, MinValue = 0.0, MaxValue = 100.0, Group = "Risk")]
        public double MaximumEquityDrawdownPercent { get; set; }

        [Parameter("Consecutive Loss Limit (0=off)", DefaultValue = 5, MinValue = 0, Group = "Risk")]
        public int ConsecutiveLossLimit { get; set; }

        [Parameter("Cooldown After Loss (minutes)", DefaultValue = 30, MinValue = 0, Group = "Risk")]
        public int CooldownAfterLossMinutes { get; set; }

        [Parameter("Cooldown After Trade (minutes)", DefaultValue = 0, MinValue = 0, Group = "Risk")]
        public int CooldownAfterTradeMinutes { get; set; }

        [Parameter("Cooldown After Trade (bars)", DefaultValue = 0, MinValue = 0, Group = "Risk")]
        public int CooldownAfterTradeBars { get; set; }

        [Parameter("Max Spread (pips, 0=off)", DefaultValue = 2.0, MinValue = 0.0, Group = "Cost")]
        public double MaximumSpreadPips { get; set; }

        [Parameter("Max Entry Slippage (pips, 0=off)", DefaultValue = 1.0, MinValue = 0.0, Group = "Cost")]
        public double MaximumEntrySlippagePips { get; set; }

        [Parameter("Enable ATR Filter", DefaultValue = true, Group = "Filters")]
        public bool EnableAtrFilter { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 2, Group = "Filters")]
        public int AtrPeriod { get; set; }

        [Parameter("Minimum ATR (pips)", DefaultValue = 1.0, MinValue = 0.0, Group = "Filters")]
        public double MinimumAtrPips { get; set; }

        [Parameter("Enable EMA Trend Filter", DefaultValue = false, Group = "Filters")]
        public bool EnableEmaTrendFilter { get; set; }

        [Parameter("EMA Period", DefaultValue = 100, MinValue = 2, Group = "Filters")]
        public int EmaPeriod { get; set; }

        [Parameter("Require EMA Slope", DefaultValue = false, Group = "Filters")]
        public bool RequireEmaSlope { get; set; }

        [Parameter("Enable Session Filter", DefaultValue = false, Group = "Session")]
        public bool EnableSessionFilter { get; set; }

        [Parameter("Trading Session Start Hour UTC", DefaultValue = 0, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int TradingSessionStartHourUtc { get; set; }

        [Parameter("Trading Session End Hour UTC", DefaultValue = 23, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int TradingSessionEndHourUtc { get; set; }

        [Parameter("Stop Loss Mode", DefaultValue = BreakoutStopMode.OppositeSide, Group = "Stops")]
        public BreakoutStopMode StopLossMode { get; set; }

        [Parameter("Bar Range SL Multiplier", DefaultValue = 1.0, MinValue = 0.1, Group = "Stops")]
        public double BarRangeStopMultiplier { get; set; }

        [Parameter("ATR SL Multiplier", DefaultValue = 1.5, MinValue = 0.1, Group = "Stops")]
        public double AtrStopMultiplier { get; set; }

        [Parameter("Opposite Side Buffer (pips)", DefaultValue = 0.2, MinValue = 0.0, Group = "Stops")]
        public double OppositeSideBufferPips { get; set; }

        [Parameter("Take Profit Mode", DefaultValue = BreakoutTpMode.RiskReward, Group = "TakeProfit")]
        public BreakoutTpMode TakeProfitMode { get; set; }

        [Parameter("Risk/Reward", DefaultValue = 1.8, MinValue = 0.1, Group = "TakeProfit")]
        public double RiskRewardRatio { get; set; }

        [Parameter("Bar Range TP Multiplier", DefaultValue = 1.5, MinValue = 0.1, Group = "TakeProfit")]
        public double BarRangeTpMultiplier { get; set; }

        [Parameter("ATR TP Multiplier", DefaultValue = 2.0, MinValue = 0.1, Group = "TakeProfit")]
        public double AtrTpMultiplier { get; set; }

        [Parameter("Enable Breakeven", DefaultValue = false, Group = "Management")]
        public bool EnableBreakeven { get; set; }

        [Parameter("Breakeven Trigger (R)", DefaultValue = 1.0, MinValue = 0.1, Group = "Management")]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Extra (pips)", DefaultValue = 0.2, MinValue = 0.0, Group = "Management")]
        public double BreakevenExtraPips { get; set; }

        [Parameter("Enable ATR Trailing", DefaultValue = false, Group = "Management")]
        public bool EnableAtrTrailing { get; set; }

        [Parameter("ATR Trail Multiplier", DefaultValue = 1.2, MinValue = 0.1, Group = "Management")]
        public double AtrTrailMultiplier { get; set; }

        [Parameter("Enable Bar Trailing", DefaultValue = false, Group = "Management")]
        public bool EnableBarTrailing { get; set; }

        [Parameter("Bar Trail Lookback", DefaultValue = 1, MinValue = 1, Group = "Management")]
        public int BarTrailLookback { get; set; }

        [Parameter("Bar Trail Buffer (pips)", DefaultValue = 0.1, MinValue = 0.0, Group = "Management")]
        public double BarTrailBufferPips { get; set; }

        private AverageTrueRange _atr;
        private ExponentialMovingAverage _ema;
        private DateTime _day;
        private double _dayStartEquity;
        private double _peakEquity;
        private int _tradesToday;
        private int _consecutiveLosses;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private int _lastTradeBar = int.MinValue;
        private bool _dailyBlocked;
        private bool _drawdownBlocked;
        private readonly HashSet<string> _consumedSignals = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<int, double> _initialRiskPips = new Dictionary<int, double>();
        private readonly Dictionary<int, string> _managedStopReason = new Dictionary<int, string>();

        protected override void OnStart()
        {
            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);
            _day = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _peakEquity = Account.Equity;
            Positions.Closed += OnPositionClosed;
            Print("[START] BarBreakoutTrading Symbol={0} TF={1}", SymbolName, TimeFrame);
        }

        protected override void OnBarClosed()
        {
            RefreshProtection();
            if (!EnableTrading || _dailyBlocked || _drawdownBlocked)
                return;

            int warmup = Math.Max(Math.Max(AtrPeriod, EmaPeriod), BreakoutLookbackBars) + 10;
            if (Bars.Count < warmup)
                return;

            if (!IsSessionAllowed() || !PassTradeLimits())
                return;

            double spread = GetSpreadPips();
            if (MaximumSpreadPips > 0 && spread > MaximumSpreadPips)
                return;

            int signal = Bars.Count - 2;
            if (signal <= BreakoutLookbackBars)
                return;

            double barRangePips = (Bars.HighPrices[signal] - Bars.LowPrices[signal]) / Symbol.PipSize;
            if (!double.IsFinite(barRangePips) || barRangePips < MinimumBarRangePips)
                return;
            if (MaximumBarRangePips > 0 && barRangePips > MaximumBarRangePips)
                return;

            double atrPips = GetAtrPips(1);
            if (EnableAtrFilter && atrPips < MinimumAtrPips)
                return;

            int lbStart = signal - BreakoutLookbackBars;
            double refHigh = Bars.HighPrices[lbStart];
            double refLow = Bars.LowPrices[lbStart];
            for (int i = lbStart + 1; i <= signal - 1; i++)
            {
                refHigh = Math.Max(refHigh, Bars.HighPrices[i]);
                refLow = Math.Min(refLow, Bars.LowPrices[i]);
            }

            double buyTrigger = refHigh + BreakoutBufferPips * Symbol.PipSize;
            double sellTrigger = refLow - BreakoutBufferPips * Symbol.PipSize;
            double close = Bars.ClosePrices[signal];
            DateTime signalTime = Bars.OpenTimes[signal];

            if (EnableBuyBreakout && close > buyTrigger)
            {
                double dist = (close - buyTrigger) / Symbol.PipSize;
                if (dist >= MinimumBreakoutDistancePips)
                    TryOpen(TradeType.Buy, signal, signalTime, barRangePips, atrPips, buyTrigger);
            }

            if (EnableSellBreakout && close < sellTrigger)
            {
                double dist = (sellTrigger - close) / Symbol.PipSize;
                if (dist >= MinimumBreakoutDistancePips)
                    TryOpen(TradeType.Sell, signal, signalTime, barRangePips, atrPips, sellTrigger);
            }
        }

        protected override void OnTick()
        {
            RefreshProtection();
            ManagePositions();
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
        }

        private void RefreshProtection()
        {
            if (Server.Time.Date != _day)
            {
                _day = Server.Time.Date;
                _dayStartEquity = Account.Equity;
                _tradesToday = 0;
                _consecutiveLosses = 0;
                _dailyBlocked = false;
            }

            if (Account.Equity > _peakEquity)
                _peakEquity = Account.Equity;

            if (!_dailyBlocked && MaximumDailyLossPercent > 0 && _dayStartEquity > 0)
            {
                double dailyLoss = Math.Max(0, (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0);
                if (dailyLoss >= MaximumDailyLossPercent)
                    _dailyBlocked = true;
            }

            if (!_drawdownBlocked && MaximumEquityDrawdownPercent > 0 && _peakEquity > 0)
            {
                double dd = Math.Max(0, (_peakEquity - Account.Equity) / _peakEquity * 100.0);
                if (dd >= MaximumEquityDrawdownPercent)
                    _drawdownBlocked = true;
            }
        }

        private bool IsSessionAllowed()
        {
            if (!EnableSessionFilter)
                return true;

            int h = Server.Time.Hour;
            if (TradingSessionStartHourUtc == TradingSessionEndHourUtc)
                return true;
            if (TradingSessionStartHourUtc < TradingSessionEndHourUtc)
                return h >= TradingSessionStartHourUtc && h < TradingSessionEndHourUtc;
            return h >= TradingSessionStartHourUtc || h < TradingSessionEndHourUtc;
        }

        private bool PassTradeLimits()
        {
            if (_tradesToday >= MaxTradesPerDay)
                return false;

            if (ConsecutiveLossLimit > 0 && _consecutiveLosses >= ConsecutiveLossLimit)
                return false;

            if (CooldownAfterTradeMinutes > 0 && _lastTradeTime != DateTime.MinValue && (Server.Time - _lastTradeTime).TotalMinutes < CooldownAfterTradeMinutes)
                return false;

            if (CooldownAfterTradeBars > 0 && _lastTradeBar != int.MinValue && Bars.Count - 1 - _lastTradeBar < CooldownAfterTradeBars)
                return false;

            if (CooldownAfterLossMinutes > 0 && _lastLossTime != DateTime.MinValue && (Server.Time - _lastLossTime).TotalMinutes < CooldownAfterLossMinutes)
                return false;

            if (Positions.FindAll(Label, SymbolName).Length >= MaxOpenPositions)
                return false;

            return true;
        }

        private bool PassTrendFilter(TradeType side)
        {
            if (!EnableEmaTrendFilter)
                return true;

            double ema0 = _ema.Result.Last(1);
            double ema1 = _ema.Result.Last(2);
            double close = Bars.ClosePrices.Last(1);
            if (!double.IsFinite(ema0) || !double.IsFinite(ema1) || !double.IsFinite(close))
                return false;

            if (side == TradeType.Buy)
            {
                if (close <= ema0) return false;
                if (RequireEmaSlope && ema0 <= ema1) return false;
            }
            else
            {
                if (close >= ema0) return false;
                if (RequireEmaSlope && ema0 >= ema1) return false;
            }

            return true;
        }

        private void TryOpen(TradeType side, int signalIndex, DateTime signalTime, double barRangePips, double atrPips, double breakoutPrice)
        {
            string key = side + "|" + signalTime.Ticks;
            if (_consumedSignals.Contains(key))
                return;

            _consumedSignals.Add(key);

            if (!PassTrendFilter(side))
                return;

            if (Positions.FindAll(Label, SymbolName).Any(p => p.TradeType == side))
                return;

            double expectedEntry = side == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            double stopPips = CalculateStopPips(side, signalIndex, barRangePips, atrPips, expectedEntry);
            double takePips = CalculateTakePips(stopPips, barRangePips, atrPips);
            if (!double.IsFinite(stopPips) || !double.IsFinite(takePips) || stopPips <= 0 || takePips <= 0)
                return;

            double volume = CalculateVolume(stopPips);
            if (volume <= 0)
                return;

            var result = ExecuteMarketOrder(side, SymbolName, volume, Label, stopPips, takePips, "BarBreakout", false);
            if (!result.IsSuccessful || result.Position == null)
                return;

            var position = result.Position;
            if (!position.StopLoss.HasValue)
            {
                var emergency = ClosePosition(position);
                if (!emergency.IsSuccessful)
                    Print("[CRITICAL] Failed to close unprotected position {0}", position.Id);
                return;
            }

            if (MaximumEntrySlippagePips > 0)
            {
                double slippage = Math.Abs(position.EntryPrice - expectedEntry) / Symbol.PipSize;
                if (slippage > MaximumEntrySlippagePips)
                {
                    Print("[SLIPPAGE] {0:F2} pips above max, closing {1}", slippage, position.Id);
                    ClosePosition(position);
                    return;
                }
            }

            _initialRiskPips[position.Id] = stopPips;
            _tradesToday++;
            _lastTradeTime = Server.Time;
            _lastTradeBar = Bars.Count - 1;
            Print("[OPEN] {0} signal={1:O} breakout={2}", side, signalTime, breakoutPrice);
        }

        private double CalculateStopPips(TradeType side, int signal, double rangePips, double atrPips, double entry)
        {
            double value;
            switch (StopLossMode)
            {
                case BreakoutStopMode.BarRangeMultiple:
                    value = rangePips * BarRangeStopMultiplier;
                    break;
                case BreakoutStopMode.AtrMultiple:
                    value = atrPips * AtrStopMultiplier;
                    break;
                default:
                    double opposite = side == TradeType.Buy
                        ? Bars.LowPrices[signal] - OppositeSideBufferPips * Symbol.PipSize
                        : Bars.HighPrices[signal] + OppositeSideBufferPips * Symbol.PipSize;
                    value = Math.Abs(entry - opposite) / Symbol.PipSize;
                    break;
            }
            return Math.Max(value, GetMinStopPips());
        }

        private double CalculateTakePips(double stopPips, double rangePips, double atrPips)
        {
            double value;
            switch (TakeProfitMode)
            {
                case BreakoutTpMode.BarRangeMultiple:
                    value = rangePips * BarRangeTpMultiplier;
                    break;
                case BreakoutTpMode.AtrMultiple:
                    value = atrPips * AtrTpMultiplier;
                    break;
                default:
                    value = stopPips * RiskRewardRatio;
                    break;
            }
            return Math.Max(value, GetMinTpPips());
        }

        private double CalculateVolume(double stopPips)
        {
            double capital = RiskBase == BreakoutRiskBase.Balance ? Account.Balance : Account.Equity;
            double riskAmount = capital * (RiskPerTradePercent / 100.0);
            double moneyRiskPerUnit = stopPips * Symbol.PipValue;
            if (riskAmount <= 0 || moneyRiskPerUnit <= 0 || !double.IsFinite(moneyRiskPerUnit))
                return 0;

            double raw = riskAmount / moneyRiskPerUnit;
            if (!double.IsFinite(raw) || raw <= 0)
                return 0;
            if (raw < Symbol.VolumeInUnitsMin)
                return 0;

            raw = Math.Min(raw, Symbol.VolumeInUnitsMax);
            double normalized = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (normalized < Symbol.VolumeInUnitsMin)
                normalized = Symbol.VolumeInUnitsMin;
            if (normalized > Symbol.VolumeInUnitsMax)
                normalized = Symbol.VolumeInUnitsMax;
            return Symbol.NormalizeVolumeInUnits(normalized, RoundingMode.Down);
        }

        private void ManagePositions()
        {
            foreach (var p in Positions.FindAll(Label, SymbolName))
            {
                if (!p.StopLoss.HasValue)
                {
                    ClosePosition(p);
                    continue;
                }

                if (!_initialRiskPips.TryGetValue(p.Id, out var initialRisk))
                {
                    initialRisk = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Symbol.PipSize;
                    if (initialRisk > 0) _initialRiskPips[p.Id] = initialRisk;
                }
                if (initialRisk <= 0) continue;

                if (EnableBreakeven && p.Pips >= initialRisk * BreakevenTriggerR)
                {
                    double be = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + BreakevenExtraPips * Symbol.PipSize
                        : p.EntryPrice - BreakevenExtraPips * Symbol.PipSize;
                    TryModifyStop(p, be, "Breakeven");
                }

                if (EnableAtrTrailing)
                {
                    double atr = GetAtrPips(0);
                    if (atr > 0)
                    {
                        double d = atr * AtrTrailMultiplier * Symbol.PipSize;
                        double trail = p.TradeType == TradeType.Buy ? Symbol.Bid - d : Symbol.Ask + d;
                        TryModifyStop(p, trail, "AtrTrail");
                    }
                }

                if (EnableBarTrailing)
                {
                    int i = Bars.Count - 2;
                    int lb = Math.Max(1, BarTrailLookback);
                    if (i > lb)
                    {
                        double proposed;
                        if (p.TradeType == TradeType.Buy)
                        {
                            double low = Bars.LowPrices[i];
                            for (int j = 1; j < lb; j++) low = Math.Min(low, Bars.LowPrices[i - j]);
                            proposed = low - BarTrailBufferPips * Symbol.PipSize;
                        }
                        else
                        {
                            double high = Bars.HighPrices[i];
                            for (int j = 1; j < lb; j++) high = Math.Max(high, Bars.HighPrices[i - j]);
                            proposed = high + BarTrailBufferPips * Symbol.PipSize;
                        }
                        TryModifyStop(p, proposed, "BarTrail");
                    }
                }
            }
        }

        private void TryModifyStop(Position p, double proposed, string reason)
        {
            if (!IsLegalImprovedStop(p, proposed))
                return;

            var oldStop = p.StopLoss;
            var result = ModifyPosition(p, proposed, p.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[MODIFY_FAIL] Id={0} reason={1} err={2}", p.Id, reason, result.Error);
                return;
            }

            if (!p.StopLoss.HasValue && oldStop.HasValue)
            {
                var restore = ModifyPosition(p, oldStop, p.TakeProfit, ProtectionType.Absolute);
                if (!restore.IsSuccessful)
                    Print("[CRITICAL] Failed to restore SL on {0}", p.Id);
                return;
            }

            _managedStopReason[p.Id] = reason;
        }

        private bool IsLegalImprovedStop(Position p, double proposed)
        {
            double minDist = GetMinStopPips() * Symbol.PipSize;
            if (p.TradeType == TradeType.Buy)
            {
                if (proposed >= Symbol.Bid - minDist) return false;
                if (p.StopLoss.HasValue && proposed <= p.StopLoss.Value + Symbol.TickSize * 0.5) return false;
            }
            else
            {
                if (proposed <= Symbol.Ask + minDist) return false;
                if (p.StopLoss.HasValue && proposed >= p.StopLoss.Value - Symbol.TickSize * 0.5) return false;
            }
            return true;
        }

        private double GetMinStopPips()
        {
            return Math.Max(ConvertMinDistanceToPips(Symbol.MinStopLossDistance), Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double GetMinTpPips()
        {
            return Math.Max(ConvertMinDistanceToPips(Symbol.MinTakeProfitDistance), Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double ConvertMinDistanceToPips(double v)
        {
            if (v <= 0) return 0;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips) return v;
            double refPrice = (Symbol.Bid + Symbol.Ask) * 0.5;
            return (refPrice * (v / 100.0)) / Symbol.PipSize;
        }

        private double GetSpreadPips()
        {
            if (Symbol.PipSize <= 0) return double.PositiveInfinity;
            return (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private double GetAtrPips(int i)
        {
            if (Symbol.PipSize <= 0) return 0;
            double value = _atr.Result.Last(i) / Symbol.PipSize;
            return double.IsFinite(value) ? value : 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != Label)
                return;

            string reason = args.Reason.ToString();
            if (args.Reason == PositionCloseReason.StopLoss && _managedStopReason.TryGetValue(p.Id, out var m))
                reason = m + "Stop";

            if (p.NetProfit < 0)
            {
                _consecutiveLosses++;
                _lastLossTime = Server.Time;
            }
            else if (p.NetProfit > 0)
            {
                _consecutiveLosses = 0;
            }

            _initialRiskPips.Remove(p.Id);
            _managedStopReason.Remove(p.Id);
            Print("[EXIT] {0} reason={1} net={2:F2} consecLoss={3}", p.Id, reason, p.NetProfit, _consecutiveLosses);
        }
    }
}
