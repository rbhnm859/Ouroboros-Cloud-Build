using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal sealed class CommercialQualityGate
    {
        private readonly double _minPatternScore;
        private readonly double _minLongScore;
        private readonly double _minShortScore;
        private readonly double _strongLongOverrideScore;
        private readonly double _minLongRr;
        private readonly double _minShortRr;
        private readonly int _sameSideLossCooldownBars;
        private readonly int _confirmationRulesNeeded;
        private readonly int _breakLookback;
        private readonly double _rejectionWickMin;
        private readonly double _bodyMin;
        private readonly double _maxEntryDistanceAtr;

        public CommercialQualityGate(
            double minPatternScore,
            double minLongScore,
            double minShortScore,
            double strongLongOverrideScore,
            double minLongRr,
            double minShortRr,
            int sameSideLossCooldownBars,
            int confirmationRulesNeeded,
            int breakLookback,
            double rejectionWickMin,
            double bodyMin,
            double maxEntryDistanceAtr)
        {
            _minPatternScore = minPatternScore;
            _minLongScore = minLongScore;
            _minShortScore = minShortScore;
            _strongLongOverrideScore = strongLongOverrideScore;
            _minLongRr = minLongRr;
            _minShortRr = minShortRr;
            _sameSideLossCooldownBars = sameSideLossCooldownBars;
            _confirmationRulesNeeded = confirmationRulesNeeded;
            _breakLookback = breakLookback;
            _rejectionWickMin = rejectionWickMin;
            _bodyMin = bodyMin;
            _maxEntryDistanceAtr = maxEntryDistanceAtr;
        }

        public bool PassSetup(HarmonicSignal signal, RegimeSnapshot regime, TradeType? lastLossDirection, int lastLossBarIndex, int currentIndex, out string reason)
        {
            reason = string.Empty;
            if (signal == null)
            {
                reason = "no-signal";
                return false;
            }

            if (signal.PatternScore < _minPatternScore)
            {
                reason = "pattern-score";
                return false;
            }

            double directionFloor = signal.Direction == TradeType.Buy ? _minLongScore : _minShortScore;
            if (signal.PatternScore < directionFloor)
            {
                reason = signal.Direction == TradeType.Buy ? "long-quality-floor" : "short-quality-floor";
                return false;
            }

            // Long quality gate: weak long trend context is allowed only for exceptionally high geometry quality.
            if (signal.Direction == TradeType.Buy && !regime.TrendAligned && signal.PatternScore < _strongLongOverrideScore)
            {
                reason = "weak-long-regime";
                return false;
            }

            if (lastLossDirection.HasValue && lastLossDirection.Value == signal.Direction && lastLossBarIndex >= 0)
            {
                if (currentIndex - lastLossBarIndex < _sameSideLossCooldownBars)
                {
                    reason = "same-side-post-loss-cooldown";
                    return false;
                }
            }

            return true;
        }

        public ConfirmationSnapshot Confirm(Bars bars, int index, HarmonicSignal signal)
        {
            var result = new ConfirmationSnapshot();
            if (bars == null || signal == null || index < Math.Max(2, _breakLookback) || index >= bars.Count)
                return result;

            double open = bars.OpenPrices[index];
            double high = bars.HighPrices[index];
            double low = bars.LowPrices[index];
            double close = bars.ClosePrices[index];
            double range = Math.Max(high - low, 1e-12);
            double bodyRatio = Math.Abs(close - open) / range;
            double distanceAtr = Math.Abs(close - signal.D.Price) / Math.Max(signal.Atr, 1e-12);

            result.BodyRatio = bodyRatio;
            result.DistanceAtr = distanceAtr;
            result.DirectionalCandle = signal.Direction == TradeType.Buy ? close > open : close < open;
            if (!result.DirectionalCandle || distanceAtr > _maxEntryDistanceAtr)
                return result;

            double closePos = (close - low) / range;
            if (signal.Direction == TradeType.Buy)
            {
                double lowerWick = Math.Min(open, close) - low;
                result.Rejection = lowerWick / range >= _rejectionWickMin && closePos >= 0.58;
                result.Momentum = bodyRatio >= _bodyMin && closePos >= 0.62;

                double priorHigh = bars.HighPrices[index - 1];
                for (int k = 2; k <= _breakLookback; k++)
                    priorHigh = Math.Max(priorHigh, bars.HighPrices[index - k]);
                result.MicroBreak = close > priorHigh;
            }
            else
            {
                double upperWick = high - Math.Max(open, close);
                result.Rejection = upperWick / range >= _rejectionWickMin && closePos <= 0.42;
                result.Momentum = bodyRatio >= _bodyMin && closePos <= 0.38;

                double priorLow = bars.LowPrices[index - 1];
                for (int k = 2; k <= _breakLookback; k++)
                    priorLow = Math.Min(priorLow, bars.LowPrices[index - k]);
                result.MicroBreak = close < priorLow;
            }

            int passed = 0;
            if (result.Rejection) passed++;
            if (result.Momentum) passed++;
            if (result.MicroBreak) passed++;
            result.RulesPassed = passed;
            return result;
        }

        public bool ConfirmationPassed(ConfirmationSnapshot confirmation)
        {
            return confirmation != null && confirmation.DirectionalCandle && confirmation.DistanceAtr <= _maxEntryDistanceAtr && confirmation.RulesPassed >= _confirmationRulesNeeded;
        }

        public bool EffectiveRiskRewardPassed(TradeType direction, double effectiveRr, out string reason)
        {
            double floor = direction == TradeType.Buy ? _minLongRr : _minShortRr;
            if (effectiveRr < floor)
            {
                reason = direction == TradeType.Buy ? "long-effective-rr" : "short-effective-rr";
                return false;
            }
            reason = string.Empty;
            return true;
        }
    }
}
