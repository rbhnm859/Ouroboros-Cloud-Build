from pathlib import Path
p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# Restore helper removed when v27 replaced the margin block.
if 'private bool IsGridGuardAccount()' not in s:
    marker = '''        private bool IsSmallAccountMode()\n        {\n'''
    helper = '''        private bool IsGridGuardAccount()\n        {\n            if (!SmallAccountMode) return false;\n            double guardThreshold = Math.Max(SmallAccountThreshold, SmallAccountThreshold * 2.0);\n            return Account.Equity <= guardThreshold + 1e-9;\n        }\n\n'''
    if marker not in s: raise SystemExit('IsSmallAccountMode marker missing')
    s = s.replace(marker, helper + marker, 1)

# Explicitly acknowledge that this parameter intentionally hides Algo.SymbolName.
s = s.replace('        public string SymbolName { get; set; }', '        public new string SymbolName { get; set; }', 1)

# Use the non-obsolete protection overload. All values below are absolute prices.
s = s.replace('ModifyPosition(p, newSl, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade)',
              'ModifyPosition(p, newSl, p.TakeProfit, ProtectionType.Absolute)')
s = s.replace('ModifyPosition(p, b.StopPrice, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade)',
              'ModifyPosition(p, b.StopPrice, p.TakeProfit, ProtectionType.Absolute)')
s = s.replace('ModifyPosition(p, sl, tp);', 'ModifyPosition(p, sl, tp, ProtectionType.Absolute);')
s = s.replace('ModifyPosition(p, b.StopPrice, p.TakeProfit);', 'ModifyPosition(p, b.StopPrice, p.TakeProfit, ProtectionType.Absolute);')

p.write_text(s, encoding='utf-8')
print('Restored grid helper and cleared known compile-debt warnings')
