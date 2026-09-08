#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.7.0-btc-round5-state-matrix"
TARGET_VERSION = "Fibonacci-v0.8.0-btc-round6-hybrid"
SOURCE_FILE = "FibonacciHarmonicSniperUltimate.cs"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def build(repo_root: Path, force: bool = False) -> Path:
    base = repo_root / BASE_VERSION
    target = repo_root / TARGET_VERSION
    if not (base / SOURCE_FILE).is_file():
        raise FileNotFoundError(base / SOURCE_FILE)
    if target.exists():
        if not force:
            raise FileExistsError(target)
        shutil.rmtree(target)
    shutil.copytree(base, target)

    p = target / SOURCE_FILE
    s = p.read_text(encoding="utf-8")

    s = replace_once(
        s,
        'Print("VERSION v0.7.0-btc-round5-state-matrix");',
        'Print("VERSION v0.8.0-btc-round6-hybrid");',
        'version marker',
    )

    param_anchor = '''        [Parameter("Log Pattern Matrix", DefaultValue = true, Group = "BTC Round5 State")]
        public bool LogPatternMatrix { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("R6 Require M30 Sell Confirm", DefaultValue = true, Group = "BTC Round6 Hybrid")]
        public bool Round6RequireM30SellConfirm { get; set; }

        [Parameter("R6 Log Rejected Sell", DefaultValue = true, Group = "BTC Round6 Hybrid")]
        public bool Round6LogRejectedSell { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'round6 parameters')

    fields_anchor = '''        private int _round5ShadowCount;
'''
    fields_block = fields_anchor + '''        private int _round6SellAcceptedCount;
        private int _round6SellRejectedCount;
        private int _round6BuyPassthroughCount;
'''
    s = replace_once(s, fields_anchor, fields_block, 'round6 counters')

    gate_anchor = '''            Round5Snapshot round5 = BuildRound5Snapshot();
            LogRound5Matrix(round5);
            if (!PassRound5HierarchyGate(best, round5))
                return;

            if (DebugLogging)
'''
    gate_block = '''            Round5Snapshot round5 = BuildRound5Snapshot();
            LogRound5Matrix(round5);
            if (!PassRound5HierarchyGate(best, round5))
                return;
            if (!PassRound6SellConfirmation(best, round5))
                return;

            if (DebugLogging)
'''
    s = replace_once(s, gate_anchor, gate_block, 'round6 execution gate')

    method_anchor = '''        private bool PassRound5HierarchyGate(PatternMatch lower, Round5Snapshot snapshot)
'''
    method_block = '''        private bool PassRound6SellConfirmation(PatternMatch lower, Round5Snapshot snapshot)
        {
            if (!Round6RequireM30SellConfirm)
            {
                if (lower.Direction == TradeType.Buy)
                    _round6BuyPassthroughCount++;
                else
                    _round6SellAcceptedCount++;
                return true;
            }

            // Round6 changes only Sell. Buy remains exactly the H1 Champion path.
            if (lower.Direction == TradeType.Buy)
            {
                _round6BuyPassthroughCount++;
                return true;
            }

            var m30 = snapshot == null ? null : snapshot.M30;
            bool aligned = m30 != null && m30.Direction == TradeType.Sell;
            if (aligned)
            {
                _round6SellAcceptedCount++;
                if (DebugLogging)
                    Print("[R6 SELL PASS] H1={0} M30={1} score={2:F1} conf={3:F3} age={4}",
                        lower.Definition.Name, m30.PatternName, m30.Score, m30.Confidence, m30.AgeBars);
                return true;
            }

            _round6SellRejectedCount++;
            if (Round6LogRejectedSell)
                Print("[R6 SHADOW SELL] reject H1 Sell | M30={0}", DescribeRound5(m30));
            return Reject("round6_m30_sell_confirmation");
        }

        private bool PassRound5HierarchyGate(PatternMatch lower, Round5Snapshot snapshot)
'''
    s = replace_once(s, method_anchor, method_block, 'round6 sell method')

    stop_anchor = '''            Print("[ROUND5 STATS] accepted={0} macroVeto={1} weightedReject={2} shadow={3}", _round5AcceptedCount, _round5MacroVetoCount, _round5WeightedRejectCount, _round5ShadowCount);
'''
    stop_block = stop_anchor + '''            Print("[ROUND6 STATS] buyPass={0} sellAccepted={1} sellRejected={2}", _round6BuyPassthroughCount, _round6SellAcceptedCount, _round6SellRejectedCount);
'''
    s = replace_once(s, stop_anchor, stop_block, 'round6 stop stats')

    startup_anchor = '''            Print("BTC Round5 State Matrix | Mode={0} | D1={1} | H4={2} | H1={3} | M30={4} | M15={5} | M5={6} | M1={7}",
                Round5Mode, D1Patterns, H4Patterns, H1Patterns, M30Patterns, M15Patterns, M5Patterns, M1Patterns);
'''
    startup_block = startup_anchor + '''            Print("BTC Round6 Hybrid | M30 Sell Confirm={0} | M30Patterns={1} | M30MaxAge={2}",
                Round6RequireM30SellConfirm, M30Patterns, M30StateMaxAge);
'''
    s = replace_once(s, startup_anchor, startup_block, 'round6 startup')

    p.write_text(s, encoding="utf-8")

    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.7.0-btc-round5-state-matrix</Version>', '<Version>0.8.0-btc-round6-hybrid</Version>')
        csproj.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', type=Path, default=Path.cwd())
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    print(build(a.repo_root.resolve(), a.force))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
