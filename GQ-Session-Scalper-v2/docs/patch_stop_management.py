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
print("GQ stop-management patch applied or already present.")
