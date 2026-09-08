# GQ v2 Stop-Only Protection Validation

Source commit: `44994eb85059e6dea735cdf6939f11ac979d67d5`

Change:
- `TryImproveStop` now uses `position.ModifyStopLossPrice(candidateStop)`.
- Existing Take Profit is not resent during Breakeven or Trailing stop amendments.
- Existing stop de-duplication and broker/execution-distance guards remain active.

Reason:
The two remaining June diagnostic failures occurred while attempting ATR trailing on positions with an existing TP. cTrader documents `Position.ModifyStopLossPrice` as the stop-loss-only shortcut for changing a position stop loss, avoiding unnecessary TP revalidation during an SL-only amendment.

Validation gates:
1. Native cTrader build: 0 errors.
2. Repeat EURUSD M15, 2026-06-08 to 2026-06-30 diagnostic.
3. At least one successful SL amendment.
4. Zero duplicate identical stop requests after success.
5. Zero `[STOP_UPDATE_ERROR]`.
6. Zero `InvalidStopLossTakeProfit` failures.
