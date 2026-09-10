from pathlib import Path

p = Path('CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs')
s = p.read_text(encoding='utf-8')

def repl(old, new, name):
    global s
    if old not in s:
        raise SystemExit(f'patch anchor not found: {name}')
    s = s.replace(old, new, 1)

repl('''        [Parameter("Use Breakeven", DefaultValue = false, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("Breakeven Pips", DefaultValue = 1.5, MinValue = 0.1, Step = 0.1, Group = "Exit")]
        public double BreakevenPips { get; set; }
''', '''        [Parameter("Use Breakeven", DefaultValue = false, Group = "Exit")]
        public bool UseBreakeven { get; set; }

        [Parameter("Use R Breakeven", DefaultValue = true, Group = "Exit")]
        public bool UseRiskMultipleBreakeven { get; set; }

        [Parameter("Breakeven At R", DefaultValue = 0.75, MinValue = 0.2, MaxValue = 2.0, Step = 0.05, Group = "Exit")]
        public double BreakevenAtR { get; set; }

        [Parameter("Breakeven Pips", DefaultValue = 1.5, MinValue = 0.1, Step = 0.1, Group = "Exit")]
        public double BreakevenPips { get; set; }
''', 'breakeven parameters')

repl('''        private void TryBreakeven(Position position)
        {
            double buffer = BreakevenBufferPips * Symbol.PipSize;
            double? tp = position.TakeProfit;

            if (position.TradeType == TradeType.Buy)
            {
                double profitPips = (Symbol.Bid - position.EntryPrice) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = position.EntryPrice + buffer;
                TryImproveStop(position, newSl, tp, "BREAKEVEN");
            }
            else
            {
                double profitPips = (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (profitPips < BreakevenPips) return;
                double newSl = position.EntryPrice - buffer;
                TryImproveStop(position, newSl, tp, "BREAKEVEN");
            }
        }
''', '''        private void TryBreakeven(Position position)
        {
            double buffer = BreakevenBufferPips * Symbol.PipSize;
            double? tp = position.TakeProfit;
            double triggerPips = BreakevenPips;

            if (UseRiskMultipleBreakeven)
            {
                double riskPips = EstimateRiskPips(position);
                if (riskPips <= 0) return;
                triggerPips = Math.Max(0.1, riskPips * Math.Max(0.2, BreakevenAtR));
            }

            if (position.TradeType == TradeType.Buy)
            {
                double profitPips = (Symbol.Bid - position.EntryPrice) / Symbol.PipSize;
                if (profitPips < triggerPips) return;
                double newSl = position.EntryPrice + buffer;
                TryImproveStop(position, newSl, tp, "BREAKEVEN");
            }
            else
            {
                double profitPips = (position.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (profitPips < triggerPips) return;
                double newSl = position.EntryPrice - buffer;
                TryImproveStop(position, newSl, tp, "BREAKEVEN");
            }
        }
''', 'R multiple breakeven')

p.write_text(s, encoding='utf-8')
print('Candidate Q2 R-multiple breakeven applied')
