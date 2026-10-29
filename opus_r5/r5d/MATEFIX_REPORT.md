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
thread finds mate 3 with d5c5 from depth 10). The loop script of the job (KRK and the test, Threads 2 and 4, SmpV2 off
and on) is `tools/r5d_proof.py`; its base-tree rates (the "before" numbers) are in section 4, next to the fix.

## 2. Root cause

Suspects in the job's order (each: code reading plus, where a change can isolate it, a one-change experiment on the
base tree, KRK depth 14, Threads 2, 1000 fresh runs, SmpV2 off / on; base 37 / 36):

| # | suspect | verdict | evidence |
|---|---|---|---|
| 1 | mate-score ply adjustment on TT store / probe, races, torn entries | not the cause | `scores.inc` stores the distance from the storing node and reads it relative to the reading node; the default TT is stripe-locked (no torn entries; LocklessTT is off); dupfix (one slot per key) 42 / 48; and the miss happens with **one thread** on a warm TT (6 of 40), where nothing races |
| 2 | best-thread selection preferring a deeper cp over a shallower mate | not the cause; one real SmpV2 defect | the default mode returns the main thread's own result (no selection); SmpBestThread ranks every mate above every cp (`better_thread_result`) and misses as often as plain Threads 2 (39 / 1000 vs 72 / 2000); SmpV2 (`fb2::smp_select_result`) protects a proven main score, but ignores a helper's mate unless the helper is strictly deeper (Astra's SmpV2 mate item, not changed here) |
| 3 | helper depth+1 or aborted iterations publishing partial scores | not the cause | depth+1 helpers exist only with SmpV2, and SmpV2 off misses as often; an aborted iteration returns before any TT store (main search, qsearch) and the result keeps the last completed iteration's score |
| 4 | aspiration fail-high / fail-low leaving a cp bound | not the cause | NOASP (full window at every iteration): 35 / 34 |
| 5 | SmpV2 merge and vote logic | not the cause | SmpV2 off and on miss at the same rate (proof: 72 / 2000 and 63 / 2000 at Threads 2); with the fix both are 0; the selector defect is under 2 |
| 6 | TB or mate-distance pruning across threads | not the cause | no tablebases are loaded in any run (`syzygy::max_pieces() == 0`); NOMDP (no mate-distance pruning): 46 / 41 |
| - | **forward pruning of the only mating quiet move** | **cause** | traced below: at "1.Kc5 Ka6" (mate in 2 by the quiet zugzwang Re7) late-move / history / SEE pruning drops Re7 or LMR reduces it below alpha; the pruning-dependent upper bounds (~+470) reach the root through the TT. Removing that pruning at bare-king nodes (BK) gives 0 misses with one thread on a warm TT and with two threads |

Mechanism (instrumented scratch copies, never committed: `F:\opus_scratch\r5\r5d\diag_src`) logged every thread's TT stores at
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

| variant | change (F* / C* touch helpers = workers 1..n-1 only; dupfix, NOASP, NOMDP, threefold-only and BK change every search, dupfix only matters with several writers) | failures off / on |
|---|---|---|
| base | none | 37 (3.7 %) / 36 (3.6 %) |
| dupfix | `TT::store` updates an existing slot of the same key instead of the probe-time slot (no duplicate keys) | 42 / 48 |
| F2 | helpers do not store fail-low upper bounds without a best move (main search) | 47 / 53 |
| C2 | helpers store no upper bounds (main search and qsearch) | 76 / 59 |
| C6 | multi-worker same-position replacement only by equal-or-deeper results | 102 / 99 |
| F3 | helpers store nothing in the main search (qsearch / ProbCut stores stay) | 102 / 97 |
| F7 | helpers store nothing in qsearch (main search / ProbCut stores stay) | 58 / - |
| **F6** | **helpers write nothing to the TT** | **0 / -** |
| NOASP | no aspiration window: full window at every iteration (suspect 4) | 35 / 34 |
| NOMDP | no mate-distance pruning in the main search (suspect 6) | 46 / 41 |
| threefold-only | repetition draws in the search only at threefold | 78 of 600 (off) |
| **BK** | **no quiet-move pruning and no LMR at nodes facing a bare king, every search** | **0 / 0** (bench changes) |
| **BKM = the fix** | **BK in multi-worker searches only** | **0 / 0** (bench unchanged; section 4: 0 in 40,000) |
| (Threads 1, any hash 1-64 MB, the same root searched first at depth 3..11) | - | 0 |
| (Threads 1 after an unrelated depth-9 search, 40 openings) | - | 6 of 40 (next subsection) |

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
(`diag/prefill40.fen`, positions from `tests/data/nnue_selfplay_sample_916.txt`) the single
thread misses the mate in **6 of 40** cases (deterministic: the same 6 every time; cp ~470, e8e4). So the wrong bounds
are not an SMP artefact: any TT/history state that changes the move order at "1.Kc5 Ka6" lets the pruning drop Re7, and
the one-thread search only escapes when its root fail-high at iteration 10 happens. A second thread is simply the most
common source of such a state (3.7 % of fresh KRK runs).

Candidate **BK** (scratch `exp_bk`, made by `diag/make_bk.py`): at a node whose side not to move has only its king, skip the
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
search keep the AL1 tree). 10 added and 2 changed lines in three files (git: 12 insertions, 2 deletions;
`git diff 5eabdb7 -- src include`, comments shortened below):

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
  moves (and promotions, in K+pawns v K); node-level pruning (null move, reverse futility, ProbCut) and qsearch are
  unchanged.
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
| rebuild from the committed tree (LF `git archive HEAD src include`, 11:01 Vienna) `forge_r5d_final.exe` | sha256 747a2f77..., FMA 0, identity **ALL OK**; differs from `forge_r5d_bkm.exe` in 4 bytes (offsets 137, 138, 217, 218: PE timestamp and checksum) | `logs/build_final.log`, `logs/identity_final.log` |

