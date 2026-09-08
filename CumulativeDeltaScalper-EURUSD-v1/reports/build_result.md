# Build Result

## Status

Prepared source code has been uploaded to GitHub branch:

`cumulative-delta-scalper-eurusd-v1`

## cTrader compile status

Not compiled in this environment.

Reason: ChatGPT/GitHub connector does not provide cTrader Automate or cTrader CLI build runtime, so generating a real `.algo` artifact here would be dishonest.

## Next required build step

1. Open cTrader Desktop.
2. Go to Automate.
3. Create a new cBot named `CumulativeDeltaScalper_EURUSD_v1`.
4. Replace the generated code with:
   `CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs`
5. Click Build.
6. If cTrader reports API-version errors, record the exact error message in this file before patching.

## Expected artifact

After successful cTrader build:

`builds/CumulativeDeltaScalper_EURUSD_v1.algo`
