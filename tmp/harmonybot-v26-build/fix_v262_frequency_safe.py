from pathlib import Path
p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# 1) Parameters
needle = '''        [Parameter("Adaptive Entry Dev Floor (ATR)", DefaultValue = 0.85, MinValue = 0.5, MaxValue = 2.0)]\n        public double AdaptiveEntryDeviationFloor { get; set; }\n'''
insert = needle + '''\n        [Parameter("Closed-Bar Provisional D", DefaultValue = true)]\n        public bool ClosedBarProvisionalD { get; set; }\n\n        [Parameter("Provisional D Min Move (ATR)", DefaultValue = 0.30, MinValue = 0.10, MaxValue = 1.00)]\n        public double ProvisionalDMinMoveAtr { get; set; }\n\n        [Parameter("Small Account Grid Guard", DefaultValue = true)]\n        public bool SmallAccountGridGuard { get; set; }\n'''
if needle not in s: raise SystemExit('parameter insertion point missing')
s = s.replace(needle, insert, 1)

# 2) Pending per-order grid decision
field_needle = '        private bool _ddClosedFlag;\n'
if field_needle not in s: raise SystemExit('field insertion point missing')
s = s.replace(field_needle, field_needle + '        private bool _pendingPrimaryUseGrid;\n', 1)

# 3) Pass provisional-D settings into detector
call_needle = '''                    effectiveFibTolerance, effectiveEntryDeviationAtr,\n                    EnableGartley, EnableBat, EnableButterfly, EnableCrab, EnableCypher,\n'''
call_repl = '''                    effectiveFibTolerance, effectiveEntryDeviationAtr,\n                    ClosedBarProvisionalD && AdaptiveFrequencyRecovery, ProvisionalDMinMoveAtr,\n                    EnableGartley, EnableBat, EnableButterfly, EnableCrab, EnableCypher,\n'''
if call_needle not in s: raise SystemExit('detector call insertion point missing')
s = s.replace(call_needle, call_repl, 1)

# 4) Per-trade grid guard for small accounts
old = '''                if (EnableFibGrid)\n                {\n                    orderSlPips = slPips * GridStopFib;\n                    orderTpPips = null;\n                    _lastPrimaryRiskPips = slPips;\n                    volumeInUnits = CalculateVolumeByRisk(orderSlPips);\n                }\n                else\n                {\n                    volumeInUnits = CalculateVolumeByRisk(slPips);\n                }\n\n                if (volumeInUnits <= 0) return;\n\n                _lastOpenedPattern = signal.PatternName;\n\n                // Hardened order with slippage protection & stop trigger method\n                var tr = ExecuteRobotMarketOrder(tt, volumeInUnits, orderSlPips, orderTpPips);\n'''
new = '''                bool useGridForThisTrade = EnableFibGrid && !(SmallAccountGridGuard && IsSmallAccountMode());\n                _pendingPrimaryUseGrid = useGridForThisTrade;\n\n                if (useGridForThisTrade)\n                {\n                    orderSlPips = slPips * GridStopFib;\n                    orderTpPips = null;\n                    _lastPrimaryRiskPips = slPips;\n                    volumeInUnits = CalculateVolumeByRisk(orderSlPips);\n                }\n                else\n                {\n                    _lastPrimaryRiskPips = 0;\n                    volumeInUnits = CalculateVolumeByRisk(slPips);\n                    if (EnableFibGrid && SmallAccountGridGuard && IsSmallAccountMode())\n                        Print("[GRID-GUARD] Small account mode: primary trade uses normal SL/TP; grid disabled for this position.");\n                }\n\n                if (volumeInUnits <= 0)\n                {\n                    _pendingPrimaryUseGrid = false;\n                    return;\n                }\n\n                _lastOpenedPattern = signal.PatternName;\n\n                // Hardened order with slippage protection & stop trigger method\n                var tr = ExecuteRobotMarketOrder(tt, volumeInUnits, orderSlPips, orderTpPips);\n                _pendingPrimaryUseGrid = false;\n'''
if old not in s: raise SystemExit('grid order block missing')
s = s.replace(old, new, 1)

