using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_v1 : Robot
    {
        private const string BotLabel = "CumulativeDeltaScalper-EURUSD-v1";
        private const int TrendEmaPeriod = 50;
        private const int TrendAdxPeriod = 14;

        [Parameter("Window Size", Group = "Delta", DefaultValue = 12, MinValue = 3, MaxValue = 200)]
        public int WindowSize { get; set; }

        [Parameter("Delta Threshold", Group = "Delta", DefaultValue = 280, MinValue = 1, MaxValue = 100000)]
        public int DeltaThreshold { get; set; }

        [Parameter("Min Confirmations", Group = "Delta", DefaultValue = 4, MinValue = 1, MaxValue = 5)]
        public int MinConfirmations { get; set; }

        [Parameter("Trend TimeFrame", Group = "Filters", DefaultValue = "Hour")]
        public TimeFrame TrendTimeFrame { get; set; }

        [Parameter("EMA Slope Bars", Group = "Filters", DefaultValue = 3, MinValue = 1, MaxValue = 20)]
        public int EmaSlopeBars { get; set; }

        [Parameter("ADX Threshold", Group = "Filters", DefaultValue = 18.0, MinValue = 0.0, MaxValue = 100.0, Step = 0.5)]
        public double AdxThreshold { get; set; }

        [Parameter("Max Spread (pips)", Group = "Filters", DefaultValue = 1.2, MinValue = 0.1, MaxValue = 50.0, Step = 0.1)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Spread Avg Multiplier", Group = "Filters", DefaultValue = 1.3, MinValue = 1.0, MaxValue = 5.0, Step = 0.1)]
        public double SpreadAverageMultiplier { get; set; }

        [Parameter("Spread History Size", Group = "Filters", DefaultValue = 20, MinValue = 2, MaxValue = 200)]
        public int SpreadHistorySize { get; set; }

        [Parameter("Min ATR (pips)", Group = "Filters", DefaultValue = 2.5, MinValue = 0.0, MaxValue = 200.0, Step = 0.1)]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR (pips)", Group = "Filters", DefaultValue = 18.0, MinValue = 0.0, MaxValue = 200.0, Step = 0.1)]
        public double MaxAtrPips { get; set; }

        [Parameter("ATR Period", Group = "Trade", DefaultValue = 14, MinValue = 2, MaxValue = 100)]
        public int AtrPeriod { get; set; }

        [Parameter("SL ATR Multiplier", Group = "Trade", DefaultValue = 1.4, MinValue = 0.1, MaxValue = 20.0, Step = 0.1)]
        public double StopLossAtrMultiplier { get; set; }

        [Parameter("TP ATR Multiplier", Group = "Trade", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 20.0, Step = 0.1)]
        public double TakeProfitAtrMultiplier { get; set; }

        [Parameter("Minimum SL (pips)", Group = "Trade", DefaultValue = 4.0, MinValue = 0.1, MaxValue = 500.0, Step = 0.1)]
        public double MinimumStopLossPips { get; set; }

        [Parameter("Minimum TP (pips)", Group = "Trade", DefaultValue = 4.0, MinValue = 0.1, MaxValue = 500.0, Step = 0.1)]
        public double MinimumTakeProfitPips { get; set; }

        [Parameter("Minimum Reward/Risk", Group = "Trade", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 10.0, Step = 0.1)]
        public double MinimumRewardRiskRatio { get; set; }

        [Parameter("Fixed Money Risk", Group = "Risk", DefaultValue = 25.0, MinValue = 0.01, MaxValue = 1000000.0, Step = 0.01)]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Max Daily Loss Money", Group = "Risk", DefaultValue = 75.0, MinValue = 0.0, MaxValue = 1000000.0, Step = 0.01)]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Max Daily Loss Percent", Group = "Risk", DefaultValue = 2.5, MinValue = 0.0, MaxValue = 100.0, Step = 0.1)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Daily Profit Target", Group = "Risk", DefaultValue = 100.0, MinValue = 0.0, MaxValue = 1000000.0, Step = 0.01)]
        public double DailyProfitTargetMoney { get; set; }

        [Parameter("Max Consecutive Losses", Group = "Risk", DefaultValue = 3, MinValue = 0, MaxValue = 50)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Cooldown (minutes)", Group = "Risk", DefaultValue = 30, MinValue = 0, MaxValue = 1440)]
        public int CooldownMinutes { get; set; }

        [Parameter("Use Breakeven", Group = "Risk", DefaultValue = true)]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven Trigger (R)", Group = "Risk", DefaultValue = 1.0, MinValue = 0.2, MaxValue = 10.0, Step = 0.1)]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Offset (pips)", Group = "Risk", DefaultValue = 0.1, MinValue = 0.0, MaxValue = 50.0, Step = 0.1)]
        public double BreakevenOffsetPips { get; set; }

        [Parameter("Max Hold Minutes", Group = "Risk", DefaultValue = 45, MinValue = 0, MaxValue = 1440)]
        public int MaxHoldMinutes { get; set; }

        [Parameter("Debug Logging", Group = "Diagnostics", DefaultValue = false)]
        public bool DebugLogging { get; set; }

        private AverageTrueRange _atr;
        private Bars _trendBars;
        private ExponentialMovingAverage _trendEma;
        private DirectionalMovementSystem _trendDms;

        private int[] _deltaBuffer;
        private int _deltaIndex;
        private int _deltaCount;
        private int _previousCumulativeDelta;
        private int _currentCumulativeDelta;
        private int _upticks;
        private int _downticks;
        private double _previousBid;

        private double[] _spreadHistory;
        private int _spreadIndex;
        private int _spreadCount;

        private DateTime _riskDate;
        private double _dayStartBalance;
        private double _dailyClosedNetProfit;
        private int _consecutiveLosses;
        private DateTime _lastManagedExitTime = DateTime.MinValue;
        private readonly Dictionary<long, double> _initialRiskPips = new Dictionary<long, double>();
        private bool _haltedForDailyRisk;

        protected override void OnStart()
        {
            try
            {
                ValidateStartup();

                _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
                _trendBars = MarketData.GetBars(TrendTimeFrame);
                _trendEma = Indicators.ExponentialMovingAverage(_trendBars.ClosePrices, TrendEmaPeriod);
                _trendDms = Indicators.DirectionalMovementSystem(_trendBars, TrendAdxPeriod);

                _deltaBuffer = new int[WindowSize];
                _spreadHistory = new double[SpreadHistorySize];
                _previousBid = Symbol.Bid;

                Positions.Closed += OnPositionsClosed;

                ResetDailyStats(true);
                RestoreManagedPositionState();
                LogInfo("Started on {0} {1}. Allowed chart timeframes: M1/M5/M15/M30. One-position mode enabled.", SymbolName, TimeFrame);
            }
            catch (Exception ex)
            {
                Print("[START_ERROR] {0}", ex.Message);
                Stop();
            }
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionsClosed;
        }

        protected override void OnTick()
        {
            try
            {
                ResetDailyStats(false);
                ProcessTickDelta();
                EnforceSingleManagedPosition();
                ManageOpenPosition();
            }
            catch (Exception ex)
            {
                Print("[TICK_ERROR] {0}", ex.Message);
            }
        }

        protected override void OnBarClosed()
        {
            try
            {
                ResetDailyStats(false);
                FinalizeBarDelta();
                EnforceSingleManagedPosition();

                if (HasManagedPosition())
                    return;

                if (!CanOpenNewTrade(out var blockedReason))
                {
                    LogDebug("Entry blocked: {0}", blockedReason);
                    return;
                }

                var signal = EvaluateSignal();
                if (signal == null)
                    return;

                ExecuteEntry(signal.Value);
            }
            catch (Exception ex)
            {
                Print("[BAR_ERROR] {0}", ex.Message);
            }
        }

        private void ValidateStartup()
        {
            if (!string.Equals(SymbolName, "EURUSD", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("This build is restricted to EURUSD.");

            if (!IsAllowedChartTimeFrame())
                throw new ArgumentException("Allowed chart timeframes are M1, M5, M15, and M30 only.");

            if (WindowSize < 3)
                throw new ArgumentException("Window Size must be at least 3.");
            if (DeltaThreshold <= 0)
                throw new ArgumentException("Delta Threshold must be positive.");
            if (AtrPeriod < 2 || StopLossAtrMultiplier <= 0 || TakeProfitAtrMultiplier <= 0)
                throw new ArgumentException("ATR parameters are invalid.");
            if (MinimumStopLossPips <= 0 || MinimumTakeProfitPips <= 0)
                throw new ArgumentException("SL/TP minimums must be positive.");
            if (FixedMoneyRisk <= 0)
                throw new ArgumentException("Fixed Money Risk must be positive.");
            if (SpreadHistorySize < 2)
                throw new ArgumentException("Spread History Size must be at least 2.");
            if (MinConfirmations < 1 || MinConfirmations > 5)
                throw new ArgumentException("Min Confirmations must be between 1 and 5.");
        }

        private bool IsAllowedChartTimeFrame()
        {
            return TimeFrame == cAlgo.API.TimeFrame.Minute
                || TimeFrame == cAlgo.API.TimeFrame.Minute5
                || TimeFrame == cAlgo.API.TimeFrame.Minute15
                || TimeFrame == cAlgo.API.TimeFrame.Minute30;
        }

        private void ProcessTickDelta()
        {
            var bid = Symbol.Bid;
            if (bid > _previousBid)
                _upticks++;
            else if (bid < _previousBid)
                _downticks++;

            _previousBid = bid;
        }

        private void FinalizeBarDelta()
        {
            var candleDelta = _upticks - _downticks;
            _deltaBuffer[_deltaIndex] = candleDelta;
            _deltaIndex = (_deltaIndex + 1) % _deltaBuffer.Length;
            if (_deltaCount < _deltaBuffer.Length)
                _deltaCount++;

            var spreadPips = GetSpreadPips();
            _spreadHistory[_spreadIndex] = spreadPips;
            _spreadIndex = (_spreadIndex + 1) % _spreadHistory.Length;
            if (_spreadCount < _spreadHistory.Length)
                _spreadCount++;

            _previousCumulativeDelta = _currentCumulativeDelta;
            _currentCumulativeDelta = CalculateCumulativeDelta();
            _upticks = 0;
            _downticks = 0;
            LogDebug("Bar delta={0}, cumDelta={1}, spreadPips={2:F2}", candleDelta, _currentCumulativeDelta, spreadPips);
        }

        private TradeType? EvaluateSignal()
        {
            if (_deltaCount < WindowSize)
                return null;
            if (Bars.Count < AtrPeriod + 5)
                return null;
            if (_trendBars.Count < Math.Max(TrendEmaPeriod, TrendAdxPeriod) + EmaSlopeBars + 5)
                return null;

            var direction = 0;
            if (_previousCumulativeDelta <= DeltaThreshold && _currentCumulativeDelta > DeltaThreshold)
                direction = 1;
            else if (_previousCumulativeDelta >= -DeltaThreshold && _currentCumulativeDelta < -DeltaThreshold)
                direction = -1;
            if (direction == 0)
                return null;

            var confirmations = 0;
            if (CheckMomentumAlignment(direction))
                confirmations++;
            if (CheckTrendEma(direction))
                confirmations++;
            if (CheckTrendSlope(direction))
                confirmations++;
            if (CheckAdx())
                confirmations++;
            if (CheckSpread())
                confirmations++;

            LogDebug("Signal direction={0}, confirmations={1}", direction, confirmations);
            if (confirmations < MinConfirmations)
                return null;

            return direction > 0 ? TradeType.Buy : TradeType.Sell;
        }

        private int CalculateCumulativeDelta()
        {
            var sum = 0;
            for (var i = 0; i < _deltaCount; i++)
                sum += _deltaBuffer[i];
            return sum;
        }

        private int[] GetOrderedDeltas()
        {
            var result = new int[_deltaCount];
            var start = _deltaCount >= _deltaBuffer.Length ? _deltaIndex : 0;
            for (var i = 0; i < _deltaCount; i++)
                result[i] = _deltaBuffer[(start + i) % _deltaBuffer.Length];
            return result;
        }

        private bool CheckMomentumAlignment(int direction)
        {
            var deltas = GetOrderedDeltas();
            if (deltas.Length < 3)
                return false;

            for (var i = deltas.Length - 3; i < deltas.Length; i++)
            {
                if (direction > 0 && deltas[i] <= 0)
                    return false;
                if (direction < 0 && deltas[i] >= 0)
                    return false;
            }

            return true;
        }

        private bool CheckTrendEma(int direction)
        {
            var ema = _trendEma.Result.Last(1);
            var close = Bars.ClosePrices.Last(1);
            return direction > 0 ? close > ema : close < ema;
        }

        private bool CheckTrendSlope(int direction)
        {
            var newest = _trendEma.Result.Last(1);
            var oldest = _trendEma.Result.Last(1 + EmaSlopeBars);
            var slope = newest.CompareTo(oldest);
            return direction > 0 ? slope > 0 : slope < 0;
        }

        private bool CheckAdx()
        {
            return _trendDms.ADX.Last(1) >= AdxThreshold;
        }

        private bool CheckSpread()
        {
            var spreadPips = GetSpreadPips();
            if (spreadPips > MaxSpreadPips)
                return false;

            var average = GetAverageSpreadPips();
            return average <= 0 || spreadPips <= average * SpreadAverageMultiplier;
        }

        private bool CanOpenNewTrade(out string reason)
        {
            if (_haltedForDailyRisk)
            {
                reason = "Daily risk halt active";
                return false;
            }

            if (HasAnySymbolPosition())
            {
                reason = "Another EURUSD position already exists; hedging and multi-position entries are disabled";
                return false;
            }

            if (MaxConsecutiveLosses > 0 && _consecutiveLosses >= MaxConsecutiveLosses)
            {
                reason = "Consecutive loss cap reached";
                return false;
            }

            if (CooldownMinutes > 0 && _lastManagedExitTime != DateTime.MinValue && Server.Time - _lastManagedExitTime < TimeSpan.FromMinutes(CooldownMinutes))
            {
                reason = "Cooldown active";
                return false;
            }

            var atrPips = GetAtrPips();
            if (atrPips < MinAtrPips)
            {
                reason = "ATR below minimum";
                return false;
            }
            if (MaxAtrPips > 0 && atrPips > MaxAtrPips)
            {
                reason = "ATR above maximum";
                return false;
            }

            var spreadPips = GetSpreadPips();
            if (spreadPips > MaxSpreadPips)
            {
                reason = "Spread above maximum";
                return false;
            }

            if (DailyProfitTargetMoney > 0 && GetDailyNetProfit() >= DailyProfitTargetMoney)
            {
                _haltedForDailyRisk = true;
                reason = "Daily profit target reached";
                return false;
            }

            var dailyLossMoney = -Math.Min(GetDailyNetProfit(), 0);
            if (MaxDailyLossMoney > 0 && dailyLossMoney >= MaxDailyLossMoney)
            {
                _haltedForDailyRisk = true;
                reason = "Daily loss money limit reached";
                return false;
            }

            if (MaxDailyLossPercent > 0 && _dayStartBalance > 0)
            {
                var lossPercent = dailyLossMoney / _dayStartBalance * 100.0;
                if (lossPercent >= MaxDailyLossPercent)
                {
                    _haltedForDailyRisk = true;
                    reason = "Daily loss percent limit reached";
                    return false;
                }
            }

            reason = string.Empty;
            return true;
        }

        private void ExecuteEntry(TradeType tradeType)
        {
            var stopLossPips = CalculateStopLossPips();
            var takeProfitPips = CalculateTakeProfitPips(stopLossPips);
            if (!IsFinitePositive(stopLossPips) || !IsFinitePositive(takeProfitPips))
            {
                Print("[ENTRY_SKIP] Invalid SL/TP distances. SL={0}, TP={1}", stopLossPips, takeProfitPips);
                return;
            }

            var volumeInUnits = CalculateVolumeInUnits(stopLossPips);
            if (volumeInUnits <= 0)
            {
                Print("[ENTRY_SKIP] Volume check rejected trade for broker min/max/step or risk constraints.");
                return;
            }

            var result = ExecuteMarketOrder(tradeType, SymbolName, volumeInUnits, BotLabel, stopLossPips, takeProfitPips);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ENTRY_FAIL] {0}", result.Error);
                return;
            }

            var position = result.Position;
            if (!position.StopLoss.HasValue || !position.TakeProfit.HasValue)
            {
                Print("[CRITICAL] Position {0} opened without mandatory SL/TP. Closing immediately.", position.Id);
                ClosePosition(position);
                return;
            }

            _initialRiskPips[position.Id] = stopLossPips;
            LogInfo("[OPEN] {0} Volume={1} SL={2:F1} TP={3:F1}", tradeType, volumeInUnits, stopLossPips, takeProfitPips);
        }

        private double CalculateStopLossPips()
        {
            return Math.Max(GetMinimumStopDistancePips(), Math.Max(MinimumStopLossPips, GetAtrPips() * StopLossAtrMultiplier));
        }

        private double CalculateTakeProfitPips(double stopLossPips)
        {
            var atrTarget = Math.Max(GetMinimumTakeProfitDistancePips(), Math.Max(MinimumTakeProfitPips, GetAtrPips() * TakeProfitAtrMultiplier));
            return Math.Max(atrTarget, stopLossPips * MinimumRewardRiskRatio);
        }

        private double CalculateVolumeInUnits(double stopLossPips)
        {
            var moneyRiskPerUnit = stopLossPips * Symbol.PipValue;
            if (!IsFinitePositive(moneyRiskPerUnit))
            {
                Print("[VOLUME_FAIL] Invalid money risk per unit. PipValue={0}, SL={1}", Symbol.PipValue, stopLossPips);
                return 0;
            }

            var rawVolume = FixedMoneyRisk / moneyRiskPerUnit;
            if (!IsFinitePositive(rawVolume))
                return 0;

            if (rawVolume > Symbol.VolumeInUnitsMax)
                rawVolume = Symbol.VolumeInUnitsMax;

            var normalized = Symbol.NormalizeVolumeInUnits(rawVolume, RoundingMode.Down);
            if (rawVolume < Symbol.VolumeInUnitsMin)
            {
                Print("[VOLUME_SKIP] Requested {0:F2} units is below broker minimum {1}.", rawVolume, Symbol.VolumeInUnitsMin);
                return 0;
            }

            if (normalized < Symbol.VolumeInUnitsMin || normalized > Symbol.VolumeInUnitsMax)
            {
                Print("[VOLUME_SKIP] Normalized volume {0} outside broker range [{1}, {2}].", normalized, Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax);
                return 0;
            }

            var renormalized = Symbol.NormalizeVolumeInUnits(normalized, RoundingMode.Down);
            if (Math.Abs(renormalized - normalized) > Symbol.VolumeInUnitsStep)
            {
                Print("[VOLUME_SKIP] Broker step normalization mismatch. Requested={0} Normalized={1} Renormalized={2}", rawVolume, normalized, renormalized);
                return 0;
            }

            LogDebug("Volume raw={0:F2}, normalized={1}, brokerMin={2}, brokerMax={3}, brokerStep={4}", rawVolume, normalized, Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep);
            return normalized;
        }

        private void ManageOpenPosition()
        {
            var position = GetManagedPosition();
            if (position == null)
                return;

            if (!position.StopLoss.HasValue || !position.TakeProfit.HasValue)
            {
                Print("[CRITICAL] Managed position {0} missing mandatory SL/TP. Closing immediately.", position.Id);
                ClosePosition(position);
                return;
            }

            if (MaxHoldMinutes > 0 && Server.Time - position.EntryTime >= TimeSpan.FromMinutes(MaxHoldMinutes))
            {
                CloseManagedPosition(position, "MaxHoldMinutes");
                return;
            }

            if (UseBreakeven)
                TryApplyBreakeven(position);

            if (RiskLimitBreached())
                CloseManagedPosition(position, "DailyRiskLimit");
        }

        private void TryApplyBreakeven(Position position)
        {
            if (!_initialRiskPips.TryGetValue(position.Id, out var initialRiskPips) || !IsFinitePositive(initialRiskPips))
                initialRiskPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize;

            if (!IsFinitePositive(initialRiskPips) || position.Pips < initialRiskPips * BreakevenTriggerR)
                return;

            var offset = BreakevenOffsetPips * Symbol.PipSize;
            var targetStop = position.TradeType == TradeType.Buy
                ? position.EntryPrice + offset
                : position.EntryPrice - offset;

            var currentStop = position.StopLoss.Value;
            var shouldModify = position.TradeType == TradeType.Buy
                ? targetStop > currentStop
                : targetStop < currentStop;

            if (!shouldModify)
                return;

            var modify = ModifyPosition(position, targetStop, position.TakeProfit, ProtectionType.Absolute);
            if (modify.IsSuccessful)
                LogDebug("Breakeven applied to position {0} at {1}", position.Id, targetStop);
        }

        private void CloseManagedPosition(Position position, string reason)
        {
            var result = ClosePosition(position);
            if (result.IsSuccessful)
                LogInfo("[CLOSE] Position={0} Reason={1}", position.Id, reason);
            else
                Print("[CLOSE_FAIL] Position={0} Reason={1} Error={2}", position.Id, reason, result.Error);
        }

        private void EnforceSingleManagedPosition()
        {
            var managedPositions = Positions.FindAll(BotLabel, SymbolName).OrderBy(p => p.EntryTime).ToArray();
            if (managedPositions.Length <= 1)
                return;

            for (var i = 1; i < managedPositions.Length; i++)
            {
                Print("[CRITICAL] Extra managed position {0} detected. Closing to enforce single-position mode.", managedPositions[i].Id);
                ClosePosition(managedPositions[i]);
            }
        }

        private void ResetDailyStats(bool force)
        {
            var currentDate = Server.Time.Date;
            if (!force && _riskDate == currentDate)
                return;

            _riskDate = currentDate;
            _dayStartBalance = Account.Balance;
            _dailyClosedNetProfit = 0;
            _haltedForDailyRisk = false;
            _consecutiveLosses = 0;
            _initialRiskPips.Clear();

            foreach (var trade in History)
            {
                if (!string.Equals(trade.SymbolName, SymbolName, StringComparison.OrdinalIgnoreCase))
                    continue;
                if (!string.Equals(trade.Label, BotLabel, StringComparison.Ordinal))
                    continue;
                if (trade.ClosingTime < currentDate)
                    continue;

                _dailyClosedNetProfit += trade.NetProfit;
                if (trade.NetProfit < 0)
                    _consecutiveLosses++;
                else if (trade.NetProfit > 0)
                    _consecutiveLosses = 0;
            }

            LogDebug("Daily stats reset. DayStartBalance={0}, DailyClosedPnL={1}, ConsecutiveLosses={2}", _dayStartBalance, _dailyClosedNetProfit, _consecutiveLosses);
        }

        private void RestoreManagedPositionState()
        {
            var position = GetManagedPosition();
            if (position == null)
                return;

            var initialRisk = position.StopLoss.HasValue
                ? Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize
                : 0;

            if (IsFinitePositive(initialRisk))
                _initialRiskPips[position.Id] = initialRisk;

            LogInfo("[RESTORE] Position={0} EntryTime={1:o} InitialRiskPips={2:F2}", position.Id, position.EntryTime, initialRisk);
        }

        private void OnPositionsClosed(PositionClosedEventArgs args)
        {
            var position = args.Position;
            if (!string.Equals(position.SymbolName, SymbolName, StringComparison.OrdinalIgnoreCase))
                return;
            if (!string.Equals(position.Label, BotLabel, StringComparison.Ordinal))
                return;

            _lastManagedExitTime = Server.Time;
            _dailyClosedNetProfit += position.NetProfit;
            if (position.NetProfit < 0)
                _consecutiveLosses++;
            else if (position.NetProfit > 0)
                _consecutiveLosses = 0;

            _initialRiskPips.Remove(position.Id);
            LogInfo("[EXIT] Position={0} NetProfit={1:F2} ConsecutiveLosses={2} DailyPnL={3:F2}", position.Id, position.NetProfit, _consecutiveLosses, _dailyClosedNetProfit);
        }

        private bool RiskLimitBreached()
        {
            var netProfit = GetDailyNetProfit();
            var dailyLossMoney = -Math.Min(netProfit, 0);
            if (DailyProfitTargetMoney > 0 && netProfit >= DailyProfitTargetMoney)
            {
                _haltedForDailyRisk = true;
                return true;
            }

            if (MaxDailyLossMoney > 0 && dailyLossMoney >= MaxDailyLossMoney)
            {
                _haltedForDailyRisk = true;
                return true;
            }

            if (MaxDailyLossPercent > 0 && _dayStartBalance > 0)
            {
                var lossPercent = dailyLossMoney / _dayStartBalance * 100.0;
                if (lossPercent >= MaxDailyLossPercent)
                {
                    _haltedForDailyRisk = true;
                    return true;
                }
            }

            return false;
        }

        private double GetDailyNetProfit()
        {
            var openProfit = Positions.FindAll(BotLabel, SymbolName).Sum(p => p.NetProfit);
            return _dailyClosedNetProfit + openProfit;
        }

        private double GetAtrPips()
        {
            return _atr.Result.Last(1) / Symbol.PipSize;
        }

        private double GetMinimumStopDistancePips()
        {
            return Math.Max(ConvertMinimumDistanceToPips(Symbol.MinStopLossDistance), Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double GetMinimumTakeProfitDistancePips()
        {
            return Math.Max(ConvertMinimumDistanceToPips(Symbol.MinTakeProfitDistance), Math.Max(Symbol.TickSize / Symbol.PipSize, 0.1));
        }

        private double ConvertMinimumDistanceToPips(double minimumDistance)
        {
            if (minimumDistance <= 0)
                return 0;

            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return minimumDistance;

            var referencePrice = (Symbol.Bid + Symbol.Ask) * 0.5;
            var priceDistance = referencePrice * (minimumDistance / 100.0);
            return priceDistance / Symbol.PipSize;
        }

        private double GetSpreadPips()
        {
            return (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private double GetAverageSpreadPips()
        {
            if (_spreadCount == 0)
                return 0;

            var total = 0.0;
            for (var i = 0; i < _spreadCount; i++)
                total += _spreadHistory[i];
            return total / _spreadCount;
        }

        private bool HasManagedPosition()
        {
            return GetManagedPosition() != null;
        }

        private Position GetManagedPosition()
        {
            return Positions.FindAll(BotLabel, SymbolName).OrderBy(p => p.EntryTime).FirstOrDefault();
        }

        private bool HasAnySymbolPosition()
        {
            return Positions.Any(position => string.Equals(position.SymbolName, SymbolName, StringComparison.OrdinalIgnoreCase));
        }

        private static bool IsFinitePositive(double value)
        {
            return value > 0 && !double.IsNaN(value) && !double.IsInfinity(value);
        }

        private void LogInfo(string format, params object[] args)
        {
            Print(format, args);
        }

        private void LogDebug(string format, params object[] args)
        {
            if (DebugLogging)
                Print("[DEBUG] " + format, args);
        }
    }
}