## 4. Proof

`tools/r5d_proof.py` on a 3-CPU affinity mask (`tools/run_pinned.py --mask 0x700`; Threads 4 = 4 search threads on
3 CPUs), 10:44-10:57 Vienna, BelowNormal. Fix = the BKM tree (`F:\opus_scratch\r5\r5d\test\repro_fix2.exe`,
`cmake_bkm\forge_tt_mate_tb_tests.exe`), base = 5eabdb7 with the same harness sources (`repro_base2.exe`,
`tt_mate_tb_tests_base.exe`). Rows: `logs/proof.tsv`; child logs `logs/proof_*.log` (the eight test-loop logs and
the two warm-TT logs, 4.3 MB, stay in scratch `proof/logs/`: sha256 in `logs/proof_big_logs.sha256`; their FAIL
lines in `logs/proof_tt_base_fail_lines.txt` and `logs/proof_warm_fail_lines.txt`).

Job targets: **0 failures in 40,000 KRK runs** (10,000 per Threads 2 / 4 x SmpV2 off / on; target >= 6000) and
**0 failed runs in 800 test runs** (200 per configuration; target >= 200), plus 0 in 4,000 SmpBestThread runs,
18,000 depth-sweep runs (depth 10-18) and 480 warm-TT runs at Threads 2 / 4. Every one of these multi-thread runs of
the fix reported exactly mate in 3 (the test loop: no longer-mate INFO line either).

KRK mate in 3, fresh Searcher per run, go depth 14 (misses / runs; exact = runs reporting exactly mate in 3):

| Threads | SmpV2 | base 5eabdb7 | fix BKM |
|---|---|---|---|
| 2 | off | 72 / 2000 (3.60 %), exact 1762 | **0 / 10000 (0.00 %), exact 10000** |
| 2 | on | 63 / 2000 (3.15 %), exact 1757 | **0 / 10000 (0.00 %), exact 10000** |
| 4 | off | 28 / 2000 (1.40 %), exact 1890 | **0 / 10000 (0.00 %), exact 10000** |
| 4 | on | 17 / 2000 (0.85 %), exact 1894 | **0 / 10000 (0.00 %), exact 10000** |

fix total: 0 misses in 40000 runs

SmpBestThread (SmpV2 off), depth 14:

| Threads | base | fix |
|---|---|---|
| 2 | 39 / 1000 (3.90 %), exact 865 | **0 / 2000 (0.00 %), exact 2000** |
| 4 | 15 / 1000 (1.50 %), exact 945 | **0 / 2000 (0.00 %), exact 2000** |

Depth sweep, fix only (misses / runs per depth; all four Threads 2/4 x SmpV2 configurations):

| depth | Threads 2 off | Threads 2 on | Threads 4 off | Threads 4 on |
|---|---|---|---|---|
| 10 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 11 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 12 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 13 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 14 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 15 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 16 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 17 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |
| 18 | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) | 0 / 500 (exact 500) |

sweep total: 0 misses in 18000 runs

Warm TT: an unrelated depth-9 search first (prefill40 openings), then KRK depth 14 on the same Searcher:

| tree | Threads | SmpV2 | misses / runs | note |
|---|---|---|---|---|
| fix | 1 | off | 6 / 40 (15.00 %), exact 29 | 40 FENs x 1 |
| base | 1 | off | 6 / 40 (15.00 %), exact 29 | 40 FENs x 1 |
| fix | 2 | off | 0 / 120 (0.00 %), exact 120 | 40 FENs x 3 |
| fix | 2 | on | 0 / 120 (0.00 %), exact 120 | 40 FENs x 3 |
| fix | 4 | off | 0 / 120 (0.00 %), exact 120 | 40 FENs x 3 |
| fix | 4 | on | 0 / 120 (0.00 %), exact 120 | 40 FENs x 3 |
| base | 2 | off | 5 / 120 (4.17 %), exact 109 | 40 FENs x 3 |

