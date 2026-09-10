from pathlib import Path
import hashlib
import json
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc6_transform.py <store-main.cs> <rc6-main.cs>')

subprocess.run([
    sys.executable,
    '.github/scripts/commercial_rc4_parity_fix.py',
    sys.argv[1],
    sys.argv[2],
], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
policy_path = Path('.github/policies/commercial_rc6_policy.json')
policy = json.loads(policy_path.read_text())
if policy.get('policy_version') != 'RC6A-2026-09-10':
    raise SystemExit('RC6 policy version mismatch')
if policy.get('candidate_count') != 1:
    raise SystemExit('RC6 must remain a single predeclared candidate')

p = policy['policy']
h1_sell_mult = float(p['h1_sell']['risk_multiplier'])
m30_buy_mult = float(p['m30_reciprocal_abcd_buy']['risk_multiplier'])
m30_sell_mult = float(p['m30_reciprocal_abcd_sell']['risk_multiplier'])
for name, value in [('h1_sell', h1_sell_mult), ('m30_buy', m30_buy_mult), ('m30_sell', m30_sell_mult)]:
    if not (0.0 < value <= 1.0):
        raise SystemExit(f'RC6 invalid reduction-only multiplier {name}={value}')
if p['m30_abcd']['decision'] != 'SHADOW' or float(p['m30_abcd']['risk_multiplier']) != 0.0:
    raise SystemExit('RC6 ABCD must default to SHADOW')
if p['growth3']['decision'] != 'SHADOW' or float(p['growth3']['risk_multiplier']) != 0.0:
    raise SystemExit('RC6 Growth3 must remain SHADOW')

main = out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC4', 'BTC-Harmonic-Guard-Commercial-RC6')

def private_method_block(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f'RC6 protected method missing: {marker}')
    nxt = text.find('\n        private ', start + len(marker))
    if nxt < 0:
        raise SystemExit(f'RC6 protected method end missing: {marker}')
    return text[start:nxt]

h1_exec_before = private_method_block(main, '        private void ExecutePatternTrade(PatternMatch m)')
h1_risk_before = private_method_block(main, '        private double Round22CalculateH1Volume(double slPips, TradeType direction)')

old = '''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            if (m.Definition.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase))\n                riskPercent=Math.Min(riskPercent,0.15);\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;\n            var intent = new CommercialTradeIntent("M30", m.Direction, slPips, tpPips, riskPercent,\n                patternName, m.Score, lastClosed, round21Bypass);'''
new = '''            var policyDecision = CommercialEvaluateM30Candidate(m, lastClosed, slPips, tpPips, round21Bypass);\n            CommercialRecordPolicyDecision(policyDecision);\n            if (policyDecision == null || policyDecision.Tier == CommercialPolicyTier.Shadow) return;\n\n            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;\n            var intent = new CommercialTradeIntent("M30", m.Direction, slPips, tpPips, riskPercent,\n                patternName, m.Score, lastClosed, round21Bypass, policyDecision.RiskMultiplier, policyDecision.Tier.ToString());'''
if old not in main:
    raise SystemExit('RC6 M30 policy insertion anchor missing')
main = main.replace(old, new, 1)
out.write_text(main)

signal_policy = base / 'Commercial.SignalPolicy.cs'
signal_policy.write_text(f'''using System;
using cAlgo.API;

namespace cAlgo.Robots
{{
    public partial class FibonacciHarmonicSniperUltimate
    {{
        private enum CommercialPolicyTier {{ LiveCore, LiveSatellite, Shadow }}

        private sealed class CommercialCandidateEnvelope
        {{
            public string CandidateId;
            public DateTime TimestampUtc;
            public string AlphaFamily;
            public string Pattern;
            public TradeType Direction;
            public string Timeframe;
            public double StopLossPips;
            public double TakeProfitPips;
            public double BaseRiskPercent;
            public double Quality;
            public double SpreadPips;
            public double SpreadToStopRatio;
            public int SignalIndex;
            public bool Round21Bypass;
        }}

        private sealed class CommercialPolicyDecision
        {{
            public CommercialCandidateEnvelope Candidate;
            public CommercialPolicyTier Tier;
            public double RiskMultiplier;
            public string Reason;
        }}

        private CommercialPolicyDecision CommercialEvaluateM30Candidate(PatternMatch m, int signalIndex,
            double stopPips, double targetPips, bool round21Bypass)
        {{
            if (m == null) return null;
            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            double baseRisk = round21Bypass ? Round21BypassRiskPercent
                : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
            var c = new CommercialCandidateEnvelope
            {{
                CandidateId = "M30|" + m.SignalKey + "|" + signalIndex,
                TimestampUtc = Server.Time,
                AlphaFamily = "M30",
                Pattern = m.Definition.Name,
                Direction = m.Direction,
                Timeframe = "M30",
                StopLossPips = stopPips,
                TakeProfitPips = targetPips,
                BaseRiskPercent = baseRisk,
                Quality = m.Score,
                SpreadPips = spreadPips,
                SpreadToStopRatio = stopPips > 0 ? spreadPips / stopPips : 999.0,
                SignalIndex = signalIndex,
                Round21Bypass = round21Bypass
            }};

            if (!Growth2Enabled)
                return new CommercialPolicyDecision {{ Candidate = c, Tier = CommercialPolicyTier.LiveCore, RiskMultiplier = 1.0, Reason = "FROZEN_CONTROL" }};

            if (m.Definition.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase))
                return new CommercialPolicyDecision {{ Candidate = c, Tier = CommercialPolicyTier.Shadow, RiskMultiplier = 0.0, Reason = "ABCD_NEGATIVE_CROSS_PERIOD_ATTRIBUTION" }};

            if (!m.Definition.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase))
                return new CommercialPolicyDecision {{ Candidate = c, Tier = CommercialPolicyTier.Shadow, RiskMultiplier = 0.0, Reason = "UNAPPROVED_M30_PATTERN" }};

            double multiplier = m.Direction == TradeType.Buy ? {m30_buy_mult:.8f} : {m30_sell_mult:.8f};
            return new CommercialPolicyDecision
            {{
                Candidate = c,
                Tier = CommercialPolicyTier.LiveSatellite,
                RiskMultiplier = multiplier,
                Reason = m.Direction == TradeType.Buy ? "RECIP_BUY_RISK_ISOLATION" : "RECIP_SELL_RISK_ISOLATION"
            }};
        }}

        private void CommercialRecordPolicyDecision(CommercialPolicyDecision d)
        {{
            if (d == null || d.Candidate == null) return;
            Print("[COMMERCIAL POLICY] id={{0}} alpha={{1}} pattern={{2}} dir={{3}} tier={{4}} mult={{5:F2}} quality={{6:F1}} spreadSL={{7:F4}} reason={{8}}",
                d.Candidate.CandidateId, d.Candidate.AlphaFamily, d.Candidate.Pattern, d.Candidate.Direction,
                d.Tier, d.RiskMultiplier, d.Candidate.Quality, d.Candidate.SpreadToStopRatio, d.Reason);
        }}
    }}
}}
''')

risk_governor = base / 'Commercial.RiskGovernor.cs'
risk_governor.write_text(f'''using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{{
    public partial class FibonacciHarmonicSniperUltimate
    {{
        private double CommercialRiskGovernorFactorV6(CommercialTradeIntent intent)
        {{
            if (intent == null) return 0.0;
            double factor = Math.Max(0.0, Math.Min(1.0, intent.PolicyRiskMultiplier));

            if (intent.Lane == "H1")
            {{
                factor = 1.0;
                if (intent.Direction == TradeType.Sell)
                    factor = Math.Min(factor, {h1_sell_mult:.8f});
            }}

            factor = Math.Min(factor, CommercialLaneHealthFactorV6(intent));
            factor = Math.Min(factor, CommercialPortfolioHealthFactorV6());
            factor = Math.Min(factor, CommercialCostFactorV6(intent));
            return Math.Max(0.0, Math.Min(1.0, factor));
        }}

        private double CommercialLaneHealthFactorV6(CommercialTradeIntent intent)
        {{
            if (intent.Lane == "H1" && intent.Direction == TradeType.Buy) return 1.0;
            var recent = History.FindAll(BotLabel, SymbolName)
                .Where(h => h.TradeType == intent.Direction && CommercialHistoryLaneMatchesV6(h.Comment, intent.Lane))
                .OrderByDescending(h => h.ClosingTime).Take(8).ToArray();
            if (recent.Length < 6) return 1.0;
            double gp = recent.Where(h => h.NetProfit > 0).Sum(h => h.NetProfit);
            double gl = -recent.Where(h => h.NetProfit < 0).Sum(h => h.NetProfit);
            double pf = gl > 0 ? gp / gl : 9.0;
            if (pf < 0.60) return 0.35;
            if (pf < 0.90) return 0.60;
            if (pf < 1.10) return 0.80;
            return 1.0;
        }}

        private double CommercialPortfolioHealthFactorV6()
        {{
            var recent = History.FindAll(BotLabel, SymbolName)
                .OrderByDescending(h => h.ClosingTime).Take(16).ToArray();
            if (recent.Length < 10) return 1.0;
            double gp = recent.Where(h => h.NetProfit > 0).Sum(h => h.NetProfit);
            double gl = -recent.Where(h => h.NetProfit < 0).Sum(h => h.NetProfit);
            double pf = gl > 0 ? gp / gl : 9.0;
            if (pf < 0.65) return 0.45;
            if (pf < 0.90) return 0.65;
            if (pf < 1.10) return 0.80;
            return 1.0;
        }}

        private double CommercialCostFactorV6(CommercialTradeIntent intent)
        {{
            double spreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (!(spreadPips >= 0) || !(intent.StopPips > 0)) return 1.0;
            double ratio = spreadPips / intent.StopPips;
            if (ratio > 0.10) return 0.35;
            if (ratio > 0.06) return 0.55;
            if (ratio > 0.03) return 0.75;
            return 1.0;
        }}

        private bool CommercialHistoryLaneMatchesV6(string comment, string lane)
        {{
            string c = comment ?? string.Empty;
            bool m30 = c.StartsWith("M30|", StringComparison.OrdinalIgnoreCase) || c.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase);
            bool growth = c.StartsWith("GROWTH2|", StringComparison.OrdinalIgnoreCase) || c.StartsWith("GROWTH3|", StringComparison.OrdinalIgnoreCase);
            if (lane == "M30") return m30;
            if (lane == "GROWTH3") return growth;
            return lane == "H1" && !m30 && !growth;
        }}
    }}
}}
''')

commercial = base / 'Commercial.IntentExecution.cs'
commercial.write_text(r'''using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private sealed class CommercialTradeIntent
        {
            public readonly string Lane;
            public readonly TradeType Direction;
            public readonly double StopPips;
            public readonly double TargetPips;
            public readonly double RequestedRiskPercent;
            public readonly string Comment;
            public readonly double Quality;
            public readonly int SignalIndex;
            public readonly bool Round21Bypass;
            public readonly double PolicyRiskMultiplier;
            public readonly string PolicyTier;

            public CommercialTradeIntent(string lane, TradeType direction, double stopPips,
                double targetPips, double requestedRiskPercent, string comment, double quality,
                int signalIndex, bool round21Bypass, double policyRiskMultiplier = 1.0,
                string policyTier = "LIVE_CORE")
            {
                Lane=lane; Direction=direction; StopPips=stopPips; TargetPips=targetPips;
                RequestedRiskPercent=requestedRiskPercent; Comment=comment; Quality=quality;
                SignalIndex=signalIndex; Round21Bypass=round21Bypass;
                PolicyRiskMultiplier=policyRiskMultiplier; PolicyTier=policyTier;
            }
        }

        private sealed class CommercialExecutionReceipt
        {
            public readonly TradeResult Result;
            public readonly double Volume;
            public readonly double RiskPercent;
            public CommercialExecutionReceipt(TradeResult result,double volume,double riskPercent)
            { Result=result; Volume=volume; RiskPercent=riskPercent; }
        }

        private CommercialExecutionReceipt CommercialSubmitIntent(CommercialTradeIntent intent)
        {
            if (intent==null || !TradingEnabled || !StoreCanExecute()) return null;
            if (Round18OwnOpenPositions()>=1) return null;
            if (!(intent.StopPips>0) || !(intent.TargetPips>0)) return null;
            if (intent.TargetPips + 1e-9 < intent.StopPips * MinimumRiskReward) return null;

            double baseVolume=CommercialBaseRiskVolumeV6(intent);
            if (double.IsNaN(baseVolume)||double.IsInfinity(baseVolume)||baseVolume<Symbol.VolumeInUnitsMin) return null;
            double factor=Growth2Enabled ? CommercialRiskGovernorFactorV6(intent) : 1.0;
            if (!(factor>0) || factor>1.0) return null;

            double desired=baseVolume*factor;
            double scaled=Symbol.NormalizeVolumeInUnits(desired,RoundingMode.Down);
            if (scaled<Symbol.VolumeInUnitsMin)
            {
                Print("[COMMERCIAL RISK SHADOW] lane={0} dir={1} reason=BELOW_BROKER_MIN desired={2} min={3}",
                    intent.Lane,intent.Direction,desired,Symbol.VolumeInUnitsMin);
                return null;
            }
            if (scaled>baseVolume) scaled=baseVolume;
            if (scaled>Symbol.VolumeInUnitsMax) scaled=Symbol.VolumeInUnitsMax;

            double baseRisk=Symbol.AmountRisked(baseVolume,intent.StopPips);
            double actualRisk=Symbol.AmountRisked(scaled,intent.StopPips);
            double policyRiskCap=baseRisk*factor;
            if (!(baseRisk>0) || !(actualRisk>0) || double.IsNaN(actualRisk) || double.IsInfinity(actualRisk)
                || actualRisk>policyRiskCap*1.001+1e-8 || actualRisk>baseRisk+1e-8)
            {
                Print("[COMMERCIAL RISK SHADOW] lane={0} dir={1} reason=POST_ROUND_RISK_EXCEEDS_CAP actual={2:F6} cap={3:F6}",
                    intent.Lane,intent.Direction,actualRisk,policyRiskCap);
                return null;
            }

            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,scaled,BotLabel,
                intent.StopPips,intent.TargetPips,intent.Comment,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[COMMERCIAL ORDER FAIL] lane={0} dir={1} error={2}",intent.Lane,intent.Direction,result.Error);
                return new CommercialExecutionReceipt(result,scaled,intent.RequestedRiskPercent*factor);
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[COMMERCIAL PROTECTION FAIL] lane={0} pos={1}",intent.Lane,result.Position.Id);
                StoreEmergencyClose(result.Position,intent.Lane+"_PROTECTION_FAIL");
                return null;
            }
            Print("[COMMERCIAL RISK] lane={0} dir={1} tier={2} quality={3:F1} factor={4:F2} baseVol={5} liveVol={6} baseRisk={7:F4} liveRisk={8:F4}",
                intent.Lane,intent.Direction,intent.PolicyTier,intent.Quality,factor,baseVolume,scaled,baseRisk,actualRisk);
            return new CommercialExecutionReceipt(result,scaled,intent.RequestedRiskPercent*factor);
        }

        private double CommercialBaseRiskVolumeV6(CommercialTradeIntent intent)
        {
            if (intent.Lane=="H1") return Round22CalculateH1Volume(intent.StopPips,intent.Direction);
            if (intent.Lane=="M30") return Round21CalculateM30Volume(intent.StopPips,intent.RequestedRiskPercent);
            return 0;
        }
    }
}
''')

final_main = out.read_text()
if private_method_block(final_main, '        private void ExecutePatternTrade(PatternMatch m)') != h1_exec_before:
    raise SystemExit('RC6 H1 alpha/entry source drift detected')
if private_method_block(final_main, '        private double Round22CalculateH1Volume(double slPips, TradeType direction)') != h1_risk_before:
    raise SystemExit('RC6 H1 base-risk source drift detected')

src = Path(sys.argv[1]).resolve()
compile_cs = [x for x in base.glob('*.cs') if x.resolve() != src]
direct = sum(x.read_text().count('ExecuteMarketOrder(') for x in compile_cs)
central_count = commercial.read_text().count('ExecuteMarketOrder(')
if direct != 1 or central_count != 1 or final_main.count('ExecuteMarketOrder(') != 0:
    raise SystemExit(f'RC6 execution invariant failed direct={direct} central={central_count}')
if 'if (!Growth2Enabled)' not in final_main:
    raise SystemExit('RC6 frozen-control M30 isolation missing')
if 'Growth2Enabled ? CommercialRiskGovernorFactorV6(intent) : 1.0' not in commercial.read_text():
    raise SystemExit('RC6 frozen-control governor bypass missing')
if '[GROWTH3 SHADOW]' not in (base / 'Growth3.Architecture.cs').read_text():
    raise SystemExit('RC6 Growth3 shadow isolation missing')
if 'ABCD_NEGATIVE_CROSS_PERIOD_ATTRIBUTION' not in signal_policy.read_text():
    raise SystemExit('RC6 ABCD default quarantine missing')
if 'scaled=Symbol.VolumeInUnitsMin' in commercial.read_text():
    raise SystemExit('RC6 forbidden broker-min round-up path detected')

policy_sha = hashlib.sha256(policy_path.read_bytes()).hexdigest()
print('Commercial RC6A generated: deterministic Candidate->Policy->Risk->Execution; control parity isolated; one live order boundary')
print('RC6 policy sha256:', policy_sha)
