#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.15.0-btc-round16-h1-health"
TARGET_VERSION="Fibonacci-v0.16.0-btc-round17-m30-half-risk"
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

    s=ro(s,'Print("VERSION v0.15.0-btc-round16-h1-health");','Print("VERSION v0.16.0-btc-round17-m30-half-risk");','version')

    pa='''        [Parameter("R16 H1 Health Gate", DefaultValue = true, Group = "BTC Round16 Regime")]
        public bool Round16H1HealthGate { get; set; }
'''
    pb=pa+'''
        [Parameter("R17 M30 Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round17 Risk")]
        public double Round17M30RiskPercent { get; set; }
'''
    s=ro(s,pa,pb,'r17 parameter')

    s=ro(s,'double volume=CalculateVolume(slPips);','double volume=Round17CalculateM30Volume(slPips);','m30 volume hook')

    ma='''        private bool Round16H1HealthAllowsM30()
'''
    methods='''        private double Round17CalculateM30Volume(double slPips)
        {
            if (slPips <= 0 || Round17M30RiskPercent <= 0)
                return 0;
            double amount = Account.Equity * Round17M30RiskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            return raw;
        }

        private bool Round16H1HealthAllowsM30()
'''
    s=ro(s,ma,methods,'r17 method')

    startup='''            Print("BTC Round16 H1 Health Gate | enabled={0} | M30 allowed only when >=2 of last 3 H1 trades are profitable", Round16H1HealthGate);
'''
    s=ro(s,startup,startup+'''            Print("BTC Round17 Risk Split | H1 RiskPercent={0:F2}% | M30 Risk={1:F2}%", RiskPercent, Round17M30RiskPercent);
''','r17 startup')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.15.0-btc-round16-h1-health</Version>','<Version>0.16.0-btc-round17-m30-half-risk</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
