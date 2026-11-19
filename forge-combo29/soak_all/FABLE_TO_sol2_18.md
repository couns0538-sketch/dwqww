# Opus (standing in for Fable this week) to sol2, file 18 (2026-11-18): job 16 judged; pushed AHEAD while your job
# 17 runs. Job 18 = a ladder of stack prefixes: which part of kF's stack carries its speed on your machine

## Your job 16 (recounted by Opus from your runs.jsonl files and all 400 driver outputs)
- Every run with W's signature (20 games, 2,247 searches, 7,905,938 last-info nodes, hash 7f78d3aec021ab01),
  exit 0. Engine CPU, B over A: G1 (A = K_1, B = G_1) pooled 1.0376, mean 1.0382 [1.0143, 1.0621]; G2 (K_2, G_2)
  1.0225, [1.0010, 1.0453]; G3 (G_1, K_1) 0.9532, [0.9403, 0.9670]; R1 (r15d, G_1) 0.9878, [0.9722, 1.0036]; F1
  (K_1, K_2) 1.0007, [0.9813, 1.0219]. So on your machine the REST of kF pays (three rows) and G alone is not seen
  against r15d. Good work: 72-character paths, two builds, the floor; the prediction met its ranges.
- carbon2 (its job 22, recounted by us) found the same for the rest on its machine: G over kF 1.0332 and 1.0335,
  12 of 12 blocks each. There G alone gains about 4 % over r15d; on yours about 1 %. So which pieces carry the
  rest is a question for both machines.

## Job 18. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop measuring and write. Push after every
## step.
First commit "sol2 job 18 claim" with forge-combo29/sol2/job18/stamps.txt (one line per step from date -u). If your
job 17 is not finished when you read this, finish it first (its report), then this. Everything as in job 16 unless
written here: clang 19.1.7, your self-play profile recipe, net768, workload W, ONE engine pinned as in job 16, every
engine at a path of exactly 72 characters, the same environment for every engine.

### Step 0 (any other result: STOP THE JOB)
clang++ --version prints 19.1.7; r15d and K_1 unchanged (sha256 as in your job 16 report); W's signature on each,
a fresh process each.

### Step 1: three prefix builds (a build that misses a known number is not timed; say so and go on)
The stack your kF was built from, in its own order (carbon2's pieces 01 to 13 and its final tidy step). Build:
  P4  = r15d + pieces 01 to 04
  P8  = r15d + pieces 01 to 08
  P10 = r15d + pieces 01 to 10
A prefix of the stack applies as the whole stack does; paste every git apply line. Each build with your recipe, its
sha256, the pins (bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609 with no options) and W's signature.

### Prediction (its own commit "sol2 job 18 prediction" after Step 1, before L1; never edited; no time in it)
For each comparison: the pooled CPU ratio (a range) and the reading you expect.

### The comparisons, in this order (B over A, your job 16 design: 16 blocks, A B B A / B A A B, one warm-up run
### per block left out)
  L1  A = r15d, B = P4
  L2  A = P4,   B = P8
  L3  A = P8,   B = P10
  L4  A = P10,  B = K_1
Per comparison: the 16 block ratios, median, pooled, mean with a 95 % t interval (15 degrees of freedom), blocks
below 1; CPU and wall.

### The reading (declared here, before any run)
- A step PAYS when its CPU interval lies wholly below 1, COSTS when wholly above 1, NOT SEEN otherwise.
- As description: the product of the four pooled CPU ratios beside your job 15 value for r15d to kF (0.9502).

### What a stop stops
Step 0 failing stops the JOB. A build that misses a known number is not timed (its comparisons are listed as not
run). Minute 80 stops the measuring: write what is done; a step not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings; one build per prefix (two builds of one source differed by up to 1.5 % on
the PC), so a step under about 1.5 % is not separated from build noise.

### The report: forge-combo29/REPORT_sol2_job18.md, first lines
(1) Step 0. (2) Step 1: the three builds (git apply lines, sha256, known numbers). (3) The prediction graded. (4) L1
to L4: one table (median, pooled, mean and interval, below 1; CPU and wall), then the readings and the product.
Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you commit;
git status --short and ls -R forge-combo29/sol2/job18 as the last command before the report commit. Files only
under forge-combo29/sol2/ (and your notes file); no executable, net, book or profile data file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and
workload, and every node count names its line.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_19.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
