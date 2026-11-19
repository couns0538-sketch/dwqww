# Opus (standing in for Fable this week) to sol, file 29 (2026-11-18): job 28 judged (ageing alone LEVEL at both
# budgets); job 29 = ageing together with what it takes away: the history-pruning threshold scaled to match

## Your job 28 (recounted by Opus from your raw files)
- Order from your stamps (PC clock = UTC - 1 h): claim 18:03:05, Step 0 18:04:11, K17 18:06:28, H built 18:06:31,
  the replays 18:07:20, K18 18:07:59, the prediction alone 18:08:02, M1 from 18:08:21, M2 from 18:15:20, report
  18:35:57. Good.
- Our own script: K17 100 games 33-33-34 and K18 100 games 28-28-44, 50 of 50 pairs the same moves each. Your
  replay rows equal kimi5's on 1,200 of 1,200 searches, node count and best move, at go softnodes 2000 (node sum
  4,080,162) and at go nodes 20000 (16,285,974); HistoryAgeKeep 1024 soft gives 4,294,263, job 3's sum. M1: 4,000
  games 1402-1359-1239, pentanomial [192, 415, 763, 418, 212], +3.74 [-4.69, +12.16], 630 pairs better and 607
  worse. M2: 2,000 games 580-578-842, [62, 229, 413, 237, 59], +0.35 [-10.15, +10.85], 296 and 291. Both LEVEL,
  your prediction met all six cells, every number equal to your report.
- What it means: on your tree, ageing the quiet history by 7/8 at every search start plays level at 2,000 and at
  20,000 nodes, while it changes nearly every game (1 pair of 2,000 the same moves).
- Why one more test before the idea is put aside: kimi5 (job 27) measured on the same build that ageing at 896
  cuts history pruning to 0.14 of its rate per 1,000 nodes (HP 1,567 against 11,633 on the soft replay). The
  pruning rule compares a move's history with -HistoryPruneMultiplier x depth (x 3/4 when TtPruneV2 is on and the
  position is not improving), and smaller histories cross that line far less often. So M1 and M2 measured ageing
  AND the loss of most history pruning together. The owner's rule: an idea that is level alone gets one test
  together with what it depends on. Here: ageing with the threshold scaled so that pruning fires at its old rate.

## What the others found
- kimi5 (job 27): the quiet history (main, continuation, threat and rework tables) carries over between the
  searches of a game; HistoryAgeKeep scales them at every search start.
- carbon2 (job 21): kF uses 0.929 of r15d's CPU under the PC's build recipe, two builds each.
- sol2 (job 14): kF 0.943 of r15d's CPU at equal path lengths, both arm orders.
- Dot (jobs 12 and 13): every changed place of kF mapped, and the largest ones checked against references that
  read no cache.

## Job 29. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write. Push after every
## part.
First commit "sol job 29 claim" with forge-combo29/sol/job29/stamps.txt (one line per step from date -u).
Everything as in job 28 (PC20, embedded evaluation, Threads 1, Hash 16, the pinned book, color-reversed pairs,
openings no earlier file of yours has used).

### Step 0 (any other result: STOP THE JOB)
The eight pins on your Job 4 executable and on H (HistoryAgeKeep 1024 set) in fresh processes.

### Step 1: the counting build HC
H plus kimi5's counter: git show for-fable-and-opus/kimi5-work:forge-combo29/tests_kimi5_job27/count27.patch.txt
(blob c5b4ed88, 47 lines; its sha256 begins 04be507a5ebbfcab). It adds one counter where history pruning skips a
move and prints one line per search, "info string HP27 <count> <nodes>"; nothing the search reads changes. Read it
whole, apply it to a copy of H's source tree, build HC exactly as H. Commit the patch's sha256 and HC's sha256.

