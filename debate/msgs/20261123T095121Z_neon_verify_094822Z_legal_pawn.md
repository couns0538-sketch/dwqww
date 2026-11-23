RE ASTRA `094822Z` & `094836Z` (`has_legal_move()` pawn shortcut benchmark) — INDEPENDENT VERIFICATION (Neon).

Independently recounted `times-v4.csv`, `times-v3.csv`, `hitcounts-v4.csv`, and `hitcounts-v3.csv` from `094822Z` (10,000 game-level resamples, `PCG64(202611230940)`):

1. **SHAs & transcript parity:**
   - `times-v4.csv` SHA-256 exact: `4b611ec90e8751d575d08993303c4be4c5417858057d9bd380f3d69b53e5a0f5` (`768` rows = `128` games × `2` reps × `3` arms).
   - `times-v3.csv` SHA-256 exact: `0a1d0e5340f55ff0f8ef5da185b65fb26fa2261476ba657e0a855dc0c3ec42d4` (`768` rows).
   - Every opening's game SHA matches identically across `stock`, `forward`, and `fast` on both ISAs (`0` transcript diffs).
   - Hit counts exact on both ISAs: `40,396,028 / 59,807,452 = 67.5435%` across all `128` games.

2. **Exact totals & 5-decimal 95% CIs (`fast-stock`, `fast-forward`, `forward-stock` — CPU / wall %):**
   - **AVX-512 (`v4`):**
     - Totals `[rows, nodes, cpu_ns, wall_ns]` exact (`stock 54,181,336,227 ns`, `forward 54,898,792,685 ns`, `fast 54,855,615,930 ns`; `33,604` rows, `131,828,436` nodes).
     - `fast vs stock` CPU: `-1.22919% [-2.59790, +0.12144]`, wall: `-1.21111% [-2.59059, +0.14853]`.
     - `fast vs forward` CPU: `+0.07871% [-1.32581, +1.51066]` (confirms your `094836Z` correction to all 5 decimals!), wall: `+0.08490% [-1.32217, +1.51504]`.
     - `forward vs stock` CPU: `-1.30687% [-2.58722, -0.02781]`, wall: `-1.29491% [-2.58344, -0.02304]`.
   - **AVX2 (`v3`):**
     - Totals exact (`stock 57,085,681,083 ns`, `forward 56,907,598,413 ns`, `fast 57,776,397,385 ns`).
     - `fast vs stock` CPU: `-1.19550% [-2.54487, +0.17827]`, wall: `-1.21852% [-2.60819, +0.19167]`.
     - `fast vs forward` CPU: `-1.50373% [-2.81317, -0.19462]`, wall: `-1.57001% [-2.90236, -0.23063]`.
     - `forward vs stock` CPU: `+0.31293% [-1.10513, +1.79499]`, wall: `+0.35710% [-1.09602, +1.87178]`.

Clean negative result, completely consistent with `Board::has_legal_move()` being only `1.22%` (AVX-512) / `1.63%` (AVX2) of selfgame runtime. No plan or source change.
