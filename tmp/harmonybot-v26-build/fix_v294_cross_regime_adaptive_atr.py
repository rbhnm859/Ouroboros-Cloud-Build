from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

param_old = '''        [Parameter("Min ATR (price)", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 50.0)]
        public double MinAtrPrice { get; set; }

'''
param_new = '''        [Parameter("Min ATR (price)", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 50.0)]
        public double MinAtrPrice { get; set; }

        [Parameter("V29.4 Relative ATR Regime", DefaultValue = false)]
        public bool V294RelativeAtrRegime { get; set; }

        [Parameter("V29.4 ATR Baseline Bars", DefaultValue = 240, MinValue = 60, MaxValue = 2880)]
        public int V294AtrBaselineBars { get; set; }

        [Parameter("V29.4 Min ATR / Baseline", DefaultValue = 1.00, MinValue = 0.40, MaxValue = 1.40)]
        public double V294MinAtrBaselineRatio { get; set; }

        [Parameter("V29.4 Absolute ATR Floor", DefaultValue = 0.10, MinValue = 0.01, MaxValue = 5.0)]
        public double V294AbsoluteAtrFloor { get; set; }

'''
if s.count(param_old) != 1:
    raise SystemExit(f'V29.4 parameter anchor count={s.count(param_old)}; expected 1')
s = s.replace(param_old, param_new, 1)

gate_old = '''                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                double effectiveMinAtr = AdaptiveFrequencyRecovery
                    ? Math.Max(0.1, MinAtrPrice * Math.Max(0.40, Math.Min(1.0, AdaptiveMinAtrFactor)))
                    : MinAtrPrice;
                if (atrNow <= 0 || atrNow < effectiveMinAtr)
                {
                    _diagAtrBlocked++;
                    return;
                }

                double regimeScore = CalculateRegimeScore(atrNow);
'''
gate_new = '''                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                double rollingAtrBaseline = V294RollingTrueRangeBaseline(signalIndex);
                double effectiveMinAtr;
                if (V294RelativeAtrRegime && rollingAtrBaseline > 0)
                {
                    effectiveMinAtr = Math.Max(
                        Math.Max(0.01, V294AbsoluteAtrFloor),
                        rollingAtrBaseline * Math.Max(0.40, Math.Min(1.40, V294MinAtrBaselineRatio)));
                }
                else
                {
                    effectiveMinAtr = AdaptiveFrequencyRecovery
                        ? Math.Max(0.1, MinAtrPrice * Math.Max(0.40, Math.Min(1.0, AdaptiveMinAtrFactor)))
                        : MinAtrPrice;
                }

                if (atrNow <= 0 || atrNow < effectiveMinAtr)
                {
                    _diagAtrBlocked++;
                    return;
                }

                double regimeScore = CalculateRegimeScore(atrNow, signalIndex);
'''
if s.count(gate_old) != 1:
    raise SystemExit(f'V29.4 ATR gate anchor count={s.count(gate_old)}; expected 1')
s = s.replace(gate_old, gate_new, 1)

reg_old = '''        private double CalculateRegimeScore(double atrNow)
        {
            double baseline = 0;
            int n = Math.Min(Math.Max(0, _signalBars.Count - 2), 240);
            int start = Math.Max(1, n - 239);
            double sum = 0;
            int cnt = 0;

            for (int i = start; i <= n; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr1 = high - low;
                double tr2 = Math.Abs(high - prevClose);
                double tr3 = Math.Abs(low - prevClose);
                sum += Math.Max(tr1, Math.Max(tr2, tr3));
                cnt++;
            }
            if (cnt > 0) baseline = sum / cnt;

            double regime = 0.5;
            if (baseline > 0 && atrNow > 0)
            {
                double ratio = atrNow / baseline;
                regime = Clamp01((ratio - 0.8) / 0.8);
            }

            if (_cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                double pct = Math.Abs(_cacheH4Ema50 - _cacheH4Ema200) / _cacheH4Ema200;
                double trendStr = Clamp01(pct / 0.03);
                regime = 0.5 * regime + 0.5 * trendStr;
            }

            return regime;
        }
'''
reg_new = '''        private double V294RollingTrueRangeBaseline(int endIndex)
        {
            if (_signalBars == null || endIndex < 1) return 0;
            int lookback = Math.Max(60, Math.Min(2880, V294AtrBaselineBars));
            int end = Math.Min(endIndex, _signalBars.Count - 1);
            int start = Math.Max(1, end - lookback + 1);
            double sum = 0;
            int cnt = 0;

            for (int i = start; i <= end; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr1 = high - low;
                double tr2 = Math.Abs(high - prevClose);
                double tr3 = Math.Abs(low - prevClose);
                sum += Math.Max(tr1, Math.Max(tr2, tr3));
                cnt++;
            }
            return cnt > 0 ? sum / cnt : 0;
        }

        private double CalculateRegimeScore(double atrNow, int signalIndex)
        {
            // V29.4: use the rolling window ending at the evaluated bar.
            // V29.3 accidentally anchored the regime baseline to the early history.
            double baseline = V294RollingTrueRangeBaseline(signalIndex);

            double regime = 0.5;
            if (baseline > 0 && atrNow > 0)
            {
                double ratio = atrNow / baseline;
                regime = Clamp01((ratio - 0.8) / 0.8);
            }

            if (_cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                double pct = Math.Abs(_cacheH4Ema50 - _cacheH4Ema200) / _cacheH4Ema200;
                double trendStr = Clamp01(pct / 0.03);
                regime = 0.5 * regime + 0.5 * trendStr;
            }

            return regime;
        }
'''
if s.count(reg_old) != 1:
    raise SystemExit(f'V29.4 regime anchor count={s.count(reg_old)}; expected 1')
s = s.replace(reg_old, reg_new, 1)

if s.count('V29.3-Grid-Risk-Cap-Hotfix-RC') < 1:
    raise SystemExit('V29.3 version marker missing')
s = s.replace('V29.3-Grid-Risk-Cap-Hotfix-RC', 'V29.4-Cross-Regime-ATR-Rolling-Dev', 1)

for required in [
    'V29.4-Cross-Regime-ATR-Rolling-Dev',
    'V294RelativeAtrRegime',
    'V294RollingTrueRangeBaseline(signalIndex)',
    'CalculateRegimeScore(atrNow, signalIndex)',
    'V29.3 GRID-RISK-CAP-HOTFIX',
    'V292FastSmallAccountExecution'
]:
    if required not in s:
        raise SystemExit(f'missing required V29.4 token: {required}')

if 'CalculateRegimeScore(atrNow);' in s:
    raise SystemExit('stale V29.3 regime call remains')

p.write_text(s, encoding='utf-8')
print('V29.4 Cross-Regime ATR Rolling Development patch applied')
print('Engineering core unchanged; only rolling regime baseline + optional relative ATR gate added')
