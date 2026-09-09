from pathlib import Path
import hashlib, sys

if len(sys.argv)!=3:
    raise SystemExit('usage: store_v1_transform.py <round26-main.cs> <store-main.cs>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); s=src.read_text()

def rep(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,count)

# Store-safe validated defaults (Round22 Balanced) and reduced diagnostics.
replacements=[
('DefaultValue = Round5DecisionMode.MacroVeto, Group = "BTC Round5 State"','DefaultValue = Round5DecisionMode.ObserveOnly, Group = "BTC Round5 State"','round5 default'),
('Parameter("Log Shadow Conflicts", DefaultValue = true','Parameter("Log Shadow Conflicts", DefaultValue = false','shadow log'),
('Parameter("Log Pattern Matrix", DefaultValue = true','Parameter("Log Pattern Matrix", DefaultValue = false','matrix log'),
('Parameter("R6 Log Rejected Sell", DefaultValue = true','Parameter("R6 Log Rejected Sell", DefaultValue = false','r6 log'),
('Parameter("R7 Veto M30 Sell Alignment", DefaultValue = true','Parameter("R7 Veto M30 Sell Alignment", DefaultValue = false','r7 veto'),
('Parameter("R7 Log Vetoed Sell", DefaultValue = true','Parameter("R7 Log Vetoed Sell", DefaultValue = false','r7 log'),
('Parameter("R8 Log MFE MAE", DefaultValue = true','Parameter("R8 Log MFE MAE", DefaultValue = false','r8 log'),
('Parameter("R9 Shadow TP Continuation", DefaultValue = true','Parameter("R9 Shadow TP Continuation", DefaultValue = false','r9 shadow'),
('Parameter("R10 Log Rejection Funnel", DefaultValue = true','Parameter("R10 Log Rejection Funnel", DefaultValue = false','r10 log'),
('Parameter("R18 Candidate Diagnostics", DefaultValue = true','Parameter("R18 Candidate Diagnostics", DefaultValue = false','r18 diag'),
('Parameter("R21 Bypass Min Score", DefaultValue = 96.0','Parameter("R21 Bypass Min Score", DefaultValue = 93.0','r21 score'),
('Parameter("R21 Bypass Risk % Equity", DefaultValue = 0.25','Parameter("R21 Bypass Risk % Equity", DefaultValue = 0.10','r21 risk'),
('Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, MaxValue = 20','Parameter("Max Open Positions", DefaultValue = 1, MinValue = 1, MaxValue = 1','hard one position'),
('Parameter("Debug Logging", DefaultValue = true','Parameter("Debug Logging", DefaultValue = false','debug default'),
('Print("VERSION v0.23.0-btc-round26-core-refactor");','Print("VERSION BTC-Harmonic-Guard-Store-v1.0");','version'),
]
for old,new,label in replacements: rep(old,new,label)

# Store safety initialization after base market/indicator setup and day reset.
rep('''            ResetDay();\n            Positions.Closed += OnPositionClosed;\n''','''            ResetDay();\n            StoreRestoreRuntimeState();\n            StoreValidateStartup();\n            Positions.Closed += OnPositionClosed;\n''','onstart safety')

# Daily reset becomes restart-safe and history reconstructable.
rep('''        private void ResetDay()\n        {\n            _day = Server.Time.Date;\n            _dayStartEquity = Account.Equity;\n            _tradesToday = 0;\n        }\n''','''        private void ResetDay()\n        {\n            _day = Server.Time.Date;\n            StoreRestoreOrCreateDailyState();\n        }\n''','reset day')

# A restored daily lock must stay locked even if equity later recovers.
rep('if (dd >= MaxDailyLossPercent)','if (StoreDailyLossReached(dd))','daily lock comparisons',count=s.count('if (dd >= MaxDailyLossPercent)'))

# Persist trade counters/runtime state after successful entries.
rep('_tradesToday++;','_tradesToday++;\n            StorePersistAll();','trade persist',count=s.count('_tradesToday++;'))

# Checked emergency close for unprotected fills.
rep('''                if (result.Position != null)\n                    ClosePosition(result.Position);\n''','''                if (result.Position != null)\n                    StoreEmergencyClose(result.Position, "H1_PROTECTION_FAIL");\n''','h1 protection close')
rep('''                Print("[R15 M30 PROTECTION FAIL] closing unprotected position");\n                ClosePosition(result.Position);\n                return;\n''','''                Print("[R15 M30 PROTECTION FAIL] closing unprotected position");\n                StoreEmergencyClose(result.Position, "M30_PROTECTION_FAIL");\n                return;\n''','m30 protection close')

# Checked close for optional M30 lane reservation.
rep('''                Print("[R21 H1 RESERVATION] close optional M30 pos={0} dir={1} heldMin={2:F1}", p.Id, p.TradeType, heldMinutes);\n                ClosePosition(p);\n''','''                Print("[R21 H1 RESERVATION] close optional M30 pos={0} dir={1} heldMin={2:F1}", p.Id, p.TradeType, heldMinutes);\n                StoreCheckedClose(p, "H1_RESERVATION");\n''','reservation close')

# Persist state on stop and after position close bookkeeping begins.
rep('''        protected override void OnStop()\n        {\n            Positions.Closed -= OnPositionClosed;\n''','''        protected override void OnStop()\n        {\n            StorePersistAll();\n            Positions.Closed -= OnPositionClosed;\n''','onstop persist')
rep('''            if (p.Label != BotLabel || p.SymbolName != SymbolName)\n                return;\n\n            string name;\n''','''            if (p.Label != BotLabel || p.SymbolName != SymbolName)\n                return;\n\n            StorePersistAll();\n            string name;\n''','close persist')

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)

