from pathlib import Path

p = Path('CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs')
s = p.read_text(encoding='utf-8')

def repl(old, new, name):
    global s
    if old not in s:
        raise SystemExit(f'patch anchor not found: {name}')
    s = s.replace(old, new, 1)

repl('''        [Parameter("TP Multiplier ATR", DefaultValue = 0.4, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double TpAtrMultiplier { get; set; }

        [Parameter("Hard Actual Loss Cap", DefaultValue = false, Group = "Risk")]
''', '''        [Parameter("TP Multiplier ATR", DefaultValue = 0.4, MinValue = 0.1, Step = 0.1, Group = "Risk")]
        public double TpAtrMultiplier { get; set; }

        [Parameter("Use Adaptive Risk/Reward", DefaultValue = true, Group = "Risk")]
        public bool UseAdaptiveRiskReward { get; set; }

        [Parameter("Base Planned R:R", DefaultValue = 1.25, MinValue = 0.5, MaxValue = 5.0, Step = 0.05, Group = "Risk")]
        public double BasePlannedRiskReward { get; set; }

        [Parameter("High Quality R:R", DefaultValue = 1.80, MinValue = 0.5, MaxValue = 8.0, Step = 0.05, Group = "Risk")]
        public double HighQualityRiskReward { get; set; }

        [Parameter("High Quality Confirmations", DefaultValue = 4, MinValue = 3, MaxValue = 5, Group = "Risk")]
        public int HighQualityConfirmations { get; set; }

        [Parameter("High Quality Delta Multiple", DefaultValue = 1.35, MinValue = 1.0, MaxValue = 3.0, Step = 0.05, Group = "Risk")]
        public double HighQualityDeltaMultiple { get; set; }

        [Parameter("Risk Budget Buffer %", DefaultValue = 15.0, MinValue = 0.0, MaxValue = 50.0, Step = 1.0, Group = "Risk")]
        public double RiskBudgetBufferPercent { get; set; }

        [Parameter("Hard Actual Loss Cap", DefaultValue = false, Group = "Risk")]
''', 'risk parameters')

repl('''        private double _openInitialRiskPips;

        private DateTime _currentDay = DateTime.MinValue;
''', '''        private double _openInitialRiskPips;
        private int _lastSignalConfirmations;
        private int _lastSignalDelta;

        private DateTime _currentDay = DateTime.MinValue;
''', 'signal quality fields')

repl('''            Debug("signal=" + signal + " confirmations=" + confirmations + "/5 need=" + requiredConfirmations + " delta=" + cumulativeDelta);
            return confirmations >= requiredConfirmations ? signal : 0;
''', '''            bool accepted = confirmations >= requiredConfirmations;
            if (accepted)
            {
                _lastSignalConfirmations = confirmations;
                _lastSignalDelta = cumulativeDelta;
            }

            Debug("signal=" + signal + " confirmations=" + confirmations + "/5 need=" + requiredConfirmations + " delta=" + cumulativeDelta + " accepted=" + accepted);
            return accepted ? signal : 0;
''', 'signal quality capture')

repl('''        private void OpenTrade(int signal)
        {
            double slPips = PriceDistanceToPips(ClosedAtr() * SlAtrMultiplier);
            double tpPips = UseRunnerExit ? slPips * Math.Max(1.0, EmergencyTpR) : PriceDistanceToPips(ClosedAtr() * TpAtrMultiplier);
''', '''        private void OpenTrade(int signal)
        {
            double atrPips = PriceDistanceToPips(ClosedAtr());
            double slPips = atrPips * SlAtrMultiplier;
            double plannedRiskReward = ResolvePlannedRiskReward();
            double tpPips = UseRunnerExit
                ? slPips * Math.Max(1.0, EmergencyTpR)
                : (UseAdaptiveRiskReward ? slPips * plannedRiskReward : atrPips * TpAtrMultiplier);
''', 'adaptive rr open trade')

