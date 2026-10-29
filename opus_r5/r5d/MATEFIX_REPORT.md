# Forge Opus R5D: forced mate reported as a centipawn score with Threads >= 2 — IN PROGRESS

**Status:** setup done; reproduction in progress. Last push: see the head commit time (pushes every 10 min).

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

## 1. Reproduction (in progress)

## 2. Root cause (in progress)

Read so far (no conclusion yet):
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
