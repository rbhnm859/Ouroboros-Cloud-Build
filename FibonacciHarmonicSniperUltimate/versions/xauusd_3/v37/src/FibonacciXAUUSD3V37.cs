using System;
using System.Collections.Generic;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class FibonacciXAUUSD3V37 : Robot
    {
        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Bot Label", DefaultValue = "FIB_XAUUSD_37", Group = "General")]
        public string BotLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = true, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Max Daily Loss %", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 8.0, Group = "Risk")]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 6, MinValue = 1, MaxValue = 20, Group = "Risk")]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Minimum RR", DefaultValue = 1.35, MinValue = 1.0, MaxValue = 4.0, Group = "Risk")]
        public double MinimumRiskReward { get; set; }

        [Parameter("Max Allowed RR", DefaultValue = 6.0, MinValue = 2.0, MaxValue = 12.0, Group = "Risk")]
        public double MaxAllowedRiskReward { get; set; }

        [Parameter("Pivot Left", DefaultValue = 3, MinValue = 1, MaxValue = 10, Group = "Harmonic")]
        public int PivotLeft { get; set; }

        [Parameter("Pivot Right", DefaultValue = 2, MinValue = 1, MaxValue = 8, Group = "Harmonic")]
        public int PivotRight { get; set; }

        [Parameter("Pivot Lookback", DefaultValue = 500, MinValue = 100, MaxValue = 2000, Group = "Harmonic")]
        public int PivotLookback { get; set; }

        [Parameter("Minimum Pattern Score", DefaultValue = 72.0, MinValue = 50.0, MaxValue = 95.0, Group = "Harmonic")]
        public double MinimumPatternScore { get; set; }

        [Parameter("Max D Age Bars", DefaultValue = 8, MinValue = 1, MaxValue = 30, Group = "Harmonic")]
        public int MaxDAgeBars { get; set; }

        [Parameter("Min XA / ATR", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0, Group = "Harmonic")]
        public double MinXaAtr { get; set; }

        [Parameter("Target AD Fib", DefaultValue = 0.618, MinValue = 0.382, MaxValue = 1.0, Group = "Fibonacci")]
        public double TargetAdFib { get; set; }

        [Parameter("Stop XA Buffer", DefaultValue = 0.06, MinValue = 0.01, MaxValue = 0.25, Group = "Fibonacci")]
        public double StopXaBuffer { get; set; }

        [Parameter("Stop ATR Buffer", DefaultValue = 0.35, MinValue = 0.10, MaxValue = 1.50, Group = "Fibonacci")]
        public double StopAtrBuffer { get; set; }

        [Parameter("Confirmation Rules Needed", DefaultValue = 2, MinValue = 1, MaxValue = 3, Group = "Confirmation")]
        public int ConfirmationRulesNeeded { get; set; }

        [Parameter("Confirm Window Bars", DefaultValue = 6, MinValue = 1, MaxValue = 20, Group = "Confirmation")]
        public int ConfirmWindowBars { get; set; }

        [Parameter("Break Lookback", DefaultValue = 2, MinValue = 1, MaxValue = 6, Group = "Confirmation")]
        public int BreakLookback { get; set; }

        [Parameter("Rejection Wick Min %", DefaultValue = 0.25, MinValue = 0.10, MaxValue = 0.70, Group = "Confirmation")]
        public double RejectionWickMin { get; set; }

        [Parameter("Body Min %", DefaultValue = 0.40, MinValue = 0.15, MaxValue = 0.90, Group = "Confirmation")]
        public double BodyMin { get; set; }

        [Parameter("Max Entry Distance ATR", DefaultValue = 1.10, MinValue = 0.25, MaxValue = 3.0, Group = "Confirmation")]
        public double MaxEntryDistanceAtr { get; set; }

        [Parameter("Relative Tick Volume Min", DefaultValue = 0.80, MinValue = 0.20, MaxValue = 2.0, Group = "Activity")]
        public double RelativeTickVolumeMin { get; set; }

        [Parameter("Volume Average Bars", DefaultValue = 20, MinValue = 5, MaxValue = 100, Group = "Activity")]
        public int VolumeAverageBars { get; set; }

        [Parameter("ATR14 / ATR50 Min", DefaultValue = 0.75, MinValue = 0.30, MaxValue = 1.50, Group = "Activity")]
        public double AtrRegimeMin { get; set; }

        [Parameter("Max Spread / ATR", DefaultValue = 0.08, MinValue = 0.005, MaxValue = 0.30, Group = "Activity")]
        public double MaxSpreadAtrRatio { get; set; }

        [Parameter("Cooldown Bars", DefaultValue = 4, MinValue = 0, MaxValue = 100, Group = "Execution")]
        public int CooldownBars { get; set; }

        [Parameter("Min Stop ATR", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 2.0, Group = "Execution")]
        public double MinStopAtr { get; set; }

        private DateTime _day;
        private double _dayStartBalance;
        private double _dayNet;
        private int _tradesToday;
        private int _lastTradeIndex = -100000;
        private bool _entryInProgress;
        private ArmedPattern _armed;
        private readonly HashSet<string> _consumed = new HashSet<string>();
        private readonly Queue<string> _consumedOrder = new Queue<string>();
        private readonly Dictionary<long, TradeMeta> _openMeta = new Dictionary<long, TradeMeta>();
        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>();

        protected override void OnStart()
        {
            Positions.Closed += OnPositionClosed;
            ResetDay();
            RestoreDailyStateFromHistory();
            Print("VERSION xauusd_3 v3.7.0-harmonic-core-rearchitecture");
            Print("[ARCH] timeframe-agnostic XABCD harmonic engine; Gartley/Bat/Butterfly/Crab/DeepCrab only");
            Print("[ENTRY] completed harmonic pattern + activity gate + price-action confirmation; no generic Fibonacci-only entry");
            Print("[SAFETY] single symbol exposure, no hedge/grid/martingale/DCA/recovery; fixed-risk SL/TP required");
            Print("[TIMEFRAME] unrestricted current chart timeframe={0}", TimeFrame);
            if (!IsXauUsdSymbol())
                Print("[WARN] This commercial candidate is specialized for XAUUSD; current symbol={0}", SymbolName);
        }

        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            foreach (var kv in _stats)
            {
                PatternStats s = kv.Value;
                double wr = s.Trades > 0 ? 100.0 * s.Wins / s.Trades : 0.0;
                Print("[PATTERN STATS] {0} trades={1} wins={2} losses={3} WR={4:F1}% net={5:F2}", kv.Key, s.Trades, s.Wins, s.Losses, wr, s.Net);
            }
        }

        protected override void OnTick()
        {
            EnsureProtectionIntegrity();
        }

        protected override void OnBarClosed()
        {
            if (!TradingEnabled || Bars.Count < Math.Max(120, VolumeAverageBars + 55))
                return;
            if (Server.Time.Date != _day)
                ResetDay();

            EnsureProtectionIntegrity();
            if (HasAnySymbolExposure())
                return;

            int index = Bars.Count - 1;
            if (index < 60)
                return;

            if (_armed != null)
            {
                if (index > _armed.ExpiresIndex)
                {
                    if (DebugLogging) Print("[ARM EXPIRE] {0} {1} score={2:F1}", _armed.PatternName, _armed.Direction, _armed.PatternScore);
                    _armed = null;
                }
                else if (index > _armed.ArmedIndex)
                {
                    if (TryConfirmAndExecute(index))
                    {
                        _armed = null;
                        return;
                    }
                }
                if (_armed != null)
                    return;
            }

            if (DailyLossLocked() || _tradesToday >= MaxTradesPerDay || index - _lastTradeIndex < CooldownBars)
                return;

            TryArmLatestHarmonic(index);
        }

        private void TryArmLatestHarmonic(int index)
        {
            double atr14 = Atr(Bars, index, 14);
            double atr50 = Atr(Bars, index, 50);
            if (atr14 <= Symbol.PipSize || atr50 <= Symbol.PipSize)
                return;

            double spreadRatio = (Symbol.Ask - Symbol.Bid) / atr14;
            if (spreadRatio > MaxSpreadAtrRatio)
            {
                if (DebugLogging) Print("[ACTIVITY REJECT] spread/ATR={0:F3}", spreadRatio);
                return;
            }

            double atrRegime = atr14 / atr50;
            if (atrRegime < AtrRegimeMin)
            {
                if (DebugLogging) Print("[ACTIVITY REJECT] ATR14/ATR50={0:F3} min={1:F3}", atrRegime, AtrRegimeMin);
                return;
            }

            double relativeVolume = RelativeTickVolume(index);
            if (relativeVolume < RelativeTickVolumeMin)
            {
                if (DebugLogging) Print("[ACTIVITY REJECT] relTickVol={0:F2} min={1:F2}", relativeVolume, RelativeTickVolumeMin);
                return;
            }

            List<Pivot> pivots = BuildPivots(index);
            if (pivots.Count < 5)
                return;

            HarmonicPattern pattern = DetectLatestPattern(pivots, atr14, index);
            if (pattern == null || pattern.Score < MinimumPatternScore)
                return;

            string key = pattern.Name + "|" + pattern.Direction + "|" + pattern.X.Index + "|" + pattern.A.Index + "|" + pattern.B.Index + "|" + pattern.C.Index + "|" + pattern.D.Index;
            if (_consumed.Contains(key))
                return;

            RememberConsumed(key);
            _armed = new ArmedPattern(pattern, key, index, index + ConfirmWindowBars, atr14);
            Print("[HARMONIC ARM] {0} {1} score={2:F1} tf={3} D={4:F2} AB/XA={5:F3} BC/AB={6:F3} CD/BC={7:F3} AD/XA={8:F3} relVol={9:F2} atrRegime={10:F2}",
                pattern.Name, pattern.Direction, pattern.Score, TimeFrame, pattern.D.Price, pattern.AbXa, pattern.BcAb, pattern.CdBc, pattern.AdXa, relativeVolume, atrRegime);
        }

        private bool TryConfirmAndExecute(int index)
        {
            ArmedPattern a = _armed;
            if (a == null)
                return false;

            double open = Bars.OpenPrices[index];
            double high = Bars.HighPrices[index];
            double low = Bars.LowPrices[index];
            double close = Bars.ClosePrices[index];
            double range = Math.Max(high - low, Symbol.PipSize);
            double bodyRatio = Math.Abs(close - open) / range;
            double distanceAtr = Math.Abs(close - a.Pattern.D.Price) / Math.Max(a.Atr, Symbol.PipSize);
            if (distanceAtr > MaxEntryDistanceAtr)
            {
                if (DebugLogging) Print("[CONFIRM EXPIRE] price too far from D distanceATR={0:F2}", distanceAtr);
                return true;
            }

            bool directional = a.Direction == TradeType.Buy ? close > open : close < open;
            if (!directional)
                return false;

            double closePos = (close - low) / range;
            bool rejection;
            bool momentum;
            bool microBreak;
            if (a.Direction == TradeType.Buy)
            {
                double lowerWick = Math.Min(open, close) - low;
                rejection = lowerWick / range >= RejectionWickMin && closePos >= 0.58;
                momentum = bodyRatio >= BodyMin && closePos >= 0.62;
                double priorHigh = Bars.HighPrices[index - 1];
                for (int k = 2; k <= BreakLookback && index - k >= 0; k++)
                    priorHigh = Math.Max(priorHigh, Bars.HighPrices[index - k]);
                microBreak = close > priorHigh;
            }
            else
            {
                double upperWick = high - Math.Max(open, close);
                rejection = upperWick / range >= RejectionWickMin && closePos <= 0.42;
                momentum = bodyRatio >= BodyMin && closePos <= 0.38;
                double priorLow = Bars.LowPrices[index - 1];
                for (int k = 2; k <= BreakLookback && index - k >= 0; k++)
                    priorLow = Math.Min(priorLow, Bars.LowPrices[index - k]);
                microBreak = close < priorLow;
            }

            int rules = 0;
            if (rejection) rules++;
            if (momentum) rules++;
            if (microBreak) rules++;
            if (rules < ConfirmationRulesNeeded)
                return false;

            double relVolume = RelativeTickVolume(index);
            double atr50 = Atr(Bars, index, 50);
            double atrRegime = atr50 > Symbol.PipSize ? Atr(Bars, index, 14) / atr50 : 0.0;
            if (relVolume < RelativeTickVolumeMin || atrRegime < AtrRegimeMin)
                return false;

            return ExecutePattern(a, index, rules, relVolume);
        }

        private bool ExecutePattern(ArmedPattern a, int index, int confirmRules, double relativeVolume)
        {
            if (_entryInProgress || HasAnySymbolExposure() || DailyLossLocked())
                return false;

            _entryInProgress = true;
            try
            {
                if (HasAnySymbolExposure())
                    return false;

                HarmonicPattern p = a.Pattern;
                double entry = p.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
                double xa = Math.Abs(p.A.Price - p.X.Price);
                double ad = Math.Abs(p.D.Price - p.A.Price);
                double stopBuffer = Math.Max(StopXaBuffer * xa, StopAtrBuffer * a.Atr);
                double stop = p.Direction == TradeType.Buy ? p.D.Price - stopBuffer : p.D.Price + stopBuffer;
                double targetDistance = ad * TargetAdFib;
                double target = p.Direction == TradeType.Buy ? p.D.Price + targetDistance : p.D.Price - targetDistance;

                double slDistance = p.Direction == TradeType.Buy ? entry - stop : stop - entry;
                double tpDistance = p.Direction == TradeType.Buy ? target - entry : entry - target;
                if (slDistance <= Symbol.PipSize || tpDistance <= Symbol.PipSize)
                    return false;

                double slPips = slDistance / Symbol.PipSize;
                double tpPips = tpDistance / Symbol.PipSize;
                double brokerMinSlPips = BrokerMinDistancePips(entry, Symbol.MinStopLossDistance);
                double brokerMinTpPips = BrokerMinDistancePips(entry, Symbol.MinTakeProfitDistance);
                double requiredSlPips = Math.Max(brokerMinSlPips * 1.10, MinStopAtr * a.Atr / Symbol.PipSize);
                if (slPips < requiredSlPips || tpPips < brokerMinTpPips * 1.10)
                    return false;

                double rr = tpPips / slPips;
                if (rr < MinimumRiskReward || rr > MaxAllowedRiskReward)
                {
                    if (DebugLogging) Print("[RR REJECT] {0} RR={1:F2}", p.Name, rr);
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

                double actualRisk = Symbol.AmountRisked(volume, slPips);
                if (double.IsNaN(actualRisk) || actualRisk <= 0 || actualRisk > budget * 1.03)
                    return false;
                double margin = Symbol.GetEstimatedMargin(p.Direction, volume);
                if (margin > Account.FreeMargin * 0.80)
                    return false;

                string comment = p.Name + "|Q" + p.Score.ToString("F0") + "|R" + confirmRules + "|TF" + TimeFrame;
                TradeResult result = ExecuteMarketOrder(p.Direction, SymbolName, volume, BotLabel, slPips, tpPips, comment);
                if (!result.IsSuccessful || result.Position == null)
                {
                    Print("[OPEN FAIL] {0} error={1}", p.Name, result.Error);
                    return false;
                }
                if (result.Position.StopLoss == null || result.Position.TakeProfit == null)
                {
                    Print("[FAILSAFE] protection missing immediately after open PID={0}", result.Position.Id);
                    ClosePosition(result.Position);
                    return false;
                }

                _tradesToday++;
                _lastTradeIndex = index;
                _openMeta[result.Position.Id] = new TradeMeta(p.Name, p.Direction, p.Score, rr, confirmRules, relativeVolume);
                string statKey = p.Name + "|" + p.Direction;
                PatternStats stat;
                if (!_stats.TryGetValue(statKey, out stat)) { stat = new PatternStats(); _stats[statKey] = stat; }
                stat.Trades++;
                Print("[OPEN] {0} {1} tf={2} quality={3:F1} rules={4}/3 relVol={5:F2} vol={6} SL={7:F1}p TP={8:F1}p RR={9:F2}",
                    p.Name, p.Direction, TimeFrame, p.Score, confirmRules, relativeVolume, volume, slPips, tpPips, rr);
                return true;
            }
            finally
            {
                _entryInProgress = false;
            }
        }

        private HarmonicPattern DetectLatestPattern(List<Pivot> pivots, double atr, int currentIndex)
        {
            Pivot x = pivots[pivots.Count - 5];
            Pivot a = pivots[pivots.Count - 4];
            Pivot b = pivots[pivots.Count - 3];
            Pivot c = pivots[pivots.Count - 2];
            Pivot d = pivots[pivots.Count - 1];

            if (currentIndex - d.Index > MaxDAgeBars)
                return null;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double ad = Math.Abs(d.Price - a.Price);
            if (xa <= Symbol.PipSize || ab <= Symbol.PipSize || bc <= Symbol.PipSize || cd <= Symbol.PipSize)
                return null;
            if (xa / Math.Max(atr, Symbol.PipSize) < MinXaAtr)
                return null;

            TradeType direction = d.IsHigh ? TradeType.Sell : TradeType.Buy;
            double abXa = ab / xa;
            double bcAb = bc / ab;
            double cdBc = cd / bc;
            double adXa = ad / xa;

            HarmonicPattern best = null;
            Consider(ref best, MakePattern("Gartley", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.618, 0.14), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.13, 1.618, 0.30), FitTarget(adXa, 0.786, 0.12), 0.25, 0.15, 0.20, 0.40));
            Consider(ref best, MakePattern("Bat", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitRange(abXa, 0.382, 0.50, 0.10), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.618, 2.618, 0.45), FitTarget(adXa, 0.886, 0.12), 0.20, 0.15, 0.25, 0.40));
            Consider(ref best, MakePattern("Butterfly", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.786, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.618, 2.618, 0.45), FitRange(adXa, 1.27, 1.618, 0.22), 0.25, 0.15, 0.25, 0.35));
            Consider(ref best, MakePattern("Crab", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitRange(abXa, 0.382, 0.618, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 2.24, 3.618, 0.60), FitTarget(adXa, 1.618, 0.14), 0.20, 0.15, 0.25, 0.40));
            Consider(ref best, MakePattern("DeepCrab", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.886, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 2.0, 3.618, 0.65), FitTarget(adXa, 1.618, 0.14), 0.25, 0.15, 0.20, 0.40));

            return best;
        }

        private HarmonicPattern MakePattern(string name, TradeType direction, Pivot x, Pivot a, Pivot b, Pivot c, Pivot d,
            double abXa, double bcAb, double cdBc, double adXa,
            double q1, double q2, double q3, double q4, double w1, double w2, double w3, double w4)
        {
            double score = 100.0 * (q1 * w1 + q2 * w2 + q3 * w3 + q4 * w4);
            return new HarmonicPattern(name, direction, score, x, a, b, c, d, abXa, bcAb, cdBc, adXa);
        }

        private void Consider(ref HarmonicPattern best, HarmonicPattern candidate)
        {
            if (candidate == null)
                return;
            if (best == null || candidate.Score > best.Score)
                best = candidate;
        }

        private double FitTarget(double value, double target, double toleranceFraction)
        {
            double tolerance = Math.Max(target * toleranceFraction, 0.03);
            return Clamp(1.0 - Math.Abs(value - target) / tolerance, 0.0, 1.0);
        }

        private double FitRange(double value, double min, double max, double shoulder)
        {
            if (value >= min && value <= max)
                return 1.0;
            if (value < min)
                return Clamp(1.0 - (min - value) / Math.Max(shoulder, 0.01), 0.0, 1.0);
            return Clamp(1.0 - (value - max) / Math.Max(shoulder, 0.01), 0.0, 1.0);
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
                Pivot p = new Pivot(i, high ? Bars.HighPrices[i] : Bars.LowPrices[i], high);
                if (pivots.Count == 0)
                {
                    pivots.Add(p);
                    continue;
                }
                Pivot previous = pivots[pivots.Count - 1];
                if (previous.IsHigh == p.IsHigh)
                {
                    bool replace = p.IsHigh ? p.Price > previous.Price : p.Price < previous.Price;
                    if (replace)
                        pivots[pivots.Count - 1] = p;
                }
                else
                {
                    pivots.Add(p);
                    if (pivots.Count > 40)
                        pivots.RemoveAt(0);
                }
            }
            return pivots;
        }

        private bool IsPivotHigh(int index)
        {
            double value = Bars.HighPrices[index];
            for (int k = 1; k <= PivotLeft; k++) if (Bars.HighPrices[index - k] >= value) return false;
            for (int k = 1; k <= PivotRight; k++) if (Bars.HighPrices[index + k] > value) return false;
            return true;
        }

        private bool IsPivotLow(int index)
        {
            double value = Bars.LowPrices[index];
            for (int k = 1; k <= PivotLeft; k++) if (Bars.LowPrices[index - k] <= value) return false;
            for (int k = 1; k <= PivotRight; k++) if (Bars.LowPrices[index + k] < value) return false;
            return true;
        }

        private double RelativeTickVolume(int index)
        {
            if (index < VolumeAverageBars + 1)
                return 0.0;
            double average = 0.0;
            for (int i = index - VolumeAverageBars; i < index; i++)
                average += Bars.TickVolumes[i];
            average /= VolumeAverageBars;
            if (average <= 0)
                return 0.0;
            return Bars.TickVolumes[index] / average;
        }

        private double Atr(Bars bars, int end, int period)
        {
            if (end < period + 1)
                return 0.0;
            double sum = 0.0;
            for (int i = end - period + 1; i <= end; i++)
            {
                double previousClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(bars.HighPrices[i] - bars.LowPrices[i], Math.Max(Math.Abs(bars.HighPrices[i] - previousClose), Math.Abs(bars.LowPrices[i] - previousClose)));
                sum += tr;
            }
            return sum / period;
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

        private void EnsureProtectionIntegrity()
        {
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (p.StopLoss != null && p.TakeProfit != null)
                    continue;
                Print("[FAILSAFE] Missing SL/TP PID={0}; closing immediately", p.Id);
                TradeResult result = ClosePosition(p);
                if (!result.IsSuccessful)
                    Print("[FAILSAFE FAIL] PID={0} error={1}", p.Id, result.Error);
            }
        }

        private double BrokerMinDistancePips(double price, double distance)
        {
            if (distance <= 0)
                return 0.0;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return distance;
            return (price * distance / 100.0) / Symbol.PipSize;
        }

        private bool DailyLossLocked()
        {
            double cap = _dayStartBalance * MaxDailyLossPercent / 100.0;
            return -(_dayNet + CurrentBotFloatingNet()) >= cap;
        }

        private double CurrentBotFloatingNet()
        {
            double net = 0.0;
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
                net += p.NetProfit;
            return net;
        }

        private void RestoreDailyStateFromHistory()
        {
            double net = 0.0;
            int trades = 0;
            foreach (HistoricalTrade t in History.FindAll(BotLabel, SymbolName))
            {
                if (t.ClosingTime.Date == _day)
                    net += t.NetProfit;
                if (t.EntryTime.Date == _day)
                    trades++;
            }
            _dayNet = net;
            _tradesToday = trades;
            _dayStartBalance = Account.Balance - _dayNet;
            if (_dayStartBalance <= 0)
                _dayStartBalance = Account.Balance;
        }

        private void ResetDay()
        {
            _day = Server.Time.Date;
            _dayStartBalance = Account.Balance;
            _dayNet = 0.0;
            _tradesToday = 0;
        }

        private void RememberConsumed(string key)
        {
            if (_consumed.Add(key))
                _consumedOrder.Enqueue(key);
            while (_consumedOrder.Count > 500)
            {
                string old = _consumedOrder.Dequeue();
                _consumed.Remove(old);
            }
        }

        private bool IsXauUsdSymbol()
        {
            return SymbolName != null && SymbolName.StartsWith("XAUUSD", StringComparison.OrdinalIgnoreCase);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            Position p = args.Position;
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
            PatternStats stat;
            if (!_stats.TryGetValue(key, out stat)) { stat = new PatternStats(); _stats[key] = stat; }
            if (p.NetProfit > 0) stat.Wins++; else stat.Losses++;
            stat.Net += p.NetProfit;
            Print("[CLOSE] {0} {1} tf={2} quality={3:F1} rules={4}/3 RR={5:F2} relVol={6:F2} net={7:F2} reason={8}",
                meta.Pattern, meta.Direction, TimeFrame, meta.Score, meta.ConfirmRules, meta.Rr, meta.RelativeVolume, p.NetProfit, args.Reason);
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

        private sealed class HarmonicPattern
        {
            public HarmonicPattern(string name, TradeType direction, double score, Pivot x, Pivot a, Pivot b, Pivot c, Pivot d, double abXa, double bcAb, double cdBc, double adXa)
            {
                Name = name; Direction = direction; Score = score; X = x; A = a; B = b; C = c; D = d; AbXa = abXa; BcAb = bcAb; CdBc = cdBc; AdXa = adXa;
            }
            public string Name;
            public TradeType Direction;
            public double Score;
            public Pivot X;
            public Pivot A;
            public Pivot B;
            public Pivot C;
            public Pivot D;
            public double AbXa;
            public double BcAb;
            public double CdBc;
            public double AdXa;
        }

        private sealed class ArmedPattern
        {
            public ArmedPattern(HarmonicPattern pattern, string key, int armedIndex, int expiresIndex, double atr)
            {
                Pattern = pattern; Key = key; ArmedIndex = armedIndex; ExpiresIndex = expiresIndex; Atr = atr;
            }
            public HarmonicPattern Pattern;
            public string Key;
            public int ArmedIndex;
            public int ExpiresIndex;
            public double Atr;
            public string PatternName { get { return Pattern.Name; } }
            public TradeType Direction { get { return Pattern.Direction; } }
            public double PatternScore { get { return Pattern.Score; } }
        }

        private sealed class TradeMeta
        {
            public TradeMeta(string pattern, TradeType direction, double score, double rr, int confirmRules, double relativeVolume)
            {
                Pattern = pattern; Direction = direction; Score = score; Rr = rr; ConfirmRules = confirmRules; RelativeVolume = relativeVolume;
            }
            public string Pattern;
            public TradeType Direction;
            public double Score;
            public double Rr;
            public int ConfirmRules;
            public double RelativeVolume;
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
