# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T03:52:43Z
- Phase: 2 debate

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md
- [x] debate/PLAN.md
- [x] debate/STATE.md
- [x] debate/READ_CHECK.md (answered in `debate/msgs/20261123T034552Z_neon_readcheck.md`; Fable scored 12/12)
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
- Built unmodified `source/src/*.cpp` on Linux (`g++ 13.3.0`, `/tmp/forge-bin/`) and verified bit-exact pins: defaults `312866 / 862329 / 4865609`; loop+r0067 `226187 / 616966` across AVX-512+PEXT (`260-268 ms`), AVX2+PEXT (`284-290 ms`, ~8% slower), and AVX2 no-PEXT (`363 ms`, ~27% slower). Stock `source/CMakeLists.txt` lacks `FORGE_NNUE_V3=1` & `FORGE_MATE_ALPHA_GUARD=1` (rejects 3 loop options, prints `278016`), and `FORGE_PORTABLE=ON` bundles PEXT=0 with ZMM=0 (`CMakeLists.txt:17,27-40`).
- `source/src/nnue_v3.cpp:125,134-151,156,678` & `nnue_v3.hpp:65,71`: AVX2 `hsum_epi32_pair_avx2` adds `sum0 + sum1` in `int32`; at `hidden=1024, max|w2|=127` (r67 hits 127, `build_clang.log:26`), worst-case is `2,114,092,800` vs `INT32_MAX` (1.55% headroom); `hidden=1056` overflows AVX2 `int32`. Widening before add fixes up to 2048/4096.
- `source/src/uci.cpp:457`: `run_selfgame` sets `ply = board.history_size() - 1` (0 on `position fen <opening>` without moves; reproduced on move-5 FEN -> 0 `sg` rows at `writeminply 8`). Confirmed by Fable (`20261123T104928Z`).
- `source/src/uci.cpp:1124-1134`: `go perft` hits v3 problem exit(2) before `first == "perft"`. Confirmed by Fable.
- `source/src/search.cpp:2243-2248,2304,2317-2328`: quiet checks fall into the capture branch and are SEE-pruned by `-SeeNoisyMultiplier * depth`. Confirmed by Fable.
- `source/src/search.cpp:2547-2588`: `CuckooRep` (`search_child`/`qsearch_child`) lacks `mate_moves_ == 0` guard (`search_child`), lacks `ply != 0` / `excluded.is_none()` (`qsearch_child`), ignores `DrawJitter`, and leaves dead `search_cuckoo`/`qsearch_cuckoo`.
- `source/src/search.cpp:1804,2000` vs `search.hpp:114-125`: TT cutoff blocks `halfmove_clock >= 90` even though `score_usable` allows exact-clock matches (so TT refines eval at >=90 but never cuts off).
- `debate/evidence/fable_filter_shares_round136.json`: 21.19% of kept rows have `|score| >= 600` (99.68% win, 0/44,893 loss), 50.00% have `<= 16` pieces; `uci.cpp:302` uses `evallimit = 2000`.
- Independently reproduced Astra's A1 fixture (`sg 0 24 e2e4 ...`, `drawadj`, `moves` empty) and recomputed all A2 and A3 numbers.

## My proposals and their status
- `N1` (`20261123T035243Z_neon_n1_p1_p10_2k_and_dead_params.md`): Reconcile P1/P10 (add 2k soft-node bar + dead/coupled parameter audit). Status: OPEN.
- `N2` (`20261123T035243Z_neon_n2_p3b_linux_build_and_avx2.md`): P3b Linux ThinLTO+PGO build flags (`FORGE_NNUE_V3=1`, `FORGE_MATE_ALPHA_GUARD=1`, decoupled PEXT/ZMM) + AVX2 fused kernel if server lacks AVX-512. Status: OPEN.
- `N3` (`20261123T035243Z_neon_n3_p4_p8_nnue_v3_int32_guard.md`): P4/P8 `int32` output-sum widening + load-time overflow check before `hidden > 1024`. Status: OPEN.
- `N4` (`20261123T035243Z_neon_n4_p3c_score_tail_and_measure.md`): P3c equal-N filter test for `|score| >= 600` tail / endgame skew + `MEASURE` cross-tab request to Fable. Status: OPEN.

## What I still owe (questions to me that have no answer yet)
- Replied to A1, A2, A3 (`RE A1`, `RE A2`, `RE A3`).
- Still to propose next: Q1/Q3 (standstill diagnostic + gate schedule once 2B training takes 4+ h), Q4/Q5 (search bundle candidates from `source/` + correctness list items for P7/P8).

## My next step
- Push RE A1-A3 and N1-N4, then watch shared + Astra branches for Fable's READY/responses and Astra's next proposals; draft N5 (Q1/Q3 gate & standstill) and N6 (Q4/Q5 P7/P8 source items).

## Last shared commit read
0b40df3d9a (shared), b54bf2b6fd (Astra).
