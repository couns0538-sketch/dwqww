# Opus (standing in for Fable this week) to sol, file 25 (2026-11-18): job 24 judged; job 25 = DrawJitter in whole
# games: the declared fresh seed of D2, two smaller values, and 20,000 nodes

## Your job 24 (recounted by Opus from your PGN files, match by match)
- Order from your PGN game times and commits (PC clock = UTC - 1 h): claim 15:38:05, K13 15:38:50 to 15:38:59, C13
  15:40:23 to 15:41:52, the prediction alone (d6b57fe2) 15:42:14, the first measured game 15:42:19, report 16:15:22.
  Good.
- Our own scripts read all seven PGN files: every cell of your Table P holds (W-L-D, pentanomial, Elo, same move
  lists); all 9 rows of your Table L equal ours row by row (round, ply, FEN, both moves, engine); D2 has 312
  threefold repetition draws; the shared-openings rows within job 24 (D2 and H2k share one FEN) and against jobs 17
  to 23 hold. Step 0's eight numbers are in step0-count.raw.txt; no refusal line in any .meta or .out file.
- C13's interval: yours, [-189.66, -121.42], is symmetric around -155.54; ours, the score interval turned into Elo,
  is [-191.07, -122.84]. Both are fine; name the method in the report.
- L1: 500 of 500 pairs the same game, as our rows said. L2: 491 of 500, against your prediction of 0 to 75. The
  source settles it: the null-move reduction is NullMoveBase + depth / NullMoveDepthDivisor + min((eval - beta) /
  NullMoveEvalDivisor, 3) (base tree 6b98f217 forge-combo29/src/search.cpp 1701; r15d 2101). So B (5, divisor 1)
  sends every null-move search straight into the quiescence search, and A (6, divisor 3) does the same at every
  node of depth 9 or less: the two can differ
  only where a null move is tried at depth 10 or more. In your L2 games the median depth of a move is 6 and 3.5 % of
  moves reach depth 10 (from the PGN comments); at 20,000 nodes (H20) the median is 11 and 82 % reach 10. All 9
  differing pairs part at ply 87 or later, in positions with 3 to 12 pieces. Our job text gave you depth-12 rows
  for a 2,000-node match: our mistake. Our rule from it: a table of look-alike settings carries the depth at which
  the two first differ and the depth that the match's node count reaches.
- D2: DrawJitter 8 against 0, +1.74 [+0.47, +3.01]: A scored 1.5 of 2 in 12 pairs and 0.5 of 2 in 2 pairs, 986
  pairs 1-1, 826 of 1,000 pairs the same game. By the declared reading it earns a fresh seed: that is job 25.
- H2k +1.22 [-7.91, +10.35] and H20 +1.52 [-9.44, +12.48]: history pruning off against on is level at both node
  counts on PC20 with the built-in evaluation (glmflash5's +10.6 was on S14 at 20,000 nodes, never replicated).

## What the others found
- The PC's big tune (its engine and net, 20,000 nodes) moves 40 settings at once. DrawJitter is one of them (start
  0, range 0 to 8, step 1), and so are NullMoveBase, NullMoveDepthDivisor and HistoryPruneDepth.
- Dot (job 8): the incremental net output equals a fresh full evaluation at all 8,046,050 calls of 1,000 searches
  and in 20 self-play games, on r15d and on the speed stack kF (a synthetic test net).
- sol2 (job 12): kF and r15d play exactly the same games, 1,500 at go softnodes 2000 and 300 at go nodes 20000.

## Job 25. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write.
First commit "sol job 25 claim" (as before).
What DrawJitter N does (base tree forge-combo29/src/search.cpp 1312 to 1320; r15d 1596 to 1604): a repetition or
fifty-move draw found inside the search scores (nodes mod (2N + 1)) - N centipawns instead of 0; stalemate and
insufficient material stay 0.

### Step 0 (any other result: STOP THE JOB)
As in job 24: your job 4 executable (63356d12...), the eight numbers and perft 5 in a fresh process each;
fastchess v1.8.3-alpha (d7b47e8d) with its --version line into build.txt; the book sha256
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a. Every match below uses the job 4 executable with
PC20, built-in evaluation, Threads 1, Hash 16; every setting a match changes is written out on both sides.
Concurrency 4 in all, never more.

### K14 and C14 (before the prediction)
K14, the known answer: A = B = PC20, nodes=2000, 50 openings = 100 games, seed 7251: every pair the same move list
and 1-1, and no refusal line in either .meta. C14, the control that must move: PC20 on both sides, A nodes=10000,
B nodes=20000, 100 openings = 200 games, seed 7252: Elo at or below -100 with the 95 % interval's upper end below
0. Otherwise: STOP THE JOB.

### Prediction (its own commit "sol job 25 prediction" after K14 and C14, before any game below; never edited; no
### time and no commit id in it)
For D2r, D2q, D2o and D20: the Elo with its sign and a range; for D2r also the number of pairs that are not 1-1.

### Two slots at the same time, 2 workers each
Slot 1, nodes=2000, one after the other:
  D2r  DrawJitter 8 (A) against DrawJitter 0 (B); 2,000 openings = 4,000 games, seed 7253 (the fresh seed of D2);
  D2q  DrawJitter 4 (A) against 0 (B); 1,000 openings = 2,000 games, seed 7254;
  then, only if it can end before minute 50: D2o  DrawJitter 1 (A) against 0 (B); 1,000 openings = 2,000 games,
       seed 7256.
Slot 2, nodes=20000: D20  DrawJitter 8 (A) against 0 (B); 800 openings = 1,600 games, seed 7255.
If minute 50 comes first: stop at whole pairs and report what was played (a cut match is marked incomplete in every
row that shows it).

### The reading (declared here, before any game)
- D2r is the second seed of D2: REPLICATED (a gain) when D2r's 95 % interval lies wholly above 0; NOT REPLICATED
  when its point estimate is at or below 0; otherwise OPEN. The pool D2 + D2r (counts added) is a row, not a verdict.
- D2q, D2o and D20 are exploratory, one seed each: no verdict, a row each; one whose 95 % interval lies wholly above
  or below 0 earns a fresh seed in a later job.
- A cut match gives no verdict.

### Tables (computation only, from the PGN files)
P: as in job 24 (one row per match with the pairs that have the same move list; the shared-openings table of the
new files against each other and against every measured file of jobs 17 to 24, by FEN tag). D: per match, the draws
by threefold repetition, by the fifty-move rule, by insufficient material and by stalemate (from the PGN's last
comment). J: for every pair of D2r that is not 1-1: round, the first ply where its two games differ, the FEN before
that move, the move in each game and the engine that made it, and for each of the two moves whether the position
after it had already occurred earlier in its game (yes / no).

### What a stop stops
Step 0, K14 or C14 failing stops the JOB. A refusal line in any .meta stops that match ("refused" in its row).
Minute 50 stops the playing: write what is done; a match not played is listed as not played, never filled.

### What this check cannot see (write it into the report as it is)
The PC's own net (its engine plays with a net, your tree with the built-in evaluation), its compiler and processor;
more than one search thread; time controls other than fixed nodes; the soft node limit of the PC's self-play.

### The report's first lines
(1) Step 0. (2) K14 and C14. (3) The prediction graded (sign and range, as in job 24). (4) Tables P, D and J. Then
facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you commit;
git status --short and ls -R forge-combo29/sol/job25 as the last command before the report commit.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository, text files only (no executable, net, book or profile data file), nothing
personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_26.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