forge_tt_mate_tb_tests runs (a run fails when the test exits non-zero; its Threads block via FORGE_TT_MATE_*):

| Threads | SmpV2 | base: failed runs | fix: failed runs |
|---|---|---|---|
| 2 | off | 2 / 200 (INFO longer-mate lines 9) | **0 / 200 (INFO longer-mate lines 0)** |
| 2 | on | 5 / 200 (INFO longer-mate lines 20) | **0 / 200 (INFO longer-mate lines 0)** |
| 4 | off | 0 / 200 (INFO longer-mate lines 16) | **0 / 200 (INFO longer-mate lines 0)** |
| 4 | on | 1 / 200 (INFO longer-mate lines 14) | **0 / 200 (INFO longer-mate lines 0)** |

Notes:
- Base failures are the job's symptom exactly: every failed test run printed `cp 438..475` with `e8e4`
  (`logs/proof_tt_base_fail_lines.txt`); the base also reports longer mates in 9-20 of 200 test runs per
  configuration (the R3-5 INFO line), the fix in none.
- Threads 1 rows are identical on both trees (6 of 40, the same positions): by the job rule the one-thread tree is
  the lock tree; see section 3 for that case.
- The job text quotes 0 of 6000 KRK misses with SmpV2 off and 13 of 6000 with it on (base b7c1772). With this
  harness (fresh Searcher, `go depth 14`, base 5eabdb7) SmpV2 off misses as often as on; the setup behind the
  quoted numbers is not in the repository, so the two are not directly comparable. The UCI loop below measures
  the shipped exes end to end.

End to end over UCI (`tools/uci_krk_loop.py`, 3-CPU mask, 10:58-11:00 Vienna): one engine process per configuration,
per run `ucinewgame`, `position fen` KRK, `go depth 14`; a run fails unless the last score is `mate N` with N >= 3
(`logs/uci_krk_loop.log`):

| Threads | SmpV2 | `forge_r5d_off_5eabdb7.exe` (base) | `forge_r5d_bkm.exe` (fix) |
|---|---|---|---|
| 2 | off | 40 / 1000 (4.0 %), mate 3 in 877 | **0 / 1000, mate 3 in 1000** |
| 2 | on | 21 / 1000 (2.1 %), mate 3 in 928 | **0 / 1000, mate 3 in 1000** |
| 4 | off | 11 / 1000 (1.1 %), mate 3 in 934 | **0 / 1000, mate 3 in 1000** |
| 4 | on | 8 / 1000 (0.8 %), mate 3 in 953 | **0 / 1000, mate 3 in 1000** |

The first miss of each base configuration (the tool prints only the first) is `score cp 450..475` with
`bestmove e8e4`, the job's symptom.

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

## 6. How to re-run (Git Bash, from the worktree; MSYS2 ucrt64 on PATH; the PC venv Python)

```
# engine (box flags) + lock identity
bash opus_r5/r5d/tools/build_r5d.sh "$PWD" F:/opus_scratch/r5/r5d/exe/forge_r5d_bkm.exe
python -I -B <lock archive>/2_build/uci_check.py F:/opus_scratch/r5/r5d/exe/forge_r5d_bkm.exe --full
# repro harness against any tree (one g++; see the header of tools/r5d_mate_repro.cpp for the options)
g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 \
    -pthread -Iinclude opus_r5/r5d/tools/r5d_mate_repro.cpp src/{bitboard,board,book,datagen,eval,eval_params,nnue,search}.cpp \
    -static -o repro.exe
./repro.exe 1000 2 0 14            # runs threads smpv2 depth -> "failures N (x%), exact E"
# proof loops (3-CPU mask) and the report tables
python -I -B opus_r5/r5d/tools/run_pinned.py --mask 0x700 -- opus_r5/r5d/tools/r5d_proof.py --out <dir> \
    --repro-fix <fixed repro.exe> --repro-base <base repro.exe> --tt-fix <fixed forge_tt_mate_tb_tests.exe> \
    --tt-base <base forge_tt_mate_tb_tests.exe> --prefill opus_r5/r5d/diag/prefill40.fen --reference tests/syzygy_reference.tsv
python -I -B opus_r5/r5d/tools/proof_table.py <dir>/proof.tsv
# end to end over UCI, and the Threads 2 smoke
python -I -B opus_r5/r5d/tools/run_pinned.py --mask 0x700 -- opus_r5/r5d/tools/uci_krk_loop.py <exe> --runs 1000
python -I -B opus_r5/r5d/tools/smoke_matefix.py <fixed exe> --exe-off <base exe> --name x --out <dir> --expect-echo none \
    --games 200 --tc 5+0.05 --concurrency 1 --threads 2
```
