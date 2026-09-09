using System;
using System.Collections.Generic;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class FibonacciXAUUSD2 : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "FIB_XAUUSD_2", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 3.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 10.0, Group = "Risk")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Minimum RR", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 5.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 6, MinValue = 1, MaxValue = 20, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Pivot Left", DefaultValue = 2, MinValue = 1, MaxValue = 8, Group = "M15 Structure")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right", DefaultValue = 1, MinValue = 1, MaxValue = 4, Group = "M15 Structure")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback", DefaultValue = 320, MinValue = 80, MaxValue = 1200, Group = "M15 Structure")]
        public int PivotLookback { get; set; }

        [Parameter("Min Leg ATR", DefaultValue = 0.45, MinValue = 0.1, MaxValue = 3.0, Group = "M15 Structure")]
        public double MinLegAtr { get; set; }

        [Parameter("Min Confidence", DefaultValue = 62.0, MinValue = 40, MaxValue = 95, Group = "Scoring")]
        public double MinConfidence { get; set; }

        [Parameter("H1 EMA Period", DefaultValue = 50, MinValue = 20, MaxValue = 200, Group = "Scoring")]
        public int H1EmaPeriod { get; set; }

        [Parameter("PRZ ATR Width", DefaultValue = 0.18, MinValue = 0.05, MaxValue = 0.75, Group = "Scoring")]
        public double PrzAtrWidth { get; set; }

        [Parameter("SL ATR Buffer", DefaultValue = 0.25, MinValue = 0.05, MaxValue = 1.5, Group = "Execution")]
        public double SlAtrBuffer { get; set; }

        [Parameter("Max Spread / M15 ATR", DefaultValue = 0.05, MinValue = 0.005, MaxValue = 0.25, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Cooldown M5 Bars", DefaultValue = 12, MinValue = 0, MaxValue = 144, Group = "M5 Confirmation")]
        public int CooldownM5Bars { get; set; }

        [Parameter("Confirm Window M5 Bars", DefaultValue = 9, MinValue = 1, MaxValue = 36, Group = "M5 Confirmation")]
        public int ConfirmWindowM5Bars { get; set; }

        [Parameter("M5 Rules Needed", DefaultValue = 2, MinValue = 1, MaxValue = 4, Group = "M5 Confirmation")]
        public int M5RulesNeeded { get; set; }

        [Parameter("M5 Break Lookback", DefaultValue = 3, MinValue = 2, MaxValue = 8, Group = "M5 Confirmation")]
        public int M5BreakLookback { get; set; }

        [Parameter("M5 Wick Min %", DefaultValue = 0.25, MinValue = 0.10, MaxValue = 0.70, Group = "M5 Confirmation")]
        public double M5WickMinRatio { get; set; }

        [Parameter("M5 Body Min %", DefaultValue = 0.45, MinValue = 0.15, MaxValue = 0.90, Group = "M5 Confirmation")]
        public double M5BodyMinRatio { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 0.45, MinValue = 0.10, MaxValue = 1.50, Group = "M5 Confirmation")]
        public double MaxEntryDistanceAtr { get; set; }

        private Bars _m15;
        private Bars _h1;
        private DateTime _lastM15ProcessedOpenTime = DateTime.MinValue;

        private DateTime _day;
        private double _dayStartBalance;
        private double _dayNet;
        private int _tradesToday;
        private int _lastTradeM5Index = -100000;
        private bool _entryInProgress;

        private ArmedSignal _armed;
        private readonly HashSet<string> _consumed = new HashSet<string>();
        private readonly Dictionary<long, TradeMeta> _openMeta = new Dictionary<long, TradeMeta>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>();
        private readonly Dictionary<string, PatternStats> _sessionStats = new Dictionary<string, PatternStats>();

        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            _h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            Positions.Closed += OnPositionClosed;
            ResetDay();

            Print("VERSION xauusd_2 v2.3.0-safety-abcd-sell-pruned");
            Print("[ARCH] M5 host -> M15 predictive XABC/PRZ -> M5 confirmation -> fixed-risk execution | hard no-duplicate/no-hedge exposure guard | ABCD Sell pruned");
            Print("[M5 RULES] engulfing | rejection-wick | micro-structure break | momentum body");
            Print("[SYMBOL] {0} Pip={1} Tick={2} VolMin={3} VolMax={4} Step={5}", SymbolName, Symbol.PipSize, Symbol.TickSize, Symbol.VolumeInUnitsMin, Symbol.VolumeInUnitsMax, Symbol.VolumeInUnitsStep);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;

            foreach (var kv in _stats)
            {
                var s = kv.Value;
                double wr = s.Trades > 0 ? 100.0 * s.Wins / s.Trades : 0.0;
                Print("[STATS] {0} trades={1} wins={2} losses={3} WR={4:F1}% net={5:F2}", kv.Key, s.Trades, s.Wins, s.Losses, wr, s.Net);
            }

            foreach (var kv in _sessionStats)
            {
                var s = kv.Value;
                double wr = s.Trades > 0 ? 100.0 * s.Wins / s.Trades : 0.0;
                Print("[SESSION] {0} trades={1} wins={2} losses={3} WR={4:F1}% net={5:F2}", kv.Key, s.Trades, s.Wins, s.Losses, wr, s.Net);
            }
        }

        protected override void OnBarClosed()
        {
            if (!TradingEnabled || Bars.Count < 40 || _m15 == null || _m15.Count < 120)
                return;

            if (Server.Time.Date != _day)
                ResetDay();

            int m5Index = Bars.Count - 1;
            if (m5Index < 10)
                return;

            if (HasAnySymbolExposure())
            {
                if (DebugLogging)
                    Print("[EXPOSURE BLOCK] Existing {0} position or pending order detected; no new signal may open.", SymbolName);
                return;
            }

            if (_armed != null)
            {
                if (m5Index > _armed.ExpiresM5Index)
                {
                    if (DebugLogging)
                        Print("[ARM EXPIRE] {0} {1} armConf={2:F1} ageM5={3}", _armed.Candidate.Name, _armed.Candidate.Direction, _armed.Confidence, m5Index - _armed.ArmedM5Index);
                    _armed = null;
                }
                else if (m5Index > _armed.ArmedM5Index)
                {
                    if (TryConfirmArmedM5(m5Index))
                    {
                        _armed = null;
                        return;
                    }
                }

                if (_armed != null)
                    return;
            }

            if (DailyLossLocked())
                return;
            if (_tradesToday >= MaxTradesPerDay)
                return;
            if (m5Index - _lastTradeM5Index < CooldownM5Bars)
                return;

            ProcessNewM15Bar(m5Index);
        }

        private void ProcessNewM15Bar(int m5Index)
        {
            int index = _m15.Count - 2;
            if (index < Math.Max(120, PivotLeft + PivotRight + 10))
                return;

            DateTime stamp = _m15.OpenTimes[index];
            if (stamp <= _lastM15ProcessedOpenTime)
                return;
            _lastM15ProcessedOpenTime = stamp;

            double atr = Atr(_m15, index, 14);
            if (atr <= Symbol.PipSize)
                return;

            double spreadRatio = (Symbol.Ask - Symbol.Bid) / atr;
            if (spreadRatio > MaxSpreadAtrRatio)
            {
                if (DebugLogging)
                    Print("[REJECT] M15={0:u} spreadATR={1:F4}", stamp, spreadRatio);
                return;
            }

            List<Pivot> pivots = BuildPivots(index);
            if (pivots.Count < 4)
                return;

            Pivot x = pivots[pivots.Count - 4];
            Pivot a = pivots[pivots.Count - 3];
            Pivot b = pivots[pivots.Count - 2];
            Pivot c = pivots[pivots.Count - 1];

            if (!Alternating(x, a, b, c))
                return;
            if (!LegsLargeEnough(x, a, b, c, atr))
                return;

            var candidates = BuildCandidates(x, a, b, c, atr);
            if (candidates.Count == 0)
                return;

            HarmonicCandidate best = null;
            double bestConfidence = double.MinValue;

            foreach (var candidate in candidates)
            {
                if (_consumed.Contains(candidate.Key))
                    continue;

                if (candidate.Name == "ABCD" && candidate.Direction == TradeType.Sell)
                {
                    if (DebugLogging)
                        Print("[PRUNE] ABCD Sell rejected by v2.3 expectancy filter key={0}", candidate.Key);
                    _consumed.Add(candidate.Key);
                    continue;
                }

                if (!BarTouchesPrz(candidate, index))
                    continue;

                double reversal = ReversalScore(_m15, candidate.Direction, index);
                double trend = H1TrendScore(candidate.Direction);
                double confidence = Clamp(candidate.ShapeScore * 0.50 + candidate.ConvergenceScore * 0.15 + reversal * 0.20 + trend * 0.15, 0, 100);

                if (DebugLogging)
                {
                    Print("[M15 CANDIDATE] {0} {1} M15={2:u} X={3:F2} A={4:F2} B={5:F2} C={6:F2} D*={7:F2} PRZ={8:F2}-{9:F2} shape={10:F1} conv={11:F1} rev={12:F1} h1={13:F1} conf={14:F1}",
                        candidate.Name, candidate.Direction, stamp, x.Price, a.Price, b.Price, c.Price, candidate.ProjectedD, candidate.ZoneLow, candidate.ZoneHigh,
                        candidate.ShapeScore, candidate.ConvergenceScore, reversal, trend, confidence);
                }

                if (reversal < 50.0 || confidence < MinConfidence)
                    continue;

                if (confidence > bestConfidence)
                {
                    best = candidate;
                    bestConfidence = confidence;
                }
            }

            if (best == null)
                return;

            _consumed.Add(best.Key);
            _armed = new ArmedSignal(best, bestConfidence, atr, m5Index, m5Index + ConfirmWindowM5Bars);

            Print("[ARM M5] {0} {1} armConf={2:F1} M15={3:u} m5Index={4} expires={5} PRZ={6:F2}-{7:F2}",
                best.Name, best.Direction, bestConfidence, stamp, m5Index, m5Index + ConfirmWindowM5Bars, best.ZoneLow, best.ZoneHigh);
        }

        private bool TryConfirmArmedM5(int index)
        {
            var a = _armed;
            if (a == null || index < Math.Max(M5BreakLookback + 2, 4))
                return false;

            double open = Bars.OpenPrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double close = Bars.ClosePrices[index];
            double range = Math.Max(high - low, Symbol.PipSize);
            double body = Math.Abs(close - open);
            double closePos = (close - low) / range;

            double distance = 0.0;
            if (close < a.Candidate.ZoneLow)
                distance = a.Candidate.ZoneLow - close;
            else if (close > a.Candidate.ZoneHigh)
                distance = close - a.Candidate.ZoneHigh;

            double distanceAtr = distance / Math.Max(a.M15Atr, Symbol.PipSize);
            if (distanceAtr > MaxEntryDistanceAtr)
            {
                Print("[ARM CANCEL] {0} {1} reason=too_far distanceATR={2:F2}", a.Candidate.Name, a.Candidate.Direction, distanceAtr);
                return true;
            }

            bool directional = a.Candidate.Direction == TradeType.Buy ? close > open : close < open;
            if (!directional)
            {
                if (DebugLogging)
                    Print("[M5 WAIT] {0} {1} rules=0 directional=false distanceATR={2:F2}", a.Candidate.Name, a.Candidate.Direction, distanceAtr);
                return false;
            }

            double prevOpen = Bars.OpenPrices[index - 1];
            double prevClose = Bars.ClosePrices[index - 1];

            bool engulfing;
            bool rejection;
            bool microBreak;
            bool momentum;

            if (a.Candidate.Direction == TradeType.Buy)
            {
                engulfing = close > open && prevClose < prevOpen && open <= prevClose && close >= prevOpen;

                double lowerWick = Math.Min(open, close) - low;
                rejection = lowerWick / range >= M5WickMinRatio && closePos >= 0.60;

                double priorHigh = Bars.HighPrices[index - 1];
                for (int k = 2; k <= M5BreakLookback; k++)
                    priorHigh = Math.Max(priorHigh, Bars.HighPrices[index - k]);
                microBreak = close > priorHigh;

                momentum = body / range >= M5BodyMinRatio && closePos >= 0.65;
            }
            else
            {
                engulfing = close < open && prevClose > prevOpen && open >= prevClose && close <= prevOpen;

                double upperWick = high - Math.Max(open, close);
                rejection = upperWick / range >= M5WickMinRatio && closePos <= 0.40;

                double priorLow = Bars.LowPrices[index - 1];
                for (int k = 2; k <= M5BreakLookback; k++)
                    priorLow = Math.Min(priorLow, Bars.LowPrices[index - k]);
                microBreak = close < priorLow;

                momentum = body / range >= M5BodyMinRatio && closePos <= 0.35;
            }

            int rules = 0;
            if (engulfing) rules++;
            if (rejection) rules++;
            if (microBreak) rules++;
            if (momentum) rules++;

            if (DebugLogging)
            {
                Print("[M5 CHECK] {0} {1} rules={2}/4 eng={3} wick={4} break={5} mom={6} distanceATR={7:F2}",
                    a.Candidate.Name, a.Candidate.Direction, rules, engulfing, rejection, microBreak, momentum, distanceAtr);
            }

            if (rules < M5RulesNeeded)
                return false;

            double confirmScore = rules * 25.0;
            double finalConfidence = Clamp(a.Confidence * 0.75 + confirmScore * 0.25, 0, 100);

            Print("[M5 CONFIRM] {0} {1} armConf={2:F1} rules={3}/4 finalConf={4:F1} distanceATR={5:F2}",
                a.Candidate.Name, a.Candidate.Direction, a.Confidence, rules, finalConfidence, distanceAtr);

            TryExecute(a.Candidate, finalConfidence, a.M15Atr, index, rules);
            return true;
        }

        private bool TryExecute(HarmonicCandidate c, double confidence, double atr, int m5Index, int confirmRules)
        {
            if (c.Name == "ABCD" && c.Direction == TradeType.Sell)
            {
                Print("[PRUNE BLOCK] ABCD Sell reached execution guard unexpectedly; order blocked.");
                return false;
            }

            if (_entryInProgress)
            {
                Print("[DUPLICATE BLOCK] Entry transaction already in progress; second order blocked.");
                return false;
            }

            if (HasAnySymbolExposure())
            {
                Print("[EXPOSURE BLOCK] Existing {0} exposure detected immediately before execution; order blocked.", SymbolName);
                return false;
            }

            _entryInProgress = true;
            try
            {
                return TryExecuteCore(c, confidence, atr, m5Index, confirmRules);
            }
            finally
            {
                _entryInProgress = false;
            }
        }

        private bool TryExecuteCore(HarmonicCandidate c, double confidence, double atr, int m5Index, int confirmRules)
        {
            double entry = c.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            double stop = c.Direction == TradeType.Buy ? c.ZoneLow - SlAtrBuffer * atr : c.ZoneHigh + SlAtrBuffer * atr;
            double target = c.CPrice;

            double slDistance = c.Direction == TradeType.Buy ? entry - stop : stop - entry;
            double tpDistance = c.Direction == TradeType.Buy ? target - entry : entry - target;
            if (slDistance <= Symbol.PipSize || tpDistance <= Symbol.PipSize)
            {
                if (DebugLogging)
                    Print("[REJECT] {0} target/stop geometry invalid entry={1:F2} stop={2:F2} target={3:F2}", c.Name, entry, stop, target);
                return false;
            }

            double slPips = slDistance / Symbol.PipSize;
            double tpPips = tpDistance / Symbol.PipSize;
            double rr = tpPips / slPips;
            if (rr < MinimumRiskReward)
            {
                if (DebugLogging)
                    Print("[REJECT] {0} poor RR={1:F2} min={2:F2}", c.Name, rr, MinimumRiskReward);
                return false;
            }

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
            if (margin > Account.FreeMargin * 0.85)
                return false;

            string session = SessionName(Server.Time.Hour);
            string comment = c.Name + "|" + confidence.ToString("F1") + "|M5R" + confirmRules;

            // Final broker-send guard. This is deliberately repeated inside the locked section.
            if (HasAnySymbolExposure())
            {
                Print("[EXPOSURE BLOCK] Exposure appeared during order preparation; broker order not sent.");
                return false;
            }

            TradeResult result = ExecuteMarketOrder(c.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[ORDER FAIL] {0} {1} error={2}", c.Name, c.Direction, result.Error);
                return false;
            }

            _tradesToday++;
            _lastTradeM5Index = m5Index;
            _openMeta[result.Position.Id] = new TradeMeta(c.Name, c.Direction, confidence, rr, confirmRules, session);

            string statKey = c.Name + "|" + c.Direction;
            if (!_stats.ContainsKey(statKey))
                _stats[statKey] = new PatternStats();
            _stats[statKey].Trades++;

            if (!_sessionStats.ContainsKey(session))
                _sessionStats[session] = new PatternStats();
            _sessionStats[session].Trades++;

            Print("[OPEN] {0} {1} session={2} conf={3:F1} m5Rules={4}/4 vol={5} entry={6:F2} SL={7:F1}p TP={8:F1}p RR={9:F2} PRZ={10:F2}-{11:F2}",
                c.Name, c.Direction, session, confidence, confirmRules, volume, result.Position.EntryPrice, slPips, tpPips, rr, c.ZoneLow, c.ZoneHigh);

            return true;
        }

        private List<HarmonicCandidate> BuildCandidates(Pivot x, Pivot a, Pivot b, Pivot c, double atr)
        {
            var list = new List<HarmonicCandidate>();

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0)
                return list;

            double bRatio = ab / xa;
            double bcRatio = bc / ab;
            double signXa = Math.Sign(a.Price - x.Price);
            double signBc = Math.Sign(c.Price - b.Price);
            TradeType direction = c.IsHigh ? TradeType.Buy : TradeType.Sell;

            AddNamed(list, "Gartley", direction, x, a, b, c, atr, bRatio, 0.55, 0.70, 0.786, 1.445, signXa, signBc, bc);
            AddNamed(list, "Bat", direction, x, a, b, c, atr, bRatio, 0.35, 0.55, 0.886, 2.00, signXa, signBc, bc);
            AddNamed(list, "Butterfly", direction, x, a, b, c, atr, bRatio, 0.70, 0.86, 1.27, 1.93, signXa, signBc, bc);
            AddNamed(list, "Crab", direction, x, a, b, c, atr, bRatio, 0.35, 0.70, 1.618, 3.12, signXa, signBc, bc);

            if (bcRatio >= 0.38 && bcRatio <= 0.90)
            {
                double d = c.Price - signBc * ab;
                double shape = 100.0 - Math.Min(45.0, Math.Abs(bcRatio - 0.618) / 0.282 * 45.0);
                double width = Math.Max(atr * PrzAtrWidth, atr * 0.10);

                list.Add(new HarmonicCandidate(
                    "ABCD",
                    direction,
                    d,
                    d - width,
                    d + width,
                    shape,
                    85.0,
                    c.Price,
                    Key("ABCD", x, a, b, c)));
            }

            return list;
        }

        private void AddNamed(
            List<HarmonicCandidate> list,
            string name,
            TradeType direction,
            Pivot x,
            Pivot a,
            Pivot b,
            Pivot c,
            double atr,
            double bRatio,
            double bMin,
            double bMax,
            double dRatio,
            double bcExtension,
            double signXa,
            double signBc,
            double bc)
        {
            if (bRatio < bMin || bRatio > bMax)
                return;

            double dXa = a.Price - signXa * dRatio * Math.Abs(a.Price - x.Price);
            double dBc = c.Price - signBc * bcExtension * bc;
            double center = (dXa + dBc) * 0.5;
            double disagreement = Math.Abs(dXa - dBc);

            double convergence = Clamp(
                100.0 - disagreement / Math.Max(atr * 1.8, Symbol.PipSize) * 100.0,
                0,
                100);

            double targetB = (bMin + bMax) * 0.5;
            double halfRange = Math.Max((bMax - bMin) * 0.5, 0.01);
            double shape = Clamp(100.0 - Math.Abs(bRatio - targetB) / halfRange * 35.0, 0, 100);

            double width = Math.Max(atr * PrzAtrWidth, disagreement * 0.5 + atr * 0.05);

            list.Add(new HarmonicCandidate(
                name,
                direction,
                center,
                center - width,
                center + width,
                shape,
                convergence,
                c.Price,
                Key(name, x, a, b, c)));
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

                var p = new Pivot(i, high ? _m15.HighPrices[i] : _m15.LowPrices[i], high);

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
                    if (pivots.Count > 16)
                        pivots.RemoveAt(0);
                }
            }

            return pivots;
        }

        private bool IsPivotHigh(int i)
        {
            double v = _m15.HighPrices[i];
            for (int k = 1; k <= PivotLeft; k++)
                if (_m15.HighPrices[i - k] >= v)
                    return false;
            for (int k = 1; k <= PivotRight; k++)
                if (_m15.HighPrices[i + k] > v)
                    return false;
            return true;
        }

        private bool IsPivotLow(int i)
        {
            double v = _m15.LowPrices[i];
            for (int k = 1; k <= PivotLeft; k++)
                if (_m15.LowPrices[i - k] <= v)
                    return false;
            for (int k = 1; k <= PivotRight; k++)
                if (_m15.LowPrices[i + k] < v)
                    return false;
            return true;
        }

        private bool Alternating(Pivot x, Pivot a, Pivot b, Pivot c)
        {
            return x.IsHigh != a.IsHigh && a.IsHigh != b.IsHigh && b.IsHigh != c.IsHigh;
        }

        private bool LegsLargeEnough(Pivot x, Pivot a, Pivot b, Pivot c, double atr)
        {
            double min = atr * MinLegAtr;
            return Math.Abs(a.Price - x.Price) >= min
                && Math.Abs(b.Price - a.Price) >= min
                && Math.Abs(c.Price - b.Price) >= min;
        }

        private bool BarTouchesPrz(HarmonicCandidate c, int index)
        {
            return _m15.LowPrices[index] <= c.ZoneHigh && _m15.HighPrices[index] >= c.ZoneLow;
        }

        private double ReversalScore(Bars bars, TradeType direction, int i)
        {
            if (i < 2)
                return 0;

            double o = bars.OpenPrices[i];
            double h = bars.HighPrices[i];
            double l = bars.LowPrices[i];
            double close = bars.ClosePrices[i];
            double range = Math.Max(h - l, Symbol.PipSize);
            double body = Math.Abs(close - o);
            double score = 0;

            if (direction == TradeType.Buy)
            {
                if (close > o) score += 35;
                if (close > bars.ClosePrices[i - 1]) score += 25;
                if ((Math.Min(o, close) - l) / range >= 0.20) score += 20;
                if ((close - l) / range >= 0.60) score += 20;
            }
            else
            {
                if (close < o) score += 35;
                if (close < bars.ClosePrices[i - 1]) score += 25;
                if ((h - Math.Max(o, close)) / range >= 0.20) score += 20;
                if ((h - close) / range >= 0.60) score += 20;
            }

            if (body / range < 0.08)
                score -= 10;

            return Clamp(score, 0, 100);
        }

        private double H1TrendScore(TradeType direction)
        {
            if (_h1 == null || _h1.Count < H1EmaPeriod + 8)
                return 50;

            int last = _h1.Count - 2;
            if (last < H1EmaPeriod + 3)
                return 50;

            double emaNow = Ema(_h1, last, H1EmaPeriod);
            double emaPrev = Ema(_h1, last - 3, H1EmaPeriod);
            double close = _h1.ClosePrices[last];

            bool priceAligned = direction == TradeType.Buy ? close >= emaNow : close <= emaNow;
            bool slopeAligned = direction == TradeType.Buy ? emaNow >= emaPrev : emaNow <= emaPrev;

            if (priceAligned && slopeAligned)
                return 100;
            if (priceAligned || slopeAligned)
                return 55;
            return 10;
        }

        private double Atr(Bars bars, int end, int period)
        {
            if (end < period + 1)
                return 0;

            double sum = 0;
            for (int i = end - period + 1; i <= end; i++)
            {
                double prevClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(
                    bars.HighPrices[i] - bars.LowPrices[i],
                    Math.Max(
                        Math.Abs(bars.HighPrices[i] - prevClose),
                        Math.Abs(bars.LowPrices[i] - prevClose)));

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

        private bool HasAnySymbolExposure()
        {
            // Account-wide symbol guard: prevents this cBot from duplicating or hedging
            // against an existing manual trade, another cBot, or its own position.
            foreach (var p in Positions)
                if (p.SymbolName == SymbolName)
                    return true;

            // Future-proofing: this version uses market orders only, but any existing
            // pending order on XAUUSD also blocks a new market entry.
            foreach (var order in PendingOrders)
                if (order.SymbolName == SymbolName)
                    return true;

            return false;
        }

        private bool DailyLossLocked()
        {
            double cap = _dayStartBalance * MaxDailyLossPercent / 100.0;
            return -_dayNet >= cap;
        }

        private void ResetDay()
        {
            _day = Server.Time.Date;
            _dayStartBalance = Account.Balance;
            _dayNet = 0;
            _tradesToday = 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != BotLabel)
                return;

            if (Server.Time.Date != _day)
                ResetDay();

            _dayNet += p.NetProfit;

            TradeMeta meta;
            if (!_openMeta.TryGetValue(p.Id, out meta))
                return;

            _openMeta.Remove(p.Id);

            string key = meta.Pattern + "|" + meta.Direction;
            PatternStats s;
            if (!_stats.TryGetValue(key, out s))
            {
                s = new PatternStats();
                _stats[key] = s;
            }

            if (p.NetProfit > 0)
                s.Wins++;
            else
                s.Losses++;
            s.Net += p.NetProfit;

            PatternStats session;
            if (!_sessionStats.TryGetValue(meta.Session, out session))
            {
                session = new PatternStats();
                _sessionStats[meta.Session] = session;
            }

            if (p.NetProfit > 0)
                session.Wins++;
            else
                session.Losses++;
            session.Net += p.NetProfit;

            Print("[CLOSE] {0} {1} session={2} conf={3:F1} m5Rules={4}/4 RR={5:F2} net={6:F2} reason={7}",
                meta.Pattern, meta.Direction, meta.Session, meta.Confidence, meta.ConfirmRules, meta.Rr, p.NetProfit, args.Reason);
        }

        private string SessionName(int hour)
        {
            if (hour < 7)
                return "Asia";
            if (hour < 13)
                return "London";
            if (hour < 21)
                return "NewYork";
            return "Late";
        }

        private string Key(string name, Pivot x, Pivot a, Pivot b, Pivot c)
        {
            return name + "|" + x.Index + "|" + a.Index + "|" + b.Index + "|" + c.Index;
        }

        private double Clamp(double v, double min, double max)
        {
            return Math.Max(min, Math.Min(max, v));
        }

        private sealed class Pivot
        {
            public Pivot(int index, double price, bool isHigh)
            {
                Index = index;
                Price = price;
                IsHigh = isHigh;
            }

            public int Index;
            public double Price;
            public bool IsHigh;
        }

        private sealed class HarmonicCandidate
        {
            public HarmonicCandidate(
                string name,
                TradeType direction,
                double d,
                double zoneLow,
                double zoneHigh,
                double shape,
                double convergence,
                double cPrice,
                string key)
            {
                Name = name;
                Direction = direction;
                ProjectedD = d;
                ZoneLow = zoneLow;
                ZoneHigh = zoneHigh;
                ShapeScore = shape;
                ConvergenceScore = convergence;
                CPrice = cPrice;
                Key = key;
            }

            public string Name;
            public TradeType Direction;
            public double ProjectedD;
            public double ZoneLow;
            public double ZoneHigh;
            public double ShapeScore;
            public double ConvergenceScore;
            public double CPrice;
            public string Key;
        }

        private sealed class ArmedSignal
        {
            public ArmedSignal(
                HarmonicCandidate candidate,
                double confidence,
                double m15Atr,
                int armedM5Index,
                int expiresM5Index)
            {
                Candidate = candidate;
                Confidence = confidence;
                M15Atr = m15Atr;
                ArmedM5Index = armedM5Index;
                ExpiresM5Index = expiresM5Index;
            }

            public HarmonicCandidate Candidate;
            public double Confidence;
            public double M15Atr;
            public int ArmedM5Index;
            public int ExpiresM5Index;
        }

        private sealed class TradeMeta
        {
            public TradeMeta(
                string pattern,
                TradeType direction,
                double confidence,
                double rr,
                int confirmRules,
                string session)
            {
                Pattern = pattern;
                Direction = direction;
                Confidence = confidence;
                Rr = rr;
                ConfirmRules = confirmRules;
                Session = session;
            }

            public string Pattern;
            public TradeType Direction;
            public double Confidence;
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
