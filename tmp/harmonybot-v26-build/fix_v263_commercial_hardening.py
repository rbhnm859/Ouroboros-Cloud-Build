from pathlib import Path
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Commercial hardening parameters
needle='''        [Parameter("Small Account Grid Guard", DefaultValue = true)]\n        public bool SmallAccountGridGuard { get; set; }\n'''
insert=needle+'''\n        [Parameter("Commercial Risk Hardening", DefaultValue = true)]\n        public bool CommercialRiskHardening { get; set; }\n\n        [Parameter("Micro Stop Compression", DefaultValue = true)]\n        public bool MicroStopCompression { get; set; }\n\n        [Parameter("Micro Max Risk %", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 5.0)]\n        public double MicroMaxRiskPercent { get; set; }\n\n        [Parameter("Auto Disable Min Trades", DefaultValue = 20, MinValue = 5, MaxValue = 200)]\n        public int AutoDisableMinTrades { get; set; }\n'''
if needle not in s: raise SystemExit('parameter point missing')
s=s.replace(needle,insert,1)

# Auto-disable must have a statistically meaningful sample before starving a pattern.
s=s.replace('''                if (kv.Value.Trades < 5) continue;\n''','''                if (kv.Value.Trades < Math.Max(5, AutoDisableMinTrades)) continue;\n''',1)

# Partial-close hardening: never normalize a sub-minimum request upward and accidentally close the whole position.
old='''                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);\n                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);\n                long closeUnits = (long)Math.Floor(norm);\n                if (closeUnits <= 0) return false;\n\n                double remain = p.VolumeInUnits - closeUnits;\n                if (closeUnits < _symbol.VolumeInUnitsMin) return false;\n                if (remain > 0 && remain < _symbol.VolumeInUnitsMin) return false;\n'''
new='''                double minVol = _symbol.VolumeInUnitsMin;\n                if (minVol <= 0 || p.VolumeInUnits < (2.0 * minVol))\n                {\n                    _tp1Done[p.Id] = true;\n                    Print("[TP1-SKIP] PosId={0} volume={1} cannot be partially closed while leaving broker minimum {2}.", p.Id, p.VolumeInUnits, minVol);\n                    return false;\n                }\n\n                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);\n                if (closeUnitsRaw < minVol) return false;\n                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);\n                double maxClosable = p.VolumeInUnits - minVol;\n                double closeUnitsD = Math.Min(norm, maxClosable);\n                closeUnitsD = _symbol.NormalizeVolumeInUnits(closeUnitsD, RoundingMode.Down);\n                long closeUnits = (long)Math.Floor(closeUnitsD);\n                if (closeUnits < minVol || closeUnits <= 0) return false;\n\n                double remain = p.VolumeInUnits - closeUnits;\n                if (remain < minVol) return false;\n'''
if old not in s: raise SystemExit('partial close block missing')
s=s.replace(old,new,1)

# Fix minimum-volume risk bypass: compare raw risk-sized volume BEFORE NormalizeVolumeInUnits.
old='''            double vol = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);\n\n            if (vol >= _symbol.VolumeInUnitsMin)\n            {\n                if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;\n                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;\n            }\n\n            if (!AllowMinVolumeFallback) return 0;\n\n            double volRiskCap = IsSmallAccountMode() ? MicroMinVolumeRiskCapPercent : MinVolumeRiskCapPercent;\n'''
new='''            double minVol = _symbol.VolumeInUnitsMin;\n            if (minVol <= 0) return 0;\n\n            // Some broker/API combinations normalize a sub-minimum raw volume up to the minimum.\n            // That would silently bypass the fallback risk cap. Handle sub-minimum raw size first.\n            if (raw >= minVol)\n            {\n                double vol = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);\n                if (vol < minVol) return 0;\n                if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;\n                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;\n            }\n\n            if (!AllowMinVolumeFallback) return 0;\n\n            double volRiskCap = IsSmallAccountMode() && CommercialRiskHardening\n                ? Math.Min(MicroMinVolumeRiskCapPercent, MicroMaxRiskPercent)\n                : (IsSmallAccountMode() ? MicroMinVolumeRiskCapPercent : MinVolumeRiskCapPercent);\n'''
if old not in s: raise SystemExit('risk normalization block missing')
s=s.replace(old,new,1)
# remove duplicate declaration later
s=s.replace('''            double minVol = _symbol.VolumeInUnitsMin;\n            double minVolRisk = minVol * slPips * _symbol.PipValue;\n''','''            double minVolRisk = minVol * slPips * _symbol.PipValue;\n''',1)

# Micro-account structural stop compression before sizing: preserve a hard money-risk ceiling instead of letting one minimum-volume stop kill the test/account.
old='''                double volumeInUnits;\n                double? orderSlPips = slPips;\n                double? orderTpPips = tpPips;\n\n                bool useGridForThisTrade = EnableFibGrid && !(SmallAccountGridGuard && IsSmallAccountMode());\n'''
new='''                if (CommercialRiskHardening && MicroStopCompression && IsSmallAccountMode() && _symbol.PipValue > 0 && _symbol.VolumeInUnitsMin > 0)\n                {\n                    double riskPctCap = Math.Max(0.5, Math.Min(MicroMaxRiskPercent, RiskPercent));\n                    double affordableSl = (Account.Equity * riskPctCap / 100.0) / (_symbol.VolumeInUnitsMin * _symbol.PipValue);\n                    affordableSl = Math.Max(EffectiveMinStopLossPips(), affordableSl);\n                    if (slPips > affordableSl)\n                    {\n                        double oldSl = slPips;\n                        slPips = affordableSl;\n                        tpPips = Math.Max(tpPips, slPips * Math.Max(2.0, MinRR));\n                        Print("[MICRO-RISK] SL compressed {0:F1}->{1:F1} pips; TP={2:F1}; hard risk cap={3:F2}%", oldSl, slPips, tpPips, riskPctCap);\n                    }\n                }\n\n                double volumeInUnits;\n                double? orderSlPips = slPips;\n                double? orderTpPips = tpPips;\n\n                bool useGridForThisTrade = EnableFibGrid && !(SmallAccountGridGuard && IsSmallAccountMode());\n'''
if old not in s: raise SystemExit('pre-sizing block missing')
s=s.replace(old,new,1)

# API hardening / zero-warning modernization where semantics are clear.
s=s.replace('double leverage = Account.Leverage > 0 ? (double)Account.Leverage : MaxNotionalToEquityRatio;',
            'double leverage = Account.PreciseLeverage > 0 ? Account.PreciseLeverage : MaxNotionalToEquityRatio;',1)
# Modern absolute protection overload for all simple price-based protection modifications.
s=s.replace('ModifyPosition(p, newSl, p.TakeProfit)', 'ModifyPosition(p, newSl, p.TakeProfit, ProtectionType.Absolute)', 1)
s=s.replace('ModifyPosition(p, sl, tp)', 'ModifyPosition(p, sl, tp, ProtectionType.Absolute)')
s=s.replace('ModifyPosition(p, b.StopPrice, p.TakeProfit)', 'ModifyPosition(p, b.StopPrice, p.TakeProfit, ProtectionType.Absolute)')

p.write_text(s,encoding='utf-8')
print('Applied v26.3 commercial hardening')