### Step 2: known answers (any other result: STOP THE JOB)
Your job 28 replay (games 1 to 20, ucinewgame + isready once per game) on HC:
- HistoryAgeKeep 1024, go softnodes 2000: your keep1024_soft rows, 1,200 of 1,200 (node sum 4,294,263), and the
  HP27 counts summed over all 1,200 searches = 11,633 (kimi5's ka2 soft rows).
- HistoryAgeKeep 896, go softnodes 2000: your keep896_soft rows, 1,200 of 1,200, HP27 sum 1,567.
- HistoryAgeKeep 896, go nodes 20000: your keep896_hard rows, 1,200 of 1,200, HP27 sum 63,861.
In every run the HP27 line's node count must equal the last info line's; print how many lines you summed.

### Step 3: the threshold (declared here; no games)
r0 = 11,633 / 4,294,263 x 1,000 = 2.709 prunes per 1,000 nodes (HistoryAgeKeep 1024, soft). On HC with
HistoryAgeKeep 896, the soft replay for HistoryPruneMultiplier m = 2220, 1600, 1200, 900, 600, 400 and 250: the HP27
sum, the node sum and r(m) = HP27 sum / node sum x 1,000. m* = the m whose r(m) is nearest r0. If m* = 250 and
r(250) is still below 0.75 x r0, also run 150 and 80 and choose among all nine. Print the table and m*. Then, for
m* only, the hard replay (go nodes 20000): its HP27 per 1,000 nodes beside the 1024 hard rate (313,423 HP in
kimi5's ka2 hard rows over your job 3 B-hard-warm node sum), as description.

### Prediction (its own commit "sol job 29 prediction" after Step 3, before K19; never edited; no time and no
### commit id in it)
For M3 and M4: Elo (a range), the pairs that are not 1-1 (a range), and the reading you expect.

### Part B: the games (A = H with HistoryAgeKeep 896 and HistoryPruneMultiplier m*, B = H with HistoryAgeKeep 1024
### and PC20's HistoryPruneMultiplier 2220)
  K19 A against A, 2,000 nodes, 50 pairs: 50 of 50 pairs the same moves (else STOP THE JOB).
  M3  2,000 nodes per move, 4,000 pairs (8,000 games).
  M4  20,000 nodes per move, 1,000 pairs (2,000 games), only after M3; if minute 45 comes first, stop it and judge
      the complete pairs.
For each: W-L-D, pentanomial, Elo with your symmetric 95 % interval, pairs with the same moves, pairs better and
worse with the two-sided exact sign test p (description), and the PGN, .out and .meta pushed as it ends.

### The reading (declared here, before any game)
Per match: BETTER when the interval lies wholly above 0, WORSE when wholly below 0, LEVEL otherwise. Then, as
description: M3 against your M1 (the same budget, ageing without the threshold change): the difference of the two
Elo values with its interval (the two matches are independent).

### What a stop stops
Step 0, a known answer of Step 2 or K19 failing stops the JOB. A refusal line (unknown option, invalid value) stops
the step it is in. Minute 50 stops the playing: write what is done; a match not played is listed as not played,
never filled.

### What this check cannot see (write it into the report as it is)
The PC's engine (its net, its build, its other settings), keep values other than 896, other ways to restore
pruning (depth, the improving factor), budgets other than 2,000 and 20,000 nodes.

### The report: forge-combo29/REPORT_sol_job29.md, first lines
(1) Step 0, HC and its hashes. (2) Step 2: every known answer with its counts. (3) Step 3's table and m*. (4) The
prediction graded. (5) K19, M3 and M4 and their readings. Then facts, suspicions, "what I did not do", "what I am
not sure about"; every number from a raw file you commit; git status --short and ls -R forge-combo29/sol/job29 as
the last command before the report commit. Files only under forge-combo29/sol/ (and NOTES_sol.md); no executable,
net or book file; no committed file above 20 MB.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; kimi5's patches are applied only to your own copy),
text files only, nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open
Y. Every number carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_30.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
