from pathlib import Path
import json
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: commercial_rc7_post_transform.py <generated-main.cs>')

out = Path(sys.argv[1]).resolve()
base = out.parent
policy = json.loads(Path('.github/policies/commercial_rc7_policy.json').read_text())
if policy.get('policy_version') != 'RC7A-2026-09-10':
    raise SystemExit('RC7 post-transform policy version mismatch')
if policy.get('candidate_count') != 1:
    raise SystemExit('RC7 must remain a single predeclared candidate')

arb = policy['policy']['arbitration']
ttl_minutes = int(arb['deferred_m30_ttl_minutes'])
max_age_bars = int(arb['deferred_m30_max_age_bars'])
blackout_min = int(arb['deferred_execution_blackout_first_minutes_of_hour'])

main = out.read_text()

old_tick = '''        protected override void OnTick()\n        {\n            Round21ReserveH1Lane();\n            Round15ProcessM30ClosedBar();'''
new_tick = '''        protected override void OnTick()\n        {\n            CommercialTryExecuteDeferredM30();\n            Round15ProcessM30ClosedBar();'''
if old_tick not in main:
    raise SystemExit('RC7 OnTick arbitration anchor missing')
main = main.replace(old_tick, new_tick, 1)

old_limits = '''            if (!PassGlobalLimits())\n            {\n                Reject("global_limits");\n                return;\n            }'''
new_limits = '''            if (!CommercialPassH1PreArbitrationLimits())\n            {\n                Reject("global_limits");\n                return;\n            }'''
if old_limits not in main:
    raise SystemExit('RC7 H1 pre-arbitration limits anchor missing')
main = main.replace(old_limits, new_limits, 1)

old_h1 = '            Round26ExecutionH1(best);'
new_h1 = '''            if (!CommercialArbitrateH1BeforeExecution(best))\n                return;\n            Round26ExecutionH1(best);'''
if old_h1 not in main:
    raise SystemExit('RC7 H1 arbitration execution anchor missing')
main = main.replace(old_h1, new_h1, 1)

old_m30 = '''            if (!Round15PassSharedLimits(lastClosed))\n            {\n                _r15M30BlockedLimits++;\n                if (best != null)\n                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "LIMITS:" + Round18SharedLimitReason(lastClosed));\n                return;\n            }'''
new_m30 = '''            if (!Round15PassSharedLimits(lastClosed))\n            {\n                _r15M30BlockedLimits++;\n                string commercialLimitReason = Round18SharedLimitReason(lastClosed);\n                if (best != null && confirmationPassed && commercialLimitReason == "OPEN_POSITION")\n                    CommercialQueueDeferredM30(best, lastClosed, round21Bypass);\n                if (best != null)\n                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "LIMITS:" + commercialLimitReason);\n                return;\n            }'''
if old_m30 not in main:
    raise SystemExit('RC7 M30 deferred-intent anchor missing')
main = main.replace(old_m30, new_m30, 1)
out.write_text(main)

