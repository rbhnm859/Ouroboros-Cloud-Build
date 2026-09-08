#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.8.0-btc-round6-hybrid"
TARGET_VERSION = "Fibonacci-v0.9.0-btc-round7-inverse-veto"
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
        'Print("VERSION v0.8.0-btc-round6-hybrid");',
        'Print("VERSION v0.9.0-btc-round7-inverse-veto");',
        'version marker',
    )

    # Round7 supersedes the rejected Round6 confirmation hypothesis by default.
    s = replace_once(
        s,
        '[Parameter("R6 Require M30 Sell Confirm", DefaultValue = true, Group = "BTC Round6 Hybrid")]',
        '[Parameter("R6 Require M30 Sell Confirm", DefaultValue = false, Group = "BTC Round6 Hybrid")]',
        'disable round6 default',
    )

    param_anchor = '''        [Parameter("R6 Log Rejected Sell", DefaultValue = true, Group = "BTC Round6 Hybrid")]
        public bool Round6LogRejectedSell { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("R7 Veto M30 Sell Alignment", DefaultValue = true, Group = "BTC Round7 Inverse Veto")]
        public bool Round7VetoM30SellAlignment { get; set; }

        [Parameter("R7 Log Vetoed Sell", DefaultValue = true, Group = "BTC Round7 Inverse Veto")]
        public bool Round7LogVetoedSell { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'round7 parameters')

    fields_anchor = '''        private int _round6BuyPassthroughCount;
'''
    fields_block = fields_anchor + '''        private int _round7BuyPassthroughCount;
        private int _round7SellAcceptedCount;
        private int _round7SellVetoedCount;
'''
    s = replace_once(s, fields_anchor, fields_block, 'round7 counters')

    gate_anchor = '''            if (!PassRound6SellConfirmation(best, round5))
                return;

            if (DebugLogging)
'''
    gate_block = '''            if (!PassRound6SellConfirmation(best, round5))
                return;
            if (!PassRound7InverseSellVeto(best, round5))
                return;

            if (DebugLogging)
'''
    s = replace_once(s, gate_anchor, gate_block, 'round7 execution gate')

    method_anchor = '''        private bool PassRound6SellConfirmation(PatternMatch lower, Round5Snapshot snapshot)
'''
    method_block = '''        private bool PassRound7InverseSellVeto(PatternMatch lower, Round5Snapshot snapshot)
        {
            if (!Round7VetoM30SellAlignment)
            {
                if (lower.Direction == TradeType.Buy)
                    _round7BuyPassthroughCount++;
                else
                    _round7SellAcceptedCount++;
                return true;
            }

            // Round7 changes only Sell. H1 Buy remains exactly the Growth Champion path.
            if (lower.Direction == TradeType.Buy)
            {
                _round7BuyPassthroughCount++;
                return true;
            }

            var m30 = snapshot == null ? null : snapshot.M30;
            bool alignedSell = m30 != null && m30.Direction == TradeType.Sell;
            if (alignedSell)
            {
                _round7SellVetoedCount++;
                if (Round7LogVetoedSell)
                    Print("[R7 VETO SELL] reject H1 Sell | M30={0} score={1:F1} conf={2:F3} age={3}",
                        m30.PatternName, m30.Score, m30.Confidence, m30.AgeBars);
                return Reject("round7_inverse_m30_sell_veto");
            }

            _round7SellAcceptedCount++;
            if (DebugLogging)
                Print("[R7 SELL PASS] H1={0} | M30={1}", lower.Definition.Name, DescribeRound5(m30));
            return true;
        }

        private bool PassRound6SellConfirmation(PatternMatch lower, Round5Snapshot snapshot)
'''
    s = replace_once(s, method_anchor, method_block, 'round7 veto method')

    stop_anchor = '''            Print("[ROUND6 STATS] buyPass={0} sellAccepted={1} sellRejected={2}", _round6BuyPassthroughCount, _round6SellAcceptedCount, _round6SellRejectedCount);
'''
    stop_block = stop_anchor + '''            Print("[ROUND7 STATS] buyPass={0} sellAccepted={1} sellVetoed={2}", _round7BuyPassthroughCount, _round7SellAcceptedCount, _round7SellVetoedCount);
'''
    s = replace_once(s, stop_anchor, stop_block, 'round7 stop stats')

    startup_anchor = '''            Print("BTC Round6 Hybrid | M30 Sell Confirm={0} | M30Patterns={1} | M30MaxAge={2}",
                Round6RequireM30SellConfirm, M30Patterns, M30StateMaxAge);
'''
    startup_block = startup_anchor + '''            Print("BTC Round7 Inverse Veto | M30 Sell Veto={0} | M30Patterns={1} | M30MaxAge={2}",
                Round7VetoM30SellAlignment, M30Patterns, M30StateMaxAge);
'''
    s = replace_once(s, startup_anchor, startup_block, 'round7 startup')

    p.write_text(s, encoding="utf-8")

    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.8.0-btc-round6-hybrid</Version>', '<Version>0.9.0-btc-round7-inverse-veto</Version>')
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
