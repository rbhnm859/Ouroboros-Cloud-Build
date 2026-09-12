from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# v28 commercial accounting: reconstruct complete position lifecycle from
# broker HistoricalTrade closing deals. This keeps partial-close commissions,
# swaps and realized PnL exact instead of estimating them from pip value.

# 1) Main position close uses all closing deals for the position when available.
old = '''            double money = p.NetProfit;\n            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;\n            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;\n            double r = ComputeR(money, riskPips, initVol, p.Pips);\n'''
new = '''            double money = p.NetProfit;\n            double lifecyclePips = p.Pips;\n            double lifecycleVol;\n            double historyMoney, historyPips;\n            if (TryGetPositionLifecycleFromHistory(p.Id, out historyMoney, out historyPips, out lifecycleVol))\n            {\n                money = historyMoney;\n                lifecyclePips = historyPips;\n            }\n            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;\n            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;\n            double r = ComputeR(money, riskPips, initVol, lifecyclePips);\n'''
if old not in s:
    raise SystemExit('main close accounting block missing')
s = s.replace(old, new, 1)

s = s.replace('_tracker.AddTrade(Server.Time, r, money, p.Pips);',
              '_tracker.AddTrade(Server.Time, r, money, lifecyclePips);', 1)

# 2) Grid close gets the same exact broker-history accounting.
old = '''            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;\n            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;\n            double money = p.NetProfit;\n            double r = ComputeR(money, riskPips, initVol, p.Pips);\n'''
new = '''            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;\n            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;\n            double money = p.NetProfit;\n            double lifecyclePips = p.Pips;\n            double lifecycleVol;\n            double historyMoney, historyPips;\n            if (TryGetPositionLifecycleFromHistory(p.Id, out historyMoney, out historyPips, out lifecycleVol))\n            {\n                money = historyMoney;\n                lifecyclePips = historyPips;\n            }\n            double r = ComputeR(money, riskPips, initVol, lifecyclePips);\n'''
if old not in s:
    raise SystemExit('grid close accounting block missing')
s = s.replace(old, new, 1)

s = s.replace('_tracker.AddTrade(Server.Time, r, money, p.Pips);',
              '_tracker.AddTrade(Server.Time, r, money, lifecyclePips);', 1)

# 3) Broker-history helper. Weight pips by actually closed volume, while money
# is summed exactly from HistoricalTrade.NetProfit (includes swap/commission).
marker = '''        private double ComputeR(double money, double riskPips, double initVol, double pips)\n'''
helper = '''        private bool TryGetPositionLifecycleFromHistory(long positionId, out double netProfit, out double weightedPips, out double totalClosedVolume)\n        {\n            netProfit = 0;\n            weightedPips = 0;\n            totalClosedVolume = 0;\n            try\n            {\n                var deals = History.Where(h => (long)h.PositionId == positionId).ToArray();\n                if (deals == null || deals.Length == 0) return false;\n\n                double pipVol = 0;\n                foreach (var h in deals)\n                {\n                    if (h == null || h.SymbolName != SymbolName) continue;\n                    double v = Math.Max(0.0, h.VolumeInUnits);\n                    netProfit += h.NetProfit;\n                    pipVol += h.Pips * v;\n                    totalClosedVolume += v;\n                }\n                if (totalClosedVolume <= 0) return false;\n                weightedPips = pipVol / totalClosedVolume;\n                return true;\n            }\n            catch\n            {\n                netProfit = 0;\n                weightedPips = 0;\n                totalClosedVolume = 0;\n                return false;\n            }\n        }\n\n'''
if marker not in s:
    raise SystemExit('history-accounting helper marker missing')
s = s.replace(marker, helper + marker, 1)

for token in ['TryGetPositionLifecycleFromHistory(long positionId', 'History.Where(h => (long)h.PositionId == positionId)', 'h.NetProfit']:
    if token not in s:
        raise SystemExit('history-accounting audit missing: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied v28 broker-history lifecycle PnL accounting')