safety=out.parent/'Store.Safety.cs'
safety.write_text(r'''using System;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private bool _storeDailyLocked;
        private bool _storeStartupValid = true;
        private bool _storeInitialized;
        private string StoreKeyPrefix => "BTC-Harmonic-Guard|" + BotLabel + "|" + SymbolName + "|";

        private void StoreValidateStartup()
        {
            _storeStartupValid = true;
            string upper = (SymbolName ?? string.Empty).ToUpperInvariant();
            if (!(upper.Contains("BITCOIN") || upper.Contains("BTC")))
            {
                Print("[STORE BLOCK] Unsupported symbol {0}. Use the broker BTC/Bitcoin symbol.", SymbolName);
                _storeStartupValid = false;
            }
            if (TimeFrame != TimeFrame.Hour)
            {
                Print("[STORE BLOCK] Execution timeframe must be H1. Current={0}", TimeFrame);
                _storeStartupValid = false;
            }
            if (RiskMode != RiskSizingMode.RiskPercentEquity)
            {
                Print("[STORE BLOCK] Store Edition supports RiskPercentEquity only. Current={0}", RiskMode);
                _storeStartupValid = false;
            }
            if (MaxOpenPositions != 1)
            {
                Print("[STORE BLOCK] MaxOpenPositions is hard-limited to 1.");
                _storeStartupValid = false;
            }
            if (Symbol.PipSize <= 0 || Symbol.VolumeInUnitsMin <= 0 || Symbol.VolumeInUnitsStep <= 0 || Symbol.VolumeInUnitsMax < Symbol.VolumeInUnitsMin)
            {
                Print("[STORE BLOCK] Invalid broker symbol volume/pip specification.");
                _storeStartupValid = false;
            }
            if (Account.Equity < 3000)
                Print("[STORE WARN] Equity {0:F2} is below the validated recommended minimum USD 3000 equivalent; min-volume rounding may skip signals.", Account.Equity);
            int own = Round18OwnOpenPositions();
            if (own > 1)
            {
                Print("[STORE BLOCK] More than one existing bot position detected ({0}). New entries disabled.", own);
                _storeStartupValid = false;
            }
            Print("[STORE SAFETY] startupValid={0} dailyLocked={1} reconstructedTradesToday={2} dayStartEquity={3:F2}", _storeStartupValid, _storeDailyLocked, _tradesToday, _dayStartEquity);
        }

        private void StoreRestoreOrCreateDailyState()
        {
            // First call is startup/restart recovery. Later calls are ordinary day rollovers
            // and preserve the Champion's original Account.Equity-at-midnight semantics.
            if (_storeInitialized)
            {
                _dayStartEquity = Account.Equity;
                _tradesToday = 0;
                _storeDailyLocked = false;
                StorePersistDailyState();
                return;
            }

            string today = _day.ToString("yyyyMMdd", CultureInfo.InvariantCulture);
            string raw = LocalStorage.GetString(StoreKeyPrefix + "daily", LocalStorageScope.Type);
            bool restored = false;
            if (!string.IsNullOrWhiteSpace(raw))
            {
                string[] p = raw.Split('|');
                double eq; int trades; bool locked;
                if (p.Length == 4 && p[0] == today &&
                    double.TryParse(p[1], NumberStyles.Float, CultureInfo.InvariantCulture, out eq) && eq > 0 &&
                    int.TryParse(p[2], NumberStyles.Integer, CultureInfo.InvariantCulture, out trades) &&
                    bool.TryParse(p[3], out locked))
                {
                    _dayStartEquity = eq;
                    _tradesToday = Math.Max(0, trades);
                    _storeDailyLocked = locked;
                    restored = true;
                }
            }

            if (!restored)
            {
                var todayTrades = History.FindAll(BotLabel, SymbolName)
                    .Where(h => h.ClosingTime.Date == _day)
                    .OrderBy(h => h.ClosingTime)
                    .ToArray();
                double closedNet = todayTrades.Sum(h => h.NetProfit);
                int openToday = Positions.Count(p => p.Label == BotLabel && p.SymbolName == SymbolName && p.EntryTime.Date == _day);
                _tradesToday = todayTrades.Length + openToday;
                _dayStartEquity = todayTrades.Length == 0 && openToday == 0
                    ? Account.Equity
                    : Math.Max(0.01, Account.Balance - closedNet);
                _storeDailyLocked = false;
            }

            StoreRebuildH1Health();
            _storeInitialized = true;
            StorePersistDailyState();
        }

        private void StoreRebuildH1Health()
        {
            _r16RecentH1Wins.Clear();
            var h1 = History.FindAll(BotLabel, SymbolName)
                .Where(h => !string.IsNullOrEmpty(h.Comment) &&
                    !h.Comment.StartsWith("M30|", StringComparison.OrdinalIgnoreCase) &&
                    !h.Comment.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase))
                .OrderByDescending(h => h.ClosingTime)
                .Take(3)
                .OrderBy(h => h.ClosingTime)
                .ToArray();
            foreach (var h in h1)
                _r16RecentH1Wins.Enqueue(h.NetProfit > 0);
        }

        private bool StoreDailyLossReached(double currentDd)
        {
            if (_storeDailyLocked)
                return true;
            if (MaxDailyLossPercent > 0 && currentDd >= MaxDailyLossPercent)
            {
                _storeDailyLocked = true;
                StorePersistDailyState();
                Print("[STORE DAILY LOCK] DD={0:F3}% limit={1:F3}% locked until next server day.", currentDd, MaxDailyLossPercent);
                return true;
            }
            return false;
        }

        private void StorePersistDailyState()
        {
            if (_dayStartEquity <= 0) return;
            string raw = string.Join("|",
                _day.ToString("yyyyMMdd", CultureInfo.InvariantCulture),
                _dayStartEquity.ToString("R", CultureInfo.InvariantCulture),
                _tradesToday.ToString(CultureInfo.InvariantCulture),
                _storeDailyLocked.ToString());
            LocalStorage.SetString(StoreKeyPrefix + "daily", raw, LocalStorageScope.Type);
            LocalStorage.Flush(LocalStorageScope.Type);
        }

        private void StoreRestoreRuntimeState()
        {
            string h1 = LocalStorage.GetString(StoreKeyPrefix + "h1signals", LocalStorageScope.Type);
            if (!string.IsNullOrWhiteSpace(h1))
                foreach (string k in h1.Split(new[]{'\n'}, StringSplitOptions.RemoveEmptyEntries))
                    _consumedSignals.Add(k);
            string m30 = LocalStorage.GetString(StoreKeyPrefix + "m30signals", LocalStorageScope.Type);
            if (!string.IsNullOrWhiteSpace(m30))
                foreach (string k in m30.Split(new[]{'\n'}, StringSplitOptions.RemoveEmptyEntries))
                    _r15M30ConsumedSignals.Add(k);
        }

        private void StorePersistRuntimeState()
        {
            LocalStorage.SetString(StoreKeyPrefix + "h1signals", string.Join("\n", _consumedSignals.TakeLast(500)), LocalStorageScope.Type);
            LocalStorage.SetString(StoreKeyPrefix + "m30signals", string.Join("\n", _r15M30ConsumedSignals.TakeLast(500)), LocalStorageScope.Type);
            LocalStorage.Flush(LocalStorageScope.Type);
        }

        private void StorePersistAll()
        {
            StorePersistDailyState();
            StorePersistRuntimeState();
        }

        private bool StoreCanExecute()
        {
            if (!_storeStartupValid || _storeDailyLocked)
                return false;
            return true;
        }

        private bool StoreCheckedClose(Position p, string reason)
        {
            if (p == null) return true;
            TradeResult r = ClosePosition(p);
            if (r.IsSuccessful) return true;
            Print("[STORE CLOSE FAIL] reason={0} pos={1} error={2}", reason, p.Id, r.Error);
            return false;
        }

        private bool StoreEmergencyClose(Position p, string reason)
        {
            if (p == null) return true;
            for (int i=1; i<=3; i++)
            {
                TradeResult r = ClosePosition(p);
                if (r.IsSuccessful)
                {
                    Print("[STORE EMERGENCY CLOSE] reason={0} pos={1} attempt={2}", reason, p.Id, i);
                    return true;
                }
                Print("[STORE EMERGENCY CLOSE FAIL] reason={0} pos={1} attempt={2} error={3}", reason, p.Id, i, r.Error);
            }
            Print("[STORE CRITICAL] Unable to close unprotected position {0}; disabling new entries.", p.Id);
            _storeStartupValid = false;
            return false;
        }

        protected override void OnException(Exception exception)
        {
            Print("[STORE EXCEPTION] {0}: {1}", exception.GetType().Name, exception.Message);
            StorePersistAll();
        }
    }
}
''')

