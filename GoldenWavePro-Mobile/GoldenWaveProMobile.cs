using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GoldenWaveProMobile : Robot
    {
        private enum Direction { Buy, Sell }

        private sealed class Pivot
        {
            public int Index { get; set; }
            public double Price { get; set; }
            public bool IsHigh { get; set; }
        }

        [Parameter("Trading Enabled", DefaultValue = true, Group = "General")]
        public bool TradingEnabled { get; set; }

        [Parameter("Label", DefaultValue = "GoldenWavePro", Group = "General")]
        public string Label { get; set; }

        [Parameter("Risk Per Trade (%)", DefaultValue = 0.30, MinValue = 0.01, MaxValue = 5.0, Step = 0.01, Group = "Risk")]
        public double RiskPercent { get; set; }

        [Parameter("Reward/Risk", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 5.0, Step = 0.1, Group = "Risk")]
        public double RewardRisk { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 50.0, MinValue = 0.0, Group = "Risk")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Cooldown Minutes", DefaultValue = 15, MinValue = 0, Group = "Risk")]
        public int CooldownMinutes { get; set; }

        [Parameter("Min Confidence", DefaultValue = 0.78, MinValue = 0.50, MaxValue = 0.99, Step = 0.01, Group = "Signal")]
        public double MinConfidence { get; set; }

        [Parameter("ZigZag Depth", DefaultValue = 8, MinValue = 2, MaxValue = 30, Group = "Signal")]
        public int ZigZagDepth { get; set; }

        [Parameter("ZigZag Backstep", DefaultValue = 3, MinValue = 1, MaxValue = 20, Group = "Signal")]
        public int ZigZagBackstep { get; set; }

        [Parameter("Lookback Bars", DefaultValue = 120, MinValue = 60, MaxValue = 500, Group = "Signal")]
        public int LookbackBars { get; set; }

        [Parameter("Use Market Filter", DefaultValue = true, Group = "Filter")]
        public bool UseMarketFilter { get; set; }

        [Parameter("Min Volatility Ratio", DefaultValue = 0.0003, MinValue = 0.0, Step = 0.0001, Group = "Filter")]
        public double MinVolatilityRatio { get; set; }

        [Parameter("Max Volatility Ratio", DefaultValue = 0.02, MinValue = 0.001, Step = 0.001, Group = "Filter")]
        public double MaxVolatilityRatio { get; set; }

        [Parameter("Min Trend Strength", DefaultValue = 0.0001, MinValue = 0.0, Step = 0.0001, Group = "Filter")]
        public double MinTrendStrength { get; set; }

        [Parameter("Min Volume Ratio", DefaultValue = 0.70, MinValue = 0.0, MaxValue = 5.0, Step = 0.05, Group = "Filter")]
        public double MinVolumeRatio { get; set; }

        private DateTime? _lastTradeTime;
        private int _lastSignalPivotIndex = -1;

        protected override void OnStart()
        {
            Print("GoldenWaveProMobile started on {0} {1}", SymbolName, TimeFrame);
        }

        protected override void OnBarClosed()
        {
            if (!TradingEnabled || Bars.Count < Math.Max(80, ZigZagDepth * 4 + 10))
                return;

            if (Positions.Any(p => p.Label == Label && p.SymbolName == SymbolName))
                return;

            if (_lastTradeTime.HasValue && (Server.Time - _lastTradeTime.Value).TotalMinutes < CooldownMinutes)
                return;

            if (Symbol.PipSize <= 0)
                return;

            var spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (spreadPips > MaxSpreadPips)
                return;

            int current = Bars.Count - 1;
            if (UseMarketFilter && !IsValidMarket(current))
                return;

            var pivots = FindPivots(current);
            if (pivots.Count < 5)
                return;

            var p = pivots.Skip(pivots.Count - 5).Take(5).ToArray();
            if (!IsAlternating(p))
                return;

            double xa = Math.Abs(p[1].Price - p[0].Price);
            double ab = Math.Abs(p[2].Price - p[1].Price);
            double bc = Math.Abs(p[3].Price - p[2].Price);
            double cd = Math.Abs(p[4].Price - p[3].Price);
            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0)
                return;

            double rXaAb = ab / xa;
            double rAbBc = bc / ab;
            double rBcCd = cd / bc;
            double rXaAd = Math.Abs(p[4].Price - p[0].Price) / xa;

            if (!InRange(rXaAb, 0.55, 0.72) ||
                !InRange(rAbBc, 0.382, 0.886) ||
                !InRange(rBcCd, 1.13, 1.80) ||
                !InRange(rXaAd, 0.70, 0.90))
                return;

            double confidence = (
                RatioScore(rXaAb, 0.618) +
                RatioScore(rAbBc, 0.618) +
                RatioScore(rBcCd, 1.272) +
                RatioScore(rXaAd, 0.786)) / 4.0;

            if (confidence < MinConfidence)
                return;

            int pivotIndex = p[4].Index;
            if (pivotIndex == _lastSignalPivotIndex)
                return;

            // Harmonic reversal: D below C => bullish, D above C => bearish.
            Direction direction = p[4].Price < p[3].Price ? Direction.Buy : Direction.Sell;
            TradeType tradeType = direction == Direction.Buy ? TradeType.Buy : TradeType.Sell;
            double entry = tradeType == TradeType.Buy ? Symbol.Ask : Symbol.Bid;

            double swingLow = p.Min(x => x.Price);
            double swingHigh = p.Max(x => x.Price);
            double range = swingHigh - swingLow;
            if (range <= 0)
                return;

            double stopReference = direction == Direction.Buy ? swingLow : swingHigh;
            double rawStopDistance = Math.Abs(entry - stopReference);
            if (rawStopDistance <= Symbol.PipSize)
                rawStopDistance = Math.Max(cd * 0.25, Symbol.PipSize * 10.0);

            double stopDistance = rawStopDistance * 1.30;
            double slPips = stopDistance / Symbol.PipSize;
            double tpPips = slPips * RewardRisk;

            if (slPips <= 0 || tpPips <= 0 || double.IsNaN(slPips) || double.IsInfinity(slPips))
                return;

            double riskAmount = Account.Equity * (RiskPercent / 100.0);
            if (riskAmount <= 0)
                return;

            double volume = Symbol.VolumeForFixedRisk(riskAmount, slPips, RoundingMode.Down);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            volume = Math.Max(Symbol.VolumeInUnitsMin, Math.Min(Symbol.VolumeInUnitsMax, volume));

            var result = ExecuteMarketOrder(tradeType, SymbolName, volume, Label, slPips, tpPips);
            _lastSignalPivotIndex = pivotIndex;

            if (result.IsSuccessful)
            {
                _lastTradeTime = Server.Time;
                Print("OPEN {0} {1} vol={2} SL={3:F1}p TP={4:F1}p Gartley conf={5:F2}",
                    SymbolName, tradeType, volume, slPips, tpPips, confidence);
            }
            else
            {
                Print("ORDER FAILED: {0}", result.Error);
            }
        }

        private List<Pivot> FindPivots(int endIndex)
        {
            int depth = Math.Max(2, ZigZagDepth);
            int start = Math.Max(depth, endIndex - Math.Max(LookbackBars, depth * 4));
            int lastCandidate = Math.Max(start, endIndex - depth);
            var raw = new List<Pivot>();

            for (int i = start; i <= lastCandidate; i++)
            {
                bool high = true;
                bool low = true;
                double currentHigh = Bars.HighPrices[i];
                double currentLow = Bars.LowPrices[i];

                for (int j = i - depth; j <= i + depth; j++)
                {
                    if (j < 0 || j >= Bars.Count || j == i)
                        continue;
                    if (Bars.HighPrices[j] > currentHigh)
                        high = false;
                    if (Bars.LowPrices[j] < currentLow)
                        low = false;
                    if (!high && !low)
                        break;
                }

                if (high && !low)
                    raw.Add(new Pivot { Index = i, Price = currentHigh, IsHigh = true });
                else if (low && !high)
                    raw.Add(new Pivot { Index = i, Price = currentLow, IsHigh = false });
            }

            if (raw.Count == 0)
                return raw;

            var compressed = new List<Pivot> { raw[0] };
            foreach (var cur in raw.Skip(1))
            {
                var last = compressed[compressed.Count - 1];
                if (cur.IsHigh == last.IsHigh)
                {
                    if ((cur.IsHigh && cur.Price >= last.Price) || (!cur.IsHigh && cur.Price <= last.Price))
                        compressed[compressed.Count - 1] = cur;
                }
                else if (cur.Index - last.Index >= Math.Max(1, ZigZagBackstep))
                {
                    compressed.Add(cur);
                }
            }

            return compressed;
        }

        private bool IsValidMarket(int index)
        {
            if (index < 30)
                return false;

            const int volPeriod = 14;
            double volSum = 0;
            int volCount = 0;
            for (int i = index - volPeriod + 1; i <= index; i++)
            {
                double avg = (Bars.HighPrices[i] + Bars.LowPrices[i] + Bars.ClosePrices[i]) / 3.0;
                if (avg <= 0)
                    continue;
                volSum += (Bars.HighPrices[i] - Bars.LowPrices[i]) / avg;
                volCount++;
            }
            double volatility = volCount > 0 ? volSum / volCount : 0;
            if (volatility < MinVolatilityRatio || volatility > MaxVolatilityRatio)
                return false;

            const int trendPeriod = 21;
            double change = 0;
            double avgClose = 0;
            for (int i = index - trendPeriod + 1; i <= index; i++)
            {
                avgClose += Bars.ClosePrices[i];
                if (i > index - trendPeriod + 1)
                    change += Bars.ClosePrices[i] - Bars.ClosePrices[i - 1];
            }
            avgClose /= trendPeriod;
            if (avgClose <= 0)
                return false;
            double trendStrength = change / (trendPeriod * avgClose);
            if (Math.Abs(trendStrength) < MinTrendStrength)
                return false;

            const int volumePeriod = 20;
            double volumeAverage = 0;
            for (int i = index - volumePeriod + 1; i <= index; i++)
                volumeAverage += Bars.TickVolumes[i];
            volumeAverage /= volumePeriod;
            double volumeRatio = volumeAverage > 0 ? Bars.TickVolumes[index] / volumeAverage : 0;
            return volumeRatio >= MinVolumeRatio;
        }

        private static bool IsAlternating(Pivot[] p)
        {
            for (int i = 1; i < p.Length; i++)
                if (p[i].IsHigh == p[i - 1].IsHigh)
                    return false;
            return true;
        }

        private static bool InRange(double value, double min, double max)
        {
            return value >= min && value <= max;
        }

        private static double RatioScore(double value, double target)
        {
            if (target <= 0)
                return 0;
            return 1.0 - Math.Min(1.0, Math.Abs(value - target) / target);
        }
    }
}
