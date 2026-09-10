from pathlib import Path

path = Path('CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs')
s = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str):
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one match, found {count}')
    s = s.replace(old, new, 1)


replace_once(
'''        [Parameter("Max ATR", DefaultValue = 0.00200, MinValue = 0.0, Step = 0.00005, Group = "Filters")]
        public double MaxAtr { get; set; }
''',
'''        [Parameter("Max ATR", DefaultValue = 0.00200, MinValue = 0.0, Step = 0.00005, Group = "Filters")]
        public double MaxAtr { get; set; }

        [Parameter("Use Normalized ATR Filter", DefaultValue = false, Group = "Filters")]
        public bool UseNormalizedAtrFilter { get; set; }

        [Parameter("Min ATR Pips", DefaultValue = 0.5, MinValue = 0.0, Step = 0.1, Group = "Filters")]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR Pips", DefaultValue = 10.5, MinValue = 0.0, Step = 0.1, Group = "Filters")]
        public double MaxAtrPips { get; set; }

        [Parameter("Use Normalized Spread", DefaultValue = false, Group = "Execution")]
        public bool UseNormalizedSpreadFilter { get; set; }

        [Parameter("Max Spread Pips", DefaultValue = 1.8, MinValue = 0.0, Step = 0.1, Group = "Execution")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Max Spread/ATR Ratio", DefaultValue = 0.50, MinValue = 0.0, Step = 0.05, Group = "Execution")]
        public double MaxSpreadAtrRatio { get; set; }
''',
'normalised filter parameters')

replace_once(
'''                Print(Prefix + "invalid symbol: " + SymbolName + ". EURUSD prefix required.");
''',
'''                Print(Prefix + "invalid symbol: " + SymbolName + ". Set Allowed Symbol Prefix to the symbol prefix, or AUTO for EURUSD/GBPUSD/USDJPY/AUDUSD.");
''',
'OnStart symbol error')

replace_once(
'''        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            string current = SymbolName.ToUpperInvariant();
            return current.StartsWith(allowed);
        }
''',
'''        private bool ValidateSymbol()
        {
            string allowed = string.IsNullOrWhiteSpace(AllowedSymbolPrefix) ? "EURUSD" : AllowedSymbolPrefix.Trim().ToUpperInvariant();
            string current = SymbolName.ToUpperInvariant();

            if (allowed == "AUTO" || allowed == "*")
                return IsSupportedFxSymbol(current);

            return current.StartsWith(allowed);
        }

        private bool IsSupportedFxSymbol(string current)
        {
            return current.StartsWith("EURUSD") ||
                   current.StartsWith("GBPUSD") ||
                   current.StartsWith("USDJPY") ||
                   current.StartsWith("AUDUSD");
        }
''',
'multi FX symbol validation')

replace_once(
'''        private bool CheckSpreadDynamic()
        {
            int spread = SpreadInPoints();
            if (spread > MaxSpreadPoints) return false;
            double avg = AverageSpreadPoints();
            if (avg <= 0) return true;
            return spread <= avg * SpreadAvgMultiplier;
        }
''',
'''        private bool CheckSpreadDynamic()
        {
            if (IsAbsoluteSpreadTooHigh()) return false;

            if (UseNormalizedSpreadFilter)
            {
                double spreadPips = SpreadInPips();
                double avgPips = AverageSpreadPips();
                if (avgPips <= 0) return true;
                return spreadPips <= avgPips * SpreadAvgMultiplier;
            }

            int spread = SpreadInPoints();
            double avg = AverageSpreadPoints();
            if (avg <= 0) return true;
            return spread <= avg * SpreadAvgMultiplier;
        }
''',
'normalised dynamic spread')

replace_once(
'''            if (SpreadInPoints() > MaxSpreadPoints) { reason = "spread_too_high"; return false; }
''',
'''            if (IsAbsoluteSpreadTooHigh()) { reason = "spread_too_high"; return false; }
''',
'guard spread normalisation')

