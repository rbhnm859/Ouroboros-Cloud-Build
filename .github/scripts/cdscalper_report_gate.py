#!/usr/bin/env python3
import argparse
import json
import math
import sys
from pathlib import Path


def get_all(obj, key, default=0.0):
    value = obj.get(key, default)
    if isinstance(value, dict):
        return value.get("all", default)
    return value


def finite_float(value, default=0.0):
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def load_metrics(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    main = data.get("main", {})
    stats = data.get("tradeStatistics", {})
    equity = data.get("equity", {})

    trades = int(get_all(stats, "totalTrades", 0) or 0)
    wins = int(get_all(stats, "winningTrades", 0) or 0)
    metrics = {
        "symbol": main.get("symbol"),
        "period": main.get("period"),
        "testingPeriod": main.get("testingPeriod", {}).get("formatted"),
        "dataType": main.get("data", {}).get("type"),
        "accountLeverage": finite_float(main.get("accountLeverage")),
        "startingCapital": finite_float(main.get("startingCapital")),
        "endingBalance": finite_float(main.get("endingBalance")),
        "roiPercent": finite_float(main.get("roi")),
        "netProfit": finite_float(main.get("netProfit")),
        "profitFactor": finite_float(get_all(stats, "profitFactor", 0)),
        "trades": trades,
        "wins": wins,
        "losses": int(get_all(stats, "losingTrades", 0) or 0),
        "winRatePercent": (100.0 * wins / trades) if trades else 0.0,
        "averageTrade": finite_float(get_all(stats, "averageTrade", 0)),
        "largestWinningTrade": finite_float(get_all(stats, "largestWinningTrade", 0)),
        "largestLosingTrade": finite_float(get_all(stats, "largestLosingTrade", 0)),
        "commissions": finite_float(get_all(stats, "commissions", 0)),
        "maxEquityDrawdownPercent": finite_float(equity.get("maxEquityDrawdownPercent")),
        "maxEquityDrawdownAbsolute": finite_float(equity.get("maxEquityDrawdownAbsolute")),
        "longProfitFactor": finite_float((stats.get("profitFactor") or {}).get("long", 0)),
        "shortProfitFactor": finite_float((stats.get("profitFactor") or {}).get("short", 0)),
        "longNetProfit": finite_float((stats.get("netProfit") or {}).get("long", 0)),
        "shortNetProfit": finite_float((stats.get("netProfit") or {}).get("short", 0)),
        "spread": main.get("spread"),
        "commissionModel": main.get("commissions"),
    }
    return metrics


def environment_checks(m):
    commission = m.get("commissionModel") or {}
    spread = m.get("spread") or {}
    data_type = str(m.get("dataType") or "").lower()
    return {
        "symbol_EURUSD": m.get("symbol") == "EURUSD",
        "period_M1": str(m.get("period") or "").lower() == "m1",
        "tick_data": "tick" in data_type,
        "leverage_500": abs(m.get("accountLeverage", 0) - 500.0) <= 0.01,
        "starting_capital_30": abs(m.get("startingCapital", 0) - 30.0) <= 0.001,
        "spread_fixed_0_43": str(spread.get("type", "")).lower() == "fixed" and abs(finite_float(spread.get("value")) - 0.43) <= 0.0001,
        "commission_type_usd_per_million": str(commission.get("type", "")).lower() == "usdpermillionusdvolume",
        "commission_value_35": abs(finite_float(commission.get("value")) - 35.0) <= 0.001,
        "commission_not_auto": commission.get("applyCommissionAutomatically") is False,
    }


def strategy_gate(m, profile):
    roi = m["roiPercent"]
    pf = m["profitFactor"]
    trades = m["trades"]
    dd = m["maxEquityDrawdownPercent"]
    largest_loss = m["largestLosingTrade"]
    expectancy = m["averageTrade"]
    net = m["netProfit"]

    if profile == "control":
        return {"informational_only": True}
    if profile == "is":
        return {
            "roi_positive": roi > 0,
            "pf_at_least_1_15": pf >= 1.15,
            "trades_at_least_50": trades >= 50,
            "dd_at_most_15": dd <= 15,
            "largest_loss_at_least_minus_1": largest_loss >= -1.0,
            "post_cost_expectancy_positive": expectancy > 0,
        }
    if profile == "oos":
        return {
            "roi_positive": roi > 0,
            "pf_at_least_1_20": pf >= 1.20,
            "trades_at_least_50": trades >= 50,
            "dd_at_most_15": dd <= 15,
            "largest_loss_at_least_minus_1": largest_loss >= -1.0,
            "post_cost_expectancy_positive": expectancy > 0,
        }
    if profile == "full":
        return {
            "roi_at_least_10": roi >= 10.0,
            "pf_at_least_1_20": pf >= 1.20,
            "trades_at_least_100": trades >= 100,
            "dd_at_most_15": dd <= 15,
            "net_positive": net > 0,
            "post_cost_expectancy_positive": expectancy > 0,
        }
    if profile == "stress15":
        return {
            "pf_at_least_1_0": pf >= 1.0,
            "net_nonnegative": net >= 0,
            "dd_at_most_20": dd <= 20,
        }
    raise ValueError(profile)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--profile", choices=["control", "is", "oos", "full", "stress15"], default="control")
    parser.add_argument("--out")
    parser.add_argument("--fail-on-gate", action="store_true")
    args = parser.parse_args()

    m = load_metrics(args.report)
    env = environment_checks(m)
    strategy = strategy_gate(m, args.profile)
    env_pass = all(env.values())
    strategy_pass = all(strategy.values()) if args.profile != "control" else True
    payload = {
        "report": str(args.report),
        "profile": args.profile,
        "environment": env,
        "environmentPass": env_pass,
        "metrics": m,
        "strategyGate": strategy,
        "strategyPass": strategy_pass,
        "overallPass": env_pass and strategy_pass,
    }

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    print(rendered)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")

    if args.fail_on_gate and not payload["overallPass"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
