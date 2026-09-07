# Fibonacci Harmonic Sniper Ultimate (cTrader Mobile/Cloud)

A cloud-compatible cTrader cBot built around confirmed-pivot Fibonacci / harmonic pattern recognition.

## Core behavior
- Confirmed non-repainting pivots (left/right confirmation bars)
- Bullish + bearish XABCD scanning
- Pattern score and ratio tolerance
- PRZ/D-point confirmation before entry
- EMA / ATR / spread filters
- Fixed lots, equity-risk %, or fixed-cash risk sizing
- Structure stop beyond D with ATR buffer
- Fibonacci AD targets or fixed R:R fallback
- Duplicate D-point protection, cooldown, max positions, max trades/day, daily equity drawdown gate
- Fibonacci direction remains authoritative; EMA can be Off, ScoreOnly, ConfirmOnly, or Strict
- Aggressive, Balanced, and Conservative D-point confirmation modes
- Opposing-pattern conflict arbitration using a configurable score advantage
- Maximum stop-distance gate and immediate close if a broker returns an unprotected position
- No Grid, no Martingale, no loss-multiplying logic

## Optimized V2 defaults
- `Confirmation Mode = Balanced`
- `EMA Filter Mode = ScoreOnly` (EMA improves ranking but does not override the pattern direction)
- `Min Score Advantage = 3` (skip unresolved bullish/bearish conflicts)
- `Max Stop = 0` (off; set a symbol-appropriate cap during backtesting)
- Every successful entry must contain both server-confirmed SL and TP. If either is absent, the bot closes the position immediately.

## Pattern selector
`Enabled Patterns` supports:
- `CORE` — canonical/common set
- `ALL` — entire built-in database
- comma/semicolon separated exact names, e.g. `Gartley,Bat,Crab,ABCD`

The built-in database contains 85 pattern definitions across canonical, Max, Anti, Swan, 121, Partizan, Total, BG and NN families. Additional definitions can be supplied without rebuilding using `Custom Pattern Ratios`.

Custom format:
`Name|xbMin|xbMax|acMin|acMax|bdMin|bdMax|xdMin|xdMax;NextName|...`

## Mobile installation
1. Fastest mobile route: upload `.github/workflows/build-fibonacci-harmonic-sniper-ultimate.yml` to the same path in your GitHub repo. It contains the full source payload and builds with official cTrader CLI 5.9.11.
2. In GitHub Actions, run **Build Fibonacci Harmonic Sniper Ultimate Mobile** and download the `FibonacciHarmonicSniperUltimate-Mobile` artifact.
3. Extract `FibonacciHarmonicSniperUltimate.algo`.
4. On Android, tap the `.algo` file and open it with cTrader, or use cTrader Algo > Upload.
5. Open cBots, select the bot and create a **Cloud** instance.
6. Choose symbol + timeframe and review parameters.
7. `Trading Enabled` defaults to **false**. Turn it on only after backtesting/demo validation.

## Suggested first validation
Start with `Enabled Patterns = CORE`, a higher timeframe such as M15/H1, and demo/backtest before enabling `ALL`. Extended databases contain community-defined variants with wider ratio windows, so enabling all increases signal frequency and overlap.
