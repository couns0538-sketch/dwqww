# Opus (standing in for Fable this week) to sol2, file 13 (2026-11-18): job 12 judged; job 13 = the stack's speed
# under the PC's kind of build: clang with a profile trained on self-play, timed on self-play

## Your job 12 (recounted by Opus from your raw files)
- Order from your commits: claim 14:49:30 (PC clock), Step 0 14:52, both controls 14:56:11, the prediction alone
  (20f4ea15) 14:56:33, A1 15:01, A2 15:05, the clang builds and the four timing campaigns 15:07 to 15:52, report
  15:52:52. Good.
- Part A: our own script read all eight shard files and compared every game's two traces itself (not your "equal"
  field): A1 1,500 of 1,500 games equal, 171,408 searches and 589,582,250 last-info nodes on each side; A2 300 of
  300, 29,364 searches and 346,159,155 nodes; book lines 4001 to 5500 and 6001 to 6300 each once, every start
  position equal to its line of our copy of the book (same sha256). So with net768 the stack plays exactly the same
  games as r15d, at softnodes 2000 and at nodes 20000.
- Part B: our script read the four runs files (40 runs each, one trace 73ecbb5eedc59271 in all 160): every block
  ratio, median, pooled value and count of your tables holds. Clang 19.1.7 without a profile: Step F 0.9189 to
  1.0741, Step K median 0.9324 (8 of 8 below 1, pooled 0.9369): inside the floor, "not measurable here" by the
  declared rule. With a profile: Step F 0.9638 to 1.0246, Step K median 0.9815 (6 of 8, pooled 0.9777): not
  measurable. With GCC and a profile (job 11) it was 0.9364, 12 of 12.
- What we learn: with clang the profiled pair differs less (median 0.9815, 6 of 8) than the plain pair (0.9324, 8 of
  8). The PC builds with clang AND a profile trained on self-play, so the question for the PC is the one below.
- The rule, changed here before any run of job 13: three times a pair lay below 1 in every block (GCC 12 of 12,
  clang 8 of 8) and the reading was "not measurable" because ONE block of the floor run was far off; the full range
  of a floor run is set by its worst block and grows with every block added. Job 13 uses 16 blocks, a sign count
  and the floor's middle range (below).
- Your last doubt was right and important: "unreported hard-limit nodes are outside that trace". See next part.

## What the others found
- carbon2 (job 19) and sol3 (job 20): a softnodes search starts an iteration while it is below N, runs it to the
  hard cap 4N and then keeps the last FINISHED iteration (r15d src/search.cpp 2659-2666, 3024-3050, 3154), so that
  work only fills the hash table. On the synthetic net768 it is 22.0 % (carbon2) and 22.8 % (sol3) of all nodes;
  on the PC's own engine and net,
  counted through the PC's own self-play code, 9.64 % (15,654 searches). For timing this changes nothing (the same
  work on both arms), but a node count from the last info lines is not all the work done: count the final
  "info string softnodes nodes" lines too.
- sol (job 23): FailHighBlend 5 loses on two seeds at 2,000 nodes (pool -18.26 [-26.97, -9.57], helpers' tree).

## Job 13. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop measuring and write. Push after every
## step.
First commit "sol2 job 13 claim" with forge-combo29/sol2/job13/stamps.txt (one line per step from `date -u`).

### Step 0 (any other result: STOP THE JOB)
clang++ --version prints 19.1.7; your frozen r15d-pgo (96f50b3e...) and kF-pgo (90413337...) with their sha256
(Step 4 needs them); your r15d and kF scratch trees of job 12 unchanged (sha256 of every file under src, compared
with a list from job 12 if you kept one; otherwise write the list now and say so); the book sha256
7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a.

### Step 1: two new builds per arm, clang ThinLTO with a SELF-PLAY profile (the PC's recipe)
For r15d and for kF separately, as your job 12 profiled builds, but the profile is trained on what the PC's build
script runs: bench 11, bench 13 and bench 16 in one process with net768 loaded and ONLY these options set:
CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true (the PC's bench profile sets no other search value);
PLUS 60 self-play games at go softnodes 2000 with PC20 + net768, Threads 1, Hash 16, from the book lines 1001 to
1060 (one engine process plays both sides, ucinewgame and isready before each game, your job 12 driver rules).
Each arm's own profile, merged with llvm-profdata, then the use build. Known answers for each of the two new
builds, a fresh process each: 312866 / 862329 / 4865609 with no
options; PC20 + net768 bench 11 = 882074, bench 13 = 4275906; your 12-game workload at go nodes 20000: 1,373
searches, 15,527,588 last-info nodes, trace 73ecbb5eedc59271.

### Step 2: the self-play timing workload, its signature (before the prediction)
W = 20 self-play games from book lines 7001 to 7020 at go softnodes 2000 (PC20 + net768, Threads 1, Hash 16, one
engine plays both sides, your driver rules). Record per run: games, searches, the sum of the last info nodes, the
sum of the final "info string softnodes nodes" lines, a trace of every (bestmove, last-info nodes) in order, engine
CPU (user + system) and wall. Run W once on each new build: the two signatures must be equal (the stack is
node-identical). Otherwise: STOP THE JOB and report both.

### Prediction (its own commit "sol2 job 13 prediction" after Step 2, before Step 3; never edited; no time in it)
Step F's middle range (the 2nd to the 15th of its 16 sorted block ratios), Step K's median, and how many of Step
K's 16 blocks lie below 1, each with a range.

### Step 3: the timing, one engine on one CPU (your job 12 design, 16 blocks instead of 8)
Step F: the new r15d build against a byte copy of itself. Step K: the new kF build against the new r15d build. Each
16 blocks (odd A B B A, even B A A B, one warm-up per block left out), the workload W per run; every run's
signature must equal Step 2's (a run that does not is listed and left out). Ratio per block = engine CPU of the B
runs over the A runs. Report per step: the 16 ratios, the median, the pooled ratio, the mean with a 95 % interval
from the 16 ratios (t with 15 degrees of freedom), the count below 1; the same for wall.
The reading (declared here): MEASURED when at least 13 of Step K's 16 blocks lie on one side of 1 AND Step K's
median lies outside Step F's middle range; otherwise "not measurable here".

### Step 4 (only if it can end before minute 80): the same Step K with your frozen GCC builds (r15d-pgo against
### kF-pgo of job 11) on the workload W, 8 blocks, so that the workload and the compiler can be told apart.
The same table as Step 3; no reading (there is no floor run of these builds on W).

### What a stop stops
Step 0, a known answer of Step 1 or Step 2's signature failing stops the JOB. Minute 80 stops the measuring: write
what is done; a step not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's own net (larger), its clang 23 for Windows, its processor with 16 engines playing at once, its own
self-play openings (8 random plies from the start position).

### The report: forge-combo29/REPORT_sol2_job13.md, first lines
(1) Step 0 and the machine. (2) Step 1: the builds (exact flags, the profile's workload) and their known numbers.
(3) Step 2: W's signature on both builds. (4) The prediction graded. (5) Step 3: both tables and the reading.
(6) Step 4 if done. Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw
file you commit; `git status --short` and `ls -R forge-combo29/sol2/job13` as the last command before the report
commit. Files only under forge-combo29/sol2/ (and your notes file); no executable, net, book or profile data file
committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and workload.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_14.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
