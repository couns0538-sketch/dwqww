# Forge Opus R5D: forced mate reported as a centipawn score with Threads >= 2 — IN PROGRESS

**Status:** reproduced; root cause found (pruning of the quiet mating move against a bare king; also reachable with
one thread on a warm TT); fix BKM being verified. Push notes: 09:56 -> 10:11 Vienna was 15 min (diagnosis runs),
10:23 -> 10:4x was over 10 min (Threads 1 finding + BK runs). Last push: see the head commit time.

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

## Experiments (scratch exports of 5eabdb7 with one change each; KRK depth 14, Threads 2, 1000 runs, SmpV2 off / on)

| variant | change (helpers = workers 1..n-1; Threads 1 unaffected by construction) | failures off / on |
|---|---|---|
| base | none | 37 (3.7 %) / 36 (3.6 %) |
| dupfix | `TT::store` updates an existing slot of the same key instead of the probe-time slot (no duplicate keys) | 42 / 48 |
| F2 | helpers do not store fail-low upper bounds without a best move (main search) | 47 / 53 |
| C2 | helpers store no upper bounds (main search and qsearch) | 76 / 59 |
| C6 | multi-worker same-position replacement only by equal-or-deeper results | 102 / 99 |
| F3 | helpers store nothing in the main search (qsearch / ProbCut stores stay) | 102 / 97 |
| F7 | helpers store nothing in qsearch (main search / ProbCut stores stay) | 58 / - |
| **F6** | **helpers write nothing to the TT** | **0 / -** |
| (Threads 1, any hash 1-64 MB, warm TT after depth 3..11) | - | 0 |

At the mate-in-2 node "1.Kc5 Ka6" (scratch `diag5`): in the bad searches Re7 is either cut by late-move pruning
(`LMP-skip@2..20`) or searched as a late quiet move with an LMR reduction whose result (~466, the quiet Ra7# lies beyond
qsearch) stays below alpha, so it is never re-searched. The single thread finds the mate at iteration 10 only because
d5c5 fails high at the root there (Ra8+ gives 499 in its null-window search) and the wider-window re-search of
"1.Kc5 Ka6" (window 481..506, depth 8) finds Re7 = mate. In the failing two-thread runs the main thread never gets that
fail-high: the helper's TT writes (any kind: main search, qsearch, ProbCut) change the bounds it meets, and the
pruning-dependent bounds keep d5c5 reduced and below alpha until depth 14. Only read-only helpers (F6) remove it.

### The same miss with one thread: the root cause is the pruning, the helpers only expose it

`r5d_mate_repro --prefill-fen <FEN> --prefill-depth 9`: one unrelated depth-9 search in the same Searcher first (its
TT entries and histories stay), then KRK at depth 14 with **Threads 1**. Over 40 opening positions
(`F:\opus_scratch\r5\r5d\tmp\prefill40.fen`, positions from `tests/data/nnue_selfplay_sample_916.txt`) the single
thread misses the mate in **6 of 40** cases (deterministic: the same 6 every time; cp ~470, e8e4). So the wrong bounds
are not an SMP artefact: any TT/history state that changes the move order at "1.Kc5 Ka6" lets the pruning drop Re7, and
the one-thread search only escapes when its root fail-high at iteration 10 happens. A second thread is simply the most
common source of such a state (3.7 % of fresh KRK runs).

Candidate **BK** (scratch `exp_bk`, `tmp/make_bk.py`): at a node whose side not to move has only its king, skip the
shallow quiet-move pruning block (move-count / futility / history / SEE) and the late-move reduction:

| BK, KRK depth 14 | result |
|---|---|
| Threads 2, 1000 fresh runs, SmpV2 off / on | **0 / 0** failures |
| Threads 1, prefill40 | **0 / 40** |
| bench d11 / 13 / 16 / 20 / 22 | 312866 (=) / 862954 / 2712632 / 11255559 / 36796258 (pins: 862329 / 3024920 / 12389307 / 34048354) |
| perft | unchanged |

BK changes the one-thread tree (bench pins), which the job forbids for a fix without an option. See section 3.

## 3. Fix

