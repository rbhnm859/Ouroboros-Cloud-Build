#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc7_transform.py <store-main.cs> <rc7-main.cs>')

subprocess.run([
    sys.executable,
    '.github/scripts/commercial_rc6_transform.py',
    sys.argv[1],
    sys.argv[2],
], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
policy_path = Path('.github/policies/commercial_rc7_policy.json')
policy = json.loads(policy_path.read_text())
if policy.get('policy_version') != 'RC7A-2026-09-10':
    raise SystemExit('RC7 policy version mismatch')
if policy.get('candidate_count') != 1:
    raise SystemExit('RC7 must remain a single predeclared candidate')

p = policy['policy']
h1_sell = float(p['h1_sell']['risk_multiplier'])
m30_buy = float(p['m30_reciprocal_abcd_buy']['risk_multiplier'])
m30_sell = float(p['m30_reciprocal_abcd_sell']['risk_multiplier'])
if not (0.0 < h1_sell <= 0.35):
    raise SystemExit('RC7 H1 Sell must be down-only relative to RC6')
if not (0.0 < m30_buy <= 0.35):
    raise SystemExit('RC7 M30 Buy must be down-only relative to RC6')
if not (0.0 < m30_sell <= 0.75):
    raise SystemExit('RC7 M30 Sell must be down-only relative to RC6')
if p['m30_abcd']['decision'] != 'SHADOW' or float(p['m30_abcd']['risk_multiplier']) != 0.0:
    raise SystemExit('RC7 ABCD must remain SHADOW')
if p['growth3']['decision'] != 'SHADOW' or float(p['growth3']['risk_multiplier']) != 0.0:
    raise SystemExit('RC7 Growth3 must remain SHADOW')

arch = policy['architecture']
deferred = arch['m30_deferred_intent']
ttl_bars = int(deferred['ttl_m30_bars'])
if not deferred.get('enabled') or deferred.get('pattern') != 'Reciprocal ABCD':
    raise SystemExit('RC7 deferred intent must be Reciprocal ABCD only')
if deferred.get('eligible_block_reason') != 'OPEN_POSITION':
    raise SystemExit('RC7 deferred intent may only recover OPEN_POSITION path conflicts')
if deferred.get('round21_bypass_deferred'):
    raise SystemExit('RC7 may not defer Round21 bypass candidates')
if ttl_bars != 4:
    raise SystemExit('RC7 TTL is predeclared at four M30 bars')

main = out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC6', 'BTC-Harmonic-Guard-Commercial-RC7')
risk_path = base / 'Commercial.RiskGovernor.cs'
signal_path = base / 'Commercial.SignalPolicy.cs'
execution_path = base / 'Commercial.IntentExecution.cs'
risk = risk_path.read_text()
signal = signal_path.read_text()
execution = execution_path.read_text()

old_h1 = 'factor = Math.Min(factor, 0.35000000);'
new_h1 = f'factor = Math.Min(factor, {h1_sell:.8f});'
if old_h1 not in risk:
    raise SystemExit('RC7 H1 Sell reduction anchor missing')
risk = risk.replace(old_h1, new_h1, 1)

old_m30 = 'double multiplier = m.Direction == TradeType.Buy ? 0.35000000 : 0.75000000;'
new_m30 = f'double multiplier = m.Direction == TradeType.Buy ? {m30_buy:.8f} : {m30_sell:.8f};'
if old_m30 not in signal:
    raise SystemExit('RC7 M30 policy reduction anchor missing')
signal = signal.replace(old_m30, new_m30, 1)

def private_method_block(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f'RC7 protected method missing: {marker}')
    nxt = text.find('\n        private ', start + len(marker))
    if nxt < 0:
        raise SystemExit(f'RC7 protected method end missing: {marker}')
    return text[start:nxt]

h1_before = private_method_block(main, '        private void ExecutePatternTrade(PatternMatch m)')
h1_risk_before = private_method_block(main, '        private double Round22CalculateH1Volume(double slPips, TradeType direction)')

old_reset = '''            if (Server.Time.Date != _day)
                ResetDay();

            // R18 diagnostics: detect the actual M30 candidate before execution gates.'''
new_reset = '''            if (Server.Time.Date != _day)
                ResetDay();

            if (Growth2Enabled)
            {
                CommercialUpdateM30ShadowLedger(lastClosed);
                if (CommercialTryExecuteDeferredM30(lastClosed))
                    return;
            }

            // R18 diagnostics: detect the actual M30 candidate before execution gates.'''
if old_reset not in main:
    raise SystemExit('RC7 M30 orchestration anchor missing')
main = main.replace(old_reset, new_reset, 1)

old_limits = '''            if (!Round15PassSharedLimits(lastClosed))
            {
                _r15M30BlockedLimits++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "LIMITS:" + Round18SharedLimitReason(lastClosed));
                return;
            }'''
new_limits = '''            if (!Round15PassSharedLimits(lastClosed))
            {
                _r15M30BlockedLimits++;
                string sharedLimitReason = Round18SharedLimitReason(lastClosed);
                if (best != null)
                {
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "LIMITS:" + sharedLimitReason);
                    if (Growth2Enabled && sharedLimitReason == "OPEN_POSITION" && confirmationPassed && !round21Bypass)
                        CommercialConsiderDeferredM30(best, lastClosed);
                }
                return;
            }'''
if old_limits not in main:
    raise SystemExit('RC7 M30 deferred capture anchor missing')
main = main.replace(old_limits, new_limits, 1)

old_policy = '''            var policyDecision = CommercialEvaluateM30Candidate(m, lastClosed, slPips, tpPips, round21Bypass);
            CommercialRecordPolicyDecision(policyDecision);
            if (policyDecision == null || policyDecision.Tier == CommercialPolicyTier.Shadow) return;

            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;'''
new_policy = '''            var policyDecision = CommercialEvaluateM30Candidate(m, lastClosed, slPips, tpPips, round21Bypass);
            CommercialRecordPolicyDecision(policyDecision);
            if (policyDecision == null) return;
            if (policyDecision.Tier == CommercialPolicyTier.Shadow)
            {
                CommercialTrackM30Shadow(policyDecision, m.SignalKey, lastClosed, entry, slPips, tpPips);
                return;
            }

            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name+(_commercialExecutingDeferredM30 ? "|DEFERRED" : "");'''
if old_policy not in main:
    raise SystemExit('RC7 shadow ledger anchor missing')
main = main.replace(old_policy, new_policy, 1)

submit_count = main.count('var receipt = CommercialSubmitIntent(intent);')
if submit_count != 2:
    raise SystemExit(f'RC7 expected two main submit call sites, found {submit_count}')
main = main.replace('var receipt = CommercialSubmitIntent(intent);',
                    'var receipt = CommercialPortfolioRouteIntent(intent);')

portfolio = base / 'Commercial.PortfolioDecision.cs'
portfolio.write_text(f'''using System;
using cAlgo.API;

namespace cAlgo.Robots
{{
    public partial class FibonacciHarmonicSniperUltimate
    {{
        private sealed class CommercialDeferredM30Intent
        {{
            public PatternMatch Match;
            public int OriginIndex;
            public int ExpiryIndex;
            public double PriorityScore;
            public string SignalKey;
            public DateTime CreatedUtc;
        }}

        private CommercialDeferredM30Intent _commercialDeferredM30;
        private bool _commercialExecutingDeferredM30;

        private CommercialExecutionReceipt CommercialPortfolioRouteIntent(CommercialTradeIntent intent)
        {{
            if (intent == null) return null;
            if (!Growth2Enabled)
                return CommercialSubmitIntent(intent);

            if (intent.Lane == "H1")
                Print("[COMMERCIAL DECISION] action=LIVE_NOW priority=H1 dir={{0}} quality={{1:F1}}", intent.Direction, intent.Quality);
            else
                Print("[COMMERCIAL DECISION] action=LIVE_NOW priority=M30 dir={{0}} quality={{1:F1}}", intent.Direction, intent.Quality);
            return CommercialSubmitIntent(intent);
        }}

        private void CommercialConsiderDeferredM30(PatternMatch m, int lastClosed)
        {{
            if (!Growth2Enabled || m == null) return;
            if (!m.Definition.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase)) return;
            string key = "M30|" + m.SignalKey;
            if (_r15M30ConsumedSignals.Contains(key)) return;

            double priority = m.FinalScore;
            if (_commercialDeferredM30 != null)
            {{
                if (_commercialDeferredM30.SignalKey == key) return;
                if (priority <= _commercialDeferredM30.PriorityScore + 1e-9)
                {{
                    Print("[COMMERCIAL DECISION] action=DROP_DEFERRED_NEW reason=LOWER_PRIORITY key={{0}} score={{1:F1}} kept={{2:F1}}",
                        key, priority, _commercialDeferredM30.PriorityScore);
                    return;
                }}
                Print("[COMMERCIAL DECISION] action=REPLACE_DEFERRED old={{0}} new={{1}} oldScore={{2:F1}} newScore={{3:F1}}",
                    _commercialDeferredM30.SignalKey, key, _commercialDeferredM30.PriorityScore, priority);
            }}

            _commercialDeferredM30 = new CommercialDeferredM30Intent
            {{
                Match = m,
                OriginIndex = lastClosed,
                ExpiryIndex = lastClosed + {ttl_bars},
                PriorityScore = priority,
                SignalKey = key,
                CreatedUtc = Server.Time
            }};
            Print("[COMMERCIAL DECISION] action=DEFER lane=M30 pattern=Reciprocal_ABCD dir={{0}} score={{1:F1}} origin={{2}} expiry={{3}} reason=OPEN_POSITION",
                m.Direction, m.Score, lastClosed, lastClosed + {ttl_bars});
        }}

        private bool CommercialTryExecuteDeferredM30(int currentLastClosed)
        {{
            if (!Growth2Enabled || _commercialDeferredM30 == null) return false;
            var d = _commercialDeferredM30;
            if (currentLastClosed > d.ExpiryIndex)
            {{
                Print("[COMMERCIAL DECISION] action=EXPIRE_DEFERRED key={{0}} ageBars={{1}}", d.SignalKey, currentLastClosed - d.OriginIndex);
                _commercialDeferredM30 = null;
                return false;
            }}
            if (_r15M30ConsumedSignals.Contains(d.SignalKey))
            {{
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=ALREADY_CONSUMED", d.SignalKey);
                _commercialDeferredM30 = null;
                return false;
            }}
            if (Round18OwnOpenPositions() >= MaxOpenPositions)
                return false;

            if (!Round16H1HealthAllowsM30())
            {{
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=H1_HEALTH", d.SignalKey);
                _commercialDeferredM30 = null;
                return false;
            }}
            if (!Round15PassSharedLimits(currentLastClosed))
            {{
                string reason = Round18SharedLimitReason(currentLastClosed);
                if (reason == "OPEN_POSITION") return false;
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=LIMIT_{{1}}", d.SignalKey, reason);
                _commercialDeferredM30 = null;
                return false;
            }}
            if (!Round15M30TrendAligned(d.Match.Direction, currentLastClosed))
            {{
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=TREND_REVALIDATION", d.SignalKey);
                _commercialDeferredM30 = null;
                return false;
            }}
            if (!Round15PassM30Confirmation(d.Match, currentLastClosed))
            {{
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=CONFIRMATION_REVALIDATION", d.SignalKey);
                _commercialDeferredM30 = null;
                return false;
            }}

            _commercialDeferredM30 = null;
            int before = _r15M30Opened;
            _commercialExecutingDeferredM30 = true;
            try
            {{
                Print("[COMMERCIAL DECISION] action=EXECUTE_DEFERRED key={{0}} ageBars={{1}}", d.SignalKey, currentLastClosed - d.OriginIndex);
                Round15ExecuteM30(d.Match, currentLastClosed, false);
            }}
            finally
            {{
                _commercialExecutingDeferredM30 = false;
            }}
            bool opened = _r15M30Opened > before;
            if (!opened)
                Print("[COMMERCIAL DECISION] action=DROP_DEFERRED key={{0}} reason=EXECUTION_REJECTED", d.SignalKey);
            return opened;
        }}
    }}
}}
''')

shadow = base / 'Commercial.ShadowLedger.cs'
shadow.write_text(f'''using System;
using System.Collections.Generic;
using cAlgo.API;

namespace cAlgo.Robots
{{
    public partial class FibonacciHarmonicSniperUltimate
    {{
        private sealed class CommercialM30ShadowObservation
        {{
            public string Id;
            public string SignalKey;
            public TradeType Direction;
            public int OriginIndex;
            public int ExpiryIndex;
            public double Entry;
            public double StopPips;
            public double TargetPips;
            public string Pattern;
        }}

        private readonly List<CommercialM30ShadowObservation> _commercialM30Shadows = new List<CommercialM30ShadowObservation>();
        private readonly HashSet<string> _commercialM30ShadowSeen = new HashSet<string>(StringComparer.Ordinal);

        private void CommercialTrackM30Shadow(CommercialPolicyDecision decision, string signalKey, int signalIndex,
            double entry, double stopPips, double targetPips)
        {{
            if (!Growth2Enabled || decision == null || decision.Candidate == null) return;
            string dedup = decision.Candidate.Pattern + "|" + signalKey;
            if (_commercialM30ShadowSeen.Contains(dedup)) return;
            _commercialM30ShadowSeen.Add(dedup);
            _commercialM30Shadows.Add(new CommercialM30ShadowObservation
            {{
                Id = decision.Candidate.CandidateId,
                SignalKey = signalKey,
                Direction = decision.Candidate.Direction,
                OriginIndex = signalIndex,
                ExpiryIndex = signalIndex + {ttl_bars},
                Entry = entry,
                StopPips = stopPips,
                TargetPips = targetPips,
                Pattern = decision.Candidate.Pattern
            }});
            Print("[COMMERCIAL COUNTERFACTUAL] action=START id={{0}} pattern={{1}} dir={{2}} horizonBars={ttl_bars} sl={{3:F1}} tp={{4:F1}}",
                decision.Candidate.CandidateId, decision.Candidate.Pattern, decision.Candidate.Direction, stopPips, targetPips);
        }}

        private void CommercialUpdateM30ShadowLedger(int lastClosed)
        {{
            if (!Growth2Enabled || _commercialM30Shadows.Count == 0 || _barsM30 == null) return;
            for (int i = _commercialM30Shadows.Count - 1; i >= 0; i--)
            {{
                var s = _commercialM30Shadows[i];
                if (lastClosed <= s.OriginIndex) continue;
                double high = _barsM30.HighPrices[lastClosed];
                double low = _barsM30.LowPrices[lastClosed];
                double slPrice = s.Direction == TradeType.Buy
                    ? s.Entry - s.StopPips * Symbol.PipSize
                    : s.Entry + s.StopPips * Symbol.PipSize;
                double tpPrice = s.Direction == TradeType.Buy
                    ? s.Entry + s.TargetPips * Symbol.PipSize
                    : s.Entry - s.TargetPips * Symbol.PipSize;
                bool slHit = s.Direction == TradeType.Buy ? low <= slPrice : high >= slPrice;
                bool tpHit = s.Direction == TradeType.Buy ? high >= tpPrice : low <= tpPrice;

                if (slHit && tpHit)
                {{
                    Print("[COMMERCIAL COUNTERFACTUAL] action=RESOLVE id={{0}} outcome=AMBIGUOUS bars={{1}}", s.Id, lastClosed - s.OriginIndex);
                    _commercialM30Shadows.RemoveAt(i);
                }}
                else if (tpHit)
                {{
                    Print("[COMMERCIAL COUNTERFACTUAL] action=RESOLVE id={{0}} outcome=TP bars={{1}}", s.Id, lastClosed - s.OriginIndex);
                    _commercialM30Shadows.RemoveAt(i);
                }}
                else if (slHit)
                {{
                    Print("[COMMERCIAL COUNTERFACTUAL] action=RESOLVE id={{0}} outcome=SL bars={{1}}", s.Id, lastClosed - s.OriginIndex);
                    _commercialM30Shadows.RemoveAt(i);
                }}
                else if (lastClosed >= s.ExpiryIndex)
                {{
                    double mark = _barsM30.ClosePrices[lastClosed];
                    double signedPips = (s.Direction == TradeType.Buy ? mark - s.Entry : s.Entry - mark) / Symbol.PipSize;
                    Print("[COMMERCIAL COUNTERFACTUAL] action=RESOLVE id={{0}} outcome=EXPIRE bars={{1}} markPips={{2:F1}}",
                        s.Id, lastClosed - s.OriginIndex, signedPips);
                    _commercialM30Shadows.RemoveAt(i);
                }}
            }}
        }}
    }}
}}
''')

risk_path.write_text(risk)
signal_path.write_text(signal)
execution_path.write_text(execution)
out.write_text(main)

h1_after = private_method_block(main, '        private void ExecutePatternTrade(PatternMatch m)')
if h1_after.replace('CommercialPortfolioRouteIntent(intent)', 'CommercialSubmitIntent(intent)') != h1_before:
    raise SystemExit('RC7 H1 alpha drift detected beyond portfolio routing')
if private_method_block(main, '        private double Round22CalculateH1Volume(double slPips, TradeType direction)') != h1_risk_before:
    raise SystemExit('RC7 H1 base-risk source drift detected')

src = Path(sys.argv[1]).resolve()
compile_cs = [x for x in base.glob('*.cs') if x.resolve() != src]
direct = sum(x.read_text().count('ExecuteMarketOrder(') for x in compile_cs)
central = execution_path.read_text().count('ExecuteMarketOrder(')
if direct != 1 or central != 1 or main.count('ExecuteMarketOrder(') != 0:
    raise SystemExit(f'RC7 execution invariant failed direct={direct} central={central}')
if main.count('CommercialPortfolioRouteIntent(intent)') != 2:
    raise SystemExit('RC7 portfolio routing invariant failed')
if 'CommercialConsiderDeferredM30(best, lastClosed)' not in main:
    raise SystemExit('RC7 deferred capture missing')
if 'CommercialTryExecuteDeferredM30(lastClosed)' not in main:
    raise SystemExit('RC7 deferred arbitration missing')
if '|DEFERRED' not in main:
    raise SystemExit('RC7 deferred attribution marker missing')
if 'ABCD_NEGATIVE_CROSS_PERIOD_ATTRIBUTION' not in signal_path.read_text():
    raise SystemExit('RC7 ABCD quarantine drifted')
if '[GROWTH3 SHADOW]' not in (base / 'Growth3.Architecture.cs').read_text():
    raise SystemExit('RC7 Growth3 shadow drifted')
if 'ExecuteMarketOrder(' in shadow.read_text() or 'ExecuteMarketOrder(' in portfolio.read_text():
    raise SystemExit('RC7 auxiliary architecture may not place direct orders')
if 'scaled=Symbol.VolumeInUnitsMin' in execution_path.read_text():
    raise SystemExit('RC7 forbidden broker-min risk round-up path detected')

policy_sha = hashlib.sha256(policy_path.read_bytes()).hexdigest()
print('Commercial RC7A generated: deterministic Portfolio Decision + M30 deferred TTL + counterfactual ledger + down-only exposure calibration')
print('RC7 policy sha256:', policy_sha)
