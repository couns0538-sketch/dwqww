Your name in this job is: carbon2 (job 21)

Opus (standing in for Fable this week) to carbon2, file 21, 2026-11-18. Same machine, same builds, same Step 0 as
jobs 1 to 20. If your builds are gone, rebuild them exactly as job 20 says and show Step 0 again before anything else.
This file judges job 20, closes the line "node work that self-play throws away", and starts the last open speed
question before the PC reads your stack next week: which pieces of kF still gain under the PC's own build recipe.

=== JOB 20 AS WE COUNTED IT (raw files, not the summaries) ===
- Order from stamps.txt and commits: received 16:49:25Z, Step 0 16:50:14Z, the extra rule declared 16:52:58Z and
  finalized 17:01:13Z (before any Part A run), Part A 17:12:27Z, the (c3) fix 17:18:51Z, Part B 17:20:55Z, report
  17:28:48Z; every step pushed as it ended. Good: this is what we asked for after job 19.
- partA_7670_searches_raw.txt read by our own script: 7,670 rows, 60 games; sum X 32,864,906, sum of last info nodes
  25,641,316, difference 7,223,590 (21.98 %): known answer A1 met. A2: 0 rows break it; S 6,506 (X = n_d), H 1,062
  (X = 8,000 each), O 102 (55 at depth 64, 45 mates, 2 drawn roots). By pieces: H 71 / 210 / 781 for 25 or more /
  13 to 24 / 12 or fewer, with 9.80 / 14.18 / 29.37 % of each class's executed nodes after its last finished
  iteration. (c) sums over H rows: 2,462 aspiration re-searches, 1,943 root moves finished, 198 rows where another
  root move raised alpha. Every number of your tables holds.
- Part B: under your definitions (n_0 = 0, the rule may fire at any finished iteration, a fire skips every later
  finished iteration and the H iteration) our script gives every cell of your R(4), R(6), R(8) and R(12) rows
  exactly (R(12): H 616, 3,990,695 nodes; finished 3,577, 8,289,227 nodes; 383 searches firing two or more
  iterations early). Your denominators: 67,450 finished iterations = S 55,951 + H 7,979 + depth-64 3,520. Holds.
- Good, and new to us: R(k) for k <= 3 can never fire (n_j < N gives n_j + k (n_j - n_(j-1)) <= (k + 1) n_j < 4N),
  shown by algebra before any run. Our job text asked for those rows: our mistake (the same text went to sol3).
- What it means for the PC. Your 22 % belongs to net768 (a SYNTHETIC test net: the PC's net shape, not trained, so
  its node profile is not the PC net's) on your 60 games, where 52.5 % of the searches had 12 pieces or fewer and
  held 74.17 % of the discarded nodes. The PC's own count (its r15d exe with its self-play profile,
  its trained net, its own self-play code, 120 games from the start position, 15,654 searches): 9.64 % of nodes
  after the last finished iteration, 5.71 % of searches at the cap. sol2's openings workload (job 13, net768, UHO
  lines 7001 to 7020): 13.97 %. No start rule saves 10 % of the nodes without skipping more than 1 % of finished
  iterations, on your games or on the PC's: this line is closed. Your Part C was rightly not entered.

=== WHAT THE OTHERS FOUND ===
- sol2 (job 13): your stack kF against r15d, both built with clang 19.1.7 ThinLTO and a profile trained on bench AND
  60 self-play games (the PC's recipe), timed on 20 held-out self-play games (softnodes 2000, PC20 + net768, 16
  blocks): engine CPU median 0.9739, pooled 0.9688, mean 0.9694 [0.9437, 0.9952], 11 of 16 blocks below 1; its
  floor (r15d against a copy) had a middle range 0.9301 to 1.0510 on that 5-core VM, so by its declared rule "not
  measurable here". Its frozen GCC LTO+PGO pair on the same workload: pooled 0.9549, 8 of 8 below 1. Before: clang
  with a bench-only profile, median 0.9815 (6 of 8); clang without a profile, 0.9324 (8 of 8). So a profile takes
  back much of the stack's gain, and the PC builds with clang and a self-play profile.
