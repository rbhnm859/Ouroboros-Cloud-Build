using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Use Live Tick Pressure", Group = "Signal", DefaultValue = false)]
        public bool UseLiveTickPressure { get; set; }

        [Parameter("Min Previous Pressure Fraction", Group = "Signal", DefaultValue = 0.30, MinValue = 0.0, MaxValue = 1.0, Step = 0.05)]
        public double MinPreviousPressureFraction { get; set; }

        [Parameter("Breakout Buffer ATR", Group = "Signal", DefaultValue = 0.05, MinValue = 0.0, MaxValue = 0.50, Step = 0.01)]
        public double BreakoutBufferAtr { get; set; }

        [Parameter("Max Entry Candle ATR", Group = "Signal", DefaultValue = 1.60, MinValue = 0.5, MaxValue = 5.0, Step = 0.05)]
        public double MaxEntryCandleAtr { get; set; }

        [Parameter("Max EMA Extension ATR", Group = "Signal", DefaultValue = 0.90, MinValue = 0.1, MaxValue = 3.0, Step = 0.05)]
        public double MaxEmaExtensionAtr { get; set; }

        [Parameter("Pullback Slow EMA Penetration ATR", Group = "Signal", DefaultValue = 0.10, MinValue = 0.0, MaxValue = 1.0, Step = 0.05)]
        public double PullbackSlowPenetrationAtr { get; set; }

        [Parameter("Min EMA Gap ATR", Group = "Trend", DefaultValue = 0.05, MinValue = 0.0, MaxValue = 1.0, Step = 0.01)]
        public double MinEmaGapAtr { get; set; }

        private double ComputeAndStorePressure(int index)
        {
            WarmupPressureHistoryIfNeeded(index);
            var pressure = CalculatePressure(index, true);
            StorePressure(pressure);
            return pressure;
        }

        private void WarmupPressureHistoryIfNeeded(int currentClosedIndex)
        {
            if (_pressureHistory.Count > 0 || currentClosedIndex <= 1)
                return;

            // Reconstruct enough deterministic closed-bar history after startup/restart. Historical
            // raw tick direction is intentionally not guessed; candle/tick-volume features are fully
            // available in both bar-data backtests and live charts.
            var needed = Math.Max(PressureWindow, PersistenceLookback) + 12;
            var start = Math.Max(1, currentClosedIndex - needed);
            for (var i = start; i < currentClosedIndex; i++)
                StorePressure(CalculatePressure(i, false));
        }

        private double CalculatePressure(int index, bool allowCurrentTickPressure)
        {
            var high = Bars.HighPrices[index];
            var low = Bars.LowPrices[index];
            var open = Bars.OpenPrices[index];
            var close = Bars.ClosePrices[index];
            var range = Math.Max(high - low, Symbol.TickSize);

            var bodyScore = Clamp(100.0 * (close - open) / range, -100.0, 100.0);
            var closeLocation = Clamp(100.0 * (2.0 * (close - low) / range - 1.0), -100.0, 100.0);

            var volumeNow = Math.Max(1.0, Bars.TickVolumes[index]);
            var start = Math.Max(0, index - 10);
            double volumeSum = 0;
            int volumeCount = 0;
            for (var i = start; i < index; i++)
            {
                volumeSum += Math.Max(1.0, Bars.TickVolumes[i]);
                volumeCount++;
            }
            var volumeAvg = volumeCount == 0 ? volumeNow : volumeSum / volumeCount;
            var volumeImpulse = Clamp(volumeNow / Math.Max(1.0, volumeAvg), 0.65, 1.35);

            // Commercial default is deterministic across m1 server-data backtests, restart and live.
            // Raw tick direction is optional/experimental until separately validated with tick-mode data.
            var useTick = UseLiveTickPressure && allowCurrentTickPressure && _lastCompletedTickSamples >= 8;
            var tickScore = useTick ? _lastCompletedTickPressure : 0.0;
            var tickWeight = useTick ? 0.25 : 0.0;
            var candleWeight = 1.0 - tickWeight;
            var candlePressure = 0.62 * bodyScore + 0.38 * closeLocation;
            return Clamp((candleWeight * candlePressure + tickWeight * tickScore) * volumeImpulse, -100.0, 100.0);
        }

        private void StorePressure(double pressure)
        {
            _pressureHistory.Add(pressure);
            var keep = Math.Max(100, PressureWindow + PersistenceLookback + 30);
            if (_pressureHistory.Count > keep)
                _pressureHistory.RemoveRange(0, _pressureHistory.Count - keep);
        }

        private EntryCandidate BuildEntryCandidate(int index, double latestPressure)
        {
            if (_pressureHistory.Count < Math.Max(PressureWindow, PersistenceLookback))
                return EntryCandidate.Invalid();

            var recent = _pressureHistory.Skip(Math.Max(0, _pressureHistory.Count - PressureWindow)).ToArray();
            var persistence = _pressureHistory.Skip(Math.Max(0, _pressureHistory.Count - PersistenceLookback)).ToArray();
            var avgPressure = recent.Average();

            // Zero pressure is neutral; it must not count toward both bullish and bearish persistence.
            var bullishBars = persistence.Count(x => x > 0);
            var bearishBars = persistence.Count(x => x < 0);
            var previousPressure = _pressureHistory.Count >= 2 ? _pressureHistory[_pressureHistory.Count - 2] : 0.0;

            TradeType direction;
            if (avgPressure >= MinAveragePressure &&
                latestPressure >= MinLastPressure &&
                previousPressure >= MinLastPressure * MinPreviousPressureFraction &&
                bullishBars >= MinDirectionalBars)
            {
                direction = TradeType.Buy;
            }
            else if (avgPressure <= -MinAveragePressure &&
                     latestPressure <= -MinLastPressure &&
                     previousPressure <= -MinLastPressure * MinPreviousPressureFraction &&
                     bearishBars >= MinDirectionalBars)
            {
                direction = TradeType.Sell;
            }
            else
            {
                return EntryCandidate.Invalid();
            }

            var atrPrice = _atr.Result[index];
            if (atrPrice <= 0 || double.IsNaN(atrPrice) || double.IsInfinity(atrPrice))
                return EntryCandidate.Invalid();

            if (!PassCandleQuality(index, direction, atrPrice))
                return EntryCandidate.Invalid();

            var momentumR = (Bars.ClosePrices[index] - Bars.ClosePrices[Math.Max(0, index - 3)]) / atrPrice;
            if (direction == TradeType.Buy && momentumR < 0.08)
                return EntryCandidate.Invalid();
            if (direction == TradeType.Sell && momentumR > -0.08)
                return EntryCandidate.Invalid();

            // Do not chase already exhausted multi-bar impulses.
            if (Math.Abs(momentumR) > 2.25)
                return EntryCandidate.Invalid();

            if (!PassLocalTrend(index, direction, atrPrice))
                return EntryCandidate.Invalid();
            if (!PassM15Trend(direction))
                return EntryCandidate.Invalid();
            if (RequireH1Agreement && !PassH1Trend(direction))
                return EntryCandidate.Invalid();
            if (!PassDms(index, direction))
                return EntryCandidate.Invalid();

            var setup = GetStructureSetup(index, direction, atrPrice);
            if (setup == null)
                return EntryCandidate.Invalid();

            return new EntryCandidate
            {
                IsValid = true,
                Direction = direction,
                Pressure = avgPressure,
                MomentumR = momentumR,
                Setup = setup
            };
        }

        private bool PassCandleQuality(int index, TradeType direction, double atrPrice)
        {
            var high = Bars.HighPrices[index];
            var low = Bars.LowPrices[index];
            var open = Bars.OpenPrices[index];
            var close = Bars.ClosePrices[index];
            var range = high - low;
            if (range <= Symbol.TickSize || atrPrice <= 0)
                return false;

            var body = Math.Abs(close - open);
            if (body / range < MinBodyToRange)
                return false;
            if (range / atrPrice > MaxEntryCandleAtr)
                return false;

            var closeLocation = (close - low) / range;
            if (direction == TradeType.Buy)
            {
                if (close <= open || closeLocation < 0.60)
                    return false;
            }
            else
            {
                if (close >= open || closeLocation > 0.40)
                    return false;
            }
            return true;
        }

        private bool PassLocalTrend(int index, TradeType direction, double atrPrice)
        {
            var fast = _fastEma.Result[index];
            var slow = _slowEma.Result[index];
            var slopeIndex = Math.Max(0, index - EmaSlopeBars);
            var slope = fast - _fastEma.Result[slopeIndex];
            var close = Bars.ClosePrices[index];
            var emaGapR = atrPrice <= 0 ? 0 : Math.Abs(fast - slow) / atrPrice;
            var extensionR = atrPrice <= 0 ? double.PositiveInfinity : Math.Abs(close - fast) / atrPrice;

            if (emaGapR < MinEmaGapAtr || extensionR > MaxEmaExtensionAtr)
                return false;

            if (direction == TradeType.Buy)
                return fast > slow && slope > 0 && close > fast;
            return fast < slow && slope < 0 && close < fast;
        }

        private bool PassM15Trend(TradeType direction)
        {
            if (_m15Bars == null || _m15Bars.Count < SlowEmaPeriod + EmaSlopeBars + 5)
                return false;
            var i = _m15Bars.Count - 2;
            var prev = Math.Max(0, i - EmaSlopeBars);
            var fast = _m15Fast.Result[i];
            var slow = _m15Slow.Result[i];
            var slope = fast - _m15Fast.Result[prev];
            var close = _m15Bars.ClosePrices[i];
            return direction == TradeType.Buy
                ? fast > slow && slope > 0 && close > fast
                : fast < slow && slope < 0 && close < fast;
        }

        private bool PassH1Trend(TradeType direction)
        {
            if (_h1Bars == null || _h1Bars.Count < SlowEmaPeriod + EmaSlopeBars + 5)
                return false;
            var i = _h1Bars.Count - 2;
            var prev = Math.Max(0, i - EmaSlopeBars);
            var fast = _h1Fast.Result[i];
            var slow = _h1Slow.Result[i];
            var slope = fast - _h1Fast.Result[prev];
            var close = _h1Bars.ClosePrices[i];
            return direction == TradeType.Buy
                ? fast > slow && slope >= 0 && close > fast
                : fast < slow && slope <= 0 && close < fast;
        }

        private bool PassDms(int index, TradeType direction)
        {
            var adx = _dms.ADX[index];
            if (double.IsNaN(adx) || adx < MinAdx)
                return false;
            if (direction == TradeType.Buy)
                return _dms.DIPlus[index] > _dms.DIMinus[index];
            return _dms.DIMinus[index] > _dms.DIPlus[index];
        }

        private string GetStructureSetup(int index, TradeType direction, double atrPrice)
        {
            if (index <= StructureLookback + 2 || atrPrice <= 0)
                return null;

            double priorHigh = double.MinValue;
            double priorLow = double.MaxValue;
            for (var i = index - StructureLookback; i < index; i++)
            {
                priorHigh = Math.Max(priorHigh, Bars.HighPrices[i]);
                priorLow = Math.Min(priorLow, Bars.LowPrices[i]);
            }

            var close = Bars.ClosePrices[index];
            var breakoutBuffer = BreakoutBufferAtr * atrPrice;
            if (direction == TradeType.Buy && close > priorHigh + breakoutBuffer)
                return "breakout";
            if (direction == TradeType.Sell && close < priorLow - breakoutBuffer)
                return "breakout";

            if (!AllowPullbackContinuation)
                return null;

            var fast = _fastEma.Result[index];
            var slow = _slowEma.Result[index];
            var previousFast = _fastEma.Result[index - 1];
            var tolerance = 0.20 * atrPrice;
            var slowPenetration = PullbackSlowPenetrationAtr * atrPrice;

            if (direction == TradeType.Buy)
            {
                var trendWasIntact = Bars.ClosePrices[index - 1] > previousFast;
                var touched = Bars.LowPrices[index] <= fast + tolerance;
                var depthOk = Bars.LowPrices[index] >= slow - slowPenetration;
                var reclaimed = close > fast && close > Bars.OpenPrices[index];
                if (trendWasIntact && touched && depthOk && reclaimed)
                    return "pullback";
            }
            else
            {
                var trendWasIntact = Bars.ClosePrices[index - 1] < previousFast;
                var touched = Bars.HighPrices[index] >= fast - tolerance;
                var depthOk = Bars.HighPrices[index] <= slow + slowPenetration;
                var reclaimed = close < fast && close < Bars.OpenPrices[index];
                if (trendWasIntact && touched && depthOk && reclaimed)
                    return "pullback";
            }

            return null;
        }

        private static double Clamp(double value, double min, double max)
        {
            return Math.Max(min, Math.Min(max, value));
        }
    }
}
