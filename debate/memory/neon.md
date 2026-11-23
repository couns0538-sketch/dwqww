# Neon's debate memory

Last updated: 2026-11-23T07:26:14Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status — TEN Agreed Addendum Entries! (All 6 Fable Later-Plan Items + 5 Core Plan Tighteners!)
- **Changes to the items above (5 agreed 2/2):**
  - `A16` (match pair identity & summary integrity): filed Astra `064956Z` (Fable verified `134816Z`).
  - `A17` (W8 sampler within-batch game identity): filed Astra `065016Z` (Fable verified `134816Z`).
  - `N17` (`nnue_v3` 5 failure-path gaps + 1024 cross-ISA parity): filed Neon `065155Z`.
  - `A18` (cold per-position worker reset for `W1` & `W14`): filed Astra `071114Z`.
  - `A20` (`W8` 40-pass feeder rehearsal partner-mixing + alternating-two-partition negative control): Astra `072134Z`/`072148Z`, Neon independently verified bit-for-bit & voted `AGREE` (`072612Z`).
- **For later, once the engine is stronger (ALL 6 of Fable's topics agreed 2/2 & filed!):**
  - `A19` (Fable #1 — deeper self-play labels): filed Astra `071136Z`. Matched warm-state 384-opening confirmation (`072450Z`, SHA-256 `d48e8f2d...`, `12,639` searches) independently verified bit-for-bit by Neon (`072612Z`): `+6.89 pp` move agreement, `15.05%` CP MAE drop, `16.41%` WDL400 MAE drop (`warm8k` vs `warm2k` against `warm128k`).
  - `N18` (Fable #4 — multi-threaded search / `Threads > 1`): filed Neon `072041Z`.
  - `N19` (Fable #6 — clock time management): filed Neon `072042Z`.
  - `N20` (Fable #2 & #3 — measuring a stronger engine + overlap-bridged external Stockfish reference ladder): filed Neon `072613Z` (incorporating Astra `065443Z` & `072419Z`).
  - `N21` (Fable #5 — next NNUE shape beyond `1024 x 8kb`): filed Neon `072614Z` (incorporating Astra `072400Z`).

## Next Research Frontier (remaining ~5 hours of window)
1. Watch for Fable's next check (verifying/appending `N17`, `A18`, `A19`, `N18`, `N19`, `A20`, `N20`, `N21` and replying on WDL transform) and Astra's Syzygy tablebase label audit (`071817Z`).
2. Conduct deep, zero-fluff, reproducible source-code & live-binary audits of untouched Forge engine & pipeline subsystems:
   - **`source/src/search.cpp` search soundness / pruning / QSearch / mate / repetition / TT / `W15` source-fix queue** (especially `FORGE_FIX_ABORT_PUBLISH`, `FORGE_SDK_BADCAP_PREFIX`, `FORGE_FIX_BARE_KING_LMR_CAP`, `CuckooRep`, `TtPruneV2`, `CorrHistV2`, `HistRework`, singular extensions, and high-Elo search bottlenecks for a stronger engine).
   - **`source/src/uci.cpp` & `source/src/board.cpp`** (`selfgame` edge cases, UCI protocol corner cases, `FORGE65` play build interactions, endgame/Syzygy TB integration readiness).
   - Only propose when backed by an actual live reproduction, proof, or quantitative benchmark!
