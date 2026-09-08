#!/usr/bin/env python3
"""Create Fibonacci v0.4.0-research1 from the immutable v0.3.0-fix3 baseline."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


BASE_VERSION = "Fibonacci-v0.3.0-fix3"
TARGET_VERSION = "Fibonacci-v0.4.0-research1"
SOURCE_FILE = "FibonacciHarmonicSniperUltimate.cs"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one match, found {count}. "
            "The baseline may have changed."
        )
    return source.replace(old, new, 1)


def build_candidate(repo_root: Path, force: bool = False) -> Path:
    baseline = repo_root / BASE_VERSION
    target = repo_root / TARGET_VERSION

    if not (baseline / SOURCE_FILE).is_file():
        raise FileNotFoundError(f"Missing baseline source: {baseline / SOURCE_FILE}")

    if target.exists():
        if not force:
            raise FileExistsError(
                f"{target} already exists. Re-run with --force to recreate it."
            )
        shutil.rmtree(target)

    shutil.copytree(baseline, target)
    source_path = target / SOURCE_FILE
    source = source_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        'Print("VERSION v0.3.0-fix3");',
        'Print("VERSION v0.4.0-research1");',
        "version marker",
    )

    risk_insert_old = '''        [Parameter("Max Stop (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Risk")]
        public double MaxStopPips { get; set; }

        [Parameter("TP Mode", DefaultValue = TakeProfitMode.Fib618AD, Group = "Risk")]
'''
    risk_insert_new = '''        [Parameter("Max Stop (pips, 0=off)", DefaultValue = 0.0, MinValue = 0.0, Group = "Risk")]
        public double MaxStopPips { get; set; }

        [Parameter("Stop Anchor Mode", DefaultValue = StopAnchorModeKind.PatternInvalidation, Group = "Risk")]
        public StopAnchorModeKind StopAnchorMode { get; set; }

        [Parameter("Target RR Policy", DefaultValue = TargetRiskRewardPolicyKind.RejectPoorGeometry, Group = "Risk")]
        public TargetRiskRewardPolicyKind TargetRiskRewardPolicy { get; set; }

        [Parameter("TP Mode", DefaultValue = TakeProfitMode.Fib618AD, Group = "Risk")]
'''
    source = replace_once(source, risk_insert_old, risk_insert_new, "risk parameters")

    stop_old = '''            double slPrice = m.Direction == TradeType.Buy
                ? m.D.Price - atr * SlAtrBuffer
                : m.D.Price + atr * SlAtrBuffer;
'''
    stop_new = '''            double stopAnchor = ResolveStopAnchor(m);
            double slPrice = m.Direction == TradeType.Buy
                ? stopAnchor - atr * SlAtrBuffer
                : stopAnchor + atr * SlAtrBuffer;
'''
    source = replace_once(source, stop_old, stop_new, "structural stop")

    target_old = '''            double tpPips = CalculateTakeProfitPips(m, entry, slPips);
            if (tpPips < slPips * MinimumRiskReward)
                tpPips = slPips * FallbackRiskReward;
            if (tpPips < slPips * MinimumRiskReward)
                return;

            double volume = CalculateVolume(slPips);
'''
    target_new = '''            double tpPips = CalculateTakeProfitPips(m, entry, slPips);
            if (tpPips < slPips * MinimumRiskReward)
            {
                if (TargetRiskRewardPolicy == TargetRiskRewardPolicyKind.RejectPoorGeometry)
                {
                    Reject("target_rr_too_low");
                    return;
                }

                tpPips = slPips * FallbackRiskReward;
            }
            if (tpPips < slPips * MinimumRiskReward)
            {
                Reject("target_rr_too_low");
                return;
            }
            double volume = CalculateVolume(slPips);
'''
    source = replace_once(source, target_old, target_new, "target R:R policy")

    volume_anchor = '''        private double CalculateVolume(double slPips)
        {
'''
    volume_method = '''        private double ResolveStopAnchor(PatternMatch match)
        {
            if (StopAnchorMode == StopAnchorModeKind.LegacyD)
                return match.D.Price;

            bool dIsInsideXa = match.Xd <= 1.0;
            return dIsInsideXa ? match.X.Price : match.D.Price;
        }

        private double CalculateVolume(double slPips)
        {
'''
    source = replace_once(source, volume_anchor, volume_method, "stop anchor resolver")

    enum_anchor = '''        public enum RiskSizingMode
        {
'''
    enum_block = '''        public enum StopAnchorModeKind
        {
            LegacyD,
            PatternInvalidation
        }

        public enum TargetRiskRewardPolicyKind
        {
            LegacyFallback,
            RejectPoorGeometry
        }

        public enum RiskSizingMode
        {
'''
    source = replace_once(source, enum_anchor, enum_block, "research enums")

    source_path.write_text(source, encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing Fibonacci-v0.3.0-fix3.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate the research candidate if it already exists.",
    )
    args = parser.parse_args()

    target = build_candidate(args.repo_root.resolve(), args.force)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
