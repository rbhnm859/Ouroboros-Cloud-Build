#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('work')
G2 = ROOT / 'g2'
POLICY = Path('.github/policies/commercial_rc7_policy.json')
AUDIT = Path('.github/policies/commercial_rc7_abcd_whitelist_audit.json')
OUT = ROOT / 'Commercial-RC7-Gate.json'


def load(path):
    if not path.exists():
        raise SystemExit(f'missing required file: {path}')
    return json.loads(path.read_text())


def hist(path):
    return load(path).get('history', {}).get('items', [])


def comment(r):
    return str(r.get('comment') or '')


def direction(r):
    return str(r.get('direction') or '').lower()


def attr(rows, pred):
    a = [r for r in rows if pred(r)]
    gp = sum(float(r.get('net', 0) or 0) for r in a if float(r.get('net', 0) or 0) > 0)
    gl = -sum(float(r.get('net', 0) or 0) for r in a if float(r.get('net', 0) or 0) < 0)
    net = sum(float(r.get('net', 0) or 0) for r in a)
    pf = gp / gl if gl > 0 else (99.0 if gp > 0 else 0.0)
    return {'trades': len(a), 'net': round(net, 2), 'pf': round(pf, 4)}


policy = load(POLICY)
audit = load(AUDIT)
if policy.get('policy_version') != 'RC7B-2026-09-10' or policy.get('candidate_count') != 1:
    raise SystemExit('RC7B policy invariant failed')
if audit.get('decision') != 'REJECT_LIVE_WHITELIST' or audit.get('next_report_step') != 'RC6C_DEFERRED_INTENT_TTL_QUEUE':
    raise SystemExit('RC6B audit sequence invariant failed')

required = [
    G2 / 'BTC-Harmonic-Guard-Growth2.cs',
    G2 / 'Commercial.IntentExecution.cs',
    G2 / 'Commercial.SignalPolicy.cs',
    G2 / 'Commercial.RiskGovernor.cs',
    G2 / 'Commercial.ArbitrationLedger.cs',
    G2 / 'Growth3.Architecture.cs',
]
for p in required:
    if not p.exists():
        raise SystemExit(f'missing generated source {p}')

main = (G2 / 'BTC-Harmonic-Guard-Growth2.cs').read_text()
exe = (G2 / 'Commercial.IntentExecution.cs').read_text()
arb = (G2 / 'Commercial.ArbitrationLedger.cs').read_text()
sig = (G2 / 'Commercial.SignalPolicy.cs').read_text()
growth = (G2 / 'Growth3.Architecture.cs').read_text()
compile_cs = [p for p in G2.glob('*.cs') if p.name != 'BTC-Harmonic-Guard.cs']
direct_by_file = {p.name: p.read_text().count('ExecuteMarketOrder(') for p in compile_cs}
direct_total = sum(direct_by_file.values())

console_path = ROOT / 'commercial-rc7-validation-console.log'
console = console_path.read_text(errors='replace') if console_path.exists() else ''
control = load(ROOT / 'Growth2-Control-Parity.json')
summary = load(ROOT / 'Growth2-Final-Summary.json')
control_3y = control.get('3y', {})
control_1y = control.get('1y', {})

arb_policy = policy['policy']['arbitration']
engineering = {
    'compile_zero_errors': 'Build succeeded.' in console and '0 Error(s)' in console,
    'single_execution_boundary': direct_total == 1 and exe.count('ExecuteMarketOrder(') == 1 and main.count('ExecuteMarketOrder(') == 0,
    'round22_control_3y_hash_match': control_3y.get('hash_match') is True,
    'round22_control_1y_hash_match': control_1y.get('hash_match') is True,
    'rc6b_abcd_whitelist_rejected_before_rc6c': audit.get('decision') == 'REJECT_LIVE_WHITELIST',
    'h1_alpha_evaluated_before_portfolio_arbitration': 'CommercialPassH1PreArbitrationLimits()' in main and 'CommercialArbitrateH1BeforeExecution(best)' in main,
    'h1_core_preempts_only_m30_satellite': 'H1_PREEMPT_M30' in arb and 'm30Satellite' in arb,
    'deferred_m30_queue_hook': 'CommercialQueueDeferredM30(best, lastClosed, round21Bypass)' in main,
    'deferred_revalidation': 'Round15PassM30Confirmation(d.Match, currentLastClosed)' in arb and 'INVALIDATE' in arb,
    'deferred_ttl_and_age_bound': 'ExpiresUtc' in arb and 'EXPIRE_BARS' in arb and int(arb_policy['deferred_m30_ttl_minutes']) == 90 and int(arb_policy['deferred_m30_max_age_bars']) == 3,
    'h1_boundary_blackout': int(arb_policy['deferred_execution_blackout_first_minutes_of_hour']) == 2,
    'decision_ledger': '[COMMERCIAL LEDGER]' in arb,
    'legacy_blind_reservation_not_called_from_ontick': 'Round21ReserveH1Lane();' not in main[main.find('protected override void OnTick()'):main.find('protected override void OnStop()')],
    'growth3_shadow_source': '[GROWTH3 SHADOW]' in growth,
    'm30_abcd_shadow_source': 'ABCD_NEGATIVE_CROSS_PERIOD_ATTRIBUTION' in sig,
    'broker_minimum_no_round_up': 'scaled=Symbol.VolumeInUnitsMin' not in exe,
    'rc6_risk_governor_retained': 'CommercialRiskGovernorFactorV6' in exe and policy['policy']['risk_governor']['keep_rc6_lane_health'] is True,
}
engineering_pass = all(engineering.values())

