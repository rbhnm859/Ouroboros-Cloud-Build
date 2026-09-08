# GQ v2 Stop-Distance Validation

Source patch commit: `09caa783a22d8c5d4a20b57fafb9a1959f4b4c09`

Root cause from the first June stop diagnostic:
- duplicate identical stop requests after a successful modification: 0;
- two ATR trailing requests failed with `InvalidStopLossTakeProfit`;
- FxPro symbol metadata reported MinSL=0, so using the broker minimum alone could place a rounded stop effectively at the current market price.

Patch:
- retain the broker minimum-distance rule;
- additionally require an execution buffer of at least two ticks (or 0.2 pip, whichever is larger) before stop rounding;
- keep the last-successful-stop de-duplication logic.

Gate: native build must pass before the same 2026-06-08 to 2026-06-30 EURUSD M15 diagnostic is repeated.
