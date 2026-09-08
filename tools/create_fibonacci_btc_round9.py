#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.10.0-btc-round8-excursion"
TARGET_VERSION = "Fibonacci-v0.11.0-btc-round9-shadow"
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
        'Print("VERSION v0.10.0-btc-round8-excursion");',
        'Print("VERSION v0.11.0-btc-round9-shadow");',
        'version marker',
    )

    param_anchor = '''        [Parameter("R8 Log MFE MAE", DefaultValue = true, Group = "BTC Round8 Excursion")]
        public bool Round8LogExcursions { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("R9 Shadow TP Continuation", DefaultValue = true, Group = "BTC Round9 Shadow")]
        public bool Round9ShadowTpContinuation { get; set; }

        [Parameter("R9 Shadow Horizon Hours", DefaultValue = 48, MinValue = 6, MaxValue = 96, Group = "BTC Round9 Shadow")]
        public int Round9ShadowHorizonHours { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'round9 parameters')

    fields_anchor = '''        private readonly Dictionary<long, double> _round8MaePips = new Dictionary<long, double>();
'''
    fields_block = fields_anchor + '''        private sealed class Round9ShadowState
        {
            public long PositionId;
            public TradeType Direction;
            public string Pattern;
            public double EntryPrice;
            public double RiskPips;
            public DateTime ExitTime;
            public double Max6R;
            public double Max12R;
            public double Max24R;
            public double Max48R;
            public double MinPostExitR = double.PositiveInfinity;
            public double Hit20Min = -1;
            public double Hit22Min = -1;
            public double Hit25Min = -1;
        }

        private readonly List<Round9ShadowState> _round9Shadows = new List<Round9ShadowState>();
