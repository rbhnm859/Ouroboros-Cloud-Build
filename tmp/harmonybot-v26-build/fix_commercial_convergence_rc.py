from pathlib import Path

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# One-pass, preregistered context-admission layer only. Engineering/risk/execution core is untouched.
anchor='''        public bool V294AllowSell { get; set; }
'''
insert='''        public bool V294AllowSell { get; set; }

        [Parameter("Commercial Convergence Candidate", DefaultValue = 0, MinValue = 0, MaxValue = 3)]
        public int CommercialConvergenceCandidate { get; set; }

        private long _ccBlockedStructural;
        private long _ccBlockedAdaptive;
        private long _ccBlockedHour15;
'''
if s.count(anchor)!=1: raise SystemExit(f'candidate param anchor count={s.count(anchor)}')
s=s.replace(anchor,insert,1)

anchor2='''                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                if (atrNow <= 0 || atrNow < MinAtrPrice) return;
'''
insert2='''                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                if (atrNow <= 0 || atrNow < MinAtrPrice) return;

                // COMMERCIAL-CONVERGENCE-RC: causal context only; no future bars.
                double ccAtrBase = 0.0;
                int ccAtrN = 0;
                for (int ccI = 1; ccI <= 48 && signalIndex - ccI >= AtrPeriod; ccI++)
                {
                    double ccA = CalculateAtr(_signalBars, AtrPeriod, signalIndex - ccI);
                    if (ccA > 0) { ccAtrBase += ccA; ccAtrN++; }
                }
                ccAtrBase = ccAtrN > 0 ? ccAtrBase / ccAtrN : atrNow;
                double ccAtrRatio = ccAtrBase > 0 ? atrNow / ccAtrBase : 1.0;
                bool ccCypher = string.Equals(signal.PatternName, "Cypher", StringComparison.OrdinalIgnoreCase);

                // A: cross-window structural negative cluster discovered in frozen V29.5 evidence.
                if (CommercialConvergenceCandidate == 1 && ccCypher && atrNow >= 1.30)
                {
                    _ccBlockedStructural++;
                    if (v29FromPending) V29RemovePending(signal, "CC_A_CYPHER_HIGH_VOL", false);
                    return;
                }

                // B/C: regime-adaptive Cypher admission using only preceding ATR observations.
                if ((CommercialConvergenceCandidate == 2 || CommercialConvergenceCandidate == 3)
                    && ccCypher && ccAtrN >= 24 && ccAtrRatio >= 1.35)
                {
                    _ccBlockedAdaptive++;
                    if (v29FromPending) V29RemovePending(signal, "CC_B_CYPHER_REL_HIGH_VOL", false);
                    return;
                }

                // C: add the only hour cluster that was negative in all three frozen DEV windows.
                // This is preregistered and is NOT the DEV-B-only 13:00 concentration.
                if (CommercialConvergenceCandidate == 3 && Server.Time.Hour == 15)
                {
                    _ccBlockedHour15++;
                    if (v29FromPending) V29RemovePending(signal, "CC_C_HOUR15_STRUCTURAL", false);
                    return;
                }
'''
if s.count(anchor2)!=1: raise SystemExit(f'ATR admission anchor count={s.count(anchor2)}')
s=s.replace(anchor2,insert2,1)

stop='''            Print("[V294-EDGE-SUMMARY] directionBlocked={0} allowBuy={1} allowSell={2}", _v294DirectionBlocked, V294AllowBuy, V294AllowSell);
'''
stop2='''            Print("[CC-RC-SUMMARY] candidate={0} structuralBlocked={1} adaptiveBlocked={2} hour15Blocked={3}", CommercialConvergenceCandidate, _ccBlockedStructural, _ccBlockedAdaptive, _ccBlockedHour15);
            Print("[V294-EDGE-SUMMARY] directionBlocked={0} allowBuy={1} allowSell={2}", _v294DirectionBlocked, V294AllowBuy, V294AllowSell);
'''
if s.count(stop)!=1: raise SystemExit(f'summary anchor count={s.count(stop)}')
s=s.replace(stop,stop2,1)

for token in ['CommercialConvergenceCandidate','CC_A_CYPHER_HIGH_VOL','CC_B_CYPHER_REL_HIGH_VOL','CC_C_HOUR15_STRUCTURAL','[CC-RC-SUMMARY]']:
    if token not in s: raise SystemExit('missing '+token)
p.write_text(s,encoding='utf-8')
print('Applied one-pass Commercial Convergence RC admission patch')
