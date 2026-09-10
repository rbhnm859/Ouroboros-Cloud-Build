#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('work')
G2 = ROOT / 'g2'
POLICY = Path('.github/policies/commercial_rc7_policy.json')
OUT = ROOT / 'Commercial-RC7-Gate.json'


def engineering_fail(msg: str):
    payload = {
        'status': 'ENGINEERING_FAIL',
        'engineering_status': 'FAIL',
        'commercial_freeze_eligible': False,
        'error': msg,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    raise SystemExit(2)


def load_json(path: Path):
    if not path.exists():
        engineering_fail(f'missing required json: {path}')
    return json.loads(path.read_text())


def history_items(path: Path):
    return load_json(path).get('history', {}).get('items', [])


def direction(row):
    return str(row.get('direction') or row.get('tradeType') or '').lower()


def comment(row):
    return str(row.get('comment') or '')


def attribution(rows, predicate):
    chosen = [r for r in rows if predicate(r)]
    gp = sum(float(r.get('net', 0) or 0) for r in chosen if float(r.get('net', 0) or 0) > 0)
    gl = -sum(float(r.get('net', 0) or 0) for r in chosen if float(r.get('net', 0) or 0) < 0)
    net = sum(float(r.get('net', 0) or 0) for r in chosen)
    pf = gp / gl if gl > 0 else (99.0 if gp > 0 else 0.0)
    return {'trades': len(chosen), 'net': round(net, 2), 'pf': round(pf, 4)}


policy = load_json(POLICY)
if policy.get('policy_version') != 'RC7A-2026-09-10':
    engineering_fail('policy version mismatch')
if policy.get('candidate_count') != 1:
    engineering_fail('RC7 must contain exactly one predeclared candidate')

required_source = [
    G2 / 'BTC-Harmonic-Guard-Growth2.cs',
    G2 / 'Commercial.IntentExecution.cs',
    G2 / 'Commercial.SignalPolicy.cs',
    G2 / 'Commercial.RiskGovernor.cs',
    G2 / 'Commercial.PortfolioDecision.cs',
    G2 / 'Commercial.ShadowLedger.cs',
    G2 / 'Growth3.Architecture.cs',
]
for p in required_source:
    if not p.exists():
        engineering_fail(f'missing generated source: {p}')

main = (G2 / 'BTC-Harmonic-Guard-Growth2.cs').read_text()
execution = (G2 / 'Commercial.IntentExecution.cs').read_text()
signal_policy = (G2 / 'Commercial.SignalPolicy.cs').read_text()
risk_governor = (G2 / 'Commercial.RiskGovernor.cs').read_text()
portfolio = (G2 / 'Commercial.PortfolioDecision.cs').read_text()
shadow = (G2 / 'Commercial.ShadowLedger.cs').read_text()
growth3 = (G2 / 'Growth3.Architecture.cs').read_text()

compile_cs = [p for p in G2.glob('*.cs') if p.name != 'BTC-Harmonic-Guard.cs']
direct_by_file = {p.name: p.read_text().count('ExecuteMarketOrder(') for p in compile_cs}
direct_total = sum(direct_by_file.values())
central_direct = execution.count('ExecuteMarketOrder(')
main_direct = main.count('ExecuteMarketOrder(')

console_path = ROOT / 'commercial-rc7-validation-console.log'
console = console_path.read_text(errors='replace') if console_path.exists() else ''
compile_zero_errors = '0 Error(s)' in console and 'Build succeeded.' in console

control = load_json(ROOT / 'Growth2-Control-Parity.json')
control_3y_match = bool(control.get('3y', {}).get('hash_match'))
control_1y_match = bool(control.get('1y', {}).get('hash_match'))

p = policy['policy']
arch = policy['architecture']
rc6_caps = {'h1_sell': 0.35, 'm30_reciprocal_abcd_buy': 0.35, 'm30_reciprocal_abcd_sell': 0.75}
reduction_only_manifest = (
    0 < float(p['h1_sell']['risk_multiplier']) <= rc6_caps['h1_sell'] and
    0 < float(p['m30_reciprocal_abcd_buy']['risk_multiplier']) <= rc6_caps['m30_reciprocal_abcd_buy'] and
    0 < float(p['m30_reciprocal_abcd_sell']['risk_multiplier']) <= rc6_caps['m30_reciprocal_abcd_sell']
)

deferred_cfg = arch['m30_deferred_intent']
engineering = {
    'single_execution_boundary': direct_total == 1 and central_direct == 1 and main_direct == 0,
    'compile_zero_errors': compile_zero_errors,
    'frozen_control_3y_hash_match': control_3y_match,
    'frozen_control_1y_hash_match': control_1y_match,
    'frozen_control_selector_isolated': 'if (!Growth2Enabled)' in main,
    'frozen_control_governor_bypass': 'Growth2Enabled ? CommercialRiskGovernorFactorV6(intent) : 1.0' in execution,
    'h1_routes_through_portfolio_decision': main.count('CommercialPortfolioRouteIntent(intent)') == 2,
    'portfolio_decision_present': '[COMMERCIAL DECISION]' in portfolio,
    'deferred_reciprocal_only_source': 'Reciprocal ABCD' in portfolio and 'CommercialConsiderDeferredM30' in portfolio,
    'deferred_open_position_only_source': 'reason=OPEN_POSITION' in portfolio,
    'deferred_ttl_four_bars': int(deferred_cfg['ttl_m30_bars']) == 4 and '+ 4' in portfolio,
    'deferred_revalidation_present': all(x in portfolio for x in [
        'Round16H1HealthAllowsM30()',
        'Round15PassSharedLimits(currentLastClosed)',
        'Round15M30TrendAligned',
        'Round15PassM30Confirmation',
        '_r15M30ConsumedSignals.Contains',
    ]),
    'round21_bypass_not_deferred': deferred_cfg.get('round21_bypass_deferred') is False and '!round21Bypass' in main,
    'shadow_counterfactual_ledger_present': '[COMMERCIAL COUNTERFACTUAL]' in shadow and 'CommercialTrackM30Shadow' in main,
    'growth3_shadow_source': '[GROWTH3 SHADOW]' in growth3 and 'CommercialSubmitIntent' not in growth3,
    'm30_abcd_default_shadow': 'ABCD_NEGATIVE_CROSS_PERIOD_ATTRIBUTION' in signal_policy,
    'broker_minimum_never_rounds_risk_up': 'scaled=Symbol.VolumeInUnitsMin' not in execution and 'BELOW_BROKER_MIN' in execution,
    'post_round_risk_cap': 'POST_ROUND_RISK_EXCEEDS_CAP' in execution,
    'reduction_only_manifest': reduction_only_manifest,
    'single_predeclared_policy': policy.get('candidate_count') == 1,
    'auxiliary_files_have_no_direct_orders': 'ExecuteMarketOrder(' not in portfolio and 'ExecuteMarketOrder(' not in shadow,
}
engineering_pass = all(engineering.values())

summary = load_json(ROOT / 'Growth2-Final-Summary.json')
full = summary['selected_3y']
recent = summary['recent']
h3 = summary['harsh_3y']
hr = summary['harsh_recent']
annual_rows = list(summary['annual'].values())
positive_years = sum(1 for x in annual_rows if float(x['roi']) > 0)
worst_pf = min(float(x['pf']) for x in annual_rows)
worst_roi = min(float(x['roi']) for x in annual_rows)

r3 = history_items(ROOT / 'moderate-3y' / 'report.json')
rr = history_items(ROOT / 'recent-a' / 'report.json')
rh = history_items(ROOT / 'harsh-3y' / 'report.json')

def is_m30(r):
    c = comment(r).upper()
    return c.startswith('M30|') or c.startswith('R21M30|')

def is_growth(r):
    c = comment(r).upper()
    return c.startswith('GROWTH2|') or c.startswith('GROWTH3|')

def is_abcd(r):
    c = comment(r).upper()
    return c.startswith('M30|ABCD') or c.startswith('R21M30|ABCD')

def is_recip(r):
    c = comment(r).upper()
    return c.startswith('M30|RECIPROCAL ABCD') or c.startswith('R21M30|RECIPROCAL ABCD')

def is_deferred(r):
    return '|DEFERRED' in comment(r).upper()

def is_h1(r):
    return not is_m30(r) and not is_growth(r)

attrib = {
    '3y': {
        'h1_buy': attribution(r3, lambda r: is_h1(r) and direction(r) == 'buy'),
        'h1_sell': attribution(r3, lambda r: is_h1(r) and direction(r) == 'sell'),
        'm30_recip_buy': attribution(r3, lambda r: is_recip(r) and direction(r) == 'buy'),
        'm30_recip_sell': attribution(r3, lambda r: is_recip(r) and direction(r) == 'sell'),
        'm30_deferred': attribution(r3, is_deferred),
        'm30_abcd_live': attribution(r3, is_abcd),
        'growth3_live': attribution(r3, is_growth),
    },
    'recent': {
        'h1_buy': attribution(rr, lambda r: is_h1(r) and direction(r) == 'buy'),
        'h1_sell': attribution(rr, lambda r: is_h1(r) and direction(r) == 'sell'),
        'm30_recip_buy': attribution(rr, lambda r: is_recip(r) and direction(r) == 'buy'),
        'm30_recip_sell': attribution(rr, lambda r: is_recip(r) and direction(r) == 'sell'),
        'm30_deferred': attribution(rr, is_deferred),
        'm30_abcd_live': attribution(rr, is_abcd),
        'growth3_live': attribution(rr, is_growth),
    },
    'harsh_3y': {
        'h1_buy': attribution(rh, lambda r: is_h1(r) and direction(r) == 'buy'),
        'h1_sell': attribution(rh, lambda r: is_h1(r) and direction(r) == 'sell'),
        'm30_recip_buy': attribution(rh, lambda r: is_recip(r) and direction(r) == 'buy'),
        'm30_recip_sell': attribution(rh, lambda r: is_recip(r) and direction(r) == 'sell'),
        'm30_deferred': attribution(rh, is_deferred),
    },
}

all_deferred_rows = [r for r in r3 + rr + rh if is_deferred(r)]
deferred_only_reciprocal = all(is_recip(r) and not is_abcd(r) and not is_growth(r) for r in all_deferred_rows)

cf_starts = console.count('[COMMERCIAL COUNTERFACTUAL] action=START')
cf_resolves = console.count('[COMMERCIAL COUNTERFACTUAL] action=RESOLVE')
defer_events = console.count('[COMMERCIAL DECISION] action=DEFER')
defer_execute_events = console.count('[COMMERCIAL DECISION] action=EXECUTE_DEFERRED')

formal_gates = {
    '3y_trades_ge_250': int(full['trades']) >= 250,
    '3y_pf_ge_1_40': float(full['pf']) >= 1.40,
    '3y_dd_le_18': float(full['dd']) <= 18.0,
    'recent_pf_ge_1_80': float(recent['pf']) >= 1.80,
    'recent_dd_le_6': float(recent['dd']) <= 6.0,
    'positive_years_ge_2': positive_years >= 2,
    'worst_year_pf_ge_0_90': worst_pf >= 0.90,
    'worst_year_roi_ge_minus_3': worst_roi >= -3.0,
    'harsh3y_roi_nonnegative': float(h3['roi']) >= 0.0,
    'harsh3y_pf_ge_1': float(h3['pf']) >= 1.0,
    'harsh_recent_pf_ge_1_35': float(hr['pf']) >= 1.35,
    'harsh_recent_dd_le_6_8': float(hr['dd']) <= 6.8,
    'growth3_shadow_no_live_trades': attrib['3y']['growth3_live']['trades'] == 0 and attrib['recent']['growth3_live']['trades'] == 0,
}

architecture_gates = {
    'engineering_invariants': engineering_pass,
    'm30_abcd_shadow_no_live_trades': attrib['3y']['m30_abcd_live']['trades'] == 0 and attrib['recent']['m30_abcd_live']['trades'] == 0,
    'deferred_live_trades_are_reciprocal_only': deferred_only_reciprocal,
}

commercial_freeze_eligible = all(formal_gates.values()) and all(architecture_gates.values())
status = 'PASS' if commercial_freeze_eligible else 'REJECT'

payload = {
    'candidate': 'BTC Harmonic Guard Commercial RC7A Final Arbitration',
    'policy_version': policy['policy_version'],
    'policy_sha256': hashlib.sha256(POLICY.read_bytes()).hexdigest(),
    'status': status,
    'engineering_status': 'PASS' if engineering_pass else 'FAIL',
    'commercial_freeze_eligible': commercial_freeze_eligible,
    'architecture': {
        'direct_execute_market_order_calls': direct_total,
        'central_execute_market_order_calls': central_direct,
        'generated_main_direct_calls': main_direct,
        'direct_calls_by_file': direct_by_file,
        'counterfactual_starts': cf_starts,
        'counterfactual_resolves': cf_resolves,
        'deferred_events': defer_events,
        'deferred_execute_events': defer_execute_events,
    },
    'engineering_gates': engineering,
    'formal_commercial_gates': formal_gates,
    'architecture_gates': architecture_gates,
    'summary': summary,
    'attribution': attrib,
    'derived': {
        'positive_years': positive_years,
        'worst_year_pf': worst_pf,
        'worst_year_roi': worst_roi,
    },
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps(payload, indent=2))

if not engineering_pass:
    raise SystemExit(2)
