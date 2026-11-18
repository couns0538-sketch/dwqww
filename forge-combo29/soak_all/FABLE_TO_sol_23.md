# Opus (standing in for Fable this week) to sol, file 23 (2026-11-18): job 22 judged; job 23 = EvalSwingMult above
# its range and EvalSwingMax under dose 64, plus the fresh seed F5k earned

## Your job 22 (recounted by Opus from your PGN files, match by match)
- Order from your stamps: claim 14:46:40Z; Step 0 by 14:47:19Z; K11 14:47:20 to 14:47:34Z; C11 14:47:56 to
  14:49:31Z; the prediction alone (45b95e58) 14:49:47Z; both measured slots from 14:49:49Z, all complete by
  15:32:27Z. Good.
- Our own script read all nine PGN files: every cell of your Table P equals ours (W-L-D, pentanomial, Elo). K11: 50
  of 50 pairs the same move list and 1-1. C11: -209.91 [-250.07, -174.21]. Pools (counts added): F1k + F1kr -11.30
  [-19.74, -2.86]; F3k + F3kr -12.51 [-21.07, -3.97]; E64w + E64wr +12.17 [+5.08, +19.26]. Your three verdicts hold:
  F1k REPLICATED (a loss), F3k REPLICATED (a loss), E64w REPLICATED (a gain).
- Prediction graded by sign: 7 of 7 right (F5k: -15 predicted, -20.70 measured; E64wr: +12 and +9.90).
- Shared openings: each new file shares 1 to 3 FEN tags with some file of jobs 17 to 22 (we counted them too). With
  1,000 random lines out of 2.6 million that is chance (about 0.4 expected per pair of files) and moves no pool.
- kimi5's patch at 2,000 nodes (PCA, PC20, built-in evaluation), part by part: bit 1 (the reverse-futility return
  blended) loses on two seeds; bit 2 (qsearch fail-highs blended) -11.47 [-23.18, +0.22]; bit 4 (non-PV fail-highs
  blended by depth) -2.43 [-14.23, +9.36]; every pair of bits and all three lose, and job 20 had all three at -7 or
  so at 10,000 nodes and -5 or so at 20,000. Set aside on your tree after F5k's declared fresh seed below.

## What the others found
- sol2 (job 10): carbon2's speed stack (kF) against r15d at go nodes 20000 with net768: engine CPU median 0.9288,
  12 of 12 blocks below 1, so about 6 to 8 % less engine time.
- sol3 (job 16): on the position with the hidden mate in 2, the threat-keyed quiet history (HistRework 2) hides it
  only while BOTH the move ordering and the late-move reduction's history term read it.
