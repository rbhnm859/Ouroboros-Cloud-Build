#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.10.0-btc-round8-excursion"
TARGET_VERSION = "Fibonacci-v0.10.1-btc-round8-exit"
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
    s = p.read_text(encoding='utf-8')
    s = replace_once(s,
        'Print("VERSION v0.10.0-btc-round8-excursion");',
        'Print("VERSION v0.10.1-btc-round8-exit");',
        'version marker')

    param_anchor = '''        [Parameter("R8 Log MFE MAE", DefaultValue = true, Group = "BTC Round8 Excursion")]
        public bool Round8LogExcursions { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("R8 Enable Breakeven", DefaultValue = false, Group = "BTC Round8 Exit")]
        public bool Round8EnableBreakeven { get; set; }

        [Parameter("R8 BE Trigger R", DefaultValue = 0.75, MinValue = 0.10, MaxValue = 3.0, Step = 0.05, Group = "BTC Round8 Exit")]
        public double Round8BreakevenTriggerR { get; set; }

        [Parameter("R8 BE Apply Buy", DefaultValue = true, Group = "BTC Round8 Exit")]
        public bool Round8BreakevenBuy { get; set; }

        [Parameter("R8 BE Apply Sell", DefaultValue = true, Group = "BTC Round8 Exit")]
        public bool Round8BreakevenSell { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'exit parameters')

    field_anchor = '''        private readonly Dictionary<long, double> _round8MaePips = new Dictionary<long, double>();
'''
    field_block = field_anchor + '''        private readonly HashSet<long> _round8BreakevenApplied = new HashSet<long>();
'''
    s = replace_once(s, field_anchor, field_block, 'exit state')

    tick_anchor = '''                double oldMae;
                if (!_round8MaePips.TryGetValue(p.Id, out oldMae) || adverse > oldMae)
                    _round8MaePips[p.Id] = adverse;
            }
        }
'''
    tick_block = '''                double oldMae;
                if (!_round8MaePips.TryGetValue(p.Id, out oldMae) || adverse > oldMae)
                    _round8MaePips[p.Id] = adverse;

                if (Round8EnableBreakeven && !_round8BreakevenApplied.Contains(p.Id))
                {
                    bool directionEnabled = p.TradeType == TradeType.Buy ? Round8BreakevenBuy : Round8BreakevenSell;
                    double riskPips;
                    if (directionEnabled && _round8InitialRiskPips.TryGetValue(p.Id, out riskPips) && riskPips > 0 && favourable >= riskPips * Round8BreakevenTriggerR)
                    {
                        bool improves = !p.StopLoss.HasValue ||
                            (p.TradeType == TradeType.Buy && p.EntryPrice > p.StopLoss.Value) ||
                            (p.TradeType == TradeType.Sell && p.EntryPrice < p.StopLoss.Value);
                        if (improves)
                        {
                            var modify = ModifyPosition(p, p.EntryPrice, p.TakeProfit, ProtectionType.Absolute);
                            if (modify.IsSuccessful)
                            {
                                _round8BreakevenApplied.Add(p.Id);
                                if (DebugLogging)
                                    Print("[R8 BE] id={0} dir={1} triggerR={2:F2} entry={3}", p.Id, p.TradeType, Round8BreakevenTriggerR, p.EntryPrice);
                            }
                            else if (DebugLogging)
                                Print("[R8 BE FAIL] id={0} error={1}", p.Id, modify.Error);
                        }
                    }
                }
            }
        }
'''
    s = replace_once(s, tick_anchor, tick_block, 'breakeven tick logic')

    close_anchor = '''            _round8MaePips.Remove(p.Id);

            if (DebugLogging)
'''
    close_block = '''            _round8MaePips.Remove(p.Id);
            _round8BreakevenApplied.Remove(p.Id);

            if (DebugLogging)
'''
    s = replace_once(s, close_anchor, close_block, 'breakeven cleanup')

    startup_anchor = '''            Print("BTC Round8 Excursion | LogMFE/MAE={0} | execution-only instrumentation; trading logic unchanged", Round8LogExcursions);
'''
    startup_block = startup_anchor + '''            Print("BTC Round8 Exit | BE={0} triggerR={1:F2} buy={2} sell={3}", Round8EnableBreakeven, Round8BreakevenTriggerR, Round8BreakevenBuy, Round8BreakevenSell);
'''
    s = replace_once(s, startup_anchor, startup_block, 'exit startup')

    p.write_text(s, encoding='utf-8')
    csproj = target / 'FibonacciHarmonicSniperUltimate.csproj'
    if csproj.is_file():
        text = csproj.read_text(encoding='utf-8')
        text = text.replace('<Version>0.10.0-btc-round8-excursion</Version>', '<Version>0.10.1-btc-round8-exit</Version>')
        csproj.write_text(text, encoding='utf-8')
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
