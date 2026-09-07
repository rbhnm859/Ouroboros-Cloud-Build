using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GQ_Session_Scalper_v2 : Robot
    {
        private const string BotLabel = "GQ_Session_Scalper_v2";

        [Parameter("Session Start (HH:mm)", Group = "Session", DefaultValue = "08:00")]
        public string SessionStart { get; set; }

        [Parameter("Session End (HH:mm)", Group = "Session", DefaultValue = "16:00")]
        public string SessionEnd { get; set; }

        [Parameter("Close At Session End", Group = "Session", DefaultValue = true)]
        public bool CloseAtSessionEnd { get; set; }

        [Parameter("Friday Last Entry (HH:mm, blank=off)", Group = "Session", DefaultValue = "")]
        public string FridayLastEntry { get; set; }

        [Parameter("Friday Force Close (HH:mm, blank=off)", Group = "Session", DefaultValue = "")]
        public string FridayForceClose { get; set; }

        [Parameter("Max Trades Per Day", Group = "Risk", DefaultValue = 6, MinValue = 1)]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Max Consecutive Losses", Group = "Risk", DefaultValue = 3, MinValue = 1)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Max Open Positions", Group = "Risk", DefaultValue = 1, MinValue = 1)]
        public int MaxOpenPositions { get; set; }

        [Parameter("Risk Per Trade %", Group = "Risk", DefaultValue = 0.5, MinValue = 0.01, MaxValue = 5.0)]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Use Fixed Lot Override", Group = "Risk", DefaultValue = false)]
        public bool UseFixedLotOverride { get; set; }

        [Parameter("Fixed Lot Size", Group = "Risk", DefaultValue = 0.1, MinValue = 0.01)]
        public double FixedLotSize { get; set; }

        [Parameter("Max Daily Loss %", Group = "Protection", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 100)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Minimum Equity Protection %", Group = "Protection", DefaultValue = 30.0, MinValue = 0.0, MaxValue = 99.0)]
        public double MinimumEquityProtectionPercent { get; set; }

        [Parameter("Cooldown Bars", Group = "Protection", DefaultValue = 2, MinValue = 0)]
        public int CooldownBars { get; set; }

        [Parameter("Primary EMA Period", Group = "Signal", DefaultValue = 34, MinValue = 2)]
        public int PrimaryEmaPeriod { get; set; }

        [Parameter("Higher TF", Group = "Signal", DefaultValue = "Hour")]
        public TimeFrame HigherTimeFrame { get; set; }

        [Parameter("Higher TF EMA Period", Group = "Signal", DefaultValue = 55, MinValue = 2)]
        public int HigherTfEmaPeriod { get; set; }

        [Parameter("Momentum Period", Group = "Signal", DefaultValue = 14, MinValue = 2)]
        public int MomentumPeriod { get; set; }

        [Parameter("ATR Period", Group = "Signal", DefaultValue = 14, MinValue = 2)]
        public int AtrPeriod { get; set; }

        [Parameter("Pullback ATR x", Group = "Signal", DefaultValue = 0.3, MinValue = 0.0)]
        public double PullbackAtrMultiplier { get; set; }

        [Parameter("Min ATR (pips)", Group = "Filter", DefaultValue = 3.0, MinValue = 0.0)]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR (pips, 0=off)", Group = "Filter", DefaultValue = 80.0, MinValue = 0.0)]
        public double MaxAtrPips { get; set; }

        [Parameter("Max Spread (pips, 0=off)", Group = "Filter", DefaultValue = 2.5, MinValue = 0.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Max Spread / SL Ratio", Group = "Filter", DefaultValue = 0.2, MinValue = 0.0)]
        public double MaxSpreadToSlRatio { get; set; }

        [Parameter("ATR SL Multiplier", Group = "Stops", DefaultValue = 1.4, MinValue = 0.1)]
        public double AtrSlMultiplier { get; set; }

        [Parameter("Minimum SL (pips)", Group = "Stops", DefaultValue = 6.0, MinValue = 0.1)]
        public double MinStopLossPips { get; set; }

        [Parameter("Maximum SL (pips)", Group = "Stops", DefaultValue = 45.0, MinValue = 0.1)]
        public double MaxStopLossPips { get; set; }

        [Parameter("Risk Reward Ratio", Group = "Stops", DefaultValue = 1.8, MinValue = 0.5, MaxValue = 5.0)]
        public double RiskRewardRatio { get; set; }

        [Parameter("Breakeven Trigger (R)", Group = "Management", DefaultValue = 1.0, MinValue = 0.1)]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Buffer (pips)", Group = "Management", DefaultValue = 0.4, MinValue = 0.0)]
        public double BreakevenBufferPips { get; set; }

        [Parameter("Enable ATR Trailing", Group = "Management", DefaultValue = true)]
        public bool EnableAtrTrailing { get; set; }

        [Parameter("Trailing Start (R)", Group = "Management", DefaultValue = 1.5, MinValue = 0.1)]
        public double TrailingStartR { get; set; }

        [Parameter("ATR Trail Multiplier", Group = "Management", DefaultValue = 1.2, MinValue = 0.1)]
        public double AtrTrailMultiplier { get; set; }

        private ExponentialMovingAverage _ema;
        private ExponentialMovingAverage _htfEma;
        private Momentum _momentum;
        private AverageTrueRange _atr;
        private Bars _higherBars;
        private TimeSpan _sessionStart;
        private TimeSpan _sessionEnd;
        private TimeSpan? _fridayLastEntry;
        private TimeSpan? _fridayForceClose;

        private DateTime _currentDay;
        private double _dayStartEquity;
        private double _initialEquity;
        private bool _dailyTradingBlocked;
        private bool _equityProtectionTriggered;
        private int _consecutiveLosses;
        private int _tradesToday;
        private int _lastSignalBarIndex = int.MinValue;
        private int _lastExitBarIndex = int.MinValue;
        private readonly Dictionary<long, double> _positionInitialRiskPips = new Dictionary<long, double>();

        protected override void OnStart()
        {
            if (!ValidateParameters())
            {
                Stop();
                return;
            }

            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, PrimaryEmaPeriod);
            _momentum = Indicators.Momentum(Bars.ClosePrices, MomentumPeriod);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);

            _higherBars = MarketData.GetBars(HigherTimeFrame, SymbolName);
            if (_higherBars == null || _higherBars.Count < HigherTfEmaPeriod + 5)
            {
                Print("[START_FAIL] Higher timeframe bars unavailable or insufficient.");
                Stop();
                return;
            }
            _htfEma = Indicators.ExponentialMovingAverage(_higherBars.ClosePrices, HigherTfEmaPeriod);

            _currentDay = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _initialEquity = Account.Equity;

            Print("[START] {0} symbol={1} tf={2} htf={3}", BotLabel, SymbolName, TimeFrame, HigherTimeFrame);
            Print("[SYMBOL] PipSize={0} TickSize={1} Digits={2} VolMin={3} VolMax={4} VolStep={5} MinSL={6} MinTP={7} MinDistanceType={8}",
                Symbol.PipSize, Symbol.TickSize, Symbol.Digits,
                Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep,
                Symbol.MinStopLossDistance, Symbol.MinTakeProfitDistance, Symbol.MinDistanceType);
        }

        protected override void OnBarClosed()
        {
            RefreshDailyState();
            if (!PassesGlobalRiskGate())
                return;

            int signalBarIndex = Bars.Count - 2;
            if (signalBarIndex < 5)
                return;

            if (signalBarIndex == _lastSignalBarIndex)
                return;

            if (!IndicatorsReady(signalBarIndex))
                return;

            if (!IsInSession(Server.Time))
            {
                if (CloseAtSessionEnd)
                    CloseAllPositions("SessionEnd");
                return;
            }

            if (IsFridayEntryBlocked(Server.Time))
                return;

            if (_tradesToday >= MaxTradesPerDay)
                return;

            if (!CooldownSatisfied(signalBarIndex))
                return;

            if (CountManagedPositions() >= MaxOpenPositions)
                return;

            if (!NoHedgingStateSatisfied())
                return;

            double atrPips = GetAtrPips(1);
            if (!PassesAtrFilter(atrPips))
                return;

            double stopLossPips = ResolveStopLossPips(atrPips);
            double takeProfitPips = ResolveTakeProfitPips(stopLossPips);
            if (!PassesDistanceRules(stopLossPips, takeProfitPips))
                return;

            double spreadPips = GetSpreadPips();
            if (!PassesSpreadFilter(spreadPips, stopLossPips))
                return;

            var signal = BuildSignal();
            if (signal == null)
                return;

            double volume = CalculateVolumeInUnits(stopLossPips);
            if (volume <= 0)
                return;

            TryEnter(signal.Value, volume, stopLossPips, takeProfitPips, signalBarIndex);
        }

        protected override void OnTick()
        {
            RefreshDailyState();

            if (IsFridayForceCloseDue(Server.Time))
                CloseAllPositions("FridayForceClose");

            if (_equityProtectionTriggered)
            {
                CloseAllPositions("MinimumEquityProtection");
                return;
            }

            ManageOpenPosition();
        }

        protected override void OnPositionOpened(Position position)
        {
            if (!IsManagedPosition(position))
                return;

            if (position.StopLoss.HasValue)
            {
                double riskPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize;
                if (riskPips > 0 && double.IsFinite(riskPips))
                    _positionInitialRiskPips[position.Id] = riskPips;
            }
        }

        protected override void OnPositionClosed(Position position)
        {
            if (!IsManagedPosition(position))
                return;

            _lastExitBarIndex = Bars.Count - 1;
            _positionInitialRiskPips.Remove(position.Id);
            _consecutiveLosses = position.NetProfit < 0 ? _consecutiveLosses + 1 : 0;

            Print("[CLOSE] Id={0} Net={1:F2} ConsecutiveLosses={2}", position.Id, position.NetProfit, _consecutiveLosses);
        }

        private bool ValidateParameters()
        {
            bool ok = true;

            ok &= TryParseTime(SessionStart, new TimeSpan(8, 0, 0), out _sessionStart, "SessionStart");
            ok &= TryParseTime(SessionEnd, new TimeSpan(16, 0, 0), out _sessionEnd, "SessionEnd");
            ok &= TryParseOptionalTime(FridayLastEntry, out _fridayLastEntry, "FridayLastEntry");
            ok &= TryParseOptionalTime(FridayForceClose, out _fridayForceClose, "FridayForceClose");

            if (RiskRewardRatio <= 0 || AtrSlMultiplier <= 0 || MinStopLossPips <= 0 || MaxStopLossPips < MinStopLossPips)
            {
                Print("[PARAM_FAIL] Invalid stop/risk settings.");
                ok = false;
            }

            if (RiskPerTradePercent <= 0 || (!UseFixedLotOverride && RiskPerTradePercent > 5))
            {
                Print("[PARAM_FAIL] RiskPerTradePercent out of allowed range.");
                ok = false;
            }

            if (Symbol.PipSize <= 0 || Symbol.TickSize <= 0 || Symbol.VolumeInUnitsStep <= 0)
            {
                Print("[PARAM_FAIL] Invalid symbol constraints.");
                ok = false;
            }

            if (Bars.Count < Math.Max(Math.Max(PrimaryEmaPeriod, MomentumPeriod), AtrPeriod) + 10)
            {
                Print("[PARAM_FAIL] Not enough bars for indicator warm-up.");
                ok = false;
            }

            return ok;
        }

        private bool TryParseTime(string input, TimeSpan fallback, out TimeSpan value, string name)
        {
            if (!TimeSpan.TryParse(input, out value))
            {
                value = fallback;
                Print("[PARAM_WARN] {0} invalid, fallback={1}", name, fallback);
            }
            return true;
        }

        private bool TryParseOptionalTime(string input, out TimeSpan? value, string name)
        {
            value = null;
            if (string.IsNullOrWhiteSpace(input))
                return true;

            TimeSpan parsed;
            if (!TimeSpan.TryParse(input, out parsed))
            {
                Print("[PARAM_FAIL] {0} invalid format: {1}", name, input);
                return false;
            }

            value = parsed;
            return true;
        }

        private void RefreshDailyState()
        {
            if (Server.Time.Date != _currentDay)
            {
                _currentDay = Server.Time.Date;
                _dayStartEquity = Account.Equity;
                _tradesToday = 0;
                _consecutiveLosses = 0;
                _dailyTradingBlocked = false;
                Print("[DAY_RESET] DayStartEquity={0:F2}", _dayStartEquity);
            }

            if (!_equityProtectionTriggered && MinimumEquityProtectionPercent > 0)
            {
                double minimumAllowed = _initialEquity * (1.0 - MinimumEquityProtectionPercent / 100.0);
                if (Account.Equity <= minimumAllowed)
                {
                    _equityProtectionTriggered = true;
                    Print("[RISK_BLOCK] Minimum equity protection triggered. Equity={0:F2} Threshold={1:F2}", Account.Equity, minimumAllowed);
                }
            }

            if (!_dailyTradingBlocked && MaxDailyLossPercent > 0 && _dayStartEquity > 0)
            {
                double dailyLossPercent = Math.Max(0.0, (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0);
                if (dailyLossPercent >= MaxDailyLossPercent)
                {
                    _dailyTradingBlocked = true;
                    Print("[RISK_BLOCK] Max daily loss reached. DailyLoss%={0:F2}", dailyLossPercent);
                }
            }
        }

        private bool PassesGlobalRiskGate()
        {
            if (_equityProtectionTriggered)
                return false;

            if (_dailyTradingBlocked)
                return false;

            if (_consecutiveLosses >= MaxConsecutiveLosses)
            {
                Print("[RISK_BLOCK] Max consecutive losses reached: {0}", _consecutiveLosses);
                return false;
            }

            return true;
        }

        private bool IndicatorsReady(int signalBarIndex)
        {
            if (_higherBars == null || _higherBars.Count < HigherTfEmaPeriod + 3)
                return false;

            return IsFinite(_ema.Result.Last(1)) &&
                   IsFinite(_ema.Result.Last(2)) &&
                   IsFinite(_momentum.Result.Last(1)) &&
                   IsFinite(_momentum.Result.Last(2)) &&
                   IsFinite(_atr.Result.Last(1)) &&
                   signalBarIndex > Math.Max(Math.Max(PrimaryEmaPeriod, MomentumPeriod), AtrPeriod);
        }

        private bool IsFinite(double v)
        {
            return !double.IsNaN(v) && !double.IsInfinity(v);
        }

        private bool IsInSession(DateTime now)
        {
            TimeSpan current = now.TimeOfDay;
            if (_sessionStart <= _sessionEnd)
                return current >= _sessionStart && current <= _sessionEnd;
            return current >= _sessionStart || current <= _sessionEnd;
        }

        private bool IsFridayEntryBlocked(DateTime now)
        {
            return now.DayOfWeek == DayOfWeek.Friday && _fridayLastEntry.HasValue && now.TimeOfDay >= _fridayLastEntry.Value;
        }

        private bool IsFridayForceCloseDue(DateTime now)
        {
            return now.DayOfWeek == DayOfWeek.Friday && _fridayForceClose.HasValue && now.TimeOfDay >= _fridayForceClose.Value;
        }

        private bool CooldownSatisfied(int signalBarIndex)
        {
            if (_lastExitBarIndex == int.MinValue || CooldownBars <= 0)
                return true;

            return signalBarIndex - _lastExitBarIndex >= CooldownBars;
        }

        private int CountManagedPositions()
        {
            return Positions.Count(p => p.SymbolName == SymbolName && p.Label == BotLabel);
        }

        private bool NoHedgingStateSatisfied()
        {
            var managed = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BotLabel).ToArray();
            if (managed.Length == 0)
                return true;

            bool hasBuy = managed.Any(p => p.TradeType == TradeType.Buy);
            bool hasSell = managed.Any(p => p.TradeType == TradeType.Sell);

            if (hasBuy && hasSell)
            {
                Print("[RISK_BLOCK] Hedged state detected. Closing all managed positions.");
                CloseAllPositions("HedgeStateDetected");
                return false;
            }

            return false;
        }

        private double GetAtrPips(int index)
        {
            double atrPrice = _atr.Result.Last(index);
            if (!IsFinite(atrPrice) || Symbol.PipSize <= 0)
                return 0;
            return atrPrice / Symbol.PipSize;
        }

        private bool PassesAtrFilter(double atrPips)
        {
            if (atrPips <= 0 || !IsFinite(atrPips))
                return false;

            if (MinAtrPips > 0 && atrPips < MinAtrPips)
            {
                Print("[FILTER] ATR too low: {0:F2} pips", atrPips);
                return false;
            }

            if (MaxAtrPips > 0 && atrPips > MaxAtrPips)
            {
                Print("[FILTER] ATR too high: {0:F2} pips", atrPips);
                return false;
            }

            return true;
        }

        private double ResolveStopLossPips(double atrPips)
        {
            double raw = atrPips * AtrSlMultiplier;
            double clamped = Math.Max(MinStopLossPips, Math.Min(MaxStopLossPips, raw));
            return Math.Max(clamped, GetMinimumStopDistancePips());
        }

        private double ResolveTakeProfitPips(double stopLossPips)
        {
            double tp = stopLossPips * RiskRewardRatio;
            return Math.Max(tp, GetMinimumTakeProfitDistancePips());
        }

        private bool PassesDistanceRules(double stopLossPips, double takeProfitPips)
        {
            if (!IsFinite(stopLossPips) || !IsFinite(takeProfitPips) || stopLossPips <= 0 || takeProfitPips <= 0)
                return false;

            if (stopLossPips < GetMinimumStopDistancePips())
            {
                Print("[FILTER] SL below broker minimum. SL={0:F2}", stopLossPips);
                return false;
            }

            if (takeProfitPips < GetMinimumTakeProfitDistancePips())
            {
                Print("[FILTER] TP below broker minimum. TP={0:F2}", takeProfitPips);
                return false;
            }

            return true;
        }

        private double GetSpreadPips()
        {
            if (Symbol.PipSize <= 0)
                return double.PositiveInfinity;
            return (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private bool PassesSpreadFilter(double spreadPips, double stopLossPips)
        {
            if (!IsFinite(spreadPips) || spreadPips < 0)
                return false;

            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
            {
                Print("[FILTER] Spread too high: {0:F2} pips", spreadPips);
                return false;
            }

            if (MaxSpreadToSlRatio > 0 && stopLossPips > 0)
            {
                double ratio = spreadPips / stopLossPips;
                if (ratio > MaxSpreadToSlRatio)
                {
                    Print("[FILTER] Spread/SL ratio too high: {0:F3}", ratio);
                    return false;
                }
            }

            return true;
        }

        private TradeType? BuildSignal()
        {
            double emaNow = _ema.Result.Last(1);
            double emaPrev = _ema.Result.Last(2);
            double closeNow = Bars.ClosePrices.Last(1);
            double closePrev = Bars.ClosePrices.Last(2);
            double highPrev = Bars.HighPrices.Last(2);
            double lowPrev = Bars.LowPrices.Last(2);
            double momentumNow = _momentum.Result.Last(1);
            double momentumPrev = _momentum.Result.Last(2);
            double atrPrice = _atr.Result.Last(1);

            if (!IsFinite(emaNow) || !IsFinite(emaPrev) || !IsFinite(atrPrice))
                return null;

            double htfEmaNow = _htfEma.Result.Last(1);
            double htfEmaPrev = _htfEma.Result.Last(2);
            bool htfBull = htfEmaNow > htfEmaPrev;
            bool htfBear = htfEmaNow < htfEmaPrev;

            bool entryEmaBull = emaNow > emaPrev;
            bool entryEmaBear = emaNow < emaPrev;

            bool pullbackBuy = lowPrev <= emaNow + atrPrice * PullbackAtrMultiplier && closePrev >= emaNow - atrPrice * PullbackAtrMultiplier;
            bool pullbackSell = highPrev >= emaNow - atrPrice * PullbackAtrMultiplier && closePrev <= emaNow + atrPrice * PullbackAtrMultiplier;

            bool momentumBull = momentumNow > 100 && momentumNow > momentumPrev;
            bool momentumBear = momentumNow < 100 && momentumNow < momentumPrev;

            bool resumeBuy = closeNow > highPrev && closeNow > emaNow;
            bool resumeSell = closeNow < lowPrev && closeNow < emaNow;

            if (htfBull && entryEmaBull && pullbackBuy && resumeBuy && momentumBull)
                return TradeType.Buy;

            if (htfBear && entryEmaBear && pullbackSell && resumeSell && momentumBear)
                return TradeType.Sell;

            return null;
        }

        private double CalculateVolumeInUnits(double stopLossPips)
        {
            double raw;

            if (UseFixedLotOverride)
            {
                raw = Symbol.QuantityToVolumeInUnits(FixedLotSize);
            }
            else
            {
                double riskAmount = Account.Equity * (RiskPerTradePercent / 100.0);
                double pipValuePerUnit = Symbol.PipValue;
                if (pipValuePerUnit <= 0 || stopLossPips <= 0 || riskAmount <= 0)
                    return 0;
                raw = riskAmount / (stopLossPips * pipValuePerUnit);
            }

            if (!IsFinite(raw) || raw <= 0)
                return 0;

            if (!UseFixedLotOverride && raw < Symbol.VolumeInUnitsMin)
            {
                Print("[VOLUME_SKIP] Risk sizing requires {0:F2} units, below broker minimum {1}.", raw, Symbol.VolumeInUnitsMin);
                return 0;
            }

            double capped = Math.Max(Symbol.VolumeInUnitsMin, Math.Min(Symbol.VolumeInUnitsMax, raw));
            double normalized = Symbol.NormalizeVolumeInUnits(capped, RoundingMode.Down);

            if (normalized < Symbol.VolumeInUnitsMin || normalized > Symbol.VolumeInUnitsMax)
            {
                Print("[VOLUME_FAIL] Normalized volume out of broker range. Raw={0} Normalized={1}", raw, normalized);
                return 0;
            }

            return normalized;
        }

        private void TryEnter(TradeType tradeType, double volume, double stopLossPips, double takeProfitPips, int signalBarIndex)
        {
            if (CountManagedPositions() > 0)
                return;

            var result = ExecuteMarketOrder(tradeType, SymbolName, volume, BotLabel, stopLossPips, takeProfitPips, "TrendPullback", false);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ENTRY_FAIL] Side={0} Vol={1} SL={2:F2} TP={3:F2} Error={4}", tradeType, volume, stopLossPips, takeProfitPips, result.Error);
                return;
            }

            _tradesToday++;
            _lastSignalBarIndex = signalBarIndex;

            if (result.Position.StopLoss.HasValue)
            {
                double riskPips = Math.Abs(result.Position.EntryPrice - result.Position.StopLoss.Value) / Symbol.PipSize;
                if (riskPips > 0 && IsFinite(riskPips))
                    _positionInitialRiskPips[result.Position.Id] = riskPips;
            }

            Print("[ENTRY_OK] Side={0} Id={1} Vol={2} SL={3:F2} TP={4:F2} TradesToday={5}", tradeType, result.Position.Id, volume, stopLossPips, takeProfitPips, _tradesToday);
        }

        private void ManageOpenPosition()
        {
            var position = Positions.Find(BotLabel, SymbolName);
            if (position == null)
                return;

            if (!position.StopLoss.HasValue)
            {
                Print("[RISK_FAIL] Position {0} missing stop loss, closing.", position.Id);
                var emergencyClose = ClosePosition(position);
                if (!emergencyClose.IsSuccessful)
                    Print("[CLOSE_FAIL] Emergency close failed Id={0} Error={1}", position.Id, emergencyClose.Error);
                return;
            }

            double initialRiskPips;
            if (!_positionInitialRiskPips.TryGetValue(position.Id, out initialRiskPips) || initialRiskPips <= 0)
            {
                initialRiskPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize;
                if (initialRiskPips <= 0 || !IsFinite(initialRiskPips))
                    return;
                _positionInitialRiskPips[position.Id] = initialRiskPips;
            }

            double rMultiple = position.Pips / initialRiskPips;

            if (rMultiple >= BreakevenTriggerR)
            {
                double bePrice = position.TradeType == TradeType.Buy
                    ? position.EntryPrice + BreakevenBufferPips * Symbol.PipSize
                    : position.EntryPrice - BreakevenBufferPips * Symbol.PipSize;
                TryModifyStop(position, bePrice, "Breakeven");
            }

            if (EnableAtrTrailing && rMultiple >= TrailingStartR)
            {
                double atrPips = GetAtrPips(0);
                if (atrPips > 0)
                {
                    double trailDistance = atrPips * AtrTrailMultiplier * Symbol.PipSize;
                    double trailStop = position.TradeType == TradeType.Buy
                        ? Symbol.Bid - trailDistance
                        : Symbol.Ask + trailDistance;
                    TryModifyStop(position, trailStop, "ATR_Trailing");
                }
            }
        }

        private void TryModifyStop(Position position, double proposedStop, string reason)
        {
            if (!IsLegalImprovedStop(position, proposedStop))
                return;

            var result = ModifyPosition(position, proposedStop, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[MODIFY_FAIL] Id={0} Reason={1} ProposedSL={2} Error={3}", position.Id, reason, proposedStop, result.Error);
                return;
            }

            Print("[MODIFY_OK] Id={0} Reason={1} NewSL={2}", position.Id, reason, proposedStop);
        }

        private bool IsLegalImprovedStop(Position position, double proposedStop)
        {
            double minDistancePips = GetMinimumStopDistancePips();
            double minDistancePrice = minDistancePips * Symbol.PipSize;

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

        private void CloseAllPositions(string reason)
        {
            foreach (var position in Positions.FindAll(BotLabel, SymbolName).ToArray())
            {
                var result = ClosePosition(position);
                if (!result.IsSuccessful)
                    Print("[CLOSE_FAIL] Reason={0} Id={1} Error={2}", reason, position.Id, result.Error);
                else
                    Print("[CLOSE_OK] Reason={0} Id={1}", reason, position.Id);
            }
        }

        private bool IsManagedPosition(Position position)
        {
            return position != null && position.SymbolName == SymbolName && position.Label == BotLabel;
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

            double referencePrice = (Symbol.Bid + Symbol.Ask) * 0.5;
            double priceDistance = referencePrice * (minimumDistance / 100.0);
            return priceDistance / Symbol.PipSize;
        }
    }
}
