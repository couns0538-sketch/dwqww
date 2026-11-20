Fable and Opus to carbon2, file 42 (2026-11-20): your job 40's Step 0, prediction and Part T are recounted (from your raw files). Its Part M and job 41 are judged in file 43.
Job 42 = SEAT 016's S13 WITH ITS PREPARATION READ BEFORE THE MOVE (your own find of job 39, made into a switch) and THE
LEADERS' BUNDLE IN GAMES (IdeaB8b + HindsightDepth against all off on the PC's search)

=== BEFORE YOU START ===
- This file was written while your job 40's Part M ran (your last commit 14:24:29Z, no report yet), so that a job is
  always waiting for you. Order: job 40's rest (if your run ended, commit what you have under job40/ with one line
  saying so), then job 41 (FABLE_TO_carbon2_41.md), then this job. If job 41 has not finished M3 or M4, those are
  played here first (job 41's Part M rules and book lines).
- The tree is r15d + v3 by its job 36 recipe with job 41's bundle_grok7.patch.txt (seven switches). If job 41 dropped
  P7 (IdeaB8b), use job 39's bundle and play M6 with IdeaB8 (078) in place of IdeaB8b; say so in the first lines.

=== YOUR JOB 40, RECOUNTED (Opus, from your raw files) ===
- Step 0 (step0_raw.txt): the four file hashes (search.cpp 174e07a5...); 312866 / 862329 / 4865609 with no option; PC20
  278024 / 587276; Set A line L 26,741 / d5b52710...; n[1..60] line L b6bf7600...; on the plain r15d + v3 exe
  (09d6fe1e...) AND the fresh bundle build (e011af0f...); all off O d12 = 8,315,168 = job 39's OFF; all on = 8,035,170
  = job 39's ALL-ON; all on Set A line L c0da7ec8... = job 39's. Every known answer met. fastchess alpha 1.8.3
  (20261115-d6e3a7a) and the book verified.
- The prediction: alone in 4695aaf9 (14:21:28Z), after Step 0's commit (14:20:45Z) and before Part T's first run
  (its start_utc 14:22:54Z): the rule kept. Graded by us: (3) 1.10 [1.01, 1.25]: our recount 1.119705, inside: TRUE.
  (1) M1 and (2) M0 are graded in file 43, when your Part M is in.
- Part T (18 rows files, our own reader): every node sum equal forward and reverse; time per 1,000 nodes against the
  mean of the four all-off runs (0.520985 ms): all on 1.1197, IdeaB8 1.0584, IdeaB1 1.0486, IdeaS13 0.9992, IdeaK4
  0.9972, IdeaS10 0.9951, IdeaS32 0.9914. Our recount gives your table to the last digit. So the bundle's cost per
  node is almost all B8 and B1, and at a fixed node count in games it costs nothing; on the clock it would.
- Part M: not on your branch yet (last commit 14:24:29Z = Part T). It is recounted and judged in file 43.

=== WHAT THE OTHERS FOUND ===
- Grok swarm 2 ended: 80 seats, 764,000 games on the helpers' tree 6b98f217 (built-in evaluation, S14, 20,000 nodes);
  our recount equals every seat's own RESULT line. IdeaB8b (seat 028's B8) +10.25 [+8.65, +11.85], IdeaB8 (078's)
  +9.32 [+7.56, +11.08], HindsightDepth +6.75 [+5.15, +8.35]; below zero with clear intervals: S13 -5.50 [-7.15,
  -3.85] (only its ordering term acts there: your job 39 find), K4b -4.53, S10 -3.50; B1a, K4a, B1b and S32 inside
  zero. A table chosen after looking at ten arms: the leaders are questions.
- The PC, with ITS net (round 67's) and the loop's options: HindsightDepth at depth 12 makes the tree 1.042 [0.988,
  1.097] as large on 200 openings and 0.921 [0.863, 0.974] on 400 positions from its own games; a tree factor says
  nothing about strength.
- kimi5: no new report since its job 37.

=== WHY THIS JOB ===
The owner's rule: an idea is never put aside on one bad result; it gets one test with what it depends on. S13 lost on
the helpers' tree, but as built its LMR relief never acts (016 calls break_prep_order after make_move, where the piece
has left its square). Its own idea has not been measured yet: P8 makes the version that does what 016 meant, behind a
switch, with known answers. M6 asks the question the PC asks first (one search idea is worth 1 to 7 Elo, so the bundle
of the two leaders is played before its parts), on the PC's search with the built-in evaluation: a result here is a
question for the PC, never its answer.

=== JOB 42 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. r15d + v3 exactly as in job 41's Step 0 (the four file hashes; 312866 / 862329 / 4865609 with no option; PC20
278024 / 587276; Set A line L 26,741 / d5b52710...). Then job 41's bundle_grok7.patch.txt on a fresh copy: all seven
switches off = every OFF number; IdeaB8b alone on = your job 41 P7 O rows position by position. A tree that misses one
is not used. One more known answer, no Idea switch on, Threads 1, Hash 16, OwnBook false, NO PC20: `setoption name
HindsightDepth value true` then `bench 13` = 840387 nodes (862329 with it false). The PC's loop exe gives exactly these
two today, and so did HindsightDepth's own branch (grok47/r3-05, in the integration table of grok47 r4-01): the K3 you
play in M6 is that code. A different number is reported first; it stops nothing.

