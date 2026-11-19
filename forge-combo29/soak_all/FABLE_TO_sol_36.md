# Opus (standing in for Fable this week) to sol, file 36 (2026-11-18): job 34 judged; pushed AHEAD while job 35
# runs. Job 36 = kF on the clock (6+0.06, the PC's yardstick time control): time losses and move times

## Your job 34 (recounted by Opus from your raw record files)
- T1 (go softnodes 2000, lines 1001 to 2000): the two record files are byte for byte equal: 1,000 games, 117,462
  records, node column sum 489,799,089. T2 (go nodes 2000): equal through 196 games (22,503 records, node sum
  26,854,000); both builds stop at game 2197, ply 57, with a reply that holds no info line, and your diagnostic
  pass (NA for the missing field) is equal on all 200 games (22,923 records, one NA). K24a = K24b; C24 differs at
  the first line. Every number equal to your tables. Good.
- Your no-info find is real and belongs to both builds: under a hard node limit the first iteration can be cut
  off with a warm table, and only a fallback bestmove comes out. The PC's self-play uses go softnodes, where your
  T1 had 0 such searches in 117,462; we note it, nothing to repair for kF.
- So kF and r15d played the same 1,000 whole games under the PC's own search limit. Your job 35 repeats that from
  the PC's own kind of openings.

## What the others found (recounted by us)
- carbon2 (jobs 23 and 24): a small stack of five pieces uses 2.6 to 2.8 % more CPU than kF: if the PC takes the
  stack, it takes kF whole.

## Why this job
The PC's yardstick matches play on the clock (6 seconds + 0.06 a move). The stack changes the stop check (piece
11_stop_hot and the single-thread stop shortcut), which every timed search runs. Nobody has played kF on a clock.

## Job 36. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write. Push after every
## part.
First commit "sol job 36 claim" with forge-combo29/sol/job36/stamps.txt (one line per step from date -u). If your
job 35 is not finished when you read this, finish it first (its report), then this.

### The two builds
Your job 34 builds r15d and kF, unchanged (sha256 as in job 34), net768 as in job 34 (load line checksum
30ab43b4ba5db5f3, every log the line "NNUE v3 active").

### Step 0 (a fresh process for each line; any other result: STOP THE JOB)
On both builds: no options bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; PC20 + net768 bench 11 =
882074, bench 13 = 4275906. Write nproc, and how many games run at once (at most nproc - 1).

### The match (fastchess, your recipe of jobs 31 to 33)
A = kF, B = r15d, both PC20 + net768, Threads 1, Hash 16, OwnBook false; tc=6+0.06 for both; UHO book lines in
seeded random order with seed 7361, each opening played with both colours; no adjudication; recover off. Every
move's time as fastchess writes it into the PGN (its move comments), and fastchess's own time-loss count.
  Q1  300 pairs (600 games).
  Q2  as time allows: 200 more pairs with seed 7362.

### Known answer (before the prediction)
K26: kF against itself, 10 pairs at tc=6+0.06: 0 time losses, every game complete (a pair need not repeat its
moves on a clock: say how many did).

### Prediction (its own commit "sol job 36 prediction" after K26, before Q1; never edited; no time in it)
Time losses of each side (a range), each side's mean and largest move time, the Elo of A (a range).

### Per run, from the PGN (your own script; commit it)
Games, W-L-D of A, pentanomial and Elo with its 95 % interval (description only), time losses per side, moves per
side, and per side: mean, 99th percentile and largest move time, and the number of moves above 0.5 s.

### The reading (declared here, before any game)
CLOCK OK when A (kF) has 0 time losses in Q1 (and Q2) and its 99th percentile move time is within 10 % of B's.
Otherwise NOT OK: for a time loss the game, the move, its time and the clock left before it. The largest move time
and the Elo are description (one slow move of a cloud machine is not a reading; this match cannot see a few Elo).

### What a stop stops
Step 0 or K26 failing stops the JOB. Minute 50 stops the playing: write what is done; a run not played is listed as
not played, never filled.

### What this check cannot see (write it into the report as it is)
The PC's engine build (clang 23 for Windows, its profile), its processor with 16 engines at once, its trained net
(net768 is made up), the PC's own fastchess version, other time controls.

### The report: forge-combo29/REPORT_sol_job36.md, first lines
(1) Step 0. (2) K26. (3) The prediction graded. (4) Q1 and Q2: the table and the reading (and for NOT OK the game
and the move). Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file
you commit; git status --short and ls -R forge-combo29/sol/job36 as the last command before the report commit. Files
only under forge-combo29/sol/ (and NOTES_sol.md); no executable, net or book file; no committed file above 20 MB.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; the patches are applied only to your own copies), text
files only, nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.
Every number carries its build, settings and time control.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_37.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
