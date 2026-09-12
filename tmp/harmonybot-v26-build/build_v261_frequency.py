from pathlib import Path
import base64, gzip, hashlib, re

root = Path('tmp/harmonybot-v26-build')
payload = ''.join((root / f'payload.part0{i}').read_text() for i in range(1, 5))
source = gzip.decompress(base64.b64decode(payload))
digest = hashlib.sha256(source).hexdigest()
expected = 'e8d1782174c8f64e7620e2503007541d2ea3bcc2c3daf9fc74e6d21326c65d54'
if digest != expected:
    raise SystemExit(f'Source checksum mismatch: {digest} != {expected}')

text = source.decode('utf-8')
text = text.replace(
    'long step = _symbol.VolumeInUnitsStep > 0 ? _symbol.VolumeInUnitsStep : 1;',
    'double step = _symbol.VolumeInUnitsStep > 0 ? _symbol.VolumeInUnitsStep : 1;')

main_pattern = r'(?s)\s*var marketParams = new MarketOrderParameters\s*\{.*?Comment = "HarmonyBotPro"\s*\};\s*return ExecuteMarketOrder\(marketParams\);'
main_replacement = '''
            return ExecuteMarketOrder(tt, SymbolName, vol, BotLabel, slPips, tpPips,
                "HarmonyBotPro", false, StopTriggerMethod.Trade);'''
text, n_main = re.subn(main_pattern, main_replacement, text, count=1)

grid_pattern = r'(?s)\s*var marketParams = new MarketOrderParameters\s*\{.*?Comment = "HarmonyBotPro-G"\s*\};\s*return ExecuteMarketOrder\(marketParams\);'
grid_replacement = '''
            return ExecuteMarketOrder(tt, SymbolName, vol, GridLabel, slPips, null,
                "HarmonyBotPro-G", false, StopTriggerMethod.Trade);'''
text, n_grid = re.subn(grid_pattern, grid_replacement, text, count=1)
if n_main != 1 or n_grid != 1:
    raise SystemExit(f'API patch mismatch: main={n_main}, grid={n_grid}')

needle = '''        [Parameter("Max Entry Dev (ATR)", DefaultValue = 0.5, MinValue = 0.1, MaxValue = 2.0)]\n        public double MaxEntryDeviationAtr { get; set; }\n'''
insert = needle + '''\n        [Parameter("Adaptive Frequency Recovery", DefaultValue = true)]\n        public bool AdaptiveFrequencyRecovery { get; set; }\n\n        [Parameter("Soft MTF Reversal Gate", DefaultValue = true)]\n        public bool SoftMtfReversalGate { get; set; }\n\n        [Parameter("Countertrend Confidence Buffer", DefaultValue = 0.06, MinValue = 0.0, MaxValue = 0.20)]\n        public double CounterTrendConfidenceBuffer { get; set; }\n\n        [Parameter("Adaptive Entry Dev Floor (ATR)", DefaultValue = 0.85, MinValue = 0.5, MaxValue = 2.0)]\n        public double AdaptiveEntryDeviationFloor { get; set; }\n'''
if needle not in text:
    raise SystemExit('parameter insertion point not found')
text = text.replace(needle, insert, 1)

needle2 = '''                _detector = new HarmonicPatternDetector(\n                    SwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,\n                    PivotScanCount, MinLegAtrRatio, GlobalMinScore, ConsensusBonus,\n                    FibTolerance, MaxEntryDeviationAtr,\n'''
replace2 = '''                double effectiveMinLegAtrRatio = AdaptiveFrequencyRecovery ? Math.Min(MinLegAtrRatio, 0.70) : MinLegAtrRatio;\n                double effectiveFibTolerance = AdaptiveFrequencyRecovery ? Math.Min(0.20, FibTolerance + 0.015) : FibTolerance;\n                double effectiveEntryDeviationAtr = AdaptiveFrequencyRecovery ? Math.Max(MaxEntryDeviationAtr, AdaptiveEntryDeviationFloor) : MaxEntryDeviationAtr;\n\n                _detector = new HarmonicPatternDetector(\n                    SwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,\n                    PivotScanCount, effectiveMinLegAtrRatio, GlobalMinScore, ConsensusBonus,\n                    effectiveFibTolerance, effectiveEntryDeviationAtr,\n'''
if needle2 not in text:
    raise SystemExit('detector constructor insertion point not found')
text = text.replace(needle2, replace2, 1)

text = text.replace('                if (!PassMtfFilter(signal.Direction)) return;\n', '                if (!PassMtfFilter(signal)) return;\n', 1)

old = '''        private bool PassMtfFilter(TradeDirection direction)\n        {\n            if (!MTFEnabled && !H4FilterEnabled) return true;\n\n            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)\n            {\n                bool ok = direction == TradeDirection.Buy ? _cacheH1Ema50 > _cacheH1Ema200 : _cacheH1Ema50 < _cacheH1Ema200;\n                if (!ok) return false;\n            }\n\n            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)\n            {\n                bool ok = direction == TradeDirection.Buy ? _cacheH4Ema50 > _cacheH4Ema200 : _cacheH4Ema50 < _cacheH4Ema200;\n                if (!ok) return false;\n            }\n\n            return true;\n        }\n'''
new = '''        private bool PassMtfFilter(Signal signal)\n        {\n            if (signal == null) return false;\n            if (!MTFEnabled && !H4FilterEnabled) return true;\n\n            bool h1Aligned = true;\n            bool h4Aligned = true;\n\n            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)\n                h1Aligned = signal.Direction == TradeDirection.Buy ? _cacheH1Ema50 > _cacheH1Ema200 : _cacheH1Ema50 < _cacheH1Ema200;\n\n            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)\n                h4Aligned = signal.Direction == TradeDirection.Buy ? _cacheH4Ema50 > _cacheH4Ema200 : _cacheH4Ema50 < _cacheH4Ema200;\n\n            if (h1Aligned && h4Aligned) return true;\n\n            if (AdaptiveFrequencyRecovery && SoftMtfReversalGate)\n            {\n                double required = Math.Min(0.95, Math.Max(PatternConfidence, GlobalMinScore) + CounterTrendConfidenceBuffer);\n                if (signal.Confidence >= required)\n                {\n                    Print("[MTF-SOFT] Counter-trend {0} accepted conf={1:F3} required={2:F3}",\n                        signal.Direction, signal.Confidence, required);\n                    return true;\n                }\n            }\n\n            return false;\n        }\n'''
if old not in text:
    raise SystemExit('MTF filter block not found')
text = text.replace(old, new, 1)

out = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding='utf-8')
print('v26.1 patched source sha256:', hashlib.sha256(text.encode('utf-8')).hexdigest())
