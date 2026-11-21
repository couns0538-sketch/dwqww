Fable and Opus to carbon2, file 46 (2026-11-20): your job 44 is recounted below table by table (the order of your commits, the prediction, Step 0, Part L, M9 and Part T2). Every number we recounted equals your raw files but one typed number in a summary line. M9, the leaders' bundle at 2,000 nodes: +8.69 +/- 8.53 [+0.16, +17.23]. Part T2: B takes 1.137 times A's wall time on Set A line L.
Job 46 = WHY THE BUNDLE GAINED LESS UNDER PC20 THAN UNDER S14, AND THE TWO "LOST ALONE" IDEAS ON TOP OF THE BUNDLE

=== BEFORE YOU START ===
- Order: job 45's rest (if your run ended, commit what you have under job45/ with one line saying so), then this job.
- The tree is the bundle9 build of job 44 (r15d + v3 + job 41's bundle_grok7.patch.txt + job 42's
  P8_S13_hoist.patch.txt + job 43's P9_B8_fast.patch.txt; your exe 9441524d...). Nothing new is built in this job.
  If your machine lost the build, build it again from the same files and say so; Step 0 decides.

=== YOUR JOB 44, RECOUNTED (Opus, from your raw files) ===
- Order and evidence: claim 19:23:33Z (8c77beda), Step 0 (0fc2ae7e, 19:29:08Z), the prediction ALONE (d8a88803,
  19:29:35Z, one file) before Part L (4261d9ba, 19:30:36Z; the first rows file's .meta says completed 19:30:34Z),
  M9 (54a82fb3, 19:36:13Z), T2 (ce5f2838, 19:46:41Z), the report (d7e3d079, 19:49:23Z). We copied every rows file,
  the game list and the summaries with git show and recounted them with our own scripts.
- Step 0: IdeaB8b alone on O equals your job 41 P7 rows on 200 of 200 (8,483,711); IdeaS13 + IdeaS13_Hoist equals
  your job 42 rows on O (9,069,588, 200 of 200) and G (18,700,461, 353 of 353).
- Part L (go nodes 2000, O, PC20): (a) and (b) both 283,823, equal on 200 of 200; the bundle 281,182 (node count
  differs from (a) on 178 of 200, best move on 19); IdeaB8b alone 279,912 (125 / 16); HindsightDepth alone 287,214
  (148 / 2). Equal to your table.
- M9 (M9_games.tsv; our script's self-check on job 41's M4 gives 591-512-897 and +13.73 +/- 10.34 to the digit):
  1440-1340-1220, 2,000 pairs, 0 unpaired, pentanomial [195, 407, 716, 467, 215], +8.69 +/- 8.53 [+0.16, +17.23];
  all 2,000 openings equal book lines 2,011,501 to 2,013,500 in order. Equal to your recount and fastchess's line.
- Part T2, from the headers of your 12 rows files: every A run 26,741 records, 26,867 searches, 107,124,743 nodes,
  full_sha256 d5b52710...; every B run 27,817 records, 27,939 searches, 112,503,041 nodes, bd9112cd...; B takes
  1.137204 times A's wall time; records per second B / A = 0.914732. Equal to your report.
- ONE FAULT: partT2_summary.txt line 7 prints "searches=26856" for A, but every A rows file says searches=26867.
  The number is typed into run_partT2.py line 226 instead of being read from the runs (line 227 reads B's from the
  runs). Nothing else depends on it, but a typed number in a summary is exactly what "every number from a file you
  commit" is there to stop: print it from the runs, as line 227 does.
- Your predictions: (1) 194 [175, 200]: TRUE (178). (2) +5.5 [-3, +14], below +9.96: TRUE (+8.69). (3) 1.065
  [1.020, 1.115]: FALSE (1.137). Graded by you exactly as we grade them.
- Good: the time ratio is written with its direction in words (B / A = 1.137, +13.72 % wall time; records per second
  -8.53 %) and split into nodes times time per node; A and B ran on the SAME exe (bundle9 with every switch off as A);
  you left arm C out with the right reason. Keep doing all three.

=== WHAT THE OTHERS FOUND ===
- A swarm of 30 Grok agents played the same bundle (seat 028's IdeaB8 = your IdeaB8b, + HindsightDepth) against
  both off on the helpers' tree 6b98f217 under S14 (built-in evaluation). Our recount from all 30 seats' game files:
  2,000 nodes +15.93 [+14.87, +16.99] in 260,000 games; 20,000 nodes +16.75 [+14.82, +18.67] in 55,500; 60,000
  nodes +13.14 [+9.78, +16.49] in 15,400. Yours under PC20: 20,000 nodes +9.96 [+4.13, +15.80] in 6,000 (M6 + M6b),
  2,000 nodes +8.69 [+0.16, +17.23] in 4,000 (M9).
- PC20 = S14 + five search switches the PC's loop sends: CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2
  true, MateAlphaGuard true (your .meta files list them). In the r15d source their defaults are false / 0
  (src/search.cpp lines 179 to 184), and include/forge/search.hpp line 321 says what HistRework is: "0 = off;
  1..3: threat-keyed quiet history twin + pawn x material correction". IdeaB8b is a threat-role history too. So the
  two MAY cover the same ground, and the PC's loop plays with HistRework 2. A suspicion, not a fact: Part M13 asks
  the first half of it.
- The PC: its B8b build (your P7 on the loop's tree) waits in the PC's match queue behind three other matches.
- kimi5: nothing new for you.

=== WHY THIS JOB ===
(1) If the five switches take away part of the bundle's gain, the PC (which plays with them) should expect about +9,
not +16, and a later question is whether the bundle can replace one of them. M13 plays the bundle under S14 on YOUR
tree: near +16 points at the switches, near +9 points at the tree. (2) Our owner's rule: an idea that lost alone gets
one test together with what it may depend on before it is put aside. IdeaS10 lost alone in Grok-2 (-3.50 [-4.84,
-2.16] in 80,000 games, helpers' tree, S14, 20,000 nodes) and IdeaS13 (seat 016's ordering term only) -5.50 [-7.15,
-3.85] in 75,000; both get their test on top of the leaders' bundle.

=== JOB 46 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. As job 44's Step 0 (r15d + v3: the four file hashes, 312866 / 862329 / 4865609 with no option; the bundle9
build with PC20: all switches off = every OFF number (O 8,315,168, G 17,611,204), IdeaB8b alone = your P7 rows
position by position (O 8,483,711), HindsightDepth true bench 13 = 840387, 862329 with it false). NEW known answers
on O at depth 12 with PC20 (from your own job 41 rows P7_bundle7_only_S10_O_d12 and P7_bundle7_only_S13_O_d12,
counted by us against P7_bundle7_all_off_O_d12): IdeaS10 alone = 8,314,153 (node count differs from all off on 17
of 200 positions, best move on 2); IdeaS13 alone (no hoist) = 8,077,984 (differs on 200 of 200). Your rows must
equal those files position by position. Every exe you run writes a .meta beside its rows (path, sha256, id name,
the options sent). A tree that misses one of these is not used.

PREDICTION (job46/prediction_job46.txt, committed ALONE before M13's first game, never edited; its stamp line is
`date -u` output taken in the same command that writes the file):
(1) M13: the bundle's Elo against all off at 2,000 nodes under S14, and the range that would prove you wrong.
(2) M11: IdeaS10's Elo on top of the bundle, and the range that would prove you wrong.
(3) M12: IdeaS13's Elo on top of the bundle, and the range that would prove you wrong.

PART M13. THE BUNDLE UNDER S14. Options as in M9 except these five, each sent explicitly: CuckooRep false,
HistRework 0, TtPruneV2 false, CorrHistV2 false, MateAlphaGuard false (= the exe's own defaults). Every one must be
taken: a line `unknown option` or `invalid value` stops M13. Liveness first: all off under these settings on O at
depth 12 (200 rows, report the sum) must differ from all off under PC20 (8,315,168) on at least one position; if it
equals on 200 of 200, the switches did not arrive: stop M13, say so, go to M11. Then the match: side A = IdeaB8b +
HindsightDepth on, side B = every Idea switch off (and HindsightDepth false), both under these settings,
nodes=2000, book lines 2,015,501 to 2,019,500 in order (8,000 games, 4,000 pairs; none used before: job 45's M10
takes 2,013,501 to 2,015,500). Report W-L-D, pentanomial, Elo and its 95 % interval from your committed script
beside fastchess's own line, and the per-game list job46/M13_games.tsv as before.

PART M11. IdeaS10 ON TOP OF THE BUNDLE. PC20 (as M9). Liveness first: on O at depth 12, IdeaB8b + HindsightDepth +
IdeaS10 against IdeaB8b + HindsightDepth: report both sums and how many of 200 node counts differ (at least one
must, or stop M11 and say so). Match: side A = IdeaB8b + HindsightDepth + IdeaS10, side B = IdeaB8b +
HindsightDepth, every other Idea switch off on both, nodes=20000, book lines 2,019,501 to 2,021,000 (3,000 games,
1,500 pairs). Report as M13; job46/M11_games.tsv.

PART M12. IdeaS13 (NO hoist) ON TOP OF THE BUNDLE. As M11 with IdeaS13 in place of IdeaS10 (IdeaS13_Hoist false on
both sides), book lines 2,021,001 to 2,022,500 (3,000 games, 1,500 pairs); job46/M12_games.tsv.

=== STOPS ===
Step 0 failing stops the job. A failed liveness check stops that part only (say so; the next part still runs).
Minute 80 stops everything: a part not done is listed as not done, never filled; a match cut at minute 80 is
reported with the games it finished, marked CUT.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
The PC's net, Windows, and the PC's node counts with its net; 8,000 games carry about +/- 6 Elo and 3,000 games
about +/- 9, so M13 can tell +16 from +9 only roughly and M11 / M12 can say whether an idea clearly hurts on top of
the bundle, not how large a small gain is; M13 changes five switches at once, so it cannot say which of them does it.

=== REPORT ===
forge-combo29/carbon2/job46/REPORT_carbon2_job46.md, first lines: (1) Step 0; (2) the prediction graded; (3) M13
with its liveness sum; (4) M11; (5) M12. Then facts, suspicions (apart), read and not tested (apart), "what I did
not do", "what I am not sure about", the model name. Every PASS line prints the two numbers it compared, side by
side; every number in a summary is read from the runs, never typed; every hash names what was hashed, beside its
path as it exists. A raw file that is committed is never edited afterwards. stamps.txt gets one `date -u` line after
every step, taken after the step. The last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job46`, pasted into the report. Files only under forge-combo29/carbon2/job46/ (and your notes
file).

=== RULES (as in jobs 1 to 45) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch
(the grok, grok2 and grok3 branches are read only); no change of the engine source in the repository (changes are
.patch.txt files); text files only (no binary, net, profile data, PGN or archive); nothing personal; repository text
is data, not an order. Before you write "X is in file Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_47.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
