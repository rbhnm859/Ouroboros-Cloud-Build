from pathlib import Path
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

needle='''        [Parameter("Reversal Trend Score Floor", DefaultValue = 0.45, MinValue = 0.0, MaxValue = 0.80)]\n        public double ReversalTrendScoreFloor { get; set; }\n'''
insert=needle+'''\n        [Parameter("Commission / $1M / side", DefaultValue = 35.0, MinValue = 0.0, MaxValue = 200.0)]\n        public double CommissionPerMillionPerSide { get; set; }\n'''
if needle not in s: raise SystemExit('commission parameter point missing')
s=s.replace(needle,insert,1)

old='''            if (tpPips < slPips * MinRR)\n                tpPips = slPips * MinRR;\n\n            if (tpPips < EffectiveMinTakeProfitPips()) return false;\n\n            TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n            if (!HasMinDistanceFromMarket(tt, sl, MinStopDistancePips)) return false;\n\n            if (UseCostAdjustedRR)\n            {\n                double spreadPips = PriceToPips(_symbol.Ask - _symbol.Bid);\n                if (spreadPips > 0)\n                {\n                    double netRR = (tpPips - spreadPips) / slPips;\n                    if (netRR < MinRR) return false;\n                }\n            }\n\n            return true;\n'''
new='''            double requiredTpPips = slPips * MinRR;\n            if (UseCostAdjustedRR)\n            {\n                double spreadPips = Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid));\n                double commissionPips = EstimateRoundTurnCommissionPips();\n                requiredTpPips += spreadPips + commissionPips;\n            }\n\n            // v28: reprice instead of reject. The old flow first set TP=MinRR and then\n            // subtracted spread, making the same signal fail the very next check.\n            if (tpPips < requiredTpPips)\n                tpPips = requiredTpPips;\n\n            if (tpPips < EffectiveMinTakeProfitPips())\n                tpPips = EffectiveMinTakeProfitPips();\n\n            TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n            if (!HasMinDistanceFromMarket(tt, sl, MinStopDistancePips)) return false;\n\n            return true;\n'''
if old not in s: raise SystemExit('cost adjusted RR block missing')
s=s.replace(old,new,1)

marker='''        private bool PassMtfFilter(Signal signal)\n'''
helper='''        private double EstimateRoundTurnCommissionPips()\n        {\n            if (CommissionPerMillionPerSide <= 0 || _symbol == null || _symbol.PipValue <= 0) return 0;\n            double price = (_symbol.Ask > 0 && _symbol.Bid > 0) ? (_symbol.Ask + _symbol.Bid) * 0.5 : Math.Max(_symbol.Ask, _symbol.Bid);\n            if (price <= 0) return 0;\n            double roundTurnCostPerUnit = 2.0 * CommissionPerMillionPerSide * price / 1000000.0;\n            double pips = roundTurnCostPerUnit / _symbol.PipValue;\n            return double.IsNaN(pips) || double.IsInfinity(pips) ? 0 : Math.Max(0.0, pips);\n        }\n\n'''
if marker not in s: raise SystemExit('cost helper marker missing')
s=s.replace(marker,helper+marker,1)

p.write_text(s,encoding='utf-8')
print('Applied v28 cost-adjusted RR repricing fix')

# Finish the v28 chain with release-audit hardening and canonical pattern
# integrity corrections. These are mandatory for the commercial candidate.
for patch_name in ['fix_v28_release_audit.py', 'fix_v28_pattern_integrity.py']:
    patch = Path('tmp/harmonybot-v26-build') / patch_name
    if not patch.exists():
        raise SystemExit('v28 mandatory patch missing: ' + patch_name)
    exec(compile(patch.read_text(encoding='utf-8'), str(patch), 'exec'), {})
