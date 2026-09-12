from pathlib import Path
p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')
marker = '''        private bool PassMtfFilter(Signal signal)\n        {\n'''
if marker not in s:
    raise SystemExit('Signal MTF overload not found')
strict = '''        private bool PassMtfFilter(TradeDirection direction)\n        {\n            if (!MTFEnabled && !H4FilterEnabled) return true;\n\n            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)\n            {\n                bool ok = direction == TradeDirection.Buy ? _cacheH1Ema50 > _cacheH1Ema200 : _cacheH1Ema50 < _cacheH1Ema200;\n                if (!ok) return false;\n            }\n\n            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)\n            {\n                bool ok = direction == TradeDirection.Buy ? _cacheH4Ema50 > _cacheH4Ema200 : _cacheH4Ema50 < _cacheH4Ema200;\n                if (!ok) return false;\n            }\n\n            return true;\n        }\n\n'''
s = s.replace(marker, strict + marker, 1)
p.write_text(s, encoding='utf-8')
print('Added strict TradeDirection overload for GridTrendAllows')
