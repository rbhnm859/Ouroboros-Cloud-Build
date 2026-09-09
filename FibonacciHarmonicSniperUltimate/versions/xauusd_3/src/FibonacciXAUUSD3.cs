using System;
using System.Collections.Generic;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class FibonacciXAUUSD3 : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "FIB_XAUUSD_3", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 3.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 10.0, Group = "Risk")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Minimum RR", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 5.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 8, MinValue = 1, MaxValue = 24, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Pre Score Min", DefaultValue = 42.0, MinValue = 25, MaxValue = 80, Group = "Scoring")]
        public double PreScoreMin { get; set; }

        [Parameter("Final Score Min", DefaultValue = 60.0, MinValue = 40, MaxValue = 90, Group = "Scoring")]
        public double FinalScoreMin { get; set; }

        [Parameter("M5 PreScore Floor", DefaultValue = 50.0, MinValue = 40, MaxValue = 80, Group = "Scoring")]
        public double M5PreScoreFloor { get; set; }

        [Parameter("Pivot Left", DefaultValue = 2, MinValue = 1, MaxValue = 8, Group = "M15 Structure")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right", DefaultValue = 1, MinValue = 1, MaxValue = 4, Group = "M15 Structure")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback", DefaultValue = 320, MinValue = 80, MaxValue = 1200, Group = "M15 Structure")]
        public int PivotLookback { get; set; }

        [Parameter("Min Impulse ATR", DefaultValue = 1.20, MinValue = 0.50, MaxValue = 6.0, Group = "M15 Structure")]
        public double MinImpulseAtr { get; set; }

        [Parameter("Fib Shallow", DefaultValue = 0.50, MinValue = 0.382, MaxValue = 0.70, Group = "Fibonacci")]
        public double FibShallow { get; set; }

        [Parameter("Fib Deep", DefaultValue = 0.786, MinValue = 0.618, MaxValue = 0.90, Group = "Fibonacci")]
        public double FibDeep { get; set; }

        [Parameter("Stop Fib", DefaultValue = 0.886, MinValue = 0.75, MaxValue = 1.05, Group = "Fibonacci")]
        public double StopFib { get; set; }

        [Parameter("SL ATR Buffer", DefaultValue = 0.12, MinValue = 0.0, MaxValue = 0.75, Group = "Execution")]
        public double SlAtrBuffer { get; set; }

        [Parameter("Max Spread / M15 ATR", DefaultValue = 0.05, MinValue = 0.005, MaxValue = 0.25, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Cooldown M5 Bars", DefaultValue = 9, MinValue = 0, MaxValue = 144, Group = "M5 Confirmation")]
        public int CooldownM5Bars { get; set; }

        [Parameter("Confirm Window M5 Bars", DefaultValue = 12, MinValue = 2, MaxValue = 48, Group = "M5 Confirmation")]
        public int ConfirmWindowM5Bars { get; set; }

        [Parameter("M5 Rules Needed", DefaultValue = 2, MinValue = 1, MaxValue = 4, Group = "M5 Confirmation")]
        public int M5RulesNeeded { get; set; }

        [Parameter("M5 Break Lookback", DefaultValue = 3, MinValue = 2, MaxValue = 8, Group = "M5 Confirmation")]
        public int M5BreakLookback { get; set; }

        [Parameter("M5 Wick Min %", DefaultValue = 0.22, MinValue = 0.10, MaxValue = 0.70, Group = "M5 Confirmation")]
        public double M5WickMinRatio { get; set; }

        [Parameter("M5 Body Min %", DefaultValue = 0.42, MinValue = 0.15, MaxValue = 0.90, Group = "M5 Confirmation")]
        public double M5BodyMinRatio { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 0.55, MinValue = 0.10, MaxValue = 1.50, Group = "M5 Confirmation")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Min Stop ATR", DefaultValue = 0.20, MinValue = 0.05, MaxValue = 1.50, Group = "Execution")]
        public double MinStopAtr { get; set; }

        [Parameter("Max Allowed RR", DefaultValue = 8.0, MinValue = 2.0, MaxValue = 20.0, Group = "Execution")]
        public double MaxAllowedRR { get; set; }

        [Parameter("Buy H1 Min Score", DefaultValue = 18.0, MinValue = 0, MaxValue = 20, Group = "Regime")]
        public double BuyH1MinScore { get; set; }

        [Parameter("Block London Entries", DefaultValue = true, Group = "Session")]
        public bool BlockLondonEntries { get; set; }

        [Parameter("Require H1 ATR Expansion", DefaultValue = true, Group = "Regime")]
        public bool RequireH1AtrExpansion { get; set; }

        [Parameter("H1 ATR14/ATR50 Min", DefaultValue = 1.15, MinValue = 1.00, MaxValue = 2.00, Group = "Regime")]
        public double H1AtrExpansionMin { get; set; }

        private Bars _m15;
        private Bars _h1;
        private DateTime _lastM15ProcessedOpenTime = DateTime.MinValue;
        private DateTime _day;
        private double _dayStartBalance;
        private double _dayNet;
        private int _tradesToday;
        private int _lastTradeM5Index = -100000;
        private bool _entryInProgress;
        private ArmedSetup _armed;
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
            Print("VERSION xauusd_3 v3.5.0-m5-first-valid");
            Print("[ARCH] H1 regime + M15 Fibonacci/structure + optional harmonic confluence + M5 execution scoring");
            Print("[SAFETY] account-wide symbol exposure lock + pending-order lock + entry mutex; no hedge/no duplicate");
            Print("[SCORE] H1 20 + M15 Fib 20 + M15 Structure 15 + Harmonic 25 + M5 20");
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
            if (!TradingEnabled || Bars.Count < 50 || _m15 == null || _m15.Count < 120)
                return;
            if (Server.Time.Date != _day)
                ResetDay();
            int m5Index = Bars.Count - 1;
            if (m5Index < 12)
                return;
            if (HasAnySymbolExposure())
                return;

            if (_armed != null)
            {
                if (m5Index > _armed.ExpiresM5Index)
                {
                    if (DebugLogging) Print("[ARM EXPIRE] {0} {1} pre={2:F1}", _armed.Tag, _armed.Direction, _armed.PreScore);
                    _armed = null;
                }
                else if (m5Index > _armed.ArmedM5Index)
                {
                    if (TryConfirmM5(m5Index))
                    {
                        _armed = null;
                        return;
                    }
                }
                if (_armed != null)
                    return;
            }

            if (DailyLossLocked() || _tradesToday >= MaxTradesPerDay || m5Index - _lastTradeM5Index < CooldownM5Bars)
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
                return;

            List<Pivot> pivots = BuildPivots(index);
            if (pivots.Count < 2)
                return;
            Pivot start = pivots[pivots.Count - 2];
            Pivot end = pivots[pivots.Count - 1];
            if (start.IsHigh == end.IsHigh)
                return;

            double impulse = Math.Abs(end.Price - start.Price);
            if (impulse < atr * MinImpulseAtr)
                return;
            TradeType direction = end.IsHigh ? TradeType.Buy : TradeType.Sell;

            double zoneLow, zoneHigh, stopAnchor, target = end.Price;
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

            if (!BarTouchesZone(_m15, index, zoneLow, zoneHigh))
                return;
            string key = direction + "|" + start.Index + "|" + end.Index;
            if (_consumed.Contains(key))
                return;

            double h1AtrRatio = H1AtrExpansionRatio();
            if (RequireH1AtrExpansion && h1AtrRatio <= H1AtrExpansionMin)
            {
                if (DebugLogging) Print("[VOL REGIME REJECT] H1 ATR14/ATR50={0:F3} min>{1:F3}", h1AtrRatio, H1AtrExpansionMin);
                return;
            }
            double h1Score = H1RegimeScore(direction);
            if (direction == TradeType.Buy && h1Score < BuyH1MinScore)
            {
                if (DebugLogging) Print("[REGIME REJECT] Buy H1={0:F1} min={1:F1}", h1Score, BuyH1MinScore);
                return;
            }
            double fibScore = FibonacciScore(_m15.ClosePrices[index], zoneLow, zoneHigh);
            double structureScore = StructureScore(impulse, atr, direction, index);
            HarmonicInfo harmonic = HarmonicConfluence(pivots, zoneLow, zoneHigh, atr);
            double preScore = h1Score + fibScore + structureScore + harmonic.Score;

            if (DebugLogging)
                Print("[SETUP] {0} M15={1:u} pre={2:F1} H1={3:F1}/20 Fib={4:F1}/20 Struct={5:F1}/15 Harm={6:F1}/25 tag={7} zone={8:F2}-{9:F2}", direction, stamp, preScore, h1Score, fibScore, structureScore, harmonic.Score, harmonic.Tag, zoneLow, zoneHigh);
            if (preScore < Math.Max(PreScoreMin, M5PreScoreFloor))
                return;

            _consumed.Add(key);
            string tag = harmonic.Score >= 12.0 ? "Hybrid-" + harmonic.Tag : "FibStructure";
            _armed = new ArmedSetup(direction, zoneLow, zoneHigh, stopAnchor, target, atr, preScore, tag, key, m5Index, m5Index + ConfirmWindowM5Bars);
            Print("[ARM] {0} {1} pre={2:F1} zone={3:F2}-{4:F2} stop={5:F2} target={6:F2}", tag, direction, preScore, zoneLow, zoneHigh, stopAnchor, target);
        }

        private bool TryConfirmM5(int index)
        {
            ArmedSetup a = _armed;
            if (a == null || index < Math.Max(M5BreakLookback + 2, 4))
                return false;
            double open = Bars.OpenPrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double close = Bars.ClosePrices[index];
            double range = Math.Max(high - low, Symbol.PipSize);
            double body = Math.Abs(close - open);
            double closePos = (close - low) / range;
            double distance = close < a.ZoneLow ? a.ZoneLow - close : close > a.ZoneHigh ? close - a.ZoneHigh : 0.0;
            double distanceAtr = distance / Math.Max(a.M15Atr, Symbol.PipSize);
            if (distanceAtr > MaxEntryDistanceAtr)
                return true;
            bool directional = a.Direction == TradeType.Buy ? close > open : close < open;
            if (!directional)
                return false;

            double prevOpen = Bars.OpenPrices[index - 1];
            double prevClose = Bars.ClosePrices[index - 1];
            bool engulfing, rejection, microBreak, momentum;
            if (a.Direction == TradeType.Buy)
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
            if (rules < M5RulesNeeded)
                return false;
            double m5Score = M5RulesNeeded * 5.0;
            double finalScore = a.PreScore + m5Score;
            Print("[M5 CONFIRM] {0} {1} pre={2:F1} rules={3}/4 M5={4:F1}/20 final={5:F1}", a.Tag, a.Direction, a.PreScore, rules, m5Score, finalScore);
            if (finalScore < FinalScoreMin)
                return false;
            return TryExecute(a, finalScore, index, rules);
        }

        private bool TryExecute(ArmedSetup a, double finalScore, int m5Index, int confirmRules)
        {
            if (BlockLondonEntries && Server.Time.Hour >= 7 && Server.Time.Hour < 13)
            {
                if (DebugLogging) Print("[SESSION REJECT] London UTC hour={0}", Server.Time.Hour);
                return false;
            }
            if (_entryInProgress || HasAnySymbolExposure())
                return false;
            _entryInProgress = true;
            try
            {
                if (HasAnySymbolExposure())
                    return false;
                double entry = a.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                double stop = a.Direction == TradeType.Buy ? a.StopAnchor - SlAtrBuffer * a.M15Atr : a.StopAnchor + SlAtrBuffer * a.M15Atr;
                double target = a.Target;
                double slDistance = a.Direction == TradeType.Buy ? entry - stop : stop - entry;
                double tpDistance = a.Direction == TradeType.Buy ? target - entry : entry - target;
                if (slDistance <= Symbol.PipSize || tpDistance <= Symbol.PipSize)
                    return false;
                double slPips = slDistance / Symbol.PipSize;
                double tpPips = tpDistance / Symbol.PipSize;
                double rr = tpPips / slPips;
                double brokerMinSlPips = BrokerMinDistancePips(entry, Symbol.MinStopLossDistance);
                double brokerMinTpPips = BrokerMinDistancePips(entry, Symbol.MinTakeProfitDistance);
                double requiredSlPips = Math.Max(brokerMinSlPips * 1.10, MinStopAtr * a.M15Atr / Symbol.PipSize);
                double requiredTpPips = brokerMinTpPips * 1.10;
                if (slPips < requiredSlPips || tpPips < requiredTpPips) return false;
                if (rr < MinimumRiskReward || rr > MaxAllowedRR) return false;

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
                double margin = Symbol.GetEstimatedMargin(a.Direction, volume);
                if (margin > Account.FreeMargin * 0.85 || HasAnySymbolExposure())
                    return false;

                string session = SessionName(Server.Time.Hour);
                string comment = a.Tag + "|" + finalScore.ToString("F1") + "|M5R" + confirmRules;
                TradeResult result = ExecuteMarketOrder(a.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment);
                if (!result.IsSuccessful || result.Position == null) return false;
                if (result.Position.StopLoss == null || result.Position.TakeProfit == null)
                {
                    ClosePosition(result.Position);
                    return false;
                }

                _tradesToday++;
                _lastTradeM5Index = m5Index;
                _openMeta[result.Position.Id] = new TradeMeta(a.Tag, a.Direction, finalScore, rr, confirmRules, session);
                string statKey = a.Tag + "|" + a.Direction;
                if (!_stats.ContainsKey(statKey)) _stats[statKey] = new PatternStats();
                _stats[statKey].Trades++;
                if (!_sessionStats.ContainsKey(session)) _sessionStats[session] = new PatternStats();
                _sessionStats[session].Trades++;
                Print("[OPEN] {0} {1} session={2} score={3:F1} rules={4}/4 vol={5} entry={6:F2} SL={7:F1}p TP={8:F1}p RR={9:F2}", a.Tag, a.Direction, session, finalScore, confirmRules, volume, result.Position.EntryPrice, slPips, tpPips, rr);
                return true;
            }
            finally
            {
                _entryInProgress = false;
            }
        }

        private double H1AtrExpansionRatio()
        {
            int h = _h1.Count - 2;
            if (h < 55) return 0.0;
            double atr14 = Atr(_h1, h, 14);
            double atr50 = Atr(_h1, h, 50);
            if (atr50 <= Symbol.PipSize) return 0.0;
            return atr14 / atr50;
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
            double score = aligned ? 18.0 : opposite ? 3.0 : 10.0;
            if (atr50 > 0 && atr14 / atr50 > 1.15) score += aligned ? 2.0 : -1.0;
            return Clamp(score, 0, 20);
        }

        private double FibonacciScore(double close, double zoneLow, double zoneHigh)
        {
            double width = Math.Max(zoneHigh - zoneLow, Symbol.PipSize);
            double center = (zoneLow + zoneHigh) * 0.5;
            double distance = Math.Abs(close - center) / (width * 0.5);
            return Clamp(20.0 - Math.Max(0.0, distance - 0.20) * 5.0, 8.0, 20.0);
        }

        private double StructureScore(double impulse, double atr, TradeType direction, int index)
        {
            double impulseAtr = impulse / Math.Max(atr, Symbol.PipSize);
            double score = Clamp((impulseAtr - MinImpulseAtr) / 2.5 * 10.0 + 5.0, 5.0, 15.0);
            if (index >= 3)
            {
                bool aligned = direction == TradeType.Buy ? _m15.ClosePrices[index] >= _m15.ClosePrices[index - 3] : _m15.ClosePrices[index] <= _m15.ClosePrices[index - 3];
                if (aligned) score = Math.Min(15.0, score + 2.0);
            }
            return score;
        }

        private HarmonicInfo HarmonicConfluence(List<Pivot> pivots, double zoneLow, double zoneHigh, double atr)
        {
            if (pivots.Count < 4)
                return new HarmonicInfo(0.0, "None");
            Pivot w = pivots[pivots.Count - 4];
            Pivot x = pivots[pivots.Count - 3];
            Pivot a = pivots[pivots.Count - 2];
            Pivot b = pivots[pivots.Count - 1];
            double wx = Math.Abs(x.Price - w.Price);
            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            if (wx <= Symbol.PipSize || xa <= Symbol.PipSize || ab <= Symbol.PipSize)
                return new HarmonicInfo(0.0, "None");
            double bRatio = ab / xa;
            double symmetry = Math.Min(wx, ab) / Math.Max(wx, ab);
            double ratioScore;
            string tag;
            if (bRatio >= 0.55 && bRatio <= 0.70) { ratioScore = 18.0; tag = "GartleyLike"; }
            else if (bRatio >= 0.35 && bRatio <= 0.55) { ratioScore = 16.0; tag = "BatLike"; }
            else if (bRatio >= 0.70 && bRatio <= 0.86) { ratioScore = 17.0; tag = "ButterflyLike"; }
            else { ratioScore = 6.0; tag = "Generic"; }
            double symmetryScore = Clamp((symmetry - 0.55) / 0.45 * 7.0, 0, 7.0);
            double score = ratioScore + symmetryScore;
            double center = (zoneLow + zoneHigh) * 0.5;
            if (Math.Abs(center - b.Price) <= atr * 1.5) score = Math.Min(25.0, score + 2.0);
            return new HarmonicInfo(Clamp(score, 0, 25), tag);
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
                if (high == low) continue;
                Pivot p = new Pivot(i, high ? _m15.HighPrices[i] : _m15.LowPrices[i], high);
                if (pivots.Count == 0) { pivots.Add(p); continue; }
                Pivot prev = pivots[pivots.Count - 1];
                if (prev.IsHigh == p.IsHigh)
                {
                    bool replace = p.IsHigh ? p.Price > prev.Price : p.Price < prev.Price;
                    if (replace) pivots[pivots.Count - 1] = p;
                }
                else
                {
                    pivots.Add(p);
                    if (pivots.Count > 20) pivots.RemoveAt(0);
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

        private bool BarTouchesZone(Bars bars, int index, double zoneLow, double zoneHigh)
        {
            return bars.LowPrices[index] <= zoneHigh && bars.HighPrices[index] >= zoneLow;
        }

        private bool HasAnySymbolExposure()
        {
            foreach (Position p in Positions) if (p.SymbolName == SymbolName) return true;
            foreach (PendingOrder order in PendingOrders) if (order.SymbolName == SymbolName) return true;
            return false;
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
            for (int i = start + 1; i <= end; i++) ema = alpha * bars.ClosePrices[i] + (1.0 - alpha) * ema;
            return ema;
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
            _dayNet = 0.0;
            _tradesToday = 0;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
            if (p.SymbolName != SymbolName || p.Label != BotLabel) return;
            if (Server.Time.Date != _day) ResetDay();
            _dayNet += p.NetProfit;
            TradeMeta meta;
            if (!_openMeta.TryGetValue(p.Id, out meta)) return;
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

        private string SessionName(int hour)
        {
            if (hour < 7) return "Asia";
            if (hour < 13) return "London";
            if (hour < 21) return "NewYork";
            return "Late";
        }

        private double Clamp(double value, double min, double max) { return Math.Max(min, Math.Min(max, value)); }

        private sealed class Pivot
        {
            public Pivot(int index, double price, bool isHigh) { Index = index; Price = price; IsHigh = isHigh; }
            public int Index; public double Price; public bool IsHigh;
        }

        private sealed class HarmonicInfo
        {
            public HarmonicInfo(double score, string tag) { Score = score; Tag = tag; }
            public double Score; public string Tag;
        }

        private sealed class ArmedSetup
        {
            public ArmedSetup(TradeType direction, double zoneLow, double zoneHigh, double stopAnchor, double target, double m15Atr, double preScore, string tag, string key, int armedM5Index, int expiresM5Index)
            {
                Direction = direction; ZoneLow = zoneLow; ZoneHigh = zoneHigh; StopAnchor = stopAnchor; Target = target; M15Atr = m15Atr; PreScore = preScore; Tag = tag; Key = key; ArmedM5Index = armedM5Index; ExpiresM5Index = expiresM5Index;
            }
            public TradeType Direction; public double ZoneLow; public double ZoneHigh; public double StopAnchor; public double Target; public double M15Atr; public double PreScore; public string Tag; public string Key; public int ArmedM5Index; public int ExpiresM5Index;
        }

        private sealed class TradeMeta
        {
            public TradeMeta(string tag, TradeType direction, double score, double rr, int confirmRules, string session)
            {
                Tag = tag; Direction = direction; Score = score; Rr = rr; ConfirmRules = confirmRules; Session = session;
            }
            public string Tag; public TradeType Direction; public double Score; public double Rr; public int ConfirmRules; public string Session;
        }

        private sealed class PatternStats
        {
            public int Trades; public int Wins; public int Losses; public double Net;
        }
    }
}
