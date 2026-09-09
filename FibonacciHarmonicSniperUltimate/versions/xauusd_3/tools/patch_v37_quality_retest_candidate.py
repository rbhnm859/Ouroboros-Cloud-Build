from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "FibonacciXAUUSD3.cs"
s = SRC.read_text()


def replace_once(old: str, new: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, got {count}: {old[:120]!r}")
    s = s.replace(old, new, 1)


replace_once(
    'Print("VERSION xauusd_3 v3.6.0-exit-resilience-candidate");',
    'Print("VERSION xauusd_3 v3.7.0-quality-retest-candidate");',
)

old = '''        [Parameter("Breakeven Lock R", DefaultValue = 0.05, MinValue = 0.0, MaxValue = 0.50, Group = "Exit")]
        public double BreakevenLockR { get; set; }
'''
new = old + '''
        [Parameter("Neutralize Generic Harmonic", DefaultValue = false, Group = "Quality")]
        public bool NeutralizeGenericHarmonic { get; set; }

        [Parameter("Recheck Spread At Entry", DefaultValue = false, Group = "Execution")]
        public bool RecheckSpreadAtEntry { get; set; }

        [Parameter("Max Arms Per Structure", DefaultValue = 1, MinValue = 1, MaxValue = 2, Group = "Execution")]
        public int MaxArmsPerStructure { get; set; }

        [Parameter("Use Actual M5 Rule Score", DefaultValue = false, Group = "Scoring")]
        public bool UseActualM5RuleScore { get; set; }
'''
replace_once(old, new)

old = '        private readonly Dictionary<long, double> _initialRiskPips = new Dictionary<long, double>();\n'
new = old + '        private readonly Dictionary<string, int> _armAttempts = new Dictionary<string, int>();\n'
replace_once(old, new)

replace_once(
    '''            string key = direction + "|" + start.Index + "|" + end.Index;
            if (_consumed.Contains(key))
                return;
''',
    '''            string key = direction + "|" + start.Index + "|" + end.Index;
            if (_consumed.Contains(key))
                return;
            int priorAttempts = 0;
            _armAttempts.TryGetValue(key, out priorAttempts);
            if (priorAttempts >= MaxArmsPerStructure)
                return;
''',
)

replace_once(
    '''            HarmonicInfo harmonic = HarmonicConfluence(pivots, zoneLow, zoneHigh, atr);
            double preScore = h1Score + fibScore + structureScore + harmonic.Score;
''',
    '''            HarmonicInfo harmonic = HarmonicConfluence(pivots, zoneLow, zoneHigh, atr);
            if (NeutralizeGenericHarmonic && harmonic.Tag == "Generic")
                harmonic = new HarmonicInfo(0.0, "Generic");
            double preScore = h1Score + fibScore + structureScore + harmonic.Score;
''',
)

replace_once(
    '''            _consumed.Add(key);
            string tag = harmonic.Score >= 12.0 ? "Hybrid-" + harmonic.Tag : "FibStructure";
''',
    '''            _armAttempts[key] = priorAttempts + 1;
            string tag = harmonic.Score >= 12.0 ? "Hybrid-" + harmonic.Tag : "FibStructure";
''',
)

replace_once(
    '            double m5Score = M5RulesNeeded * 5.0;\n',
    '            double m5Score = (UseActualM5RuleScore ? rules : M5RulesNeeded) * 5.0;\n',
)

replace_once(
    '''        private bool TryExecute(ArmedSetup a, double finalScore, int m5Index, int confirmRules)
        {
            if (BlockLondonEntries && Server.Time.Hour >= 7 && Server.Time.Hour < 13)
''',
    '''        private bool TryExecute(ArmedSetup a, double finalScore, int m5Index, int confirmRules)
        {
            if (RecheckSpreadAtEntry)
            {
                double liveSpreadRatio = (Symbol.Ask - Symbol.Bid) / Math.Max(a.M15Atr, Symbol.PipSize);
                if (liveSpreadRatio > MaxSpreadAtrRatio)
                {
                    if (DebugLogging) Print("[ENTRY SPREAD REJECT] ratio={0:F4} max={1:F4}", liveSpreadRatio, MaxSpreadAtrRatio);
                    return false;
                }
            }
            if (BlockLondonEntries && Server.Time.Hour >= 7 && Server.Time.Hour < 13)
''',
)

replace_once(
    '''                _tradesToday++;
                _lastTradeM5Index = m5Index;
''',
    '''                _consumed.Add(a.Key);
                _tradesToday++;
                _lastTradeM5Index = m5Index;
''',
)

SRC.write_text(s)
print(f"patched {SRC}")
