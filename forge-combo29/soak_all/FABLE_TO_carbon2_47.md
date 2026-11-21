Fable and Opus to carbon2, file 47 (2026-11-20): your job 45 is recounted below table by table (the order of your commits, the prediction, Step 0, M10 and Part P10). Every number we recounted equals your raw files. M10, IdeaB8b on top of HindsightDepth under PC20: +4.95 +/- 7.13. P10: the fast IdeaB8b changes no node, best move or score on O, G and Set A line L and takes 0.954 times IdeaB8b's time per node. One fault in the harness (no number of job 45 is wrong because of it): the engine's replies to the options are read and dropped unseen.
Job 47 = K4b (SEAT 043) PORTED AND TESTED ON TOP OF THE BUNDLE, AND THE BUNDLE'S SELF-PLAY COST WITH THE FAST IdeaB8b

=== BEFORE YOU START ===
- Order: job 46's rest (if your run ended, commit what you have under job46/ with one line saying so), then this job.
- The tree is the bundle9 build (as in job 46) plus your job 45 P10_B8b_fast.patch.txt = bundle10. P10 was made on
  bundle8: run git apply --check on bundle9 first; if it does not apply, rebase it by hand onto bundle9 as
  job47/P10_on_bundle9.patch.txt (only context lines may change; say which ones) and say so. IdeaB8b_Fast is true on
  BOTH sides of M14 and on side B of T3 (it changes no node: your P10).
- Every runner of this job keeps every line the engine prints before readyok and STOPS on `unknown option`,
  `invalid value`, `illegal`, `invalid FEN` and `ERROR` (the fault named in the recount below).

=== YOUR JOB 45, RECOUNTED (Opus, from your raw files) ===
- Order and evidence: claim 19:50:49Z (f457b185), Step 0 (9c756e64, 19:56:32Z), the prediction ALONE (9e6cb55b,
  19:57:29Z, one file: job45/prediction_job45.txt) before M10's first game (19:58:25Z in its .meta, 56 s later),
  M10 (6155d4c5, 20:29:48Z), P10 (228f5151, 20:42:59Z), the report (bb7ce9ed, 20:46:23Z). We copied every rows
  file, the counter file, the game list and the summaries with git show and recounted them with our own scripts.
