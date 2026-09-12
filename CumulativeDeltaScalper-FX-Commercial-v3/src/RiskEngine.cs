using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Slippage Reserve Pips", Group = "Execution", DefaultValue = 0.30, MinValue = 0.0, MaxValue = 5.0, Step = 0.05)]
        public double SlippageReservePips { get; set; }

        [Parameter("Max Entry Slippage Pips", Group = "Execution", DefaultValue = 0.80, MinValue = 0.0, MaxValue = 10.0, Step = 0.05)]
        public double MaxEntrySlippagePips { get; set; }

        private bool _commissionModelFailureLogged;

        private void TryEnter(EntryCandidate candidate, int closedIndex)
        {
            EnsureDailyStateRecovered();
            if (HasConflictingOpenPosition())
            {
                _filterRejectCount++;
                DebugLog("BLOCK pre_order_position_recheck");
                return;
            }
            if (!PassImmediateRiskStateRecheck())
            {
                _riskRejectCount++;
                return;
            }

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

            if (HasConflictingOpenPosition() || !PassImmediateRiskStateRecheck())
            {
                _riskRejectCount++;
                DebugLog("BLOCK final_pre_execution_recheck");
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

            if (!PassCostAwareRewardRisk(actualStopPips, actualTakePips, spreadPips, volume))
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

        private bool HasConflictingOpenPosition()
        {
            return PortfolioSinglePosition
                ? Positions.Any(p => p.Label == TradeLabel)
                : Positions.Any(p => p.Label == TradeLabel && p.SymbolName == SymbolName);
        }

        private bool PassImmediateRiskStateRecheck()
        {
            if (Server.Time < _nextTradeTime)
                return false;
            if (_tradesToday >= MaxTradesPerDay)
                return false;
            if (_consecutiveLosses >= MaxConsecutiveLosses)
                return false;
            if (_dailyRealized <= -Math.Abs(_dayStartEquity * MaxDailyLossPercent / 100.0))
                return false;
            return true;
        }

        private double CalculateFailClosedVolume(TradeType direction, double stopPips)
        {
            if (stopPips <= 0)
                return 0;

            var applicableCap = GetApplicableAllInRiskCap();
            var tolerance = 1.0 + RiskAuditTolerancePercent / 100.0;

            var minStopRisk = Symbol.AmountRisked(Symbol.VolumeInUnitsMin, stopPips);
            var minAllInRisk = minStopRisk +
                               EstimateRoundTripCommissionMoney(Symbol.VolumeInUnitsMin) +
                               EstimateSlippageReserveMoney(Symbol.VolumeInUnitsMin);
            if (double.IsNaN(minAllInRisk) || double.IsInfinity(minAllInRisk) || minAllInRisk > applicableCap * tolerance)
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
                var nonStopReserve = EstimateRoundTripCommissionMoney(Symbol.VolumeInUnitsMin) +
                                     EstimateSlippageReserveMoney(Symbol.VolumeInUnitsMin);
                if (double.IsNaN(nonStopReserve) || double.IsInfinity(nonStopReserve) || nonStopReserve >= applicableCap)
                    return 0;
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

            var actualStopRisk = Symbol.AmountRisked(volume, stopPips);
            var allInRisk = actualStopRisk + EstimateRoundTripCommissionMoney(volume) + EstimateSlippageReserveMoney(volume);
            if (allInRisk > applicableCap * tolerance && allInRisk > 0 && !double.IsInfinity(allInRisk))
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

        private bool PassCostAwareRewardRisk(double stopPips, double takePips, double observedSpreadPips, double volume = 0)
        {
            var commissionPips = volume >= Symbol.VolumeInUnitsMin
                ? EstimateRoundTripCommissionPips(volume)
                : EstimateRoundTripCommissionPips(Symbol.VolumeInUnitsMin);
            var explicitCostPips = Math.Max(0.0, commissionPips) + Math.Max(0.0, SlippageReservePips);
            if (double.IsNaN(explicitCostPips) || double.IsInfinity(explicitCostPips))
                return false;

            var effectiveReward = takePips - explicitCostPips;
            var effectiveRisk = stopPips + explicitCostPips;
            if (effectiveReward <= 0 || effectiveRisk <= 0)
                return false;

            var rr = effectiveReward / effectiveRisk;
            if (rr < MinEffectiveRewardRisk)
            {
                DebugLog("BLOCK effective_rr={0:F2} rawRR={1:F2} explicitCost={2:F2}p spreadGate={3:F2}p", rr, takePips / stopPips, explicitCostPips, observedSpreadPips);
                return false;
            }
            return true;
        }

        private double EstimateRoundTripCommissionPips()
        {
            return EstimateRoundTripCommissionPips(Symbol.VolumeInUnitsMin);
        }

        private double EstimateRoundTripCommissionPips(double volume)
        {
            if (volume <= 0 || Symbol.PipValue <= 0)
                return 0;
            var money = EstimateRoundTripCommissionMoney(volume);
            if (double.IsNaN(money) || double.IsInfinity(money))
                return money;
            return Math.Max(0.0, money / (Symbol.PipValue * volume));
        }

        private double EstimateRoundTripCommissionMoney(double volume)
        {
            if (volume <= 0)
                return 0;

            try
            {
                var oneSide = EstimateOneSideBrokerCommissionMoney(volume);
                var minimumOneSide = EstimateOneSideMinimumCommissionMoney();
                oneSide = Math.Max(oneSide, minimumOneSide);
                return Math.Max(0.0, oneSide * 2.0);
            }
            catch (Exception ex)
            {
                if (!_commissionModelFailureLogged)
                {
                    _commissionModelFailureLogged = true;
                    Print("[V3 CRITICAL] commission conversion failed; entries fail closed. type={0} error={1}", Symbol.CommissionType, ex.Message);
                }
                return double.PositiveInfinity;
            }
        }

        private double EstimateOneSideBrokerCommissionMoney(double volume)
        {
            var rate = Symbol.Commission;
            if (rate <= 0 && Symbol.CommissionType == SymbolCommissionType.UsdPerMillionUsdVolume)
                rate = CommissionPerMillionUsd;
            if (rate <= 0)
                return 0;

            switch (Symbol.CommissionType)
            {
                case SymbolCommissionType.UsdPerMillionUsdVolume:
                {
                    var usdNotional = Math.Abs(AssetConverter.Convert(volume, Symbol.BaseAsset, "USD"));
                    var commissionUsd = usdNotional * rate / 1000000.0;
                    return Math.Abs(AssetConverter.Convert(commissionUsd, "USD", Account.Asset));
                }
                case SymbolCommissionType.UsdPerOneLot:
                {
                    var lots = Math.Abs(Symbol.VolumeInUnitsToQuantity(volume));
                    var commissionUsd = lots * rate;
                    return Math.Abs(AssetConverter.Convert(commissionUsd, "USD", Account.Asset));
                }
                case SymbolCommissionType.QuoteCurrencyPerOneLot:
                {
                    var lots = Math.Abs(Symbol.VolumeInUnitsToQuantity(volume));
                    var commissionQuote = lots * rate;
                    return Math.Abs(AssetConverter.Convert(commissionQuote, Symbol.QuoteAsset, Account.Asset));
                }
                case SymbolCommissionType.PercentageOfTradingVolume:
                {
                    var mid = (Symbol.Bid + Symbol.Ask) * 0.5;
                    if (mid <= 0)
                        return double.PositiveInfinity;
                    var quoteNotional = Math.Abs(volume * mid);
                    var commissionQuote = quoteNotional * rate / 100.0;
                    return Math.Abs(AssetConverter.Convert(commissionQuote, Symbol.QuoteAsset, Account.Asset));
                }
                default:
                    return EstimateFallbackUsdPerMillionCommissionMoney(volume);
            }
        }

        private double EstimateFallbackUsdPerMillionCommissionMoney(double volume)
        {
            if (CommissionPerMillionUsd <= 0)
                return 0;
            var usdNotional = Math.Abs(AssetConverter.Convert(volume, Symbol.BaseAsset, "USD"));
            var commissionUsd = usdNotional * CommissionPerMillionUsd / 1000000.0;
            return Math.Abs(AssetConverter.Convert(commissionUsd, "USD", Account.Asset));
        }

        private double EstimateOneSideMinimumCommissionMoney()
        {
            if (Symbol.MinCommission <= 0)
                return 0;

            if (Symbol.MinCommissionType == SymbolMinCommissionType.QuoteAsset)
                return Math.Abs(AssetConverter.Convert(Symbol.MinCommission, Symbol.QuoteAsset, Account.Asset));

            if (Symbol.MinCommissionAsset != null)
                return Math.Abs(AssetConverter.Convert(Symbol.MinCommission, Symbol.MinCommissionAsset, Account.Asset));

            return 0;
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
