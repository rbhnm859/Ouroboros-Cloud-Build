from pathlib import Path
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

anchor='''        [Parameter("Commercial High ATR Ratio", DefaultValue = 1.30, MinValue = 1.00, MaxValue = 3.00)]
        public double CommercialHighAtrRatio { get; set; }
'''
insert=anchor+'''
        // Final Commercial Freeze architecture. Engineering/risk/broker core is frozen.
        [Parameter("Final Edge Architecture", DefaultValue = true)]
        public bool FinalEdgeArchitecture { get; set; }

        [Parameter("Final Policy Profile", DefaultValue = 1, MinValue = 1, MaxValue = 3)]
        public int FinalPolicyProfile { get; set; }

        [Parameter("Final Require Closed-Bar Confirm", DefaultValue = true)]
        public bool FinalRequireClosedBarConfirm { get; set; }

        [Parameter("Final Pure Structural Payoff", DefaultValue = true)]
        public bool FinalPureStructuralPayoff { get; set; }

        [Parameter("Final Quality Scale", DefaultValue = 1.0, MinValue = 0.80, MaxValue = 1.20)]
        public double FinalQualityScale { get; set; }

        [Parameter("Final M15 Fast EMA", DefaultValue = 20, MinValue = 5, MaxValue = 100)]
        public int FinalM15FastEma { get; set; }

        [Parameter("Final M15 Slow EMA", DefaultValue = 50, MinValue = 20, MaxValue = 200)]
        public int FinalM15SlowEma { get; set; }
'''
if s.count(anchor)!=1: raise SystemExit(f'final param anchor count={s.count(anchor)}')
s=s.replace(anchor,insert,1)

field_anchor='''        private long _commercialAdmissionSeen;
        private long _commercialAdmissionBlocked;
        private long _commercialCypherHighVolBlocked;
'''
field_insert=field_anchor+'''        private double _cacheM15EmaFast, _cacheM15EmaSlow;
        private long _finalContextSeen, _finalContextAllowed, _finalContextBlocked, _finalConfirmBlocked;
        private readonly Dictionary<string, long> _finalBlockReasons = new Dictionary<string, long>();
'''
if s.count(field_anchor)!=1: raise SystemExit(f'field anchor count={s.count(field_anchor)}')
s=s.replace(field_anchor,field_insert,1)

cache_anchor='''            _cacheH1Ema50 = _cacheH1Ema200 = 0;
            _cacheH4Ema50 = _cacheH4Ema200 = 0;

            var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
'''
cache_insert='''            _cacheH1Ema50 = _cacheH1Ema200 = 0;
            _cacheH4Ema50 = _cacheH4Ema200 = 0;
            _cacheM15EmaFast = _cacheM15EmaSlow = 0;

            var m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);
            if (m15 != null && m15.Count >= Math.Max(FinalM15SlowEma + 1, 60))
            {
                int e15 = m15.Count - 2;
                if (e15 >= 0)
                {
                    _cacheM15EmaFast = CalculateEma(m15.ClosePrices, Math.Max(5, FinalM15FastEma), e15);
                    _cacheM15EmaSlow = CalculateEma(m15.ClosePrices, Math.Max(FinalM15FastEma + 1, FinalM15SlowEma), e15);
                }
            }

            var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
'''
if s.count(cache_anchor)!=1: raise SystemExit(f'cache anchor count={s.count(cache_anchor)}')
s=s.replace(cache_anchor,cache_insert,1)

