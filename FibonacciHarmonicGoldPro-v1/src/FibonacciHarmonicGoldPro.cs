using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(
        TimeZone = TimeZones.UTC,
        AccessRights = AccessRights.None,
        DefaultSymbolName = "XAUUSD",
        DefaultTimeFrame = "Minute15")]
    public class FibonacciHarmonicGoldPro : Robot
    {
        // ============================================================
        // Commercial profile
        // ============================================================
        [Parameter("Bot Label", DefaultValue = "FHGP_XAUUSD", Group = "01 General")]
        public string BotLabel { get; set; }

        [Parameter("Trading Enabled", DefaultValue = true, Group = "01 General")]
        public bool TradingEnabled { get; set; }

        [Parameter("XAUUSD Only", DefaultValue = true, Group = "01 General")]
        public bool XauUsdOnly { get; set; }

        [Parameter("Verbose Logging", DefaultValue = true, Group = "01 General")]
        public bool VerboseLogging { get; set; }

        [Parameter("Show Chart Marks", DefaultValue = true, Group = "01 General")]
        public bool ShowChartMarks { get; set; }

        // ============================================================
        // Harmonic engine
        // ============================================================
        [Parameter("Pivot Strength", DefaultValue = 3, MinValue = 2, MaxValue = 12, Group = "02 Harmonic Engine")]
        public int PivotStrength { get; set; }

        [Parameter("Pivot Lookback Bars", DefaultValue = 500, MinValue = 100, MaxValue = 3000, Group = "02 Harmonic Engine")]
        public int PivotLookbackBars { get; set; }

        [Parameter("Ratio Tolerance %", DefaultValue = 7.0, MinValue = 1.0, MaxValue = 20.0, Step = 0.5, Group = "02 Harmonic Engine")]
        public double RatioTolerancePct { get; set; }

        [Parameter("Minimum Pattern Score", DefaultValue = 78.0, MinValue = 50.0, MaxValue = 100.0, Step = 1.0, Group = "02 Harmonic Engine")]
        public double MinimumPatternScore { get; set; }

        [Parameter("M15 Max Signal Age", DefaultValue = 8, MinValue = 1, MaxValue = 50, Group = "02 Harmonic Engine")]
        public int M15MaxSignalAgeBars { get; set; }

        [Parameter("H1 Max Signal Age", DefaultValue = 8, MinValue = 1, MaxValue = 50, Group = "02 Harmonic Engine")]
        public int H1MaxSignalAgeBars { get; set; }

        [Parameter("H4 Max Signal Age", DefaultValue = 6, MinValue = 1, MaxValue = 30, Group = "02 Harmonic Engine")]
        public int H4MaxSignalAgeBars { get; set; }

        [Parameter("Enable Gartley", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableGartley { get; set; }

        [Parameter("Enable Bat", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableBat { get; set; }

        [Parameter("Enable Alternate Bat", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableAlternateBat { get; set; }

        [Parameter("Enable Butterfly", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableButterfly { get; set; }

        [Parameter("Enable Crab", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableCrab { get; set; }

        [Parameter("Enable Deep Crab", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableDeepCrab { get; set; }

        [Parameter("Enable Cypher", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableCypher { get; set; }

        [Parameter("Enable Shark", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableShark { get; set; }

        [Parameter("Enable AB=CD", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableAbCd { get; set; }

        [Parameter("Enable 5-0", DefaultValue = true, Group = "03 Pattern Set")]
        public bool EnableFiveZero { get; set; }

        // ============================================================
        // Multi-timeframe pattern-only confluence
        // ============================================================
        [Parameter("Minimum Aligned Frames", DefaultValue = 2, MinValue = 1, MaxValue = 3, Group = "04 MTF Confluence")]
        public int MinimumAlignedFrames { get; set; }

        [Parameter("Block Any HTF Conflict", DefaultValue = true, Group = "04 MTF Confluence")]
        public bool BlockAnyHigherTimeframeConflict { get; set; }

        [Parameter("Minimum Confluence Score", DefaultValue = 80.0, MinValue = 50.0, MaxValue = 100.0, Group = "04 MTF Confluence")]
        public double MinimumConfluenceScore { get; set; }

        [Parameter("M15 Weight", DefaultValue = 0.50, MinValue = 0.0, MaxValue = 1.0, Step = 0.05, Group = "04 MTF Confluence")]
        public double M15Weight { get; set; }

        [Parameter("H1 Weight", DefaultValue = 0.30, MinValue = 0.0, MaxValue = 1.0, Step = 0.05, Group = "04 MTF Confluence")]
        public double H1Weight { get; set; }

        [Parameter("H4 Weight", DefaultValue = 0.20, MinValue = 0.0, MaxValue = 1.0, Step = 0.05, Group = "04 MTF Confluence")]
        public double H4Weight { get; set; }

        // ============================================================
        // Session controls - UTC for deterministic Cloud execution
        // ============================================================
        [Parameter("Session Start Hour UTC", DefaultValue = 7, MinValue = 0, MaxValue = 23, Group = "05 Session")]
        public int SessionStartHourUtc { get; set; }

        [Parameter("Session Start Minute", DefaultValue = 0, MinValue = 0, MaxValue = 59, Group = "05 Session")]
        public int SessionStartMinuteUtc { get; set; }

        [Parameter("Session End Hour UTC", DefaultValue = 21, MinValue = 0, MaxValue = 23, Group = "05 Session")]
        public int SessionEndHourUtc { get; set; }

        [Parameter("Session End Minute", DefaultValue = 0, MinValue = 0, MaxValue = 59, Group = "05 Session")]
        public int SessionEndMinuteUtc { get; set; }

        [Parameter("Open Freeze Minutes", DefaultValue = 15, MinValue = 0, MaxValue = 120, Group = "05 Session")]
        public int OpenFreezeMinutes { get; set; }

        [Parameter("Close Freeze Minutes", DefaultValue = 15, MinValue = 0, MaxValue = 120, Group = "05 Session")]
        public int CloseFreezeMinutes { get; set; }

        [Parameter("Close Position At Session End", DefaultValue = false, Group = "05 Session")]
        public bool CloseAtSessionEnd { get; set; }

        [Parameter("Manual Blackouts UTC", DefaultValue = "", Group = "05 Session")]
        public string ManualBlackoutWindowsUtc { get; set; }

        // ============================================================
        // Execution / cost controls
        // ============================================================
        [Parameter("Max Spread (pips)", DefaultValue = 80.0, MinValue = 0.0, Group = "06 Execution")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Round-turn Commission / $1M", DefaultValue = 70.0, MinValue = 0.0, Group = "06 Execution")]
        public double EstimatedRoundTurnCommissionPerMillion { get; set; }

        [Parameter("Max Cost / Risk %", DefaultValue = 18.0, MinValue = 0.0, MaxValue = 100.0, Group = "06 Execution")]
        public double MaxCostToRiskPct { get; set; }

        [Parameter("Free Margin Reserve %", DefaultValue = 25.0, MinValue = 0.0, MaxValue = 95.0, Group = "06 Execution")]
        public double FreeMarginReservePct { get; set; }

        [Parameter("Respect All Symbol Positions", DefaultValue = true, Group = "06 Execution")]
        public bool RespectAllSymbolPositions { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 4, MinValue = 1, MaxValue = 30, Group = "06 Execution")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Cooldown Minutes", DefaultValue = 60, MinValue = 0, MaxValue = 1440, Group = "06 Execution")]
        public int CooldownMinutes { get; set; }

        [Parameter("Entry Mode", DefaultValue = EntryExecutionMode.Market, Group = "06 Execution")]
        public EntryExecutionMode EntryMode { get; set; }

        [Parameter("Limit Pullback % of CD", DefaultValue = 8.0, MinValue = 0.0, MaxValue = 50.0, Step = 0.5, Group = "06 Execution")]
        public double LimitPullbackCdPct { get; set; }

        [Parameter("Limit Expiry Minutes", DefaultValue = 90, MinValue = 5, MaxValue = 1440, Group = "06 Execution")]
        public int LimitExpiryMinutes { get; set; }

        // ============================================================
        // Position sizing
        // ============================================================
        [Parameter("Use Risk % Sizing", DefaultValue = true, Group = "07 Position Sizing")]
        public bool UseRiskPercentSizing { get; set; }

        [Parameter("Risk % Per Trade", DefaultValue = 1.0, MinValue = 0.05, MaxValue = 10.0, Step = 0.05, Group = "07 Position Sizing")]
        public double RiskPercentPerTrade { get; set; }

        [Parameter("Monthly Compounding Anchor", DefaultValue = true, Group = "07 Position Sizing")]
        public bool UseMonthlyCompoundingAnchor { get; set; }

        [Parameter("Fixed Lots", DefaultValue = 0.01, MinValue = 0.0, Group = "07 Position Sizing")]
        public double FixedLots { get; set; }

        [Parameter("Max Lots (0=Broker Max)", DefaultValue = 0.0, MinValue = 0.0, Group = "07 Position Sizing")]
        public double MaxLots { get; set; }

        // ============================================================
        // Pattern-derived SL / Fibonacci target ladder
        // ============================================================
        [Parameter("Stop Buffer % of XA", DefaultValue = 5.0, MinValue = 0.5, MaxValue = 30.0, Step = 0.5, Group = "08 Protection")]
        public double StopBufferXaPct { get; set; }

        [Parameter("Minimum Stop Buffer Pips", DefaultValue = 30.0, MinValue = 0.0, Group = "08 Protection")]
        public double MinimumStopBufferPips { get; set; }

        [Parameter("Minimum Final R:R", DefaultValue = 3.0, MinValue = 1.0, MaxValue = 10.0, Step = 0.1, Group = "08 Protection")]
        public double MinimumFinalRiskReward { get; set; }

        [Parameter("TP1 CD Retracement", DefaultValue = 0.382, MinValue = 0.1, MaxValue = 1.0, Step = 0.001, Group = "08 Protection")]
        public double Tp1CdRatio { get; set; }

        [Parameter("TP2 CD Retracement", DefaultValue = 0.618, MinValue = 0.1, MaxValue = 1.5, Step = 0.001, Group = "08 Protection")]
        public double Tp2CdRatio { get; set; }

        [Parameter("Final CD Multiple", DefaultValue = 1.272, MinValue = 0.5, MaxValue = 3.0, Step = 0.001, Group = "08 Protection")]
        public double FinalCdMultiple { get; set; }

        [Parameter("TP1 Close %", DefaultValue = 33.0, MinValue = 0.0, MaxValue = 90.0, Group = "08 Protection")]
        public double Tp1ClosePct { get; set; }

        [Parameter("TP2 Close %", DefaultValue = 33.0, MinValue = 0.0, MaxValue = 90.0, Group = "08 Protection")]
        public double Tp2ClosePct { get; set; }

        [Parameter("BreakEven + Pips", DefaultValue = 10.0, MinValue = 0.0, Group = "08 Protection")]
        public double BreakEvenPlusPips { get; set; }

        [Parameter("Trail Lookback M15 Bars", DefaultValue = 5, MinValue = 2, MaxValue = 30, Group = "08 Protection")]
        public int TrailLookbackBars { get; set; }

        [Parameter("Trail Buffer Pips", DefaultValue = 20.0, MinValue = 0.0, Group = "08 Protection")]
        public double TrailBufferPips { get; set; }

        [Parameter("Trail Minimum Step Pips", DefaultValue = 10.0, MinValue = 0.0, Group = "08 Protection")]
        public double TrailMinimumStepPips { get; set; }

        // ============================================================
        // Portfolio-level circuit breakers
        // ============================================================
        [Parameter("Daily Loss Limit %", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 50.0, Group = "09 Risk Circuit Breakers")]
        public double DailyLossLimitPct { get; set; }

        [Parameter("Weekly Loss Limit %", DefaultValue = 10.0, MinValue = 0.0, MaxValue = 70.0, Group = "09 Risk Circuit Breakers")]
        public double WeeklyLossLimitPct { get; set; }

        [Parameter("Maximum Equity Drawdown %", DefaultValue = 20.0, MinValue = 0.0, MaxValue = 90.0, Group = "09 Risk Circuit Breakers")]
        public double MaximumDrawdownPct { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 4, MinValue = 0, MaxValue = 20, Group = "09 Risk Circuit Breakers")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Close On Hard Halt", DefaultValue = true, Group = "09 Risk Circuit Breakers")]
        public bool CloseOnHardHalt { get; set; }

        // ============================================================
        // Internal state
        // ============================================================
        private Bars _m15;
        private Bars _h1;
        private Bars _h4;
        private DateTime _lastProcessedM15Bar = DateTime.MinValue;
        private DateTime _lastExitTime = DateTime.MinValue;
        private string _lastTradedSignalKey = string.Empty;
        private int _dailyTrades;
        private int _consecutiveLosses;
        private DateTime _dayAnchor;
        private DateTime _weekAnchor;
        private double _dayStartEquity;
        private double _weekStartEquity;
        private double _peakEquity;
        private int _monthAnchorKey;
        private double _monthRiskEquity;
        private bool _hardHalt;
        private string _hardHaltReason = string.Empty;
        private readonly List<BlackoutWindow> _blackouts = new List<BlackoutWindow>();
        private readonly Dictionary<int, PositionPlan> _plans = new Dictionary<int, PositionPlan>();
        private readonly Dictionary<int, PendingPlan> _pendingPlans = new Dictionary<int, PendingPlan>();

        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _h4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);

            _dayAnchor = Server.Time.Date;
            _weekAnchor = StartOfWeek(Server.Time.Date);
            _dayStartEquity = Account.Equity;
            _weekStartEquity = Account.Equity;
            _peakEquity = Account.Equity;
            _monthAnchorKey = Server.Time.Year * 100 + Server.Time.Month;
            _monthRiskEquity = Account.Equity;

            ParseBlackouts();
            Positions.Closed += OnPositionClosed;
            PendingOrders.Filled += OnPendingOrderFilled;
            PendingOrders.Cancelled += OnPendingOrderCancelled;

            if (XauUsdOnly && !LooksLikeGold(SymbolName))
                Print("[START BLOCK] XAUUSD Only=true, current symbol={0}. Trading will remain blocked.", SymbolName);

            foreach (var position in Positions.FindAll(BotLabel, SymbolName))
                EnsurePlan(position);

            Print("[START] Fibonacci Harmonic Gold Pro v1.0.0 | Symbol={0} | M15/H1/H4 pattern-only confluence | AccessRights=None", SymbolName);
            Print("[RISK] Equity={0:F2} {1} | Risk/Trade={2:F2}% | Daily={3:F1}% | Weekly={4:F1}% | MaxDD={5:F1}%",
                Account.Equity, Account.Asset.Name, RiskPercentPerTrade, DailyLossLimitPct, WeeklyLossLimitPct, MaximumDrawdownPct);
        }

        protected override void OnTick()
        {
            RefreshRiskAnchors();
            UpdatePeakAndCircuitBreakers();
            ManageOpenPositions();

            if (_m15 == null || _m15.Count < Math.Max(50, PivotStrength * 4 + 20))
                return;

            int lastClosed = _m15.Count - 2;
            if (lastClosed < 0)
                return;

            DateTime lastClosedTime = _m15.OpenTimes[lastClosed];
            if (lastClosedTime == _lastProcessedM15Bar)
                return;

            _lastProcessedM15Bar = lastClosedTime;
            EvaluateNewM15Signal(lastClosedTime);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            PendingOrders.Filled -= OnPendingOrderFilled;
            PendingOrders.Cancelled -= OnPendingOrderCancelled;
            Print("[STOP] Fibonacci Harmonic Gold Pro stopped. HardHalt={0} Reason={1}", _hardHalt, _hardHaltReason);
        }

        private void EvaluateNewM15Signal(DateTime barTime)
        {
            if (!TradingEnabled)
                return;

            if (XauUsdOnly && !LooksLikeGold(SymbolName))
                return;

            string riskBlock;
            if (IsEntryBlockedByRisk(out riskBlock))
            {
                Log("[BLOCK:RISK] " + riskBlock);
                return;
            }

            if (!IsInsideTradingSession(Server.Time))
            {
                Log("[BLOCK:SESSION] " + Server.Time.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture) + " UTC");
                return;
            }

            if (IsManualBlackout(Server.Time.TimeOfDay))
            {
                Log("[BLOCK:BLACKOUT] Manual UTC blackout window");
                return;
            }

            if (_dailyTrades >= MaxTradesPerDay)
            {
                Log("[BLOCK:DAILY-COUNT] " + _dailyTrades + "/" + MaxTradesPerDay);
                return;
            }

            if (_lastExitTime != DateTime.MinValue && (Server.Time - _lastExitTime).TotalMinutes < CooldownMinutes)
            {
                Log("[BLOCK:COOLDOWN] Remaining=" + Math.Max(0, CooldownMinutes - (Server.Time - _lastExitTime).TotalMinutes).ToString("F1") + "m");
                return;
            }

            if (HasBlockingPosition())
            {
                Log("[BLOCK:POSITION] Existing " + SymbolName + " position detected; duplicate/hedge entry forbidden.");
                return;
            }

            if (PendingOrders.Any(o => o.SymbolName == SymbolName && o.Label == BotLabel))
            {
                Log("[BLOCK:PENDING] Existing FHGP pending order detected.");
                return;
            }

            double spreadPips = CurrentSpreadPips();
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
            {
                Log("[BLOCK:SPREAD] " + spreadPips.ToString("F1") + "p > " + MaxSpreadPips.ToString("F1") + "p");
                return;
            }

            HarmonicSignal m15 = FindBestPattern(_m15, "M15", M15MaxSignalAgeBars);
            if (m15 == null)
            {
                Log("[SCAN] No qualified M15 harmonic completion.");
                return;
            }

            string signalKey = m15.Kind + "|" + m15.Direction + "|" + m15.D.Time.Ticks;
            if (signalKey == _lastTradedSignalKey)
            {
                Log("[BLOCK:DUPLICATE] " + signalKey);
                return;
            }

            HarmonicSignal h1 = FindBestPattern(_h1, "H1", H1MaxSignalAgeBars);
            HarmonicSignal h4 = FindBestPattern(_h4, "H4", H4MaxSignalAgeBars);

            int alignedFrames = 1;
            bool conflict = false;
            double weightedScore = m15.Score * M15Weight;
            double totalWeight = M15Weight;

            EvaluateHigherTimeframe(m15, h1, H1Weight, ref alignedFrames, ref conflict, ref weightedScore, ref totalWeight);
            EvaluateHigherTimeframe(m15, h4, H4Weight, ref alignedFrames, ref conflict, ref weightedScore, ref totalWeight);

            double confluenceScore = totalWeight > 0 ? weightedScore / totalWeight : m15.Score;

            if (BlockAnyHigherTimeframeConflict && conflict)
            {
                Log("[BLOCK:MTF-CONFLICT] M15=" + Describe(m15) + " H1=" + Describe(h1) + " H4=" + Describe(h4));
                return;
            }

            if (alignedFrames < MinimumAlignedFrames)
            {
                Log("[BLOCK:MTF-ALIGN] aligned=" + alignedFrames + "/" + MinimumAlignedFrames + " H1=" + Describe(h1) + " H4=" + Describe(h4));
                return;
            }

            if (confluenceScore < MinimumConfluenceScore)
            {
                Log("[BLOCK:MTF-SCORE] " + confluenceScore.ToString("F1") + " < " + MinimumConfluenceScore.ToString("F1"));
                return;
            }

            TradeType tradeType = m15.Direction == SignalDirection.Bullish ? TradeType.Buy : TradeType.Sell;
            double entry = tradeType == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            double direction = tradeType == TradeType.Buy ? 1.0 : -1.0;

            double stopBuffer = Math.Max(m15.XaLength * StopBufferXaPct / 100.0, MinimumStopBufferPips * Symbol.PipSize);
            double stopPrice = m15.D.Price - direction * stopBuffer;
            double stopRiskPrice = Math.Abs(entry - stopPrice);

            if ((tradeType == TradeType.Buy && stopPrice >= entry) || (tradeType == TradeType.Sell && stopPrice <= entry))
            {
                Log("[BLOCK:SL-GEOMETRY] Pattern invalidation stop is on wrong side of entry.");
                return;
            }

            double stopPips = stopRiskPrice / Symbol.PipSize;
            double minStopPips = BrokerMinimumDistancePips(true, entry);
            if (stopPips < minStopPips)
                stopPips = minStopPips * 1.05;

            double tp1 = m15.D.Price + direction * m15.CdLength * Tp1CdRatio;
            double tp2 = m15.D.Price + direction * m15.CdLength * Tp2CdRatio;
            double finalTp = m15.D.Price + direction * m15.CdLength * FinalCdMultiple;

            if (!IsAheadOfEntry(tradeType, tp1, entry) || !IsAheadOfEntry(tradeType, tp2, entry) || !IsAheadOfEntry(tradeType, finalTp, entry))
            {
                Log("[BLOCK:TARGET-GEOMETRY] Price has already moved through one or more Fibonacci targets.");
                return;
            }

            double finalRewardPrice = Math.Abs(finalTp - entry);
            double actualRiskPrice = stopPips * Symbol.PipSize;
            double finalRR = actualRiskPrice > 0 ? finalRewardPrice / actualRiskPrice : 0;

            if (finalRR < MinimumFinalRiskReward)
            {
                Log("[BLOCK:RR] Pattern final R:R=" + finalRR.ToString("F2") + " < " + MinimumFinalRiskReward.ToString("F2"));
                return;
            }

            double takeProfitPips = finalRewardPrice / Symbol.PipSize;
            double minTpPips = BrokerMinimumDistancePips(false, entry);
            if (takeProfitPips < minTpPips)
            {
                Log("[BLOCK:TP-DISTANCE] Final target is inside broker minimum TP distance.");
                return;
            }

            double volume = CalculateVolume(stopPips);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                Log("[BLOCK:VOLUME] Calculated volume below broker minimum.");
                return;
            }

            double estimatedRisk = stopPips * Symbol.PipValue * volume;
            double spreadCost = spreadPips * Symbol.PipValue * volume;
            double notionalUsdApprox = volume * entry;
            double commissionCost = Math.Abs(notionalUsdApprox) / 1000000.0 * EstimatedRoundTurnCommissionPerMillion;
            double totalCost = spreadCost + commissionCost;
            double costToRiskPct = estimatedRisk > 0 ? totalCost / estimatedRisk * 100.0 : 999.0;

            if (MaxCostToRiskPct > 0 && costToRiskPct > MaxCostToRiskPct)
            {
                Log("[BLOCK:COST] Estimated spread+commission/risk=" + costToRiskPct.ToString("F1") + "%");
                return;
            }

            double estimatedMargin = Symbol.GetEstimatedMargin(tradeType, volume);
            double spendableMargin = Account.FreeMargin * Math.Max(0.0, 1.0 - FreeMarginReservePct / 100.0);
            if (estimatedMargin > spendableMargin)
            {
                Log("[BLOCK:MARGIN] Required=" + estimatedMargin.ToString("F2") + " > allowed=" + spendableMargin.ToString("F2"));
                return;
            }

            string comment = "FHGP|" + m15.Kind + "|" + m15.Direction + "|S" + m15.Score.ToString("F0", CultureInfo.InvariantCulture);

            if (EntryMode == EntryExecutionMode.LimitPullback)
            {
                double pullback = m15.CdLength * LimitPullbackCdPct / 100.0;
                double limitPrice = tradeType == TradeType.Buy ? entry - pullback : entry + pullback;

                bool validLimitSide = tradeType == TradeType.Buy ? limitPrice < Symbol.Ask : limitPrice > Symbol.Bid;
                if (!validLimitSide)
                {
                    Log("[BLOCK:LIMIT] Calculated limit price is not on the valid limit-order side.");
                    return;
                }

                double limitStopPips = Math.Abs(limitPrice - stopPrice) / Symbol.PipSize;
                double limitTpPips = Math.Abs(finalTp - limitPrice) / Symbol.PipSize;
                if (limitStopPips <= 0 || limitTpPips <= 0 || limitTpPips / limitStopPips < MinimumFinalRiskReward)
                {
                    Log("[BLOCK:LIMIT-RR] Pullback limit entry failed final R:R gate.");
                    return;
                }

                double limitVolume = CalculateVolume(limitStopPips);
                if (limitVolume < Symbol.VolumeInUnitsMin)
                {
                    Log("[BLOCK:LIMIT-VOLUME] Calculated volume below broker minimum.");
                    return;
                }

                DateTime expiry = Server.Time.AddMinutes(LimitExpiryMinutes);
                TradeResult pendingResult = PlaceLimitOrder(
                    tradeType,
                    SymbolName,
                    limitVolume,
                    limitPrice,
                    BotLabel,
                    limitStopPips,
                    limitTpPips,
                    ProtectionType.Relative,
                    expiry,
                    comment);

                if (!pendingResult.IsSuccessful || pendingResult.PendingOrder == null)
                {
                    Print("[LIMIT FAIL] {0} {1} Vol={2} Target={3} Error={4}",
                        tradeType, SymbolName, limitVolume, limitPrice, pendingResult.Error);
                    return;
                }

                PendingOrder po = pendingResult.PendingOrder;
                _pendingPlans[po.Id] = new PendingPlan
                {
                    PendingOrderId = po.Id,
                    SignalKey = signalKey,
                    Pattern = m15.Kind.ToString(),
                    Direction = m15.Direction,
                    OriginalVolume = limitVolume,
                    InitialRiskPrice = limitStopPips * Symbol.PipSize,
                    Tp1 = m15.D.Price + direction * m15.CdLength * Tp1CdRatio,
                    Tp2 = m15.D.Price + direction * m15.CdLength * Tp2CdRatio,
                    FinalTp = finalTp
                };
                _lastTradedSignalKey = signalKey;

                Print("[LIMIT] {0} {1} Vol={2} Target={3} Expiry={4:u} Pattern={5}",
                    tradeType, SymbolName, limitVolume, limitPrice, expiry, m15.Kind);
                return;
            }

            TradeResult result = ExecuteMarketOrder(
                tradeType,
                SymbolName,
                volume,
                BotLabel,
                stopPips,
                takeProfitPips,
                comment,
                false,
                StopTriggerMethod.Trade);

            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ORDER FAIL] {0} {1} Vol={2} Error={3}", tradeType, SymbolName, volume, result.Error);
                return;
            }

            Position p = result.Position;
            var plan = new PositionPlan
            {
                PositionId = p.Id,
                OriginalVolume = p.VolumeInUnits,
                SignalKey = signalKey,
                Pattern = m15.Kind.ToString(),
                Direction = m15.Direction,
                InitialRiskPrice = stopPips * Symbol.PipSize,
                Tp1 = tp1,
                Tp2 = tp2,
                FinalTp = p.TakeProfit ?? finalTp,
                T1Done = false,
                T2Done = false,
                LastStopModifyUtc = DateTime.MinValue
            };
            _plans[p.Id] = plan;
            _lastTradedSignalKey = signalKey;
            _dailyTrades++;

            Print("[OPEN] {0} {1} Vol={2} Entry={3} SLp={4:F1} FinalRR={5:F2} Pattern={6} MTFScore={7:F1} Cost/Risk={8:F1}%",
                tradeType, SymbolName, volume, p.EntryPrice, stopPips, finalRR, m15.Kind, confluenceScore, costToRiskPct);

            if (ShowChartMarks)
                DrawSignal(m15, p);
        }

        private void EvaluateHigherTimeframe(
            HarmonicSignal baseline,
            HarmonicSignal higher,
            double weight,
            ref int aligned,
            ref bool conflict,
            ref double scoreSum,
            ref double weightSum)
        {
            if (higher == null || weight <= 0)
                return;

            weightSum += weight;
            if (higher.Direction == baseline.Direction)
            {
                aligned++;
                scoreSum += higher.Score * weight;
            }
            else
            {
                conflict = true;
                // Penalise opposite pattern instead of adding its positive score.
                scoreSum += Math.Max(0.0, 100.0 - higher.Score) * weight;
            }
        }

        private void ManageOpenPositions()
        {
            Position[] positions = Positions.FindAll(BotLabel, SymbolName);
            if (positions.Length == 0)
                return;

            foreach (Position p in positions)
            {
                PositionPlan plan = EnsurePlan(p);
                double current = p.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;

                if (_hardHalt && CloseOnHardHalt)
                {
                    Print("[HARD HALT CLOSE] PID={0} Reason={1}", p.Id, _hardHaltReason);
                    ClosePosition(p);
                    continue;
                }

                if (CloseAtSessionEnd && !IsInsideTradingSession(Server.Time))
                {
                    Print("[SESSION CLOSE] PID={0}", p.Id);
                    ClosePosition(p);
                    continue;
                }

                if (!plan.T1Done && HasReached(p.TradeType, current, plan.Tp1))
                {
                    bool partial = TryPartialClose(p, plan.OriginalVolume, Tp1ClosePct, "TP1");
                    plan.T1Done = true;
                    MoveToBreakEven(p, plan);
                    Print("[TP1] PID={0} Price={1} Partial={2}", p.Id, current, partial);
                }

                if (!plan.T2Done && HasReached(p.TradeType, current, plan.Tp2))
                {
                    bool partial = TryPartialClose(p, plan.OriginalVolume, Tp2ClosePct, "TP2");
                    plan.T2Done = true;
                    Print("[TP2] PID={0} Price={1} Partial={2}", p.Id, current, partial);
                }

                if (plan.T2Done)
                    TrailByRecentM15Structure(p, plan);
            }
        }

        private PositionPlan EnsurePlan(Position p)
        {
            PositionPlan plan;
            if (_plans.TryGetValue(p.Id, out plan))
                return plan;

            double risk = p.StopLoss.HasValue ? Math.Abs(p.EntryPrice - p.StopLoss.Value) : Math.Max(100.0 * Symbol.PipSize, Symbol.PipSize);
            double direction = p.TradeType == TradeType.Buy ? 1.0 : -1.0;

            plan = new PositionPlan
            {
                PositionId = p.Id,
                OriginalVolume = p.VolumeInUnits,
                Pattern = "Recovered",
                Direction = p.TradeType == TradeType.Buy ? SignalDirection.Bullish : SignalDirection.Bearish,
                InitialRiskPrice = risk,
                Tp1 = p.EntryPrice + direction * risk,
                Tp2 = p.EntryPrice + direction * risk * 2.0,
                FinalTp = p.TakeProfit ?? (p.EntryPrice + direction * risk * Math.Max(3.0, MinimumFinalRiskReward)),
                T1Done = HasReached(p.TradeType, p.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask, p.EntryPrice + direction * risk),
                T2Done = false,
                LastStopModifyUtc = DateTime.MinValue
            };

            _plans[p.Id] = plan;
            return plan;
        }

        private bool TryPartialClose(Position p, double originalVolume, double pct, string stage)
        {
            if (pct <= 0)
                return false;

            double desired = Symbol.NormalizeVolumeInUnits(originalVolume * pct / 100.0, RoundingMode.Down);
            double currentVolume = p.VolumeInUnits;

            if (desired < Symbol.VolumeInUnitsMin)
                return false;

            if (currentVolume - desired < Symbol.VolumeInUnitsMin)
                desired = Symbol.NormalizeVolumeInUnits(currentVolume - Symbol.VolumeInUnitsMin, RoundingMode.Down);

            if (desired < Symbol.VolumeInUnitsMin)
                return false;

            TradeResult r = ClosePosition(p, desired);
            if (!r.IsSuccessful)
            {
                Print("[PARTIAL FAIL] {0} PID={1} Vol={2} Error={3}", stage, p.Id, desired, r.Error);
                return false;
            }
            return true;
        }

        private void MoveToBreakEven(Position p, PositionPlan plan)
        {
            double direction = p.TradeType == TradeType.Buy ? 1.0 : -1.0;
            double desired = p.EntryPrice + direction * BreakEvenPlusPips * Symbol.PipSize;
            TryImproveStop(p, plan, desired, "BREAKEVEN");
        }

        private void TrailByRecentM15Structure(Position p, PositionPlan plan)
        {
            if (_m15 == null || _m15.Count < TrailLookbackBars + 3)
                return;

            if ((Server.Time - plan.LastStopModifyUtc).TotalSeconds < 5)
                return;

            int lastClosed = _m15.Count - 2;
            int start = Math.Max(0, lastClosed - TrailLookbackBars + 1);
            double desired;

            if (p.TradeType == TradeType.Buy)
            {
                double floor = double.MaxValue;
                for (int i = start; i <= lastClosed; i++)
                    floor = Math.Min(floor, _m15.LowPrices[i]);

                desired = floor - TrailBufferPips * Symbol.PipSize;
            }
            else
            {
                double ceiling = double.MinValue;
                for (int i = start; i <= lastClosed; i++)
                    ceiling = Math.Max(ceiling, _m15.HighPrices[i]);

                desired = ceiling + TrailBufferPips * Symbol.PipSize;
            }

            TryImproveStop(p, plan, desired, "TRAIL");
        }

        private void TryImproveStop(Position p, PositionPlan plan, double desiredStop, string source)
        {
            double currentMarket = p.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
            double minDistance = BrokerMinimumDistancePips(true, currentMarket) * Symbol.PipSize * 1.05;

            if (p.TradeType == TradeType.Buy)
            {
                desiredStop = Math.Min(desiredStop, Symbol.Bid - minDistance);
                if (p.StopLoss.HasValue && desiredStop <= p.StopLoss.Value + TrailMinimumStepPips * Symbol.PipSize)
                    return;
                if (desiredStop >= Symbol.Bid)
                    return;
            }
            else
            {
                desiredStop = Math.Max(desiredStop, Symbol.Ask + minDistance);
                if (p.StopLoss.HasValue && desiredStop >= p.StopLoss.Value - TrailMinimumStepPips * Symbol.PipSize)
                    return;
                if (desiredStop <= Symbol.Ask)
                    return;
            }

            TradeResult r = ModifyPosition(p, desiredStop, p.TakeProfit);
            if (r.IsSuccessful)
            {
                plan.LastStopModifyUtc = Server.Time;
                Log("[" + source + "] PID=" + p.Id + " SL=" + desiredStop.ToString("F" + Symbol.Digits, CultureInfo.InvariantCulture));
            }
            else
            {
                Print("[{0} FAIL] PID={1} SL={2} Error={3}", source, p.Id, desiredStop, r.Error);
            }
        }

        private void OnPendingOrderFilled(PendingOrderFilledEventArgs args)
        {
            PendingOrder order = args.PendingOrder;
            Position p = args.Position;
            if (order == null || p == null || order.Label != BotLabel || order.SymbolName != SymbolName)
                return;

            PendingPlan pending;
            if (!_pendingPlans.TryGetValue(order.Id, out pending))
            {
                EnsurePlan(p);
                _dailyTrades++;
                Print("[LIMIT FILLED] PID={0} OID={1} recovered plan.", p.Id, order.Id);
                return;
            }

            _plans[p.Id] = new PositionPlan
            {
                PositionId = p.Id,
                OriginalVolume = p.VolumeInUnits,
                SignalKey = pending.SignalKey,
                Pattern = pending.Pattern,
                Direction = pending.Direction,
                InitialRiskPrice = pending.InitialRiskPrice,
                Tp1 = pending.Tp1,
                Tp2 = pending.Tp2,
                FinalTp = p.TakeProfit ?? pending.FinalTp,
                T1Done = false,
                T2Done = false,
                LastStopModifyUtc = DateTime.MinValue
            };
            _pendingPlans.Remove(order.Id);
            _dailyTrades++;
            Print("[LIMIT FILLED] PID={0} OID={1} Entry={2} Pattern={3}", p.Id, order.Id, p.EntryPrice, pending.Pattern);
        }

        private void OnPendingOrderCancelled(PendingOrderCancelledEventArgs args)
        {
            PendingOrder order = args.PendingOrder;
            if (order == null || order.Label != BotLabel || order.SymbolName != SymbolName)
                return;

            _pendingPlans.Remove(order.Id);
            Print("[LIMIT CANCELLED] OID={0} Reason={1}", order.Id, args.Reason);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.Label != BotLabel || p.SymbolName != SymbolName)
                return;

            _lastExitTime = Server.Time;

            if (p.NetProfit < 0)
                _consecutiveLosses++;
            else if (p.NetProfit > 0)
                _consecutiveLosses = 0;

            _plans.Remove(p.Id);

            Print("[CLOSE] PID={0} Reason={1} Net={2:F2} Pips={3:F1} ConsecutiveLosses={4}",
                p.Id, args.Reason, p.NetProfit, p.Pips, _consecutiveLosses);
        }

        // ============================================================
        // Harmonic recognition
        // ============================================================
        private HarmonicSignal FindBestPattern(Bars bars, string timeframeName, int maxSignalAgeBars)
        {
            if (bars == null || bars.Count < Math.Max(50, PivotStrength * 4 + 20))
                return null;

            List<Pivot> pivots = ExtractPivots(bars);
            if (pivots.Count < 5)
                return null;

            int lastClosed = bars.Count - 2;
            HarmonicSignal best = null;
            int minEnd = Math.Max(4, pivots.Count - 10);

            for (int end = pivots.Count - 1; end >= minEnd; end--)
            {
                Pivot[] p = new Pivot[5];
                for (int k = 0; k < 5; k++)
                    p[k] = pivots[end - 4 + k];

                int age = lastClosed - p[4].Index;
                if (age < 0 || age > maxSignalAgeBars)
                    continue;

                HarmonicSignal candidate = ClassifyFivePivotPattern(p[0], p[1], p[2], p[3], p[4], timeframeName, age);
                if (candidate == null)
                    continue;

                if (candidate.Score < MinimumPatternScore)
                    continue;

                if (best == null || candidate.Score > best.Score)
                    best = candidate;
            }

            return best;
        }

        private List<Pivot> ExtractPivots(Bars bars)
        {
            int lastClosed = bars.Count - 2;
            int first = Math.Max(PivotStrength, lastClosed - PivotLookbackBars);
            int lastCandidate = lastClosed - PivotStrength;

            var raw = new List<Pivot>();
            for (int i = first; i <= lastCandidate; i++)
            {
                bool high = true;
                bool low = true;

                double h = bars.HighPrices[i];
                double l = bars.LowPrices[i];

                for (int j = 1; j <= PivotStrength; j++)
                {
                    if (bars.HighPrices[i - j] >= h || bars.HighPrices[i + j] > h)
                        high = false;
                    if (bars.LowPrices[i - j] <= l || bars.LowPrices[i + j] < l)
                        low = false;
                    if (!high && !low)
                        break;
                }

                if (high)
                    raw.Add(new Pivot(i, bars.OpenTimes[i], h, true));
                if (low)
                    raw.Add(new Pivot(i, bars.OpenTimes[i], l, false));
            }

            raw = raw.OrderBy(x => x.Index).ThenByDescending(x => x.IsHigh).ToList();

            var clean = new List<Pivot>();
            foreach (Pivot pv in raw)
            {
                if (clean.Count == 0)
                {
                    clean.Add(pv);
                    continue;
                }

                Pivot last = clean[clean.Count - 1];

                if (pv.Index == last.Index)
                {
                    // A single candle can technically qualify both ways in pathological data.
                    // Keep whichever creates a larger excursion from the previous accepted pivot.
                    if (clean.Count >= 2)
                    {
                        Pivot prev = clean[clean.Count - 2];
                        if (Math.Abs(pv.Price - prev.Price) > Math.Abs(last.Price - prev.Price))
                            clean[clean.Count - 1] = pv;
                    }
                    continue;
                }

                if (pv.IsHigh == last.IsHigh)
                {
                    bool moreExtreme = pv.IsHigh ? pv.Price > last.Price : pv.Price < last.Price;
                    if (moreExtreme)
                        clean[clean.Count - 1] = pv;
                    continue;
                }

                clean.Add(pv);
            }

            return clean;
        }

        private HarmonicSignal ClassifyFivePivotPattern(Pivot x, Pivot a, Pivot b, Pivot c, Pivot d, string tf, int age)
        {
            // Alternation and zero-length checks
            if (x.IsHigh == a.IsHigh || a.IsHigh == b.IsHigh || b.IsHigh == c.IsHigh || c.IsHigh == d.IsHigh)
                return null;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double ad = Math.Abs(d.Price - a.Price);
            double xc = Math.Abs(c.Price - x.Price);

            if (xa <= Symbol.TickSize || ab <= Symbol.TickSize || bc <= Symbol.TickSize || cd <= Symbol.TickSize || xc <= Symbol.TickSize)
                return null;

            double abXa = ab / xa;
            double bcAb = bc / ab;
            double cdBc = cd / bc;
            double adXa = ad / xa;
            double cdAb = cd / ab;
            double xcXa = xc / xa;
            double cdXc = cd / xc;

            SignalDirection direction = d.IsHigh ? SignalDirection.Bearish : SignalDirection.Bullish;

            var candidates = new List<PatternScore>();

            if (EnableGartley)
                candidates.Add(new PatternScore(HarmonicKind.Gartley,
                    AverageScores(
                        ScoreTarget(abXa, 0.618),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 1.272, 1.618),
                        ScoreTarget(adXa, 0.786))));

            if (EnableBat)
                candidates.Add(new PatternScore(HarmonicKind.Bat,
                    AverageScores(
                        ScoreRange(abXa, 0.382, 0.500),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 1.618, 2.618),
                        ScoreTarget(adXa, 0.886))));

            if (EnableAlternateBat)
                candidates.Add(new PatternScore(HarmonicKind.AlternateBat,
                    AverageScores(
                        ScoreRange(abXa, 0.382, 0.500),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 2.000, 3.618),
                        ScoreTarget(adXa, 1.130))));

            if (EnableButterfly)
                candidates.Add(new PatternScore(HarmonicKind.Butterfly,
                    AverageScores(
                        ScoreTarget(abXa, 0.786),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 1.618, 2.618),
                        ScoreRange(adXa, 1.270, 1.618))));

            if (EnableCrab)
                candidates.Add(new PatternScore(HarmonicKind.Crab,
                    AverageScores(
                        ScoreRange(abXa, 0.382, 0.618),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 2.618, 3.618),
                        ScoreTarget(adXa, 1.618))));

            if (EnableDeepCrab)
                candidates.Add(new PatternScore(HarmonicKind.DeepCrab,
                    AverageScores(
                        ScoreTarget(abXa, 0.886),
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreRange(cdBc, 2.000, 3.618),
                        ScoreTarget(adXa, 1.618))));

            if (EnableCypher)
                candidates.Add(new PatternScore(HarmonicKind.Cypher,
                    AverageScores(
                        ScoreRange(abXa, 0.382, 0.618),
                        ScoreRange(xcXa, 1.130, 1.414),
                        ScoreTarget(cdXc, 0.786))));

            // Shark uses O-X-A-B-C terminology. Here the five detected pivots
            // are mapped as O=x, X=a, A=b, B=c, C=d for a single engine.
            if (EnableShark)
            {
                double ox = xa;
                double xaShark = ab;
                double abShark = bc;
                double bcShark = cd;
                double xaToOx = xaShark / ox;
                double abToXa = abShark / xaShark;
                double bcToAb = bcShark / abShark;
                double oc = Math.Abs(d.Price - x.Price);
                double ocToOx = oc / ox;

                candidates.Add(new PatternScore(HarmonicKind.Shark,
                    AverageScores(
                        ScoreRange(xaToOx, 0.382, 0.886),
                        ScoreRange(abToXa, 1.130, 1.618),
                        ScoreRange(bcToAb, 1.618, 2.240),
                        ScoreRange(ocToOx, 0.886, 1.130))));
            }

            if (EnableAbCd)
                candidates.Add(new PatternScore(HarmonicKind.ABCD,
                    AverageScores(
                        ScoreRange(bcAb, 0.382, 0.886),
                        ScoreTarget(cdAb, 1.000))));

            // 5-0 is a post-Shark style reversal structure:
            // B extension, C extension, then D ~50% retracement of BC.
            if (EnableFiveZero)
            {
                double cdToBc = cd / bc;
                candidates.Add(new PatternScore(HarmonicKind.FiveZero,
                    AverageScores(
                        ScoreRange(abXa, 1.130, 1.618),
                        ScoreRange(bcAb, 1.618, 2.240),
                        ScoreTarget(cdToBc, 0.500))));
            }

            PatternScore best = candidates
                .Where(z => z.Score > 0)
                .OrderByDescending(z => z.Score)
                .FirstOrDefault();

            if (best == null)
                return null;

            // Freshness is deliberately mild; pivots are already right-confirmed
            // and therefore non-repainting at the decision point.
            double freshnessPenalty = Math.Min(12.0, age * 1.5);
            double finalScore = Math.Max(0.0, best.Score - freshnessPenalty);

            return new HarmonicSignal
            {
                Kind = best.Kind,
                Direction = direction,
                Timeframe = tf,
                Score = finalScore,
                AgeBars = age,
                X = x,
                A = a,
                B = b,
                C = c,
                D = d,
                XaLength = xa,
                CdLength = cd
            };
        }

        private double ScoreTarget(double actual, double target)
        {
            double tolerance = Math.Max(0.000001, target * RatioTolerancePct / 100.0);
            double diff = Math.Abs(actual - target);
            if (diff > tolerance)
                return 0.0;
            return 100.0 - 35.0 * diff / tolerance;
        }

        private double ScoreRange(double actual, double min, double max)
        {
            if (actual >= min && actual <= max)
            {
                double mid = (min + max) * 0.5;
                double half = Math.Max(0.000001, (max - min) * 0.5);
                return 100.0 - 12.0 * Math.Abs(actual - mid) / half;
            }

            double lowerTolerance = Math.Max(0.000001, min * RatioTolerancePct / 100.0);
            double upperTolerance = Math.Max(0.000001, max * RatioTolerancePct / 100.0);

            if (actual < min && actual >= min - lowerTolerance)
                return 70.0 - 20.0 * (min - actual) / lowerTolerance;

            if (actual > max && actual <= max + upperTolerance)
                return 70.0 - 20.0 * (actual - max) / upperTolerance;

            return 0.0;
        }

        private double AverageScores(params double[] scores)
        {
            if (scores == null || scores.Length == 0 || scores.Any(x => x <= 0))
                return 0.0;
            return scores.Average();
        }

        // ============================================================
        // Risk / execution helpers
        // ============================================================
        private double CalculateVolume(double stopLossPips)
        {
            double volume;

            if (UseRiskPercentSizing)
            {
                if (UseMonthlyCompoundingAnchor)
                {
                    double riskAmount = _monthRiskEquity * RiskPercentPerTrade / 100.0;
                    volume = Symbol.VolumeForFixedRisk(riskAmount, stopLossPips, RoundingMode.Down);
                }
                else
                {
                    volume = Symbol.VolumeForProportionalRisk(
                        ProportionalAmountType.Equity,
                        RiskPercentPerTrade,
                        stopLossPips,
                        RoundingMode.Down);
                }
            }
            else
            {
                volume = Symbol.QuantityToVolumeInUnits(FixedLots);
            }

            if (MaxLots > 0)
            {
                double maxByUser = Symbol.QuantityToVolumeInUnits(MaxLots);
                volume = Math.Min(volume, maxByUser);
            }

            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

            return volume;
        }

        private bool HasBlockingPosition()
        {
            if (RespectAllSymbolPositions)
                return Positions.Any(p => p.SymbolName == SymbolName);

            return Positions.FindAll(BotLabel, SymbolName).Length > 0;
        }

        private double CurrentSpreadPips()
        {
            return Symbol.PipSize > 0 ? Symbol.Spread / Symbol.PipSize : 0.0;
        }

        private double BrokerMinimumDistancePips(bool stopLoss, double referencePrice)
        {
            double raw = stopLoss ? Symbol.MinStopLossDistance : Symbol.MinTakeProfitDistance;

            if (raw <= 0)
                return 0.0;

            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return raw;

            // Percentage distance
            return (referencePrice * raw / 100.0) / Symbol.PipSize;
        }

        private bool IsEntryBlockedByRisk(out string reason)
        {
            reason = string.Empty;

            if (_hardHalt)
            {
                reason = "HardHalt: " + _hardHaltReason;
                return true;
            }

            if (DailyLossLimitPct > 0 && _dayStartEquity > 0)
            {
                double lossPct = (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0;
                if (lossPct >= DailyLossLimitPct)
                {
                    reason = "Daily equity loss " + lossPct.ToString("F2") + "% >= " + DailyLossLimitPct.ToString("F2") + "%";
                    return true;
                }
            }

            if (WeeklyLossLimitPct > 0 && _weekStartEquity > 0)
            {
                double lossPct = (_weekStartEquity - Account.Equity) / _weekStartEquity * 100.0;
                if (lossPct >= WeeklyLossLimitPct)
                {
                    reason = "Weekly equity loss " + lossPct.ToString("F2") + "% >= " + WeeklyLossLimitPct.ToString("F2") + "%";
                    return true;
                }
            }

            if (MaxConsecutiveLosses > 0 && _consecutiveLosses >= MaxConsecutiveLosses)
            {
                reason = "Consecutive losses " + _consecutiveLosses + " >= " + MaxConsecutiveLosses;
                return true;
            }

            return false;
        }

        private void RefreshRiskAnchors()
        {
            DateTime now = Server.Time.Date;
            if (now != _dayAnchor)
            {
                _dayAnchor = now;
                _dayStartEquity = Account.Equity;
                _dailyTrades = 0;
                _consecutiveLosses = 0;
                Log("[RESET] New UTC trading day. Equity anchor=" + _dayStartEquity.ToString("F2"));
            }

            DateTime week = StartOfWeek(now);
            if (week != _weekAnchor)
            {
                _weekAnchor = week;
                _weekStartEquity = Account.Equity;
                Log("[RESET] New UTC trading week. Equity anchor=" + _weekStartEquity.ToString("F2"));
            }

            int monthKey = Server.Time.Year * 100 + Server.Time.Month;
            if (monthKey != _monthAnchorKey)
            {
                _monthAnchorKey = monthKey;
                _monthRiskEquity = Account.Equity;
                Log("[COMPOUND] New UTC month. Risk-sizing equity anchor=" + _monthRiskEquity.ToString("F2"));
            }
        }

        private void UpdatePeakAndCircuitBreakers()
        {
            if (Account.Equity > _peakEquity)
                _peakEquity = Account.Equity;

            if (_hardHalt || MaximumDrawdownPct <= 0 || _peakEquity <= 0)
                return;

            double dd = (_peakEquity - Account.Equity) / _peakEquity * 100.0;
            if (dd >= MaximumDrawdownPct)
            {
                _hardHalt = true;
                _hardHaltReason = "Max equity drawdown " + dd.ToString("F2") + "% >= " + MaximumDrawdownPct.ToString("F2") + "%";
                Print("[HARD HALT] {0}", _hardHaltReason);
            }
        }

        // ============================================================
        // Session / blackout helpers
        // ============================================================
        private bool IsInsideTradingSession(DateTime utc)
        {
            int start = SessionStartHourUtc * 60 + SessionStartMinuteUtc;
            int end = SessionEndHourUtc * 60 + SessionEndMinuteUtc;
            int now = utc.Hour * 60 + utc.Minute;

            if (!InsideCircularWindow(now, start, end))
                return false;

            int minutesSinceStart = CircularForwardDistance(start, now);
            int minutesToEnd = CircularForwardDistance(now, end);

            if (OpenFreezeMinutes > 0 && minutesSinceStart < OpenFreezeMinutes)
                return false;

            if (CloseFreezeMinutes > 0 && minutesToEnd <= CloseFreezeMinutes)
                return false;

            return true;
        }

        private static bool InsideCircularWindow(int now, int start, int end)
        {
            if (start == end)
                return true;

            if (start < end)
                return now >= start && now < end;

            return now >= start || now < end;
        }

        private static int CircularForwardDistance(int from, int to)
        {
            int d = to - from;
            if (d < 0)
                d += 24 * 60;
            return d;
        }

        private void ParseBlackouts()
        {
            _blackouts.Clear();
            if (string.IsNullOrWhiteSpace(ManualBlackoutWindowsUtc))
                return;

            string[] windows = ManualBlackoutWindowsUtc.Split(new[] { ';', ',' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string w in windows)
            {
                string[] pair = w.Trim().Split('-');
                if (pair.Length != 2)
                    continue;

                TimeSpan a, b;
                if (TimeSpan.TryParseExact(pair[0].Trim(), @"hh\:mm", CultureInfo.InvariantCulture, out a) &&
                    TimeSpan.TryParseExact(pair[1].Trim(), @"hh\:mm", CultureInfo.InvariantCulture, out b))
                {
                    _blackouts.Add(new BlackoutWindow { Start = a, End = b });
                }
            }

            if (_blackouts.Count > 0)
                Print("[BLACKOUT] Loaded {0} manual UTC blackout windows.", _blackouts.Count);
        }

        private bool IsManualBlackout(TimeSpan now)
        {
            foreach (BlackoutWindow w in _blackouts)
            {
                int n = (int)now.TotalMinutes;
                int s = (int)w.Start.TotalMinutes;
                int e = (int)w.End.TotalMinutes;
                if (InsideCircularWindow(n, s, e))
                    return true;
            }
            return false;
        }

        // ============================================================
        // Misc helpers / diagnostics
        // ============================================================
        private bool LooksLikeGold(string symbolName)
        {
            if (string.IsNullOrWhiteSpace(symbolName))
                return false;

            string s = symbolName.ToUpperInvariant().Replace("/", "").Replace(".", "").Replace("_", "");
            return s.Contains("XAUUSD") || s.Contains("GOLD");
        }

        private bool IsAheadOfEntry(TradeType type, double target, double entry)
        {
            return type == TradeType.Buy ? target > entry : target < entry;
        }

        private bool HasReached(TradeType type, double current, double target)
        {
            return type == TradeType.Buy ? current >= target : current <= target;
        }

        private static DateTime StartOfWeek(DateTime date)
        {
            int diff = (7 + (date.DayOfWeek - DayOfWeek.Monday)) % 7;
            return date.AddDays(-diff).Date;
        }

        private string Describe(HarmonicSignal s)
        {
            if (s == null)
                return "Neutral";
            return s.Timeframe + ":" + s.Kind + "/" + s.Direction + "/" + s.Score.ToString("F0");
        }

        private void DrawSignal(HarmonicSignal s, Position p)
        {
            try
            {
                Color color = s.Direction == SignalDirection.Bullish ? Color.Green : Color.Red;
                ChartIconType icon = s.Direction == SignalDirection.Bullish ? ChartIconType.UpArrow : ChartIconType.DownArrow;
                string id = "FHGP_" + p.Id;

                Chart.DrawIcon(id + "_D", icon, s.D.Time, s.D.Price, color);
                Chart.DrawText(
                    id + "_TXT",
                    s.Kind + " " + s.Direction + " S" + s.Score.ToString("F0"),
                    s.D.Time,
                    s.D.Price,
                    color);
            }
            catch (Exception ex)
            {
                Log("[CHART] " + ex.Message);
            }
        }

        private void Log(string text)
        {
            if (VerboseLogging)
                Print(text);
        }

        // ============================================================
        // Internal models
        // ============================================================
        public enum EntryExecutionMode
        {
            Market,
            LimitPullback
        }

        private enum SignalDirection
        {
            Bullish,
            Bearish
        }

        private enum HarmonicKind
        {
            Gartley,
            Bat,
            AlternateBat,
            Butterfly,
            Crab,
            DeepCrab,
            Cypher,
            Shark,
            ABCD,
            FiveZero
        }

        private sealed class Pivot
        {
            public Pivot(int index, DateTime time, double price, bool isHigh)
            {
                Index = index;
                Time = time;
                Price = price;
                IsHigh = isHigh;
            }

            public int Index { get; private set; }
            public DateTime Time { get; private set; }
            public double Price { get; private set; }
            public bool IsHigh { get; private set; }
        }

        private sealed class HarmonicSignal
        {
            public HarmonicKind Kind { get; set; }
            public SignalDirection Direction { get; set; }
            public string Timeframe { get; set; }
            public double Score { get; set; }
            public int AgeBars { get; set; }
            public Pivot X { get; set; }
            public Pivot A { get; set; }
            public Pivot B { get; set; }
            public Pivot C { get; set; }
            public Pivot D { get; set; }
            public double XaLength { get; set; }
            public double CdLength { get; set; }
        }

        private sealed class PatternScore
        {
            public PatternScore(HarmonicKind kind, double score)
            {
                Kind = kind;
                Score = score;
            }

            public HarmonicKind Kind { get; private set; }
            public double Score { get; private set; }
        }

        private sealed class PositionPlan
        {
            public int PositionId { get; set; }
            public double OriginalVolume { get; set; }
            public string SignalKey { get; set; }
            public string Pattern { get; set; }
            public SignalDirection Direction { get; set; }
            public double InitialRiskPrice { get; set; }
            public double Tp1 { get; set; }
            public double Tp2 { get; set; }
            public double FinalTp { get; set; }
            public bool T1Done { get; set; }
            public bool T2Done { get; set; }
            public DateTime LastStopModifyUtc { get; set; }
        }

        private sealed class PendingPlan
        {
            public int PendingOrderId { get; set; }
            public string SignalKey { get; set; }
            public string Pattern { get; set; }
            public SignalDirection Direction { get; set; }
            public double OriginalVolume { get; set; }
            public double InitialRiskPrice { get; set; }
            public double Tp1 { get; set; }
            public double Tp2 { get; set; }
            public double FinalTp { get; set; }
        }

        private sealed class BlackoutWindow
        {
            public TimeSpan Start { get; set; }
            public TimeSpan End { get; set; }
        }
    }
}
