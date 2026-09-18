from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

param_anchor = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
'''
param_new = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        // Commercial Convergence RC: one bounded context-admission layer.
        // Modes are preregistered; engineering/risk/execution infrastructure is untouched.
        [Parameter("Commercial Convergence Mode", DefaultValue = 0, MinValue = 0, MaxValue = 3)]
        public int CommercialConvergenceMode { get; set; }

        [Parameter("Commercial Abs High ATR", DefaultValue = 1.30, MinValue = 0.10, MaxValue = 20.0)]
        public double CommercialAbsHighAtr { get; set; }

        [Parameter("Commercial ATR Baseline Bars", DefaultValue = 240, MinValue = 60, MaxValue = 2880)]
        public int CommercialAtrBaselineBars { get; set; }

        [Parameter("Commercial High ATR Ratio", DefaultValue = 1.30, MinValue = 1.00, MaxValue = 3.00)]
        public double CommercialHighAtrRatio { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
        private long _commercialAdmissionSeen;
        private long _commercialAdmissionBlocked;
        private long _commercialCypherHighVolBlocked;
'''
if s.count(param_anchor) != 1:
    raise SystemExit(f'commercial parameter anchor count={s.count(param_anchor)}; expected 1')
s = s.replace(param_anchor, param_new, 1)

gate_anchor = '''                if (!PassMtfFilter(signal))
'''
gate_new = '''                // COMMERCIAL-CONVERGENCE ADMISSION.
                // Uses only signal-time information; no future bars, realized PnL or future excursion.
                double commercialBaseline;
                double commercialAtrRatio;
                string commercialReason;
                _commercialAdmissionSeen++;
                bool commercialBlocked = CommercialShouldBlock(signal, signalIndex, atrNow, out commercialBaseline, out commercialAtrRatio, out commercialReason);
                int commercialHour = (signalIndex >= 0 && signalIndex < _signalBars.Count) ? _signalBars.OpenTimes[signalIndex].Hour : Server.Time.Hour;
                if (commercialBlocked)
                {
                    _commercialAdmissionBlocked++;
                    if ((signal.PatternName ?? "").Equals("Cypher", StringComparison.OrdinalIgnoreCase))
                        _commercialCypherHighVolBlocked++;
                    Print("[COMM-ADMISSION] decision=BLOCK mode={0} pattern={1} dir={2} hour={3} atr={4:F4} baseline={5:F4} ratio={6:F3} confidence={7:F3} reason={8}",
                        CommercialConvergenceMode, signal.PatternName, signal.Direction, commercialHour, atrNow, commercialBaseline, commercialAtrRatio, signal.Confidence, commercialReason);
                    if (v29FromPending) V29RemovePending(signal, "COMMERCIAL_CONTEXT_BLOCK", false);
                    return;
                }
                Print("[COMM-ADMISSION] decision=ALLOW mode={0} pattern={1} dir={2} hour={3} atr={4:F4} baseline={5:F4} ratio={6:F3} confidence={7:F3} reason={8}",
                    CommercialConvergenceMode, signal.PatternName, signal.Direction, commercialHour, atrNow, commercialBaseline, commercialAtrRatio, signal.Confidence, commercialReason);

                if (!PassMtfFilter(signal))
'''
if s.count(gate_anchor) != 1:
    raise SystemExit(f'commercial gate anchor count={s.count(gate_anchor)}; expected 1')
s = s.replace(gate_anchor, gate_new, 1)

helper_anchor = '''        private double V295PeakFavorableR(GridBasket b)
'''
helper_new = '''        private double CommercialRollingTrueRangeBaseline(int endIndex)
        {
            if (_signalBars == null || endIndex < 1) return 0;
            int lookback = Math.Max(60, Math.Min(2880, CommercialAtrBaselineBars));
            int end = Math.Min(endIndex, _signalBars.Count - 1);
            int start = Math.Max(1, end - lookback + 1);
            double sum = 0;
            int count = 0;
            for (int i = start; i <= end; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr = Math.Max(high - low, Math.Max(Math.Abs(high - prevClose), Math.Abs(low - prevClose)));
                sum += tr;
                count++;
            }
            return count > 0 ? sum / count : 0;
        }

        private bool CommercialShouldBlock(Signal signal, int signalIndex, double atrNow, out double baseline, out double ratio, out string reason)
        {
            baseline = CommercialRollingTrueRangeBaseline(signalIndex);
            ratio = baseline > 0 ? atrNow / baseline : 0;
            reason = "PASS";
            if (CommercialConvergenceMode <= 0 || signal == null) return false;

            bool cypher = (signal.PatternName ?? "").Equals("Cypher", StringComparison.OrdinalIgnoreCase);
            if (!cypher) return false;

            if (CommercialConvergenceMode == 1)
            {
                if (atrNow >= CommercialAbsHighAtr)
                {
                    reason = "CYPHER_ABS_HIGH_VOL";
                    return true;
                }
                return false;
            }

            if (CommercialConvergenceMode == 2 || CommercialConvergenceMode == 3)
            {
                if (baseline > 0 && ratio >= CommercialHighAtrRatio)
                {
                    reason = "CYPHER_REL_HIGH_VOL";
                    return true;
                }
                return false;
            }

            return false;
        }

        private double V295PeakFavorableR(GridBasket b)
'''
if s.count(helper_anchor) != 1:
    raise SystemExit(f'commercial helper anchor count={s.count(helper_anchor)}; expected 1')
s = s.replace(helper_anchor, helper_new, 1)

stop_anchor = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            EnsureServerSideProtectionBeforeStop();
'''
stop_new = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            Print("[COMM-CONVERGENCE-SUMMARY] mode={0} seen={1} blocked={2} cypherHighVolBlocked={3} absHighAtr={4:F2} baselineBars={5} ratio={6:F2}",
                CommercialConvergenceMode, _commercialAdmissionSeen, _commercialAdmissionBlocked, _commercialCypherHighVolBlocked,
                CommercialAbsHighAtr, CommercialAtrBaselineBars, CommercialHighAtrRatio);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(stop_anchor) != 1:
    raise SystemExit(f'commercial stop anchor count={s.count(stop_anchor)}; expected 1')
s = s.replace(stop_anchor, stop_new, 1)

old_version = 'V29.5-Thesis-Validity-Minimum-Patch-Dev'
if s.count(old_version) != 1:
    raise SystemExit(f'commercial version marker count={s.count(old_version)}; expected 1')
s = s.replace(old_version, 'Commercial-Convergence-One-Pass-RC', 1)

required = [
    'Commercial-Convergence-One-Pass-RC',
    'CommercialConvergenceMode',
    'CommercialShouldBlock',
    '[COMM-ADMISSION]',
    '[COMM-CONVERGENCE-SUMMARY]',
    'V295ThesisGuard',
    'V29.3 GRID-RISK-CAP-HOTFIX'
]
for token in required:
    if token not in s:
        raise SystemExit('missing commercial convergence token: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied HarmonyBot Commercial Convergence One-Pass RC patch')
print('Scope: causal context admission + telemetry only; frozen engineering core unchanged')
