from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# Final compile guard: earlier refactors can replace the IsSmallAccountMode block
# after v26.2 inserted IsGridGuardAccount. Ensure the helper exists in the final
# generated V28 source, after every strategy/risk/accounting patch has run.
if 'private bool IsGridGuardAccount()' not in s:
    marker = '''        private bool IsSmallAccountMode()\n        {\n            return SmallAccountMode && Account.Equity <= SmallAccountThreshold + 1e-9;\n        }\n'''
    if marker not in s:
        marker = '''        private bool IsSmallAccountMode()\n        {\n            return SmallAccountMode && Account.Equity <= SmallAccountThreshold;\n        }\n'''
    if marker not in s:
        raise SystemExit('final IsSmallAccountMode insertion point missing')

    helper = '''        private bool IsGridGuardAccount()\n        {\n            if (!SmallAccountMode) return false;\n            double guardThreshold = Math.Max(SmallAccountThreshold, SmallAccountThreshold * 2.0);\n            return Account.Equity <= guardThreshold + 1e-9;\n        }\n\n'''
    s = s.replace(marker, helper + marker, 1)

if s.count('IsGridGuardAccount()') < 3:
    raise SystemExit('IsGridGuardAccount final audit failed')

p.write_text(s, encoding='utf-8')
print('Applied V28 final compile guard: IsGridGuardAccount restored and audited')