helper_anchor='''        private bool PassMtfFilter(TradeDirection direction)
'''
helpers='''        private int FinalDirectionVote(double fast, double slow)
        {
            if (fast <= 0 || slow <= 0) return 0;
            if (fast > slow) return 1;
            if (fast < slow) return -1;
            return 0;
        }

        private void FinalCountBlock(string reason)
        {
            if (string.IsNullOrWhiteSpace(reason)) reason = "UNKNOWN";
            long n;
            _finalBlockReasons.TryGetValue(reason, out n);
            _finalBlockReasons[reason] = n + 1;
        }

        private double FinalSignalQuality(Signal signal)
        {
            return V29CompositeQuality(signal);
        }

        private bool FinalClosedBarConfirm(Signal signal, double atrNow, out string reason)
        {
            reason = "PASS";
            if (!FinalRequireClosedBarConfirm) return true;
            if (signal == null || _signalBars == null || atrNow <= 0 || _signalBars.Count < 4)
            {
                reason = "CONFIRM_DATA";
                return false;
            }
            int i = _signalBars.Count - 2;
            if (i < 2) { reason = "CONFIRM_DATA"; return false; }
            double o = _signalBars.OpenPrices[i], c = _signalBars.ClosePrices[i];
            double h = _signalBars.HighPrices[i], l = _signalBars.LowPrices[i];
            double pc = _signalBars.ClosePrices[i - 1];
            double body = Math.Abs(c - o);
            double minBodyAtr = FinalPolicyProfile == 3 ? 0.06 : (FinalPolicyProfile == 2 ? 0.04 : 0.02);
            if (body + 1e-12 < atrNow * minBodyAtr) { reason = "CONFIRM_BODY"; return false; }
            double safeBody = Math.Max(body, atrNow * 0.005);
            if (signal.Direction == TradeDirection.Buy)
            {
                double wick = Math.Max(0.0, Math.Min(o, c) - l);
                bool directional = c > o;
                bool reclaim = c >= pc;
                bool rejection = wick >= safeBody * 0.30;
                if (!((directional && reclaim) || rejection)) { reason = "CONFIRM_BUY"; return false; }
            }
            else
            {
                double wick = Math.Max(0.0, h - Math.Max(o, c));
                bool directional = c < o;
                bool reclaim = c <= pc;
                bool rejection = wick >= safeBody * 0.30;
                if (!((directional && reclaim) || rejection)) { reason = "CONFIRM_SELL"; return false; }
            }
            return true;
        }

        private bool FinalContextAllows(Signal signal, double atrNow, out string reason, out int alignedVotes, out double quality)
        {
            reason = "PASS";
            alignedVotes = 0;
            quality = 0;
            if (!FinalEdgeArchitecture) return true;
            if (signal == null) { reason = "NULL_SIGNAL"; return false; }

            int sig = signal.Direction == TradeDirection.Buy ? 1 : -1;
            int h4 = FinalDirectionVote(_cacheH4Ema50, _cacheH4Ema200);
            int h1 = FinalDirectionVote(_cacheH1Ema50, _cacheH1Ema200);
            int m15 = FinalDirectionVote(_cacheM15EmaFast, _cacheM15EmaSlow);
            if (h4 == 0 || h1 == 0 || m15 == 0) { reason = "CONTEXT_DATA"; return false; }

            if (h4 == sig) alignedVotes++;
            if (h1 == sig) alignedVotes++;
            if (m15 == sig) alignedVotes++;
            quality = FinalSignalQuality(signal);
            double qualityScale = Math.Max(0.80, Math.Min(1.20, FinalQualityScale));

            if (h4 == h1 && h4 == -sig) { reason = "HTF_CONSENSUS_OPPOSITE"; return false; }

            if (FinalPolicyProfile == 1)
            {
                if (h4 == h1 && h4 == sig)
                {
                    if (m15 == -sig) { reason = "M15_OPPOSES_HTF"; return false; }
                    if (quality < 0.56 * qualityScale) { reason = "QUALITY_BALANCED"; return false; }
                }
                else
                {
                    if (m15 != sig || alignedVotes < 2) { reason = "MIXED_CONTEXT"; return false; }
                    if (quality < 0.64 * qualityScale) { reason = "QUALITY_MIXED"; return false; }
                }
            }
            else if (FinalPolicyProfile == 2)
            {
                if (alignedVotes < 2) { reason = "VOTES_LT2"; return false; }
                if (quality < 0.60 * qualityScale) { reason = "QUALITY_CONSENSUS"; return false; }
            }
            else
            {
                if (alignedVotes < 3) { reason = "VOTES_LT3"; return false; }
                if (quality < 0.64 * qualityScale || signal.GeometryQuality < 0.55 * qualityScale || signal.PrzConfluence < 0.58 * qualityScale)
                { reason = "QUALITY_STRICT"; return false; }
            }

            string confirmReason;
            if (!FinalClosedBarConfirm(signal, atrNow, out confirmReason))
            {
                reason = confirmReason;
                return false;
            }
            return true;
        }

'''+helper_anchor
if s.count(helper_anchor)!=1: raise SystemExit(f'helper anchor count={s.count(helper_anchor)}')
s=s.replace(helper_anchor,helpers,1)

