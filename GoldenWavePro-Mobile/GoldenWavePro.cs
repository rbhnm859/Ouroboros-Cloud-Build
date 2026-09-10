using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public enum GoldenWaveDirection
    {
        Buy,
        Sell
    }

    public sealed class GoldenWavePivot
    {
        public int BarIndex { get; set; }
        public double Price { get; set; }
        public bool IsHigh { get; set; }
    }

    public sealed class FibonacciRatios
    {
        public double XA_AB { get; set; }
        public double AB_BC { get; set; }
        public double BC_CD { get; set; }
        public double XA_AD { get; set; }
    }

    public sealed class PatternMatchResult
    {
        public string Type { get; set; }
        public double EntryPoint { get; set; }
        public double StopLossLevel { get; set; }
        public double Confidence { get; set; }
        public GoldenWaveDirection Direction { get; set; }
        public GoldenWavePivot[] PatternPoints { get; set; }
    }

    [Robot(Name = "GoldenWavePro Mobile", TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GoldenWavePro : Robot
    {
        private const string BotLabel = "GoldenWavePro";

        [Parameter("Risk Per Trade (%)", Group = "Risk", DefaultValue = 0.30, MinValue = 0.05, MaxValue = 2.0, Step = 0.05)]
        public double RiskPerTradePercent { get; set; }

        [Parameter("Reward / Risk", Group = "Risk", DefaultValue = 1.618, MinValue = 1.0, MaxValue = 5.0, Step = 0.1)]
        public double RewardRisk { get; set; }

        [Parameter("Daily Loss Limit (%)", Group = "Risk", DefaultValue = 5.0, MinValue = 0.5, MaxValue = 25.0)]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Weekly Loss Limit (%)", Group = "Risk", DefaultValue = 12.0, MinValue = 1.0, MaxValue = 40.0)]
        public double WeeklyLossLimitPercent { get; set; }

        [Parameter("Max Drawdown (%)", Group = "Risk", DefaultValue = 18.0, MinValue = 1.0, MaxValue = 50.0)]
        public double MaxDrawdownPercent { get; set; }

        [Parameter("Emergency Stop (%)", Group = "Risk", DefaultValue = 25.0, MinValue = 5.0, MaxValue = 80.0)]
        public double EmergencyStopPercent { get; set; }

        [Parameter("Min Stop (pips)", Group = "Risk", DefaultValue = 10.0, MinValue = 1.0)]
        public double MinStopLossPips { get; set; }

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
        public int TradeStartHourUtc { get; set; }

        [Parameter("Trade End UTC", Group = "Session", DefaultValue = 21, MinValue = 0, MaxValue = 23)]
        public int TradeEndHourUtc { get; set; }

        [Parameter("Cooldown Minutes", Group = "Execution", DefaultValue = 15, MinValue = 0, MaxValue = 1440)]
        public int CooldownMinutes { get; set; }

        [Parameter("Block Any Symbol Position", Group = "Execution", DefaultValue = true)]
        public bool BlockAnySymbolPosition { get; set; }

        [Parameter("Debug Logging", Group = "Execution", DefaultValue = true)]
        public bool DebugLogging { get; set; }

        private DateTime _currentDay;
        private int _currentWeek;
        private double _initialEquity;
        private double _dayStartEquity;
        private double _weekStartEquity;
        private double _peakEquity;
        private DateTime? _lastTradeTime;
        private int _lastSignalBar = -1;

        protected override void OnStart()
        {
            _initialEquity = Account.Equity;
            _dayStartEquity = Account.Equity;
            _weekStartEquity = Account.Equity;
            _peakEquity = Account.Equity;
            _currentDay = Server.Time.Date;
            _currentWeek = GetWeekOfYear(Server.Time);

            Print("GoldenWavePro Mobile started on {0}. Risk={1:F2}% RR={2:F3}", SymbolName, RiskPerTradePercent, RewardRisk);
        }

        protected override void OnBar()
        {
            try
            {
                RefreshRiskAnchors();
                UpdatePeakEquity();

                if (ShouldEmergencyClose())
                {
                    CloseBotPositions("Emergency equity stop");
                    return;
                }

                if (ShouldStopTrading())
                    return;

                if (!IsInTradingSession(Server.Time.Hour))
                    return;

                if (CooldownMinutes > 0 && _lastTradeTime.HasValue && Server.Time < _lastTradeTime.Value.AddMinutes(CooldownMinutes))
                    return;

                if (HasBlockingPosition())
                    return;

                var index = Bars.Count - 2;
                if (index < Math.Max(30, SwingDepth * 3) || index == _lastSignalBar)
                    return;

                if (UseMarketFilter && !IsValidTradingCondition(index))
                    return;

                var pattern = DetectPattern(index);
                if (pattern == null || pattern.Confidence < MinPatternScore)
                    return;

                ExecutePattern(pattern, index);
            }
            catch (Exception ex)
            {
                Print("GoldenWavePro OnBar error: {0}", ex.Message);
            }
        }

        private void ExecutePattern(PatternMatchResult pattern, int signalBar)
        {
            var tradeType = pattern.Direction == GoldenWaveDirection.Buy ? TradeType.Buy : TradeType.Sell;
            var entryPrice = tradeType == TradeType.Buy ? Symbol.Ask : Symbol.Bid;

            if ((tradeType == TradeType.Buy && pattern.StopLossLevel >= entryPrice) ||
                (tradeType == TradeType.Sell && pattern.StopLossLevel <= entryPrice))
            {
                Debug("Signal rejected: stop is on wrong side of market price.");
                return;
            }

            var stopLossPips = Math.Abs(entryPrice - pattern.StopLossLevel) / Symbol.PipSize;
            stopLossPips = Math.Max(stopLossPips, MinStopLossPips);

            if (stopLossPips <= 0 || double.IsNaN(stopLossPips) || double.IsInfinity(stopLossPips))
                return;

            var riskAmount = Account.Equity * (RiskPerTradePercent / 100.0);
            var volume = Symbol.VolumeForFixedRisk(riskAmount, stopLossPips, RoundingMode.Down);
            volume = Math.Min(volume, Symbol.VolumeInUnitsMax);
            volume = Math.Max(volume, Symbol.VolumeInUnitsMin);
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

            if (volume < Symbol.VolumeInUnitsMin)
            {
                Debug("Signal rejected: calculated volume is below broker minimum.");
                return;
            }

            var takeProfitPips = stopLossPips * RewardRisk;
            var result = ExecuteMarketOrder(tradeType, SymbolName, volume, BotLabel, stopLossPips, takeProfitPips);

            if (!result.IsSuccessful)
            {
                Print("Order failed: {0}", result.Error);
                return;
            }

            _lastTradeTime = Server.Time;
            _lastSignalBar = signalBar;

            Print("OPEN {0} {1} volume={2} score={3:F3} SL={4:F1}p TP={5:F1}p pattern={6}",
                tradeType, SymbolName, volume, pattern.Confidence, stopLossPips, takeProfitPips, pattern.Type);
        }

        private PatternMatchResult DetectPattern(int currentIndex)
        {
            var points = IdentifyRecentPivots(currentIndex);
            if (points == null || points.Length < 5)
                return null;

            var ratios = CalculateFibonacciRatios(points);
            if (!IsValidGartley(ratios))
                return null;

            var score = CalculateGartleyScore(ratios);
            if (score < MinPatternScore)
                return null;

            var d = points[4];
            var c = points[3];
            var x = points[0];
            var direction = d.Price < c.Price ? GoldenWaveDirection.Buy : GoldenWaveDirection.Sell;

            var xa = Math.Abs(points[1].Price - x.Price);
            if (xa <= 0)
                return null;

            var protectionDistance = Math.Max(Math.Abs(d.Price - x.Price) * 0.15, xa * 0.08);
            if (protectionDistance <= 0)
                return null;

            var stop = direction == GoldenWaveDirection.Buy
                ? d.Price - protectionDistance
                : d.Price + protectionDistance;

            return new PatternMatchResult
            {
                Type = "Gartley",
                EntryPoint = d.Price,
                StopLossLevel = stop,
                Confidence = score,
                Direction = direction,
                PatternPoints = points
            };
        }

        private GoldenWavePivot[] IdentifyRecentPivots(int currentIndex)
        {
            var pivots = new List<GoldenWavePivot>();
            var start = Math.Max(SwingDepth, currentIndex - LookbackBars);
            var end = currentIndex - SwingDepth;

            if (end <= start)
                return null;

            for (var i = start; i <= end; i++)
            {
                var isHigh = true;
                var isLow = true;

                for (var j = 1; j <= SwingDepth; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i - j] || Bars.HighPrices[i] < Bars.HighPrices[i + j])
                        isHigh = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i - j] || Bars.LowPrices[i] > Bars.LowPrices[i + j])
                        isLow = false;

                    if (!isHigh && !isLow)
                        break;
                }

                if (!isHigh && !isLow)
                    continue;

                var candidate = new GoldenWavePivot
                {
                    BarIndex = i,
                    Price = isHigh ? Bars.HighPrices[i] : Bars.LowPrices[i],
                    IsHigh = isHigh
                };

                if (pivots.Count == 0)
                {
                    pivots.Add(candidate);
                    continue;
                }

                var last = pivots[pivots.Count - 1];
                if (last.IsHigh == candidate.IsHigh)
                {
                    var candidateMoreExtreme = candidate.IsHigh
                        ? candidate.Price > last.Price
                        : candidate.Price < last.Price;

                    if (candidateMoreExtreme)
                        pivots[pivots.Count - 1] = candidate;
                }
                else
                {
                    pivots.Add(candidate);
                }
            }

            if (pivots.Count < 5)
                return null;

            return pivots.Skip(pivots.Count - 5).Take(5).ToArray();
        }

        private FibonacciRatios CalculateFibonacciRatios(GoldenWavePivot[] points)
        {
            var xa = Math.Abs(points[1].Price - points[0].Price);
            var ab = Math.Abs(points[2].Price - points[1].Price);
            var bc = Math.Abs(points[3].Price - points[2].Price);
            var cd = Math.Abs(points[4].Price - points[3].Price);

            if (xa <= 0 || ab <= 0 || bc <= 0)
                return new FibonacciRatios();

            return new FibonacciRatios
            {
                XA_AB = ab / xa,
                AB_BC = bc / ab,
                BC_CD = cd / bc,
                XA_AD = Math.Abs(points[4].Price - points[0].Price) / xa
            };
        }

        private static bool IsValidGartley(FibonacciRatios ratios)
        {
            return IsInRange(ratios.XA_AB, 0.618, 0.886) &&
                   IsInRange(ratios.AB_BC, 0.382, 0.886) &&
                   IsInRange(ratios.BC_CD, 1.128, 2.618) &&
                   IsInRange(ratios.XA_AD, 0.786, 1.272);
        }

        private static double CalculateGartleyScore(FibonacciRatios ratios)
        {
            var xaAbScore = Clamp01(1.0 - Math.Abs(ratios.XA_AB - 0.786));
            var abBcScore = Clamp01(1.0 - Math.Abs(ratios.AB_BC - 0.500));
            var bcCdScore = Clamp01(1.0 - Math.Abs(ratios.BC_CD - 1.272) / 1.5);
            var xaAdScore = Clamp01(1.0 - Math.Abs(ratios.XA_AD - 1.000));
            return (xaAbScore + abBcScore + bcCdScore + xaAdScore) / 4.0;
        }

        private bool IsValidTradingCondition(int currentIndex)
        {
            const int volatilityPeriod = 14;
            const int trendPeriod = 21;
            const int volumePeriod = 10;

            if (currentIndex < Math.Max(volatilityPeriod, trendPeriod) + 2)
                return false;

            var volatility = 0.0;
            for (var i = currentIndex - volatilityPeriod + 1; i <= currentIndex; i++)
            {
                var range = Bars.HighPrices[i] - Bars.LowPrices[i];
                var avgPrice = (Bars.HighPrices[i] + Bars.LowPrices[i] + Bars.ClosePrices[i]) / 3.0;
                if (avgPrice > 0)
                    volatility += range / avgPrice;
            }
            volatility /= volatilityPeriod;

            if (volatility < MinVolatility || volatility > MaxVolatility)
                return false;

            var sumChanges = 0.0;
            var sumPrices = 0.0;
            for (var i = currentIndex - trendPeriod + 1; i <= currentIndex; i++)
            {
                sumChanges += Bars.ClosePrices[i] - Bars.ClosePrices[i - 1];
                sumPrices += Bars.ClosePrices[i];
            }

            var averagePrice = sumPrices / trendPeriod;
            var trendStrength = averagePrice > 0 ? sumChanges / (trendPeriod * averagePrice) : 0.0;
            if (Math.Abs(trendStrength) < MinTrendStrength)
                return false;

            var averageVolume = 0.0;
            for (var i = currentIndex - volumePeriod + 1; i <= currentIndex; i++)
                averageVolume += Bars.TickVolumes[i];
            averageVolume /= volumePeriod;

            var volumeRatio = averageVolume > 0 ? Bars.TickVolumes[currentIndex] / averageVolume : 0.0;
            return volumeRatio >= MinVolumeRatio;
        }

        private bool HasBlockingPosition()
        {
            if (Positions.FindAll(BotLabel, SymbolName).Length > 0)
                return true;

            if (!BlockAnySymbolPosition)
                return false;

            return Positions.Any(p => p.SymbolName == SymbolName);
        }

        private bool ShouldStopTrading()
        {
            if (_dayStartEquity > 0)
            {
                var dailyLoss = (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0;
                if (dailyLoss >= DailyLossLimitPercent)
                {
                    Debug("Trading blocked by daily loss limit.");
                    return true;
                }
            }

            if (_weekStartEquity > 0)
            {
                var weeklyLoss = (_weekStartEquity - Account.Equity) / _weekStartEquity * 100.0;
                if (weeklyLoss >= WeeklyLossLimitPercent)
                {
                    Debug("Trading blocked by weekly loss limit.");
                    return true;
                }
            }

            if (_peakEquity > 0)
            {
                var drawdown = (_peakEquity - Account.Equity) / _peakEquity * 100.0;
                if (drawdown >= MaxDrawdownPercent)
                {
                    Debug("Trading blocked by max drawdown limit.");
                    return true;
                }
            }

            return false;
        }

        private bool ShouldEmergencyClose()
        {
            if (_initialEquity <= 0)
                return false;

            var loss = (_initialEquity - Account.Equity) / _initialEquity * 100.0;
            return loss >= EmergencyStopPercent;
        }

        private void CloseBotPositions(string reason)
        {
            foreach (var position in Positions.FindAll(BotLabel, SymbolName))
            {
                var result = ClosePosition(position);
                if (!result.IsSuccessful)
                    Print("Emergency close failed for position {0}: {1}", position.Id, result.Error);
            }

            Print("GoldenWavePro: {0}", reason);
        }

        private void RefreshRiskAnchors()
        {
            if (Server.Time.Date != _currentDay)
            {
                _currentDay = Server.Time.Date;
                _dayStartEquity = Account.Equity;
            }

            var week = GetWeekOfYear(Server.Time);
            if (week != _currentWeek)
            {
                _currentWeek = week;
                _weekStartEquity = Account.Equity;
            }
        }

        private void UpdatePeakEquity()
        {
            if (Account.Equity > _peakEquity)
                _peakEquity = Account.Equity;
        }

        private bool IsInTradingSession(int hourUtc)
        {
            if (TradeStartHourUtc == TradeEndHourUtc)
                return true;

            if (TradeStartHourUtc < TradeEndHourUtc)
                return hourUtc >= TradeStartHourUtc && hourUtc < TradeEndHourUtc;

            return hourUtc >= TradeStartHourUtc || hourUtc < TradeEndHourUtc;
        }

        private static int GetWeekOfYear(DateTime time)
        {
            return CultureInfo.InvariantCulture.Calendar.GetWeekOfYear(
                time,
                CalendarWeekRule.FirstFourDayWeek,
                DayOfWeek.Monday);
        }

        private static bool IsInRange(double value, double min, double max)
        {
            return value >= min && value <= max;
        }

        private static double Clamp01(double value)
        {
            if (value < 0) return 0;
            if (value > 1) return 1;
            return value;
        }

        private void Debug(string message)
        {
            if (DebugLogging)
                Print("DEBUG: {0}", message);
        }
    }
}
