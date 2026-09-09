from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: round27_transform.py <round26-dir> <round27-dir>")

srcdir = Path(sys.argv[1])
outdir = Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)

expected = {
    "FibonacciHarmonicSniperUltimate-BTC-Round26-CoreRefactor.cs":"edff7234a3fa9bd300ee6bf618e8f376e54a9c399b2a33c6da5df0f3dded8afc",
    "Round26.Execution.cs":"cbded127de602595f4f57f742fd85d0395c0d168bf73ad0536fa7245dade943f",
    "Round26.Quality.cs":"7fc4ec92ade24ea98ae166d425797158d36e2c5cb9708850e9fae31f6a5efdee",
    "Round26.Regime.cs":"9946ef48849962413344e3cd0bb618bb94e2dd3c935c91b5273a7a6a04f77a0d",
    "Round26.Risk.cs":"67c5dcd0218f3f186e973551c365c00970c628d0ce01205bfd6338370b9c9600",
    "Round26.Signal.cs":"94feec345745e4137390d0e23e5376ef8f21e7e9c95714d3898359705a01cca0"
}
for name, sha in expected.items():
    p=srcdir/name
    if not p.exists():
        raise SystemExit(f"missing Round26 file: {name}")
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != sha:
        raise SystemExit(f"Round26 SHA mismatch {name}: {actual}")
    shutil.copy2(p,outdir/name)

main=outdir/"FibonacciHarmonicSniperUltimate-BTC-Round26-CoreRefactor.cs"
s=main.read_text()
def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f"anchor missing: {label}")
    s=s.replace(old,new,1)

anchor='''        [Parameter("R22 M30 Sell Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 1.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22M30SellRiskPercent { get; set; }
'''
rep(anchor,anchor+'''
        [Parameter("R27 H1 Sell Regime Mode", DefaultValue = 0, MinValue = 0, MaxValue = 2, Group = "BTC Round27 Lane Regime")]
        public int Round27H1SellRegimeMode { get; set; }

        [Parameter("R27 M30 Buy Regime Mode", DefaultValue = 0, MinValue = 0, MaxValue = 2, Group = "BTC Round27 Lane Regime")]
        public int Round27M30BuyRegimeMode { get; set; }
''',"parameters")

rep('Print("VERSION v0.23.0-btc-round26-core-refactor");','Print("VERSION v0.24.0-btc-round27-lane-specific-regime");',"version")

log_anchor='''            Print("BTC Round26 Core Refactor | Signal/Quality/Regime/Risk/Execution layers enabled | economic logic frozen to Round22");
'''
rep(log_anchor,log_anchor+'''            Round27InitializeRegimeLayer();
            Print("BTC Round27 Lane Regime | H1SellMode={0} M30BuyMode={1} | 0=off 1=soft 2=strict", Round27H1SellRegimeMode, Round27M30BuyRegimeMode);
''',"startup")

best_block='''            if (best == null)
            {
                Reject("no_candidate_or_conflict");
                return;
            }

            MtfBiasSignal higherBias = null;
'''
rep(best_block,'''            if (best == null)
            {
                Reject("no_candidate_or_conflict");
                return;
            }

            if (!Round27AllowH1(best))
                return;

            MtfBiasSignal higherBias = null;
''',"H1 lane gate")

stop_anchor='''            Print("[R18 DIAG STATS] candidates={0} buy={1} sell={2} confirmed={3} blockedHealth={4} blockedLimits={5} blockedConfirmation={6} execute={7} sameDirH1Within6h={8} sameDirH1Within12h={9} standalone={10}",
                _r18Candidates, _r18CandidateBuys, _r18CandidateSells, _r18ConfirmedCandidates, _r18HealthBlockedCandidates, _r18LimitsBlockedCandidates,
                _r18ConfirmationBlockedCandidates, _r18ExecuteCandidates, _r18SameDirH1Within6h, _r18SameDirH1Within12h, _r18StandaloneCandidates);
'''
rep(stop_anchor,stop_anchor+'''            Print("[R27 LANE STATS] h1SellBlocked={0} m30BuyBlocked={1}", _round27H1SellBlocked, _round27M30BuyBlocked);
''',"stop stats")
main.write_text(s)

