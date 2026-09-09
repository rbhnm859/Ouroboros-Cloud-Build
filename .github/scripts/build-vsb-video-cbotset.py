from pathlib import Path
import json
import re

raw = Path('work/reports/metadata.txt').read_text(errors='replace')
a, b = raw.find('{'), raw.rfind('}')
if a < 0 or b < a:
    raise SystemExit('metadata JSON not found')
meta = json.loads(raw[a:b + 1])
params = meta.get('Parameters', [])

def norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())

index = {}
for p in params:
    index[norm(p.get('FriendlyName', ''))] = p
    index[norm(p.get('PropertyName', ''))] = p

desired = [
    ('Bot Label', 'VSB_xauusd'),
    ('Debug Logging', True),
    ('Trading Enabled', True),
    ('Use UTC Offset (hours)', 0),
    ('Preset Mode', 'GoldNY'),
    ('Export Trades to CSV', False),
    ('CSV Log Path', 'VolatilitySniperLog.csv'),
    ('Show Range Box', False),
    ('Show Pending Order Lines', False),
    ('Show EMA Filter Line', False),
    ('Show ATR Label', False),
    ('Show News Blackout Zones', False),
    ('Build Range Start (HH:mm)', '00:00'),
    ('Build Range End (HH:mm)', '07:59'),
    ('Trade Window Start (HH:mm)', '08:00'),
    ('Trade Window End (HH:mm)', '21:00'),
    ('Invalidate Range On New Day', True),
    ('Pending Offset (pips)', 15),
    ('Refresh Drift Factor', 0.8),
    ('Cancel Opposite After Fill', True),
    ('Range Min Size (pips)', 3000),
    ('Range Max Size (pips, 0=off)', 15000),
    ('Use ATR Filter', True),
    ('ATR Period', 14),
    ('ATR Timeframe', 'h1'),
    ('Min ATR (pips, 0=off)', 30),
    ('Use EMA Trend Filter', True),
    ('EMA Period', 50),
    ('EMA Timeframe', 'h1'),
    ('EMA Slope Required', True),
    ('Use Consolidation Filter', False),
    ('Consolidation Lookback (bars)', 20),
    ('Consolidation Max BB Width', 15),
    ('Risk % (Balance/Equity)', 1),
    ('Risk Source', 'Equity'),
    ('Use ATR Stop', True),
    ('ATR SL Multiplier', 1.8),
    ('Fixed SL (pips, used if ATR off)', 150),
    ('Use ATR TP', True),
    ('ATR TP Multiplier', 5.4),
    ('Fixed TP (pips, used if ATR off)', 450),
    ('Enable Breakeven', True),
    ('Breakeven Trigger (R multiple)', 2.5),
    ('Breakeven Lock (pips beyond entry)', 10),
    ('Enable ATR Trailing', False),
    ('ATR Trail Multiplier', 3.5),
    ('Enable News Blackout', True),
    ('No Trade Before News (min)', 30),
    ('No Trade After News (min)', 30),
    ('News Source', 'CsvFile'),
    ('News CSV Path (UTC, ISO...)', ''),
    ('News HTTP JSON URL (UTC...)', ''),
    ('Filter By Symbol Currency', True),
    ('Min Impact To Filter (Low/Medium/High)', 'High'),
    ('Max Trades Per Day (0=unlimited)', 3),
    ('Max Daily Loss % (0=off)', 5),
    ('Cooldown After Fill (min)', 30),
]

aliases = {
    'Use UTC Offset (hours)': ['Use UTC Offset', 'UtcOffsetHours', 'UseUtcOffsetHours'],
    'Pending Offset (pips)': ['Pending Offset', 'PendingOffset', 'PendingOffsetPips'],
    'Range Min Size (pips)': ['Range Min Size', 'RangeMinSize', 'RangeMinSizePips'],
    'Range Max Size (pips, 0=off)': ['Range Max Size', 'RangeMaxSize', 'RangeMaxSizePips'],
    'Min ATR (pips, 0=off)': ['Min ATR', 'MinATR', 'MinATRPips'],
    'Risk % (Balance/Equity)': ['Risk %', 'RiskPercent'],
    'Fixed SL (pips, used if ATR off)': ['Fixed SL', 'FixedSL', 'FixedSLPips'],
    'Fixed TP (pips, used if ATR off)': ['Fixed TP', 'FixedTP', 'FixedTPPips'],
    'Breakeven Trigger (R multiple)': ['Breakeven Trigger', 'BreakevenTrigger'],
    'Breakeven Lock (pips beyond entry)': ['Breakeven Lock', 'BreakevenLock'],
    'No Trade Before News (min)': ['No Trade Before News', 'NoTradeBeforeNews'],
    'No Trade After News (min)': ['No Trade After News', 'NoTradeAfterNews'],
    'News CSV Path (UTC, ISO...)': ['News CSV Path', 'NewsCSVPath'],
    'News HTTP JSON URL (UTC...)': ['News HTTP JSON URL', 'NewsHTTPJSONURL'],
    'Min Impact To Filter (Low/Medium/High)': ['Min Impact To Filter', 'MinImpactToFilter'],
    'Max Trades Per Day (0=unlimited)': ['Max Trades Per Day', 'MaxTradesPerDay'],
    'Max Daily Loss % (0=off)': ['Max Daily Loss %', 'MaxDailyLossPercent'],
    'Cooldown After Fill (min)': ['Cooldown After Fill', 'CooldownAfterFill'],
}

lines, mapping, missing = [], [], []
for friendly, value in desired:
    names = [friendly] + aliases.get(friendly, [])
    p = next((index.get(norm(n)) for n in names if index.get(norm(n))), None)
    if p is None:
        candidates = []
        for q in params:
            qkeys = [norm(q.get('FriendlyName', '')), norm(q.get('PropertyName', ''))]
            if any(norm(n) and (norm(n) in k or k in norm(n)) for n in names for k in qkeys):
                candidates.append(q)
        unique = {q.get('PropertyName'): q for q in candidates}
        if len(unique) == 1:
            p = next(iter(unique.values()))
    if p is None:
        missing.append(friendly)
        continue
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    lines.append(f"{p['PropertyName']}={rendered}")
    mapping.append(f"{friendly} -> {p['PropertyName']} [{p.get('Type')}] = {rendered}")

Path('work/VSB-video.cbotset').write_text('\n'.join(lines) + '\n')
Path('work/reports/parameter-mapping.txt').write_text(
    '\n'.join(mapping) + '\n\nMissing:\n' + '\n'.join(missing) + '\n'
)
print(Path('work/reports/parameter-mapping.txt').read_text())
critical = [x for x in missing if not x.startswith('News CSV Path') and not x.startswith('News HTTP JSON URL')]
if critical:
    raise SystemExit('Unmapped video parameters: ' + ', '.join(critical))
