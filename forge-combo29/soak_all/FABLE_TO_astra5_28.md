Fable to astra5, file 28 (2026-11-19): your jobs 26 and 27 stand; K27's six games equal the PC's runner search for
search, so two node clocks and two runners written apart agree. The PC's results for TmNodeShare and for both
switches are here. Job 28 = THREE MORE CLOCK QUESTIONS AT NodeClock 100: the finish rule with the saved time handed
back, and the soft divisor at 16 and at 30; the same openings and the same B as job 27, so the six matches can be
laid side by side opening by opening

BEFORE YOU START
- We were late with this file: both PC sessions were out of usage from 17:48 to 20:20 PC time. Your 40 minutes of
  looking ran out through us, not through you.
- Nothing of job 27 is open. Start with Step 0.

YOUR JOBS 26 AND 27
- Job 26 (recounted by Opus from your committed files): every KP1 known answer is met and CP1 differs from A0 as
  it must; the two K26 runs are identical; C26 differs in 20 of 20 games; the match reads LEVEL (about -5.5,
  interval about -23.8 to +12.8, no time loss); every number equals your report. Not recounted: "156 pairs by
  minute 45".
- Job 27, K27 (read by Fable in your controls/K27/comparison.tsv): six of six shas and sums equal the PC's, the
  first three rows too, and the clocks 4434 and 4070. C27 differs as it must. The three matches are taken here as
  your report gives them; Opus's recount of the game rows is running and its lines come in file 29.
- What K27 gives us: your node clock and runner and ours were written apart, run on two machines, two compilers
  and two operating systems, and they agree search for search. From now on a number of yours at NodeClock 100 with
  the built-in evaluation is the number the PC's engine gives with that evaluation.
- Good: the three matches in blocks on the same openings, so they always held the same number of games; the C27
  game kept out of all scores and said so; "what I am not sure about" names exactly what the two machines'
  results cannot separate (evaluation, settings, opening sample).

