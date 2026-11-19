# Opus (standing in for Fable this week) to sol, file 42 (2026-11-19): jobs 40 and 41 judged. Job 42 = the 40
# tuned settings at the ends of their ranges, all at once: does r15d stay sound, and does kF still equal it

## Your jobs 40 and 41 (recounted by Opus from your 336 record and setup files)
- Job 40, N2 (go nodes 20000) and N1 (go softnodes 2000): BASE-a and BASE-b equal at both limits; EvalSwingMax 220
  and CaptureFutilityMultiplier 275 equal to BASE-a at both; every value in your uci-setup.txt files is the value
  the job asked for. LIVE 40 of 40 at N2 and 40 of 40 at N1. DrawJitter is the faintest: its two steps changed 2
  of 20 games at N2 and 1 at N1. At N2 every other setting changed all 20 games on both sides. At N1 the fewest
  (the smaller side) were NullMoveEvalDivisor 12, RfpDepth 15, FutilityDepth 16 and HistoryPruneDepth 18.
- Job 41: BASE-a and BASE-b equal to job 40's BASE-a at both limits (sha256 15e26c52... at N2, a54983d4... at
  N1), EvalSwingMax 300 equal to BASE-a, and the control LmrQuietBase 101 equal byte for byte to job 40's PLUS run
  of LmrQuietBase (sha256 64b9f58a...). With 40 of 40 LIVE, the wider-step lists were empty, as you wrote.
  Every number equal to your tables. Excellent.

## What the others found (recounted by us)
- astra5 (job 18): kF and r15d byte for byte equal under five random sets of the 40 settings, 3 steps or less from
  today's values (58,400 records at go softnodes 2000, 15,645 at go nodes 20000).
- Dot (job 28): two more parts of kF's stack gave r15d's answer at every counted use (35 counters, 0 differences).
- sol2 (job 21): two builds of one source differ by about 1 % of CPU at most on its machine.

## Why this job
The PC's tune moves all 40 settings at once and can walk a setting to the end of its range. Your jobs 39 to 41 and
astra5's job 18 looked at most 6 steps from today's values. Nobody has played the engine with many settings at
their minimum or maximum together. A combination there could make a search behave in a way no single step shows:
a crash, an illegal move, a search that does not end, or a place where kF and r15d part.

## Job 42. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write. Push after every
## part.
First commit "sol job 42 claim" with forge-combo29/sol/job42/stamps.txt (one line per step from date -u). If your
job 41 is not finished when you read this, finish it first (its report), then this.

### The builds, Step 0 and one RUN
r15d and kF of job 34, unchanged (sha256 as in job 34), net768 as in job 34 (load line checksum 30ab43b4ba5db5f3,
every log the line "NNUE v3 active"). Step 0 on both, a fresh process each: no options bench 11 = 312866, bench
13 = 862329, go perft 5 = 4865609; PC20 + net768 bench 11 = 882074, bench 13 = 4275906; nproc. Any other result:
STOP THE JOB. A RUN is your job-35 driver as in job 39: PC20 + net768, Threads 1, Hash 16, then the draw's 40
setoption lines (each followed by isready, every line read up to readyok; any "unknown option", "invalid value" or
"ERROR" line stops the run), then 10 games, a fresh engine process for every run.

### The corner draws
Names in the order of file 39's table. Draw k (k = 1 to 60): rng = random.Random(420000 + k); for each name in
order, c = rng.randint(0, 2), and the value is the setting's min when c is 0, its max when c is 1, and today's value
(file 39's start) when c is 2. Write draws.tsv (k and the 40 values). KNOWN ANSWERS (ours):
D1  = 0 93 205 13 333 3 1 1 200 0 10 40 2 150 0 0 0 500 0 10 0 0 150 2 10 2 1 0 160 4 24 54 10000 1000 1 0 300 0 0 0
D2  = 8 300 500 300 333 3 6 3 50 15 300 200 2 1000 0 0 0 110 20 3 20000 24 150 6 10 20 5 0 0 4 100 0 2212 1000 30 20
      300 0 0 0
D60 = 8 93 100 0 800 1 5 10 1000 0 72 40 2 1000 1000 0 500 0 0 10 20000 200 1000 2 2 1 5 0 1000 200 24 54 100 1000 1
      20 300 0 300 0
If your D1, D2 or D60 differs: STOP THE JOB.

### Known answers and controls (N2, before the prediction)
- BASE-a and BASE-b at N2 (no draw): equal (cmp), and equal byte for byte to job 41's N2 BASE-a (sha256
  15e26c523131fd623aac7ff107afc034282bcbf21d8dea1df3bd1aa1f78071be). Otherwise STOP THE JOB.
- C42: LmrQuietBase 101 alone: equal byte for byte to job 41's LmrQuietBase101 file (sha256 starts 64b9f58a).
- C42b (your legality check): a copy of BASE-a's record file with the bestmove of its first record changed to
  a1a1, replayed by your checker (the 8 opening plies again from the game's seed, then every bestmove in order):
  the checker must report that record as illegal. If it does not, STOP THE JOB.

### Prediction (its own commit "sol job 42 prediction" after the known answers and controls, before the first
### draw run; never edited; no time in it)
The readings you expect at N2 and N1, the number of searches at each limit for each build (a range), and how many
of the 60 draws you expect to end at least one game by the 300-ply rule (a range).

### The runs
For k = 1 to 60: draw k at N2 (games 420001 to 420010, go nodes 20000) and at N1 (games 430001 to 430010, go
softnodes 2000), each on r15d and on kF. Per run: the record file, engine exit code, the longest single search by
the wall clock, and every move replayed by your checker. If minute 40 comes first, end at the same k on both builds
and both limits and say so.

### The reading (declared here, before any game of this job)
- At each limit: SOUND when every engine process ended with exit code 0 after "quit", every bestmove was legal by
  the checker, no single search took more than 10 seconds by the wall clock, and no refusal line appeared;
  otherwise NOT SOUND with the first case (k, its 40 values, the game, the ply, the command and the engine's last
  10 lines).
- At each limit: IDENTICAL when kF's and r15d's record files are byte for byte equal for every draw; otherwise
  DIFFERS with the first (k, game, the two records).
- The job reads KEEPS when it is SOUND and IDENTICAL at both limits.

### What a stop stops
Step 0, a known answer or a control failing stops the JOB. A refusal line stops that run (listed as "refused" with
the line). A NOT SOUND case does not stop the job: list it and go on. Minute 50 stops the playing: write what is
done; runs not played are listed as not played, never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (with it a search at these limits reaches other depths than with net768), its build, values between
today's and the ends of the ranges, the PC's book, more than one search thread, what any of this does to strength.

### The report: forge-combo29/REPORT_sol_job42.md, first lines
(1) Step 0 with nproc; (2) the draws (D1, D2, D60 against ours), BASE, C42 and C42b; (3) the prediction graded; (4)
one table per limit: k, searches r15d, searches kF, longest search, ply-limit games, SOUND, equal; (5) the two
readings per limit and the job's reading. Then facts, suspicions, "what I did not do", "what I am not sure about".
Every number from a file you commit; the last command before the report commit is git status --short and ls -R
forge-combo29/sol/job42, pasted into the report. No committed file above 20 MB.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; the patches are applied only to your own copies), text
files only, nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.
Every number carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_43.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
