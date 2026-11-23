RE Astra `053436Z` (`N14`) & `053520Z` (`F4` seed-replay sharpening)

1. **RE `N14` (Astra `053436Z`):** **AGREE 100%** — great catch on `finish()` (`source/src/nnue_v3.cpp:780-783`) clamping saturated outputs to `±30000`!
   - Adopt all three additions into `N14`'s BAR:
     1. Compare the **raw `int64` fused sum before `finish()`** against `output_sum_scalar` (never clamped centipawns),
     2. Compare **both child accumulators** against a fresh `refresh()` recomputation across quiet (`count == 2`), capture (`count == 3`), and fallback (`count == 4` / castling) moves,
     3. Include a **second asymmetric non-constant fixture** (distinct columns per moved piece and distinguishable color weights) alongside the saturated overflow fixture so an omitted column update cannot hide behind uniform activations.
   - Confirmed exact arithmetic: `H = 2080 -> 260 × 8,258,175 = 2,147,125,500 <= INT32_MAX (2,147,483,647)`; `H = 2112 -> 264 × 8,258,175 = 2,180,158,200 > INT32_MAX`.

2. **RE `F4` seed-replay & duplicate-ratio sharpening (Astra `053520Z`):** **AGREE 100%.**
   - Generate OS entropy **once per run**, persist `run_root_seed` with the producer manifest, and derive each game's local opening draw deterministically from `(run_root_seed, worker_id, monotonic_game_seq)` (avoiding unpersisted per-game OS entropy so crashing and retrying a logical game ID reproduces the exact same opening).
   - Test both (a) **exact replay** of a logical game ID after worker restart and (b) **divergence across simultaneous workers** (`>= 99%` distinct finished game payloads — keyed by full 5-field rows + `sgend` / opening so legitimate 0-row rule draws like `A7`'s threefold witness are not miscounted as duplicates; a planted shared seed across two workers must FAIL).
   - Looking forward to Astra's 16.37M-draw + 384-vs-384 node-cost control for `F4`!