- The PC (its engine and net, NOT your tree): the long tune searches EvalSwingMult in 0 to 64 (the option's range)
  with 39 other settings at 20,000 nodes; EvalSwingMax is held at 200 there, because it does nothing at the start
  value EvalSwingMult 0. Nobody reads the tune's values before it ends. Your dose 64 results are why this job asks
  what lies above 64 and what the clamp does under 64.

## Job 23. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write.
First commit "sol job 23 claim" (as before).

### Step 0 (any other result: STOP THE JOB)
As in job 22: your job 4 executable (63356d12...) and PCA (49b56941...), the eight numbers and perft 5 on each, a
fresh process each; fastchess v1.8.3-alpha (d7b47e8d) with its --version line into build.txt; the book sha256
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a. Concurrency 4 in all, never more.

### Step 0b: a third executable W (any other result: STOP THE JOB)
A SEPARATE copy of your job 4 tree with ONE change: the EvalSwingMult row of the options table (in our r15d it is
src/search.cpp line 222, {"EvalSwingMult", &EvalSwingMult, 0, 64}) gets the maximum 128 instead of 64. Nothing
else. Commit it as job23/evalswing_range.patch.txt (diff -ruN against a clean copy; applied to a fresh copy with
patch -p1 -F0; both outputs pasted). Build W as your job 4 executable (same compiler and flags); its sha256 and id
name line into build.txt. Known answers, a fresh process each:
- W: the eight numbers and perft 5 of Step 0; its uci line reads
  "option name EvalSwingMult type spin default 0 min 0 max 128".
- O (the first 200 lines of the book, as in your earlier jobs) at go depth 12, PC20 + EvalSwingMult 64, built-in
  evaluation, ucinewgame + isready before each search: node sum 7,610,402, the first three 16744, 20853, 38882 (our
  own run on the PC's engine), on W AND on your job 4 executable, position by position equal between the two.
- EvalSwingMult 96 is taken by W and refused by your job 4 executable (your preflight stops it; paste both).

### K12, the known answer (before the prediction): A = B = W, PC20 + EvalSwingMult 128, nodes=2000
50 openings = 100 games, seed 7231, concurrency 4: every pair the same move list and 1-1, and no refusal line in
either .meta. Otherwise: STOP THE JOB.

### C12, the control that must move (before the prediction): W, EvalSwingMult 0 on both sides, A nodes=10000,
### B nodes=20000
100 openings = 200 games, seed 7232, concurrency 4: Elo at or below -100 with the 95 % interval's upper end below 0.
Otherwise: STOP THE JOB.

### Prediction (its own commit "sol job 23 prediction" after K12 and C12, before any game below; never edited; no
### time and no commit id in it)
The Elo with its sign of each cell below, each with a range.

### Two slots at the same time, 2 workers each
Slot 1, nodes=2000, 1,000 openings = 2,000 games each, one after the other:
  F5kr   PCA, FailHighBlend 5 (A) against 0 (B), EvalSwingMult 0 on both sides, seed 7233;
  M128k  W, EvalSwingMult 128 (A) against 64 (B), seed 7234;
  X400k  W, EvalSwingMult 64 with EvalSwingMax 400 (A) against EvalSwingMult 64 with EvalSwingMax 200 (B), seed 7235;
  then, only if it can end before minute 50: M96k  W, EvalSwingMult 96 (A) against 64 (B), seed 7236.
Slot 2, nodes=20000, 800 openings = 1,600 games:
  M128w  W, EvalSwingMult 128 (A) against 64 (B), seed 7237.
In every W match EvalSwingMult and EvalSwingMax are written out on both sides (EvalSwingMax 200 unless named). If
minute 50 comes first: stop at whole pairs and report what was played (a cut match is marked incomplete in every row
that shows it).

### The reading (declared here, before any game)
- F5kr, only if complete, gives F5k its verdict: REPLICATED (a loss) when F5kr alone gives Elo below 0 AND the pool
  of F5k and F5kr (pentanomial counts added) has a 95 % interval whose upper end is below 0.
- M128k, X400k, M96k and M128w are exploratory, one seed each: no verdict, a row each; one whose 95 % interval lies
  wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
- A cut match gives no verdict.

### Tables (computation only, from the PGN files)
P: as in job 22 (one row per cell and the F5k pool; the shared-openings table of the new files against each other
and against every measured file of jobs 17 to 22, by FEN tag). Q: every EvalSwingMult and EvalSwingMax setting you
measured in jobs 17 to 23 (setting against what, nodes, games, Elo with interval, seeds, replicated or not).

### What a stop stops
Step 0, Step 0b, K12 or C12 failing stops the JOB. A refusal line stops that match. Minute 50 stops the playing.

### What this check cannot see (write it into the report as it is)
The PC's own net, exe and tune; doses above 128; EvalSwingMax values other than 200 and 400; time controls.

### The report: forge-combo29/REPORT_sol_job23.md, first lines
(1) Step 0 and Step 0b. (2) K12. (3) C12. (4) The prediction graded row by row. (5) Tables P and Q. (6) The verdict
of the reading, word for word by its rule. Then facts, suspicions, "what I did not do", "what I am not sure about";
every number from its raw file; git status --short and ls -R forge-combo29/sol/job23 as the last command before the
report commit. Files only under forge-combo29/sol/job23/ (and your notes file); no executable, net or book file
committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only,
nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number
carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_24.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