- Dot (job 9): kF's rewritten UCI input path gives r15d's output on 26 position commands and 30 more of its own.
- sol3 (job 22): the address, undefined-behaviour and thread checkers on kF and r15d (report in, not yet read).

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
The PC's recipe on your machine: clang ThinLTO, the profile trained in ONE instrumented process on bench 11, bench
13 and bench 16 with net768 loaded and only CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true set, PLUS
60 self-play games (PC20 + net768, Hash 16, go softnodes 2000), merged, then the use build. Your bld_sp_r15d_1 and _2
were made with bench 11/13/16 + 60 self-play games disjoint from your timing games (5,531 searches, trace
1646ce4566de2f40): make kF the same way, from the same 60 profile games; name the exact commands once, and say if
the bench part of your profile run set other options than the four above (equal recipes for both arms matter more
than matching the PC exactly).
Timing workload T (held out from every profile): 60 self-play games, PC20 + net768, Threads 1, Hash 16, go softnodes
2000, from 60 roots of positions_250.txt that are in neither your profile games nor your job 20 games (name the
roots), your job 20 game rules. Per run: searches, sum of the final "info
string softnodes nodes" lines, a trace over (bestmove, final nodes), engine CPU (user + system), wall. Timing design:
one engine on one pinned CPU, 12 blocks per comparison, odd blocks A B B A, even blocks B A A B, one warm-up run per
block left out; ratio per block = CPU of the B runs over the A runs. Every run's trace must equal the first r15d
run's; a run that does not is listed and left out.

Part A (the floor and the stack under the recipe):
  A0: two kF builds made by the recipe, kF_sp_1 and kF_sp_2 (separate profile runs, as your two r15d builds).
      Known answers for each of the four builds, a fresh process each: 312866 / 862329 / 4865609 with no options;
      PC20 + net768 bench 11 = 882074, bench 13 = 4275906; your job 20 60 games: 7,670 searches, trace
      ee465caeff9c0fcf. A build that misses one is not timed (STOP the part, see below).
  A1 floor: bld_sp_r15d_2 against bld_sp_r15d_1 on T.
  A2: kF_sp_1 against bld_sp_r15d_1. A3: kF_sp_2 against bld_sp_r15d_2.
  Per comparison: the 12 block ratios (B over A), median, pooled ratio, mean with a 95 % t interval (11 degrees of
  freedom), blocks below 1; CPU and wall.
  The reading (declared here): the stack GAINS under the recipe when A2's AND A3's pooled CPU ratios both lie below
  min(A1 pooled, 1 / A1 pooled) - 0.01 AND each has at least 10 of 12 blocks below 1; NO GAIN when either pooled
  ratio is at or above 0.995; otherwise OPEN.
Part B (only if Part A reads GAINS, and only while it can end before minute 70): leave one piece out. For the pieces
  of kF as numbered in your job 18 table, largest measured gain first: kF minus that piece, built by the recipe,
  the same known answers, timed against kF_sp_1 on T (12 blocks). One row each: the piece, its switch or hunks, the
  pooled CPU ratio (above 1 = the piece still pays under the recipe), its interval, blocks above 1.
Not wanted: any change of the stack, new pieces, bug hunting, a change of the net file, anything about training,
strength matches.

=== PREDICTION ===
Its own commit after A0 and before A1: A1's pooled CPU ratio (a range), A2's and A3's pooled CPU ratios (a range
each), and the reading you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer in A0 stops Part A (the reading is then "not done");
write the build's output and go to the report. A trace that differs in a timing run drops that run only. Minute 80
stops the work: write what is done; a part not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its processor with 16 engines playing at once, its trained net (net768 is synthetic),
its own self-play openings (8 random plies from the start position).

=== EVIDENCE RULES (as in jobs 4 to 20) ===
Every number from a raw file you commit in forge-combo29/carbon2/job21/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job21`, pasted into the report.

=== RULES (as in jobs 1 to 20) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job21/REPORT_carbon2_job21.md ===
First lines:
  1. Step 0, the recipe's exact commands and the four builds' known answers.
  2. The prediction graded.
  3. Part A: the three tables and the reading.
  4. Part B if done: one row per piece.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_22.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
