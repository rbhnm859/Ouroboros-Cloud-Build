from pathlib import Path
p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')
s = s.replace('SmallAccountGridGuard && IsSmallAccountMode()', 'SmallAccountGridGuard && IsGridGuardAccount()')
marker = '''        private bool IsSmallAccountMode()\n        {\n            return SmallAccountMode && Account.Equity <= SmallAccountThreshold;\n        }\n'''
helper = '''        private bool IsGridGuardAccount()\n        {\n            if (!SmallAccountMode) return false;\n            double guardThreshold = Math.Max(SmallAccountThreshold, SmallAccountThreshold * 2.0);\n            return Account.Equity <= guardThreshold;\n        }\n\n'''
if marker not in s: raise SystemExit('small-account helper marker missing')
s = s.replace(marker, helper + marker, 1)
p.write_text(s, encoding='utf-8')
print('Applied v26.2 grid guard recovery band')