# Execution wrappers enforce startup and persistent daily lock before either alpha lane can submit orders.
exe=out.parent/'Round26.Execution.cs'
if exe.exists():
    x=exe.read_text()
    x=x.replace('''        private void Round26ExecutionH1(PatternMatch match)\n        {\n            Round26CaptureRegime(match.Direction);\n            ExecutePatternTrade(match);\n        }\n''','''        private void Round26ExecutionH1(PatternMatch match)\n        {\n            if (!StoreCanExecute()) return;\n            Round26CaptureRegime(match.Direction);\n            ExecutePatternTrade(match);\n        }\n''')
    x=x.replace('''        private void Round26ExecutionM30(PatternMatch match, int lastClosed, bool round21Bypass)\n        {\n            Round26CaptureRegime(match.Direction);\n            Round15ExecuteM30(match, lastClosed, round21Bypass);\n        }\n''','''        private void Round26ExecutionM30(PatternMatch match, int lastClosed, bool round21Bypass)\n        {\n            if (!StoreCanExecute()) return;\n            Round26CaptureRegime(match.Direction);\n            Round15ExecuteM30(match, lastClosed, round21Bypass);\n        }\n''')
    exe.write_text(x)

print('Store main SHA', hashlib.sha256(out.read_bytes()).hexdigest())
print('Store safety SHA', hashlib.sha256(safety.read_bytes()).hexdigest())
