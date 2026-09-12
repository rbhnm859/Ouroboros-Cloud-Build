from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# v28 commercial diagnostics: distinguish strategy scarcity from broker/minimum-
# volume capital infeasibility. Do not raise risk; report the equity required to
# carry the structural stop at the configured risk budget.

# 1) Counter.
needle = '        private long _diagDuplicateBlocked;\n'
insert = needle + '        private long _diagCapitalInfeasible;\n'
if needle not in s:
    raise SystemExit('capital diag field insertion point missing')
s = s.replace(needle, insert, 1)

# 2) When even the minimum allowed SL cannot fit the risk budget.
old = '''            if (double.IsNaN(maxPips) || double.IsInfinity(maxPips) || maxPips < floorPips)\n            {\n                if ((Server.Time - _lastVolumeWarnTime).TotalMinutes >= 5)\n                {\n                    Print("[RISK-BLOCK] minVol={0} riskBudget={1:F2}% cannot support minSL={2:F1} pips (max={3:F1}).",\n                        minVol, riskBudgetPct, floorPips, maxPips);\n                    _lastVolumeWarnTime = Server.Time;\n                }\n                return false;\n            }\n'''
new = '''            if (double.IsNaN(maxPips) || double.IsInfinity(maxPips) || maxPips < floorPips)\n            {\n                _diagCapitalInfeasible++;\n                double requiredEquity = EstimateRequiredEquityForRisk(minVol, floorPips, riskBudgetPct);\n                if ((Server.Time - _lastVolumeWarnTime).TotalMinutes >= 5)\n                {\n                    Print("[RISK-BLOCK] minVol={0} riskBudget={1:F2}% cannot support minSL={2:F1} pips (max={3:F1}).",\n                        minVol, riskBudgetPct, floorPips, maxPips);\n                    Print("[CAPITAL-FEASIBILITY] equity={0:F2} requiredEquity={1:F2} minVol={2} structuralSL={3:F1} riskBudget={4:F2}%.",\n                        Account.Equity, requiredEquity, minVol, floorPips, riskBudgetPct);\n                    _lastVolumeWarnTime = Server.Time;\n                }\n                return false;\n            }\n'''
if old not in s:
    raise SystemExit('capital minimum-SL risk block missing')
s = s.replace(old, new, 1)

# 3) Structural stop would require more compression than commercial policy allows.
old = '''                if (compression > Math.Max(0.0, Math.Min(1.0, MaxStopCompressionRatio)))\n                {\n                    Print("[RISK-BLOCK] SL compression {0:P1} exceeds limit {1:P1}; original={2:F1} max={3:F1}.",\n                        compression, MaxStopCompressionRatio, slPips, maxPips);\n                    return false;\n                }\n'''
new = '''                if (compression > Math.Max(0.0, Math.Min(1.0, MaxStopCompressionRatio)))\n                {\n                    _diagCapitalInfeasible++;\n                    double requiredEquity = EstimateRequiredEquityForRisk(minVol, slPips, riskBudgetPct);\n                    Print("[RISK-BLOCK] SL compression {0:P1} exceeds limit {1:P1}; original={2:F1} max={3:F1}.",\n                        compression, MaxStopCompressionRatio, slPips, maxPips);\n                    Print("[CAPITAL-FEASIBILITY] equity={0:F2} requiredEquity={1:F2} minVol={2} structuralSL={3:F1} riskBudget={4:F2}%.",\n                        Account.Equity, requiredEquity, minVol, slPips, riskBudgetPct);\n                    return false;\n                }\n'''
if old not in s:
    raise SystemExit('capital compression risk block missing')
s = s.replace(old, new, 1)

# 4) Helper uses broker-native AmountRisked.
marker = '''        private double CalculateVolumeByRisk(double slPips, double riskBudgetPct)\n'''
helper = '''        private double EstimateRequiredEquityForRisk(double volumeInUnits, double slPips, double riskBudgetPct)\n        {\n            if (_symbol == null || volumeInUnits <= 0 || slPips <= 0 || riskBudgetPct <= 0) return double.MaxValue;\n            try\n            {\n                double riskMoney = _symbol.AmountRisked(volumeInUnits, slPips);\n                if (riskMoney <= 0 || double.IsNaN(riskMoney) || double.IsInfinity(riskMoney)) return double.MaxValue;\n                return riskMoney / (riskBudgetPct / 100.0);\n            }\n            catch { return double.MaxValue; }\n        }\n\n'''
if marker not in s:
    raise SystemExit('capital helper marker missing')
s = s.replace(marker, helper + marker, 1)

# 5) Include in final commercial diagnostic line created by release audit.
old = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked);\n'''
new = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10} capitalInfeasible={11}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible);\n'''
if old not in s:
    raise SystemExit('capital diagnostic final line missing')
s = s.replace(old, new, 1)

for token in ['EstimateRequiredEquityForRisk', '[CAPITAL-FEASIBILITY]', '_diagCapitalInfeasible']:
    if token not in s:
        raise SystemExit('capital feasibility audit missing: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied v28 minimum-capital feasibility diagnostics')
