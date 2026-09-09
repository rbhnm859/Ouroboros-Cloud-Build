// ===================================================================
//  CumulativeDeltaScalper_EURUSD_v1
//  Hardened cTrader / cAlgo EURUSD-only baseline.
//
//  Derived from:
//  https://github.com/dhruuvsharma/Trading-Strategies
//  platforms/cTrader/CumulativeDeltaScalper/src/CumulativeDeltaScalper.cs
//
//  Design goals:
//  - EURUSD / EURUSD suffix only
//  - M1, M5, M15, M30 only
//  - One completed-bar entry decision, not repeated OnTick entries
//  - One position only, no hedging, no grid, no martingale, no DCA
//  - Every market order is sent with SL and TP
//  - Fixed money risk / risk percent / fixed lots modes
//  - Broker min/max/step volume checks
//  - Daily loss/profit guards, cooldown, consecutive-loss stop
//  - Bar-delta fallback for cTrader CLI M1 backtests when tick delta is not populated
// ===================================================================

using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum CdsRiskMode
    {
        FixedLots = 0,
        RiskPercent = 1,
        FixedMoneyRisk = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_EURUSD_v1 : Robot
    {
        private const string Prefix = "[CDScalper-EURUSD-v1] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;
        private const double BreakevenBufferPips = 0.5;

        [Parameter("Bot Label", DefaultValue = "CDScalper_EURUSD_v1", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Allowed Symbol Prefix", DefaultValue = "EURUSD", Group = "General")]
        public string AllowedSymbolPrefix { get; set; }

        [Parameter("Allow M1", DefaultValue = true, Group = "General")]
        public bool AllowM1 { get; set; }

        [Parameter("Allow M5", DefaultValue = true, Group = "General")]
        public bool AllowM5 { get; set; }

        [Parameter("Allow M15", DefaultValue = true, Group = "General")]
        public bool AllowM15 { get; set; }

        [Parameter("Allow M30", DefaultValue = true, Group = "General")]
        public bool AllowM30 { get; set; }

        [Parameter("Window Size", DefaultValue = 10, MinValue = 2, Group = "Delta")]
        public int WindowSize { get; set; }

        [Parameter("Delta Threshold", DefaultValue = 300, MinValue = 1, Group = "Delta")]
        public int DeltaThreshold { get; set; }

        [Parameter("Min Confirmations", DefaultValue = 5, MinValue = 0, MaxValue = 5, Group = "Delta")]
        public int MinConfirmations { get; set; }

        [Parameter("Use Bar Delta Fallback", DefaultValue = true, Group = "Delta")]
        public bool UseBarDeltaFallback { get; set; }

        [Parameter("Fallback Below Tick Delta", DefaultValue = 2, MinValue = 0, Group = "Delta")]
        public int FallbackBelowTickDelta { get; set; }

        [Parameter("Bar Delta Point Mult", DefaultValue = 1.0, MinValue = 0.1, Step = 0.1, Group = "Delta")]
        public double BarDeltaPointMultiplier { get; set; }

        [Parameter("Use Session Filter", DefaultValue = true, Group = "Sessions")]
        public bool UseSessionFilter { get; set; }

        [Parameter("Overlap Only", DefaultValue = true, Group = "Sessions")]
        public bool OverlapOnly { get; set; }

        [Parameter("Session Start H", DefaultValue = 12, MinValue = 0, MaxValue = 23, Group = "Sessions")]
        public int SessionStartHour { get; set; }

        [Parameter("Session Start M", DefaultValue = 30, MinValue = 0, MaxValue = 59, Group = "Sessions")]
        public int SessionStartMinute { get; set; }

        [Parameter("Session End H", DefaultValue = 16, MinValue = 0, MaxValue = 23, Group = "Sessions")]
        public int SessionEndHour { get; set; }

        [Parameter("Session End M", DefaultValue = 0, MinValue = 0, MaxValue = 59, Group = "Sessions")]
        public int SessionEndMinute { get; set; }

        [Parameter("Use HTF EMA Filter", DefaultValue = true, Group = "Filters")]
        public bool UseHtfEmaFilter { get; set; }

        [Parameter("EMA Slope Bars", DefaultValue = 3, MinValue = 1, Group = "Filters")]
        public int EmaSlopeBars { get; set; }

        [Parameter("ADX Threshold", DefaultValue = 18.0, MinValue = 0.0, Step = 0.5, Group = "Filters")]
        public double AdxThreshold { get; set; }

        [Parameter("Min ATR", DefaultValue = 0.00030, MinValue = 0.0, Step = 0.00005, Group = "Filters")]
        public double MinAtr { get; set; }

        [Parameter("Max ATR", DefaultValue = 0.00200, MinValue = 0.0, Step = 0.00005, Group = "Filters")]
        public double MaxAtr { get; set; }

        [Parameter("Max Spread Points", DefaultValue = 15, MinValue = 1, Group = "Execution")]
        public int MaxSpreadPoints { get; set; }

        [Parameter("Spread Avg Multiplier", DefaultValue = 1.5, MinValue = 1.0, Step = 0.1, Group = "Execution")]
        public double SpreadAvgMultiplier { get; set; }

        [Parameter("Spread History Size", DefaultValue = 30, MinValue = 1, Group = "Execution")]
        public int SpreadHistorySize { get; set; }

        [Parameter("Risk Mode", DefaultValue = CdsRiskMode.FixedMoneyRisk, Group = "Risk")]
        public CdsRiskMode RiskMode { get; set; }

        [Parameter("Fixed Money Risk", DefaultValue = 1.00, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Risk % per Trade", DefaultValue = 1.0, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double RiskPercentPerTrade { get; set; }

        [Parameter("Fixed Lot Size", DefaultValue = 0.01, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedLotSize { get; set; }

        [Parameter("Max Lot Size", DefaultValue = 0.05, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double MaxLotSize { get; set; }

        [Parameter("SL Multiplier ATR", DefaultValue = 0.8, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double SlAtrMultiplier { get; set; }

        [Parameter("TP Multiplier ATR", DefaultValue = 0.4, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double TpAtrMultiplier { get; set; }

        [Parameter("Max Daily Trades", DefaultValue = 3, MinValue = 1, Group = "Protection")]
        public int MaxDailyTrades { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 2.0, MinValue = 0.1, Step = 0.1, Group = "Protection")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Daily Loss Money", DefaultValue = 3.00, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Daily Profit Target Money", DefaultValue = 5.00, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double DailyProfitTargetMoney { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 2, MinValue = 1, Group = "Protection")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Min Sec Between Trades", DefaultValue = 900, MinValue = 0, Group = "Protection")]
        public int MinSecondsBetweenTrades { get; set; }

        [Parameter("Loss Cooldown Min", DefaultValue = 15, MinValue = 0, Group = "Protection")]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Max Trade Seconds", DefaultValue = 90, MinValue = 0, Group = "Exit")]
        public int MaxTradeSeconds { get; set; }

        [Parameter("Use Breakeven", DefaultValue = false, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven Pips", DefaultValue = 1.5, MinValue = 0.1, Step = 0.1, Group = "Exit")]
        public double BreakevenPips { get; set; }

        [Parameter("Adverse Delta Exit", DefaultValue = true, Group = "Exit")]
        public bool AdverseDeltaExit { get; set; }

        [Parameter("Adverse Delta Cooldown Sec", DefaultValue = 5, MinValue = 0, Group = "Exit")]
        public int AdverseDeltaCooldownSeconds { get; set; }

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
        private int _openTradeDirection;
        private bool _breakevenApplied;

        private DateTime _currentDay = DateTime.MinValue;
        private double _dayStartBalance;
        private double _dailyClosedPnl;
        private int _dailyTradeCount;
        private int _consecutiveLosses;

        protected override void OnStart()
        {
            if (!ValidateSymbol())
            {
                Print(Prefix + "invalid symbol: " + SymbolName + ". EURUSD prefix required.");
                Stop();
                return;
            }

            if (!ValidateTimeFrame())
            {
                Print(Prefix + "invalid timeframe: " + TimeFrame + ". Allowed: M1/M5/M15/M30.");
                Stop();
                return;
            }

            if (WindowSize < 2 || DeltaThreshold <= 0 || SlAtrMultiplier <= 0 || TpAtrMultiplier <= 0 || BarDeltaPointMultiplier <= 0)
            {
                Print(Prefix + "invalid core parameters");
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Simple);
            _htfBars = MarketData.GetBars(TimeFrame.Minute15);
            _htfEma = Indicators.ExponentialMovingAverage(_htfBars.ClosePrices, EmaPeriod);
            _htfDms = Indicators.DirectionalMovementSystem(_htfBars, AdxPeriod);

            _deltaBuffer = new int[WindowSize];
            _spreadHistory = new int[Math.Max(1, SpreadHistorySize)];
            _prevBid = Symbol.Bid;
            _currentDay = Server.Time.Date;
            _dayStartBalance = Account.Balance;

            Positions.Closed += OnPositionClosed;

            Debug("started on " + SymbolName + " " + TimeFrame + " label=" + TradeLabel + " barDeltaFallback=" + UseBarDeltaFallback);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            Debug("stopped");
        }

        protected override void OnTick()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            ProcessTickDelta();

            if (HasOpenPosition())
            {
                ManageOpenPosition();
            }
        }

        protected override void OnBar()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            FinalizeClosedBarDelta();

            DateTime barTime = Bars.OpenTimes.LastValue;
            if (barTime == _lastProcessedBarTime)
                return;
            _lastProcessedBarTime = barTime;

            if (HasOpenPosition())
            {
                Debug("already has open position");
                return;
            }

            string reason;
            if (!CheckGuards(out reason))
            {
                Debug("trade skipped: " + reason);
                return;
            }

            int signal = CheckSignal();
            if (signal == 0)
            {
                Debug("trade skipped: delta threshold not crossed or confirmations failed");
                return;
            }

            OpenTrade(signal);
        }

        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            string current = SymbolName.ToUpperInvariant();
            return current.StartsWith(allowed);
        }

        private bool ValidateTimeFrame()
        {
            if (AllowM1 && TimeFrame == TimeFrame.Minute) return true;
            if (AllowM5 && TimeFrame == TimeFrame.Minute5) return true;
            if (AllowM15 && TimeFrame == TimeFrame.Minute15) return true;
            if (AllowM30 && TimeFrame == TimeFrame.Minute30) return true;
            return false;
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
            int candleDelta = tickDelta;
            bool fallbackUsed = false;

            if (UseBarDeltaFallback && Math.Abs(tickDelta) <= FallbackBelowTickDelta)
            {
                int estimated = EstimateClosedBarDelta();
                if (estimated != 0)
                {
                    candleDelta = estimated;
                    fallbackUsed = true;
                }
            }

            _deltaBuffer[_bufferIndex] = candleDelta;
            _bufferIndex = (_bufferIndex + 1) % WindowSize;
            if (_bufferFilled < WindowSize) _bufferFilled++;

            int spread = SpreadInPoints();
            _spreadHistory[_spreadHistoryIndex] = spread;
            _spreadHistoryIndex = (_spreadHistoryIndex + 1) % _spreadHistory.Length;
            if (_spreadHistoryFilled < _spreadHistory.Length) _spreadHistoryFilled++;

            _uptickCount = 0;
            _downtickCount = 0;

            Debug("bar closed delta=" + candleDelta + " tickDelta=" + tickDelta + " fallback=" + fallbackUsed + " spreadPoints=" + spread);
        }

        private int EstimateClosedBarDelta()
        {
            int index = Bars.ClosePrices.Count - 2;
            if (index < 0)
                return 0;

            double open = Bars.OpenPrices[index];
            double close = Bars.ClosePrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double body = close - open;

            if (Math.Abs(body) < Symbol.TickSize)
                return 0;

            double range = Math.Max(Symbol.TickSize, high - low);
            double bodyPoints = body / Symbol.TickSize;
            double dominance = Math.Min(1.0, Math.Abs(body) / range);
            double weighted = bodyPoints * Math.Max(0.1, BarDeltaPointMultiplier) * Math.Max(0.25, dominance);
            int estimated = (int)Math.Round(weighted);

            if (estimated == 0)
                estimated = body > 0 ? 1 : -1;

            return estimated;
        }

        private int CheckSignal()
        {
            if (_bufferFilled < WindowSize)
                return 0;

            int cumulativeDelta = CalculateCumulativeDelta();
            int previous = _prevCumDelta;
            _prevCumDelta = cumulativeDelta;

            int signal = 0;
            if (previous <= DeltaThreshold && cumulativeDelta > DeltaThreshold) signal = 1;
            if (previous >= -DeltaThreshold && cumulativeDelta < -DeltaThreshold) signal = -1;
            if (signal == 0) return 0;

            int confirmations = 0;
            if (CheckMomentum(signal)) confirmations++;
            if (CheckHtfEma(signal)) confirmations++;
            if (CheckEmaSlope(signal)) confirmations++;
            if (CheckAdx()) confirmations++;
            if (CheckSpreadDynamic()) confirmations++;

            Debug("signal=" + signal + " confirmations=" + confirmations + "/5 need=" + MinConfirmations);
            return confirmations >= MinConfirmations ? signal : 0;
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
                int idx = (_bufferIndex - i + WindowSize) % WindowSize;
                int d = _deltaBuffer[idx];
                if (signal > 0 && d <= 0) return false;
                if (signal < 0 && d >= 0) return false;
            }
            return true;
        }

        private bool CheckHtfEma(int signal)
        {
            if (!UseHtfEmaFilter) return true;
            double ema = _htfEma.Result.LastValue;
            if (ema <= 0) return false;
            return signal > 0 ? Symbol.Bid > ema : Symbol.Bid < ema;
        }

        private bool CheckEmaSlope(int signal)
        {
            if (!UseHtfEmaFilter) return true;

            int last = _htfEma.Result.Count - 1;
            int bars = Math.Max(1, EmaSlopeBars);
            if (last < bars) return false;

            double newest = _htfEma.Result[last];
            double oldest = _htfEma.Result[last - bars];
            if (signal > 0) return newest > oldest;
            return newest < oldest;
        }

        private bool CheckAdx()
        {
            return _htfDms.ADX.LastValue >= AdxThreshold;
        }

        private bool CheckSpreadDynamic()
        {
            int spread = SpreadInPoints();
            if (spread > MaxSpreadPoints) return false;
            double avg = AverageSpreadPoints();
            if (avg <= 0) return true;
            return spread <= avg * SpreadAvgMultiplier;
        }

        private bool CheckGuards(out string reason)
        {
            reason = string.Empty;

            if (!ValidateSymbol()) { reason = "invalid symbol"; return false; }
            if (!ValidateTimeFrame()) { reason = "invalid timeframe"; return false; }
            if (UseSessionFilter && !IsInSession()) { reason = "out of session"; return false; }
            if (HasOpenPosition()) { reason = "already has open position"; return false; }
            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread too high"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "daily trade limit hit"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "consecutive loss limit hit"; return false; }

            double dailyLimitByPercent = _dayStartBalance * MaxDailyLossPercent / 100.0;
            double dailyLossLimit = MaxDailyLossMoney > 0 ? Math.Min(dailyLimitByPercent, MaxDailyLossMoney) : dailyLimitByPercent;
            if (dailyLossLimit > 0 && _dailyClosedPnl <= -dailyLossLimit) { reason = "daily loss limit hit"; return false; }
            if (DailyProfitTargetMoney > 0 && _dailyClosedPnl >= DailyProfitTargetMoney) { reason = "daily profit target hit"; return false; }

            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddSeconds(MinSecondsBetweenTrades)) { reason = "cooldown active"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "loss cooldown active"; return false; }

            double atr = _atr.Result.LastValue;
            if (atr < MinAtr) { reason = "ATR too low"; return false; }
            if (MaxAtr > 0 && atr > MaxAtr) { reason = "ATR too high"; return false; }

            return true;
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
            double slPips = PriceDistanceToPips(_atr.Result.LastValue * SlAtrMultiplier);
            double tpPips = PriceDistanceToPips(_atr.Result.LastValue * TpAtrMultiplier);

            string distanceReason;
            if (!ValidateStopDistances(slPips, tpPips, out distanceReason))
            {
                Debug("trade skipped: " + distanceReason);
                return;
            }

            double volume = CalculateVolumeInUnits(slPips);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Debug("volume below broker minimum, trade skipped. volume=" + volume + " min=" + Symbol.VolumeInUnitsMin);
                return;
            }

            if (volume > Symbol.VolumeInUnitsMax)
                volume = Symbol.VolumeInUnitsMax;

            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Debug("normalized volume below broker minimum, trade skipped");
                return;
            }

            TradeType tradeType = signal > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(tradeType, SymbolName, volume, TradeLabel, slPips, tpPips);

            if (!result.IsSuccessful)
            {
                Debug("order rejected by broker: " + result.Error);
                return;
            }

            _lastTradeTime = Server.Time;
            _openTradeTime = Server.Time;
            _openTradeDirection = signal;
            _breakevenApplied = false;
            _dailyTradeCount++;

            Debug((signal > 0 ? "BUY" : "SELL") + " opened volume=" + volume + " slPips=" + slPips.ToString("F2") + " tpPips=" + tpPips.ToString("F2"));
        }

        private double CalculateVolumeInUnits(double stopLossPips)
        {
            if (RiskMode == CdsRiskMode.FixedLots)
                return Symbol.QuantityToVolumeInUnits(Math.Min(FixedLotSize, MaxLotSize));

            double riskMoney = RiskMode == CdsRiskMode.FixedMoneyRisk
                ? FixedMoneyRisk
                : Account.Balance * RiskPercentPerTrade / 100.0;

            if (riskMoney <= 0 || stopLossPips <= 0)
                return 0;

            double volume = Symbol.VolumeForFixedRisk(riskMoney, stopLossPips, RoundingMode.Down);
            double maxVolume = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            if (volume > maxVolume) volume = maxVolume;
            return volume;
        }

        private bool ValidateStopDistances(double slPips, double tpPips, out string reason)
        {
            reason = string.Empty;
            if (slPips <= 0 || tpPips <= 0) { reason = "invalid SL / TP distance"; return false; }

            double slPriceDistance = slPips * Symbol.PipSize;
            double tpPriceDistance = tpPips * Symbol.PipSize;

            if (Symbol.MinStopLossDistance > 0 && slPriceDistance < Symbol.MinStopLossDistance)
            {
                reason = "SL below broker minimum distance";
                return false;
            }

            if (Symbol.MinTakeProfitDistance > 0 && tpPriceDistance < Symbol.MinTakeProfitDistance)
            {
                reason = "TP below broker minimum distance";
                return false;
            }

            return true;
        }

        private void ManageOpenPosition()
        {
            Position position = Positions.FirstOrDefault(p => p.SymbolName == SymbolName && p.Label == TradeLabel);
            if (position == null)
            {
                _openTradeDirection = 0;
                _openTradeTime = DateTime.MinValue;
                return;
            }

            if (MaxTradeSeconds > 0 && _openTradeTime != DateTime.MinValue && Server.Time >= _openTradeTime.AddSeconds(MaxTradeSeconds))
            {
                ClosePositionWithLog(position, "TIME_EXIT");
                return;
            }

            if (AdverseDeltaExit && _openTradeTime != DateTime.MinValue && (Server.Time - _openTradeTime).TotalSeconds >= AdverseDeltaCooldownSeconds)
            {
                int cumulativeDelta = CalculateCumulativeDelta();
                bool adverse = (_openTradeDirection > 0 && cumulativeDelta < -DeltaThreshold) || (_openTradeDirection < 0 && cumulativeDelta > DeltaThreshold);
                if (adverse)
                {
                    ClosePositionWithLog(position, "ADVERSE_DELTA");
                    return;
                }
            }

            if (UseBreakeven && !_breakevenApplied)
                TryBreakeven(position);
        }

        private void ClosePositionWithLog(Position position, string reason)
        {
            TradeResult result = ClosePosition(position);
            if (result.IsSuccessful)
                Debug("position closed: " + reason);
            else
                Debug("close failed: " + result.Error);
        }

        private void TryBreakeven(Position position)
        {
            double buffer = BreakevenBufferPips * Symbol.PipSize;
            double? tp = position.TakeProfit;

            if (position.TradeType == TradeType.Buy)
            {
                double profitPips = (Symbol.Bid - position.EntryPrice) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = position.EntryPrice + buffer;
                if (!position.StopLoss.HasValue || newSl > position.StopLoss.Value)
                {
                    TradeResult result = ModifyPosition(position, newSl, tp);
                    if (result.IsSuccessful) _breakevenApplied = true;
                    else Debug("breakeven modify failed: " + result.Error);
                }
            }
            else
            {
                double profitPips = (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = position.EntryPrice - buffer;
                if (!position.StopLoss.HasValue || newSl < position.StopLoss.Value)
                {
                    TradeResult result = ModifyPosition(position, newSl, tp);
                    if (result.IsSuccessful) _breakevenApplied = true;
                    else Debug("breakeven modify failed: " + result.Error);
                }
            }
        }

        private bool HasOpenPosition()
        {
            return Positions.Any(p => p.SymbolName == SymbolName && p.Label == TradeLabel);
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

        private double PriceDistanceToPips(double priceDistance)
        {
            return priceDistance / Symbol.PipSize;
        }

        private void ResetDailyIfNeeded()
        {
            DateTime today = Server.Time.Date;
            if (today == _currentDay) return;

            _currentDay = today;
            _dayStartBalance = Account.Balance;
            _dailyClosedPnl = 0;
            _dailyTradeCount = 0;
            _consecutiveLosses = 0;
            Debug("new trading day balance=" + _dayStartBalance);
        }

        private void SyncDailyStatsFromHistory()
        {
            DateTime dayStart = Server.Time.Date;
            double pnl = 0;
            int count = 0;

            foreach (HistoricalTrade h in History)
            {
                if (h.SymbolName != SymbolName) continue;
                if (h.Label != TradeLabel) continue;
                if (h.ClosingTime < dayStart) continue;
                pnl += h.NetProfit;
                count++;
            }

            foreach (Position p in Positions.Where(p => p.SymbolName == SymbolName && p.Label == TradeLabel))
            {
                if (p.EntryTime >= dayStart) count++;
            }

            _dailyClosedPnl = pnl;
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

            _openTradeDirection = 0;
            _openTradeTime = DateTime.MinValue;
            Debug("position closed pnl=" + p.NetProfit + " consecutiveLosses=" + _consecutiveLosses);
        }

        private void Debug(string message)
        {
            if (DebugLogging)
                Print(Prefix + message);
        }
    }
}
