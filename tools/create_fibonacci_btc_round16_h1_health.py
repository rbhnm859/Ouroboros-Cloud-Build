#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.13.0-btc-round15-portfolio"
TARGET_VERSION="Fibonacci-v0.15.0-btc-round16-h1-health"
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

    s=ro(s,'Print("VERSION v0.13.0-btc-round15-portfolio");','Print("VERSION v0.15.0-btc-round16-h1-health");','version')

    pa='''        [Parameter("R15 Enable M30 Frequency Engine", DefaultValue = true, Group = "BTC Round15 Portfolio")]
        public bool Round15EnableM30Engine { get; set; }
'''
    pb=pa+'''
        [Parameter("R16 H1 Health Gate", DefaultValue = true, Group = "BTC Round16 Regime")]
        public bool Round16H1HealthGate { get; set; }
'''
    s=ro(s,pa,pb,'health parameter')

    fa='''        private int _r15M30BlockedLimits;
'''
    fb=fa+'''        private readonly Queue<bool> _r16RecentH1Wins = new Queue<bool>();
        private int _r16M30BlockedHealth;
'''
    s=ro(s,fa,fb,'health fields')

    gate_anchor='''            if (!Round15PassSharedLimits(lastClosed))
            {
                _r15M30BlockedLimits++;
                return;
            }
'''
    gate_block='''            if (!Round16H1HealthAllowsM30())
            {
                _r16M30BlockedHealth++;
                return;
            }

''' + gate_anchor
    s=ro(s,gate_anchor,gate_block,'health gate hook')

    method_anchor='''        private void Round15ProcessM30ClosedBar()
'''
    method_block='''        private bool Round16H1HealthAllowsM30()
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

        private void Round15ProcessM30ClosedBar()
'''
    s=ro(s,method_anchor,method_block,'health method')

    close_anchor='''            if (!_stats.ContainsKey(name))
                _stats[name] = new PatternStats();
            var s = _stats[name];
'''
    close_block='''            if (!name.StartsWith("M30|", StringComparison.OrdinalIgnoreCase))
            {
                _r16RecentH1Wins.Enqueue(p.NetProfit > 0);
                while (_r16RecentH1Wins.Count > 3)
                    _r16RecentH1Wins.Dequeue();
                int h1Wins = 0;
                foreach (bool w in _r16RecentH1Wins)
                    if (w) h1Wins++;
                Print("[R16 H1 HEALTH] samples={0} wins={1} m30Allowed={2}", _r16RecentH1Wins.Count, h1Wins, Round16H1HealthAllowsM30());
            }

''' + close_anchor
    s=ro(s,close_anchor,close_block,'health update')

    startup='''            Print("BTC Round15 Portfolio | H1 primary + M30 Reciprocal ABCD frequency engine={0} | shared equity/risk/MaxOpenPositions | H1 priority", Round15EnableM30Engine);
'''
    s=ro(s,startup,startup+'''            Print("BTC Round16 H1 Health Gate | enabled={0} | M30 allowed only when >=2 of last 3 H1 trades are profitable", Round16H1HealthGate);
''','health startup')

    stop='''            Print("[R15 STATS] m30Opened={0} m30BlockedOpenPosition={1} m30BlockedLimits={2}", _r15M30Opened, _r15M30BlockedOpenPosition, _r15M30BlockedLimits);
'''
    s=ro(s,stop,stop+'''            Print("[R16 HEALTH STATS] m30BlockedHealth={0}", _r16M30BlockedHealth);
''','health stop')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.13.0-btc-round15-portfolio</Version>','<Version>0.15.0-btc-round16-h1-health</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
