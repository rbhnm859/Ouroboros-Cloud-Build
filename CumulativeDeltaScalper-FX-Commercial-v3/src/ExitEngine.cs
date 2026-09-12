using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private void ManageIntrabarProtection()
        {
            var position = Positions.FirstOrDefault(p => p.Label == TradeLabel && p.SymbolName == SymbolName);
            if (position == null)
                return;

            TradeState state;
            if (!_tradeStates.TryGetValue(position.Id, out state))
                return;

            var favorablePips = GetFavorablePips(position);
            if (favorablePips > state.BestFavorablePips)
                state.BestFavorablePips = favorablePips;

            var r = state.InitialStopPips <= 0 ? 0 : favorablePips / state.InitialStopPips;
            if (UseBreakeven && !state.BreakevenApplied && r >= BreakevenTriggerR)
                TryApplyBreakeven(position, state);

            if (UseAtrTrailing && r >= TrailingStartR)
                TryApplyAtrTrail(position, state);
        }

        private void ManageClosedBarExit(int closedIndex, double latestPressure)
        {
            var position = Positions.FirstOrDefault(p => p.Label == TradeLabel && p.SymbolName == SymbolName);
            if (position == null)
                return;

            TradeState state;
            if (!_tradeStates.TryGetValue(position.Id, out state))
                return;

            var heldBars = Math.Max(0, closedIndex - state.EntryBarIndex);
            var opposite = position.TradeType == TradeType.Buy
                ? latestPressure <= -AdversePressureThreshold
                : latestPressure >= AdversePressureThreshold;
            state.OppositePressureBars = opposite ? state.OppositePressureBars + 1 : 0;

            if (heldBars >= MinHoldBarsBeforeAdverseExit &&
                state.OppositePressureBars >= AdversePersistenceBars &&
                IsStructureInvalidated(closedIndex, position.TradeType))
            {
                TryClosePosition(position, "persistent_adverse_structure_break");
                return;
            }

            var bestR = state.InitialStopPips <= 0 ? 0 : state.BestFavorablePips / state.InitialStopPips;
            if (heldBars >= StagnationBars && bestR < MinMfeRForContinuation)
            {
                TryClosePosition(position, "stagnation");
                return;
            }

            if (heldBars >= MaxTradeBars)
            {
                var favorablePips = GetFavorablePips(position);
                var healthy = favorablePips > 0 && PassLocalTrend(closedIndex, position.TradeType) && !opposite;
                if (!healthy || heldBars >= MaxTradeBars * 2)
                    TryClosePosition(position, healthy ? "hard_time_cap" : "time_exit_not_healthy");
            }
        }

        private void TryApplyBreakeven(Position position, TradeState state)
        {
            var costBufferPips = (CurrentSpreadPips() + EstimateRoundTripCommissionPips()) * BreakevenCostBufferMultiplier;
            var newStop = position.TradeType == TradeType.Buy
                ? position.EntryPrice + costBufferPips * Symbol.PipSize
                : position.EntryPrice - costBufferPips * Symbol.PipSize;

            if (!CanImproveStop(position, newStop))
                return;

            var result = ModifyPosition(position, newStop, position.TakeProfit);
            if (!result.IsSuccessful)
            {
                Print("[V3 PROTECTION] breakeven modify failed id={0} error={1}", position.Id, result.Error);
                return;
            }

            state.BreakevenApplied = true;
            DebugLog("BREAKEVEN id={0} stop={1}", position.Id, newStop);
        }

        private void TryApplyAtrTrail(Position position, TradeState state)
        {
            if (Bars.Count < 3)
                return;
            var index = Bars.Count - 2;
            var atrPrice = _atr.Result[index];
            if (atrPrice <= 0 || double.IsNaN(atrPrice))
                return;

            var distance = atrPrice * TrailingAtrMultiplier;
            var newStop = position.TradeType == TradeType.Buy
                ? Symbol.Bid - distance
                : Symbol.Ask + distance;

            if (!CanImproveStop(position, newStop))
                return;

            var result = ModifyPosition(position, newStop, position.TakeProfit);
            if (!result.IsSuccessful)
            {
                Print("[V3 PROTECTION] trail modify failed id={0} error={1}", position.Id, result.Error);
                return;
            }

            state.TrailingActivated = true;
        }

        private bool CanImproveStop(Position position, double newStop)
        {
            if (newStop <= 0 || double.IsNaN(newStop) || double.IsInfinity(newStop))
                return false;

            var minDistancePips = GetBrokerMinimumStopPips() + BrokerDistanceBufferPips;
            var minDistancePrice = minDistancePips * Symbol.PipSize;
            var improveEpsilon = Math.Max(Symbol.TickSize, 0.10 * Symbol.PipSize);

            if (position.TradeType == TradeType.Buy)
            {
                if (newStop >= Symbol.Bid - minDistancePrice)
                    return false;
                if (position.StopLoss.HasValue && newStop <= position.StopLoss.Value + improveEpsilon)
                    return false;
            }
            else
            {
                if (newStop <= Symbol.Ask + minDistancePrice)
                    return false;
                if (position.StopLoss.HasValue && newStop >= position.StopLoss.Value - improveEpsilon)
                    return false;
            }
            return true;
        }

        private bool IsStructureInvalidated(int index, TradeType direction)
        {
            if (index < 3)
                return false;

            var close = Bars.ClosePrices[index];
            var fast = _fastEma.Result[index];
            var priorLow = Math.Min(Bars.LowPrices[index - 1], Bars.LowPrices[index - 2]);
            var priorHigh = Math.Max(Bars.HighPrices[index - 1], Bars.HighPrices[index - 2]);

            if (direction == TradeType.Buy)
                return close < fast && Bars.LowPrices[index] < priorLow;
            return close > fast && Bars.HighPrices[index] > priorHigh;
        }

        private double GetFavorablePips(Position position)
        {
            if (Symbol.PipSize <= 0)
                return 0;
            return position.TradeType == TradeType.Buy
                ? (Symbol.Bid - position.EntryPrice) / Symbol.PipSize
                : (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
        }

        private void TryClosePosition(Position position, string reason)
        {
            var result = ClosePosition(position);
            if (!result.IsSuccessful)
            {
                Print("[V3 EXIT] close failed id={0} reason={1} error={2}", position.Id, reason, result.Error);
                return;
            }
            DebugLog("EXIT id={0} reason={1}", position.Id, reason);
        }
    }
}
