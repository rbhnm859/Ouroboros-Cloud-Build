#!/usr/bin/env python3
"""Apply Ouroboros V2.2 universal-symbol, daily-ROI and cash-risk fixes."""

from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_universal_daily_roi.py PATH_TO_OUROBOROS_CS")

    path = Path(sys.argv[1])
    text = path.read_text()

    def replace_once(old: str, new: str, label: str) -> None:
        nonlocal text
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{label}: expected exactly one match, found {count}")
        text = text.replace(old, new, 1)

    # Route broker-specific CFDs (indices, energy, equities, etc.) through a
    # generic current-symbol grid instead of rejecting them as unknown.
    replace_once(
        "        Forex,\n        Metals,\n        Crypto\n",
        "        Forex,\n        Metals,\n        Crypto,\n        Generic\n",
        "generic market enum",
    )
    replace_once(
        '            return OuroborosMarket.Auto; // Auto is also used as "unknown" internally.',
        "            return OuroborosMarket.Generic;",
        "generic market detection",
    )
    replace_once(
        "            if (market == OuroborosMarket.Forex)\n                return ExtractForexPair(n);",
        "            if (market == OuroborosMarket.Generic)\n"
        "                return n;\n\n"
        "            if (market == OuroborosMarket.Forex)\n"
        "                return ExtractForexPair(n);",
        "generic canonical symbol",
    )

    generic_cells_anchor = """                else if (market == OuroborosMarket.Crypto)
                {
                    AddUniversalCell(result, seen, "hydra", actualName, TimeFrame.Minute, "mamba_reversion");
                    AddUniversalCell(result, seen, "viper", actualName, TimeFrame.Minute5, "momentum_hunter");
                    AddUniversalCell(result, seen, "mamba", actualName, TimeFrame.Minute15, "mamba_reversion");
                    AddUniversalCell(result, seen, "cobra", actualName, TimeFrame.Hour, "trend_follower");
                }
"""
    replace_once(
        generic_cells_anchor,
        generic_cells_anchor
        + """                else if (market == OuroborosMarket.Generic)
                {
                    AddUniversalCell(result, seen, "hydra", actualName, TimeFrame.Minute, "mamba_reversion");
                    AddUniversalCell(result, seen, "viper", actualName, TimeFrame.Minute5, "momentum_hunter");
                    AddUniversalCell(result, seen, "mamba", actualName, TimeFrame.Minute15, "mamba_reversion");
                    AddUniversalCell(result, seen, "taipan", actualName, TimeFrame.Minute30, "session_analyst");
                    AddUniversalCell(result, seen, "cobra", actualName, TimeFrame.Hour, "trend_follower");
                }
""",
        "generic strategy grid",
    )

    # Higher-activity default. Exposure remains bounded and never uses grid or
    # martingale sizing.
    replace_once(
        '[Parameter("Preset", DefaultValue = OuroborosPreset.MobileSafe, Group = "General")]',
        '[Parameter("Preset", DefaultValue = OuroborosPreset.Balanced, Group = "General")]',
        "balanced default",
    )
    replace_once(
        '[Parameter("Min trade quality (0=off)", DefaultValue = 62.0,',
        '[Parameter("Min trade quality (0=off)", DefaultValue = 58.0,',
        "quality threshold",
    )
    text = text.replace('min confidence", DefaultValue = 0.65', 'min confidence", DefaultValue = 0.60')
    replace_once("Preset == OuroborosPreset.Balanced ? 0.50", "Preset == OuroborosPreset.Balanced ? 0.75", "balanced base risk")
    replace_once("Preset == OuroborosPreset.Balanced ? 1.00", "Preset == OuroborosPreset.Balanced ? 1.25", "balanced trade cap")
    replace_once("Preset == OuroborosPreset.Balanced ? 2.00", "Preset == OuroborosPreset.Balanced ? 2.50", "balanced portfolio cap")
    replace_once("Preset == OuroborosPreset.Balanced ? 3.50", "Preset == OuroborosPreset.Balanced ? 4.00", "balanced daily DD")
    replace_once("Preset == OuroborosPreset.Balanced ? 4.00", "Preset == OuroborosPreset.Balanced ? 4.50", "balanced flatten DD")
    replace_once("Preset == OuroborosPreset.Balanced ? 6.00", "Preset == OuroborosPreset.Balanced ? 8.00", "balanced total DD")
    replace_once("Preset == OuroborosPreset.Balanced ? 12", "Preset == OuroborosPreset.Balanced ? 24", "balanced daily trades")
    replace_once("Preset == OuroborosPreset.Balanced ? 10", "Preset == OuroborosPreset.Balanced ? 3", "balanced cooldown")
    replace_once("Preset == OuroborosPreset.Balanced ? 0.90", "Preset == OuroborosPreset.Balanced ? 1.10", "balanced minimum RR")
    replace_once("Preset == OuroborosPreset.Balanced ? 20.0", "Preset == OuroborosPreset.Balanced ? 15.0", "balanced spread ATR")
    replace_once(
        "if (qualityScore < 70.0) return 0.60;\n            if (qualityScore < 80.0) return 0.80;",
        "if (qualityScore < 70.0) return 0.75;\n            if (qualityScore < 80.0) return 0.90;",
        "quality risk curve",
    )

    # Derive cash risk from TickSize/TickValue. This avoids the metal/CFD
    # conversion mismatch observed in cTrader's convenience risk helpers.
    replace_once(
        "            double volume = sym.VolumeForFixedRisk(desiredRiskUsd, slPips, RoundingMode.Down);",
        "            double volume = UniversalVolumeForRisk(sym, desiredRiskUsd, slPips);",
        "initial universal sizing",
    )
    replace_once(
        "            double actualRiskUsd = sym.AmountRisked(volume, slPips);",
        "            double actualRiskUsd = UniversalAmountRisked(sym, volume, slPips);",
        "initial universal risk",
    )
    replace_once(
        "                volume = sym.VolumeForFixedRisk(hardTradeCap, slPips, RoundingMode.Down);",
        "                volume = UniversalVolumeForRisk(sym, hardTradeCap, slPips);",
        "defensive universal sizing",
    )
    replace_once(
        "                actualRiskUsd = sym.AmountRisked(volume, slPips);",
        "                actualRiskUsd = UniversalAmountRisked(sym, volume, slPips);",
        "defensive universal risk",
    )
    replace_once(
        "                risk += sym.AmountRisked(p.VolumeInUnits, slPips);",
        "                risk += UniversalAmountRisked(sym, p.VolumeInUnits, slPips);",
        "portfolio universal risk",
    )

    risk_anchor = """        private double CurrentOpenRiskUsd()
        {
"""
    risk_helpers = """        private double UniversalRiskPerUnit(Symbol sym, double slPips)
        {
            if (sym == null || slPips <= 0) return 0.0;
            double priceDistance = slPips * sym.PipSize;
            if (sym.TickSize > 0 && sym.TickValue > 0)
                return priceDistance / sym.TickSize * sym.TickValue;
            if (sym.PipValue > 0)
                return slPips * sym.PipValue;
            return 0.0;
        }

        private double UniversalVolumeForRisk(Symbol sym, double cashRisk, double slPips)
        {
            double perUnit = UniversalRiskPerUnit(sym, slPips);
            if (perUnit > 0 && !double.IsNaN(perUnit) && !double.IsInfinity(perUnit))
                return cashRisk / perUnit;
            return sym.VolumeForFixedRisk(cashRisk, slPips, RoundingMode.Down);
        }

        private double UniversalAmountRisked(Symbol sym, double volume, double slPips)
        {
            double perUnit = UniversalRiskPerUnit(sym, slPips);
            if (perUnit > 0 && !double.IsNaN(perUnit) && !double.IsInfinity(perUnit))
                return volume * perUnit;
            return sym.AmountRisked(volume, slPips);
        }

"""
    replace_once(risk_anchor, risk_helpers + risk_anchor, "universal risk helpers")

    post_fill = """            if (!EnsureInitialProtection(pos, sym, slPips, tpPips))
                return;

            double initialRiskDistance = Math.Abs(pos.EntryPrice - pos.StopLoss.Value);
"""
    post_fill_new = """            if (!EnsureInitialProtection(pos, sym, slPips, tpPips))
                return;

            double attachedSlPips = Math.Abs(pos.EntryPrice - pos.StopLoss.Value) / sym.PipSize;
            double attachedRiskUsd = UniversalAmountRisked(sym, pos.VolumeInUnits, attachedSlPips);
            if (attachedRiskUsd > hardTradeCap * 1.05)
            {
                Print("[OuroborosADV] RISK GUARD CLOSE {0}: attached risk {1:F2} > cap {2:F2} {3}",
                    pos.Id, attachedRiskUsd, hardTradeCap, Account.Asset.Name);
                ClosePosition(pos);
                return;
            }

            actualRiskUsd = attachedRiskUsd;
            double initialRiskDistance = Math.Abs(pos.EntryPrice - pos.StopLoss.Value);
"""
    replace_once(post_fill, post_fill_new, "post-fill risk guard")

    # Trail the day's equity high instead of imposing a fixed profit ceiling.
    profit_params = """        [Parameter("Flatten on daily profit lock", DefaultValue = false, Group = "Protection")]
        public bool FlattenOnDailyProfitLock { get; set; }
"""
    profit_params_new = profit_params + """
        [Parameter("Daily trail activation %", DefaultValue = 1.50, MinValue = 0.0, MaxValue = 100.0, Group = "Protection")]
        public double DailyTrailActivationPct { get; set; }

        [Parameter("Daily profit giveback %", DefaultValue = 0.75, MinValue = 0.10, MaxValue = 100.0, Group = "Protection")]
        public double DailyProfitGivebackPct { get; set; }
"""
    replace_once(profit_params, profit_params_new, "daily trailing parameters")

    tick_anchor = """            ManageOpenPositions();
        }
"""
    tick_new = """            double dayHighProfitPct = _dayStartEquity > 0
                ? 100.0 * (_dayHighEquity - _dayStartEquity) / _dayStartEquity : 0.0;
            double dayProfitGivebackPct = _dayStartEquity > 0
                ? 100.0 * (_dayHighEquity - Account.Equity) / _dayStartEquity : 0.0;
            if (DailyTrailActivationPct > 0 && DailyProfitGivebackPct > 0 &&
                dayHighProfitPct >= DailyTrailActivationPct && dayProfitGivebackPct >= DailyProfitGivebackPct)
            {
                _haltToday = true;
                FlattenAll(string.Format("daily profit trail high={0:F2}% giveback={1:F2}%",
                    dayHighProfitPct, dayProfitGivebackPct));
                return;
            }

            ManageOpenPositions();
        }
"""
    replace_once(tick_anchor, tick_new, "daily profit trailing")

    path.write_text(text)
    print(f"Applied universal daily ROI patch to {path}")


if __name__ == "__main__":
    main()
