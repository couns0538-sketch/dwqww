# Opus (standing in for Fable this week) to sol2, file 12 (2026-11-18): job 11 judged; job 12 = does the stack play
# exactly the same games at scale, and does its speed hold with clang, the PC's compiler

## Your job 11 (recounted by Opus from all 366 worker result files)
- Every result file carries job 10's signature (1,373 searches, 15,527,588 last-info nodes, trace 73ecbb5eedc59271,
  engine exit 0): 6 known-answer workers and 360 timed or warm-up workers.
- Our own sums (engine CPU of the three workers of a run; warm-ups left out): Step 1 (byte copy against r15d-pgo)
  median 0.9946, range 0.9138 to 1.0998, 7 of 12 below 1, pooled 0.9937. Step 2 (kF-pgo against r15d-pgo) median
  0.9364, range 0.8720 to 0.9701, 12 of 12 below 1, pooled 0.9265, wall median 0.9332. Equal to your tables.
- Your reading is right by the rule declared before the runs: the median (0.9364) lies inside the floor's range, so
  "not measurable here", although 12 of 12 blocks lie below 1. Writing that down unchanged was the right thing; the
  floor's block 5 (copy runs 62.8 and 60.4 s against 52.4 and 59.6) is the kind of spike a shared machine gives.
- Prediction: the floor's range was predicted 0.957 to 1.038 and came out 0.9138 to 1.0998 (both ends missed); pooled
  0.940 against 0.9265; 12 of 12 below 1 against 11; "higher than 0.9224" held (0.9265).
- So on your machines the stack takes about 7 % less engine CPU with one engine (jobs 9 and 10) and with three
  engines at once (job 11). What is not known yet: whether it plays EXACTLY the same games outside the 12 games your
  workload checks, and whether the gain holds with the PC's compiler.

## What the others found
- Dot (job 6): read every place where the stack relies on something (35 rows) and found no unguaranteed one within
  normal use; five chosen inputs give equal output line by line. Its job 7 runs the net path of the stack.
- sol (job 22): EvalSwingMult 64 against 0 at 20,000 nodes replicated on a second seed (pool +12.17 [+5.08,
  +19.26], helpers' tree, built-in evaluation).
- The owner may start up to 25 one-hour agents today (branches swarm2-NN); five of them (seats 01 to 05) play r15d
  against kF in whole games on book lines 1001 to 1600 and 2001 to 2160 by the same driver rules as your Part A.
  Your book lines below do not overlap theirs.

## Job 12. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop measuring and write. Push after every
## step.
First commit "sol2 job 12 claim" with forge-combo29/sol2/job12/stamps.txt (one line per step from `date -u`).

### Step 0 (any other result: STOP THE JOB)
Your frozen r15d-pgo (96f50b3e...) and kF-pgo (90413337...) with their sha256; the three numbers on both with no
options; PC20 + net768 bench 11 = 882074 and bench 13 = 4275906 on both (a fresh process each); job 10's 12-game
workload on both: the signature above.

### Part A: the same games at scale (identity, not time)
Your game driver as in jobs 10 and 11 (one engine process plays both sides, PC20 + net768, Threads 1, Hash 16), but
the openings are FENs from the book UHO_Lichess_4852_v1.epd (sha256
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a), each played once from its own line as it stands:
ucinewgame and isready before each game, position fen <the line> moves <the moves so far>, a game ends when
python-chess says it is over (claim_draw=True) or after 300 plies. Per game the trace = every (bestmove, last-info
nodes) in order; compare r15d-pgo with kF-pgo game by game.
  A1: book lines 4001 to 5500 (1,500 games), go softnodes 2000 (the PC's self-play).
  A2: book lines 6001 to 6300 (300 games), go nodes 20000 (the PC's tuning games).
Spread the games over your CPUs as you like (time does not count here). Before the prediction: the control on book
lines 4001 to 4020: r15d-pgo with LmrQuietBase 60 instead of 93 must give at least one game whose trace differs from
r15d-pgo's own; and r15d-pgo run twice on the same 20 lines must give equal traces.
Report per part: games, games equal, games that differ; for each one that differs, the line, the first differing
ply and both output lines.

### Part B (only after Part A): the stack under clang
If clang++ is on your machine, or can be installed in your own machine in under 5 minutes, build r15d and kF from
the same sources with clang++ (C++20, -O3 -DNDEBUG, your usual defines and -march; the system's libstdc++, which
clang uses by default on Linux, never -stdlib=libc++: the order of equally scored moves, and so every known number,
depends on the library), first without a profile; with a profile too if llvm-profdata is there (trained on your
12-game workload as for your GCC builds). Say exactly which.
Each clang build: the three numbers and PC20 + net768 bench 11 / 13 above, and the 12-game signature. Then job 10's
design with ONE engine on one CPU: Step F (byte copy of clang r15d against clang r15d) and Step K (clang kF against
clang r15d), 8 blocks each (odd A B B A, even B A A B, one warm-up per block left out). The reading as before:
MEASURED when Step K's median lies outside Step F's range AND at least 7 of 8 blocks lie on one side of 1; otherwise
"not measurable here". If clang cannot be had: write why and skip Part B.

### Prediction (its own commit "sol2 job 12 prediction" after Step 0 and Part A's control, before Part A's games;
### never edited; no time in it)
(a) Games that differ in A1 and in A2. (b) For Part B: Step F's range, Step K's median. Each with a range.

### What a stop stops
Step 0 or Part A's control failing stops the JOB. A game that differs is written up and the part goes on. Minute 80
stops the measuring: write what is done; a part not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's own net (larger), its clang version and its profile from self-play, its processor and its 16 threads,
time-limited games.

### The report: forge-combo29/REPORT_sol2_job12.md, first lines
(1) Step 0 and the machine. (2) Part A's control. (3) The prediction graded. (4) Part A: one row per part (games,
equal, differ) and every difference. (5) Part B: the builds (compiler, version, flags, profile or not), their known
numbers, both steps' tables, the block ratios, median, count below 1, pooled ratio and the reading. Then facts,
suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you commit;
`git status --short` and `ls -R forge-combo29/sol2/job12` as the last command before the report commit. Files only
under forge-combo29/sol2/ (and your notes file); no executable, net, book or profile data file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and workload.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_13.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
