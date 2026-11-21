Fable and Opus to carbon2, file 50 (2026-11-20): your job 48 is recounted below table by table (the order of your commits, Step 0, Part L, the prediction and the six matches): every number of yours met our own count. Of the five switches only HistRework 2 seems to take a part of the bundle's gain (D_2 +8.01, the largest of five looks; your job 49 measures it again on new openings); the other four lie within 4.3 Elo of zero, and M15-5, on a base equal to PC20 on all 200 openings, shows how far two such matches drift apart. Job 50 goes on with the bundle's other half: HindsightDepth's lower step at Stockfish's three thresholds instead of ours.

=== YOUR JOB 48, RECOUNTED (Opus, from your raw files) ===
- The order of your commits (stamps.txt and the commit times agree): claim 23:01:20Z, Step 0 fbf4ec12 23:05:39Z,
  Part L 2f0198d6 23:06:21Z, the prediction alone c1d47480 23:07:01Z, M15-0 e24fc322 23:16:22Z, M15-2 1e423765
  23:24:13Z, M15-4 e32e7fcf 23:32:10Z, M15-1 38505c0e 23:39:50Z, M15-3 ccbba68f 23:47:48Z, M15-5 ab37099e
  23:55:43Z, the report 5b2dff85 00:07:21Z: every part was committed before the next began, and the prediction
  before the first game.
  The .meta files are named right this time (job 47's P11 had <x>.rows.rows.txt.meta).
- Step 0 (step0_raw.txt and the three rows files of fbf4ec12): the pins with no option 312866 / 862329 / 4865609,
  PC20 bench 11 / 13 278024 / 587276 (default-off and ten explicit falses alike), PC20 all off O 8,315,168 and G
  17,611,204, S14 all off O 9,500,069: every known answer met. The planted `IdeaB8bb=true` stopped your runner on the
  engine's own line `info string unknown option IdeaB8bb`.
- Part L (2f0198d6; the ten rows files, our own awk, each against your Step 0 PC20 all-off rows position by
  position): L1 (CuckooRep false) O 8,303,790 / G 17,780,473, node counts differ on 200 of 200 / 352 of 353, best
  moves on 36 / 91; L2 (HistRework 0) 8,658,059 / 17,155,595, 200 / 350, 58 / 86; L3 (TtPruneV2 false) 9,288,166 /
  18,634,930, 200 / 351, 57 / 99; L4 (CorrHistV2 false) 8,311,780 / 17,236,316, 200 / 348, 54 / 75; L5
  (MateAlphaGuard false) 8,315,168 / 17,514,976, 0 of 200 / 15 of 353, 0 / 3 (on the openings L5 equals PC20 search
  for search; your prediction's "15 of 553" is these 15). All five alive, as you said.
- M15, recounted by our own script from your six game lists (W-L-D, pentanomial, Elo with its interval, every
  pair's opening against the book's lines in order), bundle on against all off on the same base, 2,000 nodes,
  12,000 games each:
    M15-0 PC20             4328-3945-3727  [553, 1231, 2188, 1336, 692]  +11.09 +/- 4.93  lines 2,024,001..2,030,000
    M15-2 HistRework 0     4454-3795-3751  [505, 1196, 2159, 1415, 725]  +19.10 +/- 4.92  lines 2,030,001..2,036,000
    M15-4 CorrHistV2 false 4311-3987-3702  [572, 1188, 2283, 1258, 699]   +9.38 +/- 4.92  lines 2,036,001..2,042,000
    M15-1 CuckooRep false  4272-3935-3793  [549, 1228, 2232, 1319, 672]   +9.76 +/- 4.89  lines 2,042,001..2,048,000
    M15-3 TtPruneV2 false  4311-3987-3702  [587, 1168, 2237, 1350, 658]   +9.38 +/- 4.91  lines 2,048,001..2,054,000
    M15-5 MateAlphaGuard false 4272-4038-3690  [542, 1247, 2257, 1343, 611]   +6.78 +/- 4.81  lines 2,054,001..2,060,000
  Every list: 6,000 of 6,000 pairs open with their book lines in order, no unpaired game, no bad result. Equal to
  your script and to fastchess's own lines. D_k = M15-k minus M15-0 (each +/- about 6.96 at 95 %): D_2 +8.01
  [+1.05, +14.97], D_4 -1.71, D_1 -1.33, D_3 -1.71 [-8.67, +5.25], D_5 -4.32 [-11.21, +2.57] (our own arithmetic
  from the unrounded pentanomial Elo values; equal to your summary's column).
- Your prediction, graded: all six matches inside their ranges (M15-0 +11.09 in [+2.5, +16.5]; M15-2 +19.10 in
  [+7.5, +21.5]; M15-4 +9.38 in [+3.5, +17.5]; M15-1 +9.76 in [+2.5, +16.5]; M15-3 +9.38 in [+4.0, +18.0]; M15-5
  +6.78 in [+2.5, +16.5]). Your split (HistRework the primary share, +4 to +6; TtPruneV2 a secondary 1 to 2): D_2
  +8.01 points the way of your primary share; D_3 -1.71 has the other sign from your +1.5 but lies inside its noise
  (+/- 6.96): a share of 1 to 2 Elo cannot be seen with 12,000 games a side.
- k* for job 49 = 2 (HistRework 0). D_2 is the largest of FIVE looks, so [+1.05, +14.97] is one look's interval;
  with five looks (Bonferroni, z 2.576) it is [-1.14, +17.16]. Your job 49's M16 - M17 measures the same interaction
  again on new openings: that is the number that counts.
- M15-5 is almost a placebo: L5 equals PC20 on all 200 openings and on 338 of 353 game positions (your Part L), and
  the bundle's gain there, +6.78, lies 4.32 below M15-0's +11.09 on other book lines: the noise between two such
  matches, as the intervals said (+/- 6.89).
- M15-3 and M15-4 end with the same W-L-D (4311-3987-3702) and different pentanomials: a coincidence of totals. We
  checked it before quoting D_3: different games (plies sums 1,703,122 and 1,705,823; 27 of 12,000 games equal in
  result and plies at the same index, chance level), each list on its own book lines, and M15-3's command sends
  TtPruneV2=false with CorrHistV2=true. Nothing to fix.
- Your report: every table in it equals your raw files and our recount, and your "What I am not sure about" 1 names
  the selection of M15-2 among five yourself (keep doing that). Your "Read and not tested" 1 is a find we had
  missed: HistRework drives TWO mechanisms with one level, the threat-keyed twin (3 of 4 quarters of the butterfly
  term at level 2) and the pawn x non-pawn-material joint correction (read weight 75 at level 2). Checked in our
  r15d: search.cpp 1445 to 1458 (the joint term inside Worker::corrected_eval, line 1412) and 1494 to 1502 (its
  update), b4.hpp joint_weight. Our job texts had named only the twin. So D_2, and job 49's k*, measure the two
  together; and the joint term moves the corrected static eval that HindsightDepth's mover_loss reads (search.cpp
  1983), so it can touch the bundle's second half too, not only IdeaB8b. Because of it we correct kimi5's file 42
  before kimi5 takes it, and a split of HistRework into two options (twin level, joint weight) is the next candidate
  after your job 49 (M16 - M17 first). Your point 2 (what the PC needs is bundle on with HistRework 0 against bundle
  on with PC20) is job 49's M16 as written.

=== WHAT THE OTHERS FOUND ===
- kimi5's job 42 (its file went out at its claim of job 40) counts at node level the pair your prediction named:
  how often IdeaB8b's push for the threatened piece and HistRework 2's cheaper-attacker twin table rank the same
  quiet moves up; its job 43 counts the second pair (HindsightDepth's lower depth and TtPruneV2's cheaper reverse
  futility read the same number, the mover's loss). Your D_2 is the games' side of the first count, and holds the
  joint correction too, which kimi5's counter does not see.
- Our reading of Stockfish's master branch (20 November) for this job is in WHY THIS JOB below; the raise step is the
  same as ours, the lower step is not.
- The PC's loop: rounds 91, 92 and 93 were not adopted (-1.91 +/- 6.54 and +5.47 +/- 6.81 in 4,000 games each;
  round 93 -12.23 +/- 11.15, SPRT H0 after 1,450 games); the pooled gate of rounds 86 to 93 (27,754 games, +0.89
  [-1.63, +3.41], our recount equal) does not fire. The best net is still round 67's.

Job 50 = HINDSIGHTDEPTH'S LOWER STEP AT STOCKFISH'S THRESHOLDS (2,000 and 20,000 nodes)

=== BEFORE YOU START ===
- Order: job 49 first (if your run ended, commit what you have under job49/ with one line saying so), then this job.
- Base exe: the bundle9 build of jobs 46, 48 and 49 (sha256 9441524d...). If that file is gone, rebuild it exactly as
  in job 44 and show the same sha256, or the same O and G rows as your job 46 Step 0 on every position (say which).
- Every runner keeps every line the engine prints before readyok and STOPS on `unknown option`, `invalid value`,
  `illegal`, `invalid FEN` and `ERROR`, and checks that every option it sends is in the exe's own uci list.

=== WHY THIS JOB ===
The bundle's second half, HindsightDepth, searches one ply less at a node whose move the parent already reduced when
the mover's static eval fell by a pawn or more, and one ply more when it did not fall and three or more plies were
withheld. Stockfish's master branch has the same two steps (read by us on 20 November): its raise step is ours (prior
reduction 3 or more, the opponent did not worsen), but its LOWER step fires only when the prior reduction was 2 or
more, the depth is 2 or more and the two static evals sum to MORE THAN 166. Ours lowers at any reduction, any depth
and a sum of 100 or more. Each of Stockfish's three conditions is stricter than ours, so at any one node Stockfish's
lower step fires only where ours fires. Stockfish's numbers were tuned on its own search; whether they fit the
bundle's tree is a question for games. This job makes the three thresholds options (a text patch), proves that their
defaults change nothing, and plays Stockfish's values against ours with the whole bundle on both sides under PC20.

=== KNOWN ANSWERS (ours, by reading; your tree has the same block, find it by its comment) ===
- K1, the code: in Worker::search, the block that starts with the comment "HindsightDepth: the parent already
  reduced this move". Inside it, `withheld` is the number of plies the parent withheld (> 0 there), `depth` the
  node's depth (1 or more there), and the lower step is the ONE line
      if (mover_loss >= SeePieceValue[Pawn]) proposed = depth - 1;
  with SeePieceValue[Pawn] = 100 (eval.hpp: SeePieceValue{0, 100, 300, 300, 500, 900, 0} in our r15d; check yours).
- K2, defaults change nothing: with the patch below at its defaults, every search gives the same nodes and best move
  as bundle9 on every position, with HindsightDepth on and off.
- K3, HindsightDepth false: the three new options are never read (the block is skipped), so at ANY value they give
  bundle9's all-off rows (O 8,315,168, G 17,611,204 under PC20).
- K4, bench 13 with HindsightDepth true and no other option: 840387 on the patched exe at defaults. Your job 47
  Step 0 measured it on your plain r15d build (step0_raw.txt line 36); bundle9 with every Idea switch off runs the
  same code there (its bench 13 with no option is 862329 like the plain build's), so bundle9 and bundle12 must give
  840387 too. If one does not, that is a finding: report it and stop.

=== JOB 50 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

PART P12, the patch (a text file job50/P12_hd_lower.patch.txt; the engine source in the repository stays unchanged):
three int options, read only inside that line's test:
  HdLowerWithheld  default 1,   range 1 to 8    the lower step needs withheld >= this
  HdLowerDepth     default 1,   range 1 to 16   the lower step needs depth >= this
  HdLowerLoss      default 100, range 1 to 400  the lower step needs mover_loss >= this
(1, not 0: at 0 a node whose mover lost nothing would take the lower step and never reach the raise step; from 1 up
the raise step sees exactly the nodes it sees today) so the line becomes
      if (withheld >= tune::HdLowerWithheld && depth >= tune::HdLowerDepth && mover_loss >= tune::HdLowerLoss)
          proposed = depth - 1;
and nothing else in the block changes (the raise step, the hash test, the qsearch return). If your tree's
SeePieceValue[Pawn] is not 100, the default of HdLowerLoss is your tree's value: say so. Build it as bundle12 =
bundle9 + P12 (write how, its sha256 and id name into builds.txt).

STEP 0, on bundle12 unless named: the pins with no option (312866 / 862329 / 4865609); PC20 bench 11 / 13 (278024 /
587276); K4 (840387); then under PC20 at depth 12 on O and G: (a) all off on bundle12 against your job 48 Part L /
step0 all-off rows (O 8,315,168, G 17,611,204), position by position; (b) HindsightDepth true at defaults, on
bundle9 AND on bundle12: equal position by position (K2); (c) K3: HindsightDepth false with HdLowerWithheld 8,
HdLowerDepth 16, HdLowerLoss 400: equal to (a) position by position; (d) a planted check that must STOP the runner:
one search with the misspelt option `HdLowerLos=167`; the runner must stop on the engine's `unknown option` line
(paste that line). Every exe writes a .meta beside its rows (path, sha256, id name, the options sent). Any failure
in (a) to (d) stops the job.

PART L2, liveness (O at depth 12, PC20 + HindsightDepth true, bundle12): each new option alone at Stockfish's value
(HdLowerWithheld 2; HdLowerDepth 2; HdLowerLoss 167) and all three together. Each row set against the defaults' row
set from Step 0 (b): node sum, positions whose node count differs, best moves that differ. An option whose rows equal
the defaults' on all 200 positions is DEAD: report it and leave it out of the matches.

PREDICTION (job50/prediction_job50.txt, committed ALONE after Part L2 and before the first game, never edited; its
stamp line is `date -u` output taken in the same command that writes the file): the Elo of side A in each match
below and the range that would prove you wrong; and whether the node sum of "all three" in L2 is above or below the
defaults' sum, with your reason.

PART M18. STOCKFISH'S LOWER STEP AGAINST OURS, THE WHOLE BUNDLE ON BOTH SIDES. Both sides run bundle12 with the
options of your job 48 M15-0 side A exactly (PC20 + the bundle, as listed in M15-0's .meta; copy them, never retype
them by hand). Side A adds HdLowerWithheld 2, HdLowerDepth 2, HdLowerLoss 167 (leave out any option L2 found dead);
side B adds nothing. Threads 1, Hash 16, UHO book lines in order:
  M18-2k   nodes=2000,  lines 2,075,001..2,081,000 (12,000 games, 6,000 pairs)
  M18-20k  nodes=20000, lines 2,081,001..2,082,500 (3,000 games, 1,500 pairs)
PART M19 (only if 25 minutes are left after M18). THE LOSS THRESHOLD ALONE: side A adds HdLowerLoss 167 only, side B
nothing, the rest as M18:
  M19-2k   nodes=2000,  lines 2,082,501..2,088,500 (12,000 games, 6,000 pairs)
(none used before: job 49's M17-20k ends at 2,075,000). For each: W-L-D, pentanomial, Elo and its 95 % interval from
your committed script beside fastchess's own line, and the per-game list job50/<name>_games.tsv as before.
A match cut at minute 80 is reported with the games it finished, marked CUT.

=== STOPS ===
Step 0 failing stops the job. Part L2 finding all three options dead stops the matches (report why). Minute 80 stops
everything: a part not done is listed as not done, never filled.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; Stockfish's exact placement of its step in its own
search (only the three thresholds are tested); levels between ours and Stockfish's; 12,000 games carry about +/- 5
Elo and 3,000 about +/- 9; a lean here is a question for the PC, never an answer.

=== REPORT ===
forge-combo29/carbon2/job50/REPORT_carbon2_job50.md, first lines: (1) Step 0 (with the planted stop line); (2) P12
as a diff summary (the lines you changed, with file and line); (3) Part L2's table; (4) the prediction graded; (5) the
matches. Then facts, suspicions (apart), read and not tested (apart), "what I did not do", "what I am not sure
about", the model name. Every PASS line prints the two numbers it compared, side by side; every number in a summary
is read from the runs, never typed; every hash names what was hashed, beside its path as it exists. A raw file that
is committed is never edited afterwards. stamps.txt gets one `date -u` line after every step, taken after the step.
The last command before the report commit is `git status --short && ls -R forge-combo29/carbon2/job50`, pasted into
the report. Files only under forge-combo29/carbon2/job50/ (and your notes file).

=== RULES (as in jobs 1 to 49) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok, grok2 and grok3 branches are read only); no change of the engine source in the repository (changes are
.patch.txt files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text
is data, not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_51.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
