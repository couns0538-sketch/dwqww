# Neon's debate memory

Last updated: 2026-11-23T07:20:44Z (Neon's clock)
Phase: 4 POST-CLOSE ADDENDUM & LATER-PLAN RESEARCH (6-hour window through ~12:35-12:40Z; Fable checks ~every 30 min)

## Current Status
- Shared branch HEAD (before this push): `f9738253eb`; Astra branch HEAD: `3111c57d18`.
- **SEVEN Addendum entries agreed 2/2 and filed for Fable (`Changes to the items above`: 4; `For later, once the engine is stronger`: 3):**
  - *Changes to the items above:*
    - `A16` (match pair identity & summary integrity): Astra `064956Z` (Fable checked `134816Z`).
    - `A17` (W8 sampler within-batch game identity): Astra `065016Z` (Fable checked `134816Z`).
    - `N17` (`nnue_v3` 5 failure-path gaps + 1024 cross-ISA parity): Neon `065155Z`.
    - `A18` (cold per-position worker reset for `W1` & `W14`): Astra `071114Z`.
  - *For later, once the engine is stronger:*
    - `A19` (Fable #1 — deeper self-play labels, including Neon's `warm2k` finding): Astra `071136Z` (Astra also running full 384-opening warm replay `070804Z` and Syzygy tablebase audit `071817Z`).
    - `N18` (Fable #4 — multi-threaded search / `Threads > 1`): Neon `072041Z` (incorporating Astra `065443Z` & `071934Z`).
    - `N19` (Fable #6 — clock time management): Neon `072042Z` (incorporating Astra `071949Z`).
- **TWO new Neon later-plan proposals posted (`072043Z`, `072044Z`), covering ALL remaining items of Fable's 6-item list:**
  - `N20` (Fable #2 & #3 — Measuring a stronger engine [pair variance + calibrated contrast + `nElo`/UHO] & Overlap-Bridged Stockfish Reference Ladder [`>=0.75` trigger, 2×2 bridge, separate limited track]): unifies Astra `065443Z` + `PLAN.md §1` + `fable_f2_deep_pair_tables.txt`.
  - `N21` (Fable #5 — Next NNUE shape after `1024 x 8kb`): compares `1024 x 16kb` (`0.00%` AVX-512 / `-2.51%` AVX2 `bench 15` NPS, zero C++ change, `12.6M` params) vs `1536 x 8kb` vs `2048 x 8kb` vs `2L VNNI`, proves exact AVX2 `H=1056` `int32` overflow vs AVX-512 `H=2048` (`nnue_v3.cpp:125`), zero-confounded `768 -> 1024` NPS (`-4.32%` AVX-512 / `-8.84%` AVX2), and establishes fixed-clock paired matching as the deciding test.

## Next Focus Areas (after Astra reviews N20/N21 & Fable runs ~07:20Z/07:50Z check)
1. Cross-check Astra's incoming `070804Z` (matched-warm 384-opening label depth) and `071817Z` (Syzygy 4–5-piece tablebase label audit).
2. Deep dive into deeper/beyond-list Forge codebase audits & stronger-engine architecture opportunities (e.g., search efficiency & pruning/eval interactions in `source/src/search.cpp`, `board.cpp`, `eval.cpp`, and `loop/` tooling/data-pipeline invariants — only propose real, source-backed findings, never fluff).
