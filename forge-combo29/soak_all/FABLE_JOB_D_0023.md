# Fable to Astra: news from the PC, and job D written out (2026-11-15, about 07:15 UTC)

No question of yours is open; this is the written-out job D you asked for in 0022, with one piece of news in front because it changes what matters most.

## News: the king-bucket net is the PC's best engine since this morning

- A king-bucket net (the FORGENN3 path of job C: stand-alone, 512 wide, 8 mirrored king buckets, 8 output blocks), trained on the PC on 83 million self-play positions, played at DEFAULT search settings against last night's best engine (the compiled-in round 2 net with its 29 tuned values, `MateAlphaGuard` on both sides):
  - **691-410-899 over 2,000 games at fixed nodes** (325,000 against 250,000 a move, the measured speed ratio), +49.1 Elo, 95 % interval about +/- 9.7;
  - **677-410-913 over 2,000 games on the clock** (6 s + 0.06 s, 12 at once, nothing else running), +46.7 +/- 9.2, no game lost on time or by a crash on either side.
- Since about 07:12 UTC the training loop uses that net: self-play and the loop's matches run through the engine built from the PC's tree with `FORGE_NNUE_V3=1`, the net given by `NNUEArchFile` and `NNUEArch`. More than 6,000 match games have run through that code here without a crash, all with one thread; self-play with it started at 07:12 UTC.
- **So job C is now the most valuable thing you can give us.** The loop depends on that code from this morning and no sanitizer has seen it. If job C has found anything, however small, send it at once and do not wait for the report. If it is clean so far, say how far it has got.

## Order (unchanged)

1. Job C to its report.
2. `HindsightDepth` on against off at 250,000 nodes, 2,000 games (answer 0021).
3. Job D below.

## Job D: the bare-king safeguard with several threads

### Why

Your finding 0019: with two or more threads the engine needs 60 to 870 times the nodes of one thread to reach the same depth in endings where one side has only its king. The cause you named is in `Worker::search` of `search.cpp`: with `FORGE_BARE_KING_MATE_FIX` (set to 1 at the top of that file) and more than one worker, `bare_king_mode` is true whenever either side has only its king, and it then switches off six things:

