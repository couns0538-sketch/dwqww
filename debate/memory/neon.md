# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T03:45:52Z
- Phase: READY

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md
- [x] debate/PLAN.md
- [x] debate/STATE.md
- [x] debate/READ_CHECK.md (answered in `debate/msgs/20261123T034552Z_neon_readcheck.md`)
- [x] loop/LOOP_OPTIONS.txt
- [x] source/R65_NOTE.txt
- [x] source/src/search.cpp (3,426 lines)
- [x] source/src/board.cpp (1,811 lines)
- [x] source/src/uci.cpp (1,314 lines)
- [x] source/src/nnue_v3.cpp (993 lines)
- [x] source/src/eval.cpp (659 lines)
- [x] source/src/nnue.cpp (557 lines)
- [x] source/src/bitboard.cpp (207 lines)
- [x] source/src/book.cpp (193 lines)
- [x] source/src/eval_params.cpp (89 lines)
- [x] source/src/forge65.cpp (61 lines)
- [x] source/include/forge/search.hpp (667 lines)
- [x] source/include/forge/board.hpp (353 lines)
- [x] source/include/forge/nnue_v3.hpp (299 lines)
- [x] source/include/forge/bitboard.hpp (224 lines)
- [x] source/include/forge/b4.hpp (109 lines)
- [x] source/include/forge/nnue.hpp (105 lines)
- [x] source/include/forge/eval_params.hpp (103 lines)
- [x] source/include/forge/eval.hpp (90 lines)
- [x] source/include/forge/tm_node_share.hpp (69 lines)
- [x] source/include/forge/book.hpp (58 lines)
- [x] source/include/forge/clock_plan.hpp (52 lines)
- [x] source/include/forge/uci_clock.hpp (43 lines)
- [x] source/include/forge/tm_finish.hpp (39 lines)
- [x] source/include/forge/forge65.hpp (22 lines)
- [x] source/include/forge/uci_output.hpp (12 lines)
- [x] source/include/forge/uci.hpp (11 lines)

## What I found (each with file and line, or with the figures I recomputed)
- Also read build/note files: `README.txt`, `source/CMakeLists.txt`, `source/R15D_NOTE.txt`, `source/R15DSG_NOTE.txt`, `Forge65_build/build_clang.log`, `Forge65_build/build_forge65_clang_pgo.sh`, `loop/build_recipe/build_forge_clang_pgo.sh`, `loop/build_recipe/pgo_selfgame.py`.
- `source/src/uci.cpp:457`: in `run_selfgame`, `ply` starts at `board.history_size() - 1` (0 after `position fen <opening>` without `moves`), ignoring the FEN fullmove counter; affects `draw_ply` (80) and `max_ply` (300) when games start from opening FENs (e.g. `pgo_selfgame.py:62` and self-play).
- `source/src/nnue_v3.cpp:125,134-151,678` & `source/include/forge/nnue_v3.hpp:65`: AVX2 `output_sum_avx2` accumulates `sum0 + sum1` in `int32`; at `hidden = 1024` and `max|w2| = 127` (r67 already hits 127 per `Forge65_build/build_clang.log:26`), worst-case lane sum is `2 * 64 * 2 * 255^2 * 127 = 2,114,092,800` vs `INT32_MAX = 2,147,483,647` (1.5% headroom); wider nets (`hidden > 1024`) overflow AVX2 `int32` and hit `MaxHidden = 1024`.
- `source/src/nnue_v3.cpp:895-918,946-976`: fused `apply_pair_and_evaluate` and 4-column unrolled `refresh_from_pieces` exist only under `#if FORGE_NNUE_V3_AVX512`, not AVX2; critical for P3b if the rented 64-core server lacks AVX-512. Also `source/CMakeLists.txt` lacks `-DFORGE_NNUE_V3=1`, `-DFORGE_MATE_ALPHA_GUARD=1`, and speed flags (`loop/build_recipe/build_forge_clang_pgo.sh:43-47` is Windows/MinGW-only).
- `source/src/search.cpp:2548-2568`: with `CuckooRep=true`, `search_child`/`qsearch_child` return literal `DrawScore = 0` (ignoring `DrawJitter`), `qsearch_child` calls `upcoming_repetition` without checking `ss->ply != 0` or `excluded_move.is_none()`, and `search_cuckoo`/`qsearch_cuckoo` (`2570-2588`) are dead duplicate wrappers.
- `source/src/search.cpp:1998-2011, 1804` vs `source/include/forge/search.hpp:114-125`: TT cutoff guards `board.halfmove_clock() < 90` even though `tte.score_usable(halfmove_clock)` already checks exact clock match at `>= 90`; so at `halfmove >= 90` TT refines `eval` (`2024`) but never cuts off.
- `source/src/search.cpp:2272-2330`: under loop options (`SoundMatePruning=false`), `pv_node` and `in_check` are not excluded from the pruning block (`2243-2248`); `quiet && gives_check` falls into `else if (prunable)` (`2304`) where `SeeNoisyMultiplier * depth` (`2320`) SEE-prunes quiet checks; in `qsearch` (`1857`), checking captures with `SEE < -40` are pruned.
- `source/src/search.cpp:2101-2102` & `loop/LOOP_OPTIONS.txt:10`: with `NullMoveBase = 5`, at depth 9 and `eval - beta = 450`, `R = 10` -> `depth - R = -1` (drops straight to `qsearch`).
- `source/src/search.cpp:2041,2307,2988`: dead/coupled parameter zones in P1 tuning (`EvalSwingMult==0`, `CaptureFutilityBase==0`, `AspFailHighReduce==0`, integer division in `LmrHistoryDivisor=5643`).
- `debate/PLAN.md:107-109` vs `301-303`: P10 (Opus) omits the 2,000 soft-node self-play check that P1 requires despite J3/J6 showing large 2k-node regressions/gains.
- `source/src/uci.cpp:1126-1129`: `go perft` triggers `v3::problem()` fatal exit before checking `first == "perft"`.

## My proposals and their status
- None yet (waiting for Phase 2 DEBATE to open).

## What I still owe (questions to me that have no answer yet)
- None yet.

## My next step
- Push readcheck + READY, read Fable's `debate/evidence/fable_filter_shares_round136.*` and Astra's messages/memory, and prepare Phase 2 proposals once debate starts.
