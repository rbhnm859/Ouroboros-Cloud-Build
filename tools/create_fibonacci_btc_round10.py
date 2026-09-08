#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION="Fibonacci-v0.11.0-btc-round9-shadow"
TARGET_VERSION="Fibonacci-v0.12.0-btc-round10-funnel"
SOURCE_FILE="FibonacciHarmonicSniperUltimate.cs"

def ro(s,o,n,label):
    c=s.count(o)
    if c!=1: raise RuntimeError(f"{label}: expected 1 match, found {c}")
    return s.replace(o,n,1)

def build(root:Path,force=False):
    base=root/BASE_VERSION; target=root/TARGET_VERSION
    if not (base/SOURCE_FILE).is_file(): raise FileNotFoundError(base/SOURCE_FILE)
    if target.exists():
        if not force: raise FileExistsError(target)
        shutil.rmtree(target)
    shutil.copytree(base,target)
    p=target/SOURCE_FILE; s=p.read_text(encoding='utf-8')
    s=ro(s,'Print("VERSION v0.11.0-btc-round9-shadow");','Print("VERSION v0.12.0-btc-round10-funnel");','version')

    pa='''        [Parameter("R9 Shadow Horizon Hours", DefaultValue = 48, MinValue = 6, MaxValue = 96, Group = "BTC Round9 Shadow")]
        public int Round9ShadowHorizonHours { get; set; }
'''
    pb=pa+'''
        [Parameter("R10 Log Rejection Funnel", DefaultValue = true, Group = "BTC Round10 Funnel")]
        public bool Round10LogFunnel { get; set; }
'''
    s=ro(s,pa,pb,'parameter')

    fa='''        private readonly Dictionary<string, int> _diagnostics = new Dictionary<string, int>();
'''
    fb=fa+'''        private readonly Dictionary<string, long> _round10Funnel = new Dictionary<string, long>(StringComparer.OrdinalIgnoreCase);
        private void Round10Count(string key)
        {
            if (!Round10LogFunnel) return;
            long n; _round10Funnel.TryGetValue(key, out n); _round10Funnel[key] = n + 1;
        }
        private void Round10Count(string key, TradeType direction)
        {
            Round10Count(key + "_" + direction.ToString().ToLowerInvariant());
        }
'''
    s=ro(s,fa,fb,'funnel fields')

    ra='''        private bool Reject(string reason)
        {
            if (!_diagnostics.ContainsKey(reason)) _diagnostics[reason] = 0;
            _diagnostics[reason]++;
            return false;
        }
'''
    rb='''        private bool Reject(string reason)
        {
            if (!_diagnostics.ContainsKey(reason)) _diagnostics[reason] = 0;
            _diagnostics[reason]++;
            Round10Count("reject_" + reason);
            return false;
        }
'''
    s=ro(s,ra,rb,'reject hook')

    s=ro(s,'''            var pivots = BuildConfirmedPivots();
            if (pivots.Count < 5)
                return;
''','''            var pivots = BuildConfirmedPivots();
            if (pivots.Count < 5)
            {
                Round10Count("bar_insufficient_pivots");
                return;
            }
            Round10Count("bar_has_5pivots");
''','pivots')

    s=ro(s,'''                int age = Bars.Count - 1 - d.Index;
                if (age < 0 || age > MaxPatternAgeBars)
                    continue;
''','''                int age = Bars.Count - 1 - d.Index;
                if (age < 0 || age > MaxPatternAgeBars)
                {
                    if (age > MaxPatternAgeBars && age <= MaxPatternAgeBars + 2) Round10Count("age_miss_0_2", direction.Value);
                    else if (age > MaxPatternAgeBars && age <= MaxPatternAgeBars + 4) Round10Count("age_miss_2_4", direction.Value);
                    else Round10Count("age_miss_far", direction.Value);
                    continue;
                }
                Round10Count("age_pass", direction.Value);
''','age buckets')

    s=ro(s,'''                    double score = def.Score(xb, ac, bd, xd, cdAb, RatioTolerancePercent);
                    if (score < MinPatternScore)
                        continue;
''','''                    double score = def.Score(xb, ac, bd, xd, cdAb, RatioTolerancePercent);
                    Round10Count("pattern_evaluated", direction.Value);
                    if (score < MinPatternScore)
                    {
                        double gap = MinPatternScore - score;
                        if (gap <= 2.0) Round10Count("score_miss_0_2", direction.Value);
                        else if (gap <= 4.0) Round10Count("score_miss_2_4", direction.Value);
                        else Round10Count("score_miss_gt4", direction.Value);
                        continue;
                    }
                    Round10Count("score_pass", direction.Value);
''','score buckets')

    s=ro(s,'''                    if (EmaFilterMode == TrendFilterMode.Strict && !match.TrendAligned)
                        continue;
                    if (EmaFilterMode == TrendFilterMode.ConfirmOnly && !match.TrendAligned)
                        continue;
                    if (_consumedSignals.Contains(match.SignalKey))
                        continue;
                    if (!PassConfirmation(match))
                        continue;
''','''                    if (EmaFilterMode == TrendFilterMode.Strict && !match.TrendAligned)
                    { Round10Count("ema_strict_reject", match.Direction); continue; }
                    if (EmaFilterMode == TrendFilterMode.ConfirmOnly && !match.TrendAligned)
                    { Round10Count("ema_confirm_reject", match.Direction); continue; }
                    if (_consumedSignals.Contains(match.SignalKey))
                    { Round10Count("duplicate_signal", match.Direction); continue; }
                    if (!PassConfirmation(match))
                    { Round10Count("confirmation_reject", match.Direction); continue; }
                    Round10Count("confirmation_pass", match.Direction);
''','candidate gates')

    s=ro(s,'''            double distance = Math.Abs(close - m.D.Price);
            if (distance > atr * MaxEntryDistanceAtr)
                return Reject("confirmation_gate_2");
''','''            double distance = Math.Abs(close - m.D.Price);
            if (distance > atr * MaxEntryDistanceAtr)
            {
                double ratio = distance / atr;
                if (ratio <= MaxEntryDistanceAtr + 0.20) Round10Count("entry_distance_miss_0_02", m.Direction);
                else if (ratio <= MaxEntryDistanceAtr + 0.40) Round10Count("entry_distance_miss_02_04", m.Direction);
                else Round10Count("entry_distance_miss_far", m.Direction);
                return Reject("confirmation_gate_2");
            }
            Round10Count("entry_distance_pass", m.Direction);
''','distance buckets')

    s=ro(s,'''                    candidates.Add(match);
''','''                    candidates.Add(match);
                    Round10Count("candidate_added", match.Direction);
''','candidate add')

    s=ro(s,'''            PatternMatch best = ordered[0];
''','''            PatternMatch best = ordered[0];
            Round10Count("best_selected", best.Direction);
''','best selected')

    s=ro(s,'''        private void ExecutePatternTrade(PatternMatch m)
        {
''','''        private void ExecutePatternTrade(PatternMatch m)
        {
            Round10Count("execute_attempt", m.Direction);
''','execute attempt')

    s=ro(s,'''            _tradesToday++;
''','''            Round10Count("opened", m.Direction);
            _tradesToday++;
''','opened')

    s=ro(s,'''            Positions.Closed -= OnPositionClosed;
''','''            Positions.Closed -= OnPositionClosed;
            foreach (var kv in _round10Funnel.OrderByDescending(k => k.Value).ThenBy(k => k.Key))
                Print("[R10 FUNNEL] {0}={1}", kv.Key, kv.Value);
''','stop funnel')

    s=ro(s,'''            Print("BTC Round9 Shadow | enabled={0} | horizon={1}h | observes TP continuation only; no shadow orders", Round9ShadowTpContinuation, Round9ShadowHorizonHours);
''','''            Print("BTC Round9 Shadow | enabled={0} | horizon={1}h | observes TP continuation only; no shadow orders", Round9ShadowTpContinuation, Round9ShadowHorizonHours);
            Print("BTC Round10 Funnel | enabled={0} | diagnostics only; trading logic unchanged", Round10LogFunnel);
''','startup')

    p.write_text(s,encoding='utf-8')
    cs=target/'FibonacciHarmonicSniperUltimate.csproj'
    if cs.is_file():
        t=cs.read_text(encoding='utf-8').replace('<Version>0.11.0-btc-round9-shadow</Version>','<Version>0.12.0-btc-round10-funnel</Version>')
        cs.write_text(t,encoding='utf-8')
    return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path.cwd()); ap.add_argument('--force',action='store_true'); a=ap.parse_args(); print(build(a.repo_root.resolve(),a.force)); return 0
if __name__=='__main__': raise SystemExit(main())