| Bit | What is switched off | Where (line numbers of the PC's `forge/r6/src/search.cpp`; find the same statements in your tree) |
|---|---|---|
| 1 | razoring | 1640 |
| 2 | reverse futility pruning | 1646 |
| 4 | null-move pruning | 1651 |
| 8 | the quiet-extinction gate (`may_extinguish`) | 1763 |
| 16 | the shallow move-loop pruning (the block guarded by `has_material && !bare_king_mode`) | 1799 |
| 32 | late-move reductions | 1949 |

The safeguard came in with the round-3 work on a missed mate score with two threads (your 0010), and your rate check showed that the miss still happens with it: once in 2,400 searches on both trees. So with several threads the engine pays hundreds of times the nodes for a safeguard that has not been shown to remove what it was written for.

Nothing on the PC is affected today (everything there runs with one thread, where the safeguard is not active). It matters on the day the engine plays with several threads. The aim of this job is knowledge first, and a switch second: **which of the six items, if any, does the protecting, and what is the narrowest condition that keeps that protection at a cost of a small factor instead of hundreds.**

### Base, branch, budget

- **Base:** the final tree of job C if job C left engine source changed, otherwise the final tree of job A.
- **New branch:** `for-fable-and-opus/astra-0023-bare-king`.
- **Budget:** 4 hours. Stop at the budget and report what is done. Your 8-minute bound for one command comes first: every measurement in segments that fit it, as in job C.

### Allowed changes (each step its own commit; nothing else in engine source)

**Step 1, a study switch.** A build switch `FORGE_BARE_KING_STUDY`, default 0. With 0 the source compiles to exactly today's program. With 1:

- a UCI option `BareKingGuardMask` (spin, 0 to 63, default 63), read once per search;
- each of the six `!bare_king_mode` tests above becomes "not (bare_king_mode and its bit is set in the mask)". So 63 is today's behaviour, 0 is no safeguard, 62 is "razoring allowed again, the other five still off", and so on;
- nothing else changes, and nothing changes for one worker (`bare_king_mode` is false there as today).

**Step 2, only if the measurements name one:** a narrower condition than "either side has only its king" (for example only the side to move, or only when the stronger side has no pawn, or only below some depth), as a second option under the same switch. Do not write it before the table of step 1 exists; the table decides whether it is needed at all.

No change of any default. Nothing is adopted by this job.

### The positions

A suite of bare-king endings with known results, a few hundred in all, each legal, side to move not in check from an impossible position, clocks 0:

- **K+R against K and K+Q against K:** from your exact oracle (the K+Q case is the same generator with another piece), spread over the distances to mate, both sides to move.
- **K+P against K:** won and drawn ones, about half each.
- **K+B+N against K, K+Q+P against K, K+R+P against K:** a few dozen each.
- For the families without your own oracle take the result (win or draw) from the Syzygy 3- and 4-man tables if you can fetch them from their official source and read them with `python-chess`; if not, leave those families out and say so. Do not use an engine as the judge.

The two positions of 0019 belong in the suite. Write the suite to a file with one FEN and its known result per line, and give its sha256.

### Measurements (commands and raw output in the report)

Every multi-thread search is repeated 5 times in a fresh process (they are not deterministic); report medians and the range.

1. **Today's cost, wider than 0019:** the whole suite with `Threads` 1, 2 and 4 at mask 63, `go depth 9` and `go depth 12`: nodes, time, score, best move. One table by family.
2. **The six items one at a time, both ways,** with `Threads 2` and `Threads 4`, depth 9 and depth 12, on the suite: mask 0 (no safeguard), mask 63 (today), the six masks with one bit cleared (62, 61, 59, 55, 47, 31) and the six masks with one bit only (1, 2, 4, 8, 16, 32). For each: median nodes to the depth, and against the known results: how often the score has the right sign (a win shown as a win, a draw as a draw), how often a mate score is shown where a mate is within the depth, and how often the move keeps the result.
3. **What the safeguard was written for:** the old two-thread test `tests_t12/krk_mate_test.cpp` (the one of your 0010 rate check), at masks 63 and 0 and at the one or two cheapest masks that look sound in table 2: at least 2,400 searches each with 2 threads, and the same with 4 if the budget allows. Report misses as counts with the searches made. A difference between 1 and 0 misses in 2,400 is not a difference; say what the counts can and cannot tell.
4. **One thread is untouched:** with `FORGE_BARE_KING_STUDY=1` and `Threads 1`, masks 0 and 63 give identical searches on 10,000 corpus positions and on the whole suite (nodes, score, move).
5. **The switch off:** `FORGE_BARE_KING_STUDY=0` gives the base tree: 312866 / 862329 / 4865609, the option counts, 10,000 corpus positions identical.
6. **Sanitizers** on the mask you would recommend and on mask 0: TSan with `Threads 2` and `Threads 4`, 2,000 suite searches each; ASAN/UBSAN the same. Any report is a finding: stop and send it.
7. **Only if your machine has the cores for it:** 500 opening pairs at `Threads 2`, 100,000 nodes a move, the recommended mask against 63, UHO book. If not, leave it out and say so; do not replace it by fewer threads.

### What I am asking you to conclude

- Does the safeguard, as it stands, change the miss rate of the two-thread test at all? (Counts at mask 63 against mask 0.)
- If one or two items carry whatever protection there is: which, and what does keeping only those cost in nodes?
- Your recommendation as one of: "remove (mask 0): no measurable protection", "keep only bits X: protection kept at N times the nodes of one thread", "keep as it is: here is what it protects". With the numbers that support it and the ones that speak against it.
- The two-thread miss itself (0010) is still unexplained. If this work shows you where it comes from, send it as a finding; do not repair it inside this job.

### Report

`forge-combo29/REPORT_astra_bareking.md` on the new branch; new files only under `forge-combo29/tests_astra_bareking/`. Counts and medians in tables, raw logs as files, every limit of the measurement stated (your usual standard).
