"""V73/R14 pure action supply adapter, frozen at c54da8c. No evaluator side effects."""
import bisect, json, math, os, pathlib, statistics, sys, time, multiprocessing as mp
from collections import defaultdict, Counter
from v74_model_lib import load_rows, metrics, SEQUENTIAL_STATE_FEATURE_COUNT, SURVIVAL_MORPH_FEATURE_COUNT, SURVIVAL_PATH_V2_FEATURE_COUNT, R7_COMMON_PATH_FEATURE_COUNT, FAMILIES, SURVIVAL_FRESH_KEYS, HIGH_CONVICTION_KEYS, REACTION_COMMIT_KEYS, FEATURE_NAMES
from v74_model_lib import event_identity
from harmonic_precision_contract import harmonic_precision_vector
RESEARCH = [f'Y{y}' for y in range(2016, 2021)]
BURNED = ['Y2021', 'Y2022', 'Y2023']
ALL = RESEARCH + BURNED
MIN_N = 250
TRAIN_COVERAGE = 275
MIN_MEAN = 0.9
MIN_PF = 3.3
MIN_WR = 0.7
MIN_AVG_RR = 2.3
LEGAL_MIN_RR = 2.0
Z = 1.645
SWEEP_ROUNDS = 100
SWEEP_CANDIDATES_PER_ROUND = 100
HISTORICAL_BEST_GUARD = {'run_id': 37255583101, 'head_sha': '0aa372d4', 'worst_gate_margin': -0.038921181358877614, 'median_gate_margin': 0.13716151265064236, 'min_mean_r': -0.035029063222989855, 'min_pf_r': 0.950163022662106, 'min_win_rate': 0.2914438502673797, 'min_lcb_r': -0.16393054369487778}
REGULAR_SOURCES = ('EARLY', 'LATE')
SOURCES = ('EARLY', 'LATE', 'SURVIVAL', 'REACTION', 'FAILURE')
EARLY_QUALIFICATION_FRACTION = '00'
EARLY_FRACTIONS = (EARLY_QUALIFICATION_FRACTION,)
LATE_FRACTIONS = ('20', '30')
ALL_FRACTIONS = (EARLY_QUALIFICATION_FRACTION,) + LATE_FRACTIONS
MSTAGES = ('05', '10', '15')
EARLY_MSTAGES = MSTAGES
LATE_MSTAGES = MSTAGES
BASES = [f'R{r}_{h}_RR{rr}' for r in ('025', '050') for h in ('H', 'D') for rr in ('35', '40')]
TREE_KFEAT = 30
PAIR_KFEAT = 26
TREE_ROUNDS = 10
PAIR_ROUNDS = 8
TREE_DEPTH = 3
TOP_PAIR = 6

def gate(m):
    return bool(m['n'] >= MIN_N and m['mean_r'] >= MIN_MEAN and (m['pf_r'] >= MIN_PF) and (m['win_rate'] >= MIN_WR) and (m['average_rr'] >= MIN_AVG_RR) and (m['lcb_r'] > 0))

def qtile(v, q):
    if not v:
        return 0.0
    x = sorted((float(z) for z in v))
    p = (len(x) - 1) * q
    a = int(math.floor(p))
    b = int(math.ceil(p))
    return x[a] if a == b else x[a] * (b - p) + x[b] * (p - a)

def med(v, d=0.0):
    return statistics.median(v) if v else d

def _qtile_sorted(x, q):
    """qtile() equivalent for an already ascending numeric sequence."""
    if not x:
        return 0.0
    p = (len(x) - 1) * q
    a = int(math.floor(p))
    b = int(math.ceil(p))
    return float(x[a]) if a == b else float(x[a]) * (b - p) + float(x[b]) * (p - a)

def key(m, b, f):
    return f'M{m}_{b}_F{f}'

def lev(b):
    return '025' if b.startswith('R025_') else '050'

def source_maps(r, src):
    if src == 'EARLY':
        return (r.get('sequential', {}), r.get('sequential_rr', {}), r.get('sequential_bars', {}), r.get('sequential_entry_bar', {}), r.get('sequential_entry_state', {}))
    return (r.get('late_auction', {}), r.get('late_auction_rr', {}), r.get('late_auction_bars', {}), r.get('late_auction_entry_bars', {}), r.get('late_auction_entry_state', {}))

