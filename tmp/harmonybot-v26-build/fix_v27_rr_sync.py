from pathlib import Path
p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

needle = '''        [Parameter("Max SL Compression Ratio", DefaultValue = 0.90, MinValue = 0.0, MaxValue = 1.0)]\n        public double MaxStopCompressionRatio { get; set; }\n'''
insert = needle + '''\n        [Parameter("Compressed Target RR", DefaultValue = 2.4, MinValue = 2.0, MaxValue = 5.0)]\n        public double CompressedTargetRR { get; set; }\n'''
if needle not in s: raise SystemExit('RR parameter insertion point missing')
s = s.replace(needle, insert, 1)

old = '''                double spreadPips = Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid));\n                double rrFloor = slPips * MinRR + (UseCostAdjustedRR ? spreadPips : 0.0);\n                tpPips = Math.Max(tpPips, Math.Max(EffectiveMinTakeProfitPips(), rrFloor));\n'''
new = '''                double spreadPips = Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid));\n                double targetRR = Math.Max(MinRR, CompressedTargetRR);\n                double rebuiltTp = slPips * targetRR + (UseCostAdjustedRR ? spreadPips : 0.0);\n                tpPips = Math.Max(EffectiveMinTakeProfitPips(), rebuiltTp);\n'''
if old not in s: raise SystemExit('RR rebuild block missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Applied v27 compressed-SL RR synchronization')
