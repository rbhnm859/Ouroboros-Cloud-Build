"""Normalize only measured CLI report fields. Missing evidence stays null."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for tf in ('M1', 'M5', 'M15', 'M30'):
    raw = root / 'backtests' / 'raw' / f'EURUSD_{tf.lower()}.json'
    rc_path = raw.with_suffix('.exitcode')
    rc = int(rc_path.read_text()) if rc_path.exists() else None
    result = {
        'symbol': 'EURUSD', 'timeframe': tf,
        'status': 'not_run', 'backtest_period': None, 'initial_balance': None,
        'planned_period_utc': {'start': '2026-08-31T00:00:00Z', 'end': '2026-09-07T00:00:00Z'},
        'planned_initial_balance': 100, 'data_mode': 'ticks',
        'cost_assumptions': {'spread_pips': 1, 'commission_per_million': 35, 'broker_verified': False},
        'net_profit': None, 'profit_factor': None, 'win_rate': None,
        'max_drawdown': None, 'total_trades': None, 'average_trade': None,
        'largest_loss': None, 'largest_win': None, 'consecutive_losses': None,
        'daily_loss_guard_triggered': None, 'duplicate_positions': None,
        'every_trade_has_sl_tp': None, 'unprotected_positions': None,
        'invalid_request': None, 'volume_below_broker_minimum': None,
        'suitable_for_optimization': None, 'cli_exit_code': rc,
        'notes': 'No backtest executed. Requires cTrader runtime, authenticated broker data and available credentials.',
    }
    if rc is not None:
        result['status'] = 'failed_or_incomplete'
        result['notes'] = 'Inspect raw CLI log and exit code. Performance and trade protection are unverified.'
    if raw.exists() and rc == 0:
        d = json.loads(raw.read_text())
        m, t = d.get('main', {}), d.get('tradeStatistics', {})
        def stat(name):
            value = t.get(name)
            return value.get('all') if isinstance(value, dict) else value
        n, wins = stat('totalTrades'), stat('winningTrades')
        result.update(status='completed_requires_event_audit', symbol=m.get('symbol', 'EURUSD'),
                      backtest_period=m.get('testingPeriod'), initial_balance=m.get('startingCapital'),
                      net_profit=m.get('netProfit'), profit_factor=stat('profitFactor'),
                      total_trades=n, win_rate=100 * wins / n if n and wins is not None else None,
                      max_drawdown={'equity_percent': d.get('equity', {}).get('maxEquityDrawdownPercent')},
                      average_trade=m.get('netProfit') / n if n and m.get('netProfit') is not None else None,
                      largest_loss=stat('largestLosingTrade'), largest_win=stat('largestWinningTrade'),
                      consecutive_losses=stat('maxConsecutiveLosingTrades'),
                      notes='Measured CLI report. Unknown fields remain null. Review events/logs for protection and duplicate entries; no profitability claim.')
    (root / 'backtests' / f'EURUSD_{tf}_baseline.json').write_text(json.dumps(result, indent=2) + '\n')
