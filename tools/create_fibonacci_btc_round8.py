#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.9.0-btc-round7-inverse-veto"
TARGET_VERSION = "Fibonacci-v0.10.0-btc-round8-excursion"
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
        'Print("VERSION v0.9.0-btc-round7-inverse-veto");',
        'Print("VERSION v0.10.0-btc-round8-excursion");',
        'version marker',
    )

    param_anchor = '''        [Parameter("R7 Log Vetoed Sell", DefaultValue = true, Group = "BTC Round7 Inverse Veto")]
        public bool Round7LogVetoedSell { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("R8 Log MFE MAE", DefaultValue = true, Group = "BTC Round8 Excursion")]
        public bool Round8LogExcursions { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'round8 parameter')

    fields_anchor = '''        private readonly Dictionary<long, string> _positionPattern = new Dictionary<long, string>();
'''
    fields_block = fields_anchor + '''        private readonly Dictionary<long, double> _round8InitialRiskPips = new Dictionary<long, double>();
        private readonly Dictionary<long, double> _round8InitialTpPips = new Dictionary<long, double>();
        private readonly Dictionary<long, double> _round8MfePips = new Dictionary<long, double>();
        private readonly Dictionary<long, double> _round8MaePips = new Dictionary<long, double>();
'''
    s = replace_once(s, fields_anchor, fields_block, 'round8 dictionaries')

    bar_anchor = '''        protected override void OnBarClosed()
'''
    tick_method = '''        protected override void OnTick()
        {
            if (!Round8LogExcursions)
                return;

            foreach (var p in Positions)
            {
                if (p.Label != BotLabel || p.SymbolName != SymbolName)
                    continue;

                double favourable = p.TradeType == TradeType.Buy
                    ? (Symbol.Bid - p.EntryPrice) / Symbol.PipSize
                    : (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                double adverse = p.TradeType == TradeType.Buy
                    ? (p.EntryPrice - Symbol.Bid) / Symbol.PipSize
                    : (Symbol.Ask - p.EntryPrice) / Symbol.PipSize;

                if (double.IsNaN(favourable) || double.IsInfinity(favourable) ||
                    double.IsNaN(adverse) || double.IsInfinity(adverse))
                    continue;

                favourable = Math.Max(0.0, favourable);
                adverse = Math.Max(0.0, adverse);

                double oldMfe;
                if (!_round8MfePips.TryGetValue(p.Id, out oldMfe) || favourable > oldMfe)
                    _round8MfePips[p.Id] = favourable;

                double oldMae;
                if (!_round8MaePips.TryGetValue(p.Id, out oldMae) || adverse > oldMae)
                    _round8MaePips[p.Id] = adverse;
            }
        }

        protected override void OnBarClosed()
'''
    s = replace_once(s, bar_anchor, tick_method, 'round8 tick tracker')

    open_anchor = '''            _positionPattern[result.Position.Id] = m.Definition.Name;
'''
    open_block = open_anchor + '''            _round8InitialRiskPips[result.Position.Id] = slPips;
            _round8InitialTpPips[result.Position.Id] = tpPips;
            _round8MfePips[result.Position.Id] = 0.0;
            _round8MaePips[result.Position.Id] = 0.0;
'''
    s = replace_once(s, open_anchor, open_block, 'round8 open tracking')

    close_anchor = '''            _positionPattern.Remove(p.Id);

            if (DebugLogging)
                Print("[CLOSE] {0} net={1:F2} reason={2}", name, p.NetProfit, args.Reason);
'''
    close_block = '''            double initialRiskPips = 0.0;
            double initialTpPips = 0.0;
            double mfePips = 0.0;
            double maePips = 0.0;
            _round8InitialRiskPips.TryGetValue(p.Id, out initialRiskPips);
            _round8InitialTpPips.TryGetValue(p.Id, out initialTpPips);
            _round8MfePips.TryGetValue(p.Id, out mfePips);
            _round8MaePips.TryGetValue(p.Id, out maePips);

            if (Round8LogExcursions && initialRiskPips > 0)
            {
                double mfeR = mfePips / initialRiskPips;
                double maeR = maePips / initialRiskPips;
                double finalR = p.Pips / initialRiskPips;
                double targetR = initialTpPips / initialRiskPips;
                double durationMin = Math.Max(0.0, (Server.Time - p.EntryTime).TotalMinutes);
                Print("[R8 EXCURSION] id={0} dir={1} pattern={2} riskPips={3:F4} targetR={4:F4} mfeR={5:F4} maeR={6:F4} finalR={7:F4} net={8:F2} durationMin={9:F1} reason={10}",
                    p.Id, p.TradeType, name.Replace(" ", "_"), initialRiskPips, targetR, mfeR, maeR, finalR, p.NetProfit, durationMin, args.Reason);
            }

            _positionPattern.Remove(p.Id);
            _round8InitialRiskPips.Remove(p.Id);
            _round8InitialTpPips.Remove(p.Id);
            _round8MfePips.Remove(p.Id);
            _round8MaePips.Remove(p.Id);

            if (DebugLogging)
                Print("[CLOSE] {0} net={1:F2} reason={2}", name, p.NetProfit, args.Reason);
'''
    s = replace_once(s, close_anchor, close_block, 'round8 close log')

    startup_anchor = '''            Print("BTC Round7 Inverse Veto | M30 Sell Veto={0} | M30Patterns={1} | M30MaxAge={2}",
                Round7VetoM30SellAlignment, M30Patterns, M30StateMaxAge);
'''
    startup_block = startup_anchor + '''            Print("BTC Round8 Excursion | LogMFE/MAE={0} | execution-only instrumentation; trading logic unchanged", Round8LogExcursions);
'''
    s = replace_once(s, startup_anchor, startup_block, 'round8 startup')

    p.write_text(s, encoding="utf-8")

    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.9.0-btc-round7-inverse-veto</Version>', '<Version>0.10.0-btc-round8-excursion</Version>')
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
