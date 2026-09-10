using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum CdsK3RiskMode
    {
        FixedLots = 0,
        RiskPercent = 1,
        FixedMoneyRisk = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_K3 : Robot
    {
        private const string Prefix = "[CDScalper-EURUSD-K3] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;
        private const int RequiredContextConfirmations = 2;

        [Parameter("Bot Label", DefaultValue = "CDScalper_EURUSD_K3", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Allowed Symbol Prefix", DefaultValue = "EURUSD", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Expected Leverage", DefaultValue = 500.0, MinValue = 1.0, Group = "General")]
        public double ExpectedLeverage { get; set; }

        [Parameter("Window Size", DefaultValue = 10, MinValue = 2, Group = "Delta")]
        public int WindowSize { get; set; }

        [Parameter("Delta Threshold", DefaultValue = 125, MinValue = 1, Group = "Delta")]
        public int DeltaThreshold { get; set; }

        [Parameter("Use Bar Delta Fallback", DefaultValue = true, Group = "Delta")]
        public bool UseBarDeltaFallback { get; set; }

        [Parameter("Fallback Below Tick Delta", DefaultValue = 2, MinValue = 0, Group = "Delta")]
        public int FallbackBelowTickDelta { get; set; }

        [Parameter("Bar Delta Point Mult", DefaultValue = 1.6, MinValue = 0.1, Step = 0.1, Group = "Delta")]
        public double BarDeltaPointMultiplier { get; set; }

        [Parameter("Use Session Filter", DefaultValue = true, Group = "Sessions")]
        public bool UseSessionFilter { get; set; }

        [Parameter("Session Start H", DefaultValue = 14, MinValue = 0, MaxValue = 23, Group = "Sessions")]
        public int SessionStartHour { get; set; }

        [Parameter("Session Start M", DefaultValue = 0, MinValue = 0, MaxValue = 59, Group = "Sessions")]
        public int SessionStartMinute { get; set; }

        [Parameter("Session End H", DefaultValue = 14, MinValue = 0, MaxValue = 23, Group = "Sessions")]
        public int SessionEndHour { get; set; }

        [Parameter("Session End M", DefaultValue = 54, MinValue = 0, MaxValue = 59, Group = "Sessions")]
        public int SessionEndMinute { get; set; }

        [Parameter("Trade Monday", DefaultValue = true, Group = "Weekday Filter")]
        public bool TradeMonday { get; set; }

        [Parameter("Trade Tuesday", DefaultValue = true, Group = "Weekday Filter")]
        public bool TradeTuesday { get; set; }

        [Parameter("Trade Wednesday", DefaultValue = true, Group = "Weekday Filter")]
        public bool TradeWednesday { get; set; }

        [Parameter("Trade Thursday", DefaultValue = false, Group = "Weekday Filter")]
        public bool TradeThursday { get; set; }

        [Parameter("Trade Friday", DefaultValue = true, Group = "Weekday Filter")]
        public bool TradeFriday { get; set; }

        [Parameter("HTF Timeframe", DefaultValue = "Minute15", Group = "Filters")]
        public string HtfTimeFrameName { get; set; }

        [Parameter("EMA Slope Bars", DefaultValue = 3, MinValue = 1, Group = "Filters")]
        public int EmaSlopeBars { get; set; }

        [Parameter("ADX Threshold", DefaultValue = 16.0, MinValue = 0.0, Step = 0.5, Group = "Filters")]
        public double AdxThreshold { get; set; }

        [Parameter("Min ATR", DefaultValue = 0.00005, MinValue = 0.0, Step = 0.00001, Group = "Filters")]
        public double MinAtr { get; set; }

        [Parameter("Max ATR", DefaultValue = 0.00105, MinValue = 0.0, Step = 0.00001, Group = "Filters")]
        public double MaxAtr { get; set; }

        [Parameter("Max Spread Points", DefaultValue = 18, MinValue = 1, Group = "Execution")]
        public int MaxSpreadPoints { get; set; }

        [Parameter("Spread Avg Multiplier", DefaultValue = 1.8, MinValue = 1.0, Step = 0.1, Group = "Execution")]
        public double SpreadAvgMultiplier { get; set; }

        [Parameter("Spread History Size", DefaultValue = 30, MinValue = 1, Group = "Execution")]
        public int SpreadHistorySize { get; set; }

        [Parameter("Min ExpectedMove/Cost", DefaultValue = 1.0, MinValue = 1.0, Step = 0.1, Group = "Execution")]
        public double MinimumExpectedMoveToCostRatio { get; set; }

        [Parameter("Commission USD/Million", DefaultValue = 35.0, MinValue = 0.0, Step = 1.0, Group = "Execution")]
        public double CommissionUsdPerMillion { get; set; }

        [Parameter("Commission Round Trip", DefaultValue = true, Group = "Execution")]
        public bool CommissionIsPerSide { get; set; }

        [Parameter("Execution Safety Pips", DefaultValue = 0.2, MinValue = 0.0, Step = 0.1, Group = "Execution")]
        public double ExecutionSafetyBufferPips { get; set; }

        [Parameter("Risk Mode", DefaultValue = CdsK3RiskMode.FixedMoneyRisk, Group = "Risk")]
        public CdsK3RiskMode RiskMode { get; set; }

        [Parameter("Fixed Money Risk", DefaultValue = 1.0, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Auto Scale Fixed Risk", DefaultValue = true, Group = "Risk")]
        public bool AutoScaleFixedRisk { get; set; }

        [Parameter("Risk Reference Balance", DefaultValue = 100.0, MinValue = 1.0, Group = "Risk")]
        public double RiskReferenceBalance { get; set; }

        [Parameter("Min Fixed Money Risk", DefaultValue = 0.05, MinValue = 0.0, Step = 0.01, Group = "Risk")]
        public double MinFixedMoneyRisk { get; set; }

        [Parameter("Risk % per Trade", DefaultValue = 1.0, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double RiskPercentPerTrade { get; set; }

        [Parameter("Fixed Lot Size", DefaultValue = 0.01, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedLotSize { get; set; }

        [Parameter("Max Lot Size", DefaultValue = 0.05, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double MaxLotSize { get; set; }

        [Parameter("SL Multiplier ATR", DefaultValue = 0.8, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double SlAtrMultiplier { get; set; }

        [Parameter("TP Multiplier ATR", DefaultValue = 1.0, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double TpAtrMultiplier { get; set; }

        [Parameter("Max Daily Trades", DefaultValue = 3, MinValue = 1, Group = "Protection")]
        public int MaxDailyTrades { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 4.0, MinValue = 0.1, Step = 0.1, Group = "Protection")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Daily Loss Money", DefaultValue = 0.55, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Daily Profit Target Money", DefaultValue = 1.10, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double DailyProfitTargetMoney { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 2, MinValue = 1, Group = "Protection")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Min Sec Between Trades", DefaultValue = 900, MinValue = 0, Group = "Protection")]
        public int MinSecondsBetweenTrades { get; set; }

        [Parameter("Loss Cooldown Min", DefaultValue = 45, MinValue = 0, Group = "Protection")]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Max Daily Equity DD Money", DefaultValue = 0.75, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxDailyEquityDrawdownMoney { get; set; }

        [Parameter("Max Floating Loss Money", DefaultValue = 0.90, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxFloatingLossMoney { get; set; }

        [Parameter("Max Equity DD %", DefaultValue = 12.0, MinValue = 0.0, Step = 0.1, Group = "Protection")]
        public double MaxEquityDrawdownPercent { get; set; }

        [Parameter("Close On Equity Guard", DefaultValue = true, Group = "Protection")]
        public bool CloseOnEquityGuard { get; set; }

        [Parameter("Max Trade Seconds", DefaultValue = 1800, MinValue = 0, Group = "Exit")]
        public int MaxTradeSeconds { get; set; }

        [Parameter("Use Breakeven", DefaultValue = true, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("BE Trigger ATR", DefaultValue = 0.5, MinValue = 0.1, Step = 0.1, Group = "Exit")]
        public double BreakevenTriggerAtr { get; set; }

        [Parameter("BE Cost Buffer Pips", DefaultValue = 0.2, MinValue = 0.0, Step = 0.1, Group = "Exit")]
        public double BreakevenCostBufferPips { get; set; }

        [Parameter("Adverse Delta Exit", DefaultValue = true, Group = "Exit")]
        public bool AdverseDeltaExit { get; set; }

        private AverageTrueRange _atr;
        private ExponentialMovingAverage _htfEma;
        private DirectionalMovementSystem _htfDms;
        private Bars _htfBars;

        private double _prevBid;
        private int _uptickCount;
        private int _downtickCount;
        private int[] _deltaBuffer;
        private int _bufferIndex;
        private int _bufferFilled;
        private int _prevCumDelta;
        private int[] _spreadHistory;
        private int _spreadHistoryIndex;
        private int _spreadHistoryFilled;

        private DateTime _lastProcessedBarTime = DateTime.MinValue;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private DateTime _openTradeTime = DateTime.MinValue;
        private bool _breakevenApplied;

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
                Print(Prefix + "K3 commercial research requires EURUSD M1.");
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
            _htfBars = MarketData.GetBars(ResolveHtfTimeFrame());
            _htfEma = Indicators.ExponentialMovingAverage(_htfBars.ClosePrices, EmaPeriod);
            _htfDms = Indicators.DirectionalMovementSystem(_htfBars, AdxPeriod);
            _deltaBuffer = new int[Math.Max(2, WindowSize)];
            _spreadHistory = new int[Math.Max(1, SpreadHistorySize)];
            _prevBid = Symbol.Bid;
            _currentDay = Server.Time.Date;
            _dayStartBalance = Account.Balance;
            _dayHighEquity = Account.Equity;
            _accountPeakEquity = Account.Equity;
            Positions.Closed += OnPositionClosed;
            RestoreRuntimeState();
            Debug("started; Flow-First hierarchy active; mandatory 3-bar delta persistence + closed-bar price acceptance + 2/4 context; cost gate floor=1.0; hard protections retained");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            if (DebugLogging)
            {
                foreach (var kv in _skipReasons.OrderByDescending(x => x.Value))
                    Print(Prefix + "SKIP_SUMMARY " + kv.Key + "=" + kv.Value);
            }
        }

        protected override void OnTick()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            UpdateEquityPeaks();
            ProcessTickDelta();
            Position p = GetOpenPosition();
            if (p != null)
                ManageOpenPositionTick(p);
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

            Position open = GetOpenPosition();
            if (open != null)
            {
                if (AdverseDeltaExit && IsConfirmedClosedBarAdverse(open))
                    ClosePositionWithLog(open, "ADVERSE_DELTA_CLOSED_BAR");
                return;
            }

            string guardReason;
            if (!CheckGuards(out guardReason))
            {
                Skip(guardReason);
                return;
            }

            int signal = CheckSignalFlowFirst();
            if (signal == 0)
                return;

            OpenTrade(signal);
        }

        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            return SymbolName.ToUpperInvariant().StartsWith(allowed);
        }

        private TimeFrame ResolveHtfTimeFrame()
        {
            string v = string.IsNullOrWhiteSpace(HtfTimeFrameName) ? "MINUTE15" : HtfTimeFrameName.Trim().ToUpperInvariant();
            if (v == "MINUTE15" || v == "M15" || v == "15") return TimeFrame.Minute15;
            return TimeFrame.Minute15;
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
            if (UseBarDeltaFallback && Math.Abs(tickDelta) <= FallbackBelowTickDelta)
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
            int index = Bars.ClosePrices.Count - 2;
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
            double weighted = bodyPoints * Math.Max(0.1, BarDeltaPointMultiplier) * Math.Max(0.25, dominance);
            int estimated = (int)Math.Round(weighted);
            if (estimated == 0) estimated = body > 0 ? 1 : -1;
            return estimated;
        }

        private int CheckSignalFlowFirst()
        {
            if (_bufferFilled < _deltaBuffer.Length)
            {
                Skip("entry_buffer_not_ready");
                return 0;
            }

            int cumulativeDelta = CalculateCumulativeDelta();
            int previous = _prevCumDelta;
            _prevCumDelta = cumulativeDelta;

            int signal = 0;
            if (previous <= DeltaThreshold && cumulativeDelta > DeltaThreshold) signal = 1;
            else if (previous >= -DeltaThreshold && cumulativeDelta < -DeltaThreshold) signal = -1;

            if (signal == 0)
            {
                Skip("entry_no_delta_cross");
                return 0;
            }

            if (!CheckMomentum(signal))
            {
                Skip("entry_flow_not_persistent");
                return 0;
            }

            int closedIndex = Bars.ClosePrices.Count - 2;
            if (closedIndex < 0)
            {
                Skip("entry_closed_bar_unavailable");
                return 0;
            }

            double open = Bars.OpenPrices[closedIndex];
            double close = Bars.ClosePrices[closedIndex];
            bool priceAccepted = signal > 0 ? close > open : close < open;
            if (!priceAccepted)
            {
                Skip("entry_price_rejected_flow");
                return 0;
            }

            int context = 0;
            if (CheckHtfEma(signal)) context++;
            if (CheckEmaSlope(signal)) context++;
            if (_htfDms.ADX.LastValue >= AdxThreshold) context++;
            if (CheckSpreadDynamic()) context++;

            if (context < RequiredContextConfirmations)
            {
                Skip("entry_context_insufficient_" + context);
                return 0;
            }

            Debug("SIGNAL_ACCEPT dir=" + signal + " cumDelta=" + cumulativeDelta + " prev=" + previous + " context=" + context + " closedOpen=" + open.ToString("F5") + " closedClose=" + close.ToString("F5") + " atr=" + _atr.Result.LastValue.ToString("F6") + " spreadPts=" + SpreadInPoints());
            return signal;
        }

        private int CalculateCumulativeDelta()
        {
            int sum = 0;
            for (int i = 0; i < _bufferFilled; i++) sum += _deltaBuffer[i];
            return sum;
        }

        private bool CheckMomentum(int signal)
        {
            if (_bufferFilled < 3) return false;
            for (int i = 1; i <= 3; i++)
            {
                int idx = (_bufferIndex - i + _deltaBuffer.Length) % _deltaBuffer.Length;
                int d = _deltaBuffer[idx];
                if (signal > 0 && d <= 0) return false;
                if (signal < 0 && d >= 0) return false;
            }
            return true;
        }

        private bool CheckHtfEma(int signal)
        {
            double ema = _htfEma.Result.LastValue;
            if (ema <= 0) return false;
            return signal > 0 ? Symbol.Bid > ema : Symbol.Bid < ema;
        }

        private bool CheckEmaSlope(int signal)
        {
            int last = _htfEma.Result.Count - 1;
            int bars = Math.Max(1, EmaSlopeBars);
            if (last < bars) return false;
            return signal > 0 ? _htfEma.Result[last] > _htfEma.Result[last - bars] : _htfEma.Result[last] < _htfEma.Result[last - bars];
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
            if (UseSessionFilter && !IsInSession()) { reason = "out_of_session"; return false; }
            if (GetOpenPosition() != null) { reason = "already_has_open_position"; return false; }
            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread_too_high"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "daily_trade_limit_hit"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "consecutive_loss_limit_hit"; return false; }
            double dailyPct = _dayStartBalance * MaxDailyLossPercent / 100.0;
            double dailyLimit = MaxDailyLossMoney > 0 ? Math.Min(dailyPct, MaxDailyLossMoney) : dailyPct;
            if (dailyLimit > 0 && _dailyClosedPnl <= -dailyLimit) { reason = "daily_loss_limit_hit"; return false; }
            if (DailyProfitTargetMoney > 0 && _dailyClosedPnl >= DailyProfitTargetMoney) { reason = "daily_profit_target_hit"; return false; }
            if (IsDailyEquityDrawdownHit()) { reason = "daily_equity_drawdown_hit"; return false; }
            if (IsAccountEquityDrawdownHit()) { reason = "account_equity_drawdown_hit"; return false; }
            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddSeconds(MinSecondsBetweenTrades)) { reason = "cooldown_active"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "loss_cooldown_active"; return false; }
            double atr = _atr.Result.LastValue;
            if (atr < MinAtr) { reason = "atr_too_low"; return false; }
            if (MaxAtr > 0 && atr > MaxAtr) { reason = "atr_too_high"; return false; }
            return true;
        }

        private bool IsTradingDayAllowed()
        {
            switch (Server.Time.ToUniversalTime().DayOfWeek)
            {
                case DayOfWeek.Monday: return TradeMonday;
                case DayOfWeek.Tuesday: return TradeTuesday;
                case DayOfWeek.Wednesday: return TradeWednesday;
                case DayOfWeek.Thursday: return TradeThursday;
                case DayOfWeek.Friday: return TradeFriday;
                default: return false;
            }
        }

        private bool IsInSession()
        {
            int now = Server.Time.ToUniversalTime().Hour * 60 + Server.Time.ToUniversalTime().Minute;
            int start = SessionStartHour * 60 + SessionStartMinute;
            int end = SessionEndHour * 60 + SessionEndMinute;
            if (start == end) return true;
            if (start < end) return now >= start && now < end;
            return now >= start || now < end;
        }

        private void OpenTrade(int signal)
        {
            double atr = _atr.Result.LastValue;
            double slPips = PriceDistanceToPips(atr * SlAtrMultiplier);
            double tpPips = PriceDistanceToPips(atr * TpAtrMultiplier);
            string reason;
            if (!ValidateStopDistances(slPips, tpPips, out reason)) { Skip(reason); return; }

            double riskMoney = CalculateRiskMoney();
            double volume = CalculateVolumeInUnits(slPips, riskMoney);
            if (volume < Symbol.VolumeInUnitsMin) { Skip("volume_below_broker_minimum"); return; }
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
            _breakevenApplied = false;
            _dailyTradeCount++;
            Debug("OPEN " + type + " vol=" + volume + " sl=" + slPips.ToString("F2") + " tp=" + tpPips.ToString("F2") + " costPips=" + totalCostPips.ToString("F2") + " moveCost=" + ratio.ToString("F2"));
        }

        private double EstimateRoundTripCostPips(double volume)
        {
            double spreadPips = Symbol.Spread / Symbol.PipSize;
            double mid = (Symbol.Bid + Symbol.Ask) / 2.0;
            double notionalUsd = volume * mid;
            double sides = CommissionIsPerSide ? 2.0 : 1.0;
            double commissionMoney = CommissionUsdPerMillion > 0 ? notionalUsd / 1000000.0 * CommissionUsdPerMillion * sides : 0.0;
            double pipValueForVolume = Math.Abs(Symbol.PipValue * volume);
            double commissionPips = pipValueForVolume > 0 ? commissionMoney / pipValueForVolume : 0.0;
            return Math.Max(0.0, spreadPips) + Math.Max(0.0, commissionPips) + Math.Max(0.0, ExecutionSafetyBufferPips);
        }

        private double CalculateRiskMoney()
        {
            if (RiskMode == CdsK3RiskMode.FixedLots) return 0;
            if (RiskMode == CdsK3RiskMode.RiskPercent) return Account.Balance * RiskPercentPerTrade / 100.0;
            double r = FixedMoneyRisk;
            if (AutoScaleFixedRisk && RiskReferenceBalance > 0) r = FixedMoneyRisk * Account.Balance / RiskReferenceBalance;
            if (MinFixedMoneyRisk > 0) r = Math.Max(MinFixedMoneyRisk, r);
            return Math.Max(0, r);
        }

        private double CalculateVolumeInUnits(double stopLossPips, double riskMoney)
        {
            if (RiskMode == CdsK3RiskMode.FixedLots)
                return Symbol.QuantityToVolumeInUnits(Math.Min(FixedLotSize, MaxLotSize));
            if (riskMoney <= 0 || stopLossPips <= 0) return 0;
            double volume = Symbol.VolumeForFixedRisk(riskMoney, stopLossPips, RoundingMode.Down);
            double cap = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            return Math.Min(volume, cap);
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

        private void ManageOpenPositionTick(Position p)
        {
            string reason;
            if (CloseOnEquityGuard && CheckCriticalEquityExit(out reason)) { ClosePositionWithLog(p, reason); return; }
            if (MaxTradeSeconds > 0 && _openTradeTime != DateTime.MinValue && Server.Time >= _openTradeTime.AddSeconds(MaxTradeSeconds)) { ClosePositionWithLog(p, "TIME_EXIT"); return; }
            if (UseBreakeven && !_breakevenApplied) TryAtrBreakeven(p);
        }

        private void TryAtrBreakeven(Position p)
        {
            double triggerPips = PriceDistanceToPips(_atr.Result.LastValue * BreakevenTriggerAtr);
            double bufferPrice = BreakevenCostBufferPips * Symbol.PipSize;
            double? tp = p.TakeProfit;
            if (p.TradeType == TradeType.Buy)
            {
                double profitPips = (Symbol.Bid - p.EntryPrice) / Symbol.PipSize;
                if (profitPips < triggerPips) return;
                double newSl = p.EntryPrice + bufferPrice;
                if (!p.StopLoss.HasValue || newSl > p.StopLoss.Value)
                {
                    TradeResult r = ModifyPosition(p, newSl, tp);
                    if (r.IsSuccessful) _breakevenApplied = true;
                }
            }
            else
            {
                double profitPips = (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (profitPips < triggerPips) return;
                double newSl = p.EntryPrice - bufferPrice;
                if (!p.StopLoss.HasValue || newSl < p.StopLoss.Value)
                {
                    TradeResult r = ModifyPosition(p, newSl, tp);
                    if (r.IsSuccessful) _breakevenApplied = true;
                }
            }
        }

        private bool IsConfirmedClosedBarAdverse(Position p)
        {
            if (_bufferFilled < _deltaBuffer.Length) return false;
            int index = Bars.ClosePrices.Count - 2;
            if (index < 0) return false;
            int cumulativeDelta = CalculateCumulativeDelta();
            double open = Bars.OpenPrices[index];
            double close = Bars.ClosePrices[index];
            if (p.TradeType == TradeType.Buy)
                return cumulativeDelta < -DeltaThreshold && close < open && close < p.EntryPrice;
            return cumulativeDelta > DeltaThreshold && close > open && close > p.EntryPrice;
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
            if (MaxFloatingLossMoney <= 0) return false;
            double pnl = Positions.Where(x => x.SymbolName == SymbolName && x.Label == TradeLabel).Sum(x => x.NetProfit);
            return pnl <= -MaxFloatingLossMoney;
        }

        private bool IsDailyEquityDrawdownHit()
        {
            return MaxDailyEquityDrawdownMoney > 0 && (_dayHighEquity - Account.Equity) >= MaxDailyEquityDrawdownMoney;
        }

        private bool IsAccountEquityDrawdownHit()
        {
            if (MaxEquityDrawdownPercent <= 0 || _accountPeakEquity <= 0) return false;
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
            {
                _openTradeTime = p.EntryTime;
                if (p.StopLoss.HasValue)
                    _breakevenApplied = p.TradeType == TradeType.Buy ? p.StopLoss.Value >= p.EntryPrice : p.StopLoss.Value <= p.EntryPrice;
            }

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
            if (p.NetProfit < 0) { _consecutiveLosses++; _lastLossTime = Server.Time; }
            else if (p.NetProfit > 0) _consecutiveLosses = 0;
            Debug("POSITION_CLOSED type=" + p.TradeType + " net=" + p.NetProfit.ToString("F2") + " entry=" + p.EntryPrice.ToString("F5"));
            _openTradeTime = DateTime.MinValue;
            _breakevenApplied = false;
        }

        private void ClosePositionWithLog(Position p, string reason)
        {
            TradeResult r = ClosePosition(p);
            Debug(r.IsSuccessful ? "CLOSE " + reason : "close failed " + r.Error);
        }

        private int SpreadInPoints()
        {
            return (int)Math.Round(Symbol.Spread / Symbol.TickSize);
        }

        private double AverageSpreadPoints()
        {
            if (_spreadHistoryFilled <= 0) return 0;
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
            int v;
            if (_skipReasons.TryGetValue(reason, out v)) _skipReasons[reason] = v + 1;
            else _skipReasons[reason] = 1;
            Debug("SKIP " + reason);
        }

        private void Debug(string message)
        {
            if (DebugLogging) Print(Prefix + message);
        }
    }
}
