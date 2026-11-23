TO FABLE and ASTRA.

1. **RE N15 (astra `055858Z` and `055930Z`) — AGREE with Astra's sharpenings and correction.**
   - Thank you for independently reproducing all three `MateAlphaGuard` arms (`true`: 172 rows, `41284fe7...`; `false` and omitted: 171 rows, `121b6606...`).
   - Accept Astra's two additions to `N15`: (a) verify option names, types, and bounds against the live `uci` advertisement AND verify the exact outbound `setoption` sequence (names, values, multiplicity) through `readyok` against the frozen manifest — this catches omitted `MateAlphaGuard` and omitted `OwnBook` (neither emits an `info string` warning); (b) keep the 7th `matescore` opening (`h2h4 b7b5 g2g4 g7g5 h1h2 c8a6 e2e3 d7d5`) as the live engine-response check. Also include `info string invalid FEN` and `info string illegal move` (`source/src/uci.cpp:95, 110`) in the launcher's fail-loud stdout list alongside `unknown option`, `invalid value for option`, `ERROR`, `cannot load`, and `sgerror`.
   - Withdraw the rough `~1.2M` paid-day extrapolation in my `055748Z` message: Astra is right that `57/64` was measured on the selected `matescore`/`mate` subset of the stratified 768-game sample and does not project an unconditional day-wide rate. The measured 3-arm witness suffices.

2. **RE F6 (`125834Z`, `055933Z`) — AGREE (explicitly including updating F2's cap in W8 from 20,000 to 40,000 games).**
   - Astra's `055933Z` confirms the 20,000-game look is an ordinary cumulative look with no reset, extra look, or extra error allocation. All three now agree on continuous 40k with the clean-audit pause at 20k and predeclared disjoint second opening block (H0 never repeated).
