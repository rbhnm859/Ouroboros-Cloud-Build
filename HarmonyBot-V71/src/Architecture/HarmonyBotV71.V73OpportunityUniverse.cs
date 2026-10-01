using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    // V73 research-only opportunity universe. It never replaces the frozen V51
    // detector or capital book. Its only purpose is to measure whether the
    // XAUUSD/M15 harmonic thesis space physically contains enough independent
    // opportunities to support the >=200 closed-basket/year commercial target.
    public partial class HarmonyBotV71
    {
        [Parameter("V73 Opportunity Universe 2", DefaultValue = false)]
        public bool EnableV73OpportunityUniverse2 { get; set; }

        private int _v73UniverseCalls;
        private int _v73UniverseRaw;
        private int _v73UniverseDeduped;

        private List<PatternSignal> V73DetectOpportunityUniverse(Bars bars, int endIndex, int lookback)
        {
            var raw = new List<PatternSignal>();
            if (bars == null || endIndex < 40) return raw;
            double atr = Atr(bars, 14, endIndex);
            if (atr <= 0) return raw;

            // Pre-registered multi-scale research lattice. No PnL/label is used
            // to choose these scales. The frozen V51 detector remains untouched.
            int[] scales = { 2, 3, 4, 5, 6, 8, 10, 12 };
            foreach (int scale in scales)
            {
                var pivots = V71BuildOraclePivots(bars, endIndex, Math.Max(lookback, 480), scale);
                if (pivots.Count < 5) continue;
                for (int dPos = Math.Max(4, pivots.Count - 24); dPos < pivots.Count; dPos++)
                {
                    var d = pivots[dPos];
                    if (endIndex - d.Index > 12) continue;
                    int c0 = Math.Max(3, dPos - 6);
                    for (int cPos = c0; cPos < dPos; cPos++)
                    {
                        if (!V71OracleLegInsideEnvelope(pivots, cPos, dPos)) continue;
                        int b0 = Math.Max(2, cPos - 6);
                        for (int bPos = b0; bPos < cPos; bPos++)
                        {
                            if (!V71OracleLegInsideEnvelope(pivots, bPos, cPos)) continue;
                            int a0 = Math.Max(1, bPos - 6);
                            for (int aPos = a0; aPos < bPos; aPos++)
                            {
                                if (!V71OracleLegInsideEnvelope(pivots, aPos, bPos)) continue;
                                int x0 = Math.Max(0, aPos - 6);
                                for (int xPos = x0; xPos < aPos; xPos++)
                                {
                                    if (dPos - xPos > 24 || !V71OracleLegInsideEnvelope(pivots, xPos, aPos)) continue;
                                    var x = pivots[xPos]; var a = pivots[aPos]; var b = pivots[bPos]; var c = pivots[cPos];
                                    foreach (var profile in _profiles)
                                    {
                                        string reject;
                                        if (!V71ExpansionPrimaryContractPass(profile, x, a, b, c, d, atr, out reject)) continue;
                                        PatternSignal sig;
                                        if (!TryMatchProfile(profile, x, a, b, c, d, atr, bars.OpenTimes[d.Index], "M15", scale, out sig, false)) continue;
                                        if (endIndex - d.Index > Math.Max(2, profile.MaxAgeM15Bars)) continue;
                                        raw.Add(sig);
                                    }
                                }
                            }
                        }
                    }
                }
            }

            _v73UniverseCalls++;
            _v73UniverseRaw += raw.Count;

            // Geometry identity, not pivot scale or PnL, owns a thesis.
            var dedup = raw
                .GroupBy(x => V71FamilyKey(x.PatternName) + "|" + BuildSetupGeometryKey(x))
                .Select(g => g.OrderByDescending(x => x.Confidence)
                              .ThenByDescending(x => x.GeometryQuality)
                              .ThenBy(x => x.PivotScale).First())
                .OrderByDescending(x => x.Confidence)
                .ThenByDescending(x => x.GeometryQuality)
                .ToList();

            foreach (var s in dedup) s.ResearchRole = V71AbcdResearchRole(s, dedup);
            _v73UniverseDeduped += dedup.Count;
            return dedup;
        }

        private void V73PrintOpportunityUniverseSummary()
        {
            if (!EnableV73OpportunityUniverse2) return;
            Print("[V73-OU2-SUMMARY] calls={0} raw={1} deduped={2} duplicateSuppressed={3} scales=2,3,4,5,6,8,10,12 capitalExecution=False labelFree=True",
                _v73UniverseCalls, _v73UniverseRaw, _v73UniverseDeduped,
                Math.Max(0, _v73UniverseRaw - _v73UniverseDeduped));
        }
    }
}
