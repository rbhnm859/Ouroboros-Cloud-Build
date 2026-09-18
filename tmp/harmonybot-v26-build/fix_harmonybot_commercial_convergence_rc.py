from pathlib import Path

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

anchor='''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }
'''
insert=anchor+'''
        // Commercial Convergence RC: strategy-edge layer only. Engineering core frozen.
        [Parameter("CC Candidate", DefaultValue = 0, MinValue = 0, MaxValue = 3)]
        public int CCCandidate { get; set; }

        [Parameter("CC High ATR", DefaultValue = 1.30, MinValue = 0.50, MaxValue = 5.0)]
        public double CCHighAtr { get; set; }

        [Parameter("CC Relative ATR Ratio", DefaultValue = 1.50, MinValue = 1.0, MaxValue = 3.0)]
        public double CCRelativeAtrRatio { get; set; }

        private long _ccBlockedStructural;
        private long _ccBlockedRegime;
        private long _ccBlockedHour15;
'''
if s.count(anchor)!=1: raise SystemExit('CC param anchor mismatch')
s=s.replace(anchor,insert,1)

gate='''                if (!PassMtfFilter(signal))
'''
logic='''                // COMMERCIAL-CONVERGENCE: causal admission state only.
                // Candidate A: cross-window structural Cypher/high-ATR exclusion.
                // Candidate B: A plus relative rolling ATR regime.
                // Candidate C: B plus cross-window-negative 15:00 UTC structural session exclusion.
                double ccAtr = _atr.Result.LastValue;
                double ccAtrMean = 0.0;
                int ccAtrN = Math.Min(20, Bars.Count - 1);
                if (ccAtrN > 0)
                {
                    for (int ccI = 1; ccI <= ccAtrN; ccI++) ccAtrMean += _atr.Result.Last(ccI);
                    ccAtrMean /= ccAtrN;
                }
                double ccAtrRatio = ccAtrMean > 0 ? ccAtr / ccAtrMean : 1.0;
                bool ccCypher = string.Equals(signal.PatternName, "Cypher", StringComparison.OrdinalIgnoreCase);
                bool ccAbsoluteHigh = ccAtr >= CCHighAtr;
                bool ccRelativeHigh = ccAtrRatio >= CCRelativeAtrRatio;
                string ccReason = null;

                if (CCCandidate >= 1 && ccCypher && ccAbsoluteHigh)
                {
                    _ccBlockedStructural++;
                    ccReason = "CYPHER_HIGH_ATR";
                }
                if (ccReason == null && CCCandidate >= 2 && ccCypher && ccRelativeHigh)
                {
                    _ccBlockedRegime++;
                    ccReason = "CYPHER_RELATIVE_HIGH_ATR";
                }
                if (ccReason == null && CCCandidate >= 3 && Server.Time.Hour == 15)
                {
                    _ccBlockedHour15++;
                    ccReason = "STRUCTURAL_HOUR15";
                }

                Print("[CC-ADMISSION] candidate={0} pattern={1} dir={2} hour={3} atr={4:F5} atrMean20={5:F5} atrRatio={6:F3} decision={7}",
                    CCCandidate, signal.PatternName, signal.Direction, Server.Time.Hour, ccAtr, ccAtrMean, ccAtrRatio, ccReason ?? "ALLOW");

                if (ccReason != null)
                {
                    if (v29FromPending) V29RemovePending(signal, ccReason, false);
                    return;
                }

                if (!PassMtfFilter(signal))
'''
if s.count(gate)!=1: raise SystemExit('CC gate anchor mismatch')
s=s.replace(gate,logic,1)

stop='''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
'''
stop2=stop+'''            Print("[CC-SUMMARY] candidate={0} structuralBlocked={1} regimeBlocked={2} hour15Blocked={3}",
                CCCandidate, _ccBlockedStructural, _ccBlockedRegime, _ccBlockedHour15);
'''
if s.count(stop)!=1: raise SystemExit('CC stop anchor mismatch')
s=s.replace(stop,stop2,1)

old='V29.5-Thesis-Validity-Minimum-Patch-Dev'
if s.count(old)!=1: raise SystemExit('CC version marker mismatch')
s=s.replace(old,'Commercial-Convergence-RC',1)

for token in ['CCCandidate','[CC-ADMISSION]','[CC-SUMMARY]','Commercial-Convergence-RC','V29.3 GRID-RISK-CAP-HOTFIX']:
    if token not in s: raise SystemExit('missing '+token)

p.write_text(s,encoding='utf-8')
print('Applied Commercial Convergence RC edge layer; engineering core unchanged')
