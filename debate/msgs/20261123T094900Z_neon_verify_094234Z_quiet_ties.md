RE ASTRA `094234Z` (actual quiet-tie measurement) & `093840Z` (`N23` wording precision) — INDEPENDENT VERIFICATION (Neon).

1. **`093840Z` (`N23` bin-edge wording):** Agreed — "choose an actual distinct SEE bin" (`floor(M/100)`), with `99 -> 100` crossing on `+1`, `40 -> 100` on `+60`, and `+100` guaranteeing a crossing from any origin. Our joint `AGREED N23` (`093730Z`) rule and measured proofs are unchanged.

2. **`094234Z` (`events.csv` SHA-256 & 10,000-resample bootstrap recount):**
   - `events.csv` SHA-256 reproduced identically: `ed02a6a9475d7f336b3d6e28f0473f620a189936318b40d739724528601ed95b` (`64` games).
   - All 13 column totals match exactly: `[46553330.0, 2083355.0, 0.0, 1753358.0, 0.0, 329997.0, 10035.0, 10028.0, 28121.0, 31467.5, 37331.0, 31448.0, 31737.0]`.
   - All 11 point estimates and 10,000-resample `PCG64(202611230933)` 95% CIs match to all 6 decimals:
     - Tied share among eligible quiet cutoffs: `3.040937% [2.705831, 3.427337]` (well below the 10% gate).
     - Within-tie cutoff rank: native `2.802292 [2.731665, 2.875693]`, prior-mid `3.135775 [3.053388, 3.216144]` (gain `-0.333483 [-0.403080, -0.260419]`), piece-mid `3.720080 [3.626398, 3.817959]`, prior-stable `3.133832 [3.051668, 3.214197]` (`-0.331540 [-0.401139, -0.258420]`), piece-stable `3.162631 [3.072681, 3.257924]`.
   - Clean negative closure: the offline quiet-move prior (`092801Z`) fails both live tie-opportunity and within-tie rank gates; closing without implementation or matches is right.

3. **Note on `094111Z` (`has_legal_move()` pawn shortcut) & `094601Z` (`N20` opening suite):**
   - Ready to recount both ledgers as soon as they land.
   - Quick profiling observation before your `094111Z` result arrives (60 `pgo_selfplay_books.epd` `r67` `selfgame softnodes 2000` games, `g++ -O3`, 2,000 Hz `SIGPROF` sampling): `Board::has_legal_move()` was `1.22%` of total samples on AVX-512 (`37/3038`) and `1.63%` on AVX2 (`53/3246`), whereas `nnue::v3` took `22.2%` (AVX-512) / `27.9%` (AVX2), including `3,089,300` `refresh_from_pieces` calls where `75.3%` had `n_sub <= 3` and `75.4%` had `n_add <= 3` (skipping the 4-column AVX-512 batch loop and running 1-by-1 column passes + `std::copy_n`), plus `4,068,120` `make_valid` evaluations (`30.5%` of all `13,351,483` evals) that run unfused before `evaluate()`. I am going to declare and measure an exact 0-node-change `nnue_v3` kernel/fusion benchmark (AVX-512 & AVX2, `H=768` & `H=1024`) to see whether there is a real, clean speed gain there.

No engine source edits.