Job rule: smallest fix, behind no option, OFF and Threads=1 bit-identical. BK cannot meet "Threads=1 bit-identical"
(it is a Threads=1 change too). The fix is **BKM** = BK applied only while more than one worker searches
(`SharedSearchState::multi_worker`, set by `Searcher::search` before any worker starts; bench and every Threads 1
search keep the AL1 tree). 12 added / 2 changed lines in three files (`git diff 5eabdb7 -- src include`):

```diff
 include/forge/thread_data.hpp (SharedSearchState)
+    bool multi_worker = false;   // set by Searcher::search before any worker starts, read-only while they run
 src/search/searcher.inc (Searcher::search, after shared_.tt.new_search())
+    shared_.multi_worker = workers_.size() > 1;
 src/search/alphabeta.inc (main search, before the move loop)
+    const bool mating_mode = shared_.multi_worker && popcount(board.occupied(opposite(board.side_to_move()))) == 1;
-        if (!root_node && best_score > -MateInMaxPly && has_material) {
+        if (!root_node && best_score > -MateInMaxPly && has_material && !mating_mode) {     // shallow pruning block
-        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && (quiet || !ss->tt_pv || move_count > 4)) {
+        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && !mating_mode && (quiet || !ss->tt_pv || move_count > 4)) {  // LMR
```

- What it changes: only nodes of a multi-worker search where the side to move faces a bare king (KXK endings,
  including K+pawns v K). There the side to move has no capture, so the two blocks only ever skipped or reduced quiet
  moves; node-level pruning (null move, reverse futility, ProbCut) and qsearch are unchanged.
- Thread safety: `multi_worker` is a plain bool written by the searching thread before `std::thread` starts the
  helpers and after the previous search joined them (both happens-before edges); workers only read it.
- Not changed (not this job, or not the cause): the SmpV2 selector defect above (SmpV2 mate selection is Astra's item;
  with BKM, SmpV2 on also reaches 0 misses), the TT duplicate-slot store (dupfix: latent, no effect here).
- Left to the owner: the one-thread warm-TT miss (6 of 40 prefill positions; bench-identical by the job rule). BK
  (the same change without the `multi_worker` gate) removes it but changes the bench pins (section 1 BK table): it
  needs new pins and a gate, so it is not part of this branch.

Fix tree checks (PC, BelowNormal, <= 3 threads):

| check | result | evidence |
|---|---|---|
| box build (RECIPE=v3) `forge_r5d_bkm.exe` | sha256 959c9785..., 0 warnings, FMA 0 | `logs/build_bkm.log` |
| lock identity `uci_check.py --full` | bench 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690: **ALL OK** | `logs/identity_bkm.log` |
| CMake (Release, all targets) | builds; 62 warning lines, all `-Wconversion` / `-Wclass-memaccess` in unchanged lines (TT store calls in `alphabeta.inc` / `qsearch.inc`, `tt_lockless.inc`) | `logs/cmake_bkm_warnings.txt` |
| full CTest on a 3-CPU mask (forge_tests apart) | **63 / 63 passed** | `logs/ctest_bkm.log` |
| forge_tests | only the 4 known FAIL lines: KNOWN-FAILURE CHECK PASS | `logs/ctest_forge_tests_bkm.log`, `logs/chain_tools.out` |

## 4. Proof (pending)

## 5. CI test

`tests/r5d_matefix_tests.cpp` -> CTest `forge_r5d_matefix_tests` (argument: runs per configuration, CTest 50,
timeout 600 s). KRK depth 14 with a fresh Searcher per run: Threads 2 and 3, SmpV2 off and on (4 x 50 runs), and
Threads 2 on a TT left by an unrelated depth-9 search (the 6 prefill openings after which the one-thread search
misses, 5 repeats = 30 runs). Every score must be a real mate no shorter than mate in 3.
- Planted bug = the base tree 5eabdb7 (no fix), same test source: **FAIL** (exit 1): Threads 2 47/50, Threads 2 SmpV2
  47/50, Threads 3 48/50, Threads 3 SmpV2 50/50, warm 27/30 (`logs/matefix_tests_base.log`).
- BKM tree: **PASS**, 230/230 runs, and every fresh run exactly mate in 3 (200/200) (`logs/matefix_tests_bkm.log`).
- `tests/tt_mate_tb_tests.cpp`: its Threads block reads `FORGE_TT_MATE_THREADS` (default 2) and `FORGE_TT_MATE_SMPV2`
  (default off) for the proof loops; default output and checks unchanged.