def outcome(r, src, m, b, f):
    om, rrm, _, _, _ = source_maps(r, src)
    k = key(m, b, f)
    v = om.get(k)
    rr = rrm.get(k)
    if v is None or rr is None:
        return None
    try:
        v = float(v)
        rr = float(rr)
    except:
        return None
    if not all((math.isfinite(x) for x in (v, rr))) or rr + 1e-09 < LEGAL_MIN_RR:
        return None
    return v

def entry_bar(r, src, m, b, f):
    _, _, _, bm, _ = source_maps(r, src)
    try:
        return int(bm.get(key(m, b, f), -1))
    except:
        return -1

def hold_bars(r, src, m, b, f):
    _, _, hm, _, _ = source_maps(r, src)
    try:
        return max(1, int(hm.get(key(m, b, f), r.get('bars', 1)) or 1))
    except:
        return max(1, int(r.get('bars', 1) or 1))

def maturity_state(r, src, m, b, f):
    if src == 'EARLY':
        v = r.get('sequential_state', {}).get(lev(b))
    else:
        v = r.get('late_auction_maturity_state', {}).get(key(m, b, f))
    if v is None or len(v) != SEQUENTIAL_STATE_FEATURE_COUNT:
        return None
    try:
        z = [float(x) for x in v]
        return z if all((math.isfinite(x) for x in z)) else None
    except:
        return None

def entry_state(r, src, m, b, f):
    _, _, _, _, em = source_maps(r, src)
    v = em.get(key(m, b, f))
    if v is None or len(v) != SEQUENTIAL_STATE_FEATURE_COUNT:
        return None
    try:
        z = [float(x) for x in v]
        return z if all((math.isfinite(x) for x in z)) else None
    except:
        return None

def timing_state(r, src, m, b, f, eb):
    k = key(m, b, f)
    if src == 'EARLY':
        rb = r.get('sequential_reaction_bar', {}).get(k, -1)
        return [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, 0.0, 0.0]
    rb = r.get('late_auction_reaction_bars', {}).get(k, -1)
    ab = r.get('late_auction_anchor_bars', {}).get(k, -1)
    tb = r.get('late_auction_trigger_bars', {}).get(k, -1)
    return [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, max(-1.0, min(6.0, float(ab) / 10.0)) if ab is not None else -1.0, max(-1.0, min(6.0, float(tb) / 10.0)) if tb is not None else -1.0]

def common_path_r7(r, src, m, b, f):
    k = key(m, b, f)
    bank = r.get('sequential_path_r7', {}) if src == 'EARLY' else r.get('late_auction_path_r7', {})
    v = bank.get(k)
    if v is None or len(v) != R7_COMMON_PATH_FEATURE_COUNT:
        return None
    try:
        z = [float(x) for x in v]
        return z if all((math.isfinite(x) for x in z)) else None
    except:
        return None

def route_cats(r, src, b, m, f, sfkey=None, action_override=None):
    action = action_override or r['action']
    return [1.0 if r['family'] == ff else 0.0 for ff in FAMILIES] + [1.0 if action == 'CONTINUATION' else 0.0, 1.0 if src == 'LATE' else 0.0, 1.0 if src == 'SURVIVAL' else 0.0, 1.0 if src == 'REACTION' else 0.0, 1.0 if src == 'FAILURE' else 0.0, 1.0 if b.startswith('R050_') else 0.0, 1.0 if '_D_' in b else 0.0, 1.0 if b.endswith('RR40') else 0.0] + [1.0 if m == mm else 0.0 for mm in MSTAGES] + [1.0 if f == ff else 0.0 for ff in ALL_FRACTIONS] + [1.0 if sfkey == kk else 0.0 for kk in SURVIVAL_FRESH_KEYS]
_HARMONIC_PRECISION_CACHE = {}

def _precision_vector(r):
    k = (r.get('window'), r.get('setup'))
    z = _HARMONIC_PRECISION_CACHE.get(k)
    if z is None:
        z = tuple(harmonic_precision_vector(r.get('family', 'ABCD'), list(r.get('features', []))))
        _HARMONIC_PRECISION_CACHE[k] = z
    return list(z)