arbitration = base / 'Commercial.ArbitrationLedger.cs'
arbitration.write_text(f'''using System;\nusing cAlgo.API;\n\nnamespace cAlgo.Robots\n{{\n    public partial class FibonacciHarmonicSniperUltimate\n    {{\n        private sealed class CommercialDeferredM30Intent\n        {{\n            public PatternMatch Match;\n            public int SignalIndex;\n            public bool Round21Bypass;\n            public DateTime EnqueuedUtc;\n            public DateTime ExpiresUtc;\n        }}\n\n        private CommercialDeferredM30Intent _commercialDeferredM30;\n\n        private void CommercialLedger(string evt, string detail)\n        {{\n            Print("[COMMERCIAL LEDGER] event={{0}} time={{1:yyyy-MM-ddTHH:mm:ss}} {{2}}", evt, Server.Time, detail ?? string.Empty);\n        }}\n\n        private bool CommercialPassH1PreArbitrationLimits()\n        {{\n            if (!Growth2Enabled) return PassGlobalLimits();\n            if (_tradesToday >= MaxTradesPerDay) return false;\n            if (Bars.Count - 1 - _lastTradeBar < CooldownBars) return false;\n            if (MaxDailyLossPercent > 0 && _dayStartEquity > 0)\n            {{\n                double dd = 100.0 * (_dayStartEquity - Account.Equity) / _dayStartEquity;\n                if (StoreDailyLossReached(dd)) return false;\n            }}\n            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;\n            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips) return false;\n            double atrPips = _atr.Result.LastValue / Symbol.PipSize;\n            if (MinAtrPips > 0 && atrPips < MinAtrPips) return false;\n            return true;\n        }}\n\n        private bool CommercialArbitrateH1BeforeExecution(PatternMatch best)\n        {{\n            if (!Growth2Enabled) return true;\n            Position blocking = null;\n            foreach (var p in Positions)\n            {{\n                if (p.SymbolName != SymbolName || p.Label != BotLabel) continue;\n                blocking = p;\n                break;\n            }}\n            if (blocking == null) return true;\n\n            string c = blocking.Comment ?? string.Empty;\n            bool m30Satellite = c.StartsWith("M30|", StringComparison.OrdinalIgnoreCase) ||\n                                c.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase);\n            if (!m30Satellite)\n            {{\n                CommercialLedger("H1_BLOCKED_NON_SATELLITE", "pos=" + blocking.Id + " comment=" + c);\n                return false;\n            }}\n\n            CommercialLedger("H1_PREEMPT_M30", "pos=" + blocking.Id + " dir=" + blocking.TradeType +\n                " heldMin=" + Math.Max(0.0, (Server.Time - blocking.EntryTime).TotalMinutes).ToString("F1") +\n                " h1Dir=" + best.Direction + " h1Score=" + best.Score.ToString("F1"));\n            if (!StoreCheckedClose(blocking, "COMMERCIAL_H1_CORE_PRIORITY")) return false;\n            return Round18OwnOpenPositions() < 1;\n        }}\n\n        private void CommercialQueueDeferredM30(PatternMatch m, int signalIndex, bool round21Bypass)\n        {{\n            if (!Growth2Enabled || m == null) return;\n            if (!m.Definition.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase))\n            {{\n                CommercialLedger("SHADOW_ONLY", "pattern=" + m.Definition.Name + " signal=" + m.SignalKey);\n                return;\n            }}\n            if (_r15M30ConsumedSignals.Contains("M30|" + m.SignalKey)) return;\n\n            bool replace = _commercialDeferredM30 == null ||\n                signalIndex > _commercialDeferredM30.SignalIndex ||\n                (signalIndex == _commercialDeferredM30.SignalIndex && m.Score > _commercialDeferredM30.Match.Score);\n            if (!replace)\n            {{\n                CommercialLedger("QUEUE_KEEP", "existing=" + _commercialDeferredM30.Match.SignalKey + " rejected=" + m.SignalKey);\n                return;\n            }}\n\n            string evt = _commercialDeferredM30 == null ? "QUEUE" : "REPLACE";\n            _commercialDeferredM30 = new CommercialDeferredM30Intent\n            {{\n                Match = m,\n                SignalIndex = signalIndex,\n                Round21Bypass = round21Bypass,\n                EnqueuedUtc = Server.Time,\n                ExpiresUtc = Server.Time.AddMinutes({ttl_minutes})\n            }};\n            CommercialLedger(evt, "signal=" + m.SignalKey + " score=" + m.Score.ToString("F1") +\n                " expires=" + _commercialDeferredM30.ExpiresUtc.ToString("yyyy-MM-ddTHH:mm:ss"));\n        }}\n\n        private void CommercialDropDeferred(string reason)\n        {{\n            if (_commercialDeferredM30 != null)\n                CommercialLedger(reason, "signal=" + _commercialDeferredM30.Match.SignalKey);\n            _commercialDeferredM30 = null;\n        }}\n\n        private void CommercialTryExecuteDeferredM30()\n        {{\n            if (!Growth2Enabled || _commercialDeferredM30 == null || _barsM30 == null) return;\n            var d = _commercialDeferredM30;\n            if (Server.Time > d.ExpiresUtc)\n            {{\n                CommercialDropDeferred("EXPIRE");\n                return;\n            }}\n            if (Server.Time.Minute < {blackout_min}) return;\n            if (Round18OwnOpenPositions() >= 1) return;\n\n            int currentLastClosed = _barsM30.Count - 2;\n            if (currentLastClosed < 100) return;\n            if (currentLastClosed - d.SignalIndex > {max_age_bars})\n            {{\n                CommercialDropDeferred("EXPIRE_BARS");\n                return;\n            }}\n            if (_r15M30ConsumedSignals.Contains("M30|" + d.Match.SignalKey))\n            {{\n                CommercialDropDeferred("ALREADY_CONSUMED");\n                return;\n            }}\n\n            double px = d.Match.Direction == TradeType.Buy ? Symbol.Bid : Symbol.Ask;\n            double invalidation = d.Match.Direction == TradeType.Buy\n                ? Math.Min(d.Match.X.Price, d.Match.D.Price)\n                : Math.Max(d.Match.X.Price, d.Match.D.Price);\n            bool invalid = d.Match.Direction == TradeType.Buy ? px <= invalidation : px >= invalidation;\n            if (invalid)\n            {{\n                CommercialDropDeferred("INVALIDATE");\n                return;\n            }}\n\n            d.Match.TrendAligned = Round15M30TrendAligned(d.Match.Direction, currentLastClosed);\n            if (!Round15PassM30Confirmation(d.Match, currentLastClosed))\n            {{\n                CommercialDropDeferred("REVALIDATION_FAIL");\n                return;\n            }}\n            if (!Round15PassSharedLimits(currentLastClosed)) return;\n\n            _commercialDeferredM30 = null;\n            CommercialLedger("DEFERRED_EXECUTE", "signal=" + d.Match.SignalKey +\n                " ageBars=" + (currentLastClosed - d.SignalIndex));\n            Round26ExecutionM30(d.Match, currentLastClosed, d.Round21Bypass);\n        }}\n    }}\n}}\n''')

final_main = out.read_text()
if 'CommercialArbitrateH1BeforeExecution(best)' not in final_main:
    raise SystemExit('RC7 deterministic H1 arbitration missing')
if 'CommercialQueueDeferredM30(best, lastClosed, round21Bypass)' not in final_main:
    raise SystemExit('RC7 deferred M30 queue hook missing')
if 'Round21ReserveH1Lane();' in final_main[final_main.find('protected override void OnTick()'):final_main.find('protected override void OnStop()')]:
    raise SystemExit('RC7 legacy blind H1 reservation still active')
print('Commercial RC7A post-transform applied: deterministic H1 priority + deferred M30 TTL + decision ledger')
