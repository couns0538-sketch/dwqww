# Forge Opus R5D: forced mate reported as a centipawn score with Threads >= 2 — IN PROGRESS

**Status:** reproduced; root-cause analysis done to the mechanism level; fix in progress. Push note: 09:56 -> 10:2x Vienna was more than 10 min (diagnosis runs). Last push: see the head commit time (pushes every 10 min).

Branch `opus-r5d-matefix` = `astra3-integration` at 5eabdb7 (the commit Code Review passed; the branch head has moved
on to e224595a since) + R5D commits. Job folder `opus_r5/r5d/`, scratch `F:\opus_scratch\r5\r5d\`. Machine exclusive:
no (live gates, NNUE training and self-play). Every build, test and run at BelowNormal (Git Bash `nice -n 10`), at
most 3 threads in total; Threads 4 searches run on a 3-CPU affinity mask (4 search threads share 3 CPUs). No Elo claims.

Time base: Vienna (CET) = the PC's "PST" clock - 1 h (GitHub Date header 08:19 GMT at 09:20 Vienna). Job start
09:52 Vienna (R5C paused at M3 for this job).

## 00_baseline

Build (job-spec flags; `tools/build_r5d.sh`, RECIPE=v3: MSYS2 ucrt64 g++ 15.2, -O3 -DNDEBUG -march=x86-64-v3
-mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256, static):
`forge_r5d_off_5eabdb7.exe` sha256 297674c8..., 0 warnings, FMA 0; lock `uci_check.py --full`: bench d11/13/16/20/22 =
312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690: **ALL OK**
(`logs/identity_off_5eabdb7.log`).

## 1. Reproduction

`tools/r5d_mate_repro.cpp` (links the engine core): N runs, each with a fresh Searcher (empty TT, like round 1 of
`tests/tt_mate_tb_tests.cpp`) on KRK `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` (mate in 3, key move Kd5-c5), `go depth D`; a run
fails when the score is not a mate no shorter than 3 (`--capture` prints the main thread's info lines of failing runs,
`--best-thread` = UCI SmpBestThread). Base 5eabdb7, Threads 2:

| setting | runs | failures |
|---|---|---|
| depth 14, SmpV2 off | 200 / 300 / 1000 | 9 (4.5 %) / 10 (3.3 %) / 37 (3.7 %) |
| depth 14, SmpV2 off, SmpBestThread on | 1000 | 52 (5.2 %) |
| depth 14, SmpV2 on | 1000 | 36 (3.6 %) |
| depth 20, SmpV2 off / on | 1000 / 1000 | 0 / 0 |
| depth 14, Threads 1 | 300 | 0 |

Failing runs report cp 440-490 with e8e4 at depth 14; the main thread's iterations 1-14 never show a mate (the single
thread finds mate 3 with d5c5 from depth 10).

## 2. Root cause

Instrumented scratch copies (never committed; `F:\opus_scratch\r5\r5d\diag_src`) logged every thread's TT stores at
the nodes of the mating tree (1.Kc5 Ka6 2.Re7 Ka5 3.Ra7# and 1.Kc5 Ka4 2.Re3 Ka5 3.Ra3#) that contradict the known mate
at a sufficient depth:
- The first wrong store is at "1.Kc5 Ka6, White to move" (mate in 2 with the quiet zugzwang move Re7): searches at
  depth 3-6 fail low with **no best move** and store an upper bound around +470..+508. Re7 is a quiet non-check, so at
  these depths it is dropped by late-move pruning (`skip_quiets` once `move_count >= FORGE_LMP_THRESHOLD`, which also
  drops later quiet checks), history pruning or SEE pruning when the move ordering puts it late.
- One ply up ("1.Kc5", Black to move) the parent then stores a lower bound around -470 (Black "not mated") at its
  nominal depth (up to 8), written by both threads.
- The single thread stores such wrong bounds too (300 of 300 runs), but at iteration 10 its reduced root search of d5c5
  fails high, triggers the full-depth re-search (Kc5 searched at depth 9, "Kc5 Ka6" at depth 8) and finds the mate.
  In the failing two-thread runs the main thread's reduced search of d5c5 at iteration 10 is cut by the wrong
  depth-5/6 bounds that both threads wrote at iteration 9, d5c5 never fails high again and is never re-searched.
- Ruled out: torn TT entries (the default TT is stripe-locked), mate-distance TT encoding (`scores.inc` is ply-correct),
  aborted iterations (main search and qsearch return before any store after an abort), repetition draws (a variant
  that only counts threefold repetitions fails more often: 78 of 600).
- SmpV2 selector defect (real, SmpV2 only): `fb2::smp_select_result` only lets a helper replace the current best when
  its capped depth is strictly greater, so a helper that proved the mate at the same or a lower depth is ignored,
  while a deeper helper with a cp score replaces a cp main result.

Code reading notes:
- Default mode (no SmpV2, no SmpBestThread) returns the main thread's result unchanged
  (`src/search/searcher.inc`); a `go depth` main thread is aborted only by the shared stop flag (set after it
  returns), a node limit or a hard time limit (`src/search/checks.inc`). So with plain Threads 2 the main thread's
  own completed iterations end on a cp score: helper entries in the shared TT must be steering it.
- The default TT is coherent (striped locks, `include/forge/tt.hpp`); only LocklessTT uses key-checked entries.
- Mate scores are stored as the distance from the storing node and read back relative to the reading node
  (`src/search/scores.inc`): no ply error visible.
- Aborted iterations (`src/search/iterative.inc` 203-219) keep the last completed score but may take the partial
  iteration's move; SmpV2 helpers keep their completed tuple.

## 3. Fix (pending)

## 4. Proof (pending)

## 5. CI test (pending)
