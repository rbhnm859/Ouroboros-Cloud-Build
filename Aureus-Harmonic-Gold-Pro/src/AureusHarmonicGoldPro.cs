using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class AureusHarmonicGoldPro : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "AUREUS_XAUUSD", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Require XAUUSD Symbol", DefaultValue = true, Group = "General")]
        public bool RequireXauUsd { get; set; }

        [Parameter("Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 3.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Min Net RR", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 8.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Target AD Retracement", DefaultValue = 0.382, MinValue = 0.236, MaxValue = 0.886, Group = "Risk")]
        public double TargetAdRetracement { get; set; }

        [Parameter("Stop Beyond PRZ ATR", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 3.0, Group = "Risk")]
        public double StopBeyondPrzAtr { get; set; }

        [Parameter("Breakeven At R", DefaultValue = 1.25, MinValue = 0.5, MaxValue = 5.0, Group = "Risk")]
        public double BreakEvenAtR { get; set; }

        [Parameter("Trail Start R", DefaultValue = 2.25, MinValue = 0.75, MaxValue = 8.0, Group = "Risk")]
        public double TrailStartR { get; set; }

        [Parameter("Trail ATR", DefaultValue = 1.40, MinValue = 0.2, MaxValue = 6.0, Group = "Risk")]
        public double TrailAtrMultiplier { get; set; }

        [Parameter("Daily Loss %", DefaultValue = 2.5, MinValue = 0.0, MaxValue = 20.0, Group = "Risk Governor")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Weekly Loss %", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 30.0, Group = "Risk Governor")]
        public double MaxWeeklyLossPercent { get; set; }

        [Parameter("Monthly Loss %", DefaultValue = 8.0, MinValue = 0.0, MaxValue = 40.0, Group = "Risk Governor")]
        public double MaxMonthlyLossPercent { get; set; }

        [Parameter("Peak Drawdown Kill %", DefaultValue = 15.0, MinValue = 1.0, MaxValue = 50.0, Group = "Risk Governor")]
        public double MaxPeakDrawdownPercent { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 3, MinValue = 1, MaxValue = 20, Group = "Limits")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Cooldown Bars", DefaultValue = 4, MinValue = 0, MaxValue = 100, Group = "Limits")]
        public int CooldownBars { get; set; }

        [Parameter("Pivot Left", DefaultValue = 3, MinValue = 2, MaxValue = 20, Group = "Harmonics")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right", DefaultValue = 3, MinValue = 2, MaxValue = 20, Group = "Harmonics")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback", DefaultValue = 700, MinValue = 160, MaxValue = 5000, Group = "Harmonics")]
        public int PivotLookback { get; set; }

        [Parameter("Max Pivot Skip", DefaultValue = 2, MinValue = 0, MaxValue = 6, Group = "Harmonics")]
        public int MaxPivotSkip { get; set; }

        [Parameter("Max C Age After Confirm", DefaultValue = 2, MinValue = 0, MaxValue = 20, Group = "Harmonics")]
        public int MaxCSetupAge { get; set; }

        [Parameter("Setup Expiry Bars", DefaultValue = 64, MinValue = 8, MaxValue = 300, Group = "Harmonics")]
        public int SetupExpiryBars { get; set; }

        [Parameter("Min Setup Score %", DefaultValue = 78.0, MinValue = 65.0, MaxValue = 100.0, Group = "Harmonics")]
        public double MinSetupScore { get; set; }

        [Parameter("Ratio Tolerance %", DefaultValue = 7.0, MinValue = 1.0, MaxValue = 20.0, Group = "Harmonics")]
        public double RatioTolerancePercent { get; set; }

        [Parameter("PRZ Half Width ATR", DefaultValue = 0.30, MinValue = 0.05, MaxValue = 2.0, Group = "Harmonics")]
        public double PrzHalfWidthAtr { get; set; }

        [Parameter("PRZ Ratio Width % XA", DefaultValue = 0.75, MinValue = 0.05, MaxValue = 5.0, Group = "Harmonics")]
        public double PrzRatioWidthPercent { get; set; }

        [Parameter("Invalidation Beyond PRZ ATR", DefaultValue = 0.45, MinValue = 0.05, MaxValue = 3.0, Group = "Harmonics")]
        public double InvalidationBeyondPrzAtr { get; set; }

        [Parameter("Rejection Wick ATR", DefaultValue = 0.10, MinValue = 0.0, MaxValue = 2.0, Group = "Harmonics")]
        public double RejectionWickAtr { get; set; }

        [Parameter("Rejection Window Bars", DefaultValue = 2, MinValue = 1, MaxValue = 10, Group = "Harmonics")]
        public int RejectionWindowBars { get; set; }

        [Parameter("Enable Gartley", DefaultValue = true, Group = "Patterns")]
        public bool EnableGartley { get; set; }

        [Parameter("Enable Bat", DefaultValue = true, Group = "Patterns")]
        public bool EnableBat { get; set; }

        [Parameter("Enable Butterfly", DefaultValue = true, Group = "Patterns")]
        public bool EnableButterfly { get; set; }

        [Parameter("Enable Crab", DefaultValue = true, Group = "Patterns")]
        public bool EnableCrab { get; set; }

        [Parameter("Enable Deep Crab", DefaultValue = true, Group = "Patterns")]
        public bool EnableDeepCrab { get; set; }

        [Parameter("Use HTF Conflict Filter", DefaultValue = true, Group = "MTF")]
        public bool UseHigherTimeframeConflictFilter { get; set; }

        [Parameter("H1 Max C Age", DefaultValue = 6, MinValue = 0, MaxValue = 40, Group = "MTF")]
        public int H1MaxCSetupAge { get; set; }

        [Parameter("H4 Max C Age", DefaultValue = 4, MinValue = 0, MaxValue = 30, Group = "MTF")]
        public int H4MaxCSetupAge { get; set; }

        [Parameter("HTF Relevant Distance ATR", DefaultValue = 2.0, MinValue = 0.25, MaxValue = 10.0, Group = "MTF")]
        public double HtfRelevantDistanceAtr { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 60.0, MinValue = 0.0, Group = "Execution")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Execution Reserve (pips)", DefaultValue = 8.0, MinValue = 0.0, Group = "Execution")]
        public double ExecutionReservePips { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 5, MaxValue = 100, Group = "Execution")]
        public int AtrPeriod { get; set; }

        [Parameter("Min ATR M15 (pips)", DefaultValue = 120.0, MinValue = 0.0, Group = "Execution")]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR Shock x Median", DefaultValue = 3.0, MinValue = 1.0, MaxValue = 10.0, Group = "Execution")]
        public double MaxAtrShockMultiple { get; set; }

        [Parameter("Manual News Blackout UTC", DefaultValue = "", Group = "Execution")]
        public string ManualNewsBlackoutUtc { get; set; }

        [Parameter("Debug Logging", DefaultValue = false, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }

        private Bars _m15;
        private Bars _h1;
        private Bars _h4;
        private AverageTrueRange _atrM15;
        private AverageTrueRange _atrH1;
        private AverageTrueRange _atrH4;
        private List<PatternDefinition> _patterns;
        private readonly List<ProjectedSetup> _activeSetups = new List<ProjectedSetup>();
        private readonly HashSet<string> _seenSetupKeys = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<long, double> _initialRiskPrice = new Dictionary<long, double>();
        private readonly Dictionary<string, int> _patternArms = new Dictionary<string, int>(StringComparer.Ordinal);
        private DateTime _day;
        private DateTime _weekAnchor;
        private int _monthKey;
        private double _dayStartEquity;
        private double _weekStartEquity;
        private double _monthStartEquity;
        private double _equityHighWater;
        private int _tradesToday;
        private int _lastTradeBar = -1000000;
        private bool _entryInFlight;
        private bool _killed;
        private long _armed;
        private long _touches;
        private long _rejections;
        private long _expired;
        private long _invalidated;
        private long _mtfBlocks;
        private long _rrBlocks;
        private long _riskBlocks;
        private long _exposureBlocks;
        private long _opened;

        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            _h4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            _atrM15 = Indicators.AverageTrueRange(_m15, AtrPeriod, MovingAverageType.Exponential);
            _atrH1 = Indicators.AverageTrueRange(_h1, AtrPeriod, MovingAverageType.Exponential);
            _atrH4 = Indicators.AverageTrueRange(_h4, AtrPeriod, MovingAverageType.Exponential);
            _patterns = PatternLibrary.Create();
            ResetPeriodAnchors(true);
            _equityHighWater = Account.Equity;
            Positions.Closed += OnPositionClosed;

            foreach (var position in Positions.Where(p => p.SymbolName == SymbolName && p.Label == BotLabel))
            {
                double risk = ParseInitialRiskFromComment(position.Comment);
                if (risk > 0)
                    _initialRiskPrice[position.Id] = risk;
            }

            Print("AUREUS v1.2 | confirmed XABC -> projected D PRZ -> M15 rejection entry");
            Print("Symbol={0} TF={1} Risk={2:F2}%", SymbolName, TimeFrame, RiskPercent);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            Print("[DIAG] armed={0} touches={1} rejections={2} expired={3} invalidated={4} mtfBlocks={5} rrBlocks={6} riskBlocks={7} exposureBlocks={8} opened={9}",
                _armed, _touches, _rejections, _expired, _invalidated, _mtfBlocks, _rrBlocks, _riskBlocks, _exposureBlocks, _opened);
            foreach (var kv in _patternArms.OrderBy(k => k.Key))
                Print("[DIAG PATTERN] {0}={1}", kv.Key, kv.Value);
        }

        protected override void OnBarClosed()
        {
            if (_killed || !TradingEnabled)
                return;

            if (RequireXauUsd && !NormalizeSymbol(SymbolName).Contains("XAUUSD"))
            {
                if (DebugLogging)
                    Print("[BLOCK] Symbol {0} is not XAUUSD.", SymbolName);
                return;
            }

            if (TimeFrame != TimeFrame.Minute15)
            {
                if (DebugLogging)
                    Print("[BLOCK] Attach this cBot to XAUUSD M15. Current TF={0}", TimeFrame);
                return;
            }

            ResetPeriodAnchors(false);
            UpdateEquityKillSwitch();

            if (_m15.Count < 180 || _h1.Count < 180 || _h4.Count < 180)
                return;

            double atr = _atrM15.Result.LastValue;
            if (!IsFinitePositive(atr))
                return;

            ArmNewSetups();
            MaintainSetups(atr);

            if (!PassRiskGovernor() || !PassExecutionFilters())
                return;

            if (_tradesToday >= MaxTradesPerDay || _m15.Count - 1 - _lastTradeBar < CooldownBars)
                return;

            if (HasAnySameSymbolExposure())
            {
                _exposureBlocks++;
                return;
            }

            ProjectedSetup setup = SelectEntrySetup(atr);
            if (setup == null)
                return;

            if (UseHigherTimeframeConflictFilter && !PassHigherTimeframeConflict(setup))
            {
                setup.Consumed = true;
                _mtfBlocks++;
                if (DebugLogging)
                    Print("[MTF BLOCK] {0} {1} rejected by opposite H1/H4 projected harmonic.", setup.Definition.Code, setup.Direction);
                return;
            }

            setup.Consumed = true;
            ExecuteSetupTrade(setup, atr);
        }

        protected override void OnTick()
        {
            foreach (var p in Positions.Where(x => x.SymbolName == SymbolName && x.Label == BotLabel).ToArray())
                ManagePosition(p);
        }

        private void ArmNewSetups()
        {
            foreach (ProjectedSetup setup in DiscoverProjectedSetups(_m15, _atrM15, MaxCSetupAge, MinSetupScore, true))
            {
                if (_seenSetupKeys.Contains(setup.Key))
                    continue;

                _seenSetupKeys.Add(setup.Key);
                _activeSetups.Add(setup);
                _armed++;
                CountPattern(setup.Definition.Code);

                if (DebugLogging)
                    Print("[ARM] {0} {1} score={2:F1} PRZ={3:F2}-{4:F2} C={5:O}",
                        setup.Definition.Code, setup.Direction, setup.Score, setup.ZoneLow, setup.ZoneHigh, setup.CTime);
            }
        }

        private void MaintainSetups(double atr)
        {
            int last = _m15.Count - 1;
            double high = _m15.HighPrices[last];
            double low = _m15.LowPrices[last];
            double close = _m15.ClosePrices[last];

            foreach (ProjectedSetup setup in _activeSetups.Where(s => !s.Consumed).ToArray())
            {
                int age = last - setup.CIndex;
                if (age > SetupExpiryBars)
                {
                    setup.Consumed = true;
                    _expired++;
                    continue;
                }

                double invalidationBuffer = Math.Max(atr * InvalidationBeyondPrzAtr, Symbol.TickSize * 2);
                if ((setup.Direction == TradeType.Buy && close < setup.ZoneLow - invalidationBuffer) ||
                    (setup.Direction == TradeType.Sell && close > setup.ZoneHigh + invalidationBuffer))
                {
                    setup.Consumed = true;
                    _invalidated++;
                    continue;
                }

                bool intersects = high >= setup.ZoneLow && low <= setup.ZoneHigh;
                if (intersects && !setup.WasTouched)
                {
                    setup.WasTouched = true;
                    setup.TouchBarIndex = last;
                    _touches++;
                    if (DebugLogging)
                        Print("[TOUCH] {0} {1} PRZ={2:F2}-{3:F2}", setup.Definition.Code, setup.Direction, setup.ZoneLow, setup.ZoneHigh);
                }
            }

            _activeSetups.RemoveAll(s => s.Consumed && last - s.CIndex > SetupExpiryBars + 20);
        }

        private ProjectedSetup SelectEntrySetup(double atr)
        {
            int last = _m15.Count - 1;
            double open = _m15.OpenPrices[last];
            double high = _m15.HighPrices[last];
            double low = _m15.LowPrices[last];
            double close = _m15.ClosePrices[last];

            var candidates = new List<ProjectedSetup>();
            foreach (ProjectedSetup setup in _activeSetups.Where(s => !s.Consumed && s.WasTouched))
            {
                if (last - setup.TouchBarIndex > RejectionWindowBars)
                    continue;

                bool rejection = IsRejectionBar(setup, open, high, low, close, atr);
                if (!rejection)
                    continue;

                _rejections++;
                candidates.Add(setup);
            }

            if (candidates.Count == 0)
                return null;

            return candidates
                .OrderByDescending(s => s.Score)
                .ThenByDescending(s => s.CIndex)
                .First();
        }

        private bool IsRejectionBar(ProjectedSetup setup, double open, double high, double low, double close, double atr)
        {
            double midpoint = (setup.ZoneLow + setup.ZoneHigh) / 2.0;
            double minWick = atr * RejectionWickAtr;

            if (setup.Direction == TradeType.Buy)
            {
                double lowerWick = Math.Min(open, close) - low;
                bool bullishBody = close > open;
                bool closesFirm = close >= midpoint;
                bool clearsZone = close > setup.ZoneHigh;
                return bullishBody && closesFirm && (lowerWick >= minWick || clearsZone);
            }

            double upperWick = high - Math.Max(open, close);
            bool bearishBody = close < open;
            bool closesWeak = close <= midpoint;
            bool clearsZoneDown = close < setup.ZoneLow;
            return bearishBody && closesWeak && (upperWick >= minWick || clearsZoneDown);
        }

        private void ExecuteSetupTrade(ProjectedSetup setup, double atr)
        {
            if (_entryInFlight || HasAnySameSymbolExposure())
                return;

            _entryInFlight = true;
            try
            {
                double entry = setup.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                double invalidation = setup.Direction == TradeType.Buy
                    ? setup.ZoneLow - atr * StopBeyondPrzAtr
                    : setup.ZoneHigh + atr * StopBeyondPrzAtr;

                if (setup.Direction == TradeType.Buy)
                    invalidation = Math.Min(invalidation, setup.X.Price - Symbol.TickSize * 2);
                else
                    invalidation = Math.Max(invalidation, setup.X.Price + Symbol.TickSize * 2);

                double stopDistance = setup.Direction == TradeType.Buy ? entry - invalidation : invalidation - entry;
                if (!IsFinitePositive(stopDistance))
                {
                    _riskBlocks++;
                    return;
                }

                double target = setup.Direction == TradeType.Buy
                    ? setup.ProjectedD + Math.Abs(setup.A.Price - setup.ProjectedD) * TargetAdRetracement
                    : setup.ProjectedD - Math.Abs(setup.A.Price - setup.ProjectedD) * TargetAdRetracement;
                double targetDistance = setup.Direction == TradeType.Buy ? target - entry : entry - target;
                if (!IsFinitePositive(targetDistance))
                {
                    _rrBlocks++;
                    return;
                }

                double slPips = stopDistance / Symbol.PipSize;
                double tpPips = targetDistance / Symbol.PipSize;
                if (slPips <= ExecutionReservePips || tpPips <= ExecutionReservePips)
                {
                    _rrBlocks++;
                    return;
                }

                double netRr = (tpPips - ExecutionReservePips) / (slPips + ExecutionReservePips);
                if (netRr < MinimumRiskReward)
                {
                    _rrBlocks++;
                    if (DebugLogging)
                        Print("[RR BLOCK] {0} netRR={1:F2} min={2:F2}", setup.Definition.Code, netRr, MinimumRiskReward);
                    return;
                }

                double riskCash = Account.Equity * RiskPercent / 100.0;
                double riskPipsForSizing = slPips + ExecutionReservePips;
                double volume = Symbol.VolumeForFixedRisk(riskCash, riskPipsForSizing, RoundingMode.Down);
                volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

                if (!IsFinitePositive(volume) || volume < Symbol.VolumeInUnitsMin)
                {
                    _riskBlocks++;
                    return;
                }

                if (volume > Symbol.VolumeInUnitsMax)
                    volume = Symbol.VolumeInUnitsMax;

                double amountRisked = Symbol.AmountRisked(volume, riskPipsForSizing);
                if (!IsFinitePositive(amountRisked) || amountRisked > riskCash * 1.001)
                {
                    _riskBlocks++;
                    return;
                }

                string comment = string.Format(System.Globalization.CultureInfo.InvariantCulture,
                    "{0}|risk={1:F8}|score={2:F1}", setup.Definition.Code, stopDistance, setup.Score);

                TradeResult result = ExecuteMarketOrder(setup.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment, false);
                if (!result.IsSuccessful || result.Position == null)
                {
                    Print("[ORDER FAIL] {0}", result.Error);
                    return;
                }

                if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
                {
                    Print("[PROTECTION FAIL] Closing unprotected position {0}.", result.Position.Id);
                    ClosePosition(result.Position);
                    return;
                }

                _initialRiskPrice[result.Position.Id] = stopDistance;
                _lastTradeBar = _m15.Count - 1;
                _tradesToday++;
                _opened++;

                Print("[OPEN] {0} {1} score={2:F1} vol={3} SL={4:F1}p TP={5:F1}p netRR={6:F2}",
                    setup.Definition.Code, setup.Direction, setup.Score, volume, slPips, tpPips, netRr);
            }
            finally
            {
                _entryInFlight = false;
            }
        }

        private bool PassHigherTimeframeConflict(ProjectedSetup m15Setup)
        {
            double price = m15Setup.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;

            List<ProjectedSetup> h1 = DiscoverProjectedSetups(_h1, _atrH1, H1MaxCSetupAge, MinSetupScore, false);
            List<ProjectedSetup> h4 = DiscoverProjectedSetups(_h4, _atrH4, H4MaxCSetupAge, MinSetupScore, false);

            foreach (ProjectedSetup higher in h1.Concat(h4))
            {
                double atr = higher.Source == "H4" ? _atrH4.Result.LastValue : _atrH1.Result.LastValue;
                if (!IsFinitePositive(atr))
                    continue;

                double distance = DistanceToZone(price, higher.ZoneLow, higher.ZoneHigh);
                if (distance > atr * HtfRelevantDistanceAtr)
                    continue;

                if (higher.Direction != m15Setup.Direction)
                    return false;
            }

            return true;
        }

        private List<ProjectedSetup> DiscoverProjectedSetups(Bars bars, AverageTrueRange atrIndicator, int maxCAge, double minScore, bool useToggles)
        {
            var results = new List<ProjectedSetup>();
            List<PivotPoint> pivots = BuildConfirmedPivots(bars);
            if (pivots.Count < 4)
                return results;

            int last = bars.Count - 1;
            int maxSkip = Math.Max(0, MaxPivotSkip);
            int cStart = Math.Max(3, pivots.Count - 12);

            for (int iC = pivots.Count - 1; iC >= cStart; iC--)
            {
                PivotPoint c = pivots[iC];
                int cAge = last - c.Index - PivotRight;
                if (cAge < 0 || cAge > maxCAge)
                    continue;

                int bFloor = Math.Max(2, iC - 1 - maxSkip);
                for (int iB = iC - 1; iB >= bFloor; iB--)
                {
                    int aFloor = Math.Max(1, iB - 1 - maxSkip);
                    for (int iA = iB - 1; iA >= aFloor; iA--)
                    {
                        int xFloor = Math.Max(0, iA - 1 - maxSkip);
                        for (int iX = iA - 1; iX >= xFloor; iX--)
                        {
                            PivotPoint x = pivots[iX];
                            PivotPoint a = pivots[iA];
                            PivotPoint b = pivots[iB];

                            TradeType? direction = GetXabcDirection(x, a, b, c);
                            if (!direction.HasValue)
                                continue;

                            double xa = Math.Abs(a.Price - x.Price);
                            double ab = Math.Abs(b.Price - a.Price);
                            double bc = Math.Abs(c.Price - b.Price);
                            if (!IsFinitePositive(xa) || !IsFinitePositive(ab) || !IsFinitePositive(bc))
                                continue;

                            double bXa = ab / xa;
                            double cAb = bc / ab;
                            double atr = atrIndicator.Result.LastValue;
                            if (!IsFinitePositive(atr))
                                continue;

                            foreach (PatternDefinition def in _patterns)
                            {
                                if (useToggles && !IsPatternEnabled(def.Code))
                                    continue;

                                ProjectedRatioResult ratios = def.Project(x, a, b, c, bXa, cAb, RatioTolerancePercent);
                                if (!ratios.IsValid)
                                    continue;

                                double score = ratios.Score;
                                if (score < minScore)
                                    continue;

                                double halfWidth = Math.Max(atr * PrzHalfWidthAtr, xa * PrzRatioWidthPercent / 100.0);
                                double zoneLow = ratios.ProjectedD - halfWidth;
                                double zoneHigh = ratios.ProjectedD + halfWidth;
                                string source = bars.TimeFrame == TimeFrame.Hour4 ? "H4" : bars.TimeFrame == TimeFrame.Hour ? "H1" : "M15";

                                results.Add(new ProjectedSetup(
                                    def, direction.Value, x, a, b, c, ratios.ProjectedD,
                                    zoneLow, zoneHigh, score, c.Index, bars.OpenTimes[c.Index], source));
                            }
                        }
                    }
                }
            }

            return results
                .OrderByDescending(s => s.Score)
                .ThenByDescending(s => s.CIndex)
                .Take(24)
                .ToList();
        }

        private TradeType? GetXabcDirection(PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c)
        {
            bool bullish = x.Kind == PivotKind.Low && a.Kind == PivotKind.High && b.Kind == PivotKind.Low && c.Kind == PivotKind.High;
            bool bearish = x.Kind == PivotKind.High && a.Kind == PivotKind.Low && b.Kind == PivotKind.High && c.Kind == PivotKind.Low;
            if (bullish)
                return TradeType.Buy;
            if (bearish)
                return TradeType.Sell;
            return null;
        }

        private List<PivotPoint> BuildConfirmedPivots(Bars bars)
        {
            var pivots = new List<PivotPoint>();
            int latestConfirmed = bars.Count - 1 - PivotRight;
            int first = Math.Max(PivotLeft, bars.Count - PivotLookback);

            for (int i = first; i <= latestConfirmed; i++)
            {
                bool high = true;
                bool low = true;

                for (int j = 1; j <= PivotLeft; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i - j]) high = false;
                    if (bars.LowPrices[i] >= bars.LowPrices[i - j]) low = false;
                }

                for (int j = 1; j <= PivotRight; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i + j]) high = false;
                    if (bars.LowPrices[i] >= bars.LowPrices[i + j]) low = false;
                }

                if (high && !low)
                    AddAlternating(pivots, new PivotPoint(i, bars.HighPrices[i], PivotKind.High));
                else if (low && !high)
                    AddAlternating(pivots, new PivotPoint(i, bars.LowPrices[i], PivotKind.Low));
            }

            if (pivots.Count > 130)
                pivots = pivots.GetRange(pivots.Count - 130, 130);

            return pivots;
        }

        private void AddAlternating(List<PivotPoint> pivots, PivotPoint next)
        {
            if (pivots.Count == 0)
            {
                pivots.Add(next);
                return;
            }

            PivotPoint last = pivots[pivots.Count - 1];
            if (last.Kind != next.Kind)
            {
                pivots.Add(next);
                return;
            }

            bool replace = next.Kind == PivotKind.High ? next.Price > last.Price : next.Price < last.Price;
            if (replace)
                pivots[pivots.Count - 1] = next;
        }

        private bool IsPatternEnabled(string code)
        {
            if (code == "Gartley") return EnableGartley;
            if (code == "Bat") return EnableBat;
            if (code == "Butterfly") return EnableButterfly;
            if (code == "Crab") return EnableCrab;
            if (code == "DeepCrab") return EnableDeepCrab;
            return true;
        }

        private void ManagePosition(Position p)
        {
            double initialRisk;
            if (!_initialRiskPrice.TryGetValue(p.Id, out initialRisk) || !IsFinitePositive(initialRisk))
            {
                initialRisk = ParseInitialRiskFromComment(p.Comment);
                if (!IsFinitePositive(initialRisk))
                    return;
                _initialRiskPrice[p.Id] = initialRisk;
            }

            double favorable = p.TradeType == TradeType.Buy ? Symbol.Bid - p.EntryPrice : p.EntryPrice - Symbol.Ask;
            if (favorable <= 0)
                return;

            double r = favorable / initialRisk;
            double desired = p.StopLoss.HasValue ? p.StopLoss.Value : double.NaN;

            if (r >= BreakEvenAtR)
            {
                double be = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + Symbol.PipSize * ExecutionReservePips
                    : p.EntryPrice - Symbol.PipSize * ExecutionReservePips;

                if (double.IsNaN(desired) ||
                    (p.TradeType == TradeType.Buy && be > desired) ||
                    (p.TradeType == TradeType.Sell && be < desired))
                    desired = be;
            }

            if (r >= TrailStartR)
            {
                double atr = _atrM15.Result.LastValue;
                if (IsFinitePositive(atr))
                {
                    double trail = p.TradeType == TradeType.Buy
                        ? Symbol.Bid - atr * TrailAtrMultiplier
                        : Symbol.Ask + atr * TrailAtrMultiplier;

                    if (p.TradeType == TradeType.Buy && (double.IsNaN(desired) || trail > desired))
                        desired = trail;
                    if (p.TradeType == TradeType.Sell && (double.IsNaN(desired) || trail < desired))
                        desired = trail;
                }
            }

            if (double.IsNaN(desired))
                return;

            bool improves = !p.StopLoss.HasValue ||
                (p.TradeType == TradeType.Buy && desired > p.StopLoss.Value + Symbol.TickSize) ||
                (p.TradeType == TradeType.Sell && desired < p.StopLoss.Value - Symbol.TickSize);

            if (!improves)
                return;

            TradeResult mod = ModifyPosition(p, desired, p.TakeProfit);
            if (!mod.IsSuccessful && DebugLogging)
                Print("[MODIFY FAIL] pid={0} err={1}", p.Id, mod.Error);
        }

        private bool PassExecutionFilters()
        {
            if (!IsWithinLondonToNewYorkWindow(Server.Time))
                return false;

            if (IsManualNewsBlackout(Server.Time))
                return false;

            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
                return false;

            double atr = _atrM15.Result.LastValue;
            if (!IsFinitePositive(atr))
                return false;

            double atrPips = atr / Symbol.PipSize;
            if (MinAtrPips > 0 && atrPips < MinAtrPips)
                return false;

            double median = MedianAtr(64);
            if (median > 0 && MaxAtrShockMultiple > 1 && atr > median * MaxAtrShockMultiple)
                return false;

            return true;
        }

        private bool PassRiskGovernor()
        {
            if (_killed)
                return false;

            if (_tradesToday >= MaxTradesPerDay)
                return false;

            if (MaxDailyLossPercent > 0 && LossPercent(_dayStartEquity, Account.Equity) >= MaxDailyLossPercent)
                return false;

            if (MaxWeeklyLossPercent > 0 && LossPercent(_weekStartEquity, Account.Equity) >= MaxWeeklyLossPercent)
                return false;

            if (MaxMonthlyLossPercent > 0 && LossPercent(_monthStartEquity, Account.Equity) >= MaxMonthlyLossPercent)
                return false;

            return true;
        }

        private void UpdateEquityKillSwitch()
        {
            if (Account.Equity > _equityHighWater)
                _equityHighWater = Account.Equity;

            if (MaxPeakDrawdownPercent <= 0 || _equityHighWater <= 0)
                return;

            double dd = 100.0 * (_equityHighWater - Account.Equity) / _equityHighWater;
            if (dd >= MaxPeakDrawdownPercent)
            {
                _killed = true;
                Print("[KILL] Peak-to-equity drawdown {0:F2}% >= {1:F2}%. New entries disabled.", dd, MaxPeakDrawdownPercent);
            }
        }

        private void ResetPeriodAnchors(bool force)
        {
            DateTime now = Server.Time;
            DateTime monday = now.Date.AddDays(-(((int)now.DayOfWeek + 6) % 7));
            int monthKey = now.Year * 100 + now.Month;

            if (force || now.Date != _day)
            {
                _day = now.Date;
                _dayStartEquity = Account.Equity;
                _tradesToday = 0;
            }

            if (force || monday != _weekAnchor)
            {
                _weekAnchor = monday;
                _weekStartEquity = Account.Equity;
            }

            if (force || monthKey != _monthKey)
            {
                _monthKey = monthKey;
                _monthStartEquity = Account.Equity;
            }
        }

        private bool HasAnySameSymbolExposure()
        {
            return Positions.Any(p => p.SymbolName == SymbolName) || PendingOrders.Any(o => o.SymbolName == SymbolName);
        }

        private double MedianAtr(int count)
        {
            int available = Math.Min(count, _m15.Count - 2);
            if (available < 10)
                return 0;

            var values = new List<double>(available);
            for (int i = 1; i <= available; i++)
            {
                double v = _atrM15.Result.Last(i);
                if (IsFinitePositive(v))
                    values.Add(v);
            }

            if (values.Count < 10)
                return 0;

            values.Sort();
            int mid = values.Count / 2;
            return values.Count % 2 == 0 ? (values[mid - 1] + values[mid]) / 2.0 : values[mid];
        }

        private bool IsWithinLondonToNewYorkWindow(DateTime utc)
        {
            if (utc.DayOfWeek == DayOfWeek.Saturday || utc.DayOfWeek == DayOfWeek.Sunday)
                return false;

            int londonOpenUtc = IsUkDst(utc.Date) ? 7 : 8;
            int newYorkCloseUtc = IsUsDst(utc.Date) ? 21 : 22;
            double hour = utc.Hour + utc.Minute / 60.0;
            return hour >= londonOpenUtc && hour < newYorkCloseUtc;
        }

        private static bool IsUkDst(DateTime date)
        {
            DateTime start = LastSunday(date.Year, 3);
            DateTime end = LastSunday(date.Year, 10);
            return date >= start && date < end;
        }

        private static bool IsUsDst(DateTime date)
        {
            DateTime start = NthSunday(date.Year, 3, 2);
            DateTime end = NthSunday(date.Year, 11, 1);
            return date >= start && date < end;
        }

        private static DateTime LastSunday(int year, int month)
        {
            DateTime d = new DateTime(year, month, DateTime.DaysInMonth(year, month));
            while (d.DayOfWeek != DayOfWeek.Sunday)
                d = d.AddDays(-1);
            return d;
        }

        private static DateTime NthSunday(int year, int month, int n)
        {
            DateTime d = new DateTime(year, month, 1);
            while (d.DayOfWeek != DayOfWeek.Sunday)
                d = d.AddDays(1);
            return d.AddDays(7 * (n - 1));
        }

        private bool IsManualNewsBlackout(DateTime utc)
        {
            if (string.IsNullOrWhiteSpace(ManualNewsBlackoutUtc))
                return false;

            string[] windows = ManualNewsBlackoutUtc.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string window in windows)
            {
                string[] pair = window.Trim().Split('/');
                if (pair.Length != 2)
                    continue;

                DateTime start;
                DateTime end;
                if (DateTime.TryParse(pair[0].Trim(), out start) && DateTime.TryParse(pair[1].Trim(), out end))
                {
                    start = DateTime.SpecifyKind(start, DateTimeKind.Utc);
                    end = DateTime.SpecifyKind(end, DateTimeKind.Utc);
                    if (utc >= start && utc <= end)
                        return true;
                }
            }
            return false;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != BotLabel)
                return;

            _initialRiskPrice.Remove(p.Id);
            Print("[CLOSE] id={0} net={1:F2} pips={2:F1}", p.Id, p.NetProfit, p.Pips);
        }

        private void CountPattern(string code)
        {
            int count;
            _patternArms.TryGetValue(code, out count);
            _patternArms[code] = count + 1;
        }

        private static double DistanceToZone(double price, double low, double high)
        {
            if (price < low) return low - price;
            if (price > high) return price - high;
            return 0;
        }

        private static double LossPercent(double start, double current)
        {
            if (start <= 0 || current >= start)
                return 0;
            return 100.0 * (start - current) / start;
        }

        private static string NormalizeSymbol(string symbol)
        {
            if (string.IsNullOrWhiteSpace(symbol))
                return "";
            return new string(symbol.ToUpperInvariant().Where(char.IsLetterOrDigit).ToArray());
        }

        private static bool IsFinitePositive(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value) && value > 0;
        }

        private static double ParseInitialRiskFromComment(string comment)
        {
            if (string.IsNullOrWhiteSpace(comment))
                return 0;

            foreach (string token in comment.Split('|'))
            {
                if (!token.StartsWith("risk=", StringComparison.OrdinalIgnoreCase))
                    continue;

                double value;
                if (double.TryParse(token.Substring(5), System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out value))
                    return value;
            }
            return 0;
        }

        private enum PivotKind
        {
            High,
            Low
        }

        private sealed class PivotPoint
        {
            public int Index { get; private set; }
            public double Price { get; private set; }
            public PivotKind Kind { get; private set; }

            public PivotPoint(int index, double price, PivotKind kind)
            {
                Index = index;
                Price = price;
                Kind = kind;
            }
        }

        private sealed class ProjectedSetup
        {
            public PatternDefinition Definition { get; private set; }
            public TradeType Direction { get; private set; }
            public PivotPoint X { get; private set; }
            public PivotPoint A { get; private set; }
            public PivotPoint B { get; private set; }
            public PivotPoint C { get; private set; }
            public double ProjectedD { get; private set; }
            public double ZoneLow { get; private set; }
            public double ZoneHigh { get; private set; }
            public double Score { get; private set; }
            public int CIndex { get; private set; }
            public DateTime CTime { get; private set; }
            public string Source { get; private set; }
            public bool WasTouched { get; set; }
            public int TouchBarIndex { get; set; }
            public bool Consumed { get; set; }

            public string Key
            {
                get
                {
                    return string.Format(System.Globalization.CultureInfo.InvariantCulture,
                        "{0}|{1}|{2}|{3}|{4}|{5}|{6:F5}",
                        Definition.Code, Direction, X.Index, A.Index, B.Index, C.Index, ProjectedD);
                }
            }

            public ProjectedSetup(PatternDefinition definition, TradeType direction,
                PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c,
                double projectedD, double zoneLow, double zoneHigh, double score,
                int cIndex, DateTime cTime, string source)
            {
                Definition = definition;
                Direction = direction;
                X = x;
                A = a;
                B = b;
                C = c;
                ProjectedD = projectedD;
                ZoneLow = zoneLow;
                ZoneHigh = zoneHigh;
                Score = score;
                CIndex = cIndex;
                CTime = cTime;
                Source = source;
                TouchBarIndex = -1000000;
            }
        }

        private sealed class ProjectedRatioResult
        {
            public bool IsValid { get; private set; }
            public double ProjectedD { get; private set; }
            public double Score { get; private set; }

            public ProjectedRatioResult(bool isValid, double projectedD, double score)
            {
                IsValid = isValid;
                ProjectedD = projectedD;
                Score = score;
            }
        }

        private sealed class RatioRule
        {
            public double Min { get; private set; }
            public double Max { get; private set; }
            public double Weight { get; private set; }

            public RatioRule(double min, double max, double weight)
            {
                Min = min;
                Max = max;
                Weight = weight;
            }

            public double Score(double value, double tolerancePercent)
            {
                if (double.IsNaN(value) || double.IsInfinity(value))
                    return 0;

                double center = (Min + Max) / 2.0;
                double tolerance = Math.Max(Math.Abs(center) * tolerancePercent / 100.0, 0.000001);
                double lo = Min - tolerance;
                double hi = Max + tolerance;

                if (value < lo || value > hi)
                    return 0;

                if (Math.Abs(Max - Min) < 0.000001)
                {
                    double distance = Math.Abs(value - center);
                    return Math.Max(70.0, 100.0 - 30.0 * distance / tolerance);
                }

                if (value >= Min && value <= Max)
                {
                    double halfWidth = Math.Max((Max - Min) / 2.0, 0.000001);
                    double normalized = Math.Abs(value - center) / halfWidth;
                    return Math.Max(90.0, 100.0 - 10.0 * normalized);
                }

                double outside = value < Min ? Min - value : value - Max;
                return Math.Max(70.0, 90.0 - 20.0 * outside / tolerance);
            }
        }

        private sealed class PatternDefinition
        {
            public string Code { get; private set; }
            public RatioRule B_XA { get; private set; }
            public RatioRule C_AB { get; private set; }
            public double D_XA { get; private set; }
            public RatioRule CD_BC { get; private set; }
            public RatioRule CD_AB { get; private set; }

            public PatternDefinition(string code, RatioRule bXa, RatioRule cAb, double dXa, RatioRule cdBc, RatioRule cdAb)
            {
                Code = code;
                B_XA = bXa;
                C_AB = cAb;
                D_XA = dXa;
                CD_BC = cdBc;
                CD_AB = cdAb;
            }

            public ProjectedRatioResult Project(PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c,
                double bXa, double cAb, double tolerancePercent)
            {
                double bScore = B_XA.Score(bXa, tolerancePercent);
                double cScore = C_AB.Score(cAb, tolerancePercent);
                if (bScore <= 0 || cScore <= 0)
                    return new ProjectedRatioResult(false, 0, 0);

                double xa = Math.Abs(a.Price - x.Price);
                double projectedD = a.Kind == PivotKind.High
                    ? a.Price - xa * D_XA
                    : a.Price + xa * D_XA;

                double bc = Math.Abs(c.Price - b.Price);
                double ab = Math.Abs(b.Price - a.Price);
                double cd = Math.Abs(projectedD - c.Price);
                if (!IsFinitePositive(bc) || !IsFinitePositive(ab) || !IsFinitePositive(cd))
                    return new ProjectedRatioResult(false, 0, 0);

                double cdBc = cd / bc;
                double cdAb = cd / ab;
                double bcScore = CD_BC.Score(cdBc, tolerancePercent);
                double abScore = CD_AB.Score(cdAb, tolerancePercent);
                if (bcScore <= 0 || abScore <= 0)
                    return new ProjectedRatioResult(false, 0, 0);

                double weighted = bScore * B_XA.Weight + cScore * C_AB.Weight +
                                  bcScore * CD_BC.Weight + abScore * CD_AB.Weight;
                double weights = B_XA.Weight + C_AB.Weight + CD_BC.Weight + CD_AB.Weight;
                return new ProjectedRatioResult(true, projectedD, weighted / weights);
            }
        }

        private static class PatternLibrary
        {
            public static List<PatternDefinition> Create()
            {
                return new List<PatternDefinition>
                {
                    new PatternDefinition("Gartley",
                        new RatioRule(0.618, 0.618, 1.50),
                        new RatioRule(0.382, 0.886, 0.80),
                        0.786,
                        new RatioRule(1.130, 1.618, 1.00),
                        new RatioRule(1.000, 1.272, 0.90)),

                    new PatternDefinition("Bat",
                        new RatioRule(0.382, 0.500, 1.30),
                        new RatioRule(0.382, 0.886, 0.80),
                        0.886,
                        new RatioRule(1.618, 2.618, 1.00),
                        new RatioRule(1.000, 1.272, 0.90)),

                    new PatternDefinition("Butterfly",
                        new RatioRule(0.786, 0.786, 1.45),
                        new RatioRule(0.382, 0.886, 0.80),
                        1.270,
                        new RatioRule(1.618, 2.618, 1.00),
                        new RatioRule(1.270, 1.618, 0.95)),

                    new PatternDefinition("Crab",
                        new RatioRule(0.382, 0.618, 1.20),
                        new RatioRule(0.382, 0.886, 0.80),
                        1.618,
                        new RatioRule(2.240, 3.618, 1.00),
                        new RatioRule(1.270, 2.000, 0.85)),

                    new PatternDefinition("DeepCrab",
                        new RatioRule(0.886, 0.886, 1.50),
                        new RatioRule(0.382, 0.886, 0.80),
                        1.618,
                        new RatioRule(2.000, 3.618, 1.00),
                        new RatioRule(1.270, 2.000, 0.85))
                };
            }
        }
    }
}