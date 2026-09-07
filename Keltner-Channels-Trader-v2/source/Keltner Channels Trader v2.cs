using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public enum KeltnerRiskMode
    {
        FixedLots,
        PercentageRisk
    }

    public enum KeltnerRiskBase
    {
        Balance,
        Equity
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class KeltnerChannelsTraderV2 : Robot
    {
        private KeltnerChannels _keltner;
        private AverageTrueRange _atr;
        private ExponentialMovingAverage _ema;
        private DateTime _currentDay;
        private double _dayStartEquity;
        private double _peakEquity;
        private bool _dailyLossBlocked;
        private bool _drawdownBlocked;
        private DateTime _lastEntryTime = DateTime.MinValue;
        private int _lastEntryBarCount = int.MinValue;
        private DateTime _lastProcessedBarTime = DateTime.MinValue;
        private int _tradesToday;
        private readonly Dictionary<int, string> _managedStopReason = new Dictionary<int, string>();
        private readonly Dictionary<int, string> _pendingExitReason = new Dictionary<int, string>();

        [Parameter("Label", DefaultValue = "KeltnerTraderV2_1", Group = "General")]
        public string Label { get; set; }

        [Parameter("Enable Trading", DefaultValue = true, Group = "General")]
        public bool EnableTrading { get; set; }

        [Parameter("Log Diagnostics", DefaultValue = true, Group = "General")]
        public bool LogDiagnostics { get; set; }

        [Parameter("Risk Mode", DefaultValue = KeltnerRiskMode.PercentageRisk, Group = "Risk")]
        public KeltnerRiskMode RiskMode { get; set; }

        [Parameter("Risk Base", DefaultValue = KeltnerRiskBase.Equity, Group = "Risk")]
        public KeltnerRiskBase RiskBase { get; set; }

        [Parameter("Fixed Volume (Lots)", DefaultValue = 0.01, MinValue = 0.0, Group = "Risk")]
        public double FixedVolumeLots { get; set; }

        [Parameter("Risk %", DefaultValue = 0.5, MinValue = 0.01, MaxValue = 100, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, Group = "Risk")]
        public int MaxOpenPositions { get; set; }

        [Parameter("Max Trades Per Day", DefaultValue = 6, MinValue = 1, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Max Spread (pips, 0=off)", DefaultValue = 3.0, MinValue = 0, Group = "Risk")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Daily Loss Limit % (0=off)", DefaultValue = 5.0, MinValue = 0, MaxValue = 100, Group = "Protection")]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Max Drawdown % (0=off)", DefaultValue = 20.0, MinValue = 0, MaxValue = 100, Group = "Protection")]
        public double MaxDrawdownPercent { get; set; }

        [Parameter("Close On Protection", DefaultValue = true, Group = "Protection")]
        public bool CloseOnProtection { get; set; }

        [Parameter("Cooldown Bars", DefaultValue = 1, MinValue = 0, Group = "Limits")]
        public int CooldownBars { get; set; }

        [Parameter("Cooldown Minutes", DefaultValue = 0, MinValue = 0, Group = "Limits")]
        public int CooldownMinutes { get; set; }

        [Parameter("MA Period", DefaultValue = 20, MinValue = 1, Group = "Keltner")]
        public int MAPeriod { get; set; }

        [Parameter("MA Type", DefaultValue = MovingAverageType.Exponential, Group = "Keltner")]
        public MovingAverageType MAType { get; set; }

        [Parameter("ATR Period", DefaultValue = 10, MinValue = 1, Group = "Keltner")]
        public int AtrPeriod { get; set; }

        [Parameter("ATR MA Type", DefaultValue = MovingAverageType.Exponential, Group = "Keltner")]
        public MovingAverageType AtrMAType { get; set; }

        [Parameter("Band Distance", DefaultValue = 2.0, MinValue = 0.1, Group = "Keltner")]
        public double BandDistance { get; set; }

        [Parameter("Use ATR Stop Loss", DefaultValue = true, Group = "Stops")]
        public bool UseAtrStopLoss { get; set; }

        [Parameter("Use ATR Take Profit", DefaultValue = true, Group = "Stops")]
        public bool UseAtrTakeProfit { get; set; }

        [Parameter("Fixed SL (pips)", DefaultValue = 20.0, MinValue = 0.1, Group = "Stops")]
        public double FixedStopLossPips { get; set; }

        [Parameter("Fixed TP (pips)", DefaultValue = 30.0, MinValue = 0.1, Group = "Stops")]
        public double FixedTakeProfitPips { get; set; }

        [Parameter("ATR SL Multiplier", DefaultValue = 1.5, MinValue = 0.1, Group = "Stops")]
        public double AtrStopMultiplier { get; set; }

        [Parameter("ATR TP Multiplier", DefaultValue = 2.25, MinValue = 0.1, Group = "Stops")]
        public double AtrTakeProfitMultiplier { get; set; }

        [Parameter("Minimum Risk Reward", DefaultValue = 1.0, MinValue = 0.1, Group = "Stops")]
        public double MinimumRiskRewardRatio { get; set; }

        [Parameter("Enable Breakeven", DefaultValue = true, Group = "Management")]
        public bool EnableBreakeven { get; set; }

        [Parameter("BE Trigger (R)", DefaultValue = 1.0, MinValue = 0.1, Group = "Management")]
        public double BreakevenTriggerR { get; set; }

        [Parameter("BE Extra (pips)", DefaultValue = 0.2, MinValue = 0.0, Group = "Management")]
        public double BreakevenExtraPips { get; set; }

        [Parameter("Enable ATR Trailing", DefaultValue = false, Group = "Management")]
        public bool EnableAtrTrailing { get; set; }

        [Parameter("ATR Trail Multiplier", DefaultValue = 1.2, MinValue = 0.1, Group = "Management")]
        public double AtrTrailMultiplier { get; set; }

        [Parameter("Enable EMA Trend Filter", DefaultValue = false, Group = "Filters")]
        public bool EnableEmaTrendFilter { get; set; }

        [Parameter("EMA Period", DefaultValue = 100, MinValue = 2, Group = "Filters")]
        public int EmaPeriod { get; set; }

        [Parameter("Require EMA Slope", DefaultValue = false, Group = "Filters")]
        public bool RequireEmaSlope { get; set; }

        [Parameter("Enable ATR Volatility Filter", DefaultValue = false, Group = "Filters")]
        public bool EnableAtrVolatilityFilter { get; set; }

        [Parameter("Minimum ATR (pips)", DefaultValue = 0.0, MinValue = 0.0, Group = "Filters")]
        public double MinimumAtrPips { get; set; }

        [Parameter("Enable Session Filter", DefaultValue = false, Group = "Session")]
        public bool EnableSessionFilter { get; set; }

        [Parameter("Session Start Hour UTC", DefaultValue = 0, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int SessionStartHourUtc { get; set; }

        [Parameter("Session End Hour UTC", DefaultValue = 23, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int SessionEndHourUtc { get; set; }

        protected override void OnStart()
        {
            _keltner = Indicators.KeltnerChannels(MAPeriod, MAType, AtrPeriod, AtrMAType, BandDistance);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);

            _currentDay = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _peakEquity = Account.Equity;
            Positions.Closed += OnPositionClosed;

            Print("[START] Keltner Channels Trader v2.1 | Symbol={0} | TF={1} | Balance={2:F2} | Equity={3:F2}", SymbolName, TimeFrame, Account.Balance, Account.Equity);
            Print("[SYMBOL] PipSize={0} TickSize={1} PipValue={2} TickValue={3} VolMin={4} VolMax={5} VolStep={6} MinSL={7} MinTP={8} MinDistanceType={9}",
                Symbol.PipSize, Symbol.TickSize, Symbol.PipValue, Symbol.TickValue,
                Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep,
                Symbol.MinStopLossDistance, Symbol.MinTakeProfitDistance, Symbol.MinDistanceType);
        }

        protected override void OnBarClosed()
        {
            RefreshProtectionState();

            if (!EnableTrading || _dailyLossBlocked || _drawdownBlocked)
                return;

            int warmup = Math.Max(Math.Max(MAPeriod, AtrPeriod), EmaPeriod) + 5;
            if (Bars.Count < warmup)
                return;

            var currentBarTime = Bars.OpenTimes.Last(0);
            if (currentBarTime == _lastProcessedBarTime)
                return;
            _lastProcessedBarTime = currentBarTime;

            if (!IsSessionAllowed(Server.Time))
                return;

            if (_tradesToday >= MaxTradesPerDay)
                return;

            if (!CooldownSatisfied())
                return;

            var spreadPips = GetSpreadPips();
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
            {
                Log("FILTER", "Spread too high: " + spreadPips.ToString("F2") + " pips");
                return;
            }

            var atrPips = GetAtrPips(0);
            if (EnableAtrVolatilityFilter && atrPips < MinimumAtrPips)
            {
                Log("FILTER", "ATR below threshold: " + atrPips.ToString("F2") + " pips");
                return;
            }

            var close0 = Bars.ClosePrices.Last(0);
            var close1 = Bars.ClosePrices.Last(1);
            var top0 = _keltner.Top.Last(0);
            var top1 = _keltner.Top.Last(1);
            var bottom0 = _keltner.Bottom.Last(0);
            var bottom1 = _keltner.Bottom.Last(1);

            bool bullishBreakout = close0 > top0 && close1 <= top1;
            bool bearishBreakout = close0 < bottom0 && close1 >= bottom1;

            if (bullishBreakout && PassesTrendFilter(TradeType.Buy))
                TryOpen(TradeType.Buy, "KeltnerUpperBreakout");
            else if (bearishBreakout && PassesTrendFilter(TradeType.Sell))
                TryOpen(TradeType.Sell, "KeltnerLowerBreakout");
        }

        protected override void OnTick()
        {
            RefreshProtectionState();
            ManagePositions();
        }

        private void RefreshProtectionState()
        {
            if (Server.Time.Date != _currentDay)
            {
                _currentDay = Server.Time.Date;
                _dayStartEquity = Account.Equity;
                _tradesToday = 0;
                _dailyLossBlocked = false;
                Log("DAY", "New UTC day. DayStartEquity=" + _dayStartEquity.ToString("F2"));
            }

            if (Account.Equity > _peakEquity)
                _peakEquity = Account.Equity;

            if (!_dailyLossBlocked && DailyLossLimitPercent > 0 && _dayStartEquity > 0)
            {
                var dailyLossPct = Math.Max(0, (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0);
                if (dailyLossPct >= DailyLossLimitPercent)
                {
                    _dailyLossBlocked = true;
                    Print("[PROTECTION] Daily loss limit triggered: {0:F2}% >= {1:F2}%", dailyLossPct, DailyLossLimitPercent);
                    if (CloseOnProtection)
                        CloseAllManagedPositions("DailyLossProtection");
                }
            }

            if (!_drawdownBlocked && MaxDrawdownPercent > 0 && _peakEquity > 0)
            {
                var ddPct = Math.Max(0, (_peakEquity - Account.Equity) / _peakEquity * 100.0);
                if (ddPct >= MaxDrawdownPercent)
                {
                    _drawdownBlocked = true;
                    Print("[PROTECTION] Max drawdown triggered: {0:F2}% >= {1:F2}%", ddPct, MaxDrawdownPercent);
                    if (CloseOnProtection)
                        CloseAllManagedPositions("MaxDrawdownProtection");
                }
            }
        }

        private bool IsSessionAllowed(DateTime time)
        {
            if (!EnableSessionFilter)
                return true;

            int hour = time.Hour;
            if (SessionStartHourUtc <= SessionEndHourUtc)
                return hour >= SessionStartHourUtc && hour <= SessionEndHourUtc;

            return hour >= SessionStartHourUtc || hour <= SessionEndHourUtc;
        }

        private bool CooldownSatisfied()
        {
            if (CooldownBars > 0 && _lastEntryBarCount != int.MinValue)
            {
                if (Bars.Count - _lastEntryBarCount <= CooldownBars)
                    return false;
            }

            if (CooldownMinutes > 0 && _lastEntryTime != DateTime.MinValue)
            {
                if ((Server.Time - _lastEntryTime).TotalMinutes < CooldownMinutes)
                    return false;
            }

            return true;
        }

        private bool PassesTrendFilter(TradeType tradeType)
        {
            if (!EnableEmaTrendFilter)
                return true;

            var price = Bars.ClosePrices.Last(0);
            var ema0 = _ema.Result.Last(0);
            var ema1 = _ema.Result.Last(1);

            if (tradeType == TradeType.Buy)
            {
                if (price <= ema0)
                    return false;
                if (RequireEmaSlope && ema0 <= ema1)
                    return false;
            }
            else
            {
                if (price >= ema0)
                    return false;
                if (RequireEmaSlope && ema0 >= ema1)
                    return false;
            }

            return true;
        }

        private void TryOpen(TradeType tradeType, string entryReason)
        {
            var positions = Positions.FindAll(Label, SymbolName);

            if (positions.Any(p => p.TradeType == tradeType))
            {
                Log("ENTRY_SKIP", "Same-direction position already exists");
                return;
            }

            foreach (var opposite in positions.Where(p => p.TradeType != tradeType).ToArray())
            {
                _pendingExitReason[opposite.Id] = "SignalReversal";
                var closeResult = ClosePosition(opposite);
                if (!closeResult.IsSuccessful)
                {
                    Print("[CLOSE_FAIL] Position={0} Error={1}", opposite.Id, closeResult.Error);
                    _pendingExitReason.Remove(opposite.Id);
                    return;
                }
            }

            positions = Positions.FindAll(Label, SymbolName);
            if (positions.Length >= MaxOpenPositions)
            {
                Log("ENTRY_SKIP", "MaxOpenPositions reached");
                return;
            }

            double stopLossPips = CalculateStopLossPips();
            double takeProfitPips = CalculateTakeProfitPips(stopLossPips);

            if (!double.IsFinite(stopLossPips) || !double.IsFinite(takeProfitPips) || stopLossPips <= 0 || takeProfitPips <= 0)
            {
                Print("[ENTRY_SKIP] Invalid SL/TP distances SL={0} TP={1}", stopLossPips, takeProfitPips);
                return;
            }

            var rr = takeProfitPips / stopLossPips;
            if (rr < MinimumRiskRewardRatio)
            {
                Print("[ENTRY_SKIP] RR {0:F2} below minimum {1:F2}", rr, MinimumRiskRewardRatio);
                return;
            }

            var volume = CalculateVolumeInUnits(stopLossPips);
            if (volume <= 0)
                return;

            Print("[ENTRY] Reason={0} Side={1} Spread={2:F2} ATR={3:F2} SL={4:F2} TP={5:F2} RR={6:F2} Volume={7}",
                entryReason, tradeType, GetSpreadPips(), GetAtrPips(0), stopLossPips, takeProfitPips, rr, volume);

            var result = ExecuteMarketOrder(tradeType, SymbolName, volume, Label, stopLossPips, takeProfitPips, entryReason, false);
            if (!result.IsSuccessful)
            {
                Print("[ENTRY_FAIL] Side={0} Error={1}", tradeType, result.Error);
                return;
            }

            var position = result.Position;
            if (position == null)
            {
                Print("[ENTRY_FAIL] TradeResult successful but Position is null");
                return;
            }

            if (!position.StopLoss.HasValue)
            {
                Print("[CRITICAL] Position {0} opened without StopLoss. Closing immediately.", position.Id);
                _pendingExitReason[position.Id] = "MissingInitialStopLoss";
                var emergencyClose = ClosePosition(position);
                if (!emergencyClose.IsSuccessful)
                    Print("[CRITICAL] Emergency close failed for position {0}: {1}", position.Id, emergencyClose.Error);
                return;
            }

            _tradesToday++;
            _lastEntryTime = Server.Time;
            _lastEntryBarCount = Bars.Count;
            Print("[OPEN_OK] Id={0} Side={1} Entry={2} SL={3} TP={4} Volume={5}", position.Id, position.TradeType, position.EntryPrice, position.StopLoss, position.TakeProfit, position.VolumeInUnits);
        }

        private double CalculateStopLossPips()
        {
            double value = UseAtrStopLoss ? GetAtrPips(0) * AtrStopMultiplier : FixedStopLossPips;
            return Math.Max(value, GetMinimumStopDistancePips());
        }

        private double CalculateTakeProfitPips(double stopLossPips)
        {
            double value = UseAtrTakeProfit ? GetAtrPips(0) * AtrTakeProfitMultiplier : FixedTakeProfitPips;
            value = Math.Max(value, GetMinimumTakeProfitDistancePips());
            value = Math.Max(value, stopLossPips * MinimumRiskRewardRatio);
            return value;
        }

        private double CalculateVolumeInUnits(double stopLossPips)
        {
            double rawVolume;
            if (RiskMode == KeltnerRiskMode.FixedLots)
            {
                rawVolume = Symbol.QuantityToVolumeInUnits(FixedVolumeLots);
            }
            else
            {
                var capital = RiskBase == KeltnerRiskBase.Balance ? Account.Balance : Account.Equity;
                var riskAmount = capital * (RiskPercent / 100.0);
                var moneyRiskPerUnit = stopLossPips * Symbol.PipValue;
                if (riskAmount <= 0 || moneyRiskPerUnit <= 0 || !double.IsFinite(moneyRiskPerUnit))
                {
                    Print("[VOLUME_FAIL] Invalid risk sizing inputs capital={0} riskAmount={1} PipValue={2} SL={3}", capital, riskAmount, Symbol.PipValue, stopLossPips);
                    return 0;
                }
                rawVolume = riskAmount / moneyRiskPerUnit;
            }

            if (!double.IsFinite(rawVolume) || rawVolume <= 0)
                return 0;

            rawVolume = Math.Min(rawVolume, Symbol.VolumeInUnitsMax);
            var normalized = Symbol.NormalizeVolumeInUnits(rawVolume, RoundingMode.Down);
            if (normalized < Symbol.VolumeInUnitsMin)
                normalized = Symbol.VolumeInUnitsMin;
            if (normalized > Symbol.VolumeInUnitsMax)
                normalized = Symbol.VolumeInUnitsMax;

            normalized = Symbol.NormalizeVolumeInUnits(normalized, RoundingMode.Down);
            Print("[VOLUME] Raw={0} Normalized={1} Min={2} Max={3} Step={4}", rawVolume, normalized, Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep);
            return normalized;
        }

        private void ManagePositions()
        {
            foreach (var position in Positions.FindAll(Label, SymbolName))
            {
                if (!position.StopLoss.HasValue)
                {
                    Print("[CRITICAL] Managed position {0} has no StopLoss. Closing immediately.", position.Id);
                    _pendingExitReason[position.Id] = "MissingStopLossDetected";
                    var emergencyClose = ClosePosition(position);
                    if (!emergencyClose.IsSuccessful)
                        Print("[CRITICAL] Emergency close failed for position {0}: {1}", position.Id, emergencyClose.Error);
                    continue;
                }

                var originalRiskPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize;
                if (originalRiskPips <= 0 || !double.IsFinite(originalRiskPips))
                    continue;

                if (EnableBreakeven && position.Pips >= originalRiskPips * BreakevenTriggerR)
                {
                    double bePrice = position.TradeType == TradeType.Buy
                        ? position.EntryPrice + BreakevenExtraPips * Symbol.PipSize
                        : position.EntryPrice - BreakevenExtraPips * Symbol.PipSize;

                    TryModifyStop(position, bePrice, "Breakeven");
                }

                if (EnableAtrTrailing)
                {
                    var atrPips = GetAtrPips(0);
                    if (atrPips > 0)
                    {
                        var distance = atrPips * AtrTrailMultiplier * Symbol.PipSize;
                        double trailPrice = position.TradeType == TradeType.Buy
                            ? Symbol.Bid - distance
                            : Symbol.Ask + distance;

                        TryModifyStop(position, trailPrice, "Trailing");
                    }
                }
            }
        }

        private void TryModifyStop(Position position, double proposedStop, string reason)
        {
            if (!IsLegalImprovedStop(position, proposedStop))
                return;

            var oldStop = position.StopLoss;
            var takeProfit = position.TakeProfit;
            var result = ModifyPosition(position, proposedStop, takeProfit, ProtectionType.Absolute);

            if (!result.IsSuccessful)
            {
                Print("[MODIFY_FAIL] Id={0} Reason={1} OldSL={2} ProposedSL={3} TP={4} Error={5}", position.Id, reason, oldStop, proposedStop, takeProfit, result.Error);
                return;
            }

            if (!position.StopLoss.HasValue)
            {
                Print("[CRITICAL] Modify returned success but SL became null. Attempting restore to {0}", oldStop);
                if (oldStop.HasValue)
                {
                    var restore = ModifyPosition(position, oldStop, takeProfit, ProtectionType.Absolute);
                    if (!restore.IsSuccessful)
                        Print("[CRITICAL] SL restore failed Id={0} Error={1}", position.Id, restore.Error);
                }
                return;
            }

            _managedStopReason[position.Id] = reason;
            Print("[MODIFY_OK] Id={0} Reason={1} NewSL={2} TP={3}", position.Id, reason, position.StopLoss, position.TakeProfit);
        }

        private bool IsLegalImprovedStop(Position position, double proposedStop)
        {
            var minDistancePips = GetMinimumStopDistancePips();
            var minDistancePrice = minDistancePips * Symbol.PipSize;

            if (position.TradeType == TradeType.Buy)
            {
                if (proposedStop >= Symbol.Bid - minDistancePrice)
                    return false;
                if (position.StopLoss.HasValue && proposedStop <= position.StopLoss.Value + Symbol.TickSize * 0.5)
                    return false;
            }
            else
            {
                if (proposedStop <= Symbol.Ask + minDistancePrice)
                    return false;
                if (position.StopLoss.HasValue && proposedStop >= position.StopLoss.Value - Symbol.TickSize * 0.5)
                    return false;
            }

            return true;
        }

        private double GetMinimumStopDistancePips()
        {
            double brokerMin = ConvertMinDistanceToPips(Symbol.MinStopLossDistance);
            return Math.Max(brokerMin, Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double GetMinimumTakeProfitDistancePips()
        {
            double brokerMin = ConvertMinDistanceToPips(Symbol.MinTakeProfitDistance);
            return Math.Max(brokerMin, Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double ConvertMinDistanceToPips(double minimumDistance)
        {
            if (minimumDistance <= 0)
                return 0;

            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return minimumDistance;

            var referencePrice = (Symbol.Bid + Symbol.Ask) * 0.5;
            var priceDistance = referencePrice * (minimumDistance / 100.0);
            return priceDistance / Symbol.PipSize;
        }

        private double GetAtrPips(int index)
        {
            var value = _atr.Result.Last(index) / Symbol.PipSize;
            return double.IsFinite(value) ? value : 0;
        }

        private double GetSpreadPips()
        {
            if (Symbol.PipSize <= 0)
                return double.PositiveInfinity;
            return (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private void CloseAllManagedPositions(string reason)
        {
            foreach (var position in Positions.FindAll(Label, SymbolName).ToArray())
            {
                _pendingExitReason[position.Id] = reason;
                var result = ClosePosition(position);
                if (!result.IsSuccessful)
                {
                    Print("[CLOSE_FAIL] Protection close failed Id={0} Reason={1} Error={2}", position.Id, reason, result.Error);
                    _pendingExitReason.Remove(position.Id);
                }
            }
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p.Label != Label || p.SymbolName != SymbolName)
                return;

            string exitReason;
            if (_pendingExitReason.TryGetValue(p.Id, out var pending))
            {
                exitReason = pending;
                _pendingExitReason.Remove(p.Id);
            }
            else if (args.Reason == PositionCloseReason.StopLoss && _managedStopReason.TryGetValue(p.Id, out var managed))
            {
                exitReason = managed + "Stop";
            }
            else
            {
                exitReason = args.Reason.ToString();
            }

            _managedStopReason.Remove(p.Id);

            Print("[EXIT] Id={0} Side={1} ExitReason={2} Gross={3:F2} Net={4:F2} Pips={5:F2} Entry={6} ExitTime={7:O}",
                p.Id, p.TradeType, exitReason, p.GrossProfit, p.NetProfit, p.Pips, p.EntryPrice, Server.Time);
        }

        private void Log(string category, string message)
        {
            if (LogDiagnostics)
                Print("[{0}] {1}", category, message);
        }
    }
}
