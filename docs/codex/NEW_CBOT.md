# Independent New XAUUSD cBot — candidate AGENTS.md (not installed as root)

The new cBot project MUST use an explicitly selected separate repository or isolated branch. It is **not** V74 and must not be developed on `harmonybot/v73-opportunity-universe`.

Scope: cTrader C#, XAUUSD-only, compatible symbol/point/tick/volume-step and broker profiles (FxPro where verified), daylight-saving-aware sessions, $100 initial-capital test. Harmonic pattern family recognition, long/short signals, completed-bar confirmation, executable price/fees/slippage/margin and no lookahead.

One active basket and no simultaneous hedging, Martingale, DCA, recovery, averaging losses, stop widening or duplicate thesis. Requested Grid multipliers conflict with these invariants if they require loss averaging or extra exposure: do not implement this conflicted behavior without distinct approved semantics.

User-proposed goals: annual trades >=500, MeanR >=0.90, PF_R>=3.30, WR>=60%, AvgRR>=2.30, LCB95>0, monthly compounding 12%. **Aspirational, not guaranteed**. Independently validated OOS years required; no use of V74 historic results as new-bot proof.

Process: choose branch -> inspect baseline -> propose narrow reversible patch -> real compilation/CI -> actual cTrader backtest -> statistical OOS and risk review -> PR review. Never place live orders, expose secrets, force-push or merge/deploy automatically.

When using this file: create a separately scoped root AGENTS.md on the new branch rather than copying both project policies to a single root.
