from pathlib import Path

SOURCE = Path("GQ-Session-Scalper-v2/src/GQ_Session_Scalper_v2.cs")
s = SOURCE.read_text(encoding="utf-8")

field_anchor = "            public string ManagedExitReason;\n"
field_insert = (
    "            public string ManagedExitReason;\n"
    "            public double LastAppliedStopPrice;\n"
)
if "public double LastAppliedStopPrice;" not in s:
    if field_anchor not in s:
        raise SystemExit("PositionState field anchor not found")
    s = s.replace(field_anchor, field_insert, 1)

old_distance = '''            double minPips = GetBrokerMinStopLossPips() * 1.05;
            if (position.TradeType == TradeType.Buy)
                candidateStop = Math.Min(candidateStop, Symbol.Bid - minPips * Symbol.PipSize);
            else
                candidateStop = Math.Max(candidateStop, Symbol.Ask + minPips * Symbol.PipSize);
            candidateStop = Math.Round(candidateStop, Symbol.Digits);
'''
new_distance = '''            double brokerDistancePrice = GetBrokerMinStopLossPips() * Symbol.PipSize * 1.05;
            double executionBufferPrice = Math.Max(Symbol.TickSize * 2.0, Symbol.PipSize * 0.2);
            double minimumDistancePrice = Math.Max(brokerDistancePrice, executionBufferPrice);
            if (position.TradeType == TradeType.Buy)
                candidateStop = Math.Min(candidateStop, Symbol.Bid - minimumDistancePrice);
            else
                candidateStop = Math.Max(candidateStop, Symbol.Ask + minimumDistancePrice);
            candidateStop = Math.Round(candidateStop, Symbol.Digits);
'''
if "double minimumDistancePrice = Math.Max(brokerDistancePrice, executionBufferPrice);" not in s:
    if old_distance not in s:
        raise SystemExit("Stop-distance anchor not found")
    s = s.replace(old_distance, new_distance, 1)

old = '''            bool improves = !position.StopLoss.HasValue ||
                (position.TradeType == TradeType.Buy && candidateStop > position.StopLoss.Value) ||
                (position.TradeType == TradeType.Sell && candidateStop < position.StopLoss.Value);
            if (!improves)
                return;

            var result = ModifyPosition(position, candidateStop, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[STOP_UPDATE_ERROR] reason={0} error={1}", reason, result.Error);
                return;
            }
            PositionState state;
            if (_states.TryGetValue(position.Id, out state))
                state.ManagedExitReason = reason;
'''

new = '''            PositionState state;
            _states.TryGetValue(position.Id, out state);

            double referenceStop = position.StopLoss ?? 0.0;
            if (state != null && IsFinitePositive(state.LastAppliedStopPrice))
            {
                referenceStop = !IsFinitePositive(referenceStop)
                    ? state.LastAppliedStopPrice
                    : (position.TradeType == TradeType.Buy
                        ? Math.Max(referenceStop, state.LastAppliedStopPrice)
                        : Math.Min(referenceStop, state.LastAppliedStopPrice));
            }

            double minimumImprovement = Math.Max(Symbol.TickSize, Symbol.PipSize * 0.1);
            bool improves = !IsFinitePositive(referenceStop) ||
                (position.TradeType == TradeType.Buy && candidateStop >= referenceStop + minimumImprovement) ||
                (position.TradeType == TradeType.Sell && candidateStop <= referenceStop - minimumImprovement);
            if (!improves)
                return;

            var result = ModifyPosition(position, candidateStop, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("[STOP_UPDATE_ERROR] reason={0} error={1}", reason, result.Error);
                return;
            }

            if (state != null)
            {
                state.LastAppliedStopPrice = candidateStop;
                state.ManagedExitReason = reason;
            }
'''

if "double minimumImprovement = Math.Max(Symbol.TickSize, Symbol.PipSize * 0.1);" not in s:
    if old not in s:
        raise SystemExit("TryImproveStop anchor not found")
    s = s.replace(old, new, 1)

SOURCE.write_text(s, encoding="utf-8")
print("GQ stop-management and minimum-distance patches applied or already present.")