# 5) Only attach a basket when this primary was intentionally opened as grid parent
s = s.replace('''            if (EnableFibGrid)\n                CreateBasketFor(p);\n''', '''            if (EnableFibGrid && _pendingPrimaryUseGrid)\n                CreateBasketFor(p);\n''', 1)

# 6) $100 exactly must count as small account
s = s.replace('return SmallAccountMode && Account.Equity < SmallAccountThreshold;',
              'return SmallAccountMode && Account.Equity <= SmallAccountThreshold;', 1)

# 7) Detector fields
field_det = '''        private readonly double _maxEntryDeviationAtr;\n\n        private readonly Dictionary<string, bool> _enabled'''
field_det_repl = '''        private readonly double _maxEntryDeviationAtr;\n        private readonly bool _closedBarProvisionalD;\n        private readonly double _provisionalDMinMoveAtr;\n\n        private readonly Dictionary<string, bool> _enabled'''
if field_det not in s: raise SystemExit('detector field insertion point missing')
s = s.replace(field_det, field_det_repl, 1)

# 8) Detector constructor signature and assignments
sig = '''            double fibTolerance, double maxEntryDeviationAtr,\n            bool gartley, bool bat, bool butterfly, bool crab, bool cypher,'''
sig_repl = '''            double fibTolerance, double maxEntryDeviationAtr,\n            bool closedBarProvisionalD, double provisionalDMinMoveAtr,\n            bool gartley, bool bat, bool butterfly, bool crab, bool cypher,'''
if sig not in s: raise SystemExit('detector signature missing')
s = s.replace(sig, sig_repl, 1)
assign = '''            _fibTolerance = Math.Max(0.0, Math.Min(0.5, fibTolerance));\n            _maxEntryDeviationAtr = Math.Max(0.0, maxEntryDeviationAtr);\n'''
assign_repl = assign + '''            _closedBarProvisionalD = closedBarProvisionalD;\n            _provisionalDMinMoveAtr = Math.Max(0.10, Math.Min(1.00, provisionalDMinMoveAtr));\n'''
if assign not in s: raise SystemExit('detector assignment missing')
s = s.replace(assign, assign_repl, 1)

# 9) Append one completed-bar provisional D/C pivot after the last confirmed pivot.
try_needle = '''            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);\n            if (pivots.Count < 5) return false;\n'''
try_repl = '''            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);\n            if (_closedBarProvisionalD)\n                AppendClosedBarProvisionalPivot(pivots, bars, currentIndex, atrNow, _provisionalDMinMoveAtr);\n            if (pivots.Count < 4) return false;\n'''
if try_needle not in s: raise SystemExit('TryDetect pivot point missing')
s = s.replace(try_needle, try_repl, 1)

# 10) Helper before BuildSwingPoints
helper_marker = '''        private static List<SwingPoint> BuildSwingPoints(Bars bars, int endIndex, int lookback, int depth)\n'''
helper = '''        private static void AppendClosedBarProvisionalPivot(List<SwingPoint> pivots, Bars bars, int currentIndex, double atr, double minMoveAtr)\n        {\n            if (pivots == null || pivots.Count == 0 || bars == null || currentIndex < 0 || currentIndex >= bars.Count || atr <= 0) return;\n\n            SwingPoint last = pivots[pivots.Count - 1];\n            if (last == null || last.Index >= currentIndex) return;\n\n            bool nextIsHigh = !last.IsHigh;\n            double price = nextIsHigh ? bars.HighPrices[currentIndex] : bars.LowPrices[currentIndex];\n            if (price <= 0) return;\n            if (Math.Abs(price - last.Price) < atr * Math.Max(0.10, minMoveAtr)) return;\n\n            // Only use a completed-bar extreme and preserve alternating pivot structure.\n            pivots.Add(new SwingPoint { Index = currentIndex, Price = price, IsHigh = nextIsHigh });\n        }\n\n'''
if helper_marker not in s: raise SystemExit('helper marker missing')
s = s.replace(helper_marker, helper + helper_marker, 1)

p.write_text(s, encoding='utf-8')
print('Applied v26.2 frequency-safe architecture fixes')
