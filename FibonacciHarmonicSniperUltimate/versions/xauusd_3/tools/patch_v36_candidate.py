from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "FibonacciXAUUSD3.cs"
s = SRC.read_text()


def replace_once(old: str, new: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, got {count}: {old[:80]!r}")
    s = s.replace(old, new, 1)


replace_once(
    'Print("VERSION xauusd_3 v3.5.0-m5-first-valid");',
    'Print("VERSION xauusd_3 v3.6.0-exit-resilience-candidate");',
)

old = '''        [Parameter("H1 ATR14/ATR50 Min", DefaultValue = 1.15, MinValue = 1.00, MaxValue = 2.00, Group = "Regime")]
        public double H1AtrExpansionMin { get; set; }
'''
new = old + '''
        [Parameter("TP Distance Multiplier", DefaultValue = 1.0, MinValue = 0.80, MaxValue = 1.50, Group = "Exit")]
        public double TakeProfitMultiplier { get; set; }

        [Parameter("Enable Breakeven", DefaultValue = false, Group = "Exit")]
        public bool EnableBreakeven { get; set; }

        [Parameter("Breakeven Trigger R", DefaultValue = 1.0, MinValue = 0.5, MaxValue = 3.0, Group = "Exit")]
        public double BreakevenTriggerR { get; set; }

        [Parameter("Breakeven Lock R", DefaultValue = 0.05, MinValue = 0.0, MaxValue = 0.50, Group = "Exit")]
        public double BreakevenLockR { get; set; }
'''
replace_once(old, new)

old = '        private readonly Dictionary<long, TradeMeta> _openMeta = new Dictionary<long, TradeMeta>();\n'
new = old + '        private readonly Dictionary<long, double> _initialRiskPips = new Dictionary<long, double>();\n'
replace_once(old, new)

replace_once(
    '''            ResetDay();
            Print("VERSION xauusd_3 v3.6.0-exit-resilience-candidate");
''',
    '''            ResetDay();
            RestoreDailyStateFromHistory();
            Print("VERSION xauusd_3 v3.6.0-exit-resilience-candidate");
''',
)

replace_once(
    '''            if (m5Index < 12)
                return;
            if (HasAnySymbolExposure())
                return;
''',
    '''            if (m5Index < 12)
                return;
            EnsureProtectionIntegrity();
            ManageOpenPositions();
            if (HasAnySymbolExposure())
                return;
''',
)

replace_once(
    '''                double tpPips = tpDistance / Symbol.PipSize;
                double rr = tpPips / slPips;
''',
    '''                double tpPips = (tpDistance / Symbol.PipSize) * TakeProfitMultiplier;
                double rr = tpPips / slPips;
''',
)

old = '                _openMeta[result.Position.Id] = new TradeMeta(a.Tag, a.Direction, finalScore, rr, confirmRules, session);\n'
new = old + '                _initialRiskPips[result.Position.Id] = slPips;\n'
replace_once(old, new)

marker = '''        private double H1AtrExpansionRatio()
        {
'''
helper = '''        private void EnsureProtectionIntegrity()
        {
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (p.StopLoss != null && p.TakeProfit != null)
                    continue;
                Print("[FAILSAFE] Missing protection PID={0}; closing position", p.Id);
                ClosePosition(p);
            }
        }

        private void ManageOpenPositions()
        {
            if (!EnableBreakeven)
                return;

            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
            {
                if (p.StopLoss == null || p.TakeProfit == null)
                    continue;

                double initialRiskPips;
                if (!_initialRiskPips.TryGetValue(p.Id, out initialRiskPips))
                {
                    bool alreadyProtected = p.TradeType == TradeType.Buy
                        ? p.StopLoss.Value >= p.EntryPrice
                        : p.StopLoss.Value <= p.EntryPrice;
                    if (alreadyProtected)
                        continue;

                    initialRiskPips = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Symbol.PipSize;
                    if (initialRiskPips <= 0)
                        continue;
                    _initialRiskPips[p.Id] = initialRiskPips;
                }

                double favorablePips = p.TradeType == TradeType.Buy
                    ? (Symbol.Bid - p.EntryPrice) / Symbol.PipSize
                    : (p.EntryPrice - Symbol.Ask) / Symbol.PipSize;
                if (favorablePips < BreakevenTriggerR * initialRiskPips)
                    continue;

                double desired = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + BreakevenLockR * initialRiskPips * Symbol.PipSize
                    : p.EntryPrice - BreakevenLockR * initialRiskPips * Symbol.PipSize;
                bool improves = p.TradeType == TradeType.Buy
                    ? desired > p.StopLoss.Value
                    : desired < p.StopLoss.Value;
                if (!improves)
                    continue;

                double market = p.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
                double distancePips = Math.Abs(market - desired) / Symbol.PipSize;
                double brokerMin = BrokerMinDistancePips(market, Symbol.MinStopLossDistance) * 1.10;
                if (distancePips <= brokerMin)
                    continue;

                TradeResult mr = ModifyPosition(p, desired, p.TakeProfit);
                if (mr.IsSuccessful)
                    Print("[BREAKEVEN] PID={0} trigger={1:F2}R lock={2:F2}R", p.Id, BreakevenTriggerR, BreakevenLockR);
                else
                    Print("[BREAKEVEN FAIL] PID={0} error={1}", p.Id, mr.Error);
            }
        }

        private void RestoreDailyStateFromHistory()
        {
            double net = 0.0;
            int trades = 0;
            foreach (HistoricalTrade t in History.FindAll(BotLabel, SymbolName))
            {
                if (t.ClosingTime.Date == _day)
                    net += t.NetProfit;
                if (t.EntryTime.Date == _day)
                    trades++;
            }
            _dayNet = net;
            _tradesToday = trades;
            _dayStartBalance = Account.Balance - _dayNet;
            if (_dayStartBalance <= 0)
                _dayStartBalance = Account.Balance;
        }

        private double CurrentBotFloatingNet()
        {
            double net = 0.0;
            foreach (Position p in Positions.FindAll(BotLabel, SymbolName))
                net += p.NetProfit;
            return net;
        }

        private double H1AtrExpansionRatio()
        {
'''
replace_once(marker, helper)

replace_once(
    '''            double cap = _dayStartBalance * MaxDailyLossPercent / 100.0;
            return -_dayNet >= cap;
''',
    '''            double cap = _dayStartBalance * MaxDailyLossPercent / 100.0;
            return -(_dayNet + CurrentBotFloatingNet()) >= cap;
''',
)

replace_once(
    '            _openMeta.Remove(p.Id);\n',
    '            _openMeta.Remove(p.Id);\n            _initialRiskPips.Remove(p.Id);\n',
)

SRC.write_text(s)
print(f"patched {SRC}")
