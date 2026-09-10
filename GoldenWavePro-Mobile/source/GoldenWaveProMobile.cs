using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GoldenWaveProMobile : Robot
    {
        [Parameter("Bot Label", DefaultValue = "GoldenWavePro")]
        public string BotLabel { get; set; }

        [Parameter("Risk Per Trade (%)", DefaultValue = 0.30, MinValue = 0.05, MaxValue = 5.0, Step = 0.05)]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Min Reward/Risk", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 10.0, Step = 0.1)]
        public double MinRewardRisk { get; set; }

        [Parameter("Pattern Confidence", DefaultValue = 0.92, MinValue = 0.50, MaxValue = 0.99, Step = 0.01)]
        public double MinPatternConfidence { get; set; }

        [Parameter("Fibonacci Tolerance", DefaultValue = 0.08, MinValue = 0.01, MaxValue = 0.25, Step = 0.01)]
        public double FibonacciTolerance { get; set; }

        [Parameter("Swing Depth", DefaultValue = 4, MinValue = 2, MaxValue = 20)]
        public int SwingDepth { get; set; }

        [Parameter("Pattern Lookback", DefaultValue = 180, MinValue = 40, MaxValue = 1000)]
        public int PatternLookback { get; set; }

        [Parameter("Cooldown (minutes)", DefaultValue = 15, MinValue = 0, MaxValue = 1440)]
        public int CooldownMinutes { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 50.0, MinValue = 0.1, MaxValue = 10000.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Daily Loss Limit (%)", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 50.0)]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Max Drawdown (%)", DefaultValue = 18.0, MinValue = 0.0, MaxValue = 80.0)]
        public double MaxDrawdownPercent { get; set; }

        [Parameter("Emergency Equity Stop (%)", DefaultValue = 25.0, MinValue = 0.0, MaxValue = 90.0)]
        public double EmergencyStopPercent { get; set; }

        private DateTime _lastEntryTime = DateTime.MinValue;
        private int _lastPatternDIndex = -1;
        private DateTime _equityDay;
        private double _dayStartEquity;
        private double _initialEquity;
        private double _peakEquity;
        private bool _riskStop;

        protected override void OnStart()
        {
            _initialEquity = Account.Equity;
            _peakEquity = Account.Equity;
            _dayStartEquity = Account.Equity;
            _equityDay = Server.Time.Date;
            Print("GoldenWaveProMobile started on {0}. Risk={1:F2}%", SymbolName, RiskPerTradePercent);
        }

        protected override void OnBar()
        {
            UpdateRiskState();
            if (_riskStop || !IsRiskStateValid())
                return;

            if (HasOpenPosition())
                return;

            if (CooldownMinutes > 0 && _lastEntryTime != DateTime.MinValue &&
                (Server.Time - _lastEntryTime).TotalMinutes < CooldownMinutes)
                return;

            var spreadPips = Symbol.Spread / Symbol.PipSize;
            if (spreadPips > MaxSpreadPips)
                return;

            var lastClosedIndex = Bars.Count - 2;
            if (lastClosedIndex < Math.Max(30, SwingDepth * 4))
                return;

            PatternSignal signal;
            if (!TryDetectGartley(lastClosedIndex, out signal))
                return;

            if (signal.DIndex == _lastPatternDIndex || signal.Confidence < MinPatternConfidence)
                return;

            var entryPrice = signal.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            var stopDistance = signal.Direction == TradeType.Buy
                ? entryPrice - signal.StopPrice
                : signal.StopPrice - entryPrice;

            if (stopDistance <= 0)
                return;

            var stopLossPips = stopDistance / Symbol.PipSize;
            if (stopLossPips <= 0 || double.IsNaN(stopLossPips) || double.IsInfinity(stopLossPips))
                return;

            var takeProfitPips = stopLossPips * MinRewardRisk;
            var volume = Symbol.VolumeForProportionalRisk(
                ProportionalAmountType.Equity,
                RiskPerTradePercent,
                stopLossPips,
                RoundingMode.Down);

            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            volume = Math.Max(Symbol.VolumeInUnitsMin, Math.Min(Symbol.VolumeInUnitsMax, volume));

            if (volume < Symbol.VolumeInUnitsMin)
                return;

            var result = ExecuteMarketOrder(
                signal.Direction,
                SymbolName,
                volume,
                BotLabel,
                stopLossPips,
                takeProfitPips);

            if (result.IsSuccessful)
            {
                _lastEntryTime = Server.Time;
                _lastPatternDIndex = signal.DIndex;
                Print("{0} Gartley | confidence={1:F3} | volume={2} | SL={3:F1} pips | TP={4:F1} pips",
                    signal.Direction, signal.Confidence, volume, stopLossPips, takeProfitPips);
            }
            else
            {
                Print("Order failed: {0}", result.Error);
            }
        }

        private void UpdateRiskState()
        {
            if (Server.Time.Date != _equityDay)
            {
                _equityDay = Server.Time.Date;
                _dayStartEquity = Account.Equity;
            }

            if (Account.Equity > _peakEquity)
                _peakEquity = Account.Equity;
        }

        private bool IsRiskStateValid()
        {
            if (_initialEquity > 0 && EmergencyStopPercent > 0)
            {
                var emergencyLoss = (_initialEquity - Account.Equity) / _initialEquity * 100.0;
                if (emergencyLoss >= EmergencyStopPercent)
                {
                    TriggerRiskStop("Emergency equity stop");
                    return false;
                }
            }

            if (_dayStartEquity > 0 && DailyLossLimitPercent > 0)
            {
                var dailyLoss = (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0;
                if (dailyLoss >= DailyLossLimitPercent)
                {
                    TriggerRiskStop("Daily loss limit");
                    return false;
                }
            }

            if (_peakEquity > 0 && MaxDrawdownPercent > 0)
            {
                var drawdown = (_peakEquity - Account.Equity) / _peakEquity * 100.0;
                if (drawdown >= MaxDrawdownPercent)
                {
                    TriggerRiskStop("Maximum drawdown limit");
                    return false;
                }
            }

            return true;
        }

        private void TriggerRiskStop(string reason)
        {
            if (_riskStop)
                return;

            _riskStop = true;
            foreach (var position in Positions.FindAll(BotLabel, SymbolName))
                ClosePosition(position);

            Print("Trading stopped: {0}", reason);
        }

        private bool HasOpenPosition()
        {
            return Positions.FindAll(BotLabel, SymbolName).Length > 0;
        }

        private bool TryDetectGartley(int lastClosedIndex, out PatternSignal signal)
        {
            signal = null;
            var pivots = FindPivots(lastClosedIndex);
            if (pivots.Count < 5)
                return false;

            var p = pivots.Skip(pivots.Count - 5).ToArray();
            if (!AreAlternating(p))
                return false;

            var x = p[0];
            var a = p[1];
            var b = p[2];
            var c = p[3];
            var d = p[4];

            var xa = Math.Abs(a.Price - x.Price);
            var ab = Math.Abs(b.Price - a.Price);
            var bc = Math.Abs(c.Price - b.Price);
            var cd = Math.Abs(d.Price - c.Price);
            var ad = Math.Abs(d.Price - x.Price);
            if (xa <= 0 || ab <= 0 || bc <= 0)
                return false;

            var abXa = ab / xa;
            var bcAb = bc / ab;
            var cdBc = cd / bc;
            var adXa = ad / xa;

            var score1 = RatioScore(abXa, 0.618, FibonacciTolerance);
            var score2 = RangeScore(bcAb, 0.382, 0.886);
            var score3 = RangeScore(cdBc, 1.13, 1.618);
            var score4 = RatioScore(adXa, 0.786, FibonacciTolerance * 1.25);
            var confidence = (score1 + score2 + score3 + score4) / 4.0;

            if (confidence < MinPatternConfidence)
                return false;

            TradeType direction;
            if (!d.IsHigh && a.IsHigh && c.IsHigh)
                direction = TradeType.Buy;
            else if (d.IsHigh && !a.IsHigh && !c.IsHigh)
                direction = TradeType.Sell;
            else
                return false;

            var entryReference = Bars.ClosePrices[lastClosedIndex];
            double stopPrice;
            if (direction == TradeType.Buy)
            {
                var structuralLow = Math.Min(x.Price, Math.Min(b.Price, d.Price));
                var rawDistance = Math.Max(Symbol.PipSize, entryReference - structuralLow);
                stopPrice = entryReference - rawDistance * 1.30;
            }
            else
            {
                var structuralHigh = Math.Max(x.Price, Math.Max(b.Price, d.Price));
                var rawDistance = Math.Max(Symbol.PipSize, structuralHigh - entryReference);
                stopPrice = entryReference + rawDistance * 1.30;
            }

            signal = new PatternSignal
            {
                Direction = direction,
                Confidence = confidence,
                StopPrice = stopPrice,
                DIndex = d.Index
            };
            return true;
        }

        private List<Pivot> FindPivots(int lastClosedIndex)
        {
            var pivots = new List<Pivot>();
            var start = Math.Max(SwingDepth, lastClosedIndex - PatternLookback);
            var end = lastClosedIndex - SwingDepth;

            for (var i = start; i <= end; i++)
            {
                var isHigh = true;
                var isLow = true;
                var high = Bars.HighPrices[i];
                var low = Bars.LowPrices[i];

                for (var j = i - SwingDepth; j <= i + SwingDepth; j++)
                {
                    if (j == i)
                        continue;
                    if (Bars.HighPrices[j] > high)
                        isHigh = false;
                    if (Bars.LowPrices[j] < low)
                        isLow = false;
                    if (!isHigh && !isLow)
                        break;
                }

                if (isHigh == isLow)
                    continue;

                var candidate = new Pivot { Index = i, Price = isHigh ? high : low, IsHigh = isHigh };
                if (pivots.Count == 0)
                {
                    pivots.Add(candidate);
                    continue;
                }

                var previous = pivots[pivots.Count - 1];
                if (previous.IsHigh == candidate.IsHigh)
                {
                    var moreExtreme = candidate.IsHigh ? candidate.Price > previous.Price : candidate.Price < previous.Price;
                    if (moreExtreme)
                        pivots[pivots.Count - 1] = candidate;
                }
                else
                {
                    pivots.Add(candidate);
                }
            }

            return pivots;
        }

        private static bool AreAlternating(IReadOnlyList<Pivot> p)
        {
            for (var i = 1; i < p.Count; i++)
                if (p[i].IsHigh == p[i - 1].IsHigh)
                    return false;
            return true;
        }

        private static double RatioScore(double value, double target, double tolerance)
        {
            if (target <= 0 || tolerance <= 0)
                return 0;
            var relativeError = Math.Abs(value - target) / target;
            return Math.Max(0.0, 1.0 - relativeError / tolerance);
        }

        private static double RangeScore(double value, double min, double max)
        {
            if (value < min || value > max)
                return 0;
            var center = (min + max) / 2.0;
            var half = (max - min) / 2.0;
            if (half <= 0)
                return 1.0;
            return Math.Max(0.0, 1.0 - Math.Abs(value - center) / half * 0.25);
        }

        private sealed class Pivot
        {
            public int Index { get; set; }
            public double Price { get; set; }
            public bool IsHigh { get; set; }
        }

        private sealed class PatternSignal
        {
            public TradeType Direction { get; set; }
            public double Confidence { get; set; }
            public double StopPrice { get; set; }
            public int DIndex { get; set; }
        }
    }
}
