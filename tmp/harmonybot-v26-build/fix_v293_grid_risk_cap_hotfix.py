from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

old = '''            TradeDirection dir = p.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;\n            double stopPrice = FibonacciGridEngine.BasketStopPrice(dir, p.EntryPrice, baseRiskPrice, GridStopFib);\n\n            var b = new GridBasket\n'''
new = '''            TradeDirection dir = p.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;\n            double stopPrice = FibonacciGridEngine.BasketStopPrice(dir, p.EntryPrice, baseRiskPrice, GridStopFib);\n\n            // V29.3 GRID-RISK-CAP-HOTFIX: the synthetic basket stop must never\n            // sit farther from entry than the broker-accepted protective SL.\n            // V28.4 already caps the primary order to the executable all-in risk\n            // budget; reapplying GridStopFib here would otherwise defeat that cap.\n            if (CommercialRiskEngine && CapGridStopToRiskBudget && p.StopLoss.HasValue)\n            {\n                double protectedStop = p.StopLoss.Value;\n                double uncappedStop = stopPrice;\n                stopPrice = dir == TradeDirection.Buy\n                    ? Math.Max(stopPrice, protectedStop)\n                    : Math.Min(stopPrice, protectedStop);\n                if (Math.Abs(stopPrice - uncappedStop) > 1e-12)\n                    Print(\"[V293-GRID-RISK-CAP] pos={0} uncapped={1:F2} protectedSL={2:F2} basketStop={3:F2}\",\n                        p.Id, uncappedStop, protectedStop, stopPrice);\n            }\n\n            var b = new GridBasket\n'''
if s.count(old) != 1:
    raise SystemExit(f'CreateBasketFor stop anchor count={s.count(old)}; expected 1')
s = s.replace(old, new, 1)

s = s.replace('V29.2-Grid-Lifecycle-Hotfix-RC', 'V29.3-Grid-Risk-Cap-Hotfix-RC', 1)

for required in [
    'V29.3 GRID-RISK-CAP-HOTFIX',
    '[V293-GRID-RISK-CAP]',
    'CapGridStopToRiskBudget && p.StopLoss.HasValue',
    'V29.3-Grid-Risk-Cap-Hotfix-RC',
    'CreateBasketFor(tr.Position)',
    'EnableFibGrid'
]:
    if required not in s:
        raise SystemExit(f'missing required token after V29.3 patch: {required}')

p.write_text(s, encoding='utf-8')
print('V29.3 Grid risk-cap hotfix applied')
print('Synthetic basket stop capped to broker-protected position SL; Harmonic/Entry/Filters/Grid ladder unchanged')
