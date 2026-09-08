#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.16.0-btc-round17-m30-half-risk"
TARGET_VERSION="Fibonacci-v0.17.1-btc-round19-h1-cold-risk"
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

    s=ro(s,'Print("VERSION v0.16.0-btc-round17-m30-half-risk");','Print("VERSION v0.17.1-btc-round19-h1-cold-risk");','version')

    pa='''        [Parameter("R17 M30 Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round17 Risk")]
        public double Round17M30RiskPercent { get; set; }
'''
    pb=pa+'''
        [Parameter("R19 Enable H1 Cold Risk", DefaultValue = true, Group = "BTC Round19 Risk")]
        public bool Round19EnableH1ColdRisk { get; set; }

        [Parameter("R19 H1 Cold Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Risk")]
        public double Round19H1ColdRiskPercent { get; set; }
'''
    s=ro(s,pa,pb,'r19 parameters')

    s=ro(s,'double volume = CalculateVolume(slPips);','double volume = Round19CalculateH1Volume(slPips);','h1 volume hook')

    anchor='''        private double Round17CalculateM30Volume(double slPips)
'''
    methods='''        private bool Round19H1ColdHealth()
        {
            if (_r16RecentH1Wins.Count < 3)
                return false;
            int wins = 0;
            foreach (bool w in _r16RecentH1Wins)
                if (w) wins++;
            return wins < 2;
        }

        private double Round19CalculateH1Volume(double slPips)
        {
            if (!Round19EnableH1ColdRisk || RiskMode != RiskSizingMode.RiskPercentEquity || !Round19H1ColdHealth())
                return CalculateVolume(slPips);
            if (slPips <= 0 || Round19H1ColdRiskPercent <= 0)
                return 0;
            double amount = Account.Equity * Round19H1ColdRiskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            return raw;
        }

        private double Round17CalculateM30Volume(double slPips)
'''
    s=ro(s,anchor,methods,'r19 methods')

    startup='''            Print("BTC Round17 Risk Split | H1 RiskPercent={0:F2}% | M30 Risk={1:F2}%", RiskPercent, Round17M30RiskPercent);
'''
    s=ro(s,startup,startup+'''            Print("BTC Round19 H1 Cold Risk | enabled={0} | normal={1:F2}% | cold(<2 wins of last 3 H1)={2:F2}%", Round19EnableH1ColdRisk, RiskPercent, Round19H1ColdRiskPercent);
''','r19 startup')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.16.0-btc-round17-m30-half-risk</Version>','<Version>0.17.1-btc-round19-h1-cold-risk</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
