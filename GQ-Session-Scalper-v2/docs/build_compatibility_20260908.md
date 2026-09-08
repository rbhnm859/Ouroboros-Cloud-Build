# Build Compatibility — 2026-09-08

Official container tested: `ghcr.io/spotware/ctrader-console:latest`.

Observed toolchain in CI: .NET SDK 6.0.100, so the project targets `net6.0`.

Compatibility changes made without changing the intended trading semantics:

- Original unavailable `Momentum` API replaced by a close-to-close momentum ratio on completed bars, preserving the original 100 centerline convention.
- Proportional equity risk sizing uses `Symbol.AmountRisked(...)` to scale and verify normalized `VolumeInUnits`, avoiding an unavailable `RiskType` enum while preserving equity-budget sizing.
- Stop modification uses the current absolute-protection overload with `ProtectionType.Absolute`.

These changes are build/API compatibility work only and do not constitute profitability validation.
