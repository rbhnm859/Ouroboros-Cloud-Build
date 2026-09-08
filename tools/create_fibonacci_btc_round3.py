#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.4.0-research1"
TARGET_VERSION = "Fibonacci-v0.5.0-btc-round3"
SOURCE_FILE = "FibonacciHarmonicSniperUltimate.cs"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def build(repo_root: Path, force: bool=False) -> Path:
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

    s = replace_once(s,
        'Print("VERSION v0.4.0-research1");',
        'Print("VERSION v0.5.0-btc-round3");',
        'version marker')

    anchor = '''        [Parameter("Ratio Tolerance %", DefaultValue = 6.0, MinValue = 0.0, MaxValue = 25.0, Group = "Patterns")]
        public double RatioTolerancePercent { get; set; }
'''
    block = anchor + '''
        [Parameter("Sell Min Pattern Score % (0=inherit)", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 100.0, Group = "BTC Round3 Sell")]
        public double SellMinPatternScore { get; set; }

        [Parameter("Sell Require EMA Alignment", DefaultValue = false, Group = "BTC Round3 Sell")]
        public bool SellRequireTrendAlignment { get; set; }

        [Parameter("Sell Confirmation Move ATR (0=inherit)", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 2.0, Group = "BTC Round3 Sell")]
        public double SellConfirmationMoveAtr { get; set; }

        [Parameter("Sell Max Entry Distance ATR (0=inherit)", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 10.0, Group = "BTC Round3 Sell")]
        public double SellMaxEntryDistanceAtr { get; set; }

        [Parameter("Sell Require Previous Low Break", DefaultValue = false, Group = "BTC Round3 Sell")]
        public bool SellRequirePreviousLowBreak { get; set; }
'''
    s = replace_once(s, anchor, block, 'sell parameters')

    gate_anchor = '''                    if (!PassConfirmation(match))
                        continue;
                    candidates.Add(match);
'''
    gate_block = '''                    if (!PassConfirmation(match))
                        continue;
                    if (match.Direction == TradeType.Sell && !PassSellRound3Gate(match))
                        continue;
                    candidates.Add(match);
'''
    s = replace_once(s, gate_anchor, gate_block, 'sell candidate gate')

    method_anchor = '''        private bool PassConfirmation(PatternMatch m)
        {
'''
    method_block = '''        private bool PassSellRound3Gate(PatternMatch m)
        {
            if (m.Direction != TradeType.Sell)
                return true;

            double minScore = SellMinPatternScore > 0 ? SellMinPatternScore : MinPatternScore;
            if (m.Score < minScore)
                return Reject("sell_score");

            if (SellRequireTrendAlignment && !m.TrendAligned)
                return Reject("sell_ema");

            int last = Bars.Count - 1;
            double close = Bars.ClosePrices[last];
            double atr = _atr.Result.LastValue;
            if (atr <= 0)
                return Reject("sell_atr");

            double confirmation = SellConfirmationMoveAtr > 0 ? SellConfirmationMoveAtr : ConfirmationMoveAtr;
            if (confirmation > ConfirmationMoveAtr && close > m.D.Price - atr * confirmation)
                return Reject("sell_confirmation");

            double maxDistance = SellMaxEntryDistanceAtr > 0 ? SellMaxEntryDistanceAtr : MaxEntryDistanceAtr;
            if (maxDistance < MaxEntryDistanceAtr && Math.Abs(close - m.D.Price) > atr * maxDistance)
                return Reject("sell_distance");

            if (SellRequirePreviousLowBreak)
            {
                if (last < 1 || close >= Bars.LowPrices[last - 1])
                    return Reject("sell_previous_low");
            }
            return true;
        }

        private bool PassConfirmation(PatternMatch m)
        {
'''
    s = replace_once(s, method_anchor, method_block, 'sell gate method')
    p.write_text(s, encoding="utf-8")
    return target


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root', type=Path, default=Path.cwd())
    ap.add_argument('--force', action='store_true')
    a=ap.parse_args()
    print(build(a.repo_root.resolve(), a.force))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
