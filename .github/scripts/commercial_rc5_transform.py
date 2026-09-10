from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc5_transform.py <store-main.cs> <rc5-main.cs>')

# RC5 starts from RC4 with the frozen-control parity fix already applied.
# Candidate-only changes are deliberately narrow:
#   1) prune the empirically toxic M30 ABCD 95<=score<100 band,
#   2) normalize excessive-RR tails instead of deleting otherwise valid signals,
#   3) reduce exposure to weak M30 Reciprocal-ABCD buys,
#   4) let H1 Buy participate in reduction-only realized-health governance,
#   5) add a slower restart-safe portfolio health layer for prolonged weak regimes.
subprocess.run([sys.executable, '.github/scripts/commercial_rc4_parity_fix.py', sys.argv[1], sys.argv[2]], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
main = out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC4', 'BTC-Harmonic-Guard-Commercial-RC5')

old = '''        private void ExecutePatternTrade(PatternMatch m)
        {
            Round10Count("execute_attempt", m.Direction);'''
new = '''        private void ExecutePatternTrade(PatternMatch m)
        {
            if (Growth2Enabled && m.Direction == TradeType.Sell && m.Score >= 90.0 && m.Score < 95.0)
            {
                Reject("rc5_h1_sell_midscore");
                return;
            }
            Round10Count("execute_attempt", m.Direction);'''
if old not in main:
    raise SystemExit('RC5 H1 admission anchor missing')
main = main.replace(old, new, 1)

old = '''            if (tpPips < slPips * MinimumRiskReward)
            {
                Reject("target_rr_too_low");
                return;
            }
            double requestedRiskPercent = m.Direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;'''
new = '''            if (tpPips < slPips * MinimumRiskReward)
            {
                Reject("target_rr_too_low");
                return;
            }
            if (Growth2Enabled && tpPips > slPips * 1.80)
                tpPips = slPips * 1.80;
            double requestedRiskPercent = m.Direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;'''
if old not in main:
    raise SystemExit('RC5 H1 RR-cap anchor missing')
main = main.replace(old, new, 1)

old = '''                    double score=def.Score(xb,ac,bd,xd,cdAb,6.0);
                    if (score<84.0) continue;
                    var match=new PatternMatch(def,direction.Value,x,a,b,c,d,score,xb,ac,bd,xd,cdAb);'''
new = '''                    double score=def.Score(xb,ac,bd,xd,cdAb,6.0);
                    if (score<84.0) continue;
                    if (Growth2Enabled && def.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase) &&
                        score >= 95.0 && score < 100.0) continue;
                    var match=new PatternMatch(def,direction.Value,x,a,b,c,d,score,xb,ac,bd,xd,cdAb);'''
if old not in main:
    raise SystemExit('RC5 M30 score-band anchor missing')
main = main.replace(old, new, 1)

old = '''            if (tpPips<slPips*MinimumRiskReward) return;
            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);'''
new = '''            if (tpPips<slPips*MinimumRiskReward) return;
            if (Growth2Enabled && m.Definition.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase) &&
                m.Direction == TradeType.Buy && tpPips > slPips * 1.80)
                tpPips = slPips * 1.80;
            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);'''
if old not in main:
    raise SystemExit('RC5 M30 RR-cap anchor missing')
main = main.replace(old, new, 1)

out.write_text(main)

commercial = base / 'Commercial.IntentExecution.cs'
c = commercial.read_text()

old = '''            if (intent.Lane=="H1" && intent.Direction==TradeType.Sell && intent.Quality>=90.0 && intent.Quality<95.0)
                factor=Math.Min(factor,0.35);
            if (intent.Lane=="M30")
            {
                if ((intent.Comment??string.Empty).EndsWith("|ABCD",StringComparison.OrdinalIgnoreCase))
                    factor=Math.Min(factor,0.35);
                else if (intent.Quality>=90.0 && intent.Quality<95.0)
                    factor=Math.Min(factor,0.30);
                else if (intent.Quality>=97.5)
                    factor=Math.Min(factor,0.75);
            }

            factor=Math.Min(factor,CommercialLaneHealthFactor(intent));
            factor=Math.Min(factor,CommercialPortfolioHealthFactor());
            factor=Math.Min(factor,CommercialCostFactor(intent));'''
new = '''            if (intent.Lane=="M30")
            {
                string comment=intent.Comment??string.Empty;
                if (comment.EndsWith("|ABCD",StringComparison.OrdinalIgnoreCase))
                    factor=Math.Min(factor,0.35);
                else if (intent.Direction==TradeType.Buy &&
                         comment.EndsWith("|Reciprocal ABCD",StringComparison.OrdinalIgnoreCase))
                    factor=Math.Min(factor,0.35);
                else if (intent.Quality>=90.0 && intent.Quality<95.0)
                    factor=Math.Min(factor,0.30);
                else if (intent.Quality>=97.5)
                    factor=Math.Min(factor,0.75);
            }

            factor=Math.Min(factor,CommercialLaneHealthFactor(intent));
            factor=Math.Min(factor,CommercialPortfolioHealthFactor());
            factor=Math.Min(factor,CommercialSlowPortfolioHealthFactor());
            factor=Math.Min(factor,CommercialCostFactor(intent));'''
if old not in c:
    raise SystemExit('RC5 governor anchor missing')
c = c.replace(old, new, 1)

old = '''            // H1 Buy remains the frozen core and is governed only by portfolio/cost safety.
            if (intent.Lane=="H1" && intent.Direction==TradeType.Buy) return 1.0;
            var recent=History.FindAll(BotLabel,SymbolName)'''
new = '''            // H1 alpha remains unchanged. RC5 only allows realized lane health
            // to reduce (never increase) H1 Buy risk during sustained weak regimes.
            var recent=History.FindAll(BotLabel,SymbolName)'''
if old not in c:
    raise SystemExit('RC5 H1 health anchor missing')
c = c.replace(old, new, 1)

old = '''        private double CommercialCostFactor(CommercialTradeIntent intent)
        {'''
new = '''        private double CommercialSlowPortfolioHealthFactor()
        {
            var recent=History.FindAll(BotLabel,SymbolName)
                .OrderByDescending(h=>h.ClosingTime).Take(32).ToArray();
            if (recent.Length<16) return 1.0;
            double gp=recent.Where(h=>h.NetProfit>0).Sum(h=>h.NetProfit);
            double gl=-recent.Where(h=>h.NetProfit<0).Sum(h=>h.NetProfit);
            double pf=gl>0 ? gp/gl : 9.0;
            if (pf<0.80) return 0.25;
            if (pf<1.00) return 0.45;
            if (pf<1.15) return 0.70;
            return 1.0;
        }

        private double CommercialCostFactor(CommercialTradeIntent intent)
        {'''
if old not in c:
    raise SystemExit('RC5 slow-health anchor missing')
c = c.replace(old, new, 1)
commercial.write_text(c)

src = Path(sys.argv[1]).resolve()
cs = [p for p in base.glob('*.cs') if p.resolve() != src]
direct = sum(p.read_text().count('ExecuteMarketOrder(') for p in cs)
central = commercial.read_text().count('ExecuteMarketOrder(')
generated = out.read_text()
if direct != 1 or central != 1 or generated.count('ExecuteMarketOrder(') != 0:
    raise SystemExit(f'RC5 structural invariant failed direct={direct} central={central}')
required = [
    'rc5_h1_sell_midscore',
    'score >= 95.0 && score < 100.0',
    'CommercialSlowPortfolioHealthFactor()',
    'intent.Direction==TradeType.Buy',
]
all_text = generated + '\n' + commercial.read_text()
for token in required:
    if token not in all_text:
        raise SystemExit('RC5 required token missing: '+token)

print('Commercial RC5 generated: selective quality whitelist + RR normalization + reduction-only lane/slow portfolio governance; direct orders=1')
