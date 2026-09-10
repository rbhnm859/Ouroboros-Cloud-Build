using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_K6 : Robot
    {
        private const string Prefix = "[CDScalper-EURUSD-K6] ";
        private const int RangeStartMinute = 0;
        private const int RangeEndMinute = 7 * 60;
        private const int EntryStartMinute = 7 * 60;
        private const int EntryEndMinute = 12 * 60;
        private const int MinimumRangeBars = 300;
        private const double MinimumRangePips = 4.0;
        private const double MaximumRangePips = 35.0;
        private const double SweepDistancePips = 1.0;
        private const double RejectionCloseFraction = 0.50;
        private const double MinimumBodyFraction = 0.25;
        private const double BarRangeCostMultiple = 2.0;
        private const double StructuralStopBufferPips = 0.50;
        private const double MinimumRewardRisk = 1.20;
        private const double MinimumRewardCost = 2.50;
        private const double CommissionUsdPerMillion = 35.0;
        private const double ExecutionSafetyBufferPips = 0.20;
        private const double MaxLotSize = 0.05;
        private const int MaxDailyTrades = 1;
        private const double MaxDailyClosedLossMoney = 0.60;
        private const double MaxDailyEquityDrawdownMoney = 1.20;
        private const double MaxFloatingLossMoney = 0.90;
        private const double MaxAccountEquityDrawdownPercent = 12.0;
        private const int MaxConsecutiveLosses = 2;
        private const int MaxTradeSeconds = 180 * 60;

        [Parameter("Bot Label", DefaultValue = "CDScalper_EURUSD_K6", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Allowed Symbol Prefix", DefaultValue = "EURUSD", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Expected Leverage", DefaultValue = 500.0, MinValue = 1.0, Group = "General")]
        public double ExpectedLeverage { get; set; }

        private DateTime _currentDay = DateTime.MinValue;
        private DateTime _lastProcessedM1Open = DateTime.MinValue;
        private DateTime _openTradeTime = DateTime.MinValue;
        private double _rangeHigh;
        private double _rangeLow;
        private int _rangeBars;
        private bool _rangeFrozen;
        private bool _rangeAdmitted;
        private double _frozenRangeHigh;
        private double _frozenRangeLow;
        private double _frozenMidpoint;
        private double _dayHighEquity;
        private double _accountPeakEquity;
        private double _dailyClosedPnl;
        private int _dailyTradeCount;
        private int _consecutiveLosses;
        private readonly Dictionary<string, int> _skipReasons = new Dictionary<string, int>();

        protected override void OnStart()
        {
            if (!ValidateSymbol() || TimeFrame != TimeFrame.Minute)
            {
                Print(Prefix + "K6 research requires EURUSD M1.");
                Stop();
                return;
            }

            if (ExpectedLeverage > 0 && Math.Abs(Account.PreciseLeverage - ExpectedLeverage) > 0.01)
            {
                Print(Prefix + "INVALID_TEST_LEVERAGE actual=" + Account.PreciseLeverage.ToString("F2") + " expected=" + ExpectedLeverage.ToString("F2"));
                Stop();
                return;
            }

            _accountPeakEquity = Account.Equity;
            _currentDay = Server.Time.Date;
            ResetDayState(true);
            Positions.Closed += OnPositionClosed;
            RestoreRuntimeState();
            Debug("started; RESEARCH ONLY; completed-M1 overnight range 00:00-06:59; London sweep rejection 07:00-11:59; midpoint target; delta no decision role; symbol-wide no-hedge guard");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            if (!DebugLogging) return;
            foreach (var kv in _skipReasons.OrderByDescending(x => x.Value))
                Print(Prefix + "SKIP_SUMMARY " + kv.Key + "=" + kv.Value);
        }

        protected override void OnTick()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            UpdateEquityPeaks();
            Position open = GetOpenPosition();
            if (open != null)
                ManageOpenPosition(open);
        }

        protected override void OnBar()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            UpdateEquityPeaks();

            DateTime currentOpen = Bars.OpenTimes.LastValue;
            if (currentOpen == _lastProcessedM1Open)
                return;
            _lastProcessedM1Open = currentOpen;

            int i = Bars.ClosePrices.Count - 2;
            if (i < 0)
                return;

            DateTime barOpen = Bars.OpenTimes[i].ToUniversalTime();
            if (barOpen.Date != _currentDay)
                return;

            int minute = barOpen.Hour * 60 + barOpen.Minute;
            if (minute >= RangeStartMinute && minute < RangeEndMinute)
            {
                AccumulateRange(i);
                return;
            }

            if (!_rangeFrozen && minute >= RangeEndMinute)
                FreezeRange();

            if (!_rangeFrozen || !_rangeAdmitted)
                return;
            if (minute < EntryStartMinute || minute >= EntryEndMinute)
                return;
            if (HasAnySymbolPosition())
                return;

            EvaluateSweepRejection(i);
        }

        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            return SymbolName.ToUpperInvariant().StartsWith(allowed);
        }

        private void AccumulateRange(int i)
        {
            double high = Bars.HighPrices[i];
            double low = Bars.LowPrices[i];
            if (_rangeBars == 0)
            {
                _rangeHigh = high;
                _rangeLow = low;
            }
            else
            {
                _rangeHigh = Math.Max(_rangeHigh, high);
                _rangeLow = Math.Min(_rangeLow, low);
            }
            _rangeBars++;
        }

        private void FreezeRange()
        {
            _rangeFrozen = true;
            if (_rangeBars < MinimumRangeBars || _rangeHigh <= _rangeLow)
            {
                _rangeAdmitted = false;
                Debug("RANGE_FREEZE admitted=false bars=" + _rangeBars);
                return;
            }

            double widthPips = (_rangeHigh - _rangeLow) / Symbol.PipSize;
            _rangeAdmitted = widthPips >= MinimumRangePips && widthPips <= MaximumRangePips;
            if (_rangeAdmitted)
            {
                _frozenRangeHigh = _rangeHigh;
                _frozenRangeLow = _rangeLow;
                _frozenMidpoint = (_rangeHigh + _rangeLow) / 2.0;
            }
            Debug("RANGE_FREEZE admitted=" + _rangeAdmitted + " bars=" + _rangeBars + " widthPips=" + widthPips.ToString("F2") + " high=" + _rangeHigh.ToString("F5") + " low=" + _rangeLow.ToString("F5"));
        }

        private void EvaluateSweepRejection(int i)
        {
            string guardReason;
            if (!CheckEntryGuards(out guardReason))
            {
                Skip(guardReason);
                return;
            }

            double open = Bars.OpenPrices[i];
            double close = Bars.ClosePrices[i];
            double high = Bars.HighPrices[i];
            double low = Bars.LowPrices[i];
            double barRange = high - low;
            if (barRange <= Symbol.TickSize)
            {
                Skip("bar_range_zero");
                return;
            }

            double sweepDistance = SweepDistancePips * Symbol.PipSize;
            bool sweptLow = low <= _frozenRangeLow - sweepDistance;
            bool sweptHigh = high >= _frozenRangeHigh + sweepDistance;
            if (sweptLow && sweptHigh)
            {
                Skip("ambiguous_dual_extreme_bar");
                return;
            }

            double closeLocation = (close - low) / barRange;
            double bodyFraction = Math.Abs(close - open) / barRange;
            double barRangePips = barRange / Symbol.PipSize;
            double costPips = EstimateRoundTripCostPips(Symbol.VolumeInUnitsMin);
            if (barRangePips < BarRangeCostMultiple * costPips)
            {
                Skip("bar_range_below_cost_floor");
                return;
            }
            if (bodyFraction < MinimumBodyFraction)
            {
                Skip("body_fraction_rejected");
                return;
            }

            bool longSignal = sweptLow && close > _frozenRangeLow && closeLocation >= RejectionCloseFraction;
            bool shortSignal = sweptHigh && close < _frozenRangeHigh && closeLocation <= 1.0 - RejectionCloseFraction;
            Debug("SWEEP_AUDIT ts=" + Bars.OpenTimes[i].ToUniversalTime().ToString("O") + " sweptLow=" + sweptLow + " sweptHigh=" + sweptHigh + " closeLoc=" + closeLocation.ToString("F3") + " bodyFrac=" + bodyFraction.ToString("F3") + " costPips=" + costPips.ToString("F2") + " long=" + longSignal + " short=" + shortSignal);

            if (longSignal == shortSignal)
                return;

            OpenTrade(longSignal ? 1 : -1, longSignal ? low : high);
        }

        private bool CheckEntryGuards(out string reason)
        {
            reason = string.Empty;
            if (HasAnySymbolPosition()) { reason = "guard_symbol_position_exists"; return false; }
            if (!IsWeekday()) { reason = "guard_weekend"; return false; }
            if (!IsInEntrySession()) { reason = "guard_outside_session"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "guard_max_daily_trades"; return false; }
            if (_dailyClosedPnl <= -MaxDailyClosedLossMoney) { reason = "guard_daily_closed_loss"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "guard_consecutive_losses"; return false; }
            if (IsDailyEquityDrawdownHit()) { reason = "guard_daily_equity_dd"; return false; }
            if (IsAccountEquityDrawdownHit()) { reason = "guard_account_equity_dd"; return false; }
            return true;
        }

        private bool IsWeekday()
        {
            DayOfWeek d = Server.Time.ToUniversalTime().DayOfWeek;
            return d != DayOfWeek.Saturday && d != DayOfWeek.Sunday;
        }

        private bool IsInEntrySession()
        {
            DateTime t = Server.Time.ToUniversalTime();
            int minute = t.Hour * 60 + t.Minute;
            return minute >= EntryStartMinute && minute < EntryEndMinute;
        }

        private bool HasAnySymbolPosition()
        {
            return Positions.Any(x => x.SymbolName == SymbolName);
        }

        private Position GetOpenPosition()
        {
            return Positions.FirstOrDefault(x => x.SymbolName == SymbolName && x.Label == TradeLabel);
        }

        private void OpenTrade(int direction, double sweepExtreme)
        {
            if (HasAnySymbolPosition())
            {
                Skip("guard_symbol_position_exists");
                return;
            }

            double entry = direction > 0 ? Symbol.Ask : Symbol.Bid;
            double stopPrice = direction > 0
                ? sweepExtreme - StructuralStopBufferPips * Symbol.PipSize
                : sweepExtreme + StructuralStopBufferPips * Symbol.PipSize;
            double targetPrice = _frozenMidpoint;

            double rawSlPips = direction > 0 ? (entry - stopPrice) / Symbol.PipSize : (stopPrice - entry) / Symbol.PipSize;
            double rawTpPips = direction > 0 ? (targetPrice - entry) / Symbol.PipSize : (entry - targetPrice) / Symbol.PipSize;
            if (rawSlPips <= 0 || rawTpPips <= 0)
            {
                Skip("invalid_structural_geometry");
                return;
            }

            double slPips = Math.Max(rawSlPips, BrokerMinStopPips());
            double tpPips = Math.Max(rawTpPips, BrokerMinTakeProfitPips());
            if (tpPips > rawTpPips + 1e-9)
            {
                Skip("midpoint_inside_broker_min_tp");
                return;
            }

            double rr = tpPips / slPips;
            if (rr < MinimumRewardRisk)
            {
                Skip("reward_risk_floor_" + rr.ToString("F2"));
                return;
            }

            double riskMoney = Math.Min(Account.Balance * 0.01, 0.30);
            if (riskMoney <= 0)
            {
                Skip("invalid_risk_money");
                return;
            }

            double volume = Symbol.VolumeForFixedRisk(riskMoney, slPips, RoundingMode.Down);
            double cap = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            volume = Math.Min(volume, cap);
            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Skip("normalized_volume_below_broker_minimum");
                return;
            }

            double costPips = EstimateRoundTripCostPips(volume);
            double rewardCost = costPips > 0 ? tpPips / costPips : double.PositiveInfinity;
            if (rewardCost < MinimumRewardCost)
            {
                Skip("reward_cost_floor_" + rewardCost.ToString("F2"));
                return;
            }

            TradeType type = direction > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful)
            {
                Skip("order_rejected_" + result.Error);
                return;
            }

            _dailyTradeCount++;
            _openTradeTime = Server.Time;
            Debug("OPEN type=" + type + " vol=" + volume + " slPips=" + slPips.ToString("F2") + " tpPips=" + tpPips.ToString("F2") + " rr=" + rr.ToString("F2") + " costPips=" + costPips.ToString("F2") + " rewardCost=" + rewardCost.ToString("F2") + " riskMoney=" + riskMoney.ToString("F2"));
        }

        private double BrokerMinStopPips()
        {
            return BrokerMinimumDistancePips(Symbol.MinStopLossDistance);
        }

        private double BrokerMinTakeProfitPips()
        {
            return BrokerMinimumDistancePips(Symbol.MinTakeProfitDistance);
        }

        private double BrokerMinimumDistancePips(double raw)
        {
            if (raw <= 0) return 0.0;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips) return raw;
            double mid = (Symbol.Bid + Symbol.Ask) / 2.0;
            if (mid <= 0) return 0.0;
            return (mid * raw / 100.0) / Symbol.PipSize;
        }

        private double EstimateRoundTripCostPips(double volume)
        {
            double spreadPips = Symbol.Spread / Symbol.PipSize;
            double mid = (Symbol.Bid + Symbol.Ask) / 2.0;
            double notionalUsd = volume * mid;
            double commissionMoney = notionalUsd / 1000000.0 * CommissionUsdPerMillion * 2.0;
            double pipValueForVolume = Math.Abs(Symbol.PipValue * volume);
            double commissionPips = pipValueForVolume > 0 ? commissionMoney / pipValueForVolume : 0.0;
            return Math.Max(0.0, spreadPips) + Math.Max(0.0, commissionPips) + ExecutionSafetyBufferPips;
        }

        private void ManageOpenPosition(Position position)
        {
            string reason;
            if (CheckCriticalEquityExit(out reason))
            {
                ClosePositionWithLog(position, reason);
                return;
            }
            if (MaxTradeSeconds > 0 && _openTradeTime != DateTime.MinValue && Server.Time >= _openTradeTime.AddSeconds(MaxTradeSeconds))
                ClosePositionWithLog(position, "time_stop_180m");
        }

        private bool CheckCriticalEquityExit(out string reason)
        {
            reason = string.Empty;
            if (IsFloatingLossHit()) { reason = "floating_loss_guard"; return true; }
            if (IsDailyEquityDrawdownHit()) { reason = "daily_equity_dd_guard"; return true; }
            if (IsAccountEquityDrawdownHit()) { reason = "account_equity_dd_guard"; return true; }
            return false;
        }

        private bool IsFloatingLossHit()
        {
            double pnl = Positions.Where(x => x.SymbolName == SymbolName && x.Label == TradeLabel).Sum(x => x.NetProfit);
            return pnl <= -MaxFloatingLossMoney;
        }

        private bool IsDailyEquityDrawdownHit()
        {
            return (_dayHighEquity - Account.Equity) >= MaxDailyEquityDrawdownMoney;
        }

        private bool IsAccountEquityDrawdownHit()
        {
            if (_accountPeakEquity <= 0) return false;
            return (_accountPeakEquity - Account.Equity) / _accountPeakEquity * 100.0 >= MaxAccountEquityDrawdownPercent;
        }

        private void UpdateEquityPeaks()
        {
            if (Account.Equity > _dayHighEquity) _dayHighEquity = Account.Equity;
            if (Account.Equity > _accountPeakEquity) _accountPeakEquity = Account.Equity;
        }

        private void RestoreRuntimeState()
        {
            Position p = GetOpenPosition();
            if (p != null) _openTradeTime = p.EntryTime;
            SyncDailyStatsFromHistory();
        }

        private void ResetDailyIfNeeded()
        {
            DateTime today = Server.Time.Date;
            if (today == _currentDay) return;
            _currentDay = today;
            ResetDayState(false);
        }

        private void ResetDayState(bool startup)
        {
            _rangeHigh = 0.0;
            _rangeLow = 0.0;
            _rangeBars = 0;
            _rangeFrozen = false;
            _rangeAdmitted = false;
            _frozenRangeHigh = 0.0;
            _frozenRangeLow = 0.0;
            _frozenMidpoint = 0.0;
            _dayHighEquity = Account.Equity;
            _dailyClosedPnl = 0.0;
            _dailyTradeCount = 0;
            _consecutiveLosses = 0;
            if (!startup) Debug("DAY_RESET " + _currentDay.ToString("yyyy-MM-dd"));
        }

        private void SyncDailyStatsFromHistory()
        {
            DateTime start = Server.Time.Date;
            var trades = History.Where(h => h.SymbolName == SymbolName && h.Label == TradeLabel && h.ClosingTime >= start).OrderBy(h => h.ClosingTime).ToList();
            _dailyClosedPnl = trades.Sum(h => h.NetProfit);
            int count = trades.Count + Positions.Count(p => p.SymbolName == SymbolName && p.Label == TradeLabel && p.EntryTime >= start);
            _dailyTradeCount = Math.Max(_dailyTradeCount, count);
            _consecutiveLosses = 0;
            for (int i = trades.Count - 1; i >= 0; i--)
            {
                if (trades[i].NetProfit < 0) _consecutiveLosses++;
                else break;
            }
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != TradeLabel) return;
            if (p.NetProfit < 0) _consecutiveLosses++;
            else if (p.NetProfit > 0) _consecutiveLosses = 0;
            _openTradeTime = DateTime.MinValue;
            Debug("POSITION_CLOSED type=" + p.TradeType + " net=" + p.NetProfit.ToString("F2") + " entry=" + p.EntryPrice.ToString("F5"));
        }

        private void ClosePositionWithLog(Position p, string reason)
        {
            TradeResult result = ClosePosition(p);
            Debug(result.IsSuccessful ? "CLOSE " + reason : "close_failed_" + result.Error);
        }

        private void Skip(string reason)
        {
            int count;
            if (_skipReasons.TryGetValue(reason, out count)) _skipReasons[reason] = count + 1;
            else _skipReasons[reason] = 1;
            Debug("SKIP " + reason);
        }

        private void Debug(string message)
        {
            if (DebugLogging) Print(Prefix + message);
        }
    }
}