replace_once(
'''            double atr = ClosedAtr();
            if (atr <= 0) { reason = "atr_not_ready"; return false; }
            if (atr < MinAtr) { reason = "atr_too_low"; return false; }
            if (MaxAtr > 0 && atr > MaxAtr) { reason = "atr_too_high"; return false; }

            return true;
''',
'''            double atr = ClosedAtr();
            if (atr <= 0) { reason = "atr_not_ready"; return false; }

            if (UseNormalizedAtrFilter)
            {
                double atrPips = PriceDistanceToPips(atr);
                if (atrPips < MinAtrPips) { reason = "atr_pips_too_low"; return false; }
                if (MaxAtrPips > 0 && atrPips > MaxAtrPips) { reason = "atr_pips_too_high"; return false; }
            }
            else
            {
                if (atr < MinAtr) { reason = "atr_too_low"; return false; }
                if (MaxAtr > 0 && atr > MaxAtr) { reason = "atr_too_high"; return false; }
            }

            return true;
''',
'guard ATR normalisation')

replace_once(
'''        private int SpreadInPoints()
        {
            return (int)Math.Round(Symbol.Spread / Symbol.TickSize);
        }

        private double AverageSpreadPoints()
''',
'''        private bool IsAbsoluteSpreadTooHigh()
        {
            if (!UseNormalizedSpreadFilter)
                return SpreadInPoints() > MaxSpreadPoints;

            double spreadPips = SpreadInPips();
            if (MaxSpreadPips > 0 && spreadPips > MaxSpreadPips)
                return true;

            double atr = ClosedAtr();
            double atrPips = atr > 0 ? PriceDistanceToPips(atr) : 0;
            if (MaxSpreadAtrRatio > 0 && atrPips > 0 && spreadPips / atrPips > MaxSpreadAtrRatio)
                return true;

            return false;
        }

        private int SpreadInPoints()
        {
            return Symbol.TickSize > 0 ? (int)Math.Round(Symbol.Spread / Symbol.TickSize) : 0;
        }

        private double SpreadInPips()
        {
            return Symbol.PipSize > 0 ? Symbol.Spread / Symbol.PipSize : 0;
        }

        private double AverageSpreadPips()
        {
            if (Symbol.PipSize <= 0 || Symbol.TickSize <= 0) return 0;
            return AverageSpreadPoints() * Symbol.TickSize / Symbol.PipSize;
        }

        private double AverageSpreadPoints()
''',
'spread helper methods')

replace_once(
'''            Debug("started on " + SymbolName + " " + TimeFrame + " label=" + TradeLabel + " htf=" + htf + " runner=" + UseRunnerExit + " sessionQuality=" + UseSessionQualityFilter);
''',
'''            Debug("started on " + SymbolName + " " + TimeFrame + " label=" + TradeLabel + " htf=" + htf + " runner=" + UseRunnerExit + " sessionQuality=" + UseSessionQualityFilter + " normATR=" + UseNormalizedAtrFilter + " normSpread=" + UseNormalizedSpreadFilter);
''',
'start diagnostic')

# Make the session-quality spread gate respect normalised pips when enabled.
replace_once(
'''                int maxSpread = Math.Max(1, MaxSpreadPoints - tier * 2);

                if (Math.Abs(cumulativeDelta) < requiredDelta)
''',
'''                int maxSpread = Math.Max(1, MaxSpreadPoints - tier * 2);
                double maxSpreadPips = Math.Max(0.1, MaxSpreadPips - tier * 0.2);

                if (Math.Abs(cumulativeDelta) < requiredDelta)
''',
'session quality spread setup')

replace_once(
'''                if (SpreadInPoints() > maxSpread)
                {
                    Debug("quality blocked spread tier=" + tier + " spread=" + SpreadInPoints() + " max=" + maxSpread);
                    return 0;
                }
''',
'''                if ((!UseNormalizedSpreadFilter && SpreadInPoints() > maxSpread) ||
                    (UseNormalizedSpreadFilter && SpreadInPips() > maxSpreadPips))
                {
                    Debug("quality blocked spread tier=" + tier + " spreadPoints=" + SpreadInPoints() + " spreadPips=" + SpreadInPips().ToString("F2"));
                    return 0;
                }
''',
'session quality normalised spread gate')

path.write_text(s, encoding='utf-8')
print('Candidate P multi-FX normalisation refactor applied successfully.')
