from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

param_anchor = '''        public int SessionEnd { get; set; }
'''
param_insert = '''        public int SessionEnd { get; set; }

        [Parameter("V29.4 Allow Buy", DefaultValue = true)]
        public bool V294AllowBuy { get; set; }

        [Parameter("V29.4 Allow Sell", DefaultValue = true)]
        public bool V294AllowSell { get; set; }

        private long _v294DirectionBlocked;
'''
if s.count(param_anchor) != 1:
    raise SystemExit(f'V29.4 direction parameter anchor count={s.count(param_anchor)}; expected 1')
s = s.replace(param_anchor, param_insert, 1)

gate_anchor = '''                if (!PassMtfFilter(signal.Direction)) return;
'''
gate_insert = '''                if ((signal.Direction == TradeDirection.Buy && !V294AllowBuy)
                    || (signal.Direction == TradeDirection.Sell && !V294AllowSell))
                {
                    _v294DirectionBlocked++;
                    return;
                }

                if (!PassMtfFilter(signal.Direction)) return;
'''
if s.count(gate_anchor) != 1:
    raise SystemExit(f'V29.4 direction gate anchor count={s.count(gate_anchor)}; expected 1')
s = s.replace(gate_anchor, gate_insert, 1)

stop_anchor = '''            EnsureServerSideProtectionBeforeStop();
'''
stop_new = '''            Print("[V294-EDGE-SUMMARY] directionBlocked={0} allowBuy={1} allowSell={2}", _v294DirectionBlocked, V294AllowBuy, V294AllowSell);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(stop_anchor) != 1:
    raise SystemExit(f'V29.4 stop-summary anchor count={s.count(stop_anchor)}; expected 1')
s = s.replace(stop_anchor, stop_new, 1)

old_version = 'V29.3-Grid-Risk-Cap-Hotfix-RC'
if old_version not in s:
    raise SystemExit('V29.3 source marker missing')
s = s.replace(old_version, 'V29.4-Edge-Context-Gate-Dev', 1)

for token in [
    'V29.4-Edge-Context-Gate-Dev',
    'V294AllowBuy',
    'V294AllowSell',
    '[V294-EDGE-SUMMARY]',
    'V29.3 GRID-RISK-CAP-HOTFIX',
    'V292FastSmallAccountExecution'
]:
    if token not in s:
        raise SystemExit(f'missing required token: {token}')

p.write_text(s, encoding='utf-8')
print('Applied V29.4 Edge Context Gate Development patch')
print('Only Buy/Sell permission gate added; V29.3 engineering core unchanged')