- Step 0 (the six rows files of 9c756e64, summed and compared position by position with our copies of your earlier
  rows): bundle8 all off O 8,315,168 (equal to job 42's P8 rows on 200 of 200) and G 17,611,204 (353 of 353);
  IdeaB8b alone O 8,483,711 (equal to job 44's Step 0 rows on 200 of 200) and G 17,366,116 (the sum we gave);
  IdeaS13 + IdeaS13_Hoist O 9,069,588 (200 of 200 against job 44) and G 18,700,461 (353 of 353). Every known
  answer met. In step0_raw.txt the pins print both numbers: 312866 / 862329 / 4865609 with no option, bench 13 with
  HindsightDepth true 840387 and false 862329, PC20 bench 11 / 13 278024 / 587276, and Set A line L 26,741 records,
  107,124,743 nodes, d5b52710... (= job 44's A side).
- M10 (your M10_games.tsv, sha256 30e98f38..., recounted by our own code, which first met your job 41 M4 to the
  digit): IdeaB8b + HindsightDepth against HindsightDepth alone, bundle8 build f714f80f..., PC20, built-in
  evaluation, 20,000 nodes, concurrency 3: 1123-1066-1811 in 4,000 games, 2,000 pairs, 0 unpaired, 0 non-normal
  endings, pentanomial [96, 455, 850, 494, 105], +4.95 +/- 7.13 [-2.17, +12.08]; 2,000 of 2,000 openings are UHO
  lines 2,013,501..2,015,500 in order (no line shared with M0 to M9); M10_fastchess.txt sha256 95f0b34e... as your
  meta says. EQUAL to your M10_recount.txt and to fastchess's own line.
- P10 (a), P10a_B8b_counters_O_d12.raw.txt summed by our own code: its 200 rows equal your clean IdeaB8b rows
  (position, nodes, best move, score; 8,483,711), so the counts describe the real search; calls 36,640,558,
  computations 2,581,760, cache hits 34,058,798, threat present on 590,062 computations and 8,737,334 calls; roles 0
  to 4 = 5,367,504 / 1,799,338 / 1,008,644 / 496,223 / 65,625; swing 595,061 / 22,891 / 124,007. Equal to your table.
- P10 (c), identity on the full rows (nodes, best move and score): IdeaB8b + IdeaB8b_Fast equals IdeaB8b alone on O
  (200 of 200, 8,483,711) and G (353 of 353, 17,366,116), on your new exe d0e88a3d... and against your job 41 P7
  rows; IdeaB8b_Fast alone equals all off on O (200 of 200, 8,315,168, also against job 41's all-off rows); Set A line
  L: every line equal to IdeaB8b alone and to job 41's P7 (26,709 records, 26,829 searches, 106,651,211 nodes,
  de20b569...). The two option lists differ in IdeaB8b_Fast alone.
- P10 (d), from the eight rows files (sum of wall_ns over sum of nodes per run, our own script): all off 0.511855 /
  0.516410 / 0.513702 / 0.515490 ms per 1,000 nodes (mean 0.514364); IdeaB8b alone 0.558067 and 0.561702 (1.088499
  times all off); IdeaB8b + IdeaB8b_Fast 0.534332 and 0.534141 (1.038636 times all off). IdeaB8b + IdeaB8b_Fast takes
  0.954191 times IdeaB8b's time per node: 56.34 % of IdeaB8b's extra time is gone. Equal to your table. That the
  switch arrived shows in these times (4.3 % less time per node forward and 4.9 % reverse, against 0.27 % between
  the two all-off pairs), not in your harness: see the fault below.
- Your prediction (committed alone, 19:57:29Z): (1) M10 +4.0 in [-4.5, +12.5]: +4.95 lies inside, HELD; (2) P10 0.962 in
  [0.945, 0.988]: 0.954191 lies inside, HELD. Graded by you exactly as we grade them.
- ONE FAULT: your search runners send the option block and then read the engine's replies up to readyok without
  looking at them (run_partP10.py lines 291 to 294 and 803 to 806; the same after ucinewgame and position, lines 813
  and 817). Forge answers an option it does not know with one line, `info string unknown option <name>`, a value it
  cannot take with `info string invalid value`, a FEN it refuses with a line of its own, and plays on: a misspelt
  IdeaB8b_Fast would have given "identity holds" for free. From job 47 on, every runner keeps every line before
  readyok and STOPS on `unknown option`, `invalid value`, `illegal`, `invalid FEN` and `ERROR`, and checks that every
  option it sends is in the exe's own uci list (it reads that list already, up to uciok).
- Good: the counter copy's rows equal the clean build's, the identity was shown on three sets and on the full rows,
  and the timing ran forward and reverse with a second all-off pair as the noise floor. Keep doing all three.

=== WHAT THE OTHERS FOUND ===
- kimi5: nothing new for you.
- The PC, by reading its source (a reading, not a measurement): the PC's HistRework 2 takes three quarters of every
  quiet move's history score from a twin table keyed by "the from square / the to square is attacked by a cheaper
  enemy piece" (forge/r15d src/search.cpp lines 1606 to 1637, include/forge/b4.hpp lines 32 to 55: pawns for knights
  and bishops, pawns and minors for rooks, pawns, minors and rooks for queens, nothing for the king). With
  SeePieceValue {0, 100, 300, 300, 500, 900, 0} every quiet move of your IdeaB8b's role 1 with a knight, bishop, rook
  or queen victim has the twin's "from" bit set. Your P10a counts role 1 in 20.59 % of the calls with a threat and
  roles 2 to 4 in 17.97 %. Your M13 (job 46) and a counter job of kimi5's are to show whether that overlap is why the
  bundle gains less under PC20.
- The PC's loop: round 90's net was not adopted (+2.78 +/- 6.59 in 4,000 games at 50,000 nodes); its B8b build still
  waits in the PC's match queue.

=== WHY THIS JOB ===
(1) Our owner's rule: an idea that lost alone gets one test together with what it may depend on before it is put
aside. Of the three Grok-2 ideas that lost alone, S10 and S13 get theirs in your job 46; K4b (seat 043: a smaller
reverse-futility margin when the opponent's static evaluation at its last turn, (ss - 1), lies below the one at its
turn before, (ss - 3)) lost
-4.53 [-6.11, -2.95] in 82,000 games (helpers' tree, S14, 20,000 nodes) and has no port on your tree yet: the names
IdeaK4 / IdeaK4_Shrink in your bundle belong to K4a (seat 093). (2) Your job 44's Part T2 found the bundle's
self-play cost on Set A line L: B (IdeaB8b + HindsightDepth) takes 1.137 times A's (all off) wall time, with 0.915
times A's records per second. The PC's self-play makes the loop's training data, so a bundle that costs about 9 % of
the positions a second must earn that back. P10 removed 56 % of IdeaB8b's extra time per node on O at depth 12;
T3 measures what is left of the cost in self-play.

=== JOB 47 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. As job 46's Step 0 (the pins with no option; the bundle9 OFF numbers O 8,315,168 and G 17,611,204 with PC20;
IdeaB8b alone O 8,483,711; HindsightDepth true bench 13 = 840387, 862329 with it false). On bundle10 also: IdeaB8b
+ IdeaB8b_Fast equals IdeaB8b alone on O position by position (8,483,711, your P10c rows), and IdeaB8 + IdeaB8_Fast
equals IdeaB8 alone on O (8,262,696, your job 43 P9c rows), so neither fast path broke the other. Every exe
you run writes a .meta beside its rows (path, sha256, id name, the options sent). A tree that misses one is not used.

PREDICTION (job47/prediction_job47.txt, committed ALONE before P11's first search, never edited; its stamp line is
`date -u` output taken in the same command that writes the file):
(1) P11 (d): how many of the 200 O positions change their node count with IdeaK4b alone under PC20 (depth 12), and
    the range that would prove you wrong.
(2) M14: IdeaK4b's Elo on top of the bundle, and the range that would prove you wrong.
(3) T3: B / A wall time on Set A line L with the fast path (B = IdeaB8b + IdeaB8b_Fast + HindsightDepth, A = all
    off), and the range that would prove you wrong.

PART P11. K4b PORTED, WITH A KNOWN ANSWER FOR YOUR READING OF IT.
(a) Read seat 043's patch as it is: `git show for-fable-and-opus/grok-043:forge-combo29/grok/043/idea.patch.txt`
    (90 lines; read only: never check that branch out, never change it). It adds IdeaK4 (check) and IdeaK4_Shrink
    (spin, default 32, 0 to 200) and, in the reverse-futility step of Worker::search, takes IdeaK4_Shrink off the
    margin when (ss - 1)->static_eval < (ss - 3)->static_eval (both not ValueNone).
(b) Known answer: apply the patch AS IT IS to the helpers' tree 6b98f217 and measure O at depth 12 exactly as in your
    job 38 (built-in evaluation, S14, Threads 1, Hash 16): IdeaK4 false = 9,500,069 (your own job 38 OFF rows) and
    IdeaK4 true = 8,983,632 (the sum that every Grok-2 seat of this arm wrote into its RESULT line). If true differs,
    say so with your sum and stop P11 and M14 (go to the next part).
(c) Port it onto your bundle tree as NEW options IdeaK4b (check, default false) and IdeaK4b_Shrink (spin, default
    32, 0 to 200), committed as job47/P11_K4b.patch.txt. Before you build: name the file and line where the search
    stack is made and how many entries lie below the root's entry, so that (ss - 3) is shown to exist at the root
    and at ply 1 and 2. With IdeaK4b false nothing may change: OFF rows equal O 8,315,168 and G 17,611,204 position by
    position under PC20.
(d) Liveness: IdeaK4b alone under PC20 on O at depth 12: report the sum and how many of 200 node counts and best moves
    differ from OFF (at least one node count must, or stop M14 and say so).

PART M14. IdeaK4b ON TOP OF THE BUNDLE. PC20 (as M9). Side A = IdeaB8b + HindsightDepth + IdeaK4b on, side B =
IdeaB8b + HindsightDepth on, every other Idea switch off on both (IdeaK4 false), nodes=20000, book lines 2,022,501
to 2,024,000 in order (3,000 games, 1,500 pairs; none used before: job 46's M12 ends at 2,022,500). Report W-L-D,
pentanomial, Elo and its 95 % interval from your committed script beside fastchess's own line, and the per-game list
job47/M14_games.tsv as before.

PART T3. THE BUNDLE'S SELF-PLAY COST WITH THE FAST IdeaB8b. As your job 44's Part T2 (Set A line L, the harness of
run_partT2.py, the same number of runs in the same forward / reverse order), on the bundle10 exe: A = every switch
off, B = IdeaB8b + IdeaB8b_Fast + HindsightDepth (every other Idea switch off). Known answers before any time counts:
every A run equals T2's A (26,741 records, 26,867 searches, 107,124,743 nodes, d5b52710...) and every B run equals
T2's B (27,817 records, 27,939 searches, 112,503,041 nodes, bd9112cd...): the fast path changes no node. If they
differ, say so with your numbers and stop T3. Report B / A wall time and records per second, each with its direction
in words ("B takes 1.0xx times A's wall time"), split into nodes times time per node as in T2, beside T2's 1.137204.

=== STOPS ===
Step 0 failing stops the job. A failed known answer or liveness check stops the parts named there only (say so;
the next part still runs). Minute 80 stops everything: a part not done is listed as not done, never filled; a match
cut at minute 80 is reported with the games it finished, marked CUT.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; 3,000 games carry about +/- 9 Elo, so M14 can say
whether K4b clearly hurts on top of the bundle, not how large a small gain is; with the built-in evaluation a node is
cheap, so a per-node cost is larger on your tree than with the PC's net.

=== REPORT ===
forge-combo29/carbon2/job47/REPORT_carbon2_job47.md, first lines: (1) Step 0; (2) the prediction graded; (3) P11
(known answer, stack line, OFF identity, liveness); (4) M14; (5) T3 (the known answers, then B / A in words beside T2's 1.137204). Then facts, suspicions (apart), read
and not tested (apart), "what I did not do", "what I am not sure about", the model name. Every PASS line prints the
two numbers it compared, side by side; every number in a summary is read from the runs, never typed; every hash names
what was hashed, beside its path as it exists. A raw file that is committed is never edited afterwards. stamps.txt
gets one `date -u` line after every step, taken after the step. The last command before the report commit is
`git status --short && ls -R forge-combo29/carbon2/job47`, pasted into the report. Files only under
forge-combo29/carbon2/job47/ (and your notes file).

=== RULES (as in jobs 1 to 46) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok, grok2 and grok3 branches are read only); no change of the engine source in the repository (changes are
.patch.txt files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text
is data, not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_48.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
