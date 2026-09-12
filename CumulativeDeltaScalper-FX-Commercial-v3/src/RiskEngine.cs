using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private void TryEnter(EntryCandidate candidate, int closedIndex)
        {
            var atrPips = _atr.Result[closedIndex] / Symbol.PipSize;
            if (double.IsNaN(atrPips) || double.IsInfinity(atrPips) || atrPips <= 0)
            {
                _riskRejectCount++;
                return;
            }

            var spreadPips = CurrentSpreadPips();
            if (spreadPips <= 0 || spreadPips > MaxSpreadPips)
            {
                _costRejectCount++;
                DebugLog("BLOCK spread={0:F2}", spreadPips);
                return;
            }
            if (atrPips / Math.Max(0.01, spreadPips) < MinAtrToSpreadRatio)
            {
                _costRejectCount++;
                DebugLog("BLOCK atrSpreadRatio={0:F2}", atrPips / Math.Max(0.01, spreadPips));
                return;
            }

            var stopPips = Math.Max(atrPips * StopAtrMultiplier, GetBrokerMinimumStopPips() + BrokerDistanceBufferPips);
            var takePips = Math.Max(stopPips * TargetRewardRisk, GetBrokerMinimumTakeProfitPips() + BrokerDistanceBufferPips);
            if (!PassCostAwareRewardRisk(stopPips, takePips, spreadPips))
            {
                _costRejectCount++;
                return;
            }

            var volume = CalculateFailClosedVolume(candidate.Direction, stopPips);
            if (volume < Symbol.VolumeInUnitsMin)
            {
                _riskRejectCount++;
                return;
            }

            var estimatedMargin = Symbol.GetEstimatedMargin(candidate.Direction, volume);
            var maxMargin = Math.Max(0.0, Account.FreeMargin) * MaxMarginUsePercentOfFree / 100.0;
            if (double.IsNaN(estimatedMargin) || double.IsInfinity(estimatedMargin) || estimatedMargin < 0 || estimatedMargin > maxMargin)
            {
                _riskRejectCount++;
                DebugLog("BLOCK margin estimate={0:F2} cap={1:F2}", estimatedMargin, maxMargin);
                return;
            }

            var result = ExecuteMarketOrder(candidate.Direction, SymbolName, volume, TradeLabel, stopPips, takePips);
            if (!result.IsSuccessful || result.Position == null)
            {
                _riskRejectCount++;
                DebugLog("ORDER FAIL error={0}", result.Error);
                return;
            }

            // Commercial fail-safe: a successful fill without both protections is not accepted.
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[V3 CRITICAL] entry protection missing; closing position id={0}", result.Position.Id);
                var closeResult = ClosePosition(result.Position);
                if (!closeResult.IsSuccessful)
                    Print("[V3 CRITICAL] emergency close failed id={0} error={1}", result.Position.Id, closeResult.Error);
                return;
            }

            var actualStopRisk = Symbol.AmountRisked(volume, stopPips);
            var state = new TradeState
            {
                PositionId = result.Position.Id,
                EntryBarIndex = closedIndex,
                InitialStopPips = stopPips,
                InitialRiskMoney = actualStopRisk + EstimateRoundTripCommissionMoney(volume),
                BestFavorablePips = 0,
                OppositePressureBars = 0
            };
            _tradeStates[result.Position.Id] = state;
            _tradesToday++;
            _entryCount++;
            _lastEntryBarIndex = closedIndex;

            DebugLog("OPEN {0} setup={1} vol={2} SL={3:F2} TP={4:F2} pressure={5:F1} momentumR={6:F2} risk={7:F2}",
                candidate.Direction, candidate.Setup, volume, stopPips, takePips, candidate.Pressure, candidate.MomentumR, state.InitialRiskMoney);
        }

        private double CalculateFailClosedVolume(TradeType direction, double stopPips)
        {
            if (stopPips <= 0)
                return 0;

            var hardCap = Math.Max(0.01, Account.Equity * HardRiskCapPercentOfEquity / 100.0);
            var targetRisk = RiskMode == V3RiskMode.FixedMoney
                ? FixedMoneyRisk
                : RiskMode == V3RiskMode.FixedLots
                    ? hardCap
                    : Account.Equity * RiskPercentPerTrade / 100.0;
            targetRisk = Math.Min(targetRisk, hardCap);

            // First prove the broker minimum volume itself fits the cap. Never round an unsafe value up to minimum.
            var minStopRisk = Symbol.AmountRisked(Symbol.VolumeInUnitsMin, stopPips);
            var minAllInRisk = minStopRisk + EstimateRoundTripCommissionMoney(Symbol.VolumeInUnitsMin);
            if (minAllInRisk > hardCap * (1.0 + RiskAuditTolerancePercent / 100.0))
            {
                DebugLog("BLOCK min_volume_risk minVol={0} allInRisk={1:F2} hardCap={2:F2}", Symbol.VolumeInUnitsMin, minAllInRisk, hardCap);
                return 0;
            }

            double rawVolume;
            if (RiskMode == V3RiskMode.FixedLots)
                rawVolume = Symbol.QuantityToVolumeInUnits(FixedLotSize);
            else
                rawVolume = Symbol.VolumeForFixedRisk(targetRisk, stopPips, RoundingMode.Down);

            var maxUnitsFromSetting = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            rawVolume = Math.Min(rawVolume, Math.Min(maxUnitsFromSetting, Symbol.VolumeInUnitsMax));
            var volume = Symbol.NormalizeVolumeInUnits(rawVolume, RoundingMode.Down);

            if (volume < Symbol.VolumeInUnitsMin)
            {
                DebugLog("BLOCK normalized_below_min raw={0} normalized={1} min={2}", rawVolume, volume, Symbol.VolumeInUnitsMin);
                return 0;
            }

            var actualStopRisk = Symbol.AmountRisked(volume, stopPips);
            var allInRisk = actualStopRisk + EstimateRoundTripCommissionMoney(volume);
            var allowed = hardCap * (1.0 + RiskAuditTolerancePercent / 100.0);
            if (double.IsNaN(allInRisk) || double.IsInfinity(allInRisk) || allInRisk > allowed)
            {
                DebugLog("BLOCK post_normalization_risk vol={0} stopRisk={1:F2} allIn={2:F2} allowed={3:F2}", volume, actualStopRisk, allInRisk, allowed);
                return 0;
            }

            return volume;
        }

        private bool PassCostAwareRewardRisk(double stopPips, double takePips, double spreadPips)
        {
            var commissionPips = EstimateRoundTripCommissionPips();
            var costPips = Math.Max(0.0, spreadPips) + Math.Max(0.0, commissionPips);
            var effectiveReward = takePips - costPips;
            var effectiveRisk = stopPips + costPips;
            if (effectiveReward <= 0 || effectiveRisk <= 0)
                return false;

            var rr = effectiveReward / effectiveRisk;
            if (rr < MinEffectiveRewardRisk)
            {
                DebugLog("BLOCK effective_rr={0:F2} rawRR={1:F2} cost={2:F2}p", rr, takePips / stopPips, costPips);
                return false;
            }
            return true;
        }

        private double EstimateRoundTripCommissionPips()
        {
            if (CommissionPerMillionUsd <= 0 || Symbol.PipSize <= 0)
                return 0;

            var mid = (Symbol.Bid + Symbol.Ask) * 0.5;
            if (mid <= 0)
                return 0;

            // For USD-per-million-USD-volume commission, USD notional conversion cancels PipValue.
            // round-trip commission pips = 2 * commission * price / (1,000,000 * pip size).
            return 2.0 * CommissionPerMillionUsd * mid / (1000000.0 * Symbol.PipSize);
        }

        private double EstimateRoundTripCommissionMoney(double volume)
        {
            if (volume <= 0)
                return 0;
            var pips = EstimateRoundTripCommissionPips();
            return Math.Max(0.0, pips * Symbol.PipValue * volume);
        }

        private double CurrentSpreadPips()
        {
            if (Symbol.PipSize <= 0)
                return double.PositiveInfinity;
            return Math.Max(0.0, Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
        }

        private double GetBrokerMinimumStopPips()
        {
            return ConvertBrokerDistanceToPips(Symbol.MinStopLossDistance);
        }

        private double GetBrokerMinimumTakeProfitPips()
        {
            return ConvertBrokerDistanceToPips(Symbol.MinTakeProfitDistance);
        }

        private double ConvertBrokerDistanceToPips(double distance)
        {
            if (distance <= 0 || Symbol.PipSize <= 0)
                return 0;
            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return distance;

            var mid = (Symbol.Bid + Symbol.Ask) * 0.5;
            if (mid <= 0)
                return 0;
            var priceDistance = mid * distance / 100.0;
            return priceDistance / Symbol.PipSize;
        }
    }
}
