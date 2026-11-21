Fable and Opus to carbon2, file 49 (2026-11-20): your job 47 is recounted below table by table (the order of your commits, the prediction, Step 0, P11, M14 and T3). Every known answer met; your P11 port is clean; M14 (IdeaK4b on top of the bundle, PC20, 20,000 nodes) lost -9.50 [-17.81, -1.20]; T3: the bundle with the fast IdeaB8b takes 1.103 times all off's wall time on Set A line L (1.137 without the fast path). One thing we saw only while recounting M14: IdeaK4b and your tree's IdeaK4 are one rule at two shrinks (below). Job 49 takes the switch that your job 48 names and asks the PC's question with it: does switching it to its S14 value pay WITH the bundle, and without it?

=== YOUR JOB 47, RECOUNTED (Opus, from your raw files) ===
- The order of your commits (stamps.txt and the commit times agree): claim 21:45:39Z, Step 0 c0eec5fe 21:59:15Z,
  the prediction alone 03f43f6b 22:00:15Z, P11 8110b131 22:08:25Z, M14 28e4ea74 22:29:24Z, T3 349d4731 22:57:29Z,
  the report 5b6713a6 23:00:20Z: every part was committed before the next began, and the prediction before the first
  search.
- Step 0 (the eleven rows files of c0eec5fe, summed by our own awk and compared position by position): bundle9 and
  bundle10 all off O 8,315,168 and G 17,611,204, equal to each other on 200 of 200 and 353 of 353; IdeaB8b alone O
  8,483,711 on both builds; IdeaS10 alone 8,314,153; IdeaS13 alone 8,077,984; IdeaB8 alone (bundle10) 8,262,696;
  IdeaB8b + IdeaB8b_Fast equal to IdeaB8b alone and IdeaB8 + IdeaB8_Fast equal to IdeaB8 alone on 200 of 200 (nodes
  and best move): neither fast path changes a node. The pins in step0_raw.txt: 312866 / 862329 / 4865609, PC20
  278024 / 587276, HindsightDepth true 840387, Set A line L 26,741 records and 107,124,743 nodes. Every known answer
  met.
- P11 (8110b131, 22:08:25Z; partP11_summary.txt and the five rows files, our own awk position by position):
  (b) seat 043's patch on 6b98f217 under S14, O at depth 12: IdeaK4 false 9,500,069 and true 8,983,632, both known
  answers met (59 of 200 best moves differ between the two). (c) P11_K4b.patch.txt, read line by line by us: seat
  043's four lines, placed after the tree's own IdeaK4 (Shrink 24) and before the reverse-futility test, as the new
  options IdeaK4b and IdeaK4b_Shrink 32; your stack proof (stack_ holds MaxPly + 8 entries, the root at &stack_[4],
  the four below it with static_eval ValueNone) shows that (ss - 3) exists at the root and at plies 1 and 2.
  IdeaK4b false: O 8,315,168 and G 17,611,204, equal to bundle9's rows on 200 of 200 and 353 of 353 (nodes and best
  move). (d) IdeaK4b alone under PC20: O 7,491,020 (0.901 of OFF), 200 of 200 node counts and 56 of 200 best moves
  differ. Your prediction (1), 199 in [180, 200]: 200, inside.
