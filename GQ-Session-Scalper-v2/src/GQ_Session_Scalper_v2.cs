// GQ_Session_Scalper_v2
// Independent hardening of the open-source Gueta Quant session scalper.
// Cloud/Mobile safe: AccessRights.None; no local files, credentials or network access.
// Forbidden by design: Grid, Martingale, DCA, Recovery, Loss Averaging and Hedging.

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public enum GqTrailingMode
    {
        Atr,
        Swing,
        Chandelier
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GQ_Session_Scalper_v2 : Robot
    {
        private const string BotLabel = "GQ-Session-Scalper-v2";
        private const int MaxOpenPositions = 1;

        [Parameter("Trading Enabled", Group = "General", DefaultValue = true)]
        public bool TradingEnabled { get; set; }

        [Parameter("Session Start (HH:mm)", Group = "Session", DefaultValue = "08:00")]
        public string SessionStart { get; set; }

        [Parameter("Session End (HH:mm)", Group = "Session", DefaultValue = "16:00")]
        public string SessionEnd { get; set; }

        [Parameter("Friday Last Entry UTC Hour", Group = "Session", DefaultValue = 18, MinValue = 0, MaxValue = 23)]
        public int FridayLastEntryHourUtc { get; set; }

        [Parameter("Friday Force Close UTC Hour", Group = "Session", DefaultValue = 20, MinValue = 0, MaxValue = 23)]
        public int FridayForceCloseHourUtc { get; set; }

        [Parameter("Risk Per Trade (%)", Group = "Risk", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 1.0, Step = 0.05)]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Max Daily Loss (%)", Group = "Risk", DefaultValue = 2.0, MinValue = 0.25, MaxValue = 10.0, Step = 0.25)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Session Loss (R)", Group = "Risk", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0, Step = 0.5)]
        public double MaxSessionLossR { get; set; }

        [Parameter("Max Losing R / Day", Group = "Risk", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 10.0, Step = 0.5)]
        public double MaxLosingRPerDay { get; set; }

        [Parameter("Max Consecutive Losses", Group = "Risk", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Max Trades / Day", Group = "Risk", DefaultValue = 6, MinValue = 1, MaxValue = 30)]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Minimum Equity", Group = "Risk", DefaultValue = 0.0, MinValue = 0.0)]
        public double MinimumEquity { get; set; }

        [Parameter("Profit Lock Trigger (R, 0=off)", Group = "Risk", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 10.0, Step = 0.5)]
        public double ProfitLockTriggerR { get; set; }

        [Parameter("Profit Lock Risk Multiplier", Group = "Risk", DefaultValue = 1.0, MinValue = 0.25, MaxValue = 1.0, Step = 0.05)]
        public double ProfitLockRiskMultiplier { get; set; }

        [Parameter("EMA Period", Group = "Entry", DefaultValue = 21, MinValue = 2, MaxValue = 200)]
        public int EMAPeriod { get; set; }

        [Parameter("Momentum Period", Group = "Entry", DefaultValue = 14, MinValue = 2, MaxValue = 100)]
        public int MomentumPeriod { get; set; }

        [Parameter("Momentum Threshold", Group = "Entry", DefaultValue = 100.0, MinValue = 1.0, MaxValue = 200.0, Step = 0.1)]
        public double MomentumThreshold { get; set; }

        [Parameter("Pullback ATR Fraction", Group = "Entry", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Step = 0.05)]
        public double PullbackAtrFraction { get; set; }

        [Parameter("Allow Grade B", Group = "Entry", DefaultValue = false)]
        public bool AllowGradeB { get; set; }

        [Parameter("Trend EMA Fast", Group = "HTF Trend", DefaultValue = 50, MinValue = 2, MaxValue = 200)]
        public int TrendFastPeriod { get; set; }

        [Parameter("Trend EMA Slow", Group = "HTF Trend", DefaultValue = 200, MinValue = 10, MaxValue = 500)]
        public int TrendSlowPeriod { get; set; }

        [Parameter("Trend TimeFrame", Group = "HTF Trend", DefaultValue = "Hour")]
        public TimeFrame TrendTimeFrame { get; set; }

        [Parameter("ATR Period", Group = "Volatility", DefaultValue = 14, MinValue = 2, MaxValue = 100)]
        public int ATRPeriod { get; set; }

        [Parameter("Min ATR (pips, 0=off)", Group = "Volatility", DefaultValue = 0.0, MinValue = 0.0)]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR (pips, 0=off)", Group = "Volatility", DefaultValue = 0.0, MinValue = 0.0)]
        public double MaxAtrPips { get; set; }

        [Parameter("Extreme ATR %", Group = "Volatility", DefaultValue = 1.50, MinValue = 0.05, MaxValue = 20.0, Step = 0.05)]
        public double ExtremeAtrPercent { get; set; }

        [Parameter("ATR SL Multiplier", Group = "Volatility", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 5.0, Step = 0.1)]
        public double AtrSlMultiplier { get; set; }

        [Parameter("Minimum SL (pips)", Group = "Volatility", DefaultValue = 5.0, MinValue = 0.1, MaxValue = 10000.0, Step = 0.1)]
        public double MinimumSlPips { get; set; }

        [Parameter("Maximum SL (pips, 0=off)", Group = "Volatility", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 100000.0, Step = 0.5)]
        public double MaximumSlPips { get; set; }

        [Parameter("TP R Multiple", Group = "Trade Management", DefaultValue = 1.5, MinValue = 1.0, MaxValue = 5.0, Step = 0.1)]
        public double TpRMultiple { get; set; }

        [Parameter("Breakeven Trigger (R)", Group = "Trade Management", DefaultValue = 1.0, MinValue = 0.5, MaxValue = 3.0, Step = 0.1)]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Cost Buffer (pips)", Group = "Trade Management", DefaultValue = 0.3, MinValue = 0.0, MaxValue = 100.0, Step = 0.1)]
        public double BreakevenCostBufferPips { get; set; }

        [Parameter("Trailing Trigger (R)", Group = "Trade Management", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 5.0, Step = 0.1)]
        public double TrailingTriggerR { get; set; }

        [Parameter("Trailing Mode", Group = "Trade Management", DefaultValue = GqTrailingMode.Atr)]
        public GqTrailingMode TrailingMode { get; set; }

        [Parameter("Trailing ATR Multiplier", Group = "Trade Management", DefaultValue = 1.2, MinValue = 0.25, MaxValue = 5.0, Step = 0.1)]
        public double TrailingAtrMultiplier { get; set; }

        [Parameter("Swing Lookback Bars", Group = "Trade Management", DefaultValue = 3, MinValue = 2, MaxValue = 20)]
        public int SwingLookbackBars { get; set; }

        [Parameter("Max Holding Bars (0=off)", Group = "Trade Management", DefaultValue = 0, MinValue = 0, MaxValue = 500)]
        public int MaxHoldingBars { get; set; }

        [Parameter("Stagnation Bars (0=off)", Group = "Trade Management", DefaultValue = 0, MinValue = 0, MaxValue = 500)]
        public int StagnationBars { get; set; }

        [Parameter("Stagnation Min MFE (R)", Group = "Trade Management", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 5.0, Step = 0.05)]
        public double StagnationMinMfeR { get; set; }

        [Parameter("Structural Failure Exit", Group = "Trade Management", DefaultValue = false)]
        public bool StructuralFailureExit { get; set; }

        [Parameter("Partial Exit Trigger (R, 0=off)", Group = "Trade Management", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 5.0, Step = 0.1)]
        public double PartialExitTriggerR { get; set; }

        [Parameter("Partial Exit (%)", Group = "Trade Management", DefaultValue = 50.0, MinValue = 10.0, MaxValue = 90.0, Step = 5.0)]
        public double PartialExitPercent { get; set; }

        [Parameter("Cooldown Bars", Group = "Execution", DefaultValue = 1, MinValue = 0, MaxValue = 100)]
        public int CooldownBars { get; set; }

        [Parameter("Loss Cooldown Bars", Group = "Execution", DefaultValue = 3, MinValue = 0, MaxValue = 200)]
        public int LossCooldownBars { get; set; }

        [Parameter("Consecutive Loss Extra Bars", Group = "Execution", DefaultValue = 2, MinValue = 0, MaxValue = 100)]
        public int ConsecutiveLossExtraBars { get; set; }

        [Parameter("Maximum Spread (pips)", Group = "Costs", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 10000.0, Step = 0.1)]
        public double MaximumSpreadPips { get; set; }

        [Parameter("Estimated Slippage (pips)", Group = "Costs", DefaultValue = 0.2, MinValue = 0.0, MaxValue = 100.0, Step = 0.1)]
        public double EstimatedSlippagePips { get; set; }

        [Parameter("Estimated Commission (pips RT)", Group = "Costs", DefaultValue = 0.2, MinValue = 0.0, MaxValue = 100.0, Step = 0.1)]
        public double EstimatedCommissionPips { get; set; }

        [Parameter("Max Spread / SL", Group = "Costs", DefaultValue = 0.15, MinValue = 0.01, MaxValue = 1.0, Step = 0.01)]
        public double MaxSpreadToSlRatio { get; set; }

        [Parameter("Max Cost / Expected TP", Group = "Costs", DefaultValue = 0.20, MinValue = 0.01, MaxValue = 1.0, Step = 0.01)]
        public double MaxCostToExpectedProfitRatio { get; set; }

        private sealed class SignalCandidate
        {
            public TradeType TradeType;
            public string Grade;
            public int Score;
            public string Id;
            public string Session;
        }

        private sealed class PositionState
        {
            public double InitialRiskPips;
            public double RiskMoney;
            public int EntryBarIndex;
            public DateTime EntryTime;
            public double MfePips;
            public double MaePips;
            public bool PartialDone;
            public string Grade;
            public string SignalId;
            public string Session;
            public string ManagedExitReason;
        }

        private ExponentialMovingAverage _entryEma;
        private AverageTrueRange _atr;
        private Bars _trendBars;
        private ExponentialMovingAverage _trendFast;
        private ExponentialMovingAverage _trendSlow;
        private readonly Dictionary<int, PositionState> _states = new Dictionary<int, PositionState>();
        private readonly Dictionary<string, double> _sessionNet = new Dictionary<string, double>();
        private readonly Dictionary<string, int> _sessionTrades = new Dictionary<string, int>();
        private TimeSpan _sessionStart;
        private TimeSpan _sessionEnd;
        private DateTime _riskDate;
        private double _dayStartEquity;
        private double _dailyR;
        private double _dailyLosingR;
        private double _sessionR;
        private int _tradesToday;
        private int _consecutiveLosses;
        private int _nextEntryBarIndex;
        private DateTime _lastSignalBar = DateTime.MinValue;
        private DateTime _lastEntryBar = DateTime.MinValue;
        private bool _stoppedForRisk;
        private int _closedTrades;
        private int _wins;
        private double _grossWins;
        private double _grossLosses;
        private double _sumR;
        private double _sumMfe;
        private double _sumMae;
        private double _sumHoldingMinutes;
        private double _longNet;
        private double _shortNet;
        private int _longTrades;
        private int _shortTrades;

        protected override void OnStart()
        {
            try
            {
                ValidateParameters();
                _entryEma = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EMAPeriod);
                _atr = Indicators.AverageTrueRange(ATRPeriod, MovingAverageType.Exponential);
                _trendBars = MarketData.GetBars(TrendTimeFrame);
                _trendFast = Indicators.ExponentialMovingAverage(_trendBars.ClosePrices, TrendFastPeriod);
                _trendSlow = Indicators.ExponentialMovingAverage(_trendBars.ClosePrices, TrendSlowPeriod);
                _sessionStart = ParseTime(SessionStart, new TimeSpan(8, 0, 0));
                _sessionEnd = ParseTime(SessionEnd, new TimeSpan(16, 0, 0));
                ResetDay();
                Positions.Closed += OnManagedPositionClosed;

                Print("[START] {0} Symbol={1} TF={2} MaxOpenPositions={3}", BotLabel, SymbolName, TimeFrame, MaxOpenPositions);
                Print("[SOURCE] upstream=guetaquant-byte/guetaquant-tools ctrader/GQ_Session_Scalper.cs blob=0ebb802aae6ccbfaf4a83548a04f76ba0865424d");
                Print("[SYMBOL] PipSize={0} TickSize={1} PipValue={2} TickValue={3} VolMin={4} VolMax={5} VolStep={6} MinSL={7} MinTP={8} MinDistanceType={9} Spread={10} Commission={11} CommissionType={12}",
                    Symbol.PipSize, Symbol.TickSize, Symbol.PipValue, Symbol.TickValue,
                    Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep,
                    Symbol.MinStopLossDistance, Symbol.MinTakeProfitDistance, Symbol.MinDistanceType,
                    Symbol.Spread, Symbol.Commission, Symbol.CommissionType);
            }
            catch (Exception ex)
            {
                Print("[START_ERROR] {0}", ex.Message);
                Stop();
            }
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnManagedPositionClosed;
            double pf = _grossLosses < 0 ? _grossWins / Math.Abs(_grossLosses) : (_grossWins > 0 ? double.PositiveInfinity : 0);
            double avgR = _closedTrades > 0 ? _sumR / _closedTrades : 0;
            double avgMfe = _closedTrades > 0 ? _sumMfe / _closedTrades : 0;
            double avgMae = _closedTrades > 0 ? _sumMae / _closedTrades : 0;
            double avgHold = _closedTrades > 0 ? _sumHoldingMinutes / _closedTrades : 0;
            Print("[SUMMARY] Trades={0} Wins={1} PF={2:F3} AvgR={3:F3} AvgMFEp={4:F2} AvgMAEp={5:F2} AvgHoldMin={6:F1} LongTrades={7} LongNet={8:F2} ShortTrades={9} ShortNet={10:F2}",
                _closedTrades, _wins, pf, avgR, avgMfe, avgMae, avgHold, _longTrades, _longNet, _shortTrades, _shortNet);
            foreach (var item in _sessionTrades.OrderBy(k => k.Key))
                Print("[SESSION_SUMMARY] {0} Trades={1} Net={2:F2}", item.Key, item.Value, _sessionNet.ContainsKey(item.Key) ? _sessionNet[item.Key] : 0);
        }

        protected override void OnBarClosed()
        {
            try
            {
                ResetDailyRiskIfNeeded();
                ManageBarBasedExit();

                if (!TradingEnabled || !CanEnterNow())
                    return;

                DateTime signalBar = Bars.OpenTimes.Last(0);
                if (signalBar == _lastSignalBar || signalBar == _lastEntryBar)
                    return;
                _lastSignalBar = signalBar;

                int warmup = Math.Max(Math.Max(EMAPeriod, ATRPeriod), MomentumPeriod) + 5;
                if (Bars.Count < warmup || _trendBars.Count < TrendSlowPeriod + 5)
                    return;

                var signal = GetSignal(signalBar);
                if (signal == null)
                    return;
                if (signal.Grade == "B" && !AllowGradeB)
                {
                    Print("[SIGNAL_REJECT] GradeB disabled id={0}", signal.Id);
                    return;
                }

                double atrPips = _atr.Result.Last(0) / Symbol.PipSize;
                double atrPercent = _atr.Result.Last(0) / Math.Max(Symbol.PipSize, Bars.ClosePrices.Last(0)) * 100.0;
                if (!PassesVolatilityRegime(atrPips, atrPercent))
                    return;

                double brokerMinSl = GetBrokerMinStopLossPips();
                double stopLossPips = Math.Max(MinimumSlPips, Math.Max(atrPips * AtrSlMultiplier, brokerMinSl * 1.05));
                if (MaximumSlPips > 0 && stopLossPips > MaximumSlPips)
                {
                    Print("[VOL_REJECT] SL={0:F2} > MaxSL={1:F2}", stopLossPips, MaximumSlPips);
                    return;
                }

                double takeProfitPips = Math.Max(stopLossPips * TpRMultiple, GetBrokerMinTakeProfitPips() * 1.05);
                if (!PassesCostFilter(stopLossPips, takeProfitPips))
                    return;

                double riskPct = EffectiveRiskPercent();
                double volume = CalculateRiskBasedVolume(stopLossPips, riskPct);
                if (volume < Symbol.VolumeInUnitsMin)
                {
                    Print("[RISK_REJECT] Risk budget below broker minimum volume.");
                    return;
                }

                ExecuteEntry(signal, volume, stopLossPips, takeProfitPips, riskPct);
            }
            catch (Exception ex)
            {
                Print("[BAR_CLOSE_ERROR] {0}", ex.Message);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDailyRiskIfNeeded();
                ManageTickPosition();
                ApplyEmergencyRiskControls();
            }
            catch (Exception ex)
            {
                Print("[TICK_MANAGEMENT_ERROR] {0}", ex.Message);
            }
        }

        private SignalCandidate GetSignal(DateTime signalBar)
        {
            double close = Bars.ClosePrices.Last(0);
            double open = Bars.OpenPrices.Last(0);
            double previousClose = Bars.ClosePrices.Last(1);
            double ema = _entryEma.Result.Last(0);
            double previousEma = _entryEma.Result.Last(1);
            double momentumReference = Bars.ClosePrices.Last(MomentumPeriod);
            double momentum = momentumReference > 0
                ? close / momentumReference * 100.0
                : 100.0;
            double atr = _atr.Result.Last(0);
            double trendFast = _trendFast.Result.Last(1);
            double trendSlow = _trendSlow.Result.Last(1);
            double previousTrendFast = _trendFast.Result.Last(2);

            bool trendUp = trendFast > trendSlow && trendFast > previousTrendFast;
            bool trendDown = trendFast < trendSlow && trendFast < previousTrendFast;
            bool ltfUp = close > ema && ema > previousEma;
            bool ltfDown = close < ema && ema < previousEma;
            bool touchedEma = Bars.HighPrices.Last(0) >= ema && Bars.LowPrices.Last(0) <= ema;
            bool nearEma = Math.Abs(close - ema) <= atr * PullbackAtrFraction;
            bool pullback = touchedEma || nearEma;
            bool bullishReversal = close > open && close > previousClose;
            bool bearishReversal = close < open && close < previousClose;
            bool bullishMomentum = momentum > MomentumThreshold;
            bool bearishMomentum = momentum < MomentumThreshold;

            TradeType? direction = null;
            if (trendUp && ltfUp && pullback && bullishReversal && bullishMomentum)
                direction = TradeType.Buy;
            else if (trendDown && ltfDown && pullback && bearishReversal && bearishMomentum)
                direction = TradeType.Sell;
            if (!direction.HasValue)
                return null;

            double trendSeparation = Math.Abs(trendFast - trendSlow) / Math.Max(Symbol.PipSize, atr);
            double momentumDistance = Math.Abs(momentum - MomentumThreshold);
            int score = 4;
            if (trendSeparation >= 0.50)
                score++;
            if (momentumDistance >= 0.20)
                score++;
            string grade = score >= 5 ? "A" : "B";
            string id = string.Format("{0}-{1}-{2:yyyyMMddHHmm}-{3}", SymbolName, TimeFrame, signalBar, direction.Value);
            return new SignalCandidate
            {
                TradeType = direction.Value,
                Grade = grade,
                Score = score,
                Id = id,
                Session = GetSessionBucket(signalBar)
            };
        }

        private bool PassesVolatilityRegime(double atrPips, double atrPercent)
        {
            if (!IsFinitePositive(atrPips))
                return false;
            if (MinAtrPips > 0 && atrPips < MinAtrPips)
            {
                Print("[VOL_REJECT] LOW atrPips={0:F2}", atrPips);
                return false;
            }
            if (MaxAtrPips > 0 && atrPips > MaxAtrPips)
            {
                Print("[VOL_REJECT] HIGH atrPips={0:F2}", atrPips);
                return false;
            }
            if (atrPercent >= ExtremeAtrPercent)
            {
                Print("[VOL_REJECT] EXTREME atrPct={0:F3}", atrPercent);
                return false;
            }
            return true;
        }

        private bool PassesCostFilter(double stopLossPips, double takeProfitPips)
        {
            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            double expectedCostPips = spreadPips + EstimatedSlippagePips + EstimatedCommissionPips;
            if (spreadPips > MaximumSpreadPips)
            {
                Print("[COST_REJECT] spread={0:F2}", spreadPips);
                return false;
            }
            if (spreadPips / Math.Max(0.1, stopLossPips) > MaxSpreadToSlRatio)
            {
                Print("[COST_REJECT] spread/sl={0:F3}", spreadPips / stopLossPips);
                return false;
            }
            if (expectedCostPips / Math.Max(0.1, takeProfitPips) > MaxCostToExpectedProfitRatio)
            {
                Print("[COST_REJECT] cost/tp={0:F3}", expectedCostPips / takeProfitPips);
                return false;
            }
            return true;
        }

        private double CalculateRiskBasedVolume(double stopLossPips, double riskPercent)
        {
            double volume = Symbol.VolumeForProportionalRisk(RiskType.Equity, riskPercent, stopLossPips, RoundingMode.Down);
            if (!IsFinitePositive(volume))
                return 0;
            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume < Symbol.VolumeInUnitsMin)
                return 0;

            double budget = Account.Equity * riskPercent / 100.0;
            double estimatedRisk = Symbol.AmountRisked(volume, stopLossPips);
            if (!IsFinitePositive(estimatedRisk) || estimatedRisk > budget * 1.01)
            {
                Print("[RISK_REJECT] estimated={0:F4} budget={1:F4} volume={2}", estimatedRisk, budget, volume);
                return 0;
            }
            return volume;
        }

        private void ExecuteEntry(SignalCandidate signal, double volume, double stopLossPips, double takeProfitPips, double riskPercent)
        {
            if (HasAnyManagedPosition() || _stoppedForRisk)
                return;

            var result = ExecuteMarketOrder(signal.TradeType, SymbolName, volume, BotLabel,
                stopLossPips, takeProfitPips,
                string.Format("grade={0};score={1};signal={2};session={3}", signal.Grade, signal.Score, signal.Id, signal.Session));
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ENTRY_ERROR] {0}", result.Error);
                return;
            }

            double riskMoney = Symbol.AmountRisked(result.Position.VolumeInUnits, stopLossPips);
            _states[result.Position.Id] = new PositionState
            {
                InitialRiskPips = stopLossPips,
                RiskMoney = riskMoney,
                EntryBarIndex = Bars.Count - 1,
                EntryTime = Server.Time,
                Grade = signal.Grade,
                SignalId = signal.Id,
                Session = signal.Session,
                ManagedExitReason = ""
            };
            _tradesToday++;
            _lastEntryBar = Bars.OpenTimes.Last(0);
            _nextEntryBarIndex = Bars.Count - 1 + CooldownBars;
            Print("[ENTRY] id={0} grade={1} score={2} side={3} volume={4} riskPct={5:F2} SLp={6:F2} TPp={7:F2} session={8}",
                signal.Id, signal.Grade, signal.Score, signal.TradeType, result.Position.VolumeInUnits, riskPercent, stopLossPips, takeProfitPips, signal.Session);
        }

        private void ManageTickPosition()
        {
            var position = Positions.FirstOrDefault(p => p.Label == BotLabel);
            if (position == null)
                return;
            PositionState state;
            if (!_states.TryGetValue(position.Id, out state))
                return;

            double favorablePips = position.TradeType == TradeType.Buy
                ? (Symbol.Bid - position.EntryPrice) / Symbol.PipSize
                : (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
            double adversePips = position.TradeType == TradeType.Buy
                ? (position.EntryPrice - Symbol.Bid) / Symbol.PipSize
                : (Symbol.Ask - position.EntryPrice) / Symbol.PipSize;
            state.MfePips = Math.Max(state.MfePips, Math.Max(0, favorablePips));
            state.MaePips = Math.Max(state.MaePips, Math.Max(0, adversePips));
            double r = favorablePips / Math.Max(0.1, state.InitialRiskPips);

            if (r >= BreakevenTriggerR)
            {
                double be = position.TradeType == TradeType.Buy
                    ? position.EntryPrice + BreakevenCostBufferPips * Symbol.PipSize
                    : position.EntryPrice - BreakevenCostBufferPips * Symbol.PipSize;
                TryImproveStop(position, be, "Breakeven");
            }

            if (r >= TrailingTriggerR)
            {
                double candidate = GetTrailingStop(position, state);
                if (IsFinitePositive(candidate))
                    TryImproveStop(position, candidate, "Trailing-" + TrailingMode);
            }

            if (PartialExitTriggerR > 0 && !state.PartialDone && r >= PartialExitTriggerR)
                TryPartialExit(position, state);

            if (Server.Time.DayOfWeek == DayOfWeek.Friday && Server.Time.Hour >= FridayForceCloseHourUtc)
                RequestClose(position, state, "FridayForceClose");
        }

        private double GetTrailingStop(Position position, PositionState state)
        {
            double atr = _atr.Result.Last(0);
            if (!IsFinitePositive(atr))
                return double.NaN;

            if (TrailingMode == GqTrailingMode.Atr)
                return position.TradeType == TradeType.Buy
                    ? Symbol.Bid - atr * TrailingAtrMultiplier
                    : Symbol.Ask + atr * TrailingAtrMultiplier;

            if (TrailingMode == GqTrailingMode.Swing)
            {
                int lookback = Math.Min(SwingLookbackBars, Bars.Count - 1);
                if (lookback < 2)
                    return double.NaN;
                double level = position.TradeType == TradeType.Buy ? double.MaxValue : double.MinValue;
                for (int i = 0; i < lookback; i++)
                {
                    if (position.TradeType == TradeType.Buy)
                        level = Math.Min(level, Bars.LowPrices.Last(i));
                    else
                        level = Math.Max(level, Bars.HighPrices.Last(i));
                }
                return level;
            }

            double anchor = position.TradeType == TradeType.Buy
                ? position.EntryPrice + state.MfePips * Symbol.PipSize
                : position.EntryPrice - state.MfePips * Symbol.PipSize;
            return position.TradeType == TradeType.Buy
                ? anchor - atr * TrailingAtrMultiplier
                : anchor + atr * TrailingAtrMultiplier;
        }

        private void TryImproveStop(Position position, double candidateStop, string reason)
        {
            if (!IsFinitePositive(candidateStop))
                return;
            double minPips = GetBrokerMinStopLossPips() * 1.05;
            if (position.TradeType == TradeType.Buy)
                candidateStop = Math.Min(candidateStop, Symbol.Bid - minPips * Symbol.PipSize);
            else
                candidateStop = Math.Max(candidateStop, Symbol.Ask + minPips * Symbol.PipSize);
            candidateStop = Math.Round(candidateStop, Symbol.Digits);

            bool improves = !position.StopLoss.HasValue ||
                (position.TradeType == TradeType.Buy && candidateStop > position.StopLoss.Value) ||
                (position.TradeType == TradeType.Sell && candidateStop < position.StopLoss.Value);
            if (!improves)
                return;

            var result = ModifyPosition(position, candidateStop, position.TakeProfit);
            if (!result.IsSuccessful)
            {
                Print("[STOP_UPDATE_ERROR] reason={0} error={1}", reason, result.Error);
                return;
            }
            PositionState state;
            if (_states.TryGetValue(position.Id, out state))
                state.ManagedExitReason = reason;
        }

        private void TryPartialExit(Position position, PositionState state)
        {
            double closeVolume = Symbol.NormalizeVolumeInUnits(position.VolumeInUnits * PartialExitPercent / 100.0, RoundingMode.Down);
            double remaining = position.VolumeInUnits - closeVolume;
            if (closeVolume < Symbol.VolumeInUnitsMin || remaining < Symbol.VolumeInUnitsMin)
            {
                state.PartialDone = true;
                return;
            }
            var result = ClosePosition(position, closeVolume);
            if (!result.IsSuccessful)
            {
                Print("[PARTIAL_EXIT_ERROR] {0}", result.Error);
                return;
            }
            state.PartialDone = true;
            Print("[PARTIAL_EXIT] volume={0} triggerR={1:F2}", closeVolume, PartialExitTriggerR);
        }

        private void ManageBarBasedExit()
        {
            var position = Positions.FirstOrDefault(p => p.Label == BotLabel);
            if (position == null)
                return;
            PositionState state;
            if (!_states.TryGetValue(position.Id, out state))
                return;
            int heldBars = Math.Max(0, (Bars.Count - 1) - state.EntryBarIndex);
            double mfeR = state.MfePips / Math.Max(0.1, state.InitialRiskPips);

            if (MaxHoldingBars > 0 && heldBars >= MaxHoldingBars)
            {
                RequestClose(position, state, "TimeExit");
                return;
            }
            if (StagnationBars > 0 && heldBars >= StagnationBars && mfeR < StagnationMinMfeR)
            {
                RequestClose(position, state, "StagnationExit");
                return;
            }
            if (StructuralFailureExit)
            {
                double close = Bars.ClosePrices.Last(0);
                double ema = _entryEma.Result.Last(0);
                double prevEma = _entryEma.Result.Last(1);
                bool failed = position.TradeType == TradeType.Buy
                    ? close < ema && ema < prevEma
                    : close > ema && ema > prevEma;
                if (failed)
                    RequestClose(position, state, "StructuralFailure");
            }
        }

        private void RequestClose(Position position, PositionState state, string reason)
        {
            state.ManagedExitReason = reason;
            var result = ClosePosition(position);
            if (!result.IsSuccessful)
                Print("[CLOSE_ERROR] reason={0} error={1}", reason, result.Error);
        }

        private void ApplyEmergencyRiskControls()
        {
            double dailyLossPct = (_dayStartEquity - Account.Equity) / Math.Max(1.0, _dayStartEquity) * 100.0;
            if (dailyLossPct < MaxDailyLossPercent)
                return;
            _stoppedForRisk = true;
            var position = Positions.FirstOrDefault(p => p.Label == BotLabel);
            if (position != null)
            {
                PositionState state;
                if (_states.TryGetValue(position.Id, out state))
                    RequestClose(position, state, "MaxDailyLossEmergency");
            }
            Print("[RISK_STOP] MaxDailyLoss reached={0:F2}%", dailyLossPct);
        }

        private void OnManagedPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p.Label != BotLabel)
                return;

            PositionState state;
            _states.TryGetValue(p.Id, out state);
            double riskMoney = state != null && state.RiskMoney > 0 ? state.RiskMoney : Math.Abs(p.NetProfit);
            double realizedR = riskMoney > 0 ? p.NetProfit / riskMoney : 0;
            string exitReason = state != null && !string.IsNullOrWhiteSpace(state.ManagedExitReason)
                ? state.ManagedExitReason
                : args.Reason.ToString();
            string session = state != null ? state.Session : GetSessionBucket(Server.Time);
            double mfe = state != null ? state.MfePips : 0;
            double mae = state != null ? state.MaePips : 0;
            double holding = state != null ? (Server.Time - state.EntryTime).TotalMinutes : 0;

            _closedTrades++;
            _sumR += realizedR;
            _sumMfe += mfe;
            _sumMae += mae;
            _sumHoldingMinutes += Math.Max(0, holding);
            _dailyR += realizedR;
            _sessionR += realizedR;
            if (p.NetProfit > 0)
            {
                _wins++;
                _grossWins += p.NetProfit;
                _consecutiveLosses = 0;
            }
            else if (p.NetProfit < 0)
            {
                _grossLosses += p.NetProfit;
                _consecutiveLosses++;
                _dailyLosingR += Math.Abs(Math.Min(0, realizedR));
                int extra = LossCooldownBars + Math.Max(0, _consecutiveLosses - 1) * ConsecutiveLossExtraBars;
                _nextEntryBarIndex = Math.Max(_nextEntryBarIndex, Bars.Count - 1 + extra);
            }

            if (p.TradeType == TradeType.Buy)
            {
                _longTrades++;
                _longNet += p.NetProfit;
            }
            else
            {
                _shortTrades++;
                _shortNet += p.NetProfit;
            }
            if (!_sessionTrades.ContainsKey(session))
            {
                _sessionTrades[session] = 0;
                _sessionNet[session] = 0;
            }
            _sessionTrades[session]++;
            _sessionNet[session] += p.NetProfit;

            Print("[CLOSE] id={0} side={1} net={2:F2} R={3:F3} MFEp={4:F2} MAEp={5:F2} holdMin={6:F1} exit={7} grade={8} session={9}",
                state != null ? state.SignalId : "unknown", p.TradeType, p.NetProfit, realizedR, mfe, mae, holding, exitReason,
                state != null ? state.Grade : "unknown", session);
            _states.Remove(p.Id);
        }

        private bool CanEnterNow()
        {
            if (_stoppedForRisk || !IsInSession(Server.Time))
                return false;
            if (HasAnyManagedPosition())
                return false;
            if (Bars.Count - 1 < _nextEntryBarIndex)
                return false;
            if (_tradesToday >= MaxTradesPerDay)
                return false;
            if (_consecutiveLosses >= MaxConsecutiveLosses)
                return false;
            if (_dailyLosingR >= MaxLosingRPerDay)
                return false;
            if (_sessionR <= -Math.Abs(MaxSessionLossR))
                return false;
            if (MinimumEquity > 0 && Account.Equity < MinimumEquity)
                return false;
            if (Server.Time.DayOfWeek == DayOfWeek.Friday && Server.Time.Hour >= FridayLastEntryHourUtc)
                return false;

            double dailyLossPct = (_dayStartEquity - Account.Equity) / Math.Max(1.0, _dayStartEquity) * 100.0;
            if (dailyLossPct >= MaxDailyLossPercent)
            {
                _stoppedForRisk = true;
                return false;
            }
            return true;
        }

        private bool HasAnyManagedPosition()
        {
            return Positions.Count(p => p.Label == BotLabel) >= MaxOpenPositions;
        }

        private double EffectiveRiskPercent()
        {
            if (ProfitLockTriggerR > 0 && _dailyR >= ProfitLockTriggerR)
                return RiskPerTradePercent * ProfitLockRiskMultiplier;
            return RiskPerTradePercent;
        }

        private bool IsInSession(DateTime time)
        {
            TimeSpan current = time.TimeOfDay;
            return _sessionStart <= _sessionEnd
                ? current >= _sessionStart && current <= _sessionEnd
                : current >= _sessionStart || current <= _sessionEnd;
        }

        private string GetSessionBucket(DateTime time)
        {
            int h = time.Hour;
            if (h >= 7 && h < 10) return "LondonEarly";
            if (h >= 10 && h < 12) return "LondonMid";
            if (h >= 12 && h < 16) return "Overlap";
            if (h >= 16 && h < 18) return "NYEarly";
            if (h >= 18 && h < 21) return "NYLate";
            return "Other";
        }

        private double GetBrokerMinStopLossPips()
        {
            return ConvertMinDistanceToPips(Symbol.MinStopLossDistance);
        }

        private double GetBrokerMinTakeProfitPips()
        {
            return ConvertMinDistanceToPips(Symbol.MinTakeProfitDistance);
        }

        private double ConvertMinDistanceToPips(double minimumDistance)
        {
            double floor = Math.Max(Symbol.TickSize / Math.Max(Symbol.PipSize, double.Epsilon), 0.1);
            if (minimumDistance <= 0)
                return floor;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return Math.Max(minimumDistance, floor);
            double referencePrice = (Symbol.Bid + Symbol.Ask) * 0.5;
            if (referencePrice <= 0)
                return floor;
            double priceDistance = referencePrice * minimumDistance / 100.0;
            return Math.Max(priceDistance / Symbol.PipSize, floor);
        }

        private void ResetDailyRiskIfNeeded()
        {
            if (Server.Time.Date != _riskDate)
                ResetDay();
        }

        private void ResetDay()
        {
            _riskDate = Server.Time.Date;
            _dayStartEquity = Account.Equity;
            _dailyR = 0;
            _dailyLosingR = 0;
            _sessionR = 0;
            _tradesToday = 0;
            _consecutiveLosses = 0;
            _stoppedForRisk = false;
        }

        private void ValidateParameters()
        {
            if (TrendSlowPeriod <= TrendFastPeriod)
                throw new ArgumentException("Trend EMA Slow must be greater than Trend EMA Fast.");
            if (RiskPerTradePercent <= 0 || RiskPerTradePercent > 1.0)
                throw new ArgumentException("Risk Per Trade must be in (0, 1.0].");
            if (TpRMultiple <= 0 || AtrSlMultiplier <= 0)
                throw new ArgumentException("TP R and ATR SL multiplier must be positive.");
            if (FridayForceCloseHourUtc < FridayLastEntryHourUtc)
                throw new ArgumentException("Friday force-close hour cannot be earlier than Friday last-entry hour.");
        }

        private static TimeSpan ParseTime(string value, TimeSpan fallback)
        {
            TimeSpan parsed;
            return TimeSpan.TryParse(value, out parsed) ? parsed : fallback;
        }

        private static bool IsFinitePositive(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value) && value > 0;
        }
    }
}
