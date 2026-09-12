using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Slippage Reserve Pips", Group = "Execution", DefaultValue = 0.30, MinValue = 0.0, MaxValue = 5.0, Step = 0.05)]
        public double SlippageReservePips { get; set; }

        [Parameter("Max Entry Slippage Pips", Group = "Execution", DefaultValue = 0.80, MinValue = 0.0, MaxValue = 10.0, Step = 0.05)]
        public double MaxEntrySlippagePips { get; set; }

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

            var preExecutionPrice = candidate.Direction == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
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
                EmergencyCloseNewPosition(result.Position, "missing_protection");
                return;
            }

            var adverseEntrySlippagePips = GetAdverseEntrySlippagePips(candidate.Direction, preExecutionPrice, result.Position.EntryPrice);
            if (MaxEntrySlippagePips > 0 && adverseEntrySlippagePips > MaxEntrySlippagePips)
            {
                Print("[V3 CRITICAL] entry slippage exceeded id={0} slip={1:F2}p cap={2:F2}p", result.Position.Id, adverseEntrySlippagePips, MaxEntrySlippagePips);
                EmergencyCloseNewPosition(result.Position, "entry_slippage_cap");
                return;
            }

            // Re-audit using the protections actually attached to the filled position. Relative
            // protection is based on opening price, but execution/rounding/broker rules can still
            // make requested and realised distances differ.
            var actualStopPips = Math.Abs(result.Position.EntryPrice - result.Position.StopLoss.Value) / Symbol.PipSize;
            var actualTakePips = Math.Abs(result.Position.TakeProfit.Value - result.Position.EntryPrice) / Symbol.PipSize;
            var applicableCap = GetApplicableAllInRiskCap();
            var tolerance = 1.0 + RiskAuditTolerancePercent / 100.0;
            var actualStopRisk = Symbol.AmountRisked(volume, actualStopPips);
            var actualAllInRisk = actualStopRisk + EstimateRoundTripCommissionMoney(volume) + EstimateSlippageReserveMoney(volume);

            if (double.IsNaN(actualAllInRisk) || double.IsInfinity(actualAllInRisk) ||
                actualStopPips <= 0 || actualTakePips <= 0 || actualAllInRisk > applicableCap * tolerance)
            {
                Print("[V3 CRITICAL] post-fill risk audit failed id={0} stop={1:F2}p take={2:F2}p allInRisk={3:F2} cap={4:F2}",
                    result.Position.Id, actualStopPips, actualTakePips, actualAllInRisk, applicableCap);
                EmergencyCloseNewPosition(result.Position, "post_fill_risk_audit");
                return;
            }

            if (!PassCostAwareRewardRisk(actualStopPips, actualTakePips, spreadPips))
            {
                Print("[V3 CRITICAL] post-fill RR audit failed id={0} stop={1:F2}p take={2:F2}p", result.Position.Id, actualStopPips, actualTakePips);
                EmergencyCloseNewPosition(result.Position, "post_fill_rr_audit");
                return;
            }

            var state = new TradeState
            {
                PositionId = result.Position.Id,
                EntryBarIndex = closedIndex,
                InitialStopPips = actualStopPips,
                InitialRiskMoney = actualAllInRisk,
                BestFavorablePips = 0,
                OppositePressureBars = 0
            };
            _tradeStates[result.Position.Id] = state;
            _tradesToday++;
            _entryCount++;
            _lastEntryBarIndex = closedIndex;

            DebugLog("OPEN {0} setup={1} vol={2} SL={3:F2} TP={4:F2} pressure={5:F1} momentumR={6:F2} allInRisk={7:F2} slip={8:F2}p",
                candidate.Direction, candidate.Setup, volume, actualStopPips, actualTakePips, candidate.Pressure, candidate.MomentumR, state.InitialRiskMoney, adverseEntrySlippagePips);
        }

        private double CalculateFailClosedVolume(TradeType direction, double stopPips)
        {
            if (stopPips <= 0)
                return 0;

            var applicableCap = GetApplicableAllInRiskCap();
            var tolerance = 1.0 + RiskAuditTolerancePercent / 100.0;

            // First prove the broker minimum volume itself fits the requested all-in risk cap.
            // Never round an unsafe value up to minimum volume.
            var minStopRisk = Symbol.AmountRisked(Symbol.VolumeInUnitsMin, stopPips);
            var minAllInRisk = minStopRisk +
                               EstimateRoundTripCommissionMoney(Symbol.VolumeInUnitsMin) +
                               EstimateSlippageReserveMoney(Symbol.VolumeInUnitsMin);
            if (minAllInRisk > applicableCap * tolerance)
            {
                DebugLog("BLOCK min_volume_risk minVol={0} allInRisk={1:F2} cap={2:F2}", Symbol.VolumeInUnitsMin, minAllInRisk, applicableCap);
                return 0;
            }

            double rawVolume;
            if (RiskMode == V3RiskMode.FixedLots)
            {
                rawVolume = Symbol.QuantityToVolumeInUnits(FixedLotSize);
            }
            else
            {
                // Reserve estimated commission and stop-execution slippage before asking the platform
                // for fixed-risk volume. The final normalized result is audited again below.
                var nonStopReserve = EstimateRoundTripCommissionMoney(Symbol.VolumeInUnitsMin) +
                                     EstimateSlippageReserveMoney(Symbol.VolumeInUnitsMin);
                var stopRiskBudget = Math.Max(0.01, applicableCap - nonStopReserve);
                rawVolume = Symbol.VolumeForFixedRisk(stopRiskBudget, stopPips, RoundingMode.Down);
            }

            var maxUnitsFromSetting = Symbol.QuantityToVolumeInUnits(MaxLotSize);
            rawVolume = Math.Min(rawVolume, Math.Min(maxUnitsFromSetting, Symbol.VolumeInUnitsMax));
            var volume = Symbol.NormalizeVolumeInUnits(rawVolume, RoundingMode.Down);

            if (volume < Symbol.VolumeInUnitsMin)
            {
                DebugLog("BLOCK normalized_below_min raw={0} normalized={1} min={2}", rawVolume, volume, Symbol.VolumeInUnitsMin);
                return 0;
            }

            // Recalculate with actual normalized volume. If all-in risk remains too large, scale down
            // and normalize DOWN again rather than silently accepting excess risk.
            var actualStopRisk = Symbol.AmountRisked(volume, stopPips);
            var allInRisk = actualStopRisk + EstimateRoundTripCommissionMoney(volume) + EstimateSlippageReserveMoney(volume);
            if (allInRisk > applicableCap * tolerance && allInRisk > 0)
            {
                volume *= applicableCap / allInRisk;
                volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            }

            if (volume < Symbol.VolumeInUnitsMin)
                return 0;

            actualStopRisk = Symbol.AmountRisked(volume, stopPips);
            allInRisk = actualStopRisk + EstimateRoundTripCommissionMoney(volume) + EstimateSlippageReserveMoney(volume);
            if (double.IsNaN(allInRisk) || double.IsInfinity(allInRisk) || allInRisk > applicableCap * tolerance)
            {
                DebugLog("BLOCK post_normalization_risk vol={0} stopRisk={1:F2} allIn={2:F2} cap={3:F2}", volume, actualStopRisk, allInRisk, applicableCap);
                return 0;
            }

            return volume;
        }

        private double GetApplicableAllInRiskCap()
        {
            var hardCap = Math.Max(0.01, Account.Equity * HardRiskCapPercentOfEquity / 100.0);
            if (RiskMode == V3RiskMode.FixedLots)
                return hardCap;

            var requested = RiskMode == V3RiskMode.FixedMoney
                ? Math.Max(0.01, FixedMoneyRisk)
                : Math.Max(0.01, Account.Equity * RiskPercentPerTrade / 100.0);
            return Math.Min(requested, hardCap);
        }

        private bool PassCostAwareRewardRisk(double stopPips, double takePips, double spreadPips)
        {
            var commissionPips = EstimateRoundTripCommissionPips();
            var costPips = Math.Max(0.0, spreadPips) + Math.Max(0.0, commissionPips) + Math.Max(0.0, SlippageReservePips);
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

            // Commission setting is USD per million USD notional per side; round trip = 2 sides.
            return 2.0 * CommissionPerMillionUsd * mid / (1000000.0 * Symbol.PipSize);
        }

        private double EstimateRoundTripCommissionMoney(double volume)
        {
            if (volume <= 0)
                return 0;
            var pips = EstimateRoundTripCommissionPips();
            return Math.Max(0.0, pips * Symbol.PipValue * volume);
        }

        private double EstimateSlippageReserveMoney(double volume)
        {
            if (volume <= 0 || Symbol.PipValue <= 0)
                return 0;
            return Math.Max(0.0, SlippageReservePips) * Symbol.PipValue * volume;
        }

        private double GetAdverseEntrySlippagePips(TradeType direction, double requestedPrice, double fillPrice)
        {
            if (Symbol.PipSize <= 0 || requestedPrice <= 0 || fillPrice <= 0)
                return 0;
            var priceDelta = direction == TradeType.Buy
                ? fillPrice - requestedPrice
                : requestedPrice - fillPrice;
            return Math.Max(0.0, priceDelta / Symbol.PipSize);
        }

        private void EmergencyCloseNewPosition(Position position, string reason)
        {
            var closeResult = ClosePosition(position);
            if (!closeResult.IsSuccessful)
                Print("[V3 CRITICAL] emergency close failed id={0} reason={1} error={2}", position.Id, reason, closeResult.Error);
            else
                Print("[V3 SAFETY] rejected filled position id={0} reason={1}", position.Id, reason);
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
