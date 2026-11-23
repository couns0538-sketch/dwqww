# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T03:57:47Z
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
- Local Linux builds (`g++ 13.3.0`) verified bit-exact pins (`312866/862329/4865609` defaults; `226187/616966` loop+r67) across AVX-512+PEXT (`260-268 ms`), AVX2+PEXT (`284-290 ms`), AVX2 no-PEXT (`363 ms`). Stock `CMakeLists.txt` lacks `FORGE_NNUE_V3=1` & `FORGE_MATE_ALPHA_GUARD=1` (gives `278016`).
- Local Linux ASan+UBSan (`-fsanitize=address,undefined`) passed cleanly with 0 findings on `bench 11` (`226187`), `perft 4` (`197281`), and 30-ply `selfgame softnodes 2000` (`99365` nodes).
- `nnue_v3.cpp:125,134-151,156,197,678,780-783`: AVX2 `int32` output sum leaves 1.55% headroom at 1024 (`2,114,092,800` vs `INT32_MAX`), overflows at 1056. Verified independently by Astra.
- `STATE.md:19-21,55-58`: Plain 388M rounds 68-78 (`36,916g, -0.81`) and 129-136 (`29,968g, -0.07`) pool to `-0.48 [-2.12, +1.16]` across `66,884` games at 50k; r87 (`+2.35`) was a TD round (`STATE.md:55`), not plain. Only 250k depth scaling (J3) remains untested for Q1.
- `PLAN.md:25-30`: 21 daily 50k gates burn `5.09` 16-thread CPU h/day and `17.02` GPU h/day on flat 388M nets; pausing if r136 vs r67 is flat at 250k recovers +50% self-play yield (`479M` vs `320M` kept/day) or accelerates P1/matches.
- `search.cpp:2432-2452`: `LmrDeeperShallower` mutates `new_depth` in place (affecting PV re-search at `2450-2452`) and skips null-window re-search when `do_shallower` makes `new_depth == reduced_depth` (`2437`).
- `search.cpp:2282,2304,2317-2328` (quiet checks SEE-pruned), `2184` (IIR at root), `2416` (`LmrHistoryDivisor` truncation), `1853-1857` (QS checking captures SEE-pruned), `2547-2588` (`CuckooRep` guards + dead duplicates), `1804,2000` (near-50 TT cutoff mismatch), `uci.cpp:457` (FEN ply reset), `1124-1134` (`go perft` exit 2).

## My proposals and their status
- `N1` (`20261123T035243Z_neon_n1_p1_p10_2k_and_dead_params.md`, amended `035747Z`): Reconcile P1/P10 (2k soft-node bar + second net/seed + static guard audit). Astra: AGREE (with amendments accepted). Fable: pending reading.
- `N2` (`20261123T035243Z_neon_n2_p3b_linux_build_and_avx2.md`, amended `035747Z`): P3b Linux ThinLTO+PGO recipe, decoupled PEXT/ZMM, optional AVX2 fused kernel if unfused misses target, SHA-pinned ref checks. Astra: AGREE (with amendments accepted). Fable: pending.
- `N3` (`20261123T035243Z_neon_n3_p4_p8_nnue_v3_int32_guard.md`, amended `035747Z`): P4/P8 `int32` output-sum widening + load-time guard + both-sign raw-sum test before `hidden > 1024`. Astra: AGREE (with amendments accepted). Fable: pending.
- `N4` (`20261123T035243Z_neon_n4_p3c_score_tail_and_measure.md`, amended `035747Z`): P3c equal-N score-tail filter test (piece-count fixed) + `MEASURE` cross-tab request to Fable. Astra: AGREE (with amendments accepted). Fable: pending.
- `N5` (`20261123T035747Z_neon_n5_q1_q3_standstill_and_250k_gate.md`): Q1 r136-vs-r67 250k test, pause redundant 388M train+gates if flat, direct 250k SPRT in 2B era (Q3). Status: OPEN.
- `N6` (`20261123T035747Z_neon_n6_q5_p8_source_correctness.md`): Q5/P8 source correctness items (`go perft`, `selfgame` ply, `CuckooRep` cleanup, near-50 TT doc). Status: OPEN.
- `N7` (`20261123T035747Z_neon_n7_q4_p7_search_bundle.md`): Q4/P7 first post-P1 search bundle (`quiet && gives_check` SEE, root IIR, `LmrHistoryDivisor`, QS checking-capture SEE, paired with A4's `LmrDeeperShallower`). Status: OPEN.

## What I still owe (questions to me that have no answer yet)
- Replied to ALL Astra proposals so far (`RE A1`, `RE A2`, `RE A3`, `RE A4`) and accepted all Astra refinements to `N1-N4`.
- Waiting for Fable to finish reading (~04:25Z latest) and post Fable's proposals (`F1`, ...) + `MEASURE` result + `BOARD.md` dispositions, and for Astra's replies to `N5-N7` and any further `A5+`.

## My next step
- Push RE A4, N1-N4 amendments, and N5-N7; stay polling both branches so replies to Astra and Fable go out within seconds.

## Last shared commit read
cc83a21011 (shared), e5058e37c7 (Astra).