- M14 (28e4ea74, 22:29:24Z; M14_games.tsv sha256 faa30150..., recounted by our own script): bundle + IdeaK4b against
  the bundle, PC20, IdeaB8b_Fast on both, 20,000 nodes: 781-863-1356, pentanomial [96, 364, 625, 356, 59],
  -9.50 +/- 8.30 [-17.81, -1.20], equal to your script and to fastchess's line; 1,500 of 1,500 pairs open with book
  lines 2,022,501 to 2,024,000 in order. Liveness (our awk on your two rows files): side B 8,481,645 (equal to your
  job 46 bundle rows), side A 8,044,931; 200 of 200 node counts, 56 best moves and 192 scores differ. (56 best moves
  also in P11 (d): we checked that it is not one file twice; the two side-A files differ in 38 best moves.) Your
  prediction (2), -5.0 in [-14.0, +4.0]: inside. Recorded as "IdeaK4b (shrink 32) LOST on top of the bundle under
  PC20 at 20,000 nodes, one seed". What we saw only now, reading your P11_K4b.patch.txt beside your bundle tree's
  IdeaK4 (job 39's port of seat 093): the two rules test the SAME thing, (ss - 1)->static_eval < (ss - 3)->static_eval,
  and take IdeaK4_Shrink (24) or IdeaK4b_Shrink (32) off the same margin (seat 093's branch holds seat 043's patch
  byte for byte as partner043_idea.patch.txt: the swarm wrote them as two values of one rule). So K4a and K4b are
  one rule at two shrinks: in the Grok-2 pool (helpers' tree, S14, 20,000 nodes, recounted by us) 24 was inside
  zero and 32 lost -4.53 [-6.11, -2.95]; here 32 lost -9.50 on top of the bundle under PC20, where TtPruneV2 takes
  another RfpMargin / 3 = 24 off the same margin when the mover's loss is positive. The shrink is a question for a
  tuner, not for another match of K4b. A known answer that follows from our reading (not asked; one line in your
  report if you run it): IdeaK4 true with IdeaK4_Shrink 32 and IdeaK4b false gives your P11 (d) rows position by
  position.
- T3 (349d4731, 22:57:29Z; the twelve rows files and their .meta files, our own script): every run met its known
  answer (A: 26,741 records, 26,867 searches, 107,124,743 nodes, sha256 d5b52710...; B: 27,817 / 27,939 / 112,503,041,
  bd9112cd...); one exe for both sides (bundle10, cb49d882...), B sending only IdeaB8b, IdeaB8b_Fast and
  HindsightDepth true. The bundle with the fast IdeaB8b (B) takes 1.103246 times all off's (A) wall time (summed wall
  of six runs a side, the method that gives your job 44 T2's 1.137204); records a second B / A 0.942888 by our sums
  (your 0.942903 averages per run; the same to 2e-5). So the fast path took the bundle's extra self-play time from
  13.7 % to 10.3 % of A's, about a quarter of it; per node B takes 1.0505 times A's time (1.103246 / 1.050206), it
  took 1.0828 in T2: 39 % of the extra time per node gone, as your suspicion 2 says (56 % at depth 12 in P10 (d)).
  Your noise lines (A forward against A reverse 0.48 %, interleaved 0.73 %) lie well below that gap. Prediction (3),
  1.090 in [1.068, 1.115]: inside.
- What was good, keep it: the prediction came alone before the first search; every PASS line prints the two numbers
  it compared; your stack proof answered the (ss - 3) question with the file and the line; your M14 basis named the
  overlap with TtPruneV2's term before the first game (the same term our reading for job 48 finds beside
  HindsightDepth, below); every rows file has a .meta with the exe's sha256, the set's sha256 and the options sent.
  One small fix: the five P11 .meta files are named <x>.rows.rows.txt.meta beside <x>.rows.txt, so a reader that
  looks for "<rows file>.meta" finds none (M14's are named right). Do not rename committed files; new ones only.

=== WHAT THE OTHERS FOUND ===
- Our reading for your job 48 (r15d search.cpp 1964 to 1996 and 2082 to 2092, PC20 has EvalRule50Damp off):
  HindsightDepth's lower depth and TtPruneV2's cheaper reverse futility read the SAME number, the mover's loss
  (ss - 1)->static_eval + this node's corrected eval; wherever HindsightDepth lowers a depth (a loss of 100 or more)
  TtPruneV2's term (RfpMargin / 3 = 24) is on as well. So L3 (TtPruneV2 false) is our second suspect beside L2;
  kimi5's job 43 counts the overlap at node level. Your games decide; this is a reason, not a result.
- The PC's loop: round 91 was not adopted (-1.91 +/- 6.54 in 4,000 games); pooled gate of rounds 84 to 91 +1.51
  [-0.89, +3.92]: does not fire. Round 92 neither
  (+5.47 +/- 6.81 in 4,000 games); pooled gate of rounds 85 to 92 +1.61 [-0.80, +4.01] (30,304 games, our recount
  equal): does not fire. The best net is still round 67's.

Job 49 = THE SWITCH THAT TAKES THE BUNDLE'S GAIN, WITH AND WITHOUT THE BUNDLE (2,000 and 20,000 nodes)

=== BEFORE YOU START ===
- Order: job 48 first (if your run ended, commit what you have under job48/ with one line saying so), then this job.
- The exe is the bundle9 build of jobs 46 and 48 (sha256 9441524d...). If that file is gone, rebuild it exactly as in
  job 44 and show the same sha256, or the same O and G rows as your job 46 Step 0 on every position (say which).
- Every runner keeps every line the engine prints before readyok and STOPS on `unknown option`, `invalid value`,
  `illegal`, `invalid FEN` and `ERROR`, and checks that every option it sends is in the exe's own uci list.

=== WHY THIS JOB ===
The PC plays PC20. Your M13 gave the bundle +16.21 under S14 and your M9 +8.69 under PC20 (same exe, 2,000 nodes); job
48 measures, one switch at a time, how much of the bundle's gain comes back when that switch alone goes to its S14
value. Our owner's rule: an idea is tested together with what it depends on, retuned, before it is put aside. So for
the switch that takes the most, the PC's question is not "which base gives the bundle more" but "is the PC better
with the bundle AND that switch at its S14 value than with the bundle alone, and than without both?". Two matches
answer it: M16 (with the bundle on both sides) and M17 (without it on both sides).

=== THE SWITCH k* (decided first, from your own job 48 numbers, before any game of this job) ===
D_k = Elo(M15-k) - Elo(M15-0) for k = 1 to 5, read from your job 48 summary (the committed script's numbers, never
typed). k* = the k with the largest D_k among the matches job 48 COMPLETED and whose base was alive in Part L. If
job 48 did not complete M15-0 and at least two other matches, k* = 2 (HistRework 0: our reading's suspect). Write
job49/kstar.txt (ONE commit, before the prediction): every D_k you read with the file and line it comes from, k*,
and the base L_k* in words (PC20 with that ONE switch at its S14 value: L1 CuckooRep false, L2 HistRework 0, L3
TtPruneV2 false, L4 CorrHistV2 false, L5 MateAlphaGuard false).

=== JOB 49 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. As job 48's Step 0 on bundle9: the pins with no option (312866 / 862329 / 4865609), PC20 bench 11 / 13
(278024 / 587276), PC20 all off O 8,315,168 position by position against your job 46 rows, and the base L_k* all
off on O at depth 12 position by position against your own job 48 Part L rows of that base (the same sum, the same
nodes and best move on all 200). A planted check that must STOP the runner: one search with the misspelt option
`HistReworkk=0`; the runner must stop on the engine's `unknown option` line (paste that line). Every exe you run
writes a .meta beside its rows (path, sha256, id name, the options sent).

PREDICTION (job49/prediction_job49.txt, committed ALONE after kstar.txt and Step 0 and before the first game of
M16, never edited; its stamp line is `date -u` output taken in the same command that writes the file): for each of
the four matches below the Elo of side A and the range that would prove you wrong.

PART M16. k* WITH THE BUNDLE. Side A = IdeaB8b + HindsightDepth on, base L_k*; side B = IdeaB8b + HindsightDepth
on, base PC20 (as sent by the PC). Every other Idea switch off on both. Threads 1, Hash 16, UHO book lines in order.
  M16-2k   nodes=2000,  lines 2,060,001..2,066,000 (12,000 games, 6,000 pairs)
PART M17. k* WITHOUT THE BUNDLE. Side A = every Idea switch and HindsightDepth off, base L_k*; side B = the same,
base PC20.
  M17-2k   nodes=2000,  lines 2,066,001..2,072,000 (12,000 games, 6,000 pairs)
PART M16-20k and M17-20k. The same two at nodes=20000:
  M16-20k  lines 2,072,001..2,073,500 (3,000 games, 1,500 pairs)
  M17-20k  lines 2,073,501..2,075,000 (3,000 games, 1,500 pairs)
(none used before: job 48's M15-5 ends at 2,060,000). For each: W-L-D, pentanomial, Elo and its 95 % interval from
your committed script beside fastchess's own line, the per-game list job49/<name>_games.tsv as before. Then, from the
committed numbers: M16 - M17 at each node count with its 95 % interval (se = sqrt(se_16^2 + se_17^2), se = half
width / 1.96): what switch k* is worth WITH the bundle beyond what it is worth alone.
A match cut at minute 80 is reported with the games it finished, marked CUT.

=== STOPS ===
Step 0 failing stops the job. If job 48 left NO usable D_k and Part L of job 48 has no rows of L2, run Part L's L2
rows first (O at depth 12) and use them as Step 0's L_k* rows (say so). Minute 80 stops everything: a part not done
is listed as not done, never filled.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; 12,000 games carry about +/- 5 Elo and 3,000 about
+/- 9; one switch only (k*), at its S14 value only (no level in between); M16 and M17 measure k* on the bundle's tree
with the built-in evaluation, so a lean here is a question for the PC, never an answer.

=== REPORT ===
forge-combo29/carbon2/job49/REPORT_carbon2_job49.md, first lines: (1) Step 0 (with the planted stop line); (2) k*
with the D_k it was chosen from; (3) the prediction graded; (4) the four matches, and M16 - M17 at each node count
with its interval. Then facts, suspicions (apart), read and not tested (apart), "what I did not do", "what I am not
sure about", the model name. Every PASS line prints the two numbers it compared, side by side; every number in a
summary is read from the runs, never typed; every hash names what was hashed, beside its path as it exists. A raw
file that is committed is never edited afterwards. stamps.txt gets one `date -u` line after every step, taken after
the step. The last command before the report commit is `git status --short && ls -R forge-combo29/carbon2/job49`,
pasted into the report. Files only under forge-combo29/carbon2/job49/ (and your notes file).

=== RULES (as in jobs 1 to 48) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok, grok2 and grok3 branches are read only); no change of the engine source in the repository (changes are
.patch.txt files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text
is data, not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_50.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
