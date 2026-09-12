using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private double ComputeAndStorePressure(int index)
        {
            var high = Bars.HighPrices[index];
            var low = Bars.LowPrices[index];
            var open = Bars.OpenPrices[index];
            var close = Bars.ClosePrices[index];
            var range = Math.Max(high - low, Symbol.TickSize);

            var bodyScore = Clamp(100.0 * (close - open) / range, -100.0, 100.0);
            var closeLocation = Clamp(100.0 * (2.0 * (close - low) / range - 1.0), -100.0, 100.0);
            var tickScore = _lastCompletedTickSamples >= 8 ? _lastCompletedTickPressure : 0.0;

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

            // Deterministic on M1 backtests: candle pressure dominates when raw tick samples are unavailable.
            var tickWeight = _lastCompletedTickSamples >= 8 ? 0.25 : 0.0;
            var candleWeight = 1.0 - tickWeight;
            var candlePressure = 0.62 * bodyScore + 0.38 * closeLocation;
            var pressure = Clamp((candleWeight * candlePressure + tickWeight * tickScore) * volumeImpulse, -100.0, 100.0);

            _pressureHistory.Add(pressure);
            var keep = Math.Max(100, PressureWindow + PersistenceLookback + 30);
            if (_pressureHistory.Count > keep)
                _pressureHistory.RemoveRange(0, _pressureHistory.Count - keep);

            return pressure;
        }

        private EntryCandidate BuildEntryCandidate(int index, double latestPressure)
        {
            if (_pressureHistory.Count < Math.Max(PressureWindow, PersistenceLookback))
                return EntryCandidate.Invalid();

            var recent = _pressureHistory.Skip(Math.Max(0, _pressureHistory.Count - PressureWindow)).ToArray();
            var persistence = _pressureHistory.Skip(Math.Max(0, _pressureHistory.Count - PersistenceLookback)).ToArray();
            var avgPressure = recent.Average();

            var bullishBars = persistence.Count(x => x >= 0);
            var bearishBars = persistence.Count(x => x <= 0);

            TradeType direction;
            if (avgPressure >= MinAveragePressure && latestPressure >= MinLastPressure && bullishBars >= MinDirectionalBars)
                direction = TradeType.Buy;
            else if (avgPressure <= -MinAveragePressure && latestPressure <= -MinLastPressure && bearishBars >= MinDirectionalBars)
                direction = TradeType.Sell;
            else
                return EntryCandidate.Invalid();

            if (!PassCandleQuality(index, direction))
                return EntryCandidate.Invalid();

            var atrPrice = _atr.Result[index];
            if (atrPrice <= 0 || double.IsNaN(atrPrice))
                return EntryCandidate.Invalid();

            var momentumR = (Bars.ClosePrices[index] - Bars.ClosePrices[Math.Max(0, index - 3)]) / atrPrice;
            if (direction == TradeType.Buy && momentumR < 0.08)
                return EntryCandidate.Invalid();
            if (direction == TradeType.Sell && momentumR > -0.08)
                return EntryCandidate.Invalid();

            if (!PassLocalTrend(index, direction))
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

        private bool PassCandleQuality(int index, TradeType direction)
        {
            var range = Bars.HighPrices[index] - Bars.LowPrices[index];
            if (range <= Symbol.TickSize)
                return false;
            var body = Math.Abs(Bars.ClosePrices[index] - Bars.OpenPrices[index]);
            if (body / range < MinBodyToRange)
                return false;
            if (direction == TradeType.Buy && Bars.ClosePrices[index] <= Bars.OpenPrices[index])
                return false;
            if (direction == TradeType.Sell && Bars.ClosePrices[index] >= Bars.OpenPrices[index])
                return false;
            return true;
        }

        private bool PassLocalTrend(int index, TradeType direction)
        {
            var fast = _fastEma.Result[index];
            var slow = _slowEma.Result[index];
            var slopeIndex = Math.Max(0, index - EmaSlopeBars);
            var slope = fast - _fastEma.Result[slopeIndex];

            if (direction == TradeType.Buy)
                return fast > slow && slope > 0 && Bars.ClosePrices[index] > fast;
            return fast < slow && slope < 0 && Bars.ClosePrices[index] < fast;
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
            return direction == TradeType.Buy ? fast > slow && slope > 0 : fast < slow && slope < 0;
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
            return direction == TradeType.Buy ? fast > slow && slope >= 0 : fast < slow && slope <= 0;
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
            if (index <= StructureLookback + 2)
                return null;

            double priorHigh = double.MinValue;
            double priorLow = double.MaxValue;
            for (var i = index - StructureLookback; i < index; i++)
            {
                priorHigh = Math.Max(priorHigh, Bars.HighPrices[i]);
                priorLow = Math.Min(priorLow, Bars.LowPrices[i]);
            }

            var close = Bars.ClosePrices[index];
            if (direction == TradeType.Buy && close > priorHigh)
                return "breakout";
            if (direction == TradeType.Sell && close < priorLow)
                return "breakout";

            if (!AllowPullbackContinuation)
                return null;

            var fast = _fastEma.Result[index];
            var tolerance = 0.20 * atrPrice;
            if (direction == TradeType.Buy)
            {
                var touched = Bars.LowPrices[index] <= fast + tolerance;
                var reclaimed = close > fast && close > Bars.OpenPrices[index];
                if (touched && reclaimed)
                    return "pullback";
            }
            else
            {
                var touched = Bars.HighPrices[index] >= fast - tolerance;
                var reclaimed = close < fast && close < Bars.OpenPrices[index];
                if (touched && reclaimed)
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
