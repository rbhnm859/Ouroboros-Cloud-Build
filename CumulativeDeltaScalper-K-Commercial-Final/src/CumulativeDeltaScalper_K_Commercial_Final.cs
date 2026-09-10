using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum KFinalRiskMode
    {
        FixedLots = 0,
        RiskPercent = 1,
        FixedMoneyRisk = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_K_Commercial_Final : Robot
    {
        private const string Prefix = "[K-COMM-FINAL] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;
        private const double BreakevenBufferPips = 0.5;

        [Parameter("Bot Label", DefaultValue = "K_COMM_FINAL", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = false, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Window Size", DefaultValue = 10, MinValue = 2, Group = "K Alpha")]
        public int WindowSize { get; set; }

        [Parameter("Delta Threshold", DefaultValue = 125, MinValue = 1, Group = "K Alpha")]
        public int DeltaThreshold { get; set; }

        [Parameter("Min Confirmations", DefaultValue = 3, MinValue = 0, MaxValue = 5, Group = "K Alpha")]
        public int MinConfirmations { get; set; }

        [Parameter("Use Bar Delta Fallback", DefaultValue = true, Group = "K Alpha")]
        public bool UseBarDeltaFallback { get; set; }

        [Parameter("Fallback Below Tick Delta", DefaultValue = 2, MinValue = 0, Group = "K Alpha")]
        public int FallbackBelowTickDelta { get; set; }

        [Parameter("Bar Delta Point Mult", DefaultValue = 1.6, MinValue = 0.1, Step = 0.1, Group = "K Alpha")]
        public double BarDeltaPointMultiplier { get; set; }

        [Parameter("Session Start H", DefaultValue = 14, MinValue = 0, MaxValue = 23, Group = "K Alpha")]
        public int SessionStartHour { get; set; }

        [Parameter("Session Start M", DefaultValue = 0, MinValue = 0, MaxValue = 59, Group = "K Alpha")]
        public int SessionStartMinute { get; set; }

        [Parameter("Session End H", DefaultValue = 14, MinValue = 0, MaxValue = 23, Group = "K Alpha")]
        public int SessionEndHour { get; set; }

        [Parameter("Session End M", DefaultValue = 54, MinValue = 0, MaxValue = 59, Group = "K Alpha")]
        public int SessionEndMinute { get; set; }

        [Parameter("Trade Monday", DefaultValue = true, Group = "K Alpha")]
        public bool TradeMonday { get; set; }
        [Parameter("Trade Tuesday", DefaultValue = true, Group = "K Alpha")]
        public bool TradeTuesday { get; set; }
        [Parameter("Trade Wednesday", DefaultValue = true, Group = "K Alpha")]
        public bool TradeWednesday { get; set; }
        [Parameter("Trade Thursday", DefaultValue = false, Group = "K Alpha")]
        public bool TradeThursday { get; set; }
        [Parameter("Trade Friday", DefaultValue = true, Group = "K Alpha")]
        public bool TradeFriday { get; set; }

        [Parameter("EMA Slope Bars", DefaultValue = 3, MinValue = 1, Group = "K Alpha")]
        public int EmaSlopeBars { get; set; }

        [Parameter("ADX Threshold", DefaultValue = 16.0, MinValue = 0, Step = 0.5, Group = "K Alpha")]
        public double AdxThreshold { get; set; }

        [Parameter("Min ATR", DefaultValue = 0.00005, MinValue = 0, Step = 0.00001, Group = "K Alpha")]
        public double MinAtr { get; set; }

        [Parameter("Max ATR", DefaultValue = 0.00105, MinValue = 0, Step = 0.00001, Group = "K Alpha")]
        public double MaxAtr { get; set; }

        [Parameter("Max Spread Points", DefaultValue = 15, MinValue = 1, Group = "Execution")]
        public int MaxSpreadPoints { get; set; }

        [Parameter("Spread Avg Multiplier", DefaultValue = 1.6, MinValue = 1.0, Step = 0.1, Group = "Execution")]
        public double SpreadAvgMultiplier { get; set; }

        [Parameter("Spread History Size", DefaultValue = 30, MinValue = 1, Group = "Execution")]
        public int SpreadHistorySize { get; set; }

        [Parameter("Risk Mode", DefaultValue = KFinalRiskMode.FixedMoneyRisk, Group = "Risk")]
        public KFinalRiskMode RiskMode { get; set; }

        [Parameter("Fixed Money Risk", DefaultValue = 0.90, MinValue = 0.01, Step = 0.01, Group = "Risk")]
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

        [Parameter("Max Lot Size", DefaultValue = 0.03, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double MaxLotSize { get; set; }

        [Parameter("Hard Max Loss Money", DefaultValue = 1.00, MinValue = 0.10, Step = 0.05, Group = "Risk")]
        public double HardMaxLossMoney { get; set; }

        [Parameter("SL ATR Multiplier", DefaultValue = 0.8, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double SlAtrMultiplier { get; set; }

        [Parameter("TP ATR Multiplier", DefaultValue = 0.4, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double TpAtrMultiplier { get; set; }

        [Parameter("Max Daily Trades", DefaultValue = 3, MinValue = 1, Group = "Protection")]
        public int MaxDailyTrades { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 3.5, MinValue = 0.1, Step = 0.1, Group = "Protection")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Daily Loss Money", DefaultValue = 0.50, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Daily Profit Target Money", DefaultValue = 1.00, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double DailyProfitTargetMoney { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 2, MinValue = 1, Group = "Protection")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Min Sec Between Trades", DefaultValue = 900, MinValue = 0, Group = "Protection")]
        public int MinSecondsBetweenTrades { get; set; }

        [Parameter("Loss Cooldown Min", DefaultValue = 60, MinValue = 0, Group = "Protection")]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Max Daily Equity DD Money", DefaultValue = 0.65, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxDailyEquityDrawdownMoney { get; set; }

        [Parameter("Max Floating Loss Money", DefaultValue = 0.80, MinValue = 0.0, Step = 0.01, Group = "Protection")]
        public double MaxFloatingLossMoney { get; set; }

        [Parameter("Max Equity DD %", DefaultValue = 12.0, MinValue = 0.0, Step = 0.1, Group = "Protection")]
        public double MaxEquityDrawdownPercent { get; set; }

        [Parameter("Max Trade Seconds", DefaultValue = 1800, MinValue = 0, Group = "Exit")]
        public int MaxTradeSeconds { get; set; }

        [Parameter("Use Breakeven", DefaultValue = true, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven Pips", DefaultValue = 0.8, MinValue = 0.1, Step = 0.1, Group = "Exit")]
        public double BreakevenPips { get; set; }

        [Parameter("Adverse Delta Exit", DefaultValue = true, Group = "Exit")]
        public bool AdverseDeltaExit { get; set; }

        [Parameter("Adverse Delta Cooldown Sec", DefaultValue = 5, MinValue = 0, Group = "Exit")]
        public int AdverseDeltaCooldownSeconds { get; set; }

        private AverageTrueRange _atr;
        private ExponentialMovingAverage _htfEma;
        private DirectionalMovementSystem _htfDms;
        private Bars _htfBars;
        private int[] _deltaBuffer;
        private int _bufferIndex;
        private int _bufferFilled;
        private int _prevCumDelta;
        private int[] _spreadHistory;
        private int _spreadHistoryIndex;
        private int _spreadHistoryFilled;
        private double _prevBid;
        private int _uptickCount;
        private int _downtickCount;
        private DateTime _lastProcessedBarTime = DateTime.MinValue;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private DateTime _openTradeTime = DateTime.MinValue;
        private int _openTradeDirection;
        private bool _breakevenApplied;
        private DateTime _currentDay = DateTime.MinValue;
        private double _dayStartBalance;
        private double _dayHighEquity;
        private double _accountPeakEquity;
        private double _dailyClosedPnl;
        private int _dailyTradeCount;
        private int _consecutiveLosses;

        protected override void OnStart()
        {
            if (!SymbolName.ToUpperInvariant().StartsWith("EURUSD") || TimeFrame != TimeFrame.Minute)
            {
                Print(Prefix + "EURUSD M1 only");
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Simple);
            _htfBars = MarketData.GetBars(TimeFrame.Minute15);
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
            RecoverStateFromExistingPosition();
            SyncDailyStatsFromHistory();
            Debug("started with K alpha preserved");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
        }

        protected override void OnTick()
        {
            ResetDailyIfNeeded();
            SyncDailyStatsFromHistory();
            UpdateEquityPeaks();
            ProcessTickDelta();
            var position = GetOpenPosition();
            if (position != null)
                ManageOpenPosition(position);
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
            string reason;
            if (!CheckGuards(out reason))
                return;
            int signal = CheckSignal();
            if (signal != 0)
                OpenTrade(signal);
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
            int value = tickDelta;
            if (UseBarDeltaFallback && Math.Abs(tickDelta) <= FallbackBelowTickDelta)
            {
                int estimated = EstimateClosedBarDelta();
                if (estimated != 0) value = estimated;
            }
            _deltaBuffer[_bufferIndex] = value;
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

        private int CheckSignal()
        {
            if (_bufferFilled < _deltaBuffer.Length) return 0;
            int cumulative = _deltaBuffer.Sum();
            int previous = _prevCumDelta;
            _prevCumDelta = cumulative;
            int signal = 0;
            if (previous <= DeltaThreshold && cumulative > DeltaThreshold) signal = 1;
            else if (previous >= -DeltaThreshold && cumulative < -DeltaThreshold) signal = -1;
            if (signal == 0) return 0;
            int confirmations = 0;
            if (CheckMomentum(signal)) confirmations++;
            if (CheckHtfEma(signal)) confirmations++;
            if (CheckEmaSlope(signal)) confirmations++;
            if (_htfDms.ADX.LastValue >= AdxThreshold) confirmations++;
            if (CheckSpreadDynamic()) confirmations++;
            return confirmations >= MinConfirmations ? signal : 0;
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
            return ema > 0 && (signal > 0 ? Symbol.Bid > ema : Symbol.Bid < ema);
        }

        private bool CheckEmaSlope(int signal)
        {
            int last = _htfEma.Result.Count - 1;
            if (last < EmaSlopeBars) return false;
            double newest = _htfEma.Result[last];
            double oldest = _htfEma.Result[last - EmaSlopeBars];
            return signal > 0 ? newest > oldest : newest < oldest;
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
            if (!IsTradingDayAllowed()) { reason = "weekday"; return false; }
            if (!IsInSession()) { reason = "session"; return false; }
            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "daily_trades"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "loss_streak"; return false; }
            double dailyLimitByPercent = _dayStartBalance * MaxDailyLossPercent / 100.0;
            double dailyLimit = MaxDailyLossMoney > 0 ? Math.Min(dailyLimitByPercent, MaxDailyLossMoney) : dailyLimitByPercent;
            if (dailyLimit > 0 && _dailyClosedPnl <= -dailyLimit) { reason = "daily_loss"; return false; }
            if (DailyProfitTargetMoney > 0 && _dailyClosedPnl >= DailyProfitTargetMoney) { reason = "daily_profit"; return false; }
            if (IsDailyEquityDrawdownHit() || IsAccountEquityDrawdownHit()) { reason = "equity_guard"; return false; }
            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddSeconds(MinSecondsBetweenTrades)) { reason = "cooldown"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "loss_cooldown"; return false; }
            double atr = _atr.Result.LastValue;
            if (atr < MinAtr || (MaxAtr > 0 && atr > MaxAtr)) { reason = "atr"; return false; }
            return true;
        }

        private bool IsTradingDayAllowed()
        {
            DayOfWeek d = Server.Time.DayOfWeek;
            if (d == DayOfWeek.Monday) return TradeMonday;
            if (d == DayOfWeek.Tuesday) return TradeTuesday;
            if (d == DayOfWeek.Wednesday) return TradeWednesday;
            if (d == DayOfWeek.Thursday) return TradeThursday;
            if (d == DayOfWeek.Friday) return TradeFriday;
            return false;
        }

        private bool IsInSession()
        {
            int now = Server.Time.Hour * 60 + Server.Time.Minute;
            int start = SessionStartHour * 60 + SessionStartMinute;
            int end = SessionEndHour * 60 + SessionEndMinute;
            if (start == end) return true;
            if (start < end) return now >= start && now < end;
            return now >= start || now < end;
        }

        private void OpenTrade(int signal)
        {
            double slPips = Math.Max(0.1, _atr.Result.LastValue * SlAtrMultiplier / Symbol.PipSize);
            double tpPips = Math.Max(0.1, _atr.Result.LastValue * TpAtrMultiplier / Symbol.PipSize);
            NormalizeStopDistances(ref slPips, ref tpPips);
            double riskMoney = CalculateRiskMoney();
            double volume = CalculateVolume(slPips, riskMoney);
            if (volume < Symbol.VolumeInUnitsMin) return;
            TradeType type = signal > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful || result.Position == null) return;
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                ClosePosition(result.Position);
                Debug("integrity close: missing SL/TP");
                return;
            }
            _lastTradeTime = Server.Time;
            _openTradeTime = result.Position.EntryTime;
            _openTradeDirection = signal;
            _breakevenApplied = false;
            _dailyTradeCount++;
        }

        private double CalculateRiskMoney()
        {
            if (RiskMode == KFinalRiskMode.FixedLots) return 0;
            if (RiskMode == KFinalRiskMode.RiskPercent) return Math.Min(HardMaxLossMoney, Account.Balance * RiskPercentPerTrade / 100.0);
            double risk = FixedMoneyRisk;
            if (AutoScaleFixedRisk && RiskReferenceBalance > 0)
                risk = FixedMoneyRisk * Account.Balance / RiskReferenceBalance;
            if (MinFixedMoneyRisk > 0)
                risk = Math.Max(MinFixedMoneyRisk, risk);
            return Math.Max(0, Math.Min(HardMaxLossMoney * 0.90, risk));
        }

        private double CalculateVolume(double stopLossPips, double riskMoney)
        {
            double volume;
            if (RiskMode == KFinalRiskMode.FixedLots)
                volume = Symbol.QuantityToVolumeInUnits(Math.Min(FixedLotSize, MaxLotSize));
            else
                volume = Symbol.VolumeForFixedRisk(riskMoney, stopLossPips, RoundingMode.Down);
            double maxVolume = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            volume = Math.Min(volume, Math.Min(maxVolume, Symbol.VolumeInUnitsMax));
            return Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
        }

        private void NormalizeStopDistances(ref double slPips, ref double tpPips)
        {
            if (Symbol.MinStopLossDistance > 0)
                slPips = Math.Max(slPips, Symbol.MinStopLossDistance / Symbol.PipSize);
            if (Symbol.MinTakeProfitDistance > 0)
                tpPips = Math.Max(tpPips, Symbol.MinTakeProfitDistance / Symbol.PipSize);
        }

        private void ManageOpenPosition(Position position)
        {
            if (HardMaxLossMoney > 0 && position.NetProfit <= -HardMaxLossMoney)
            {
                ClosePositionWithLog(position, "HARD_LOSS_CAP");
                return;
            }
            if (MaxFloatingLossMoney > 0 && position.NetProfit <= -MaxFloatingLossMoney)
            {
                ClosePositionWithLog(position, "FLOATING_LOSS_GUARD");
                return;
            }
            if (IsDailyEquityDrawdownHit() || IsAccountEquityDrawdownHit())
            {
                ClosePositionWithLog(position, "EQUITY_GUARD");
                return;
            }
            if (!position.StopLoss.HasValue || !position.TakeProfit.HasValue)
            {
                ClosePositionWithLog(position, "SLTP_INTEGRITY_FAIL");
                return;
            }
            if (MaxTradeSeconds > 0 && _openTradeTime != DateTime.MinValue && Server.Time >= _openTradeTime.AddSeconds(MaxTradeSeconds))
            {
                ClosePositionWithLog(position, "TIME_EXIT");
                return;
            }
            if (AdverseDeltaExit && _openTradeTime != DateTime.MinValue && (Server.Time - _openTradeTime).TotalSeconds >= AdverseDeltaCooldownSeconds)
            {
                int cumulative = _deltaBuffer.Sum();
                bool adverse = (_openTradeDirection > 0 && cumulative < -DeltaThreshold) || (_openTradeDirection < 0 && cumulative > DeltaThreshold);
                if (adverse)
                {
                    ClosePositionWithLog(position, "ADVERSE_DELTA");
                    return;
                }
            }
            if (UseBreakeven && !_breakevenApplied)
                TryBreakeven(position);
        }

        private void TryBreakeven(Position p)
        {
            double? tp = p.TakeProfit;
            if (p.TradeType == TradeType.Buy)
            {
                double profitPips = (Symbol.Bid - p.EntryPrice) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = p.EntryPrice + BreakevenBufferPips * Symbol.PipSize;
                if (!p.StopLoss.HasValue || newSl > p.StopLoss.Value)
                {
                    TradeResult r = ModifyPosition(p, newSl, tp);
                    if (r.IsSuccessful) _breakevenApplied = true;
                }
            }
            else
            {
                double profitPips = (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = p.EntryPrice - BreakevenBufferPips * Symbol.PipSize;
                if (!p.StopLoss.HasValue || newSl < p.StopLoss.Value)
                {
                    TradeResult r = ModifyPosition(p, newSl, tp);
                    if (r.IsSuccessful) _breakevenApplied = true;
                }
            }
        }

        private void RecoverStateFromExistingPosition()
        {
            Position p = GetOpenPosition();
            if (p == null) return;
            _openTradeTime = p.EntryTime;
            _openTradeDirection = p.TradeType == TradeType.Buy ? 1 : -1;
            _lastTradeTime = p.EntryTime;
            _breakevenApplied = p.StopLoss.HasValue && ((p.TradeType == TradeType.Buy && p.StopLoss.Value >= p.EntryPrice) || (p.TradeType == TradeType.Sell && p.StopLoss.Value <= p.EntryPrice));
            Debug("recovered existing position state");
        }

        private Position GetOpenPosition()
        {
            return Positions.FirstOrDefault(p => p.SymbolName == SymbolName && p.Label == TradeLabel);
        }

        private void ClosePositionWithLog(Position p, string reason)
        {
            TradeResult r = ClosePosition(p);
            if (r.IsSuccessful) Debug("closed " + reason);
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
            DateTime dayStart = Server.Time.Date;
            double pnl = 0;
            int count = 0;
            foreach (HistoricalTrade h in History)
            {
                if (h.SymbolName != SymbolName || h.Label != TradeLabel || h.ClosingTime < dayStart) continue;
                pnl += h.NetProfit;
                count++;
            }
            Position p = GetOpenPosition();
            if (p != null && p.EntryTime >= dayStart) count++;
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

        private void Debug(string message)
        {
            if (DebugLogging) Print(Prefix + message);
        }
    }
}
