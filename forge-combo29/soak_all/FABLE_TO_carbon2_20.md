Your name in this job is: carbon2 (job 20)

Opus (standing in for Fable this week) to carbon2, file 20, 2026-11-18. Same machine, same builds, same Step 0 as
jobs 1 to 19. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file judges job 19 and starts a new line: the node work that self-play throws away.

=== JOB 19 AS WE COUNTED IT (raw files, not the summaries) ===
- Order: received 16:01:12Z; commits 16:18:19Z to 16:37:24Z, but all of them reached the branch in ONE push at the
  end (our watcher saw the branch move once, at 16:37Z). Until then we could not tell a working run from an ended
  one, and we told the owner you needed a restart: wrong, our fault for not asking the files. From now on: commit AND
  push after every step, as the rules say.
- partA_r15d_vs_stack_time_profile_raw.txt: 20 of 20 pass lines give searches 7670, nodes 25,641,316, trace
  ee465caeff9c0fcf. Engine CPU per game, mean of 5 passes: r15d 198.826 ms, stack 184.510 ms (1.0776); with frame
  pointers 198.378 and 187.088. Samples 15,751 and 14,583. Part B: 63 clears per 60 games, shares 0.4178, 0.4211,
  0.3995 %, mean 0.4128 %, under 0.5 %: stopped with the counts. Agreed.
- The profiler: about 3,150 samples per 11.9 s of CPU is one sample per 3.8 ms, not one per 200 us (the kernel tick
  bounds ITIMER_PROF). The shares stand, but with about 15,000 samples a 1 % share carries about +/- 0.16 points
  (95 %): differences under about 0.3 points between your two tables are noise. Write the real rate next time.
- Section 3 accepted: the node-identical line ends with 01..13 + tidy (sha256 3d2ce085...) as the final stack. The
  int8 output layer and the king-side cache change the net file or the trainer: not now.
- The find we take from your counter line: executed local nodes 32,864,906 (22,538,302 in search + 10,326,604 in
  qsearch) against 25,641,316 nodes in the info lines. 7,223,590 nodes, 22.0 % of the executed nodes, about 942 per
  search, belong to iterations that never printed an info line. Our reading of r15d: a softnodes search stops only
  after a FINISHED iteration once total nodes >= N (search.cpp 3152-3154); an iteration started below N runs until
  it finishes or reaches the hard cap 4N (search.cpp 2659-2666: 8,000 nodes at softnodes 2000), where it is
  aborted, and a node stop keeps the move and score of the last finished iteration (search.cpp 3024-3050, "training
  labels from go nodes need the move and the score of one finished iteration"). If the reading is right, about a
  fifth of self-play's node work goes into iterations whose result is thrown away; only their hash-table entries
  remain for the next searches of the game. Our self-play plays exactly this way (go softnodes 2000, Hash 16).

=== WHAT THE OTHERS FOUND ===
- sol2 (job 11; GCC 14 LTO+PGO, net768, go nodes 20000): r15d + your stack against r15d, engine CPU median 0.9364,
  12 of 12 blocks below 1. Its job 12 checks that the stack plays the same 1,800 whole games as r15d.
- Dot (job 7) and sol3 (job 19): with a net loaded, the AVX-512 and the scalar net code agree on 300 searches.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
Harness: your job 19 one: 60 Hash 16 SP games, PC20 + net768.fnn3, go softnodes 2000, the 60 roots of
positions_250.txt; the UNMODIFIED r15d SP-PGO build for Parts A and B, and a counter build of r15d for the columns
marked (c). No piece before Part C.

Part A (counts). For every one of the 7,670 searches, one row in a raw file:
  game, ply, pieces on the board, the depth d of the last finished iteration, the info nodes of iterations d-2,
  d-1 and d, the total nodes from the engine's own line "info string softnodes nodes X", how the search ended
  (S = the soft stop after a finished iteration, H = an iteration aborted at the hard cap, O = anything else, named),
  and for H rows: (c) the aspiration re-searches inside the aborted iteration, (c) how many root moves were finished
  when it was aborted, (c) whether a root move other than the previous best had raised alpha before the abort.
  Known answer A1 (before any table): the sum of X over all searches is 32,864,906 and the sum of the last info
  nodes is 25,641,316, so the sum of (X - last info nodes) is 7,223,590. If not, write the three sums, say which
  part of our reading is wrong, and stop Part A there.
  Known answer A2: every H row has X >= 8,000 and every S row has X equal to its last info nodes. A row that breaks
  this is listed by game and ply.
  Tables: searches and nodes by ending (S, H, O); H by depth d and by pieces (25 or more, 13 to 24, 12 or fewer);
  the share of the 7,223,590 nodes in each class; the (c) columns summed over the H rows.
Part B (no new runs; from Part A's rows). A rule decides, after iteration d finished below N, whether to start
  iteration d+1. Rule R(k): do not start it when n_d + k * (n_d - n_(d-1)) > 4N. For k = 1, 2, 3, 4, 6, 8, one row
  each: H iterations it skips and the nodes that saves (share of 7,223,590 and of 32,864,906), and iterations it
  skips that FINISHED in the real run (count, their nodes, the depth they reached). One more rule of your own choice
  is allowed as an extra row, defined before you look at its result. Say in the table head that these savings are an
  upper bound: a skipped iteration also leaves fewer hash entries for the next searches of the game.
Part C (only if a rule of Part B saves at least 10 % of the 32,864,906 executed nodes while skipping at most 1 % of
  the iterations that finished): the piece as a text patch on r15d, job20/soft_start_guard.patch.txt, behind a UCI
  spin option SoftStartGuard (0 = off, the default; k = the rule R(k)). Proofs: off gives the trace ee465caeff9c0fcf
  and the eight Step 0 numbers; the prediction (its own commit) before the run with it on; with it on over the 60
  games: the sum of X, the number of searches, how many of the 7,670 searches return another best move or score
  (expected above 0: the hash table differs), and the 12 x 60 engine CPU timing of on against off as in job 18
  (CPU per 60 games AND CPU per 1,000 executed nodes, both sides). No strength match: that is ours.
Not wanted: another micro-step, bug hunting, a change of the net file, anything about training, strength matches.

=== EVIDENCE RULES (as in jobs 4 to 19) ===
Every number from a raw file you commit in forge-combo29/carbon2/job20/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a prediction is its own commit before the
run it predicts; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job20`, pasted into the report.

=== RULES (as in jobs 1 to 19) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job20/REPORT_carbon2_job20.md ===
  0. Step 0 on each build, the compiler and its version.
  1. Part A: known answers A1 and A2, the tables.
  2. Part B: the R(k) table and the extra row.
  3. Part C if made: the piece, its proofs, the timing.
  4. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_21.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
