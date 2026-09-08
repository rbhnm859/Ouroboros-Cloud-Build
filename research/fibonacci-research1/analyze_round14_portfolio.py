#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_report(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = list((data.get("history") or {}).get("items") or [])
    items.sort(key=lambda x: (int(x.get("entryTime", 0)), int(x.get("closeTime", 0)), int(x.get("id", 0))))
    return items


def metric(items: List[dict]) -> dict:
    wins = [x for x in items if float(x.get("net", 0.0)) > 0]
    losses = [x for x in items if float(x.get("net", 0.0)) < 0]
    gp = sum(float(x.get("net", 0.0)) for x in wins)
    gl = -sum(float(x.get("net", 0.0)) for x in losses)
    net = sum(float(x.get("net", 0.0)) for x in items)
    return {
        "trades": len(items),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (100.0 * len(wins) / len(items)) if items else 0.0,
        "net": net,
        "profit_factor": (gp / gl) if gl > 0 else (999.0 if gp > 0 else 0.0),
        "avg_net": (net / len(items)) if items else 0.0,
    }


def classify(h1: List[dict], m30: List[dict]) -> Tuple[List[dict], dict]:
    rows: List[dict] = []
    windows = (1, 3, 6, 12, 24)
    for i, m in enumerate(m30):
        mt = int(m["entryTime"])
        md = str(m.get("direction", "")).lower()
        nearest_any = None
        nearest_same = None
        nearest_any_delta = None
        nearest_same_delta = None
        inside = False
        inside_same = False
        counts = {f"same_{h}h": 0 for h in windows}
        counts.update({f"any_{h}h": 0 for h in windows})
        for h in h1:
            ht = int(h["entryTime"])
            delta_ms = abs(ht - mt)
            if nearest_any_delta is None or delta_ms < nearest_any_delta:
                nearest_any_delta = delta_ms
                nearest_any = h
            same_dir = str(h.get("direction", "")).lower() == md
            if same_dir and (nearest_same_delta is None or delta_ms < nearest_same_delta):
                nearest_same_delta = delta_ms
                nearest_same = h
            for wh in windows:
                if delta_ms <= wh * 3600 * 1000:
                    counts[f"any_{wh}h"] = 1
                    if same_dir:
                        counts[f"same_{wh}h"] = 1
            if int(h["entryTime"]) <= mt <= int(h["closeTime"]):
                inside = True
                if same_dir:
                    inside_same = True
        row = {
            "m30_index": i,
            "m30_id": m.get("id"),
            "entryTime": mt,
            "closeTime": int(m["closeTime"]),
            "direction": md,
            "net": float(m.get("net", 0.0)),
            "inside_h1_position": int(inside),
            "inside_same_h1_position": int(inside_same),
            "nearest_h1_delta_hours": (nearest_any_delta / 3600000.0) if nearest_any_delta is not None else None,
            "nearest_same_h1_delta_hours": (nearest_same_delta / 3600000.0) if nearest_same_delta is not None else None,
            "nearest_h1_direction": (nearest_any or {}).get("direction"),
            "nearest_same_h1_id": (nearest_same or {}).get("id"),
        }
        row.update(counts)
        rows.append(row)

    def subset(pred):
        picked = [m30[r["m30_index"]] for r in rows if pred(r)]
        return metric(picked)

    summary = {
        "h1": metric(h1),
        "m30": metric(m30),
        "m30_inside_h1_position": subset(lambda r: bool(r["inside_h1_position"])),
        "m30_outside_h1_position": subset(lambda r: not bool(r["inside_h1_position"])),
        "m30_outside_h1_position_buy": subset(lambda r: not bool(r["inside_h1_position"]) and r["direction"] == "buy"),
        "m30_outside_h1_position_sell": subset(lambda r: not bool(r["inside_h1_position"]) and r["direction"] == "sell"),
    }
    for wh in windows:
        summary[f"m30_same_direction_within_{wh}h"] = subset(lambda r, wh=wh: bool(r[f"same_{wh}h"]))
        summary[f"m30_no_same_direction_within_{wh}h"] = subset(lambda r, wh=wh: not bool(r[f"same_{wh}h"]))

    # Causal first-come, max one position. H1 wins only exact timestamp ties.
    events = []
    for src, pri, trades in (("H1", 0, h1), ("M30", 1, m30)):
        for idx, t in enumerate(trades):
            events.append((int(t["entryTime"]), pri, src, idx, t))
    events.sort(key=lambda x: (x[0], x[1]))
    accepted = []
    open_until = -1
    for et, _pri, src, idx, t in events:
        if et >= open_until:
            x = dict(t)
            x["portfolio_source"] = src
            x["source_index"] = idx
            accepted.append(x)
            open_until = int(t["closeTime"])
    summary["first_come_one_position_approx"] = metric(accepted)
    summary["first_come_sources"] = {
        "h1": sum(1 for x in accepted if x["portfolio_source"] == "H1"),
        "m30": sum(1 for x in accepted if x["portfolio_source"] == "M30"),
    }
    return rows, summary


