using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GoldenWavePro : Robot
    {
        private const string Label = "GoldenWavePro";

        [Parameter("Risk Per Trade (%)", Group = "Risk", DefaultValue = 0.30, MinValue = 0.05, MaxValue = 2.0, Step = 0.05)]
        public double RiskPercent { get; set; }

        [Parameter("Reward / Risk", Group = "Risk", DefaultValue = 1.618, MinValue = 1.0, MaxValue = 5.0, Step = 0.1)]
        public double RewardRisk { get; set; }

        [Parameter("Daily Loss Limit (%)", Group = "Risk", DefaultValue = 5.0, MinValue = 0.5, MaxValue = 25.0)]
        public double DailyLossLimit { get; set; }

        [Parameter("Weekly Loss Limit (%)", Group = "Risk", DefaultValue = 12.0, MinValue = 1.0, MaxValue = 40.0)]
        public double WeeklyLossLimit { get; set; }

        [Parameter("Max Drawdown (%)", Group = "Risk", DefaultValue = 18.0, MinValue = 1.0, MaxValue = 50.0)]
        public double MaxDrawdown { get; set; }

        [Parameter("Emergency Stop (%)", Group = "Risk", DefaultValue = 25.0, MinValue = 5.0, MaxValue = 80.0)]
        public double EmergencyStop { get; set; }

        [Parameter("Min Stop (pips)", Group = "Risk", DefaultValue = 10.0, MinValue = 1.0)]
        public double MinStopPips { get; set; }

        [Parameter("Pattern Score", Group = "Pattern", DefaultValue = 0.92, MinValue = 0.50, MaxValue = 0.99, Step = 0.01)]
        public double MinPatternScore { get; set; }

        [Parameter("Swing Depth", Group = "Pattern", DefaultValue = 5, MinValue = 2, MaxValue = 20)]
        public int SwingDepth { get; set; }

        [Parameter("Lookback Bars", Group = "Pattern", DefaultValue = 250, MinValue = 50, MaxValue = 2000)]
        public int LookbackBars { get; set; }

        [Parameter("Use Market Filter", Group = "Filter", DefaultValue = true)]
        public bool UseMarketFilter { get; set; }

        [Parameter("Min Volatility", Group = "Filter", DefaultValue = 0.0003, MinValue = 0.0, Step = 0.0001)]
        public double MinVolatility { get; set; }

        [Parameter("Max Volatility", Group = "Filter", DefaultValue = 0.045, MinValue = 0.001, Step = 0.001)]
        public double MaxVolatility { get; set; }

        [Parameter("Min Trend Strength", Group = "Filter", DefaultValue = 0.00003, MinValue = 0.0, Step = 0.00001)]
        public double MinTrendStrength { get; set; }

        [Parameter("Min Volume Ratio", Group = "Filter", DefaultValue = 0.80, MinValue = 0.1, MaxValue = 5.0, Step = 0.05)]
        public double MinVolumeRatio { get; set; }

        [Parameter("Trade Start UTC", Group = "Session", DefaultValue = 7, MinValue = 0, MaxValue = 23)]
        public int TradeStartUtc { get; set; }

        [Parameter("Trade End UTC", Group = "Session", DefaultValue = 21, MinValue = 0, MaxValue = 23)]
        public int TradeEndUtc { get; set; }

        [Parameter("Cooldown Minutes", Group = "Execution", DefaultValue = 15, MinValue = 0, MaxValue = 1440)]
        public int CooldownMinutes { get; set; }

        [Parameter("Block Any Symbol Position", Group = "Execution", DefaultValue = true)]
        public bool BlockAnySymbolPosition { get; set; }

        [Parameter("Debug Logging", Group = "Execution", DefaultValue = true)]
        public bool DebugLogging { get; set; }

        private double _initialEquity;
        private double _dayStartEquity;
        private double _weekStartEquity;
        private double _peakEquity;
        private DateTime _day;
        private int _week;
        private DateTime? _lastTradeTime;
        private int _lastSignalBar = -1;

        private sealed class Pivot
        {
            public int Index;
            public double Price;
            public bool IsHigh;
        }

        private sealed class Pattern
        {
            public TradeType TradeType;
            public double StopPrice;
            public double Score;
        }

        protected override void OnStart()
        {
            _initialEquity = _dayStartEquity = _weekStartEquity = _peakEquity = Account.Equity;
            _day = Server.Time.Date;
            _week = WeekOfYear(Server.Time);
            Print("GoldenWavePro started: {0}", SymbolName);
        }

        protected override void OnBar()
        {
            try
            {
                RefreshRiskAnchors();
                if (Account.Equity > _peakEquity)
                    _peakEquity = Account.Equity;

                if (EmergencyTriggered())
                {
                    CloseOwnPositions();
                    return;
                }

                if (RiskBlocked() || !InSession(Server.Time.Hour) || InCooldown() || HasPosition())
                    return;

                var index = Bars.Count - 2;
                if (index < Math.Max(30, SwingDepth * 3) || index == _lastSignalBar)
                    return;

                if (UseMarketFilter && !MarketFilterPasses(index))
                    return;

                var pattern = DetectGartley(index);
                if (pattern == null || pattern.Score < MinPatternScore)
                    return;

                ExecuteSignal(pattern, index);
            }
            catch (Exception ex)
            {
                Print("GoldenWavePro error: {0}", ex.Message);
            }
        }

        private void ExecuteSignal(Pattern pattern, int signalBar)
        {
            var entry = pattern.TradeType == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            if ((pattern.TradeType == TradeType.Buy && pattern.StopPrice >= entry) ||
                (pattern.TradeType == TradeType.Sell && pattern.StopPrice <= entry))
                return;

            var stopPips = Math.Max(Math.Abs(entry - pattern.StopPrice) / Symbol.PipSize, MinStopPips);
            if (stopPips <= 0 || double.IsNaN(stopPips) || double.IsInfinity(stopPips))
                return;

            var riskAmount = Account.Equity * RiskPercent / 100.0;
            var volume = Symbol.VolumeForFixedRisk(riskAmount, stopPips, RoundingMode.Down);
            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Math.Max(volume, Symbol.VolumeInUnitsMin);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume < Symbol.VolumeInUnitsMin)
                return;

            var tpPips = stopPips * RewardRisk;
            var result = ExecuteMarketOrder(pattern.TradeType, SymbolName, volume, Label, stopPips, tpPips);
            if (!result.IsSuccessful)
            {
                Print("Order failed: {0}", result.Error);
                return;
            }

            _lastTradeTime = Server.Time;
            _lastSignalBar = signalBar;
            Print("OPEN {0} {1} volume={2} score={3:F3} SL={4:F1}p TP={5:F1}p", pattern.TradeType, SymbolName, volume, pattern.Score, stopPips, tpPips);
        }

        private Pattern DetectGartley(int currentIndex)
        {
            var p = RecentPivots(currentIndex);
            if (p == null || p.Length < 5)
                return null;

            var xa = Math.Abs(p[1].Price - p[0].Price);
            var ab = Math.Abs(p[2].Price - p[1].Price);
            var bc = Math.Abs(p[3].Price - p[2].Price);
            var cd = Math.Abs(p[4].Price - p[3].Price);
            if (xa <= 0 || ab <= 0 || bc <= 0)
                return null;

            var xaAb = ab / xa;
            var abBc = bc / ab;
            var bcCd = cd / bc;
            var xaAd = Math.Abs(p[4].Price - p[0].Price) / xa;

            if (!Between(xaAb, 0.618, 0.886) || !Between(abBc, 0.382, 0.886) ||
                !Between(bcCd, 1.128, 2.618) || !Between(xaAd, 0.786, 1.272))
                return null;

            var score = (Clamp01(1 - Math.Abs(xaAb - 0.786)) +
                         Clamp01(1 - Math.Abs(abBc - 0.500)) +
                         Clamp01(1 - Math.Abs(bcCd - 1.272) / 1.5) +
                         Clamp01(1 - Math.Abs(xaAd - 1.000))) / 4.0;

            var d = p[4];
            var c = p[3];
            var direction = d.Price < c.Price ? TradeType.Buy : TradeType.Sell;
            var protection = Math.Max(Math.Abs(d.Price - p[0].Price) * 0.15, xa * 0.08);
            if (protection <= 0)
                return null;

            return new Pattern
            {
                TradeType = direction,
                StopPrice = direction == TradeType.Buy ? d.Price - protection : d.Price + protection,
                Score = score
            };
        }

        private Pivot[] RecentPivots(int currentIndex)
        {
            var pivots = new List<Pivot>();
            var start = Math.Max(SwingDepth, currentIndex - LookbackBars);
            var end = currentIndex - SwingDepth;
            if (end <= start)
                return null;

            for (var i = start; i <= end; i++)
            {
                var high = true;
                var low = true;
                for (var j = 1; j <= SwingDepth; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i - j] || Bars.HighPrices[i] < Bars.HighPrices[i + j]) high = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i - j] || Bars.LowPrices[i] > Bars.LowPrices[i + j]) low = false;
                    if (!high && !low) break;
                }
                if (!high && !low) continue;

                var candidate = new Pivot { Index = i, Price = high ? Bars.HighPrices[i] : Bars.LowPrices[i], IsHigh = high };
                if (pivots.Count == 0)
                {
                    pivots.Add(candidate);
                    continue;
                }

                var last = pivots[pivots.Count - 1];
                if (last.IsHigh == candidate.IsHigh)
                {
                    if ((candidate.IsHigh && candidate.Price > last.Price) || (!candidate.IsHigh && candidate.Price < last.Price))
                        pivots[pivots.Count - 1] = candidate;
                }
                else
                {
                    pivots.Add(candidate);
                }
            }

            return pivots.Count < 5 ? null : pivots.Skip(pivots.Count - 5).Take(5).ToArray();
        }

        private bool MarketFilterPasses(int index)
        {
            const int volPeriod = 14;
            const int trendPeriod = 21;
            const int volumePeriod = 10;
            if (index < trendPeriod + 2)
                return false;

            var volatility = 0.0;
            for (var i = index - volPeriod + 1; i <= index; i++)
            {
                var avg = (Bars.HighPrices[i] + Bars.LowPrices[i] + Bars.ClosePrices[i]) / 3.0;
                if (avg > 0) volatility += (Bars.HighPrices[i] - Bars.LowPrices[i]) / avg;
            }
            volatility /= volPeriod;
            if (volatility < MinVolatility || volatility > MaxVolatility)
                return false;

            var change = 0.0;
            var priceSum = 0.0;
            for (var i = index - trendPeriod + 1; i <= index; i++)
            {
                change += Bars.ClosePrices[i] - Bars.ClosePrices[i - 1];
                priceSum += Bars.ClosePrices[i];
            }
            var avgPrice = priceSum / trendPeriod;
            var trendStrength = avgPrice > 0 ? change / (trendPeriod * avgPrice) : 0.0;
            if (Math.Abs(trendStrength) < MinTrendStrength)
                return false;

            var avgVolume = 0.0;
            for (var i = index - volumePeriod + 1; i <= index; i++) avgVolume += Bars.TickVolumes[i];
            avgVolume /= volumePeriod;
            return avgVolume > 0 && Bars.TickVolumes[index] / avgVolume >= MinVolumeRatio;
        }

        private bool HasPosition()
        {
            if (Positions.FindAll(Label, SymbolName).Length > 0)
                return true;
            if (!BlockAnySymbolPosition)
                return false;
            foreach (var p in Positions)
                if (p.SymbolName == SymbolName)
                    return true;
            return false;
        }

        private bool RiskBlocked()
        {
            if (_dayStartEquity > 0 && (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0 >= DailyLossLimit) return true;
            if (_weekStartEquity > 0 && (_weekStartEquity - Account.Equity) / _weekStartEquity * 100.0 >= WeeklyLossLimit) return true;
            if (_peakEquity > 0 && (_peakEquity - Account.Equity) / _peakEquity * 100.0 >= MaxDrawdown) return true;
            return false;
        }

        private bool EmergencyTriggered()
        {
            return _initialEquity > 0 && (_initialEquity - Account.Equity) / _initialEquity * 100.0 >= EmergencyStop;
        }

        private void CloseOwnPositions()
        {
            foreach (var p in Positions.FindAll(Label, SymbolName))
                ClosePosition(p);
        }

        private void RefreshRiskAnchors()
        {
            if (Server.Time.Date != _day)
            {
                _day = Server.Time.Date;
                _dayStartEquity = Account.Equity;
            }
            var week = WeekOfYear(Server.Time);
            if (week != _week)
            {
                _week = week;
                _weekStartEquity = Account.Equity;
            }
        }

        private bool InCooldown()
        {
            return CooldownMinutes > 0 && _lastTradeTime.HasValue && Server.Time < _lastTradeTime.Value.AddMinutes(CooldownMinutes);
        }

        private bool InSession(int hour)
        {
            if (TradeStartUtc == TradeEndUtc) return true;
            if (TradeStartUtc < TradeEndUtc) return hour >= TradeStartUtc && hour < TradeEndUtc;
            return hour >= TradeStartUtc || hour < TradeEndUtc;
        }

        private static int WeekOfYear(DateTime dt)
        {
            return CultureInfo.InvariantCulture.Calendar.GetWeekOfYear(dt, CalendarWeekRule.FirstFourDayWeek, DayOfWeek.Monday);
        }

        private static bool Between(double v, double min, double max) { return v >= min && v <= max; }
        private static double Clamp01(double v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }
    }
}
