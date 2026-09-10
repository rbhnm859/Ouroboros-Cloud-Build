using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_K5 : Robot
    {
        private const string Prefix = "[CDScalper-EURUSD-K5] ";

        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int EmaSlopeBars = 3;
        private const double ImpulseAtrMultiplier = 1.25;
        private const double MinImpulseBodyFraction = 0.60;
        private const double ImpulseCloseEdgeFraction = 0.25;
        private const double RetraceLowFraction = 0.33;
        private const double RetraceHighFraction = 0.66;
        private const int SetupExpiryM1Bars = 6;
        private const int SessionStartMinute = 7 * 60;
        private const int SessionEndMinute = 16 * 60 + 30;
        private const double StopBufferAtrMultiplier = 0.10;
        private const double RewardRiskMultiple = 1.80;
        private const double MinimumMoveCostRatio = 2.50;
        private const double CommissionUsdPerMillion = 35.0;
        private const double ExecutionSafetyBufferPips = 0.20;
        private const double MaxLotSize = 0.05;
        private const int MaxDailyTrades = 3;
        private const double MaxDailyClosedLossMoney = 0.90;
        private const double MaxDailyEquityDrawdownMoney = 1.20;
        private const double MaxFloatingLossMoney = 0.90;
        private const double MaxAccountEquityDrawdownPercent = 12.0;
        private const int MaxConsecutiveLosses = 2;
        private const int MinSecondsBetweenTrades = 900;
        private const int LossCooldownMinutes = 45;
        private const int MaxTradeSeconds = 90 * 60;

        [Parameter("Bot Label", DefaultValue = "CDScalper_EURUSD_K5", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Allowed Symbol Prefix", DefaultValue = "EURUSD", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Expected Leverage", DefaultValue = 500.0, MinValue = 1.0, Group = "General")]
        public double ExpectedLeverage { get; set; }

        private Bars _m5Bars;
        private Bars _m15Bars;
        private AverageTrueRange _m1Atr;
        private AverageTrueRange _m5Atr;
        private ExponentialMovingAverage _m15Ema;

        private DateTime _lastProcessedM1Open = DateTime.MinValue;
        private DateTime _lastEvaluatedM5Open = DateTime.MinValue;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private DateTime _openTradeTime = DateTime.MinValue;

        private DateTime _currentDay = DateTime.MinValue;
        private double _dayHighEquity;
        private double _accountPeakEquity;
        private double _dailyClosedPnl;
        private int _dailyTradeCount;
        private int _consecutiveLosses;

        private int _setupDirection;
        private DateTime _impulseOpenTime = DateTime.MinValue;
        private DateTime _impulseCloseTime = DateTime.MinValue;
        private double _impulseHigh;
        private double _impulseLow;
        private double _zoneLow;
        private double _zoneHigh;
        private double _impulseMid;
        private bool _pullbackTouched;
        private double _pullbackExtreme;
        private int _setupBarsElapsed;

        private readonly Dictionary<string, int> _skipReasons = new Dictionary<string, int>();

        protected override void OnStart()
        {
            if (!ValidateSymbol() || TimeFrame != TimeFrame.Minute)
            {
                Print(Prefix + "K5 research requires EURUSD M1.");
                Stop();
                return;
            }

            if (ExpectedLeverage > 0 && Math.Abs(Account.PreciseLeverage - ExpectedLeverage) > 0.01)
            {
                Print(Prefix + "INVALID_TEST_LEVERAGE actual=" + Account.PreciseLeverage.ToString("F2") + " expected=" + ExpectedLeverage.ToString("F2"));
                Stop();
                return;
            }

            _m5Bars = MarketData.GetBars(TimeFrame.Minute5);
            _m15Bars = MarketData.GetBars(TimeFrame.Minute15);
            _m1Atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Simple);
            _m5Atr = Indicators.AverageTrueRange(_m5Bars, AtrPeriod, MovingAverageType.Simple);
            _m15Ema = Indicators.ExponentialMovingAverage(_m15Bars.ClosePrices, EmaPeriod);

            _currentDay = Server.Time.Date;
            _dayHighEquity = Account.Equity;
            _accountPeakEquity = Account.Equity;
            Positions.Closed += OnPositionClosed;
            RestoreRuntimeState();

            Debug("started; RESEARCH ONLY; completed M5 impulse -> M1 pullback -> M1 reclaim; completed M15 EMA context; delta has no decision role; structural SL + 1.80R TP; BE/trailing/adverse-delta off");
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

            DateTime currentM1Open = Bars.OpenTimes.LastValue;
            if (currentM1Open == _lastProcessedM1Open)
                return;
            _lastProcessedM1Open = currentM1Open;

            EvaluateNewCompletedM5Impulse();

            if (GetOpenPosition() != null)
                return;

            ProcessActiveSetup();
        }

        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            return SymbolName.ToUpperInvariant().StartsWith(allowed);
        }

        private int ClosedM1Index()
        {
            return Bars.ClosePrices.Count - 2;
        }

        private int ClosedM5Index()
        {
            return _m5Bars == null ? -1 : _m5Bars.ClosePrices.Count - 2;
        }

        private int ClosedM15Index()
        {
            return _m15Bars == null ? -1 : _m15Bars.ClosePrices.Count - 2;
        }

        private double ClosedM1Atr()
        {
            int i = ClosedM1Index();
            return i >= 0 && i < _m1Atr.Result.Count ? _m1Atr.Result[i] : 0.0;
        }

        private void EvaluateNewCompletedM5Impulse()
        {
            int i = ClosedM5Index();
            if (i < AtrPeriod + 2 || i >= _m5Atr.Result.Count)
                return;

            DateTime openTime = _m5Bars.OpenTimes[i];
            if (openTime == _lastEvaluatedM5Open)
                return;
            _lastEvaluatedM5Open = openTime;

            double open = _m5Bars.OpenPrices[i];
            double close = _m5Bars.ClosePrices[i];
            double high = _m5Bars.HighPrices[i];
            double low = _m5Bars.LowPrices[i];
            double range = high - low;
            double atr = _m5Atr.Result[i];

            if (range <= Symbol.TickSize || atr <= 0 || range < ImpulseAtrMultiplier * atr)
            {
                AuditImpulse(openTime, 0, range, atr, 0, 0, false, "m5_range_not_impulsive");
                return;
            }

            double bodyFraction = Math.Abs(close - open) / range;
            if (bodyFraction < MinImpulseBodyFraction)
            {
                AuditImpulse(openTime, 0, range, atr, bodyFraction, 0, false, "m5_body_fraction_rejected");
                return;
            }

            int direction = close > open ? 1 : close < open ? -1 : 0;
            if (direction == 0)
            {
                AuditImpulse(openTime, 0, range, atr, bodyFraction, 0, false, "m5_doji_rejected");
                return;
            }

            double closeLocation = (close - low) / range;
            bool closeAtEdge = direction > 0 ? closeLocation >= 1.0 - ImpulseCloseEdgeFraction : closeLocation <= ImpulseCloseEdgeFraction;
            if (!closeAtEdge)
            {
                AuditImpulse(openTime, direction, range, atr, bodyFraction, closeLocation, false, "m5_close_location_rejected");
                return;
            }

            if (!CompletedM15TrendSupports(direction))
            {
                AuditImpulse(openTime, direction, range, atr, bodyFraction, closeLocation, false, "m15_trend_rejected");
                return;
            }

            AuditImpulse(openTime, direction, range, atr, bodyFraction, closeLocation, true, "none");

            if (_setupDirection != 0)
            {
                if (_setupDirection != direction)
                {
                    Debug("SETUP_INVALIDATE opposite_m5_impulse old=" + _setupDirection + " new=" + direction);
                    ClearSetup();
                }
                else
                {
                    Debug("SETUP_KEEP same_direction_new_impulse ignored");
                    return;
                }
            }

            StartSetup(direction, openTime, high, low);
        }

        private bool CompletedM15TrendSupports(int direction)
        {
            int i = ClosedM15Index();
            if (i < EmaPeriod + EmaSlopeBars || i >= _m15Ema.Result.Count)
                return false;

            double close = _m15Bars.ClosePrices[i];
            double ema = _m15Ema.Result[i];
            double older = _m15Ema.Result[i - EmaSlopeBars];
            return direction > 0 ? close > ema && ema > older : close < ema && ema < older;
        }

        private void StartSetup(int direction, DateTime impulseOpen, double high, double low)
        {
            _setupDirection = direction;
            _impulseOpenTime = impulseOpen;
            _impulseCloseTime = impulseOpen.AddMinutes(5);
            _impulseHigh = high;
            _impulseLow = low;
            double range = high - low;
            _zoneLow = low + range * RetraceLowFraction;
            _zoneHigh = low + range * RetraceHighFraction;
            _impulseMid = low + range * 0.50;
            _pullbackTouched = false;
            _pullbackExtreme = direction > 0 ? double.MaxValue : double.MinValue;
            _setupBarsElapsed = 0;

            Debug("SETUP_START dir=" + direction
                + " impulseOpen=" + impulseOpen.ToUniversalTime().ToString("O")
                + " high=" + high.ToString("F5")
                + " low=" + low.ToString("F5")
                + " zoneLow=" + _zoneLow.ToString("F5")
                + " zoneHigh=" + _zoneHigh.ToString("F5")
                + " mid=" + _impulseMid.ToString("F5"));
        }

        private void ProcessActiveSetup()
        {
            if (_setupDirection == 0)
                return;

            int i = ClosedM1Index();
            if (i < 0)
                return;

            DateTime barOpen = Bars.OpenTimes[i];
            if (barOpen < _impulseCloseTime)
                return;

            _setupBarsElapsed++;
            if (_setupBarsElapsed > SetupExpiryM1Bars)
            {
                Debug("SETUP_EXPIRE bars=" + _setupBarsElapsed);
                ClearSetup();
                return;
            }

            double open = Bars.OpenPrices[i];
            double close = Bars.ClosePrices[i];
            double high = Bars.HighPrices[i];
            double low = Bars.LowPrices[i];

            if (_setupDirection > 0 && close < _impulseMid)
            {
                Debug("SETUP_INVALIDATE long_close_below_mid close=" + close.ToString("F5"));
                ClearSetup();
                return;
            }
            if (_setupDirection < 0 && close > _impulseMid)
            {
                Debug("SETUP_INVALIDATE short_close_above_mid close=" + close.ToString("F5"));
                ClearSetup();
                return;
            }

            bool overlapsZone = low <= _zoneHigh && high >= _zoneLow;
            if (overlapsZone)
                _pullbackTouched = true;

            if (_pullbackTouched)
            {
                if (_setupDirection > 0)
                    _pullbackExtreme = Math.Min(_pullbackExtreme, low);
                else
                    _pullbackExtreme = Math.Max(_pullbackExtreme, high);
            }

            bool reclaim = _pullbackTouched && (_setupDirection > 0
                ? close > _zoneHigh && close > open
                : close < _zoneLow && close < open);

            Debug("SETUP_AUDIT ts=" + Server.Time.ToUniversalTime().ToString("O")
                + " dir=" + _setupDirection
                + " bars=" + _setupBarsElapsed
                + " touched=" + _pullbackTouched
                + " close=" + close.ToString("F5")
                + " zoneLow=" + _zoneLow.ToString("F5")
                + " zoneHigh=" + _zoneHigh.ToString("F5")
                + " reclaim=" + reclaim);

            if (!reclaim)
                return;

            string guardReason;
            if (!CheckEntryGuards(out guardReason))
            {
                Skip(guardReason);
                ClearSetup();
                return;
            }

            double extreme = _pullbackExtreme;
            int direction = _setupDirection;
            if (double.IsInfinity(extreme) || extreme == double.MaxValue || extreme == double.MinValue)
            {
                Skip("invalid_pullback_extreme");
                ClearSetup();
                return;
            }

            OpenTrade(direction, extreme);
            ClearSetup();
        }

        private bool CheckEntryGuards(out string reason)
        {
            reason = string.Empty;

            if (!IsWeekday()) { reason = "guard_weekend"; return false; }
            if (!IsInSession()) { reason = "guard_outside_session"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "guard_max_daily_trades"; return false; }
            if (_dailyClosedPnl <= -MaxDailyClosedLossMoney) { reason = "guard_daily_closed_loss"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "guard_consecutive_losses"; return false; }
            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddSeconds(MinSecondsBetweenTrades)) { reason = "guard_entry_cooldown"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "guard_loss_cooldown"; return false; }
            if (IsDailyEquityDrawdownHit()) { reason = "guard_daily_equity_dd"; return false; }
            if (IsAccountEquityDrawdownHit()) { reason = "guard_account_equity_dd"; return false; }
            return true;
        }

        private bool IsWeekday()
        {
            DayOfWeek d = Server.Time.ToUniversalTime().DayOfWeek;
            return d != DayOfWeek.Saturday && d != DayOfWeek.Sunday;
        }

        private bool IsInSession()
        {
            DateTime t = Server.Time.ToUniversalTime();
            int minute = t.Hour * 60 + t.Minute;
            return minute >= SessionStartMinute && minute < SessionEndMinute;
        }

        private void OpenTrade(int direction, double pullbackExtreme)
        {
            double atr = ClosedM1Atr();
            if (atr <= 0)
            {
                Skip("invalid_m1_atr");
                return;
            }

            double entry = direction > 0 ? Symbol.Ask : Symbol.Bid;
            double stopPrice = direction > 0
                ? pullbackExtreme - StopBufferAtrMultiplier * atr
                : pullbackExtreme + StopBufferAtrMultiplier * atr;

            double rawSlPips = direction > 0
                ? (entry - stopPrice) / Symbol.PipSize
                : (stopPrice - entry) / Symbol.PipSize;

            if (rawSlPips <= 0)
            {
                Skip("structural_stop_not_beyond_entry");
                return;
            }

            double slPips = Math.Max(rawSlPips, BrokerMinStopPips());
            double tpPips = Math.Max(slPips * RewardRiskMultiple, BrokerMinTakeProfitPips());

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

            double totalCostPips = EstimateRoundTripCostPips(volume);
            double moveCost = totalCostPips > 0 ? tpPips / totalCostPips : double.PositiveInfinity;
            if (moveCost < MinimumMoveCostRatio)
            {
                Skip("economic_floor_ratio_" + moveCost.ToString("F2"));
                return;
            }

            TradeType type = direction > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful)
            {
                Skip("order_rejected_" + result.Error);
                return;
            }

            _lastTradeTime = Server.Time;
            _openTradeTime = Server.Time;
            _dailyTradeCount++;

            Debug("OPEN type=" + type
                + " vol=" + volume
                + " slPips=" + slPips.ToString("F2")
                + " tpPips=" + tpPips.ToString("F2")
                + " costPips=" + totalCostPips.ToString("F2")
                + " moveCost=" + moveCost.ToString("F2")
                + " riskMoney=" + riskMoney.ToString("F2"));
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
            if (raw <= 0)
                return 0.0;

            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return raw;

            double mid = (Symbol.Bid + Symbol.Ask) / 2.0;
            if (mid <= 0)
                return 0.0;
            double priceDistance = mid * raw / 100.0;
            return priceDistance / Symbol.PipSize;
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
                ClosePositionWithLog(position, "time_stop_90m");
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
            if (_accountPeakEquity <= 0)
                return false;
            return (_accountPeakEquity - Account.Equity) / _accountPeakEquity * 100.0 >= MaxAccountEquityDrawdownPercent;
        }

        private void UpdateEquityPeaks()
        {
            if (Account.Equity > _dayHighEquity)
                _dayHighEquity = Account.Equity;
            if (Account.Equity > _accountPeakEquity)
                _accountPeakEquity = Account.Equity;
        }

        private Position GetOpenPosition()
        {
            return Positions.FirstOrDefault(x => x.SymbolName == SymbolName && x.Label == TradeLabel);
        }

        private void RestoreRuntimeState()
        {
            Position p = GetOpenPosition();
            if (p != null)
                _openTradeTime = p.EntryTime;

            DateTime dayStart = Server.Time.Date;
            var trades = History.Where(h => h.SymbolName == SymbolName && h.Label == TradeLabel && h.ClosingTime >= dayStart).OrderBy(h => h.ClosingTime).ToList();
            _dailyClosedPnl = trades.Sum(h => h.NetProfit);
            _dailyTradeCount = trades.Count + (p != null && p.EntryTime >= dayStart ? 1 : 0);
            _consecutiveLosses = 0;
            for (int i = trades.Count - 1; i >= 0; i--)
            {
                if (trades[i].NetProfit < 0)
                    _consecutiveLosses++;
                else
                    break;
            }

            var last = trades.LastOrDefault();
            if (last != null)
            {
                _lastTradeTime = last.ClosingTime;
                if (last.NetProfit < 0)
                    _lastLossTime = last.ClosingTime;
            }
        }

        private void ResetDailyIfNeeded()
        {
            DateTime today = Server.Time.Date;
            if (today == _currentDay)
                return;

            _currentDay = today;
            _dayHighEquity = Account.Equity;
            _dailyClosedPnl = 0.0;
            _dailyTradeCount = 0;
            _consecutiveLosses = 0;
        }

        private void SyncDailyStatsFromHistory()
        {
            DateTime start = Server.Time.Date;
            var trades = History.Where(h => h.SymbolName == SymbolName && h.Label == TradeLabel && h.ClosingTime >= start).ToList();
            _dailyClosedPnl = trades.Sum(h => h.NetProfit);
            int count = trades.Count + Positions.Count(p => p.SymbolName == SymbolName && p.Label == TradeLabel && p.EntryTime >= start);
            _dailyTradeCount = Math.Max(_dailyTradeCount, count);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != TradeLabel)
                return;

            if (p.NetProfit < 0)
            {
                _consecutiveLosses++;
                _lastLossTime = Server.Time;
            }
            else if (p.NetProfit > 0)
            {
                _consecutiveLosses = 0;
            }

            Debug("POSITION_CLOSED type=" + p.TradeType
                + " net=" + p.NetProfit.ToString("F2")
                + " entry=" + p.EntryPrice.ToString("F5"));
            _openTradeTime = DateTime.MinValue;
        }

        private void ClosePositionWithLog(Position p, string reason)
        {
            TradeResult result = ClosePosition(p);
            Debug(result.IsSuccessful ? "CLOSE " + reason : "close_failed_" + result.Error);
        }

        private void ClearSetup()
        {
            _setupDirection = 0;
            _impulseOpenTime = DateTime.MinValue;
            _impulseCloseTime = DateTime.MinValue;
            _impulseHigh = 0.0;
            _impulseLow = 0.0;
            _zoneLow = 0.0;
            _zoneHigh = 0.0;
            _impulseMid = 0.0;
            _pullbackTouched = false;
            _pullbackExtreme = 0.0;
            _setupBarsElapsed = 0;
        }

        private void AuditImpulse(DateTime time, int direction, double range, double atr, double bodyFraction, double closeLocation, bool accepted, string reason)
        {
            Debug("IMPULSE_AUDIT ts=" + time.ToUniversalTime().ToString("O")
                + " dir=" + direction
                + " range=" + range.ToString("F6")
                + " atr=" + atr.ToString("F6")
                + " bodyFrac=" + bodyFraction.ToString("F3")
                + " closeLoc=" + closeLocation.ToString("F3")
                + " decision=" + (accepted ? "ACCEPT" : "REJECT")
                + " reason=" + reason);
        }

        private void Skip(string reason)
        {
            int count;
            if (_skipReasons.TryGetValue(reason, out count))
                _skipReasons[reason] = count + 1;
            else
                _skipReasons[reason] = 1;
            Debug("SKIP " + reason);
        }

        private void Debug(string message)
        {
            if (DebugLogging)
                Print(Prefix + message);
        }
    }
}
