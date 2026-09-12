using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum V3RiskMode
    {
        RiskPercent = 0,
        FixedMoney = 1,
        FixedLots = 2
    }

    public enum V3SessionMode
    {
        Off = 0,
        ManualUtc = 1,
        AutoPairLiquidity = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public partial class CumulativeDeltaScalper_FX_Commercial_v3 : Robot
    {
        private const string VersionName = "3.1.0-commercial-hardening-candidate";

        [Parameter("Bot Label", Group = "General", DefaultValue = "CDS_FX_COMMERCIAL_V3")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", Group = "General", DefaultValue = false)]
        public bool DebugLogging { get; set; }

        [Parameter("Summary Logging", Group = "General", DefaultValue = false)]
        public bool SummaryLogging { get; set; }

        [Parameter("Portfolio Single Position", Group = "General", DefaultValue = true)]
        public bool PortfolioSinglePosition { get; set; }

        [Parameter("Validation Universe", Group = "General", DefaultValue = "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY")]
        public string ValidationUniverse { get; set; }

        [Parameter("Use Production Whitelist", Group = "General", DefaultValue = false)]
        public bool UseProductionWhitelist { get; set; }

        [Parameter("Production Whitelist", Group = "General", DefaultValue = "")]
        public string ProductionWhitelist { get; set; }

        [Parameter("Pressure Window", Group = "Signal", DefaultValue = 7, MinValue = 3, MaxValue = 20)]
        public int PressureWindow { get; set; }

        [Parameter("Persistence Lookback", Group = "Signal", DefaultValue = 5, MinValue = 3, MaxValue = 10)]
        public int PersistenceLookback { get; set; }

        [Parameter("Min Directional Bars", Group = "Signal", DefaultValue = 3, MinValue = 2, MaxValue = 8)]
        public int MinDirectionalBars { get; set; }

        [Parameter("Min Avg Pressure", Group = "Signal", DefaultValue = 24.0, MinValue = 5.0, MaxValue = 80.0, Step = 1.0)]
        public double MinAveragePressure { get; set; }

        [Parameter("Min Last Pressure", Group = "Signal", DefaultValue = 30.0, MinValue = 5.0, MaxValue = 100.0, Step = 1.0)]
        public double MinLastPressure { get; set; }

        [Parameter("Structure Lookback", Group = "Signal", DefaultValue = 5, MinValue = 2, MaxValue = 20)]
        public int StructureLookback { get; set; }

        [Parameter("Allow Pullback Continuation", Group = "Signal", DefaultValue = true)]
        public bool AllowPullbackContinuation { get; set; }

        [Parameter("Min Candle Body/Range", Group = "Signal", DefaultValue = 0.32, MinValue = 0.05, MaxValue = 0.90, Step = 0.01)]
        public double MinBodyToRange { get; set; }

        [Parameter("Fast EMA", Group = "Trend", DefaultValue = 20, MinValue = 5, MaxValue = 100)]
        public int FastEmaPeriod { get; set; }

        [Parameter("Slow EMA", Group = "Trend", DefaultValue = 50, MinValue = 10, MaxValue = 250)]
        public int SlowEmaPeriod { get; set; }

        [Parameter("EMA Slope Bars", Group = "Trend", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int EmaSlopeBars { get; set; }

        [Parameter("Require H1 Agreement", Group = "Trend", DefaultValue = true)]
        public bool RequireH1Agreement { get; set; }

        [Parameter("ADX Period", Group = "Trend", DefaultValue = 14, MinValue = 5, MaxValue = 50)]
        public int AdxPeriod { get; set; }

        [Parameter("Min ADX", Group = "Trend", DefaultValue = 18.0, MinValue = 5.0, MaxValue = 60.0, Step = 0.5)]
        public double MinAdx { get; set; }

        [Parameter("ATR Period", Group = "Execution", DefaultValue = 14, MinValue = 5, MaxValue = 100)]
        public int AtrPeriod { get; set; }

        [Parameter("Max Spread Pips", Group = "Execution", DefaultValue = 3.0, MinValue = 0.1, MaxValue = 10.0, Step = 0.1)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Min ATR/Spread", Group = "Execution", DefaultValue = 5.0, MinValue = 1.0, MaxValue = 30.0, Step = 0.25)]
        public double MinAtrToSpreadRatio { get; set; }

        [Parameter("Min Effective RR", Group = "Execution", DefaultValue = 1.25, MinValue = 0.5, MaxValue = 5.0, Step = 0.05)]
        public double MinEffectiveRewardRisk { get; set; }

        [Parameter("Estimated Commission / Million USD", Group = "Execution", DefaultValue = 35.0, MinValue = 0.0, MaxValue = 200.0, Step = 1.0)]
        public double CommissionPerMillionUsd { get; set; }

        [Parameter("Max Margin Use % Free", Group = "Execution", DefaultValue = 30.0, MinValue = 1.0, MaxValue = 100.0, Step = 1.0)]
        public double MaxMarginUsePercentOfFree { get; set; }

        [Parameter("Session Mode", Group = "Session", DefaultValue = V3SessionMode.AutoPairLiquidity)]
        public V3SessionMode SessionMode { get; set; }

        [Parameter("Manual Start Hour UTC", Group = "Session", DefaultValue = 6, MinValue = 0, MaxValue = 23)]
        public int ManualStartHour { get; set; }

        [Parameter("Manual End Hour UTC", Group = "Session", DefaultValue = 20, MinValue = 0, MaxValue = 23)]
        public int ManualEndHour { get; set; }

        [Parameter("Rollover Blackout", Group = "Session", DefaultValue = true)]
        public bool UseRolloverBlackout { get; set; }

        [Parameter("Risk Mode", Group = "Risk", DefaultValue = V3RiskMode.RiskPercent)]
        public V3RiskMode RiskMode { get; set; }

        [Parameter("Risk % / Trade", Group = "Risk", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 5.0, Step = 0.05)]
        public double RiskPercentPerTrade { get; set; }

        [Parameter("Fixed Money Risk", Group = "Risk", DefaultValue = 0.50, MinValue = 0.01, MaxValue = 1000.0, Step = 0.01)]
        public double FixedMoneyRisk { get; set; }

        [Parameter("Fixed Lot Size", Group = "Risk", DefaultValue = 0.01, MinValue = 0.01, MaxValue = 100.0, Step = 0.01)]
        public double FixedLotSize { get; set; }

        [Parameter("Max Lot Size", Group = "Risk", DefaultValue = 0.05, MinValue = 0.01, MaxValue = 100.0, Step = 0.01)]
        public double MaxLotSize { get; set; }

        [Parameter("Hard Risk Cap % Equity", Group = "Risk", DefaultValue = 1.0, MinValue = 0.10, MaxValue = 5.0, Step = 0.05)]
        public double HardRiskCapPercentOfEquity { get; set; }

        [Parameter("Risk Audit Tolerance %", Group = "Risk", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 10.0, Step = 0.5)]
        public double RiskAuditTolerancePercent { get; set; }

        [Parameter("SL ATR Mult", Group = "Risk", DefaultValue = 1.20, MinValue = 0.3, MaxValue = 5.0, Step = 0.05)]
        public double StopAtrMultiplier { get; set; }

        [Parameter("Target RR", Group = "Risk", DefaultValue = 1.80, MinValue = 0.5, MaxValue = 6.0, Step = 0.05)]
        public double TargetRewardRisk { get; set; }

        [Parameter("Broker Distance Buffer Pips", Group = "Risk", DefaultValue = 0.3, MinValue = 0.0, MaxValue = 5.0, Step = 0.1)]
        public double BrokerDistanceBufferPips { get; set; }

        [Parameter("Max Trades / Day", Group = "Protection", DefaultValue = 4, MinValue = 1, MaxValue = 30)]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Max Daily Loss %", Group = "Protection", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 20.0, Step = 0.1)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Consecutive Losses", Group = "Protection", DefaultValue = 2, MinValue = 1, MaxValue = 10)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Cooldown Bars", Group = "Protection", DefaultValue = 3, MinValue = 0, MaxValue = 50)]
        public int CooldownBars { get; set; }

        [Parameter("Loss Cooldown Minutes", Group = "Protection", DefaultValue = 30, MinValue = 0, MaxValue = 1440)]
        public int LossCooldownMinutes { get; set; }

        [Parameter("Min Hold Bars Before Adverse Exit", Group = "Exit", DefaultValue = 3, MinValue = 1, MaxValue = 20)]
        public int MinHoldBarsBeforeAdverseExit { get; set; }

        [Parameter("Max Trade Bars", Group = "Exit", DefaultValue = 10, MinValue = 3, MaxValue = 50)]
        public int MaxTradeBars { get; set; }

        [Parameter("Stagnation Bars", Group = "Exit", DefaultValue = 5, MinValue = 2, MaxValue = 20)]
        public int StagnationBars { get; set; }

        [Parameter("Min MFE R To Avoid Stagnation Exit", Group = "Exit", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 2.0, Step = 0.05)]
        public double MinMfeRForContinuation { get; set; }

        [Parameter("Adverse Persistence Bars", Group = "Exit", DefaultValue = 2, MinValue = 1, MaxValue = 5)]
        public int AdversePersistenceBars { get; set; }

        [Parameter("Adverse Pressure Threshold", Group = "Exit", DefaultValue = 34.0, MinValue = 5.0, MaxValue = 100.0, Step = 1.0)]
        public double AdversePressureThreshold { get; set; }

        [Parameter("Use Breakeven", Group = "Exit", DefaultValue = true)]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven Trigger R", Group = "Exit", DefaultValue = 1.05, MinValue = 0.2, MaxValue = 5.0, Step = 0.05)]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Cost Buffer Mult", Group = "Exit", DefaultValue = 1.20, MinValue = 1.0, MaxValue = 3.0, Step = 0.05)]
        public double BreakevenCostBufferMultiplier { get; set; }

        [Parameter("Use ATR Trailing", Group = "Exit", DefaultValue = true)]
        public bool UseAtrTrailing { get; set; }

        [Parameter("Trailing Start R", Group = "Exit", DefaultValue = 1.50, MinValue = 0.5, MaxValue = 5.0, Step = 0.05)]
        public double TrailingStartR { get; set; }

        [Parameter("Trailing ATR Mult", Group = "Exit", DefaultValue = 1.20, MinValue = 0.2, MaxValue = 5.0, Step = 0.05)]
        public double TrailingAtrMultiplier { get; set; }

        private AverageTrueRange _atr;
        private DirectionalMovementSystem _dms;
        private ExponentialMovingAverage _fastEma;
        private ExponentialMovingAverage _slowEma;
        private Bars _m15Bars;
        private Bars _h1Bars;
        private ExponentialMovingAverage _m15Fast;
        private ExponentialMovingAverage _m15Slow;
        private ExponentialMovingAverage _h1Fast;
        private ExponentialMovingAverage _h1Slow;

        private readonly List<double> _pressureHistory = new List<double>();
        private readonly Dictionary<long, TradeState> _tradeStates = new Dictionary<long, TradeState>();
        private DateTime _tickBarTime;
        private double _lastBid;
        private int _upTicks;
        private int _downTicks;
        private int _flatTicks;
        private double _lastCompletedTickPressure;
        private int _lastCompletedTickSamples;
        private DateTime _currentDay;
        // Daily realised-loss protection intentionally uses start-of-day balance so restart recovery
        // can reproduce the same baseline from account history. Per-trade risk still uses live equity.
        private double _dayStartEquity;
        private double _dailyRealized;
        private int _tradesToday;
        private int _consecutiveLosses;
        private int _lastEntryBarIndex = -1000000;
        private DateTime _nextTradeTime = DateTime.MinValue;
        private int _signalCount;
        private int _entryCount;
        private int _riskRejectCount;
        private int _costRejectCount;
        private int _filterRejectCount;

        protected override void OnStart()
        {
            if (!IsValidationSymbolAllowed())
            {
                Print("[V3 BLOCK] symbol not allowed: {0}", SymbolName);
                Stop();
                return;
            }

            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
            _dms = Indicators.DirectionalMovementSystem(AdxPeriod);
            _fastEma = Indicators.ExponentialMovingAverage(Bars.ClosePrices, FastEmaPeriod);
            _slowEma = Indicators.ExponentialMovingAverage(Bars.ClosePrices, SlowEmaPeriod);

            _m15Bars = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1Bars = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _m15Fast = Indicators.ExponentialMovingAverage(_m15Bars.ClosePrices, FastEmaPeriod);
            _m15Slow = Indicators.ExponentialMovingAverage(_m15Bars.ClosePrices, SlowEmaPeriod);
            _h1Fast = Indicators.ExponentialMovingAverage(_h1Bars.ClosePrices, FastEmaPeriod);
            _h1Slow = Indicators.ExponentialMovingAverage(_h1Bars.ClosePrices, SlowEmaPeriod);

            _currentDay = Server.Time.Date;
            _dayStartEquity = Account.Balance;
            if (Bars.Count > 0)
                _tickBarTime = Bars.OpenTimes.LastValue;

            // Recover before subscribing/processing new trade events so a restart cannot briefly run
            // with zeroed daily-loss, trade-count or consecutive-loss state.
            EnsureDailyStateRecovered();
            Positions.Closed += OnPositionClosed;
            Print("[V3 START] {0} symbol={1} tf={2} equity={3:F2} minVol={4} step={5}", VersionName, SymbolName, TimeFrame, Account.Equity, Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsStep);
        }

        protected override void OnTick()
        {
            RollTradingDayIfNeeded();
            CaptureTickPressure();
            ManageIntrabarProtection();
        }

        protected override void OnBar()
        {
            RollTradingDayIfNeeded();
            FinalizeTickBarIfNeeded();

            if (Bars.Count < Math.Max(100, SlowEmaPeriod + EmaSlopeBars + StructureLookback + 10))
                return;

            var closedIndex = Bars.Count - 2;
            if (closedIndex < 2)
                return;

            var barPressure = ComputeAndStorePressure(closedIndex);
            ManageClosedBarExit(closedIndex, barPressure);

            if (HasBotPosition())
                return;
            if (!PassGlobalEntryGuards(closedIndex))
                return;

            var candidate = BuildEntryCandidate(closedIndex, barPressure);
            if (!candidate.IsValid)
                return;

            _signalCount++;
            TryEnter(candidate, closedIndex);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            if (SummaryLogging)
                Print("[V3 SUMMARY] signals={0} entries={1} riskReject={2} costReject={3} filterReject={4} dailyPnL={5:F2}", _signalCount, _entryCount, _riskRejectCount, _costRejectCount, _filterRejectCount, _dailyRealized);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var position = args.Position;
            if (position == null || position.Label != TradeLabel)
                return;
            if (!PortfolioSinglePosition && position.SymbolName != SymbolName)
                return;

            RollTradingDayIfNeeded();
            _dailyRealized += position.NetProfit;
            if (position.NetProfit < 0)
            {
                _consecutiveLosses++;
                if (LossCooldownMinutes > 0)
                    _nextTradeTime = Server.Time.AddMinutes(LossCooldownMinutes);
            }
            else if (position.NetProfit > 0)
            {
                _consecutiveLosses = 0;
            }

            _tradeStates.Remove(position.Id);
            DebugLog("CLOSE id={0} symbol={1} net={2:F2} daily={3:F2} consecutiveLosses={4}", position.Id, position.SymbolName, position.NetProfit, _dailyRealized, _consecutiveLosses);
        }

        private bool PassGlobalEntryGuards(int closedIndex)
        {
            if (!Symbol.IsTradingEnabled)
                return RejectFilter("trading_disabled");
            if (!IsSupportedTimeFrame())
                return RejectFilter("unsupported_timeframe");
            if (!IsWithinTradingSession(Server.Time))
                return RejectFilter("session");
            if (UseRolloverBlackout && IsRolloverBlackout(Server.Time))
                return RejectFilter("rollover");
            if (Server.Time < _nextTradeTime)
                return RejectFilter("loss_cooldown");
            if (_tradesToday >= MaxTradesPerDay)
                return RejectFilter("daily_trade_cap");
            if (_consecutiveLosses >= MaxConsecutiveLosses)
                return RejectFilter("consecutive_loss_cap");
            if (_dailyRealized <= -Math.Abs(_dayStartEquity * MaxDailyLossPercent / 100.0))
                return RejectFilter("daily_loss_cap");
            if (closedIndex - _lastEntryBarIndex < CooldownBars)
                return RejectFilter("bar_cooldown");
            if (PortfolioSinglePosition && Positions.Any(p => p.Label == TradeLabel))
                return RejectFilter("portfolio_position_exists");
            return true;
        }

        private bool HasBotPosition()
        {
            return Positions.Any(p => p.Label == TradeLabel && p.SymbolName == SymbolName);
        }

        private void RollTradingDayIfNeeded()
        {
            var today = Server.Time.Date;
            if (today == _currentDay)
                return;

            if (SummaryLogging)
                Print("[V3 DAY] {0:yyyy-MM-dd} realized={1:F2} trades={2}", _currentDay, _dailyRealized, _tradesToday);

            _currentDay = today;
            _dayStartEquity = Account.Balance;
            _dailyRealized = 0;
            _tradesToday = 0;
            _consecutiveLosses = 0;
            _nextTradeTime = DateTime.MinValue;
            _dailyStateRecovered = false;
        }

        private void CaptureTickPressure()
        {
            if (Bars.Count == 0)
                return;

            FinalizeTickBarIfNeeded();
            var bid = Symbol.Bid;
            if (_lastBid > 0)
            {
                if (bid > _lastBid)
                    _upTicks++;
                else if (bid < _lastBid)
                    _downTicks++;
                else
                    _flatTicks++;
            }
            _lastBid = bid;
        }

        private void FinalizeTickBarIfNeeded()
        {
            if (Bars.Count == 0)
                return;

            var liveBarTime = Bars.OpenTimes.LastValue;
            if (_tickBarTime == default(DateTime))
            {
                _tickBarTime = liveBarTime;
                return;
            }
            if (liveBarTime == _tickBarTime)
                return;

            var directional = _upTicks + _downTicks;
            _lastCompletedTickSamples = directional + _flatTicks;
            _lastCompletedTickPressure = directional <= 0 ? 0 : 100.0 * (_upTicks - _downTicks) / directional;
            _upTicks = 0;
            _downTicks = 0;
            _flatTicks = 0;
            _tickBarTime = liveBarTime;
        }

        private bool RejectFilter(string reason)
        {
            _filterRejectCount++;
            DebugLog("BLOCK {0}", reason);
            return false;
        }

        private void DebugLog(string format, params object[] args)
        {
            if (DebugLogging)
                Print("[V3] " + format, args);
        }
    }
}