gate_anchor='''                Print("[COMM-ADMISSION] decision=ALLOW mode={0} pattern={1} dir={2} hour={3} atr={4:F4} baseline={5:F4} ratio={6:F3} confidence={7:F3} reason={8}",
                    CommercialConvergenceMode, signal.PatternName, signal.Direction, commercialHour, atrNow, commercialBaseline, commercialAtrRatio, signal.Confidence, commercialReason);

                if (!PassMtfFilter(signal))
'''
gate_insert='''                Print("[COMM-ADMISSION] decision=ALLOW mode={0} pattern={1} dir={2} hour={3} atr={4:F4} baseline={5:F4} ratio={6:F3} confidence={7:F3} reason={8}",
                    CommercialConvergenceMode, signal.PatternName, signal.Direction, commercialHour, atrNow, commercialBaseline, commercialAtrRatio, signal.Confidence, commercialReason);

                _finalContextSeen++;
                string finalReason;
                int finalVotes;
                double finalQuality;
                if (!FinalContextAllows(signal, atrNow, out finalReason, out finalVotes, out finalQuality))
                {
                    _finalContextBlocked++;
                    if (finalReason.StartsWith("CONFIRM", StringComparison.Ordinal)) _finalConfirmBlocked++;
                    FinalCountBlock(finalReason);
                    Print("[FINAL-EDGE] decision=BLOCK profile={0} pattern={1} dir={2} votes={3} q={4:F3} reason={5}",
                        FinalPolicyProfile, signal.PatternName, signal.Direction, finalVotes, finalQuality, finalReason);
                    if (v29FromPending) V29RemovePending(signal, "FINAL_EDGE_" + finalReason, false);
                    return;
                }
                _finalContextAllowed++;
                Print("[FINAL-EDGE] decision=ALLOW profile={0} pattern={1} dir={2} votes={3} q={4:F3}",
                    FinalPolicyProfile, signal.PatternName, signal.Direction, finalVotes, finalQuality);

                if (!PassMtfFilter(signal))
'''
if s.count(gate_anchor)!=1: raise SystemExit(f'gate anchor count={s.count(gate_anchor)}')
s=s.replace(gate_anchor,gate_insert,1)

summary_anchor='''            Print("[COMM-CONVERGENCE-SUMMARY] mode={0} seen={1} blocked={2} cypherHighVolBlocked={3} absHighAtr={4:F2} baselineBars={5} ratio={6:F2}",
                CommercialConvergenceMode, _commercialAdmissionSeen, _commercialAdmissionBlocked, _commercialCypherHighVolBlocked,
                CommercialAbsHighAtr, CommercialAtrBaselineBars, CommercialHighAtrRatio);
            EnsureServerSideProtectionBeforeStop();
'''
summary_insert='''            Print("[COMM-CONVERGENCE-SUMMARY] mode={0} seen={1} blocked={2} cypherHighVolBlocked={3} absHighAtr={4:F2} baselineBars={5} ratio={6:F2}",
                CommercialConvergenceMode, _commercialAdmissionSeen, _commercialAdmissionBlocked, _commercialCypherHighVolBlocked,
                CommercialAbsHighAtr, CommercialAtrBaselineBars, CommercialHighAtrRatio);
            Print("[FINAL-EDGE-SUMMARY] enabled={0} profile={1} seen={2} allowed={3} blocked={4} confirmBlocked={5}",
                FinalEdgeArchitecture, FinalPolicyProfile, _finalContextSeen, _finalContextAllowed, _finalContextBlocked, _finalConfirmBlocked);
            foreach (var kv in _finalBlockReasons.OrderBy(k => k.Key))
                Print("[FINAL-EDGE-BLOCK] reason={0} count={1}", kv.Key, kv.Value);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(summary_anchor)!=1: raise SystemExit(f'summary anchor count={s.count(summary_anchor)}')
s=s.replace(summary_anchor,summary_insert,1)

manage_anchor='''                EnsureRuntimeState(p);
                double profitPips = p.Pips;
                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);
'''
manage_insert='''                EnsureRuntimeState(p);
                double profitPips = p.Pips;
                if (FinalEdgeArchitecture && FinalPureStructuralPayoff)
                    continue; // preserve server-side structural SL/TP; no partial/BE/trailing payoff clipping
                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);
'''
if s.count(manage_anchor)!=1: raise SystemExit(f'manage anchor count={s.count(manage_anchor)}')
s=s.replace(manage_anchor,manage_insert,1)

old='Commercial-Convergence-One-Pass-RC'
if s.count(old)!=1: raise SystemExit(f'version marker count={s.count(old)}')
s=s.replace(old,'Final-Commercial-Freeze-Architecture-RC',1)

for token in ['FinalEdgeArchitecture','FinalPolicyProfile','FinalPureStructuralPayoff','TimeFrame.Minute15','[FINAL-EDGE]','[FINAL-EDGE-SUMMARY]','Final-Commercial-Freeze-Architecture-RC','V29.3 GRID-RISK-CAP-HOTFIX']:
    if token not in s: raise SystemExit('missing '+token)
p.write_text(s,encoding='utf-8')
print('Applied Final Commercial Freeze Architecture RC')
print('Scope: strategy context/admission/confirmation only; engineering/risk/broker core unchanged')