'''
    s = replace_once(s, fields_anchor, fields_block, 'round9 fields')

    tick_anchor = '''        protected override void OnTick()
        {
            if (!Round8LogExcursions)
                return;

            foreach (var p in Positions)
'''
    tick_block = '''        protected override void OnTick()
        {
            if (Round9ShadowTpContinuation)
                UpdateRound9Shadows();

            if (!Round8LogExcursions)
                return;

            foreach (var p in Positions)
'''
    s = replace_once(s, tick_anchor, tick_block, 'round9 tick hook')

    bar_anchor = '''        protected override void OnBarClosed()
'''
    methods = '''        private void UpdateRound9Shadows()
        {
            if (_round9Shadows.Count == 0)
                return;

            for (int i = _round9Shadows.Count - 1; i >= 0; i--)
            {
                var sh = _round9Shadows[i];
                double elapsedMin = Math.Max(0.0, (Server.Time - sh.ExitTime).TotalMinutes);
                double closePrice = sh.Direction == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
                double signedPips = sh.Direction == TradeType.Buy
                    ? (closePrice - sh.EntryPrice) / Symbol.PipSize
                    : (sh.EntryPrice - closePrice) / Symbol.PipSize;
                double r = sh.RiskPips > 0 ? signedPips / sh.RiskPips : 0.0;

                if (elapsedMin <= 360.0 && r > sh.Max6R) sh.Max6R = r;
                if (elapsedMin <= 720.0 && r > sh.Max12R) sh.Max12R = r;
                if (elapsedMin <= 1440.0 && r > sh.Max24R) sh.Max24R = r;
                if (elapsedMin <= 2880.0 && r > sh.Max48R) sh.Max48R = r;
                if (r < sh.MinPostExitR) sh.MinPostExitR = r;

                if (sh.Hit20Min < 0 && r >= 2.0) sh.Hit20Min = elapsedMin;
                if (sh.Hit22Min < 0 && r >= 2.2) sh.Hit22Min = elapsedMin;
                if (sh.Hit25Min < 0 && r >= 2.5) sh.Hit25Min = elapsedMin;

                double horizonMin = Math.Max(360.0, Round9ShadowHorizonHours * 60.0);
                if (elapsedMin >= horizonMin)
                {
                    Print("[R9 SHADOW] id={0} dir={1} pattern={2} riskPips={3:F4} max6R={4:F4} max12R={5:F4} max24R={6:F4} max48R={7:F4} minPostR={8:F4} hit20Min={9:F1} hit22Min={10:F1} hit25Min={11:F1} horizonH={12}",
                        sh.PositionId, sh.Direction, sh.Pattern.Replace(" ", "_"), sh.RiskPips,
                        sh.Max6R, sh.Max12R, sh.Max24R, sh.Max48R,
                        double.IsPositiveInfinity(sh.MinPostExitR) ? 0.0 : sh.MinPostExitR,
                        sh.Hit20Min, sh.Hit22Min, sh.Hit25Min, Round9ShadowHorizonHours);
                    _round9Shadows.RemoveAt(i);
                }
            }
        }

        private void FlushRound9Shadows()
        {
            foreach (var sh in _round9Shadows)
            {
                double elapsedMin = Math.Max(0.0, (Server.Time - sh.ExitTime).TotalMinutes);
                Print("[R9 SHADOW PARTIAL] id={0} dir={1} pattern={2} riskPips={3:F4} max6R={4:F4} max12R={5:F4} max24R={6:F4} max48R={7:F4} minPostR={8:F4} hit20Min={9:F1} hit22Min={10:F1} hit25Min={11:F1} elapsedMin={12:F1}",
                    sh.PositionId, sh.Direction, sh.Pattern.Replace(" ", "_"), sh.RiskPips,
                    sh.Max6R, sh.Max12R, sh.Max24R, sh.Max48R,
                    double.IsPositiveInfinity(sh.MinPostExitR) ? 0.0 : sh.MinPostExitR,
                    sh.Hit20Min, sh.Hit22Min, sh.Hit25Min, elapsedMin);
            }
        }

        protected override void OnBarClosed()
'''
    s = replace_once(s, bar_anchor, methods, 'round9 methods')

    close_insertion_anchor = '''            if (Round8LogExcursions && initialRiskPips > 0)
            {
'''
    close_insertion = '''            if (Round9ShadowTpContinuation && initialRiskPips > 0 && args.Reason.ToString() == "TakeProfit")
            {
                _round9Shadows.Add(new Round9ShadowState
                {
                    PositionId = p.Id,
                    Direction = p.TradeType,
                    Pattern = name,
                    EntryPrice = p.EntryPrice,
                    RiskPips = initialRiskPips,
                    ExitTime = Server.Time,
                    Max6R = Math.Max(0.0, p.Pips / initialRiskPips),
                    Max12R = Math.Max(0.0, p.Pips / initialRiskPips),
                    Max24R = Math.Max(0.0, p.Pips / initialRiskPips),
                    Max48R = Math.Max(0.0, p.Pips / initialRiskPips)
                });
                Print("[R9 SHADOW START] id={0} dir={1} pattern={2} exitR={3:F4} horizonH={4}", p.Id, p.TradeType, name.Replace(" ", "_"), p.Pips / initialRiskPips, Round9ShadowHorizonHours);
            }

            if (Round8LogExcursions && initialRiskPips > 0)
            {
'''
    s = replace_once(s, close_insertion_anchor, close_insertion, 'round9 shadow start')

    stop_anchor = '''            Print("[ROUND7 STATS] buyPass={0} sellAccepted={1} sellVetoed={2}", _round7BuyPassthroughCount, _round7SellAcceptedCount, _round7SellVetoedCount);
'''
    stop_block = '''            FlushRound9Shadows();
''' + stop_anchor
    s = replace_once(s, stop_anchor, stop_block, 'round9 flush')

    startup_anchor = '''            Print("BTC Round8 Excursion | LogMFE/MAE={0} | execution-only instrumentation; trading logic unchanged", Round8LogExcursions);
'''
    startup_block = startup_anchor + '''            Print("BTC Round9 Shadow | enabled={0} | horizon={1}h | observes TP continuation only; no shadow orders", Round9ShadowTpContinuation, Round9ShadowHorizonHours);
'''
    s = replace_once(s, startup_anchor, startup_block, 'round9 startup')

    p.write_text(s, encoding="utf-8")

    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.10.0-btc-round8-excursion</Version>', '<Version>0.11.0-btc-round9-shadow</Version>')
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
