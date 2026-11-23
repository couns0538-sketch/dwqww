MEASURE — Exact zero-node-change `nnue::v3` tiled Finny-refresh + fused final-ply `make_valid` + fused AVX2 kernel diagnostic (Neon, scratch builds under `/tmp/` only; zero repo `source/` edits).

**Motivation from real `selfgame` profiling (`094900Z`):**
Across 60 `pgo_selfplay_books.epd` `r67` `selfgame softnodes 2000` games (`29,806,386` nodes; `13,351,483` `static_evaluate_v3` calls), 2,000 Hz `SIGPROF` sampling puts `nnue::v3` at `22.2%` (AVX-512) / `27.9%` (AVX2) of total runtime, with three exact micro-bottlenecks in unmodified `source/`:
1. `refresh_from_pieces` (`nnue_v3.cpp:920-978`, `3,089,300` calls = `23.1%` of evals; `4.77%` AVX-512 / `4.90%` AVX2 of total time): `75.3%` have `n_sub <= 3` and `75.4%` have `n_add <= 3` (mean `5.16` total columns), skipping the 4-column AVX-512 batch loop and running 1-by-1 accumulator load/store passes plus a separate `std::copy_n` pass.
2. `make_valid` (`nnue_v3.hpp:283-293`, `search.cpp:3396-3410`, `4,068,120` calls = `30.5%` of evals: `1,819,695` 1-ply king-bucket changes + `2,248,425` multi-ply gaps `>= 2`): writes `stack[index]` unfused, then `evaluate()` reloads all `2 * H * 2` bytes for `output_sum`.
3. `apply_pair_and_evaluate` on AVX2 (`nnue_v3.cpp:903-917`, `9,216,723` `fast_pair` calls = `69.0%` of evals): runs unfused `apply_changes_pair` + `output_sum_avx2` (`16.69%` of total AVX2 runtime) and computes `collect_changes` twice; on AVX-512 (`461-510`), `apply_pair_and_sum_avx512` is 1x unrolled (`sum0..sum1`) vs 2x in `output_sum_avx512` (`sum0..sum3`) and falls back to unfused for `dirty.count == 0` (`111,785` null-move evals).

**Frozen candidate implementation (100% bit-exact arithmetic, zero search/eval/node change):**
- `cand_refresh_only` (Piece 1 alone): single-pass register-tiled `refresh_from_pieces` over 128-`int16` tiles (4 ZMM on AVX-512 / 8 YMM on AVX2, plus 32-`int16` tail for `H % 128 != 0`), loading `entry.values` once, applying `subs[0..n_sub-1]` then `adds[0..n_add-1]` in exact original order, writing `entry.values` once (skipped if `n_sub == 0 && n_add == 0`) and `destination` once.
- `cand_full` (Pieces 1 + 2 + 3):
  - Piece 1 (tiled `refresh_from_pieces`).
  - Piece 2: fused final-ply `make_valid_and_evaluate` — intermediate plies `ancestor + 1 .. index - 1` replay normally, then the final ply `k == index` fuses with the exact `int64` SCReLU sum (`apply_pair_and_evaluate` when both kings keep their key; fused single-perspective `refresh_from_pieces_and_sum` + `apply_changes_and_sum` when one or both perspectives refresh), plus fused `dirty.count == 0` (null move) copy+sum.
  - Piece 3: fused AVX2 `apply_pair_and_sum_avx2` (`count == 2` quiet, `count == 3` capture, `count == 0` null; removes double `collect_changes`) and 2x unrolled (`h += 64`, `sum0..sum3`) `apply_pair_and_sum_avx512`.

**Frozen parity & verification gates (ALL must pass with 0 diffs):**
1. All 5 engine pins exact on every build (`default bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609`, `r67 bench 11 = 226187`, `bench 13 = 616966`).
2. `FORGE_NNUE_V3_VERIFY=1` builds of `cand_full` on BOTH AVX-512 and AVX2 exit `0` across castling/EP/promotion `selfgame`s and depth-10 searches on `r67` (`H=768, 8 KB`), max-boundary `H=1024, 16 KB` mirrored (`max|b1|+32*max|w1|=32767, |w2|=127`), and max-boundary `H=1024, 32 KB` non-mirrored, with AVX-512 vs AVX2 bit-identical transcripts.
3. Exact per-game SHA-256 parity of full `sg` + `sgend` transcripts across all 3 arms and both ISAs on every timed game.

**Frozen timing protocol & advance bar:**
- Arms: `[stock, cand_refresh_only, cand_full]`, built with identical `g++ -std=c++20 -O3 -DNDEBUG` production flags on BOTH AVX-512/PEXT (`-march=native -DFORGE_SPD_NNUE_ZMM=1`) and AVX2/PEXT (`-mavx2 -mbmi2 -mpopcnt -mno-avx512f -DFORGE_SPD_NNUE_ZMM=0`).
- Primary panel: all 60 openings of `loop/build_recipe/pgo_selfplay_books.epd`, real `selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 40 drawscore 12 drawcount 6` on `r67` + 24 `LOOP_OPTIONS.txt`, **2 repetitions** with cyclic permutation of the 3 arms across game IDs (reversed in rep 2), measuring child process CPU time (`ru_utime + ru_stime`) and wall time per game.
- Secondary scaling check (`N21`/`W13(b)`): same paired timing (`stock` vs `cand_full`, 2 reps, rotated order) on 30 openings with a realistic 16-bucket `H=1024` net (`N21` all-16-reachable map, each bucket splitting one `r67` parent bucket).
- Bootstrap: resample game IDs 10,000 times with `PCG64(202611230952)`, reporting CPU rows/s % gain and wall rows/s % gain with 95% CIs.
- **Advance bar (strict):**
  - 100% parity on all pins, `FORGE_NNUE_V3_VERIFY=1`, and every game transcript.
  - **AVX-512 `r67`:** `cand_full` vs `stock` CPU rows/s `>= +2.0%` with lower 95% bound `> 0%` and no conflicting wall regression (and if passed, must also survive a `g++` PGO build check on held-out games).
  - **AVX2 `r67`:** `cand_full` vs `stock` CPU rows/s `>= +3.0%` with lower 95% bound `> 0%` and no conflicting wall regression (quantifies the `W5(a)` AVX2 fallback value).
  - Host numbers never claim a target-PC (`znver5` Clang PGO+ThinLTO) gain and never delay `W5` if the plain build meets `W5(g)`'s pilot rate.
