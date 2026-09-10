using System;
using System.Collections.Generic;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal sealed class HarmonicSignalEngine
    {
        private readonly int _pivotLeft;
        private readonly int _pivotRight;
        private readonly int _pivotLookback;
        private readonly int _maxDAgeBars;
        private readonly double _minXaAtr;
        private readonly double _przAtrHalfWidth;
        private readonly double _przXaHalfWidth;

        public HarmonicSignalEngine(int pivotLeft, int pivotRight, int pivotLookback, int maxDAgeBars, double minXaAtr, double przAtrHalfWidth, double przXaHalfWidth)
        {
            _pivotLeft = pivotLeft;
            _pivotRight = pivotRight;
            _pivotLookback = pivotLookback;
            _maxDAgeBars = maxDAgeBars;
            _minXaAtr = minXaAtr;
            _przAtrHalfWidth = przAtrHalfWidth;
            _przXaHalfWidth = przXaHalfWidth;
        }

        public HarmonicSignal DetectLatest(Bars bars, Symbol symbol, int currentIndex, double atr)
        {
            List<PivotPoint> pivots = BuildConfirmedPivots(bars, currentIndex);
            if (pivots.Count < 5)
                return null;

            PivotPoint x = pivots[pivots.Count - 5];
            PivotPoint a = pivots[pivots.Count - 4];
            PivotPoint b = pivots[pivots.Count - 3];
            PivotPoint c = pivots[pivots.Count - 2];
            PivotPoint d = pivots[pivots.Count - 1];

            if (currentIndex - d.Index > _maxDAgeBars)
                return null;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double ad = Math.Abs(d.Price - a.Price);

            if (xa <= symbol.PipSize || ab <= symbol.PipSize || bc <= symbol.PipSize || cd <= symbol.PipSize)
                return null;
            if (xa / Math.Max(atr, symbol.PipSize) < _minXaAtr)
                return null;

            TradeType direction = d.IsHigh ? TradeType.Sell : TradeType.Buy;
            double abXa = ab / xa;
            double bcAb = bc / ab;
            double cdBc = cd / bc;
            double adXa = ad / xa;

            HarmonicSignal best = null;

            // Frozen v3.7 alpha definitions. Do not tune these against known OOS segments.
            Consider(ref best, MakeSignal("Gartley", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.618, 0.14), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.13, 1.618, 0.30), FitTarget(adXa, 0.786, 0.12),
                0.25, 0.15, 0.20, 0.40, atr, xa));

            Consider(ref best, MakeSignal("Bat", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitRange(abXa, 0.382, 0.50, 0.10), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.618, 2.618, 0.45), FitTarget(adXa, 0.886, 0.12),
                0.20, 0.15, 0.25, 0.40, atr, xa));

            Consider(ref best, MakeSignal("Butterfly", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.786, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 1.618, 2.618, 0.45), FitRange(adXa, 1.27, 1.618, 0.22),
                0.25, 0.15, 0.25, 0.35, atr, xa));

            Consider(ref best, MakeSignal("Crab", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitRange(abXa, 0.382, 0.618, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 2.24, 3.618, 0.60), FitTarget(adXa, 1.618, 0.14),
                0.20, 0.15, 0.25, 0.40, atr, xa));

            Consider(ref best, MakeSignal("DeepCrab", direction, x, a, b, c, d, abXa, bcAb, cdBc, adXa,
                FitTarget(abXa, 0.886, 0.12), FitRange(bcAb, 0.382, 0.886, 0.20), FitRange(cdBc, 2.0, 3.618, 0.65), FitTarget(adXa, 1.618, 0.14),
                0.25, 0.15, 0.20, 0.40, atr, xa));

            return best;
        }

        private HarmonicSignal MakeSignal(string name, TradeType direction, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            double abXa, double bcAb, double cdBc, double adXa,
            double q1, double q2, double q3, double q4,
            double w1, double w2, double w3, double w4,
            double atr, double xa)
        {
            double score = 100.0 * (q1 * w1 + q2 * w2 + q3 * w3 + q4 * w4);
            double przHalfWidth = Math.Max(atr * _przAtrHalfWidth, xa * _przXaHalfWidth);

            return new HarmonicSignal
            {
                PatternName = name,
                Direction = direction,
                PatternScore = score,
                X = x,
                A = a,
                B = b,
                C = c,
                D = d,
                AbXa = abXa,
                BcAb = bcAb,
                CdBc = cdBc,
                AdXa = adXa,
                Atr = atr,
                PrzLow = d.Price - przHalfWidth,
                PrzHigh = d.Price + przHalfWidth
            };
        }

        private void Consider(ref HarmonicSignal best, HarmonicSignal candidate)
        {
            if (candidate == null)
                return;
            if (best == null || candidate.PatternScore > best.PatternScore)
                best = candidate;
        }

        private List<PivotPoint> BuildConfirmedPivots(Bars bars, int endIndex)
        {
            var pivots = new List<PivotPoint>();
            int start = Math.Max(_pivotLeft, endIndex - _pivotLookback);
            int last = endIndex - _pivotRight;

            for (int i = start; i <= last; i++)
            {
                bool high = IsPivotHigh(bars, i);
                bool low = IsPivotLow(bars, i);
                if (high == low)
                    continue;

                var next = new PivotPoint(i, high ? bars.HighPrices[i] : bars.LowPrices[i], high);
                if (pivots.Count == 0)
                {
                    pivots.Add(next);
                    continue;
                }

                PivotPoint previous = pivots[pivots.Count - 1];
                if (previous.IsHigh == next.IsHigh)
                {
                    bool replace = next.IsHigh ? next.Price > previous.Price : next.Price < previous.Price;
                    if (replace)
                        pivots[pivots.Count - 1] = next;
                }
                else
                {
                    pivots.Add(next);
                    if (pivots.Count > 40)
                        pivots.RemoveAt(0);
                }
            }
            return pivots;
        }

        private bool IsPivotHigh(Bars bars, int index)
        {
            double value = bars.HighPrices[index];
            for (int k = 1; k <= _pivotLeft; k++)
                if (bars.HighPrices[index - k] >= value)
                    return false;
            for (int k = 1; k <= _pivotRight; k++)
                if (bars.HighPrices[index + k] > value)
                    return false;
            return true;
        }

        private bool IsPivotLow(Bars bars, int index)
        {
            double value = bars.LowPrices[index];
            for (int k = 1; k <= _pivotLeft; k++)
                if (bars.LowPrices[index - k] <= value)
                    return false;
            for (int k = 1; k <= _pivotRight; k++)
                if (bars.LowPrices[index + k] < value)
                    return false;
            return true;
        }

        private static double FitTarget(double value, double target, double toleranceFraction)
        {
            double tolerance = Math.Max(target * toleranceFraction, 0.03);
            return MarketMath.Clamp(1.0 - Math.Abs(value - target) / tolerance, 0.0, 1.0);
        }

        private static double FitRange(double value, double min, double max, double shoulder)
        {
            if (value >= min && value <= max)
                return 1.0;
            if (value < min)
                return MarketMath.Clamp(1.0 - (min - value) / Math.Max(shoulder, 0.01), 0.0, 1.0);
            return MarketMath.Clamp(1.0 - (value - max) / Math.Max(shoulder, 0.01), 0.0, 1.0);
        }
    }
}
