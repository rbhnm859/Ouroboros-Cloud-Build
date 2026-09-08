#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

SYMBOLS = ["EURUSD", "XAUUSD", "BITCOIN", "ETHEREUM"]

def find_key(obj, wanted):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == wanted.lower():
                return v
            r = find_key(v, wanted)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, wanted)
            if r is not None:
                return r
    return None

def metrics(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    main = d.get("main", {})
    stats = d.get("tradeStatistics", {})
    eq = d.get("equity", {})
    total = stats.get("totalTrades", {})
    wins = stats.get("winningTrades", {})
    losses = stats.get("losingTrades", {})
    trades = int(total.get("all", 0) or 0)
    win_count = int(wins.get("all", 0) or 0)
    loss_count = int(losses.get("all", max(0, trades-win_count)) or 0)
    pf_raw = find_key(d, "profitFactor")
    try:
        pf = float(pf_raw) if pf_raw is not None else None
    except (TypeError, ValueError):
        pf = None
    dd = float(eq.get("maxEquityDrawdownPercent", 0.0) or 0.0)
    net = float(main.get("netProfit", 0.0) or 0.0)
    roi = float(main.get("roi", 0.0) or 0.0)
    win_rate = (100.0 * win_count / trades) if trades else None
    score = roi - 0.75 * dd
    if pf is not None and math.isfinite(pf):
        score += min(pf, 3.0) * 2.0
    screening_pass = trades >= 10 and net > 0 and dd <= 15.0
    if pf is not None and math.isfinite(pf):
        screening_pass = screening_pass and pf >= 1.10
    return {
        "trades": trades,
        "wins": win_count,
        "losses": loss_count,
        "win_rate": win_rate,
        "net_profit": net,
        "roi": roi,
        "max_equity_dd_percent": dd,
        "profit_factor": pf,
        "score": score,
        "screening_pass": screening_pass,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports-dir", type=Path, required=True)
    ap.add_argument("--json-output", type=Path, required=True)
    ap.add_argument("--md-output", type=Path, required=True)
    a = ap.parse_args()
    rows = []
    for p in sorted(a.reports_dir.rglob("*.json")):
        symbol = next((s for s in SYMBOLS if p.stem.endswith("-" + s)), None)
        if not symbol:
            continue
        profile = p.stem[:-(len(symbol)+1)]
        m = metrics(p)
        rows.append({"symbol": symbol, "profile": profile, **m})
    best = {}
    for s in SYMBOLS:
        candidates = [r for r in rows if r["symbol"] == s]
        eligible = [r for r in candidates if r["screening_pass"]]
        pool = eligible or candidates
        best[s] = max(pool, key=lambda r: r["score"]) if pool else None
    result = {
        "window_utc": {"start": "2026-06-08 00:00", "end": "2026-09-08 00:00"},
        "period": "H1",
        "data_mode": "M1 server data",
        "research_balance_usd": 10000,
        "risk_percent_equity": 1.0,
        "commission": "cTrader CLI/account default for console 5.9.11 (no explicit --commission override)",
        "spread": "cTrader CLI/account default (no explicit --spread override in this screening pass)",
        "rows": rows,
        "best_by_symbol": best,
        "note": "Three-month screening only; not untouched OOS approval or a guarantee of live profitability."
    }
    a.json_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "# Fibonacci Harmonic Sniper v0.4.0 Research1 — 3M / 4-symbol screening",
        "",
        "Window: 2026-06-08 00:00 UTC → 2026-09-08 00:00 UTC",
        "",
        "| Symbol | Best profile | Trades | Win rate | Net | ROI | Max DD | PF | Screen pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for s in SYMBOLS:
        r = best[s]
        if not r:
            lines.append(f"| {s} | no report | - | - | - | - | - | - | no |")
            continue
        wr = "-" if r["win_rate"] is None else f'{r["win_rate"]:.1f}%'
        pf = "-" if r["profit_factor"] is None else f'{r["profit_factor"]:.2f}'
        lines.append(
            f'| {s} | {r["profile"]} | {r["trades"]} | {wr} | {r["net_profit"]:.2f} | '
            f'{r["roi"]:.2f}% | {r["max_equity_dd_percent"]:.2f}% | {pf} | '
            f'{"yes" if r["screening_pass"] else "no"} |'
        )
    lines += ["", "Screening gate: >=10 trades, net profit > 0, max equity DD <=15%, and PF >=1.10 when PF is present."]
    a.md_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(a.md_output.read_text(encoding="utf-8"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