repl('''            double riskMoney = CalculateRiskMoney();
            if (UseHardActualLossCap && MaxActualTradeLossMoney > 0 && riskMoney > MaxActualTradeLossMoney)
                riskMoney = MaxActualTradeLossMoney;
''', '''            double riskMoney = CalculateRiskMoney();
            double hardLossBudget = EffectiveHardLossBudget();
            if (UseHardActualLossCap && hardLossBudget > 0 && riskMoney > hardLossBudget)
                riskMoney = hardLossBudget;
''', 'risk budget buffer')

repl('''            if (UseHardActualLossCap && SkipIfMinVolumeRiskTooHigh && MaxActualTradeLossMoney > 0)
            {
                double maxCapVolume = Symbol.VolumeForFixedRisk(MaxActualTradeLossMoney, slPips, RoundingMode.Down);
                if (maxCapVolume < Symbol.VolumeInUnitsMin)
''', '''            if (UseHardActualLossCap && SkipIfMinVolumeRiskTooHigh && hardLossBudget > 0)
            {
                double maxCapVolume = Symbol.VolumeForFixedRisk(hardLossBudget, slPips, RoundingMode.Down);
                if (maxCapVolume < Symbol.VolumeInUnitsMin)
''', 'min volume buffered cap')

repl('''            Debug((signal > 0 ? "BUY" : "SELL") + " opened volume=" + volume + " riskMoney=" + riskMoney.ToString("F2") + " slPips=" + slPips.ToString("F2") + " emergencyTpPips=" + tpPips.ToString("F2") + " runner=" + UseRunnerExit);
        }

        private double CalculateRiskMoney()
''', '''            Debug((signal > 0 ? "BUY" : "SELL") + " opened volume=" + volume + " lots=" + Symbol.VolumeInUnitsToQuantity(volume).ToString("F2") + " riskMoney=" + riskMoney.ToString("F2") + " slPips=" + slPips.ToString("F2") + " tpPips=" + tpPips.ToString("F2") + " plannedRR=" + plannedRiskReward.ToString("F2") + " runner=" + UseRunnerExit);
        }

        private double ResolvePlannedRiskReward()
        {
            double baseRr = Math.Max(0.5, BasePlannedRiskReward);
            if (!UseAdaptiveRiskReward)
                return baseRr;

            bool highQuality = _lastSignalConfirmations >= Math.Max(3, HighQualityConfirmations) &&
                               Math.Abs(_lastSignalDelta) >= DeltaThreshold * Math.Max(1.0, HighQualityDeltaMultiple);
            return highQuality ? Math.Max(baseRr, HighQualityRiskReward) : baseRr;
        }

        private double EffectiveHardLossBudget()
        {
            if (!UseHardActualLossCap || MaxActualTradeLossMoney <= 0)
                return 0;

            double buffer = Math.Max(0.0, Math.Min(50.0, RiskBudgetBufferPercent)) / 100.0;
            return MaxActualTradeLossMoney * (1.0 - buffer);
        }

        private double CalculateRiskMoney()
''', 'rr and risk helpers')

s = s.replace('PriceDistanceToPips(_atr.Result.LastValue * RunnerTrailAtrMultiplier)', 'PriceDistanceToPips(ClosedAtr() * RunnerTrailAtrMultiplier)')
s = s.replace('return PriceDistanceToPips(_atr.Result.LastValue * SlAtrMultiplier);', 'return PriceDistanceToPips(ClosedAtr() * SlAtrMultiplier);')

# Make start-up validation reject nonsensical reward/risk settings rather than silently running them.
repl('''            if (WindowSize < 2 || DeltaThreshold <= 0 || SlAtrMultiplier <= 0 || TpAtrMultiplier <= 0 || BarDeltaPointMultiplier <= 0)
''', '''            if (WindowSize < 2 || DeltaThreshold <= 0 || SlAtrMultiplier <= 0 || TpAtrMultiplier <= 0 || BarDeltaPointMultiplier <= 0 ||
                BasePlannedRiskReward < 0.5 || HighQualityRiskReward < BasePlannedRiskReward || RiskBudgetBufferPercent < 0 || RiskBudgetBufferPercent > 50)
''', 'startup risk validation')

p.write_text(s, encoding='utf-8')
print('Candidate Q risk/reward hardening applied')
