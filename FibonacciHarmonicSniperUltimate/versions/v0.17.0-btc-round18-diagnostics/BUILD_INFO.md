# Round18 Diagnostics Build Info

## Anchor / provenance
- Published Round17 Mobile anchor: `FibonacciHarmonicSniperUltimate-BTC-Round17-Mobile.algo`
- Published Mobile SHA-256: `c1adca6e37ac50e97d4e124572439ca0b9063de8c661866aae9ffed3fcde874a`
- Exact Round17 M30HalfRisk source version: `v0.16.0-btc-round17-m30-half-risk`
- Exact Round17 source SHA-256: `b414173f9d5aa3e4fdd9c4b1f28cf0f048b736ebff190b0611956479794e3112`
- Exact backtested Round17 M30HalfRisk .algo SHA-256: `4f49692a38b9b1d537c3003ed1bc9fd87402884f8eb6b5f8d90985e25dbcf8d0`

The published Mobile binary and exact backtested M30HalfRisk binary are not byte-identical, so Round18 is based on the preserved exact Round17 source/build bundle rather than reverse engineering the published binary.

## Round18 Diagnostics
- Version: `v0.17.0-btc-round18-diagnostics`
- Source SHA-256 after reconstruction: `5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93`
- Source payload SHA-256 (concatenated gzip+base64 parts): `00705a04fa65bba2b1725b812d3b6523a27a99ecc2bb9a7b2fc1026abf2fb60e`
- Target framework: `net6.0`
- cTrader Automate package: `1.*-*` (current restore resolves 1.0.19)

## Economics policy
R18-Diagnostics must remain logic-neutral. H1/M30 entry thresholds, order comments, risk split, shared position limit, daily trade cap and Round16 H1-health execution gate are unchanged. CI runs the exact Round17 standard and harsh one-year parameter sets and fails the neutrality gate if trade count changes or ROI/PF/DD diverge beyond the tight validation tolerance.