full = summary['selected_3y']
recent = summary['recent']
h3 = summary['harsh_3y']
hr = summary['harsh_recent']
annual = summary['annual']
years = list(annual.values())
pos_years = sum(1 for x in years if float(x['roi']) > 0)
worst_pf = min(float(x['pf']) for x in years)
worst_roi = min(float(x['roi']) for x in years)

r3 = hist(ROOT / 'moderate-3y' / 'report.json')
rr = hist(ROOT / 'recent-a' / 'report.json')
rh = hist(ROOT / 'harsh-3y' / 'report.json')
is_m30 = lambda r: comment(r).upper().startswith(('M30|', 'R21M30|'))
is_growth = lambda r: comment(r).upper().startswith(('GROWTH2|', 'GROWTH3|'))
is_abcd = lambda r: comment(r).upper() in ('M30|ABCD', 'R21M30|ABCD')
is_recip = lambda r: comment(r).upper() in ('M30|RECIPROCAL ABCD', 'R21M30|RECIPROCAL ABCD')
is_h1 = lambda r: not is_m30(r) and not is_growth(r)


def breakdown(rows):
    return {
        'h1_buy': attr(rows, lambda r: is_h1(r) and direction(r) == 'buy'),
        'h1_sell': attr(rows, lambda r: is_h1(r) and direction(r) == 'sell'),
        'm30_recip_buy': attr(rows, lambda r: is_recip(r) and direction(r) == 'buy'),
        'm30_recip_sell': attr(rows, lambda r: is_recip(r) and direction(r) == 'sell'),
        'm30_abcd_live': attr(rows, is_abcd),
        'growth3_live': attr(rows, is_growth),
    }


attrib = {'3y': breakdown(r3), 'recent': breakdown(rr), 'harsh_3y': breakdown(rh)}
formal = {
    '3y_trades_ge_250': int(full['trades']) >= 250,
    '3y_pf_ge_1_40': float(full['pf']) >= 1.40,
    '3y_dd_le_18': float(full['dd']) <= 18.0,
    'recent_pf_ge_1_80': float(recent['pf']) >= 1.80,
    'recent_dd_le_6': float(recent['dd']) <= 6.0,
    'positive_years_ge_2': pos_years >= 2,
    'worst_year_pf_ge_0_90': worst_pf >= 0.90,
    'worst_year_roi_ge_minus_3': worst_roi >= -3.0,
    'harsh3y_roi_nonnegative': float(h3['roi']) >= 0.0,
    'harsh3y_pf_ge_1': float(h3['pf']) >= 1.0,
    'harsh_recent_pf_ge_1_35': float(hr['pf']) >= 1.35,
    'harsh_recent_dd_le_6_8': float(hr['dd']) <= 6.8,
    'growth3_zero_live': attrib['3y']['growth3_live']['trades'] == 0 and attrib['recent']['growth3_live']['trades'] == 0,
    'm30_abcd_zero_live': attrib['3y']['m30_abcd_live']['trades'] == 0 and attrib['recent']['m30_abcd_live']['trades'] == 0,
}

ledger_names = ['QUEUE', 'REPLACE', 'EXPIRE', 'EXPIRE_BARS', 'INVALIDATE', 'REVALIDATION_FAIL', 'H1_PREEMPT_M30', 'DEFERRED_EXECUTE']
ledger_events = {k: len(re.findall(r'\[COMMERCIAL LEDGER\] event=' + re.escape(k) + r'\b', console)) for k in ledger_names}
freeze = engineering_pass and all(formal.values())

failed_formal = [k for k, v in formal.items() if not v]
next_report_step = 'FREEZE_AND_PUBLISH' if freeze else (
    'RC6D_DYNAMIC_RISK_ISOLATION_HEALTH_BUDGET' if any(k in failed_formal for k in ['3y_pf_ge_1_40', 'worst_year_pf_ge_0_90', 'harsh3y_roi_nonnegative', 'harsh3y_pf_ge_1'])
    else 'DIAGNOSE_WITHOUT_BRUTE_FORCE'
)

payload = {
    'candidate': 'BTC Harmonic Guard Commercial RC7B RC6C Arbitration/Deferred Intent',
    'policy_version': policy['policy_version'],
    'report_sequence': policy['report_sequence'],
    'status': 'PASS' if freeze else 'REJECT',
    'engineering_status': 'PASS' if engineering_pass else 'FAIL',
    'commercial_freeze_eligible': freeze,
    'engineering_gates': engineering,
    'formal_commercial_gates': formal,
    'failed_formal_gates': failed_formal,
    'next_report_step': next_report_step,
    'summary': summary,
    'attribution': attrib,
    'ledger_events': ledger_events,
    'architecture': {'direct_execute_market_order_calls': direct_total, 'direct_calls_by_file': direct_by_file},
    'derived': {'positive_years': pos_years, 'worst_year_pf': worst_pf, 'worst_year_roi': worst_roi},
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps(payload, indent=2))

# Strategy rejection is a valid experiment; only engineering/harness failure fails CI.
if not engineering_pass:
    raise SystemExit(2)