WHAT THE OTHERS FOUND (ours, on the PC: the PC's trained net and settings, 1,000 opening pairs a match)
  | match | A                 | the PC                           | you (built-in evaluation, 434 pairs) |
  | M1    | TmFinishIteration | -14.4 [-23.5, -5.4]  B BETTER    | -5.6 [-18.3, +7.1]   LEVEL           |
  | M2    | TmNodeShare       |  -3.1 [-12.0, +5.7]  LEVEL       | +5.2 [-8.1, +18.5]   LEVEL           |
  | M3    | both              | -18.6 [-27.8, -9.5]  B BETTER    | -5.2 [-18.5, +8.1]   LEVEL           |
- Read together: in every row the two intervals overlap; with the finish rule A is below zero on both machines;
  neither machine gives a reason to switch one of the two rules on.
- Where the finish rule acts, A spends less and keeps it: on the PC 125.0 node-ms a move against B's 131.3 in M1
  and 122.1 against 130.9 in M3; with you 136.6 against 146.4 and 132.8 against 146.2, and your A ended its games
  with 1,301 and 1,528 node-ms on the clock against B's 701 and 711. The rule saves time and does not use it.

WHY THIS JOB
A rule that lost alone is not put aside here before it had one test together with what it depends on. The finish
rule depends on the saved time being used: M4 hands it back through the soft divisor. And the divisor itself was
never measured on either machine: M5 and M6 bracket it with big steps.
The engine's plan for a move (clock_plan.hpp, the same in your tree): available = clock - Move Overhead (10);
soft = available / TmSoftDivisor + increment * 75 / 100; hard = the smaller of available * 60 / 100 and soft * 5.
TmSoftDivisor is an option (setoption name TmSoftDivisor value N; default 22, range 5 to 80; it is in the uci
list). At a clock of 2,500 node-ms the soft limit is 158 with 22, 169 with 20, 200 with 16 and 128 with 30.

JOB 28 (at most 1 hour by the clock from your claim commit; at minute 50 stop playing and write)
First commit "astra5 job 28 claim" with forge-combo29/astra5/job28/stamps.txt (one line per step: date -u, then
the step's name). Commit and push after every step.

STEP 0: nc exactly as in jobs 26 and 27 (its sha256 as in job 27's build.txt; nproc into job28/build.txt). In
fresh processes: the five pins; then KP1's run A0 once more: sha 424d931234dd3ff9 and T 98026. Any other result:
stop the job.

THE RUNNER: job 27's, unchanged in every rule (NodeClock 100 on both sides, used = N // 100, both clocks 6000,
increment 60). Side A gets its own option(s) after the common list, in the order written below; side B none.

K28, THE KNOWN ANSWER FROM THE PC (before any other game)
Three pairs from the start position, sent as in K27. Game 1 of a pair: A has White. Game 2: B has White.
  pair 1: A = TmFinishIteration true, then TmSoftDivisor 20
  pair 2: A = TmSoftDivisor 16                pair 3: A = TmSoftDivisor 30
Rows, sha and sum exactly as in K27 (the first 20 searches, "<ply> <N> <bestmove>", one LF after each row).
These are the PC's (built-in evaluation, the same options, our runner, our node-clock engine):
  | pair | game | first three rows                              | sha of 20 rows   | sum of N |
  | 1    | 1    | 1 21600 d2d4 / 2 39366 g8f6 / 3 23305 c2c4    | f49482fe2b9738aa | 470764   |
  | 1    | 2    | 1 28565 d2d4 / 2 39366 g8f6 / 3 34511 c2c4    | 749f902e91070fc2 | 507873   |
  | 2    | 1    | 1 28565 d2d4 / 2 39366 g8f6 / 3 34511 c2c4    | f7dc1451fef2f337 | 583536   |
  | 2    | 2    | 1 28565 d2d4 / 2 95535 c7c5 / 3 18811 d4d5    | af5f929dd8c03cc2 | 551293   |
  | 3    | 1    | 1 21600 d2d4 / 2 39366 g8f6 / 3 23305 c2c4    | fb0a79e5c1ffcd06 | 433827   |
  | 3    | 2    | 1 28565 d2d4 / 2 39366 g8f6 / 3 34511 c2c4    | 749f902e91070fc2 | 507873   |
Clocks: pair 2 game 1: White 3290 after ply 19, Black 4084 after ply 20. Pair 3 game 1: 4661 and 4211.
Three of the six equal a game you already played, and that is right: pair 1 game 1 equals K27's pair 1 game 1
(with the finish rule holding, the divisor 20 does not change White's first ten searches), and pair 1 game 2 and
pair 3 game 2 both give the same 20 rows as K27's pair 2 game 2. Our reading of it: a search ends at the end of
a depth or inside one, and those ends lie far apart, so a small change of the
plan often changes nothing for many moves. What shows that the divisor ARRIVED: pair 1 game 2 differs from K27's
pair 1 game 2 (f0130049ccd2829f), both games of pair 2, and pair 3 game 1.
In none of the six games is a claim possible before ply 58 (checked with python-chess), so the first 20 searches
do not depend on the two runners' different draw rules.
If a sha differs: stop before the matches, commit your 20 rows of that game, and put the first row that differs
into the report's first line. That difference is then the finding of this job.
C28, the control and one more known answer: pair 2's game 1 once more with A = TmSoftDivisor 22 (the default,
written out). Its first 20 rows are the engine against itself: sha 492d271d43b7ce03, sum of N 485583. It must
differ from pair 2's f7dc1451fef2f337.

PREDICTION: commit forge-combo29/astra5/job28/prediction.txt ALONE after K28 and C28, before the first game of the
matches (never edited, no time in it): for M4, M5 and M6 the Elo of A against B (a range each) and the reading you
expect; time losses in all three together (a range); blocks complete by minute 45 (a range).

THE MATCHES (NodeClock 100; B = the engine as it is, in all three)
  M4: A = TmFinishIteration true, then TmSoftDivisor 20     M5: A = TmSoftDivisor 16     M6: A = TmSoftDivisor 30
- Openings: the list L27 of job 27, the same 434 lines in the same order (its sha256 into build.txt, with one line
  that it equals job 27's). Pair k of M4, of M5 and of M6 starts from line k (game 2k - 1: A has White; game 2k:
  B has White).
- Played in blocks of 50 lines: M4's block, then M5's, then M6's on the same lines, then the next block. Up to
  nproc - 1 games at once; every game starts two new engine processes.
- At minute 45 start no new block. A block counts only when all three matches finished it; games of a block that
  is not complete are listed and not counted. When L27 is played through in all three, stop playing and write.

THE READING (declared here, before any game of this job; each match by itself)
- Elo of A against B and its 95 % interval from the pentanomial counts of the pairs, as in jobs 26 and 27.
  A BETTER when the lower bound is above 0; B BETTER when the upper bound is below 0; LEVEL otherwise.
- TIME LOSSES: their number; each one with its match, game, ply, N and the clock before the move.
- For the record, no verdict: games by ending; mean used per search for A and for B; in M4 the number of A's
  searches with a line that begins "info string TmFinishIteration hold"; the mean clock left at the end of a game
  for each side.
- For the record, no verdict, and new: B and the openings are job 27's, so every opening now has A's pair points
  (0, 0.5, 1, 1.5 or 2) from six matches against the same B. Over the openings that are complete in both
  matches, give for "M4 minus job 27's M1" and for "M5 minus M6" the mean of the per-opening difference of A's
  pair points, its standard deviation and the 95 % interval of the mean; and beside each, the width that two
  separate matches of that size would give (from the two matches' own pair-point deviations). One line: does
  playing the same openings make the comparison of two settings narrower, and by how much.
- One line at the end: M4 READS AS M1 or M4 READS OTHERWISE, with your two intervals side by side.

WHAT A STOP STOPS: Step 0 failing stops the job. K28 or C28 failing stops the matches (the report covers Step 0,
K28 and C28 with the rows). A bestmove that is not legal, a search without its N line, or an engine line with
"unknown option", "invalid value" or "ERROR" stops the matches. Minute 50 stops the playing: write what is done;
a block not played is listed as not played, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's net and build (the built-in evaluation plays
here); the wall clock; NodeClock values other than 100; divisors other than 16, 20 and 30; the other nine numbers
of the time model; more than one thread; time controls other than 6000 + 60; a difference smaller than the
interval the played pairs give.

The PC plays the same three matches tonight (its net, 1,000 opening pairs each); file 29 brings them.

REPORT: forge-combo29/REPORT_astra5_job28.md, first lines: (1) Step 0 with nproc and A0's sha and T; (2) K28: the
six shas and sums beside ours, and C28; (3) the prediction graded; (4) one table for M4, M5 and M6: pairs, W-L-D,
pentanomial, Elo and interval, time losses, mean used A and B, holds, mean end clock A and B; (5) the three
readings, the two per-opening comparisons, and the last line, word for word by the rules above. Then: facts,
suspicions, "what I did not do", "what I am not sure about". Every number from a file you commit (one row per game
and one row per search; a file above 20 MB is split in parts of 15 MB). The last command before the report
commit: git status --short and ls -R forge-combo29/astra5/job28, pasted into the report. Files only under
forge-combo29/astra5/job28/ (and your notes file); no executable, net, book or archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_29.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is
your next job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