q=outdir/"Round26.Quality.cs"
qs=q.read_text()
old='''        private bool Round26QualityPassM30(PatternMatch match, int lastClosed)
        {
            return Round15PassM30Confirmation(match, lastClosed);
        }
'''
new='''        private bool Round26QualityPassM30(PatternMatch match, int lastClosed)
        {
            if (!Round15PassM30Confirmation(match, lastClosed))
                return false;
            return Round27AllowM30(match);
        }
'''
if old not in qs:
    raise SystemExit("Round26 Quality anchor missing")
q.write_text(qs.replace(old,new,1))

(outdir/"Round27.Regime.cs").write_text(r'''using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private ExponentialMovingAverage _round27H4Ema;
        private ExponentialMovingAverage _round27H1Ema;
        private int _round27H1SellBlocked;
        private int _round27M30BuyBlocked;

        private void Round27InitializeRegimeLayer()
        {
            _round27H4Ema = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, EmaPeriod);
            _round27H1Ema = Indicators.ExponentialMovingAverage(_barsH1.ClosePrices, EmaPeriod);
        }

        private bool Round27TrendState(Bars bars, ExponentialMovingAverage ema, TradeType direction, int mode)
        {
            if (mode <= 0 || bars == null || ema == null || bars.Count < 4)
                return true;

            int i = bars.Count - 2;
            if (i < 2)
                return true;

            double close = bars.ClosePrices[i];
            double e = ema.Result[i];
            double prev = ema.Result[i - 1];
            bool priceAligned = direction == TradeType.Buy ? close > e : close < e;
            bool slopeAligned = direction == TradeType.Buy ? e > prev : e < prev;

            if (mode == 1)
                return priceAligned || slopeAligned;
            return priceAligned && slopeAligned;
        }

        private bool Round27AllowH1(PatternMatch match)
        {
            if (match == null || match.Direction != TradeType.Sell || Round27H1SellRegimeMode <= 0)
                return true;

            bool ok = Round27TrendState(_barsH4, _round27H4Ema, TradeType.Sell, Round27H1SellRegimeMode);
            if (!ok)
            {
                _round27H1SellBlocked++;
                if (DebugLogging)
                    Print("[R27 BLOCK] lane=H1_SELL mode={0} time={1:yyyy-MM-ddTHH:mm:ss} score={2:F2}", Round27H1SellRegimeMode, Server.Time, match.Score);
            }
            return ok;
        }

        private bool Round27AllowM30(PatternMatch match)
        {
            if (match == null || match.Direction != TradeType.Buy || Round27M30BuyRegimeMode <= 0)
                return true;

            bool ok = Round27TrendState(_barsH1, _round27H1Ema, TradeType.Buy, Round27M30BuyRegimeMode);
            if (!ok)
            {
                _round27M30BuyBlocked++;
                if (DebugLogging)
                    Print("[R27 BLOCK] lane=M30_BUY mode={0} time={1:yyyy-MM-ddTHH:mm:ss} score={2:F2}", Round27M30BuyRegimeMode, Server.Time, match.Score);
            }
            return ok;
        }
    }
}
''')

locked={
    "FibonacciHarmonicSniperUltimate-BTC-Round26-CoreRefactor.cs":"fea75f79c36c512bc7da2ed5dd42073bad604f4ff43f6825c07eaa0c0483be32",
    "Round26.Quality.cs":"fa7ecfb3e184330a2ec5790c9aa4edb946a74a0ce78c10197fad1ada7d235fec",
    "Round27.Regime.cs":"81f9975914096d65fd2c9a3fd867f98ba86dec7efcbec90cabd39e3c3b205da1"
}
for name, sha in locked.items():
    actual=hashlib.sha256((outdir/name).read_bytes()).hexdigest()
    if actual != sha:
        raise SystemExit(f"Round27 output SHA mismatch {name}: {actual}")
print("Round27 transform verified")