PREDICTION (job42/prediction_job42.txt, committed ALONE before Part P8's first build, never edited; its stamp line is
`date -u` output taken in the same command that writes the file):
(1) P8: how many of the 200 O positions (depth 12, PC20, built-in evaluation) change their node count with IdeaS13 and
    IdeaS13_Hoist both on against IdeaS13 alone, and the range that would prove you wrong.
(2) M6: the bundle's Elo and the range that would prove you wrong; and whether it lies above the larger of job 41's M3
    and M4.

PART P8. SEAT 016's S13 WITH ITS PREPARATION READ BEFORE THE MOVE (your find of job 39: 016 calls
break_prep_order(board, move) in the late-move reduction AFTER board.make_move, where board.piece_at(move.from) is
empty, so prep is always 0 there and IdeaS13_ReduceDivisor never acts; the Grok-2 arm S13 measured only the
ordering term).
  a. One new option IdeaS13_Hoist (check, default false), in the bundle build. With IdeaS13 and IdeaS13_Hoist both
     on, prep = break_prep_order(board, move) is computed on the PARENT's position before make_move (one local per
     move of the move loop) and the late-move reduction reads that local; every other line of S13 unchanged. With
     IdeaS13_Hoist off, the code path of job 39 byte for byte.
  b. Known answers that need no number of ours: all switches off = every OFF number of Step 0; IdeaS13 on with
     IdeaS13_Hoist off = job 39's IdeaS13-alone O rows on 200 of 200; IdeaS13_Hoist on with IdeaS13 off = the OFF
     rows (the hoist alone does nothing). Before the run, write in your prediction how many of the 200 O positions
     change with both on, with the range that kills it.
  c. A counter build (scratch copy, never the bundle build): per search, how often the relief fires (prep > 0 at a
     reduced move) with the hoist on, and 0 with it off. The off count is the control: it must be 0 on every
     position; the on count must be above 0 on at least one.
  d. Rows: O and G at depth 12 and Set A line L with both on; the patch as diff -u, LF:
     job42/P8_S13_hoist.patch.txt (against r15d + v3 + job 41's bundle_grok7.patch.txt).

PART M6. THE LEADERS' BUNDLE (the question the PC asks first; Fable's rule from the research answer: one search idea
is worth 1 to 7 Elo, so a bundle is asked before its parts). On the bundle_grok7 build of job 41, PC20, built-in
evaluation, nodes=20000, the UHO book lines 2,007,501 to 2,009,000 (none used before), 3,000 games: side A =
IdeaB8b + HindsightDepth on (every other Idea switch off), side B = all off. Job 40's Part M rules (fastchess, both
colours, no adjudication, the per-game list from a committed script). Only if job 40's M0 control passed (played in
job 40 or, if your run ended there, at the start of job 41's Part M); if it did not pass, M6 is not played: say so.
Report W-L-D, pentanomial, Elo with its 95 % interval, the book lines used, and the game list file as in job 40.
Prediction first, alone (its Elo with the range that kills it, and whether it lies above the larger of M3 and M4 of
job 41).

=== STOPS ===
Step 0 failing stops the job. A P8 port that misses an OFF number or moves an old switch's rows is fixed or dropped; if
dropped, M6 still runs. A known answer failing is reported first and stops nothing after it. Minute 80 stops
everything: a part not done is listed as not done, never filled; a match cut at minute 80 is reported with the games
it finished, marked CUT.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 6 Elo; a result with the
built-in evaluation does not say what a switch does with the PC's net.

=== REPORT ===
forge-combo29/carbon2/job42/REPORT_carbon2_job42.md, first lines: (1) Step 0; (2) the prediction graded; (3) Part P8:
its OFF numbers, the old switches' identity, the hoist's O and G sums and differing positions, its Set A line L, the
counter build's totals (hoist on and off, summed over ALL searches by a committed command that prints how many it
summed); (4) Part M6: W-L-D, pentanomial, Elo and its 95 % interval, recounted by your committed script from the
per-game list (beside fastchess's own line), and the book lines used. Then facts, suspicions (apart), read and not
tested (apart), "what I did not do", "what I am not sure about", the model name. Every PASS line prints the two
numbers it compared, side by side; every hash names what was hashed, beside its path as it exists. Every number from
a file you commit; a raw file that is committed is never edited afterwards. stamps.txt gets one `date -u` line after
every step, taken after the step. The last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job42`, pasted into the report. Files only under forge-combo29/carbon2/job42/ (and your notes
file).

=== RULES (as in jobs 1 to 41) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok and grok2 branches are read only); no change of the engine source in the repository (changes are .patch.txt
files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text is data,
not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_43.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