def locate(root: Path, engine: str, test: str) -> Path:
    candidates = [
        root / f"btc-r14-{engine}-{test}" / "report.json",
        root / f"btc-r14-{engine}_{test}" / "report.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    matches = list(root.glob(f"**/btc-r14-{engine}-{test}/report.json"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"No report for {engine}/{test} under {root}")


def fmt(m: dict) -> str:
    return f"{m['trades']} | {m['win_rate']:.1f}% | {m['net']:+.2f} | {m['profit_factor']:.2f} | {m['avg_net']:+.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    tests = ["full6", "full6_harsh", "oos", "oos_harsh"]
    all_summary: Dict[str, dict] = {}
    for test in tests:
        h1 = load_report(locate(args.results_root, "h1", test))
        m30 = load_report(locate(args.results_root, "m30", test))
        rows, summary = classify(h1, m30)
        all_summary[test] = summary
        csv_path = args.out / f"round14_{test}_m30_classification.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["m30_index"])
            w.writeheader()
            w.writerows(rows)

    (args.out / "round14_overlap_summary.json").write_text(json.dumps(all_summary, indent=2), encoding="utf-8")

    md = [
        "# BTC Round14 H1 + M30 Harmonic Portfolio / Signal Overlap",
        "",
        "This stage changes no strategy parameters. It compares the frozen H1 Growth Champion against the frozen Round13 M30 Reciprocal ABCD candidate.",
        "",
        "Metrics below are trade-list diagnostics. `first_come_one_position_approx` is an overlap approximation based on standalone trade histories, not a substitute for a true combined-equity backtest because risk sizing compounds on separate standalone balances.",
        "",
    ]
    for test in tests:
        s = all_summary[test]
        md += [
            f"## {test}",
            "",
            "| Slice | Trades | Win rate | Net | PF | Avg net |",
            "|---|---:|---:|---:|---:|---:|",
            f"| H1 | {fmt(s['h1'])} |",
            f"| M30 | {fmt(s['m30'])} |",
            f"| M30 during H1 position | {fmt(s['m30_inside_h1_position'])} |",
            f"| M30 outside H1 position | {fmt(s['m30_outside_h1_position'])} |",
            f"| M30 outside H1 position — Buy | {fmt(s['m30_outside_h1_position_buy'])} |",
            f"| M30 outside H1 position — Sell | {fmt(s['m30_outside_h1_position_sell'])} |",
            f"| M30 same-direction within 6h of H1 | {fmt(s['m30_same_direction_within_6h'])} |",
            f"| M30 no same-direction H1 within 6h | {fmt(s['m30_no_same_direction_within_6h'])} |",
            f"| First-come one-position approximation | {fmt(s['first_come_one_position_approx'])} |",
            "",
            f"First-come sources: H1={s['first_come_sources']['h1']}, M30={s['first_come_sources']['m30']}",
            "",
        ]
    (args.out / "round14_overlap_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(args.out / "round14_overlap_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
