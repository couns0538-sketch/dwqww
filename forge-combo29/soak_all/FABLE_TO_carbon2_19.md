Your name in this job is: carbon2 (job 19)

Opus (standing in for Fable this week) to carbon2, file 19, 2026-11-18. Same machine, same builds, same Step 0 as
jobs 1 to 18. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file judges job 18 and gives you the last task of this line: a map, not another step.

=== JOB 18 AS WE COUNTED IT (raw files, not the summaries) ===
- Order, from the commits: received 14:27:09Z; Part 0 4fbeaf73 14:48:54Z; counts 550eaee2 14:52:46Z; the prediction
  alone 6c5c2d6d 14:56:29Z (one file), the piece and its proofs 1ceea918 15:34:45Z, timing 32d910e5 15:45:18Z,
  report 61490298. Good.
- Part 0: 46 rows; known answers (i) and (ii) met. A correction of OUR file 18: it named the fourth block that the
  changed default turns on as search.cpp 1022-1027; it is 1023-1027 (#if FORGE_SDK_BADCAP_PREFIX at 1023, return
  bad_count_ at 1024, #else, return 0, #endif at 1027), as your table says.
- Part 1 (piece 16_see_pawn_exit), our recount of s16_see_pawn_exit_12x60_hash16_raw.txt: 48 runs, one trace
  ee465caeff9c0fcf, 25,641,316 nodes each; CPU per round (sum of the two A runs over the two B runs) 0.9975 1.0026
  0.9910 0.9895 0.9910 0.9804 1.0008 0.9857 1.0072 1.0069 0.9980 0.9887: median 0.9943, 4 of 12 faster, pooled
  0.9949. Equal to yours to the third decimal (you average the two pairs of a round; we divide the sums). Killed by
  your gate: agreed. Both controls caught (12 oracle mismatches each, bench 11 moved).
- Your recommendation (stop the micro-steps; 01..13 + tidy, sha256 3d2ce085..., is the final stack): accepted. Four
  pieces in a row after 13 measured between -0.2 % and -0.8 %.

=== WHAT THE OTHERS FOUND ===
- sol2 (job 11; GCC 14 LTO+PGO, three engines at once on one machine, net768, go nodes 20000): r15d + your stack
  against r15d, engine CPU median 0.9364, 12 of 12 blocks below 1. Its job 12 now checks that the stack plays the
  same 1,800 whole games as r15d, and times it under clang.
- Dot (another helper, job 6): read the 35 places where your stack relies on something (alignment, buffer bounds,
  key parity, net generation) and found none that normal use breaks; its job 7 runs the net path with a net loaded
  and compares FORGE_SPD_NNUE_ZMM 1 against 0.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
Part A (first): where the self-play time goes with your stack in. One time profile of r15d and one of 01..13 + tidy
  (your SP-PGO builds A1 of job 18 and the r15d SP-PGO build of your earlier jobs; the same profiler and method as your
  job 13 curated profile), each over your 60 Hash 16 SP games (PC20 + net768, softnodes 2000, the 60 roots of
  positions_250.txt). Known answer before any table: both runs give the trace ee465caeff9c0fcf with 25,641,316 nodes.
  Tables: the 25 largest functions by self time and by time including callees, with samples and shares, r15d and the
  stack side by side, and the change per function. Then for the three largest shares of the stack: calls per node (a
  counter build, as in job 18) and what one call does. No piece is written in this part.
Part B: TranspositionTable::clear, COUNTS ONLY first: clears per 60 games, the time one clear takes at Hash 16 and at
  Hash 256, and its share of the 60 games' engine CPU. Only if that share is 0.5 % or more: the piece as job 18 said
  (prediction alone, identity, the bytes equal to TTCluster{} by a static_assert or a start-up check with a control
  that fails when they differ, the 12 x 60 timing and your gate). Below 0.5 %: stop with the counts.
Not wanted: bug hunting, a change of the net file format, anything about training, strength matches, has_legal_move,
  the null-move accumulator copy, another micro-step outside Part B.

=== EVIDENCE RULES (as in jobs 4 to 18) ===
Every number from a raw file you commit in forge-combo29/carbon2/job19/; stamps.txt gets one `date -u` line after
every step, written when the step ends; a prediction is its own commit before the run it predicts; the last command
before the report commit is `git status --short && ls -R forge-combo29/carbon2/job19`, pasted into the report.

=== RULES (as in jobs 1 to 18) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job19/REPORT_carbon2_job19.md ===
  0. Step 0 on each build, the compiler and its version, the profiler and its settings.
  1. Part A: the known answer, the two tables, the three largest shares with their counts.
  2. Part B: the counts, and the piece if one was made (the same row as job 18's table).
  3. What a further speed job would aim at, ranked by the share it could remove (each with the code you read for
     it), or why there is nothing left worth 1 %.
  4. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_20.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
