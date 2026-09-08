#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.13.0-btc-round15-portfolio"
TARGET_VERSION="Fibonacci-v0.14.0-btc-round16-regime-diagnostics"
SOURCE_FILE="FibonacciHarmonicSniperUltimate.cs"

def ro(s,o,n,label):
    c=s.count(o)
    if c!=1: raise RuntimeError(f"{label}: expected 1 match, found {c}")
    return s.replace(o,n,1)

def build(root:Path, force=False):
    base=root/BASE_VERSION; target=root/TARGET_VERSION
    if not (base/SOURCE_FILE).is_file(): raise FileNotFoundError(base/SOURCE_FILE)
    if target.exists():
        if not force: raise FileExistsError(target)
        shutil.rmtree(target)
    shutil.copytree(base,target)
    p=target/SOURCE_FILE; s=p.read_text(encoding='utf-8')

    s=ro(s,'Print("VERSION v0.13.0-btc-round15-portfolio");','Print("VERSION v0.14.0-btc-round16-regime-diagnostics");','version')

    pa='''        [Parameter("R15 Enable M30 Frequency Engine", DefaultValue = true, Group = "BTC Round15 Portfolio")]
        public bool Round15EnableM30Engine { get; set; }
'''
    pb=pa+'''
        [Parameter("R16 Log M30 Regime State", DefaultValue = true, Group = "BTC Round16 Regime")]
        public bool Round16LogM30Regime { get; set; }
'''
    s=ro(s,pa,pb,'r16 parameter')

    anchor='''            _r15M30Opened++;
            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);
'''
    block='''            _r15M30Opened++;
            Round16LogM30State(result.Position.Id, m, lastClosed, atr);
            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);
'''
    s=ro(s,anchor,block,'r16 open hook')

    ma='''        private void UpdateRound9Shadows()
'''
    methods=r'''        private void Round16LogM30State(long positionId, PatternMatch m, int lastClosed, double atr)
        {
            if (!Round16LogM30Regime || atr <= 0 || lastClosed < 2)
                return;

            double close = _barsM30.ClosePrices[lastClosed];
            double ema = _r15M30Ema.Result[lastClosed];
            double emaPrev = _r15M30Ema.Result[lastClosed - 1];
            double side = m.Direction == TradeType.Buy ? 1.0 : -1.0;
            double atrPct = close != 0 ? 100.0 * atr / Math.Abs(close) : 0.0;
            double emaDistAtr = side * (close - ema) / atr;
            double emaSlopeAtr = side * (ema - emaPrev) / atr;

            int n24 = Math.Min(24, lastClosed);
            double path = 0.0;
            for (int i = lastClosed - n24 + 1; i <= lastClosed; i++)
                if (i > 0) path += Math.Abs(_barsM30.ClosePrices[i] - _barsM30.ClosePrices[i - 1]);
            double er24 = path > 0 ? Math.Abs(close - _barsM30.ClosePrices[lastClosed - n24]) / path : 0.0;
            double trend24Atr = side * (close - _barsM30.ClosePrices[lastClosed - n24]) / atr;

            int n48 = Math.Min(48, lastClosed + 1);
            int first48 = lastClosed - n48 + 1;
            double hi = double.MinValue, lo = double.MaxValue, atrSum = 0.0;
            int atrCount = 0;
            for (int i = first48; i <= lastClosed; i++)
            {
                hi = Math.Max(hi, _barsM30.HighPrices[i]);
                lo = Math.Min(lo, _barsM30.LowPrices[i]);
                double av = _r15M30Atr.Result[i];
                if (!double.IsNaN(av) && !double.IsInfinity(av) && av > 0) { atrSum += av; atrCount++; }
            }
            double range48Atr = (hi > lo) ? (hi - lo) / atr : 0.0;
            double atrMean48 = atrCount > 0 ? atrSum / atrCount : atr;
            double atrRatio48 = atrMean48 > 0 ? atr / atrMean48 : 1.0;
            double distanceAtr = Math.Abs(close - m.D.Price) / atr;
            int age = lastClosed - m.D.Index;

            Print("[R16 M30 STATE] id={0} t={1:yyyy-MM-ddTHH:mm:ss} dir={2} score={3:F3} age={4} atrPct={5:F6} atrRatio48={6:F6} emaDistAtr={7:F6} emaSlopeAtr={8:F6} er24={9:F6} trend24Atr={10:F6} range48Atr={11:F6} distanceAtr={12:F6}",
                positionId, Server.Time, m.Direction, m.Score, age, atrPct, atrRatio48, emaDistAtr, emaSlopeAtr, er24, trend24Atr, range48Atr, distanceAtr);
        }

        private void UpdateRound9Shadows()
'''
    s=ro(s,ma,methods,'r16 state method')

    startup='''            Print("BTC Round15 Portfolio | H1 primary + M30 Reciprocal ABCD frequency engine={0} | shared equity/risk/MaxOpenPositions | H1 priority", Round15EnableM30Engine);
'''
    s=ro(s,startup,startup+'''            Print("BTC Round16 Regime Diagnostics | M30 state logging={0} | diagnostics only; no regime gate", Round16LogM30Regime);
''','r16 startup')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.13.0-btc-round15-portfolio</Version>','<Version>0.14.0-btc-round16-regime-diagnostics</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
