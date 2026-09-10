# BTC Harmonic Guard RC7B — Commercial Freeze

Status: **PASS / commercial_freeze_eligible=true**

Validated source commit: `3279bf0562c01bc0dfa6053a93462ccd383fd179`  
Workflow run: `34487265573`  
Artifact ID: `10156977935`  
Artifact digest: `sha256:f00510bb80043122060fa3e39db969d9843e65b17c8e01514bfbee8bcf73e551`

## Frozen performance

- 3Y: 261 trades, ROI +38.30%, PF 1.55, Max Equity DD 11.4988%
- Recent 1Y: 97 trades, ROI +33.46%, PF 2.44, Max Equity DD 3.8432%
- Y1: +8.75%, PF 1.33
- Y2: -1.36%, PF 0.93
- Y3: +33.46%, PF 2.44
- Harsh 3Y: +2.58%, PF 1.04, DD 13.2931%
- Harsh Recent: +10.99%, PF 1.45, DD 3.8630%

## Frozen engineering gates

- Compile: 0 errors
- Round22 3Y/1Y hash parity: PASS
- Direct `ExecuteMarketOrder(` calls in generated compile set: exactly 1, centralized in `Commercial.IntentExecution.cs`
- M30 ABCD: shadow only
- Growth3: shadow only
- Max open positions: 1
- Hedging/Grid/Martingale/DCA/Recovery/Loss Averaging: forbidden
- Live trades require SL/TP

## Mobile / Cloud binary

`BTC-Harmonic-Guard-RC7B-Commercial-Mobile.algo`  
SHA256: `be97fde0489c2392300deb4543d2dc3d00a50fc20d3d54ff4a2a6ef48a8ac31d`  
Size: 83,982 bytes

This directory is a frozen commercial evidence package. Any later strategy change must use a new version/candidate and rerun the complete frozen validation.
