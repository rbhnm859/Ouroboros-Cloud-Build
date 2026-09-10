using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_K_Commercial_v3 : Robot
    {
        private const string Prefix = "[K-COMM-V3] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;

        [Parameter("Bot Label", DefaultValue = "K_COMM_V3", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = false, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Min Ticks Per Bar", DefaultValue = 20, MinValue = 1, Group = "Microstructure")]
        public int MinTicksPerBar { get; set; }

        [Parameter("Imbalance Trigger", DefaultValue = 0.18, MinValue = 0.01, MaxValue = 1.0, Step = 0.01, Group = "Microstructure")]
        public double ImbalanceTrigger { get; set; }

        [Parameter("Persistence Bars", DefaultValue = 3, MinValue = 2, MaxValue = 8, Group = "Microstructure")]
        public int PersistenceBars { get; set; }

        [Parameter("Min Same Direction Bars", DefaultValue = 2, MinValue = 1, MaxValue = 8, Group = "Microstructure")]
        public int MinSameDirectionBars { get; set; }

        [Parameter("Entry Score Min", DefaultValue = 0.62, MinValue = 0.10, MaxValue = 1.0, Step = 0.01, Group = "Signal")]
        public double EntryScoreMin { get; set; }

        [Parameter("Session Start Hour", DefaultValue = 12, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int SessionStartHour { get; set; }

        [Parameter("Session Start Minute", DefaultValue = 30, MinValue = 0, MaxValue = 59, Group = "Session")]
        public int SessionStartMinute { get; set; }

        [Parameter("Session End Hour", DefaultValue = 16, MinValue = 0, MaxValue = 23, Group = "Session")]
        public int SessionEndHour { get; set; }

        [Parameter("Session End Minute", DefaultValue = 30, MinValue = 0, MaxValue = 59, Group = "Session")]
        public int SessionEndMinute { get; set; }

        [Parameter("ADX Minimum", DefaultValue = 16.0, MinValue = 0, Step = 0.5, Group = "Regime")]
        public double AdxMinimum { get; set; }

        [Parameter("Min ATR", DefaultValue = 0.00005, MinValue = 0, Step = 0.00001, Group = "Regime")]
        public double MinAtr { get; set; }

        [Parameter("Max ATR", DefaultValue = 0.00120, MinValue = 0, Step = 0.00001, Group = "Regime")]
        public double MaxAtr { get; set; }

        [Parameter("Max Spread Points", DefaultValue = 15, MinValue = 1, Group = "Execution")]
        public int MaxSpreadPoints { get; set; }

        [Parameter("Max Spread / ATR", DefaultValue = 0.25, MinValue = 0.01, MaxValue = 1.0, Step = 0.01, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Fixed Money Risk", DefaultValue = 0.90, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Risk Reference Balance", DefaultValue = 100.0, MinValue = 1, Group = "Risk")]
        public double RiskReferenceBalance { get; set; }

        [Parameter("Min Fixed Risk", DefaultValue = 0.05, MinValue = 0, Step = 0.01, Group = "Risk")]
        public double MinFixedMoneyRisk { get; set; }

        [Parameter("Hard Max Loss Money", DefaultValue = 1.00, MinValue = 0.05, Step = 0.05, Group = "Risk")]
        public double HardMaxLossMoney { get; set; }

        [Parameter("Max Lot Size", DefaultValue = 0.03, MinValue = 0.01, Step = 0.01, Group = "Risk")]
        public double MaxLotSize { get; set; }

        [Parameter("SL ATR Multiplier", DefaultValue = 0.80, MinValue = 0.10, Step = 0.05, Group = "Exit")]
        public double SlAtrMultiplier { get; set; }

        [Parameter("Reward / Risk", DefaultValue = 1.00, MinValue = 0.20, Step = 0.05, Group = "Exit")]
        public double RewardRisk { get; set; }

        [Parameter("Breakeven At R", DefaultValue = 0.80, MinValue = 0.20, Step = 0.05, Group = "Exit")]
        public double BreakevenAtR { get; set; }

        [Parameter("Breakeven Buffer Pips", DefaultValue = 0.20, MinValue = 0, Step = 0.05, Group = "Exit")]
        public double BreakevenBufferPips { get; set; }

        [Parameter("Max Trade Minutes", DefaultValue = 45, MinValue = 1, Group = "Exit")]
        public int MaxTradeMinutes { get; set; }

        [Parameter("Max Daily Trades", DefaultValue = 4, MinValue = 1, Group = "Protection")]
        public int MaxDailyTrades { get; set; }

        [Parameter("Max Daily Loss Money", DefaultValue = 0.60, MinValue = 0.05, Step = 0.05, Group = "Protection")]
        public double MaxDailyLossMoney { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 2, MinValue = 1, Group = "Protection")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Loss Cooldown Minutes", DefaultValue = 45, MinValue = 0, Group = "Protection")]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Min Minutes Between Trades", DefaultValue = 10, MinValue = 0, Group = "Protection")]
        public int MinMinutesBetweenTrades { get; set; }

        private AverageTrueRange _atr;
        private Bars _m15;
        private ExponentialMovingAverage _m15Ema;
        private DirectionalMovementSystem _m15Dms;

        private double _prevBid;
        private int _upTicks;
        private int _downTicks;
        private readonly List<double> _imbalanceHistory = new List<double>();
        private readonly List<int> _tickCountHistory = new List<int>();

        private DateTime _lastProcessedBar = DateTime.MinValue;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastLossTime = DateTime.MinValue;
        private DateTime _currentDay = DateTime.MinValue;
        private double _dailyClosedPnl;
        private int _dailyTradeCount;
        private int _consecutiveLosses;
        private double _initialRiskPips;
        private bool _breakevenApplied;

        protected override void OnStart()
        {
            if (!SymbolName.ToUpperInvariant().StartsWith("EURUSD"))
            {
                Print(Prefix + "EURUSD only");
                Stop();
                return;
            }

            if (TimeFrame != TimeFrame.Minute)
            {
                Print(Prefix + "M1 only");
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Simple);
            _m15 = MarketData.GetBars(TimeFrame.Minute15);
            _m15Ema = Indicators.ExponentialMovingAverage(_m15.ClosePrices, EmaPeriod);
            _m15Dms = Indicators.DirectionalMovementSystem(_m15, AdxPeriod);
            _prevBid = Symbol.Bid;
            _currentDay = Server.Time.Date;
            SyncDailyStats();
            RecoverOpenState();
            Positions.Closed += OnPositionClosed;
            Debug("started");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
        }

        protected override void OnTick()
        {
            ResetDayIfNeeded();

            double bid = Symbol.Bid;
            if (bid > _prevBid) _upTicks++;
            else if (bid < _prevBid) _downTicks++;
            _prevBid = bid;

            Position p = GetPosition();
            if (p != null)
                ManageOpenPosition(p);
        }

        protected override void OnBar()
        {
            ResetDayIfNeeded();
            SyncDailyStats();

            DateTime barTime = Bars.OpenTimes.LastValue;
            if (barTime == _lastProcessedBar)
                return;
            _lastProcessedBar = barTime;

            FinalizeMicrostructureBar();

            if (GetPosition() != null)
                return;

            string block;
            if (!PassGuards(out block))
            {
                Debug("BLOCK " + block);
                return;
            }

            int direction;
            double score;
            if (!TryGetSignal(out direction, out score))
                return;

            OpenTrade(direction, score);
        }

        private void FinalizeMicrostructureBar()
        {
            int total = _upTicks + _downTicks;
            double imbalance = total > 0 ? (double)(_upTicks - _downTicks) / total : 0.0;
            _imbalanceHistory.Add(imbalance);
            _tickCountHistory.Add(total);
            while (_imbalanceHistory.Count > 20) _imbalanceHistory.RemoveAt(0);
            while (_tickCountHistory.Count > 20) _tickCountHistory.RemoveAt(0);
            Debug("BAR ticks=" + total + " imbalance=" + imbalance.ToString("F3"));
            _upTicks = 0;
            _downTicks = 0;
        }

        private bool PassGuards(out string reason)
        {
            reason = string.Empty;
            if (!IsWeekday()) { reason = "weekend"; return false; }
            if (!IsSession()) { reason = "session"; return false; }
            if (_dailyTradeCount >= MaxDailyTrades) { reason = "daily_trades"; return false; }
            if (_dailyClosedPnl <= -MaxDailyLossMoney) { reason = "daily_loss"; return false; }
            if (_consecutiveLosses >= MaxConsecutiveLosses) { reason = "consecutive_losses"; return false; }
            if (_lastTradeTime != DateTime.MinValue && Server.Time < _lastTradeTime.AddMinutes(MinMinutesBetweenTrades)) { reason = "trade_cooldown"; return false; }
            if (_lastLossTime != DateTime.MinValue && Server.Time < _lastLossTime.AddMinutes(LossCooldownMinutes)) { reason = "loss_cooldown"; return false; }

            double atr = _atr.Result.LastValue;
            if (atr < MinAtr || (MaxAtr > 0 && atr > MaxAtr)) { reason = "atr"; return false; }
            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread_points"; return false; }
            if (atr <= 0 || Symbol.Spread / atr > MaxSpreadAtrRatio) { reason = "spread_atr"; return false; }
            return true;
        }

        private bool TryGetSignal(out int direction, out double score)
        {
            direction = 0;
            score = 0;
            if (_imbalanceHistory.Count < Math.Max(PersistenceBars, 2) || _tickCountHistory.Count == 0)
                return false;

            int last = _imbalanceHistory.Count - 1;
            if (_tickCountHistory[last] < MinTicksPerBar)
            {
                Debug("BLOCK tick_quality");
                return false;
            }

            double cur = _imbalanceHistory[last];
            if (Math.Abs(cur) < ImbalanceTrigger)
                return false;

            direction = cur > 0 ? 1 : -1;
            int same = 0;
            int n = Math.Min(PersistenceBars, _imbalanceHistory.Count);
            for (int i = 0; i < n; i++)
            {
                double v = _imbalanceHistory[last - i];
                if ((direction > 0 && v > 0) || (direction < 0 && v < 0)) same++;
            }
            if (same < MinSameDirectionBars)
                return false;

            double imbalanceStrength = Math.Min(1.0, Math.Abs(cur) / 0.60);
            double persistence = (double)same / n;
            bool trendAligned = IsTrendAligned(direction);
            bool slopeAligned = IsSlopeAligned(direction);
            double adx = _m15Dms.ADX.LastValue;
            double adxQuality = AdxMinimum <= 0 ? 1.0 : Math.Min(1.0, adx / Math.Max(AdxMinimum * 1.5, 1.0));
            double execQuality = ExecutionQuality();

            score = 0.35 * imbalanceStrength
                  + 0.20 * persistence
                  + 0.20 * (trendAligned ? 1.0 : 0.0)
                  + 0.10 * (slopeAligned ? 1.0 : 0.0)
                  + 0.10 * adxQuality
                  + 0.05 * execQuality;

            if (adx < AdxMinimum || !trendAligned)
                return false;

            Debug("SIGNAL dir=" + direction + " score=" + score.ToString("F3") + " imb=" + cur.ToString("F3") + " same=" + same + "/" + n + " adx=" + adx.ToString("F1"));
            return score >= EntryScoreMin;
        }

        private bool IsTrendAligned(int direction)
        {
            double ema = _m15Ema.Result.LastValue;
            if (ema <= 0) return false;
            return direction > 0 ? Symbol.Bid > ema : Symbol.Bid < ema;
        }

        private bool IsSlopeAligned(int direction)
        {
            int last = _m15Ema.Result.Count - 1;
            if (last < 3) return false;
            double delta = _m15Ema.Result[last] - _m15Ema.Result[last - 3];
            return direction > 0 ? delta > 0 : delta < 0;
        }

        private double ExecutionQuality()
        {
            double atr = _atr.Result.LastValue;
            if (atr <= 0) return 0;
            double ratio = Symbol.Spread / atr;
            return Math.Max(0.0, Math.Min(1.0, 1.0 - ratio / Math.Max(MaxSpreadAtrRatio, 0.0001)));
        }

        private void OpenTrade(int direction, double score)
        {
            double atr = _atr.Result.LastValue;
            double slPriceDistance = atr * SlAtrMultiplier;
            if (Symbol.MinStopLossDistance > 0)
                slPriceDistance = Math.Max(slPriceDistance, Symbol.MinStopLossDistance);
            double slPips = slPriceDistance / Symbol.PipSize;

            double tpPriceDistance = slPriceDistance * RewardRisk;
            if (Symbol.MinTakeProfitDistance > 0)
                tpPriceDistance = Math.Max(tpPriceDistance, Symbol.MinTakeProfitDistance);
            double tpPips = tpPriceDistance / Symbol.PipSize;

            double riskMoney = FixedMoneyRisk * Account.Balance / Math.Max(1.0, RiskReferenceBalance);
            riskMoney = Math.Max(MinFixedMoneyRisk, riskMoney);
            riskMoney = Math.Min(riskMoney, HardMaxLossMoney * 0.85);

            double volume = Symbol.VolumeForFixedRisk(riskMoney, slPips, RoundingMode.Down);
            double maxVolume = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            volume = Math.Min(volume, maxVolume);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

            if (volume < Symbol.VolumeInUnitsMin)
            {
                Debug("BLOCK volume_below_min risk=" + riskMoney.ToString("F2"));
                return;
            }

            TradeType type = direction > 0 ? TradeType.Buy : TradeType.Sell;
            TradeResult result = ExecuteMarketOrder(type, SymbolName, volume, TradeLabel, slPips, tpPips);
            if (!result.IsSuccessful || result.Position == null)
            {
                Debug("ORDER_FAIL " + result.Error);
                return;
            }

            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                ClosePosition(result.Position);
                Debug("INTEGRITY_CLOSE missing_sl_tp");
                return;
            }

            _initialRiskPips = Math.Abs(result.Position.EntryPrice - result.Position.StopLoss.Value) / Symbol.PipSize;
            _breakevenApplied = false;
            _lastTradeTime = Server.Time;
            _dailyTradeCount++;
            Debug("OPEN " + type + " volume=" + volume + " score=" + score.ToString("F3") + " risk=" + riskMoney.ToString("F2") + " sl=" + slPips.ToString("F2") + " tp=" + tpPips.ToString("F2"));
        }

        private void ManageOpenPosition(Position p)
        {
            if (p.NetProfit <= -HardMaxLossMoney)
            {
                ClosePosition(p);
                Debug("HARD_LOSS_CLOSE pnl=" + p.NetProfit.ToString("F2"));
                return;
            }

            if (MaxTradeMinutes > 0 && Server.Time >= p.EntryTime.AddMinutes(MaxTradeMinutes))
            {
                ClosePosition(p);
                Debug("TIME_EXIT");
                return;
            }

            if (!_breakevenApplied && _initialRiskPips > 0)
            {
                double favorablePips = p.TradeType == TradeType.Buy
                    ? (Symbol.Bid - p.EntryPrice) / Symbol.PipSize
                    : (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;

                if (favorablePips >= _initialRiskPips * BreakevenAtR)
                {
                    double buffer = BreakevenBufferPips * Symbol.PipSize;
                    double newSl = p.TradeType == TradeType.Buy ? p.EntryPrice + buffer : p.EntryPrice - buffer;
                    bool improves = !p.StopLoss.HasValue || (p.TradeType == TradeType.Buy ? newSl > p.StopLoss.Value : newSl < p.StopLoss.Value);
                    if (improves)
                    {
                        TradeResult m = ModifyPosition(p, newSl, p.TakeProfit);
                        if (m.IsSuccessful)
                        {
                            _breakevenApplied = true;
                            Debug("BREAKEVEN");
                        }
                    }
                }
            }
        }

        private void RecoverOpenState()
        {
            Position p = GetPosition();
            if (p == null) return;
            _lastTradeTime = p.EntryTime;
            if (p.StopLoss.HasValue)
            {
                _initialRiskPips = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Symbol.PipSize;
                _breakevenApplied = p.TradeType == TradeType.Buy ? p.StopLoss.Value >= p.EntryPrice : p.StopLoss.Value <= p.EntryPrice;
            }
            Debug("RECOVER position=" + p.Id);
        }

        private Position GetPosition()
        {
            return Positions.FirstOrDefault(x => x.SymbolName == SymbolName && x.Label == TradeLabel);
        }

        private void SyncDailyStats()
        {
            DateTime start = Server.Time.Date;
            double pnl = 0;
            int trades = 0;
            foreach (HistoricalTrade h in History)
            {
                if (h.SymbolName != SymbolName || h.Label != TradeLabel || h.ClosingTime < start) continue;
                pnl += h.NetProfit;
                trades++;
            }
            if (GetPosition() != null && GetPosition().EntryTime >= start) trades++;
            _dailyClosedPnl = pnl;
            _dailyTradeCount = trades;
        }

        private void ResetDayIfNeeded()
        {
            DateTime today = Server.Time.Date;
            if (today == _currentDay) return;
            _currentDay = today;
            _dailyClosedPnl = 0;
            _dailyTradeCount = 0;
            _consecutiveLosses = 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != TradeLabel) return;
            _dailyClosedPnl += p.NetProfit;
            if (p.NetProfit < 0)
            {
                _consecutiveLosses++;
                _lastLossTime = Server.Time;
            }
            else if (p.NetProfit > 0)
            {
                _consecutiveLosses = 0;
            }
            _initialRiskPips = 0;
            _breakevenApplied = false;
            Debug("CLOSE pnl=" + p.NetProfit.ToString("F2"));
        }

        private bool IsWeekday()
        {
            DayOfWeek d = Server.Time.DayOfWeek;
            return d >= DayOfWeek.Monday && d <= DayOfWeek.Friday;
        }

        private bool IsSession()
        {
            int now = Server.Time.Hour * 60 + Server.Time.Minute;
            int start = SessionStartHour * 60 + SessionStartMinute;
            int end = SessionEndHour * 60 + SessionEndMinute;
            if (start == end) return true;
            if (start < end) return now >= start && now < end;
            return now >= start || now < end;
        }

        private int SpreadInPoints()
        {
            return (int)Math.Round(Symbol.Spread / Symbol.TickSize);
        }

        private void Debug(string message)
        {
            if (DebugLogging)
                Print(Prefix + message);
        }
    }
}
