using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal sealed class RiskEngine
    {
        private readonly RiskBudgetMode _mode;
        private readonly double _riskPercent;
        private readonly double _fixedRiskCash;
        private readonly double _minimumLots;
        private readonly double _maximumLots;
        private readonly double _maxFreeMarginFraction;

        public RiskEngine(RiskBudgetMode mode, double riskPercent, double fixedRiskCash, double minimumLots, double maximumLots, double maxFreeMarginFraction)
        {
            _mode = mode;
            _riskPercent = riskPercent;
            _fixedRiskCash = fixedRiskCash;
            _minimumLots = minimumLots;
            _maximumLots = maximumLots;
            _maxFreeMarginFraction = maxFreeMarginFraction;
        }

        public bool TrySize(Symbol symbol, double equity, double freeMargin, TradeType direction, double stopLossPips, out double volumeInUnits, out double estimatedRiskCash, out double estimatedMargin, out string reason)
        {
            volumeInUnits = 0.0;
            estimatedRiskCash = 0.0;
            estimatedMargin = 0.0;
            reason = string.Empty;

            if (symbol == null || equity <= 0.0 || freeMargin <= 0.0 || stopLossPips <= 0.0)
            {
                reason = "invalid-risk-input";
                return false;
            }

            double budget = _mode == RiskBudgetMode.FixedCash ? _fixedRiskCash : equity * _riskPercent / 100.0;
            if (budget <= 0.0)
            {
                reason = "risk-budget-zero";
                return false;
            }

            double raw = symbol.VolumeForFixedRisk(budget, stopLossPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0.0)
            {
                reason = "volume-calculation-failed";
                return false;
            }

            double brokerMin = symbol.VolumeInUnitsMin;
            double userMin = _minimumLots > 0.0 ? symbol.QuantityToVolumeInUnits(_minimumLots) : brokerMin;
            double effectiveMin = Math.Max(brokerMin, userMin);

            double brokerMax = symbol.VolumeInUnitsMax;
            double userMax = _maximumLots > 0.0 ? symbol.QuantityToVolumeInUnits(_maximumLots) : brokerMax;
            double effectiveMax = Math.Min(brokerMax, userMax);

            double normalized = symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (normalized < effectiveMin)
            {
                // Minimum lots is a minimum acceptable size, never permission to exceed the fixed-risk budget.
                reason = "risk-volume-below-user-minimum-lots";
                return false;
            }

            normalized = Math.Min(normalized, effectiveMax);
            normalized = symbol.NormalizeVolumeInUnits(normalized, RoundingMode.Down);
            if (normalized < brokerMin || normalized > brokerMax)
            {
                reason = "broker-volume-bounds";
                return false;
            }

            double actualRisk = symbol.AmountRisked(normalized, stopLossPips);
            if (double.IsNaN(actualRisk) || double.IsInfinity(actualRisk) || actualRisk <= 0.0)
            {
                reason = "actual-risk-invalid";
                return false;
            }

            if (actualRisk > budget * 1.03)
            {
                reason = "actual-risk-over-budget";
                return false;
            }

            double margin = symbol.GetEstimatedMargin(direction, normalized);
            if (double.IsNaN(margin) || double.IsInfinity(margin) || margin < 0.0)
            {
                reason = "margin-estimate-invalid";
                return false;
            }

            if (_maxFreeMarginFraction > 0.0 && margin > freeMargin * _maxFreeMarginFraction)
            {
                reason = "margin-cap";
                return false;
            }

            volumeInUnits = normalized;
            estimatedRiskCash = actualRisk;
            estimatedMargin = margin;
            return true;
        }
    }
}
