using System;
using System.Collections.Generic;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal enum PivotKind
    {
        High,
        Low
    }

    internal sealed class PivotPoint
    {
        public PivotPoint(int index, double price, PivotKind kind)
        {
            Index = index;
            Price = price;
            Kind = kind;
        }

        public int Index { get; private set; }
        public double Price { get; private set; }
        public PivotKind Kind { get; private set; }
    }

    internal sealed class IncrementalPivotEngine
    {
        private readonly Bars _bars;
        private readonly int _left;
        private readonly int _right;
        private readonly int _seedLookback;
        private readonly int _maxPivots;
        private readonly List<PivotPoint> _pivots = new List<PivotPoint>();
        private int _lastEvaluatedIndex = -1;

        public IncrementalPivotEngine(Bars bars, int left, int right, int seedLookback, int maxPivots)
        {
            _bars = bars;
            _left = Math.Max(2, left);
            _right = Math.Max(2, right);
            _seedLookback = Math.Max(100, seedLookback);
            _maxPivots = Math.Max(20, maxPivots);
        }

        public IReadOnlyList<PivotPoint> Pivots
        {
            get { return _pivots; }
        }

        public void Seed()
        {
            _pivots.Clear();
            int latestConfirmed = _bars.Count - 1 - _right;
            int first = Math.Max(_left, _bars.Count - _seedLookback);
            if (latestConfirmed < first)
            {
                _lastEvaluatedIndex = latestConfirmed;
                return;
            }

            for (int i = first; i <= latestConfirmed; i++)
                EvaluateIndex(i);

            _lastEvaluatedIndex = latestConfirmed;
            Trim();
        }

        public bool Update()
        {
            int latestConfirmed = _bars.Count - 1 - _right;
            if (latestConfirmed <= _lastEvaluatedIndex)
                return false;

            bool changed = false;
            for (int i = _lastEvaluatedIndex + 1; i <= latestConfirmed; i++)
            {
                if (i >= _left && i + _right < _bars.Count)
                    changed |= EvaluateIndex(i);
            }

            _lastEvaluatedIndex = latestConfirmed;
            Trim();
            return changed;
        }

        private bool EvaluateIndex(int index)
        {
            bool isHigh = true;
            bool isLow = true;

            for (int j = 1; j <= _left; j++)
            {
                if (_bars.HighPrices[index] <= _bars.HighPrices[index - j])
                    isHigh = false;
                if (_bars.LowPrices[index] >= _bars.LowPrices[index - j])
                    isLow = false;
            }

            for (int j = 1; j <= _right; j++)
            {
                if (_bars.HighPrices[index] <= _bars.HighPrices[index + j])
                    isHigh = false;
                if (_bars.LowPrices[index] >= _bars.LowPrices[index + j])
                    isLow = false;
            }

            if (isHigh && !isLow)
                return AddAlternating(new PivotPoint(index, _bars.HighPrices[index], PivotKind.High));
            if (isLow && !isHigh)
                return AddAlternating(new PivotPoint(index, _bars.LowPrices[index], PivotKind.Low));
            return false;
        }

        private bool AddAlternating(PivotPoint next)
        {
            if (_pivots.Count == 0)
            {
                _pivots.Add(next);
                return true;
            }

            var last = _pivots[_pivots.Count - 1];
            if (last.Kind != next.Kind)
            {
                _pivots.Add(next);
                return true;
            }

            bool replace = next.Kind == PivotKind.High ? next.Price > last.Price : next.Price < last.Price;
            if (!replace)
                return false;

            _pivots[_pivots.Count - 1] = next;
            return true;
        }

        private void Trim()
        {
            if (_pivots.Count <= _maxPivots)
                return;
            _pivots.RemoveRange(0, _pivots.Count - _maxPivots);
        }
    }
}