def xvec(r, src, m, b, f, eb):
    a = maturity_state(r, src, m, b, f)
    e = entry_state(r, src, m, b, f)
    ap = 1.0 if a is not None else 0.0
    ep = 1.0 if e is not None else 0.0
    aa = a if a is not None else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    ee = e if e is not None else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    delta = [ee[i] - aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    hp = _precision_vector(r)
    return list(r.get('features', [])) + hp + route_cats(r, src, b, m, f) + aa + ee + delta + [ap, ep, 1.0 if ap and ep else 0.0] + timing_state(r, src, m, b, f, eb) + [0.0] * SURVIVAL_MORPH_FEATURE_COUNT + (common_path_r7(r, src, m, b, f) or [0.0] * R7_COMMON_PATH_FEATURE_COUNT)

def survival_xvec(r, sf, eb):
    a = r.get('survival_fresh_maturity_state', {}).get(sf)
    e = r.get('survival_fresh_entry_state', {}).get(sf)
    ap = 1.0 if a is not None and len(a) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep = 1.0 if e is not None and len(e) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa = [float(x) for x in a] if ap else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    ee = [float(x) for x in e] if ep else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    delta = [ee[i] - aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    rb = r.get('survival_fresh_reaction_bar', {}).get(sf, -1)
    pb = r.get('survival_fresh_pullback_bar', {}).get(sf, -1)
    tb = r.get('survival_fresh_trigger_bar', {}).get(sf, -1)
    timing = [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, max(-1.0, min(6.0, float(pb) / 10.0)) if pb is not None else -1.0, max(-1.0, min(6.0, float(tb) / 10.0)) if tb is not None else -1.0]
    q = r.get('survival_fresh_morphology', {}).get(sf)
    morph = [float(x) for x in q] if q is not None and len(q) == SURVIVAL_MORPH_FEATURE_COUNT else [0.0] * SURVIVAL_MORPH_FEATURE_COUNT
    pv = r.get('survival_fresh_path_v2', {}).get(sf)
    path_v3 = [float(x) for x in pv] if pv is not None and len(pv) == SURVIVAL_PATH_V2_FEATURE_COUNT else [0.0] * SURVIVAL_PATH_V2_FEATURE_COUNT
    hp = _precision_vector(r)
    return list(r.get('features', [])) + hp + route_cats(r, 'SURVIVAL', 'SURVIVAL', 'FIB', '00', sf) + aa + ee + delta + [ap, ep, 1.0 if ap and ep else 0.0] + timing + morph + path_v3

def proof_commit_xvec(r, hc, eb):
    """R9 high-conviction proof-commit vector, dimension-parity with SURVIVAL.

    All fields are frozen on completed causal bars by C#.  The common 32-D R7
    path is right-padded to the SURVIVAL Path-V4 width so the matched estimator
    sees one stable feature geometry across native survival and proof routes.
    """
    a = r.get('high_conviction_maturity_state', {}).get(hc)
    e = r.get('high_conviction_entry_state', {}).get(hc)
    ap = 1.0 if a is not None and len(a) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep = 1.0 if e is not None and len(e) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa = [float(x) for x in a] if ap else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    ee = [float(x) for x in e] if ep else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    delta = [ee[i] - aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    rb = r.get('high_conviction_reaction_bar', {}).get(hc, -1)
    bars = r.get('high_conviction_bars', {}).get(hc, 0)
    timing = [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, max(-1.0, min(6.0, float(eb - rb) / 10.0)) if rb is not None and rb >= 0 else -1.0, max(0.0, min(6.0, float(bars) / 10.0))]
    pv = r.get('high_conviction_path_r7', {}).get(hc)
    common = [float(x) for x in pv] if pv is not None and len(pv) == R7_COMMON_PATH_FEATURE_COUNT else [0.0] * R7_COMMON_PATH_FEATURE_COUNT
    if SURVIVAL_PATH_V2_FEATURE_COUNT < R7_COMMON_PATH_FEATURE_COUNT:
        raise SystemExit('V74-R9 proof path width exceeds SURVIVAL vector contract')
    path = common + [0.0] * (SURVIVAL_PATH_V2_FEATURE_COUNT - R7_COMMON_PATH_FEATURE_COUNT)
    hp = _precision_vector(r)
    return list(r.get('features', [])) + hp + route_cats(r, 'SURVIVAL', 'SURVIVAL', 'FIB', '00', None) + aa + ee + delta + [ap, ep, 1.0 if ap and ep else 0.0] + timing + [0.0] * SURVIVAL_MORPH_FEATURE_COUNT + path

def reaction_commit_xvec(r, rc, eb):
    """R11 fixed-payoff delayed reaction-commit vector.

    Maturity is the completed shadow +0.75R/+1.00R observation; entry is a later
    completed hold bar.  All telemetry is frozen before capital is committed.
    """
    a = r.get('reaction_commit_maturity_state', {}).get(rc)
    e = r.get('reaction_commit_entry_state', {}).get(rc)
    ap = 1.0 if a is not None and len(a) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep = 1.0 if e is not None and len(e) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa = [float(x) for x in a] if ap else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    ee = [float(x) for x in e] if ep else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    delta = [ee[i] - aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    rb = r.get('reaction_commit_reaction_bar', {}).get(rc, -1)
    bars = r.get('reaction_commit_bars', {}).get(rc, 0)
    timing = [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, max(-1.0, min(6.0, float(eb - rb) / 10.0)) if rb is not None and rb >= 0 else -1.0, max(0.0, min(6.0, float(bars) / 10.0))]
    pv = r.get('reaction_commit_path_r7', {}).get(rc)
    common = [float(x) for x in pv] if pv is not None and len(pv) == R7_COMMON_PATH_FEATURE_COUNT else [0.0] * R7_COMMON_PATH_FEATURE_COUNT
    if SURVIVAL_PATH_V2_FEATURE_COUNT < R7_COMMON_PATH_FEATURE_COUNT:
        raise SystemExit('V74-R11 reaction path width exceeds unified vector contract')
    path = common + [0.0] * (SURVIVAL_PATH_V2_FEATURE_COUNT - R7_COMMON_PATH_FEATURE_COUNT)
    hp = _precision_vector(r)
    return list(r.get('features', [])) + hp + route_cats(r, 'REACTION', 'REACTION', 'RC', '00', None) + aa + ee + delta + [ap, ep, 1.0 if ap and ep else 0.0] + timing + [0.0] * SURVIVAL_MORPH_FEATURE_COUNT + path

def failure_xvec(r, eb):
    a = r.get('failure_continuation_maturity_state', {}).get('FC230')
    e = r.get('failure_continuation_entry_state', {}).get('FC230')
    ap = 1.0 if a is not None and len(a) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep = 1.0 if e is not None and len(e) == SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa = [float(x) for x in a] if ap else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    ee = [float(x) for x in e] if ep else [0.0] * SEQUENTIAL_STATE_FEATURE_COUNT
    delta = [ee[i] - aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    bb = r.get('failure_continuation_break_bar', {}).get('FC230', -1)
    rb = r.get('failure_continuation_retest_bar', {}).get('FC230', -1)
    timing = [max(-1.0, min(6.0, float(eb) / 10.0)), max(-1.0, min(6.0, float(bb) / 10.0)) if bb is not None else -1.0, max(-1.0, min(6.0, float(rb) / 10.0)) if rb is not None else -1.0, max(-1.0, min(6.0, float(eb - rb) / 10.0)) if rb is not None and rb >= 0 else -1.0]
    hp = _precision_vector(r)
    pv = r.get('failure_continuation_path_r7', {}).get('FC230')
    path_r7 = [float(x) for x in pv] if pv is not None and len(pv) == R7_COMMON_PATH_FEATURE_COUNT else [0.0] * R7_COMMON_PATH_FEATURE_COUNT
    return list(r.get('features', [])) + hp + route_cats(r, 'FAILURE', 'FAILURE', 'FC230', '00', None, 'CONTINUATION') + aa + ee + delta + [ap, ep, 1.0 if ap and ep else 0.0] + timing + [0.0] * SURVIVAL_MORPH_FEATURE_COUNT + path_r7
_OPTION_CACHE = {}

def all_options(r, b):
    ck = (r['window'], r['setup'], b)
    if ck in _OPTION_CACHE:
        return _OPTION_CACHE[ck]
    z = []
    seen_early = set()
    for src in REGULAR_SOURCES:
        for m in EARLY_MSTAGES if src == 'EARLY' else LATE_MSTAGES:
            for f in EARLY_FRACTIONS if src == 'EARLY' else LATE_FRACTIONS:
                eb = entry_bar(r, src, m, b, f)
                if eb < 0:
                    continue
                y = outcome(r, src, m, b, f)
                if y is None:
                    continue
                bars = hold_bars(r, src, m, b, f)
                if src == 'EARLY':
                    sig = (b, f, int(eb))
                    if sig in seen_early:
                        continue
                    seen_early.add(sig)
                rid = 'EARLY|' + b if src == 'EARLY' else 'LATE|M' + m + '_' + b
                z.append({'rid': rid, 'src': src, 'm': m, 'b': b, 'f': f, 'y': float(y), 'bar': eb, 'bars': bars, 'x': xvec(r, src, m, b, f, eb)})
    _OPTION_CACHE[ck] = z
    return z

def make_samples(xs):
    out = []
    for r in xs:
        for b in BASES:
            for o in all_options(r, b):
                out.append({'window': r['window'], 'setup': r['setup'], 'family': r['family'], 'action': r['action'], 'source': o['src'], 'base': b, 'route': o['rid'], 'm': o['m'], 'fraction': o['f'], 'bar': o['bar'], 'bars': o['bars'], 'x': o['x'], 'y': o['y'], 'row': r})
        for sf in SURVIVAL_FRESH_KEYS:
            y = r.get('survival_fresh', {}).get(sf)
            rr = r.get('survival_fresh_rr', {}).get(sf)
            try:
                eb = int(r.get('survival_fresh_entry_bar', {}).get(sf, -1))
            except:
                eb = -1
            if y is None or rr is None or eb < 0 or (float(rr) + 1e-09 < LEGAL_MIN_RR):
                continue
            bars = max(1, int(r.get('survival_fresh_bars', {}).get(sf, r.get('bars', 1)) or 1))
            out.append({'window': r['window'], 'setup': r['setup'], 'family': r['family'], 'action': r['action'], 'source': 'SURVIVAL', 'base': 'SURVIVAL_' + sf, 'route': 'SURVIVAL|' + sf, 'bar': eb, 'bars': bars, 'x': survival_xvec(r, sf, eb), 'y': float(y), 'row': r})
        for hc in HIGH_CONVICTION_KEYS:
            y = r.get('high_conviction', {}).get(hc)
            rr = r.get('high_conviction_rr', {}).get(hc)
            try:
                eb = int(r.get('high_conviction_entry_bar', {}).get(hc, -1))
            except:
                eb = -1
            if y is None or rr is None or eb < 0 or (float(rr) + 1e-09 < LEGAL_MIN_RR):
                continue
            bars = max(1, int(r.get('high_conviction_bars', {}).get(hc, r.get('bars', 1)) or 1))
            out.append({'window': r['window'], 'setup': r['setup'], 'family': r['family'], 'action': r['action'], 'source': 'SURVIVAL', 'base': 'SURVIVAL_PROOF_' + hc, 'route': 'SURVIVAL|' + hc, 'bar': eb, 'bars': bars, 'x': proof_commit_xvec(r, hc, eb), 'y': float(y), 'row': r})
        for rc in REACTION_COMMIT_KEYS:
            y = r.get('reaction_commit', {}).get(rc)
            rr = r.get('reaction_commit_rr', {}).get(rc)
            try:
                eb = int(r.get('reaction_commit_entry_bar', {}).get(rc, -1))
            except:
                eb = -1
            if y is None or rr is None or eb < 0 or (float(rr) + 1e-09 < LEGAL_MIN_RR):
                continue
            bars = max(1, int(r.get('reaction_commit_bars', {}).get(rc, r.get('bars', 1)) or 1))
            out.append({'window': r['window'], 'setup': r['setup'], 'family': r['family'], 'action': r['action'], 'source': 'REACTION', 'base': 'REACTION_' + rc, 'route': 'REACTION|' + rc, 'bar': eb, 'bars': bars, 'x': reaction_commit_xvec(r, rc, eb), 'y': float(y), 'row': r})
        fy = r.get('failure_continuation', {}).get('FC230')
        frr = r.get('failure_continuation_rr', {}).get('FC230')
        try:
            feb = int(r.get('failure_continuation_entry_bar', {}).get('FC230', -1))
        except:
            feb = -1
        if fy is not None and frr is not None and (feb >= 0) and (float(frr) + 1e-09 >= LEGAL_MIN_RR):
            fbars = max(1, int(r.get('failure_continuation_bars', {}).get('FC230', r.get('bars', 1)) or 1))
            out.append({'window': r['window'], 'setup': r['setup'], 'family': r['family'], 'action': 'CONTINUATION', 'source': 'FAILURE', 'base': 'FAILURE_FC230', 'route': 'FAILURE|FC230', 'bar': feb, 'bars': fbars, 'x': failure_xvec(r, feb), 'y': float(fy), 'row': r})
    return out
