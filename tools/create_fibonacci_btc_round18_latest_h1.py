#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.16.0-btc-round17-m30-half-risk"
TARGET_VERSION="Fibonacci-v0.17.0-btc-round18-latest-h1"
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

    s=ro(s,'Print("VERSION v0.16.0-btc-round17-m30-half-risk");','Print("VERSION v0.17.0-btc-round18-latest-h1");','version')

    pa='''        [Parameter("R17 M30 Risk % Equity", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round17 Risk")]
        public double Round17M30RiskPercent { get; set; }
'''
    pb=pa+'''
        [Parameter("R18 Require Latest H1 Win", DefaultValue = true, Group = "BTC Round18 Regime")]
        public bool Round18RequireLatestH1Win { get; set; }
'''
    s=ro(s,pa,pb,'r18 parameter')

    old='''        private bool Round16H1HealthAllowsM30()
        {
            if (!Round16H1HealthGate)
                return true;
            if (_r16RecentH1Wins.Count < 3)
                return false;
            int wins = 0;
            foreach (bool w in _r16RecentH1Wins)
                if (w) wins++;
            return wins >= 2;
        }
'''
    new='''        private bool Round16H1HealthAllowsM30()
        {
            if (!Round16H1HealthGate)
                return true;
            if (_r16RecentH1Wins.Count < 3)
                return false;
            int wins = 0;
            bool latestWin = false;
            foreach (bool w in _r16RecentH1Wins)
            {
                if (w) wins++;
                latestWin = w;
            }
            bool baseHealth = wins >= 2;
            if (!Round18RequireLatestH1Win)
                return baseHealth;
            return baseHealth && latestWin;
        }
'''
    s=ro(s,old,new,'latest H1 health logic')

    startup='''            Print("BTC Round17 Risk Split | H1 RiskPercent={0:F2}% | M30 Risk={1:F2}%", RiskPercent, Round17M30RiskPercent);
'''
    s=ro(s,startup,startup+'''            Print("BTC Round18 Regime | require latest closed H1 trade profitable={0} in addition to Round16 2-of-3 health", Round18RequireLatestH1Win);
''','r18 startup')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.16.0-btc-round17-m30-half-risk</Version>','<Version>0.17.0-btc-round18-latest-h1</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
