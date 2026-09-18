using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Min Trail Step Pips", Group = "Exit", DefaultValue = 0.50, MinValue = 0.10, MaxValue = 10.0, Step = 0.10)]
        public double MinTrailStepPips { get; set; }

        [Parameter("Min Protection Update Seconds", Group = "Exit", DefaultValue = 2, MinValue = 0, MaxValue = 60)]
        public int MinProtectionUpdateSeconds { get; set; }

        [Parameter("Runtime Stop Widen Tolerance Pips", Group = "Exit", DefaultValue = 0.20, MinValue = 0.0, MaxValue = 5.0, Step = 0.05)]
        public double RuntimeStopWidenTolerancePips { get; set; }

        private void ManageIntrabarProtection()
        {
            var position = Positions.FirstOrDefault(p => p.Label == TradeLabel && p.SymbolName == SymbolName);
            if (position == null)
                return;

            // Fail closed if broker/runtime state ever loses either mandatory protection.
            if (!position.StopLoss.HasValue || !position.TakeProfit.HasValue)
            {
                Print("[V3 CRITICAL] runtime protection missing id={0} sl={1} tp={2}",
                    position.Id, position.StopLoss.HasValue, position.TakeProfit.HasValue);
                EmergencyCloseNewPosition(position, "runtime_protection_missing");
                return;
            }

            var state = EnsureTradeState(position);
            if (state == null)
                return;

            // This strategy never intentionally widens risk. If the live stop becomes materially
            // farther from entry than the initial audited stop, treat it as protection corruption.
            var currentStopPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize;
            if (currentStopPips > state.InitialStopPips + RuntimeStopWidenTolerancePips)
            {
                Print("[V3 CRITICAL] stop widened id={0} current={1:F2}p initial={2:F2}p", position.Id, currentStopPips, state.InitialStopPips);
                EmergencyCloseNewPosition(position, "runtime_stop_widened");
                return;
            }

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

            var state = EnsureTradeState(position);
            if (state == null)
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
                var healthy = favorablePips > 0 && PassLocalTrend(closedIndex, position.TradeType, _atr.Result[closedIndex]) && !opposite;
                if (!healthy || heldBars >= MaxTradeBars * 2)
                    TryClosePosition(position, healthy ? "hard_time_cap" : "time_exit_not_healthy");
            }
        }

        private void TryApplyBreakeven(Position position, TradeState state)
        {
            // Entry spread is already represented by the actual filled entry price. The stop only
            // needs to cover explicit commission plus the configured execution reserve.
            var costBufferPips = (EstimateRoundTripCommissionPips() + Math.Max(0.0, SlippageReservePips)) * BreakevenCostBufferMultiplier;
            var newStop = position.TradeType == TradeType.Buy
                ? position.EntryPrice + costBufferPips * Symbol.PipSize
                : position.EntryPrice - costBufferPips * Symbol.PipSize;

            if (!CanImproveStop(position, newStop, 0.10))
                return;
            if (!ProtectionUpdateAllowed(state))
                return;

            var result = ModifyPosition(position, newStop, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[V3 PROTECTION] breakeven modify failed id={0} error={1}", position.Id, result.Error);
                return;
            }

            state.BreakevenApplied = true;
            state.LastProtectionUpdateTime = Server.Time;
            DebugLog("BREAKEVEN id={0} stop={1}", position.Id, newStop);
        }

        private void TryApplyAtrTrail(Position position, TradeState state)
        {
            if (Bars.Count < 3 || !ProtectionUpdateAllowed(state))
                return;
            var index = Bars.Count - 2;
            var atrPrice = _atr.Result[index];
            if (atrPrice <= 0 || double.IsNaN(atrPrice) || double.IsInfinity(atrPrice))
                return;

            var distance = atrPrice * TrailingAtrMultiplier;
            var newStop = position.TradeType == TradeType.Buy
                ? Symbol.Bid - distance
                : Symbol.Ask + distance;

            if (!CanImproveStop(position, newStop, MinTrailStepPips))
                return;

            var result = ModifyPosition(position, newStop, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[V3 PROTECTION] trail modify failed id={0} error={1}", position.Id, result.Error);
                return;
            }

            state.TrailingActivated = true;
            state.LastProtectionUpdateTime = Server.Time;
            DebugLog("TRAIL id={0} stop={1}", position.Id, newStop);
        }

        private bool ProtectionUpdateAllowed(TradeState state)
        {
            if (MinProtectionUpdateSeconds <= 0 || state.LastProtectionUpdateTime == default(DateTime))
                return true;
            return (Server.Time - state.LastProtectionUpdateTime).TotalSeconds >= MinProtectionUpdateSeconds;
        }

        private bool CanImproveStop(Position position, double newStop, double minimumStepPips)
        {
            if (newStop <= 0 || double.IsNaN(newStop) || double.IsInfinity(newStop))
                return false;

            var minDistancePips = GetBrokerMinimumStopPips() + BrokerDistanceBufferPips;
            var minDistancePrice = minDistancePips * Symbol.PipSize;
            var improveEpsilon = Math.Max(Symbol.TickSize, Math.Max(0.0, minimumStepPips) * Symbol.PipSize);

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
