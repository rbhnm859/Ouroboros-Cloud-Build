#!/usr/bin/env python3
from pathlib import Path
p=Path('HarmonyBot-V36/src/HarmonyBotV36.cs')
s=p.read_text()

def rep(old,new):
 global s
 if old not in s: raise SystemExit('patch anchor missing: '+old[:100])
 s=s.replace(old,new,1)

rep('''        [Parameter("Recall Min Confidence", DefaultValue = 0.68, MinValue = 0.55, MaxValue = 0.90)]
        public double RecallMinConfidence { get; set; }
''','''        [Parameter("Recall Min Confidence", DefaultValue = 0.68, MinValue = 0.55, MaxValue = 0.90)]
        public double RecallMinConfidence { get; set; }

        [Parameter("Dynamic Route Re-evaluation", DefaultValue = false)]
        public bool EnableDynamicRouteReevaluation { get; set; }
''')

rep('''        private int _structuredRecallAdmitted;
        private readonly HashSet<string> _deferredCandidates = new HashSet<string>();
''','''        private int _structuredRecallAdmitted;
        private int _routeDeferred;
        private int _routeRecovered;
        private readonly HashSet<string> _deferredCandidates = new HashSet<string>();
''')

rep('''            Print("[V36-FREQUENCY-CONFIG] deferredRetention={0} agingPriority={1} ageBoost={2:F3} structuredRecall={3} recallGeometry={4:F3} recallPrz={5:F3} recallConfidence={6:F3}",
                EnableDeferredCandidateRetention, EnableFrequencyAgingPriority, CandidateAgeRankBoost, EnableStructuredRecallExpansion,
                RecallMinGeometry, RecallMinPrz, RecallMinConfidence);
''','''            Print("[V36-FREQUENCY-CONFIG] deferredRetention={0} agingPriority={1} ageBoost={2:F3} structuredRecall={3} recallGeometry={4:F3} recallPrz={5:F3} recallConfidence={6:F3} dynamicReroute={7}",
                EnableDeferredCandidateRetention, EnableFrequencyAgingPriority, CandidateAgeRankBoost, EnableStructuredRecallExpansion,
                RecallMinGeometry, RecallMinPrz, RecallMinConfidence, EnableDynamicRouteReevaluation);
''')

rep('''            Print("[V36-FREQUENCY-SUMMARY] schedulerDeferred={0} schedulerRecoveredExecutions={1} structuredRecallAdmitted={2} activeDeferred={3}",
                _schedulerDeferred, _schedulerRecoveredExecutions, _structuredRecallAdmitted, _deferredCandidates.Count);
''','''            Print("[V36-FREQUENCY-SUMMARY] schedulerDeferred={0} schedulerRecoveredExecutions={1} structuredRecallAdmitted={2} activeDeferred={3} routeDeferred={4} routeRecovered={5}",
                _schedulerDeferred, _schedulerRecoveredExecutions, _structuredRecallAdmitted, _deferredCandidates.Count, _routeDeferred, _routeRecovered);
''')

rep('''            var regime = BuildRegimeSnapshot();
            var detected = DetectPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback, PortfolioMaxCandidates, "M15");
''','''            var regime = BuildRegimeSnapshot();
            ReevaluateDeferredRoutes(h4State, h1State, regime);
            var detected = DetectPatternCandidates(_m15Bars, i, M15SwingDepth, M15SwingLookback, PortfolioMaxCandidates, "M15");
''')

rep('''                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    if (EnableRegimeContextGate) _regimeRejected++;
                    Reject(record, "ROUTER_NO_TRADE");
                    continue;
                }
''','''                if (record.Route == HarmonicRoute.NO_TRADE)
                {
                    if (EnableRegimeContextGate) _regimeRejected++;
                    if (EnableDynamicRouteReevaluation)
                    {
                        _routeDeferred++;
                        Event(record, "ROUTER_DEFERRED_REEVALUATE");
                    }
                    else
                    {
                        Reject(record, "ROUTER_NO_TRADE");
                    }
                    continue;
                }
''')

anchor='''        private void ProcessNewM1Close()
'''
method='''        private void ReevaluateDeferredRoutes(HarmonicState h4State, HarmonicState h1State, RegimeSnapshot regime)
        {
            if (!EnableDynamicRouteReevaluation) return;
            DateTime now = Server.Time.ToUniversalTime();
            foreach (var c in _candidates.Values.Where(x => x.IsActive && x.State == CandidateState.VALIDATED).ToList())
            {
                if (now >= c.ExpiryUtc) continue;
                if (PatternInvalidatedBeforeEntry(c.Signal)) continue;

                c.Conflict = ClassifyMtfConflict(c.Signal.Direction, h4State, h1State);
                c.Regime = regime;
                c.RegimeScore = RegimeContextScore(c.Signal, c.Conflict, regime);
                c.Route = RouteSignal(c.Signal, c.Conflict, regime);
                if (c.Route == HarmonicRoute.NO_TRADE)
                {
                    Event(c, "ROUTER_REEVALUATE_STILL_NO_TRADE");
                    continue;
                }

                if (EnableCapitalFeasibilityGate)
                {
                    double minL0Risk, minL0Margin;
                    c.CapitalFeasible = CapitalFeasibilityEligible(c, out minL0Risk, out minL0Margin);
                    c.CapitalMinL0Risk = minL0Risk;
                    c.CapitalMinL0Margin = minL0Margin;
                    if (!c.CapitalFeasible) continue;
                }
                else c.CapitalFeasible = true;

                _routeRecovered++;
                Print("[V36-DYNAMIC-REROUTE] cid={0} pattern={1} direction={2} conflict={3} route={4} regime={5:F3}",
                    c.CandidateId, c.Signal.PatternName, c.Signal.Direction, c.Conflict, c.Route, c.RegimeScore);
                Transition(c, CandidateState.ROUTED, "DYNAMIC_ROUTE_" + c.Route);
                CountPipeline(c.Signal.PatternName).Routed++;
                Transition(c, CandidateState.WAIT_PRZ, "WAIT_PRZ_AFTER_DYNAMIC_ROUTE");
                CountPipeline(c.Signal.PatternName).PrzWaiting++;
            }
        }

'''
if anchor not in s: raise SystemExit('method anchor missing')
s=s.replace(anchor,method+anchor,1)
p.write_text(s)
print('dynamic reroute patch applied', len(s))
