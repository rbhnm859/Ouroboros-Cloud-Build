from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

marker = '// V29.2 GRID-LIFECYCLE-HOTFIX: explicitly register successful primary orders'
if marker not in s:
    old = '''                    if (tr.Position != null)\n                        _patternByPosition[tr.Position.Id] = signal.PatternName;'''
    new = '''                    if (tr.Position != null)\n                    {\n                        _patternByPosition[tr.Position.Id] = signal.PatternName;\n\n                        // V29.2 GRID-LIFECYCLE-HOTFIX: explicitly register successful primary orders\n                        // instead of depending on the transient _pendingPrimaryUseGrid flag surviving\n                        // the Positions.Opened event timing. CreateBasketFor is idempotent.\n                        if (useGridForThisTrade && !_positionToBasket.ContainsKey(tr.Position.Id))\n                            CreateBasketFor(tr.Position);\n                    }'''
    if s.count(old) != 1:
        raise SystemExit(f'grid lifecycle anchor count={s.count(old)}; expected 1')
    s = s.replace(old, new, 1)

s = s.replace('V29.2-Small-Account-Fast-Execution-RC', 'V29.2-Grid-Lifecycle-Hotfix-RC')

for required in [
    marker,
    'CreateBasketFor(tr.Position)',
    'V29.2-Grid-Lifecycle-Hotfix-RC',
    'EnableFibGrid',
    'GridStopFib',
    'GridProfitFib'
]:
    if required not in s:
        raise SystemExit(f'missing required token after patch: {required}')

p.write_text(s, encoding='utf-8')
print('V29.2 Grid lifecycle hotfix applied')
