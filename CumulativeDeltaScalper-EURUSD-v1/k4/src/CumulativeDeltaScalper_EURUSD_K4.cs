using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_K4 : Robot
    {
        private const string Prefix = "[CDScalper-EURUSD-K4] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;
        private const int EmaSlopeBars = 3;
        private const int DeltaWindowSize = 10;
        private const int BreakoutLookback = 5;
        private const int SpreadHistorySize = 30;
        private const int MaxSpreadPoints = 18;
        private const double SpreadAvgMultiplier = 1.8;
        private const double MinAtr = 0.00005;
        private const double MaxAtr = 0.00105;
        private const int SessionStartMinuteOfDay = 14 * 60;
        private const int SessionEndMinuteOfDay = 14 * 60 + 54;
        private const int MaxDailyTrades = 3;
        private const double MaxDailyLossPercent = 4.0;
        private const double MaxDailyLossMoney = 0.55;
        private const double DailyProfitTargetMoney = 1.10;
        private const int MaxConsecutiveLosses = 2;
        private const int MinSecondsBetweenTrades = 900;
        private const int LossCooldownMinutes = 45;
        private const double MaxDailyEquityDrawdownMoney = 0.75;
        private const double MaxFloatingLossMoney = 0.90;
        private const double MaxEquityDrawdownPercent = 12.0;
        private const int MaxTradeSeconds = 1800;
        private const double FixedMoneyRisk = 1.0;
        private const double RiskReferenceBalance = 100.0;
        private const double MinFixedMoneyRisk = 0.05;
        private const double MaxLotSize = 0.05;
        private const double SlAtrMultiplier = 0.8;
        private const double TpAtrMultiplier = 1.2;
        private const int FallbackBelowTickDelta = 2;
        private const double BarDeltaPointMultiplier = 1.6;
        private const double AdxThreshold = 16.0;
        private const double CloseLocationFraction = 0.30;
        private const double CommissionUsdPerMillion = 35.0;
        private const double ExecutionSafetyBufferPips = 0.2;
        private const double MinimumExpectedMoveToCostRatio = 1.0;

        [Parameter("Bot Label", DefaultValue = "CDScalper_EURUSD_K4", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Allowed Symbol Prefix", DefaultValue = "EURUSD", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Expected Leverage", DefaultValue = 500.0, MinValue = 1.0, Group = "General")]
        public double ExpectedLeverage { get; set; }

        private AverageTrueRange _atr;
        private ExponentialMovingAverage _htfEma;
        private DirectionalMovementSystem _htfDms;
        private Bars _htfBars;

        private double _prevBid;
        private int _uptickCount;
        private int _downtickCount;
        private readonly int[] _deltaBuffer = new int[DeltaWindowSize];
        private int _bufferIndex;
        private int _bufferFilled;
        private readonly int[] _spreadHistory = new int[SpreadHistorySize];
        private int _spreadHistoryIndex;
        private int _spreadHistoryFilled;

        private DateTime _lastProcessedBarTime = DateTime.MinValue;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private DateTime _openTradeTime = DateTime.MinValue;

        private DateTime _currentDay = DateTime.MinValue;
        private double _dayStartBalance;
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
                Print(Prefix + "K4 research requires EURUSD M1.");
                Stop();
                return;
            }

            if (ExpectedLeverage > 0 && Math.Abs(Account.PreciseLeverage - ExpectedLeverage) > 0.01)
            {
                Print(Prefix + "INVALID_TEST_LEVERAGE actual=" + Account.PreciseLeverage.ToString("F2") + " expected=" + ExpectedLeverage.ToString("F2"));
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Simple);
            _htfBars = MarketData.GetBars(TimeFrame.Minute15);
            _htfEma = Indicators.ExponentialMovingAverage(_htfBars.ClosePrices, EmaPeriod);
            _htfDms = Indicators.DirectionalMovementSystem(_htfBars, AdxPeriod);
            _prevBid = Symbol.Bid;
            _currentDay = Server.Time.Date;
            _dayStartBalance = Account.Balance;
            _dayHighEquity = Account.Equity;
            _accountPeakEquity = Account.Equity;
            Positions.Closed += OnPositionClosed;
            RestoreRuntimeState();
            Debug("started; research-only; price-first 5-bar breakout + 30pct close location + closed M15 trend/ADX + delta veto; SL0.8ATR TP1.2ATR; BE off");
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
            ProcessTickDelta();

            Position open = GetOpenPosition();
            if (open != null)
                ManageOpenPositionTick(open);
        }

        protected override void OnBar()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            UpdateEquityPeaks();
            FinalizeClosedBarDelta();

            DateTime barTime = Bars.OpenTimes.LastValue;
            if (barTime == _lastProcessedBarTime)
                return;
            _lastProcessedBarTime = barTime;

            if (GetOpenPosition() != null)
                return;

            string guardReason;
            if (!CheckGuards(out guardReason))
            {
                Skip(guardReason);
                return;
            }

            int signal = CheckPriceFirstSignal();
            if (signal == 0)
                return;

            OpenTrade(signal);
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

        private int ClosedHtfIndex()
        {
            return _htfBars == null ? -1 : _htfBars.ClosePrices.Count - 2;
        }

        private double ClosedAtrValue()
        {
            int index = ClosedM1Index();
            if (index < 0 || index >= _atr.Result.Count) return 0.0;
            return _atr.Result[index];
        }

        private void ProcessTickDelta()
        {
            double bid = Symbol.Bid;
            if (bid > _prevBid) _uptickCount++;
            else if (bid < _prevBid) _downtickCount++;
            _prevBid = bid;
        }

        private void FinalizeClosedBarDelta()
        {
            int tickDelta = _uptickCount - _downtickCount;
            int finalDelta = tickDelta;
            if (Math.Abs(tickDelta) <= FallbackBelowTickDelta)
            {
                int estimated = EstimateClosedBarDelta();
                if (estimated != 0) finalDelta = estimated;
            }

            _deltaBuffer[_bufferIndex] = finalDelta;
            _bufferIndex = (_bufferIndex + 1) % _deltaBuffer.Length;
            if (_bufferFilled < _deltaBuffer.Length) _bufferFilled++;

            int spread = SpreadInPoints();
            _spreadHistory[_spreadHistoryIndex] = spread;
            _spreadHistoryIndex = (_spreadHistoryIndex + 1) % _spreadHistory.Length;
            if (_spreadHistoryFilled < _spreadHistory.Length) _spreadHistoryFilled++;

            _uptickCount = 0;
            _downtickCount = 0;
        }

        private int EstimateClosedBarDelta()
        {
            int index = ClosedM1Index();
            if (index < 0) return 0;
            double open = Bars.OpenPrices[index];
            double close = Bars.ClosePrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double body = close - open;
            if (Math.Abs(body) < Symbol.TickSize) return 0;
            double range = Math.Max(Symbol.TickSize, high - low);
            double bodyPoints = body / Symbol.TickSize;
            double dominance = Math.Min(1.0, Math.Abs(body) / range);
            double weighted = bodyPoints * BarDeltaPointMultiplier * Math.Max(0.25, dominance);
            int estimated = (int)Math.Round(weighted);
            if (estimated == 0) estimated = body > 0 ? 1 : -1;
            return estimated;
        }

        private int CheckPriceFirstSignal()
        {
            int index = ClosedM1Index();
            if (index < BreakoutLookback + 1 || _bufferFilled < DeltaWindowSize)
            {
                Skip("entry_history_not_ready");
                return 0;
            }

            double close = Bars.ClosePrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double range = high - low;
            if (range <= Symbol.TickSize)
            {
                Skip("entry_signal_bar_range_too_small");
                return 0;
            }

            double priorHigh = double.MinValue;
            double priorLow = double.MaxValue;
            for (int i = 1; i <= BreakoutLookback; i++)
            {
                int j = index - i;
                priorHigh = Math.Max(priorHigh, Bars.HighPrices[j]);
                priorLow = Math.Min(priorLow, Bars.LowPrices[j]);
            }

            bool longBreakout = close > priorHigh;
            bool shortBreakout = close < priorLow;
            if (!longBreakout && !shortBreakout)
            {
                Skip("entry_no_price_breakout");
                return 0;
            }

            int signal = longBreakout ? 1 : -1;
            double closeLocation = (close - low) / range;
            bool closeLocationOk = signal > 0 ? closeLocation >= 1.0 - CloseLocationFraction : closeLocation <= CloseLocationFraction;

            int htfIndex = ClosedHtfIndex();
            bool htfTrendOk = false;
            bool adxOk = false;
            double htfClose = 0.0;
            double htfEma = 0.0;
            double htfAdx = 0.0;
            if (htfIndex >= EmaSlopeBars && htfIndex < _htfEma.Result.Count && htfIndex < _htfDms.ADX.Count)
            {
                htfClose = _htfBars.ClosePrices[htfIndex];
                htfEma = _htfEma.Result[htfIndex];
                double olderEma = _htfEma.Result[htfIndex - EmaSlopeBars];
                bool priceSide = signal > 0 ? htfClose > htfEma : htfClose < htfEma;
                bool slopeSide = signal > 0 ? htfEma > olderEma : htfEma < olderEma;
                htfTrendOk = priceSide && slopeSide;
                htfAdx = _htfDms.ADX[htfIndex];
                adxOk = htfAdx >= AdxThreshold;
            }

            int cumulativeDelta = CalculateCumulativeDelta();
            int d1 = DeltaFromNewest(1);
            int d2 = DeltaFromNewest(2);
            int d3 = DeltaFromNewest(3);
            int agreeing = 0;
            if (signal > 0)
            {
                if (d1 > 0) agreeing++;
                if (d2 > 0) agreeing++;
                if (d3 > 0) agreeing++;
            }
            else
            {
                if (d1 < 0) agreeing++;
                if (d2 < 0) agreeing++;
                if (d3 < 0) agreeing++;
            }
            bool deltaOk = signal > 0 ? cumulativeDelta > 0 && agreeing >= 2 : cumulativeDelta < 0 && agreeing >= 2;
            bool spreadOk = CheckSpreadDynamic();
            double atr = ClosedAtrValue();
            double estimatedCostPips = EstimateCandidateCostPips(atr);

            string reason = "none";
            bool accepted = true;
            if (!closeLocationOk) { accepted = false; reason = "entry_close_location_rejected"; }
            else if (!htfTrendOk) { accepted = false; reason = "entry_closed_m15_trend_rejected"; }
            else if (!adxOk) { accepted = false; reason = "entry_closed_m15_adx_rejected"; }
            else if (!deltaOk) { accepted = false; reason = "entry_delta_confirmation_rejected"; }
            else if (!spreadOk) { accepted = false; reason = "entry_dynamic_spread_rejected"; }

            Debug("SIGNAL_AUDIT ts=" + Server.Time.ToUniversalTime().ToString("O")
                + " dir=" + signal
                + " breakout=true"
                + " close=" + close.ToString("F5")
                + " priorHigh=" + priorHigh.ToString("F5")
                + " priorLow=" + priorLow.ToString("F5")
                + " closeLocation=" + closeLocation.ToString("F3")
                + " htfClose=" + htfClose.ToString("F5")
                + " htfEma=" + htfEma.ToString("F5")
                + " htfAdx=" + htfAdx.ToString("F2")
                + " cumDelta=" + cumulativeDelta
                + " d1=" + d1 + " d2=" + d2 + " d3=" + d3
                + " deltaVotes=" + agreeing
                + " spreadPts=" + SpreadInPoints()
                + " atr=" + atr.ToString("F6")
                + " estimatedCostPips=" + estimatedCostPips.ToString("F2")
                + " decision=" + (accepted ? "ACCEPT" : "REJECT")
                + " skipReason=" + reason);

            if (!accepted)
            {
                Skip(reason);
                return 0;
            }

            return signal;
        }

        private int CalculateCumulativeDelta()
        {
            int sum = 0;
            for (int i = 0; i < _bufferFilled; i++) sum += _deltaBuffer[i];
            return sum;
        }

        private int DeltaFromNewest(int offset)
        {
            if (_bufferFilled < offset || offset <= 0) return 0;
            int idx = (_bufferIndex - offset + _deltaBuffer.Length) % _deltaBuffer.Length;
            return _deltaBuffer[idx];
        }

        private bool CheckSpreadDynamic()
        {
            int spread = SpreadInPoints();
            if (spread > MaxSpreadPoints) return false;
            double avg = AverageSpreadPoints();
            return avg <= 0 || spread <= avg * SpreadAvgMultiplier;
        }

        private bool CheckGuards(out string reason)
        {
            reason = string.Empty;
            if (!IsTradingDayAllowed()) { reason = "weekday_blocked"; return false; }
            if (!IsInSession()) { reason = "out_of_session"; return false; }
            if (GetOpenPosition() != null) { reason = "already_has_open_position"; return false; }
            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread_too_high"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "daily_trade_limit_hit"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "consecutive_loss_limit_hit"; return false; }

            double dailyPct = _dayStartBalance * MaxDailyLossPercent / 100.0;
            double dailyLimit = Math.Min(dailyPct, MaxDailyLossMoney);
            if (dailyLimit > 0 && _dailyClosedPnl <= -dailyLimit) { reason = "daily_loss_limit_hit"; return false; }
            if (_dailyClosedPnl >= DailyProfitTargetMoney) { reason = "daily_profit_target_hit"; return false; }
            if (IsDailyEquityDrawdownHit()) { reason = "daily_equity_drawdown_hit"; return false; }
            if (IsAccountEquityDrawdownHit()) { reason = "account_equity_drawdown_hit"; return false; }
            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddSeconds(MinSecondsBetweenTrades)) { reason = "cooldown_active"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "loss_cooldown_active"; return false; }

            double atr = ClosedAtrValue();
            if (atr <= 0) { reason = "closed_atr_unavailable"; return false; }
            if (atr < MinAtr) { reason = "atr_too_low"; return false; }
            if (atr > MaxAtr) { reason = "atr_too_high"; return false; }
            return true;
        }

        private bool IsTradingDayAllowed()
        {
            switch (Server.Time.ToUniversalTime().DayOfWeek)
            {
                case DayOfWeek.Monday:
                case DayOfWeek.Tuesday:
                case DayOfWeek.Wednesday:
                case DayOfWeek.Friday:
                    return true;
                default:
                    return false;
            }
        }

        private bool IsInSession()
        {
            int now = Server.Time.ToUniversalTime().Hour * 60 + Server.Time.ToUniversalTime().Minute;
            return now >= SessionStartMinuteOfDay && now < SessionEndMinuteOfDay;
        }

        private void OpenTrade(int signal)
        {
            double atr = ClosedAtrValue();
            double slPips = PriceDistanceToPips(atr * SlAtrMultiplier);
            double tpPips = PriceDistanceToPips(atr * TpAtrMultiplier);
            string reason;
            if (!ValidateStopDistances(slPips, tpPips, out reason)) { Skip(reason); return; }

            double riskMoney = CalculateRiskMoney();
            double volume = Symbol.VolumeForFixedRisk(riskMoney, slPips, RoundingMode.Down);
            double cap = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            volume = Math.Min(volume, cap);
            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume < Symbol.VolumeInUnitsMin) { Skip("normalized_volume_below_broker_minimum"); return; }

            double totalCostPips = EstimateRoundTripCostPips(volume);
            double ratio = totalCostPips > 0 ? tpPips / totalCostPips : double.PositiveInfinity;
            if (ratio < MinimumExpectedMoveToCostRatio)
            {
                Skip("economic_floor_ratio_" + ratio.ToString("F2"));
                return;
            }

            TradeType type = signal > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful) { Skip("order_rejected_" + result.Error); return; }

            _lastTradeTime = Server.Time;
            _openTradeTime = Server.Time;
            _dailyTradeCount++;
            Debug("OPEN " + type + " vol=" + volume + " sl=" + slPips.ToString("F2") + " tp=" + tpPips.ToString("F2") + " costPips=" + totalCostPips.ToString("F2") + " moveCost=" + ratio.ToString("F2"));
        }

        private double CalculateRiskMoney()
        {
            double risk = FixedMoneyRisk * Account.Balance / RiskReferenceBalance;
            return Math.Max(MinFixedMoneyRisk, risk);
        }

        private double EstimateCandidateCostPips(double atr)
        {
            if (atr <= 0) return 0.0;
            double slPips = PriceDistanceToPips(atr * SlAtrMultiplier);
            double volume = Symbol.VolumeForFixedRisk(CalculateRiskMoney(), slPips, RoundingMode.Down);
            double cap = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            volume = Math.Min(volume, cap);
            volume = Math.Min(Math.Max(volume, Symbol.VolumeInUnitsMin), Symbol.VolumeInUnitsMax);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            return EstimateRoundTripCostPips(volume);
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

        private bool ValidateStopDistances(double slPips, double tpPips, out string reason)
        {
            reason = string.Empty;
            if (slPips <= 0 || tpPips <= 0) { reason = "invalid_sl_tp_distance"; return false; }
            double slDistance = slPips * Symbol.PipSize;
            double tpDistance = tpPips * Symbol.PipSize;
            if (Symbol.MinStopLossDistance > 0 && slDistance < Symbol.MinStopLossDistance) { reason = "sl_below_broker_minimum"; return false; }
            if (Symbol.MinTakeProfitDistance > 0 && tpDistance < Symbol.MinTakeProfitDistance) { reason = "tp_below_broker_minimum"; return false; }
            return true;
        }

        private void ManageOpenPositionTick(Position position)
        {
            string reason;
            if (CheckCriticalEquityExit(out reason))
            {
                ClosePositionWithLog(position, reason);
                return;
            }

            if (MaxTradeSeconds > 0 && _openTradeTime != DateTime.MinValue && Server.Time >= _openTradeTime.AddSeconds(MaxTradeSeconds))
                ClosePositionWithLog(position, "TIME_EXIT");
        }

        private bool CheckCriticalEquityExit(out string reason)
        {
            reason = string.Empty;
            if (IsFloatingLossHit()) { reason = "FLOATING_LOSS_GUARD"; return true; }
            if (IsDailyEquityDrawdownHit()) { reason = "DAILY_EQUITY_DD_GUARD"; return true; }
            if (IsAccountEquityDrawdownHit()) { reason = "ACCOUNT_EQUITY_DD_GUARD"; return true; }
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
            return (_accountPeakEquity - Account.Equity) / _accountPeakEquity * 100.0 >= MaxEquityDrawdownPercent;
        }

        private void UpdateEquityPeaks()
        {
            if (Account.Equity > _dayHighEquity) _dayHighEquity = Account.Equity;
            if (Account.Equity > _accountPeakEquity) _accountPeakEquity = Account.Equity;
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
                if (trades[i].NetProfit < 0) _consecutiveLosses++;
                else break;
            }
            var last = trades.LastOrDefault();
            if (last != null)
            {
                _lastTradeTime = last.ClosingTime;
                if (last.NetProfit < 0) _lastLossTime = last.ClosingTime;
            }
        }

        private void ResetDailyIfNeeded()
        {
            DateTime today = Server.Time.Date;
            if (today == _currentDay) return;
            _currentDay = today;
            _dayStartBalance = Account.Balance;
            _dayHighEquity = Account.Equity;
            _dailyClosedPnl = 0;
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
            if (p.SymbolName != SymbolName || p.Label != TradeLabel) return;
            if (p.NetProfit < 0)
            {
                _consecutiveLosses++;
                _lastLossTime = Server.Time;
            }
            else if (p.NetProfit > 0)
            {
                _consecutiveLosses = 0;
            }
            Debug("POSITION_CLOSED type=" + p.TradeType + " net=" + p.NetProfit.ToString("F2") + " entry=" + p.EntryPrice.ToString("F5"));
            _openTradeTime = DateTime.MinValue;
        }

        private void ClosePositionWithLog(Position p, string reason)
        {
            TradeResult result = ClosePosition(p);
            Debug(result.IsSuccessful ? "CLOSE " + reason : "close failed " + result.Error);
        }

        private int SpreadInPoints()
        {
            return (int)Math.Round(Symbol.Spread / Symbol.TickSize);
        }

        private double AverageSpreadPoints()
        {
            if (_spreadHistoryFilled <= 0) return 0.0;
            long sum = 0;
            for (int i = 0; i < _spreadHistoryFilled; i++) sum += _spreadHistory[i];
            return (double)sum / _spreadHistoryFilled;
        }

        private double PriceDistanceToPips(double distance)
        {
            return distance / Symbol.PipSize;
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
