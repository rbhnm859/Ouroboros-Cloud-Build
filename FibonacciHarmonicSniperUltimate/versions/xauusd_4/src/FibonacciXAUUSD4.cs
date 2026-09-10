using System;
using System.Collections.Generic;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class FibonacciXAUUSD4 : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "FIB_XAUUSD_4", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 10.0, Group = "Risk")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 8, MinValue = 1, MaxValue = 24, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Max Consecutive Losses", DefaultValue = 3, MinValue = 1, MaxValue = 10, Group = "Risk")]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Minimum RR", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 5.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Max Allowed RR", DefaultValue = 6.0, MinValue = 2.0, MaxValue = 15.0, Group = "Risk")]
        public double MaxAllowedRR { get; set; }

        [Parameter("Enable Harmonics", DefaultValue = true, Group = "Architecture")]
        public bool EnableHarmonics { get; set; }

        [Parameter("Enable Fib Pullback", DefaultValue = true, Group = "Architecture")]
        public bool EnableFibPullback { get; set; }

        [Parameter("Final Score Min", DefaultValue = 64.0, MinValue = 45.0, MaxValue = 90.0, Group = "Scoring")]
        public double FinalScoreMin { get; set; }

        [Parameter("Harmonic Geometry Min", DefaultValue = 31.0, MinValue = 20.0, MaxValue = 55.0, Group = "Scoring")]
        public double HarmonicGeometryMin { get; set; }

        [Parameter("Pivot Left", DefaultValue = 2, MinValue = 1, MaxValue = 6, Group = "M15 Structure")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right", DefaultValue = 1, MinValue = 1, MaxValue = 4, Group = "M15 Structure")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback", DefaultValue = 420, MinValue = 120, MaxValue = 1200, Group = "M15 Structure")]
        public int PivotLookback { get; set; }

        [Parameter("Max Pattern Age M15", DefaultValue = 16, MinValue = 4, MaxValue = 64, Group = "M15 Structure")]
        public int MaxPatternAgeM15Bars { get; set; }

        [Parameter("Min XA ATR", DefaultValue = 2.0, MinValue = 0.75, MaxValue = 8.0, Group = "M15 Structure")]
        public double MinXaAtr { get; set; }

        [Parameter("Min Impulse ATR", DefaultValue = 1.20, MinValue = 0.50, MaxValue = 6.0, Group = "M15 Structure")]
        public double MinImpulseAtr { get; set; }

        [Parameter("Ratio Tolerance %", DefaultValue = 8.0, MinValue = 2.0, MaxValue = 20.0, Group = "Harmonics")]
        public double RatioTolerancePercent { get; set; }

        [Parameter("PRZ ATR Half Width", DefaultValue = 0.18, MinValue = 0.05, MaxValue = 0.80, Group = "Harmonics")]
        public double PrzAtrHalfWidth { get; set; }

        [Parameter("Max Projection Dispersion ATR", DefaultValue = 1.75, MinValue = 0.50, MaxValue = 4.0, Group = "Harmonics")]
        public double MaxProjectionDispersionAtr { get; set; }

        [Parameter("Target AD Fib", DefaultValue = 0.618, MinValue = 0.382, MaxValue = 1.0, Group = "Exit")]
        public double TargetAdFib { get; set; }

        [Parameter("Fib Shallow", DefaultValue = 0.50, MinValue = 0.382, MaxValue = 0.70, Group = "Fibonacci Pullback")]
        public double FibShallow { get; set; }

        [Parameter("Fib Deep", DefaultValue = 0.786, MinValue = 0.618, MaxValue = 0.90, Group = "Fibonacci Pullback")]
        public double FibDeep { get; set; }

        [Parameter("Stop Fib", DefaultValue = 0.886, MinValue = 0.75, MaxValue = 1.05, Group = "Fibonacci Pullback")]
        public double StopFib { get; set; }

        [Parameter("SL ATR Buffer", DefaultValue = 0.18, MinValue = 0.0, MaxValue = 1.0, Group = "Execution")]
        public double SlAtrBuffer { get; set; }

        [Parameter("Min Stop ATR", DefaultValue = 0.20, MinValue = 0.05, MaxValue = 1.50, Group = "Execution")]
        public double MinStopAtr { get; set; }

        [Parameter("Max Spread / M15 ATR", DefaultValue = 0.05, MinValue = 0.005, MaxValue = 0.25, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 0.45, MinValue = 0.10, MaxValue = 1.50, Group = "Execution")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Margin Safety %", DefaultValue = 85.0, MinValue = 25.0, MaxValue = 95.0, Group = "Execution")]
        public double MarginSafetyPercent { get; set; }

        [Parameter("Candidate Life M5 Bars", DefaultValue = 96, MinValue = 12, MaxValue = 288, Group = "M5 Confirmation")]
        public int CandidateLifeM5Bars { get; set; }

        [Parameter("Cooldown M5 Bars", DefaultValue = 9, MinValue = 0, MaxValue = 144, Group = "M5 Confirmation")]
        public int CooldownM5Bars { get; set; }

        [Parameter("M5 Rules Needed", DefaultValue = 2, MinValue = 1, MaxValue = 4, Group = "M5 Confirmation")]
        public int M5RulesNeeded { get; set; }

        [Parameter("M5 Break Lookback", DefaultValue = 3, MinValue = 2, MaxValue = 8, Group = "M5 Confirmation")]
        public int M5BreakLookback { get; set; }

        [Parameter("M5 Wick Min %", DefaultValue = 0.22, MinValue = 0.10, MaxValue = 0.70, Group = "M5 Confirmation")]
        public double M5WickMinRatio { get; set; }

        [Parameter("M5 Body Min %", DefaultValue = 0.42, MinValue = 0.15, MaxValue = 0.90, Group = "M5 Confirmation")]
        public double M5BodyMinRatio { get; set; }

        [Parameter("Block London Entries", DefaultValue = true, Group = "Session")]
        public bool BlockLondonEntries { get; set; }

        [Parameter("Block Friday Late", DefaultValue = true, Group = "Session")]
        public bool BlockFridayLate { get; set; }

        [Parameter("Friday Block UTC Hour", DefaultValue = 18, MinValue = 12, MaxValue = 23, Group = "Session")]
        public int FridayBlockUtcHour { get; set; }

        private Bars _m15;
        private Bars _h1;
        private DateTime _lastM15ProcessedOpenTime = DateTime.MinValue;
        private DateTime _day;
        private double _dayStartBalance;
        private double _dayNet;
        private int _tradesToday;
        private int _consecutiveLosses;
        private int _lastTradeM5Index = -100000;
        private bool _entryInProgress;

        private readonly List<SetupCandidate> _candidates = new List<SetupCandidate>();
        private readonly HashSet<string> _observedKeys = new HashSet<string>();
        private readonly HashSet<string> _tradedKeys = new HashSet<string>();
        private readonly Dictionary<long, TradeMeta> _openMeta = new Dictionary<long, TradeMeta>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>();
        private readonly Dictionary<string, PatternStats> _sessionStats = new Dictionary<string, PatternStats>();

        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            Positions.Closed += OnPositionClosed;
            ResetDay();
            RestoreDailyStateFromHistory();
            Print("VERSION xauusd_4 v4.0.0-predictive-harmonic-commercial");
            Print("[ARCH] H1 soft regime + M15 confirmed XABC -> projected D/PRZ + M5 closed-bar execution");
            Print("[PATTERNS] Gartley Bat Butterfly Crab DeepCrab ABCD + explicit FibPullback fallback");
            Print("[SAFETY] fixed-risk SL/TP + daily loss + consecutive loss + account-wide symbol exposure lock");
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            foreach (var kv in _stats)
            {
                PatternStats s = kv.Value;
                double wr = s.Trades > 0 ? 100.0 * s.Wins / s.Trades : 0.0;
                Print("[STATS] {0} trades={1} wins={2} losses={3} WR={4:F1}% net={5:F2}", kv.Key, s.Trades, s.Wins, s.Losses, wr, s.Net);
            }
            foreach (var kv in _sessionStats)
            {
                PatternStats s = kv.Value;
                double wr = s.Trades > 0 ? 100.0 * s.Wins / s.Trades : 0.0;
                Print("[SESSION] {0} trades={1} wins={2} losses={3} WR={4:F1}% net={5:F2}", kv.Key, s.Trades, s.Wins, s.Losses, wr, s.Net);
            }
        }

        protected override void OnBarClosed()
        {
            if (!TradingEnabled || Bars.Count < 50 || _m15 == null || _m15.Count < 140)
                return;

            if (Server.Time.Date != _day)
                ResetDay();

            EnsureProtectionIntegrity();
            int m5Index = Bars.Count - 1;
            if (m5Index < Math.Max(12, M5BreakLookback + 2))
                return;

            ProcessNewM15Bar(m5Index);
            PruneCandidates(m5Index);

            if (HasAnySymbolExposure())
                return;
            if (DailyLossLocked() || _tradesToday >= MaxTradesPerDay || _consecutiveLosses >= MaxConsecutiveLosses)
                return;
            if (m5Index - _lastTradeM5Index < CooldownM5Bars)
                return;
            if (BlockFridayLate && Server.Time.DayOfWeek == DayOfWeek.Friday && Server.Time.Hour >= FridayBlockUtcHour)
                return;

            TryConfirmBestCandidate(m5Index);
        }

        private void ProcessNewM15Bar(int m5Index)
        {
            int index = _m15.Count - 2;
            if (index < Math.Max(130, PivotLeft + PivotRight + 20))
                return;

            DateTime stamp = _m15.OpenTimes[index];
            if (stamp <= _lastM15ProcessedOpenTime)
                return;
            _lastM15ProcessedOpenTime = stamp;

            double atr = Atr(_m15, index, 14);
            if (atr <= Symbol.PipSize)
                return;

            List<Pivot> pivots = BuildPivots(index);
            if (pivots.Count < 2)
                return;

            if (EnableHarmonics && pivots.Count >= 4)
                GenerateHarmonicCandidates(pivots, index, atr, m5Index);
            if (EnableFibPullback)
                GenerateFibPullbackCandidate(pivots, index, atr, m5Index);
        }

        private void GenerateHarmonicCandidates(List<Pivot> pivots, int m15Index, double atr, int m5Index)
        {
            PatternSpec[] specs = PatternSpecs();
            int firstEnd = Math.Max(3, pivots.Count - 7);
            for (int end = firstEnd; end < pivots.Count; end++)
            {
                Pivot x = pivots[end - 3];
                Pivot a = pivots[end - 2];
                Pivot b = pivots[end - 1];
                Pivot c = pivots[end];
                if (m15Index - c.Index > MaxPatternAgeM15Bars)
                    continue;

                bool bullish = !x.IsHigh && a.IsHigh && !b.IsHigh && c.IsHigh;
                bool bearish = x.IsHigh && !a.IsHigh && b.IsHigh && !c.IsHigh;
                if (!bullish && !bearish)
                    continue;

                double xa = Math.Abs(a.Price - x.Price);
                double ab = Math.Abs(b.Price - a.Price);
                double bc = Math.Abs(c.Price - b.Price);
                if (xa < atr * MinXaAtr || ab <= Symbol.PipSize || bc <= Symbol.PipSize)
                    continue;

                double bRatio = ab / xa;
                double cRatio = bc / ab;
                TradeType direction = bullish ? TradeType.Buy : TradeType.Sell;

                for (int i = 0; i < specs.Length; i++)
                {
                    PatternSpec spec = specs[i];
                    double bTolerance = RatioTolerancePercent / 100.0;
                    if (bRatio < spec.BMin - bTolerance || bRatio > spec.BMax + bTolerance)
                        continue;
                    if (cRatio < 0.30 || cRatio > 1.05)
                        continue;

                    double dXa = bullish ? a.Price - xa * spec.DXa : a.Price + xa * spec.DXa;
                    double bc1 = bullish ? c.Price - bc * spec.BcExtMin : c.Price + bc * spec.BcExtMin;
                    double bc2 = bullish ? c.Price - bc * spec.BcExtMax : c.Price + bc * spec.BcExtMax;
                    double bcLow = Math.Min(bc1, bc2);
                    double bcHigh = Math.Max(bc1, bc2);
                    double dBc = Clamp(dXa, bcLow, bcHigh);
                    double dAbcd = bullish ? c.Price - ab : c.Price + ab;

                    double pMin = Math.Min(dXa, Math.Min(dBc, dAbcd));
                    double pMax = Math.Max(dXa, Math.Max(dBc, dAbcd));
                    double dispersion = pMax - pMin;
                    if (dispersion > atr * MaxProjectionDispersionAtr)
                        continue;

                    double center = (dXa * 0.50) + (dBc * 0.30) + (dAbcd * 0.20);
                    double halfWidth = Math.Max(atr * PrzAtrHalfWidth, dispersion * 0.60);
                    double zoneLow = center - halfWidth;
                    double zoneHigh = center + halfWidth;

                    double bScore = RatioWindowScore(bRatio, spec.BMin, spec.BMax, 20.0);
                    double cScore = RatioWindowScore(cRatio, 0.382, 0.886, 10.0);
                    double bcDistance = dXa < bcLow ? bcLow - dXa : dXa > bcHigh ? dXa - bcHigh : 0.0;
                    double bcScore = Clamp(15.0 - 15.0 * bcDistance / Math.Max(atr * 1.25, Symbol.PipSize), 0.0, 15.0);
                    double abcdDistance = Math.Abs(dAbcd - dXa);
                    double abcdScale = Math.Max(atr * 1.50, xa * 0.12);
                    double abcdScore = Clamp(15.0 - 15.0 * abcdDistance / abcdScale, 0.0, 15.0);
                    double geometry = bScore + cScore + bcScore + abcdScore;
                    if (geometry < HarmonicGeometryMin)
                        continue;

                    double h1Score = H1RegimeScore(direction);
                    double preScore = geometry + h1Score;
                    double stopAnchor;
                    if (spec.StopBeyondX)
                        stopAnchor = x.Price;
                    else
                        stopAnchor = bullish ? zoneLow : zoneHigh;

                    string key = spec.Name + "|" + direction + "|" + x.Index + "|" + a.Index + "|" + b.Index + "|" + c.Index;
                    AddCandidate(new SetupCandidate(
                        key, spec.Name, direction, true, zoneLow, zoneHigh, stopAnchor, a.Price,
                        atr, preScore, geometry, h1Score, m5Index, m5Index + CandidateLifeM5Bars));
                }

                AddAbcdCandidate(x, a, b, c, bullish, atr, m5Index);
            }
        }

        private void AddAbcdCandidate(Pivot x, Pivot a, Pivot b, Pivot c, bool bullish, double atr, int m5Index)
        {
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            if (ab <= Symbol.PipSize || bc <= Symbol.PipSize)
                return;

            double cRatio = bc / ab;
            if (cRatio < 0.382 - RatioTolerancePercent / 100.0 || cRatio > 0.886 + RatioTolerancePercent / 100.0)
                return;

            TradeType direction = bullish ? TradeType.Buy : TradeType.Sell;
            double d = bullish ? c.Price - ab : c.Price + ab;
            double zoneHalf = atr * Math.Max(PrzAtrHalfWidth, 0.15);
            double geometry = RatioWindowScore(cRatio, 0.382, 0.886, 25.0) + 20.0;
            double h1Score = H1RegimeScore(direction);
            double preScore = geometry + h1Score;
            string key = "ABCD|" + direction + "|" + a.Index + "|" + b.Index + "|" + c.Index;
            AddCandidate(new SetupCandidate(
                key, "ABCD", direction, true, d - zoneHalf, d + zoneHalf,
                bullish ? d - zoneHalf : d + zoneHalf, a.Price,
                atr, preScore, geometry, h1Score, m5Index, m5Index + CandidateLifeM5Bars));
        }

        private void GenerateFibPullbackCandidate(List<Pivot> pivots, int index, double atr, int m5Index)
        {
            if (pivots.Count < 2)
                return;
            Pivot start = pivots[pivots.Count - 2];
            Pivot end = pivots[pivots.Count - 1];
            if (start.IsHigh == end.IsHigh || index - end.Index > MaxPatternAgeM15Bars)
                return;

            double impulse = Math.Abs(end.Price - start.Price);
            if (impulse < atr * MinImpulseAtr)
                return;

            TradeType direction = end.IsHigh ? TradeType.Buy : TradeType.Sell;
            double zoneLow, zoneHigh, stopAnchor;
            if (direction == TradeType.Buy)
            {
                zoneLow = end.Price - impulse * FibDeep;
                zoneHigh = end.Price - impulse * FibShallow;
                stopAnchor = end.Price - impulse * StopFib;
            }
            else
            {
                zoneLow = end.Price + impulse * FibShallow;
                zoneHigh = end.Price + impulse * FibDeep;
                stopAnchor = end.Price + impulse * StopFib;
            }

            double h1 = H1RegimeScore(direction);
            double structure = Clamp(5.0 + (impulse / atr - MinImpulseAtr) * 4.0, 5.0, 15.0);
            double preScore = 30.0 + structure + h1;
            string key = "FibPullback|" + direction + "|" + start.Index + "|" + end.Index;
            AddCandidate(new SetupCandidate(
                key, "FibPullback", direction, false, zoneLow, zoneHigh, stopAnchor, end.Price,
                atr, preScore, 30.0 + structure, h1, m5Index, m5Index + CandidateLifeM5Bars));
        }

        private void AddCandidate(SetupCandidate c)
        {
            if (_observedKeys.Contains(c.Key) || _tradedKeys.Contains(c.Key))
                return;
            _observedKeys.Add(c.Key);
            _candidates.Add(c);
            if (DebugLogging)
                Print("[CANDIDATE] {0} {1} pre={2:F1} geo={3:F1} H1={4:F1} PRZ={5:F2}-{6:F2}", c.Tag, c.Direction, c.PreScore, c.GeometryScore, c.H1Score, c.ZoneLow, c.ZoneHigh);
            while (_candidates.Count > 16)
                _candidates.RemoveAt(0);
        }

        private void PruneCandidates(int m5Index)
        {
            double low = Bars.LowPrices[m5Index];
            double high = Bars.HighPrices[m5Index];
            for (int i = _candidates.Count - 1; i >= 0; i--)
            {
                SetupCandidate c = _candidates[i];
                bool expired = m5Index > c.ExpiresM5Index;
                bool invalidated = c.Direction == TradeType.Buy
                    ? low < c.StopAnchor - c.M15Atr * SlAtrBuffer
                    : high > c.StopAnchor + c.M15Atr * SlAtrBuffer;
                if (expired || invalidated || _tradedKeys.Contains(c.Key))
                    _candidates.RemoveAt(i);
            }
        }

        private void TryConfirmBestCandidate(int index)
        {
            if (_candidates.Count == 0)
                return;

            SetupCandidate best = null;
            int bestRules = 0;
            double bestFinal = double.MinValue;
            for (int i = 0; i < _candidates.Count; i++)
            {
                SetupCandidate c = _candidates[i];
                if (!BarTouchesZone(Bars, index, c.ZoneLow, c.ZoneHigh) && !c.Touched)
                    continue;
                if (!c.Touched)
                {
                    c.Touched = true;
                    c.TouchM5Index = index;
                    if (DebugLogging) Print("[PRZ TOUCH] {0} {1} pre={2:F1}", c.Tag, c.Direction, c.PreScore);
                }

                int rules = ConfirmationRules(c.Direction, index);
                if (rules < M5RulesNeeded)
                    continue;

                double close = Bars.ClosePrices[index];
                double distance = close < c.ZoneLow ? c.ZoneLow - close : close > c.ZoneHigh ? close - c.ZoneHigh : 0.0;
                double distanceAtr = distance / Math.Max(c.M15Atr, Symbol.PipSize);
                if (distanceAtr > MaxEntryDistanceAtr)
                    continue;

                double m5Score = rules * 5.0;
                double finalScore = c.PreScore + m5Score;
                if (finalScore < FinalScoreMin)
                    continue;
                if (finalScore > bestFinal)
                {
                    best = c;
                    bestRules = rules;
                    bestFinal = finalScore;
                }
            }

            if (best != null)
            {
                if (DebugLogging) Print("[M5 CONFIRM] {0} {1} pre={2:F1} rules={3}/4 final={4:F1}", best.Tag, best.Direction, best.PreScore, bestRules, bestFinal);
                if (TryExecute(best, bestFinal, index, bestRules))
                    _candidates.Clear();
            }
        }

        private int ConfirmationRules(TradeType direction, int index)
        {
            double open = Bars.OpenPrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double close = Bars.ClosePrices[index];
            double range = Math.Max(high - low, Symbol.PipSize);
            double body = Math.Abs(close - open);
            double closePos = (close - low) / range;
            double prevOpen = Bars.OpenPrices[index - 1];
            double prevClose = Bars.ClosePrices[index - 1];
            bool directional = direction == TradeType.Buy ? close > open : close < open;
            if (!directional)
                return 0;

            bool engulfing, rejection, microBreak, momentum;
            if (direction == TradeType.Buy)
            {
                engulfing = prevClose < prevOpen && open <= prevClose && close >= prevOpen;
                double lowerWick = Math.Min(open, close) - low;
                rejection = lowerWick / range >= M5WickMinRatio && closePos >= 0.60;
                double priorHigh = Bars.HighPrices[index - 1];
                for (int k = 2; k <= M5BreakLookback; k++) priorHigh = Math.Max(priorHigh, Bars.HighPrices[index - k]);
                microBreak = close > priorHigh;
                momentum = body / range >= M5BodyMinRatio && closePos >= 0.65;
            }
            else
            {
                engulfing = prevClose > prevOpen && open >= prevClose && close <= prevOpen;
                double upperWick = high - Math.Max(open, close);
                rejection = upperWick / range >= M5WickMinRatio && closePos <= 0.40;
                double priorLow = Bars.LowPrices[index - 1];
                for (int k = 2; k <= M5BreakLookback; k++) priorLow = Math.Min(priorLow, Bars.LowPrices[index - k]);
                microBreak = close < priorLow;
                momentum = body / range >= M5BodyMinRatio && closePos <= 0.35;
            }

            int rules = 0;
            if (engulfing) rules++;
            if (rejection) rules++;
            if (microBreak) rules++;
            if (momentum) rules++;
            return rules;
        }

        private bool TryExecute(SetupCandidate c, double finalScore, int m5Index, int confirmRules)
        {
            if (BlockLondonEntries && Server.Time.Hour >= 7 && Server.Time.Hour < 13)
                return false;
            if (_entryInProgress || HasAnySymbolExposure())
                return false;

            double spreadRatio = (Symbol.Ask - Symbol.Bid) / Math.Max(c.M15Atr, Symbol.PipSize);
            if (spreadRatio > MaxSpreadAtrRatio)
                return false;

            _entryInProgress = true;
            try
            {
                if (HasAnySymbolExposure())
                    return false;

                double entry = c.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                double stop = c.Direction == TradeType.Buy
                    ? c.StopAnchor - SlAtrBuffer * c.M15Atr
                    : c.StopAnchor + SlAtrBuffer * c.M15Atr;
                double slDistance = c.Direction == TradeType.Buy ? entry - stop : stop - entry;
                if (slDistance <= Symbol.PipSize)
                    return false;

                double target;
                if (c.IsHarmonic)
                {
                    double adRange = Math.Abs(c.TargetReference - entry);
                    double rewardDistance = adRange * TargetAdFib;
                    target = c.Direction == TradeType.Buy ? entry + rewardDistance : entry - rewardDistance;
                }
                else
                {
                    target = c.TargetReference;
                }

                double tpDistance = c.Direction == TradeType.Buy ? target - entry : entry - target;
                if (tpDistance <= Symbol.PipSize)
                    return false;

                double slPips = slDistance / Symbol.PipSize;
                double tpPips = tpDistance / Symbol.PipSize;
                double rr = tpPips / slPips;
                double brokerMinSlPips = BrokerMinDistancePips(entry, Symbol.MinStopLossDistance);
                double brokerMinTpPips = BrokerMinDistancePips(entry, Symbol.MinTakeProfitDistance);
                double requiredSlPips = Math.Max(brokerMinSlPips * 1.10, MinStopAtr * c.M15Atr / Symbol.PipSize);
                double requiredTpPips = brokerMinTpPips * 1.10;
                if (slPips < requiredSlPips || tpPips < requiredTpPips)
                    return false;
                if (rr < MinimumRiskReward || rr > MaxAllowedRR)
                    return false;

                double budget = Account.Equity * RiskPercent / 100.0;
                double volume = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);
                if (double.IsNaN(volume) || double.IsInfinity(volume) || volume <= 0)
                    return false;
                volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
                if (volume < Symbol.VolumeInUnitsMin)
                    return false;
                if (volume > Symbol.VolumeInUnitsMax)
                    volume = Symbol.VolumeInUnitsMax;

                double risk = Symbol.AmountRisked(volume, slPips);
                if (double.IsNaN(risk) || risk <= 0 || risk > budget * 1.03)
                    return false;
                double margin = Symbol.GetEstimatedMargin(c.Direction, volume);
                if (margin > Account.FreeMargin * MarginSafetyPercent / 100.0)
                    return false;

                string session = SessionName(Server.Time.Hour);
                string comment = c.Tag + "|S" + finalScore.ToString("F1") + "|R" + confirmRules;
                TradeResult result = ExecuteMarketOrder(c.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment);
                if (!result.IsSuccessful || result.Position == null)
                    return false;
                if (result.Position.StopLoss == null || result.Position.TakeProfit == null)
                {
                    ClosePosition(result.Position);
                    return false;
                }

                _tradedKeys.Add(c.Key);
                _tradesToday++;
                _lastTradeM5Index = m5Index;
                _openMeta[result.Position.Id] = new TradeMeta(c.Tag, c.Direction, finalScore, rr, confirmRules, session);
                string statKey = c.Tag + "|" + c.Direction;
                PatternStats ps;
                if (!_stats.TryGetValue(statKey, out ps)) { ps = new PatternStats(); _stats[statKey] = ps; }
                ps.Trades++;
                PatternStats ss;
                if (!_sessionStats.TryGetValue(session, out ss)) { ss = new PatternStats(); _sessionStats[session] = ss; }
                ss.Trades++;
                Print("[OPEN] {0} {1} session={2} score={3:F1} rules={4}/4 vol={5} entry={6:F2} SL={7:F1}p TP={8:F1}p RR={9:F2}", c.Tag, c.Direction, session, finalScore, confirmRules, volume, result.Position.EntryPrice, slPips, tpPips, rr);
                return true;
            }
            finally
            {
                _entryInProgress = false;
            }
        }

        private double H1RegimeScore(TradeType direction)
        {
            if (_h1 == null || _h1.Count < 220)
                return 10.0;
            int i = _h1.Count - 2;
            double ema50 = Ema(_h1, i, 50);
            double ema50Prev = Ema(_h1, i - 4, 50);
            double ema200 = Ema(_h1, i, 200);
            double close = _h1.ClosePrices[i];
            double atr14 = Atr(_h1, i, 14);
            double atr50 = Atr(_h1, i, 50);
            bool bull = close > ema50 && ema50 > ema200 && ema50 >= ema50Prev;
            bool bear = close < ema50 && ema50 < ema200 && ema50 <= ema50Prev;
            bool aligned = direction == TradeType.Buy ? bull : bear;
            bool opposite = direction == TradeType.Buy ? bear : bull;
            double score = aligned ? 18.0 : opposite ? 5.0 : 11.0;
            if (atr50 > Symbol.PipSize && atr14 / atr50 > 1.10)
                score += aligned ? 2.0 : 0.5;
            return Clamp(score, 0.0, 20.0);
        }

        private PatternSpec[] PatternSpecs()
        {
            return new PatternSpec[]
            {
                new PatternSpec("Gartley", 0.58, 0.66, 0.786, 1.13, 1.618, true),
                new PatternSpec("Bat", 0.382, 0.50, 0.886, 1.618, 2.618, true),
                new PatternSpec("Butterfly", 0.74, 0.82, 1.27, 1.618, 2.24, false),
                new PatternSpec("Crab", 0.382, 0.618, 1.618, 2.618, 3.618, false),
                new PatternSpec("DeepCrab", 0.84, 0.92, 1.618, 2.0, 3.618, false)
            };
        }

        private double RatioWindowScore(double value, double min, double max, double points)
        {
            if (value >= min && value <= max)
                return points;
            double tolerance = RatioTolerancePercent / 100.0;
            double distance = value < min ? min - value : value - max;
            return Clamp(points * (1.0 - distance / Math.Max(tolerance, 0.0001)), 0.0, points);
        }

        private List<Pivot> BuildPivots(int end)
        {
            var pivots = new List<Pivot>();
            int start = Math.Max(PivotLeft, end - PivotLookback);
            int last = end - PivotRight;
            for (int i = start; i <= last; i++)
            {
                bool high = IsPivotHigh(i);
                bool low = IsPivotLow(i);
                if (high == low)
                    continue;
                Pivot p = new Pivot(i, high ? _m15.HighPrices[i] : _m15.LowPrices[i], high);
                if (pivots.Count == 0)
                {
                    pivots.Add(p);
                    continue;
                }
                Pivot prev = pivots[pivots.Count - 1];
                if (prev.IsHigh == p.IsHigh)
                {
                    bool replace = p.IsHigh ? p.Price > prev.Price : p.Price < prev.Price;
                    if (replace)
                        pivots[pivots.Count - 1] = p;
                }
                else
                {
                    pivots.Add(p);
                    if (pivots.Count > 30)
                        pivots.RemoveAt(0);
                }
            }
            return pivots;
        }

        private bool IsPivotHigh(int i)
        {
            double v = _m15.HighPrices[i];
            for (int k = 1; k <= PivotLeft; k++) if (_m15.HighPrices[i - k] >= v) return false;
            for (int k = 1; k <= PivotRight; k++) if (_m15.HighPrices[i + k] > v) return false;
            return true;
        }

        private bool IsPivotLow(int i)
        {
            double v = _m15.LowPrices[i];
            for (int k = 1; k <= PivotLeft; k++) if (_m15.LowPrices[i - k] <= v) return false;
            for (int k = 1; k <= PivotRight; k++) if (_m15.LowPrices[i + k] < v) return false;
            return true;
        }

        private void EnsureProtectionIntegrity()
        {
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (p.StopLoss != null && p.TakeProfit != null)
                    continue;
                Print("[FAILSAFE] Missing protection PID={0}; closing", p.Id);
                TradeResult r = ClosePosition(p);
                if (!r.IsSuccessful)
                    Print("[FAILSAFE FAIL] PID={0} error={1}", p.Id, r.Error);
            }
        }

        private bool HasAnySymbolExposure()
        {
            foreach (Position p in Positions)
                if (p.SymbolName == SymbolName)
                    return true;
            foreach (PendingOrder order in PendingOrders)
                if (order.SymbolName == SymbolName)
                    return true;
            return false;
        }

        private void RestoreDailyStateFromHistory()
        {
            double net = 0.0;
            int trades = 0;
            var today = new List<HistoricalTrade>();
            foreach (HistoricalTrade t in History.FindAll(BotLabel, SymbolName))
            {
                if (t.ClosingTime.Date == _day)
                {
                    net += t.NetProfit;
                    today.Add(t);
                }
                if (t.EntryTime.Date == _day)
                    trades++;
            }
            today.Sort(delegate(HistoricalTrade a, HistoricalTrade b) { return a.ClosingTime.CompareTo(b.ClosingTime); });
            int streak = 0;
            for (int i = 0; i < today.Count; i++)
            {
                if (today[i].NetProfit < 0) streak++;
                else if (today[i].NetProfit > 0) streak = 0;
            }
            _consecutiveLosses = streak;
            _dayNet = net;
            _tradesToday = trades;
            _dayStartBalance = Account.Balance - _dayNet;
            if (_dayStartBalance <= 0)
                _dayStartBalance = Account.Balance;
        }

        private double CurrentBotFloatingNet()
        {
            double net = 0.0;
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
                net += p.NetProfit;
            return net;
        }

        private bool DailyLossLocked()
        {
            double cap = _dayStartBalance * MaxDailyLossPercent / 100.0;
            return -(_dayNet + CurrentBotFloatingNet()) >= cap;
        }

        private void ResetDay()
        {
            _day = Server.Time.Date;
            _dayStartBalance = Account.Balance;
            _dayNet = 0.0;
            _tradesToday = 0;
            _consecutiveLosses = 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != BotLabel)
                return;
            if (Server.Time.Date != _day)
                ResetDay();

            _dayNet += p.NetProfit;
            if (p.NetProfit < 0)
                _consecutiveLosses++;
            else if (p.NetProfit > 0)
                _consecutiveLosses = 0;

            TradeMeta meta;
            if (!_openMeta.TryGetValue(p.Id, out meta))
                return;
            _openMeta.Remove(p.Id);

            string key = meta.Tag + "|" + meta.Direction;
            PatternStats s;
            if (!_stats.TryGetValue(key, out s)) { s = new PatternStats(); _stats[key] = s; }
            if (p.NetProfit > 0) s.Wins++; else s.Losses++;
            s.Net += p.NetProfit;

            PatternStats session;
            if (!_sessionStats.TryGetValue(meta.Session, out session)) { session = new PatternStats(); _sessionStats[meta.Session] = session; }
            if (p.NetProfit > 0) session.Wins++; else session.Losses++;
            session.Net += p.NetProfit;

            Print("[CLOSE] {0} {1} session={2} score={3:F1} rules={4}/4 RR={5:F2} net={6:F2} reason={7}", meta.Tag, meta.Direction, meta.Session, meta.Score, meta.ConfirmRules, meta.Rr, p.NetProfit, args.Reason);
        }

        private bool BarTouchesZone(Bars bars, int index, double zoneLow, double zoneHigh)
        {
            return bars.LowPrices[index] <= zoneHigh && bars.HighPrices[index] >= zoneLow;
        }

        private double BrokerMinDistancePips(double price, double distance)
        {
            if (distance <= 0) return 0.0;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips) return distance;
            return (price * distance / 100.0) / Symbol.PipSize;
        }

        private double Atr(Bars bars, int end, int period)
        {
            if (end < period + 1) return 0.0;
            double sum = 0.0;
            for (int i = end - period + 1; i <= end; i++)
            {
                double prevClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(bars.HighPrices[i] - bars.LowPrices[i], Math.Max(Math.Abs(bars.HighPrices[i] - prevClose), Math.Abs(bars.LowPrices[i] - prevClose)));
                sum += tr;
            }
            return sum / period;
        }

        private double Ema(Bars bars, int end, int period)
        {
            int start = Math.Max(0, end - period * 4);
            double alpha = 2.0 / (period + 1.0);
            double ema = bars.ClosePrices[start];
            for (int i = start + 1; i <= end; i++)
                ema = alpha * bars.ClosePrices[i] + (1.0 - alpha) * ema;
            return ema;
        }

        private string SessionName(int hour)
        {
            if (hour < 7) return "Asia";
            if (hour < 13) return "London";
            if (hour < 21) return "NewYork";
            return "Late";
        }

        private double Clamp(double value, double min, double max)
        {
            return Math.Max(min, Math.Min(max, value));
        }

        private sealed class Pivot
        {
            public Pivot(int index, double price, bool isHigh) { Index = index; Price = price; IsHigh = isHigh; }
            public int Index;
            public double Price;
            public bool IsHigh;
        }

        private sealed class PatternSpec
        {
            public PatternSpec(string name, double bMin, double bMax, double dXa, double bcExtMin, double bcExtMax, bool stopBeyondX)
            {
                Name = name; BMin = bMin; BMax = bMax; DXa = dXa; BcExtMin = bcExtMin; BcExtMax = bcExtMax; StopBeyondX = stopBeyondX;
            }
            public string Name;
            public double BMin;
            public double BMax;
            public double DXa;
            public double BcExtMin;
            public double BcExtMax;
            public bool StopBeyondX;
        }

        private sealed class SetupCandidate
        {
            public SetupCandidate(string key, string tag, TradeType direction, bool isHarmonic, double zoneLow, double zoneHigh, double stopAnchor, double targetReference, double m15Atr, double preScore, double geometryScore, double h1Score, int createdM5Index, int expiresM5Index)
            {
                Key = key; Tag = tag; Direction = direction; IsHarmonic = isHarmonic; ZoneLow = zoneLow; ZoneHigh = zoneHigh; StopAnchor = stopAnchor; TargetReference = targetReference; M15Atr = m15Atr; PreScore = preScore; GeometryScore = geometryScore; H1Score = h1Score; CreatedM5Index = createdM5Index; ExpiresM5Index = expiresM5Index; Touched = false; TouchM5Index = -1;
            }
            public string Key;
            public string Tag;
            public TradeType Direction;
            public bool IsHarmonic;
            public double ZoneLow;
            public double ZoneHigh;
            public double StopAnchor;
            public double TargetReference;
            public double M15Atr;
            public double PreScore;
            public double GeometryScore;
            public double H1Score;
            public int CreatedM5Index;
            public int ExpiresM5Index;
            public bool Touched;
            public int TouchM5Index;
        }

        private sealed class TradeMeta
        {
            public TradeMeta(string tag, TradeType direction, double score, double rr, int confirmRules, string session)
            {
                Tag = tag; Direction = direction; Score = score; Rr = rr; ConfirmRules = confirmRules; Session = session;
            }
            public string Tag;
            public TradeType Direction;
            public double Score;
            public double Rr;
            public int ConfirmRules;
            public string Session;
        }

        private sealed class PatternStats
        {
            public int Trades;
            public int Wins;
            public int Losses;
            public double Net;
        }
    }
}
