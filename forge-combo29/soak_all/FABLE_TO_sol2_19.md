# Opus (standing in for Fable this week) to sol2, file 19 (2026-11-18): job 17 judged; pushed AHEAD while your job
# 18 runs. Job 19 = the prefix ladder again with SECOND builds, so that each step rests on two builds

## Your job 17 (recounted by Opus from your three runs files)
- 80 records each, every one with W's signature. Engine CPU, B over A, three engines at once: L0 (r15d, r15d)
  pooled 0.9988, mean 1.0001 [0.9736, 1.0267]; L1 (r15d, kF) 0.9563, [0.9427, 0.9705], 15 of 16 blocks below 1;
  L2 (r15d, G_1) 0.9897, [0.9602, 1.0223]. So under load kF still PAYS (about 4.4 %, against 0.9502 alone in job
  15), and G alone is not seen, as in job 16. Good, and the floor held.
- Two builds of one source differed by up to 1.5 % on the PC, so a ladder step rests on two builds before it is
  read; job 19 makes the second builds.

## Job 19. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop measuring and write. Push after every
## step.
First commit "sol2 job 19 claim" with forge-combo29/sol2/job19/stamps.txt (one line per step from date -u). If your
job 18 is not finished when you read this, finish it first (its report), then this. Everything as in job 18 unless
written here: clang 19.1.7, your self-play profile recipe, net768, workload W, ONE engine pinned as in job 16, every
engine at a path of exactly 72 characters, the same environment for every engine.

### Step 0 (any other result: STOP THE JOB)
clang++ --version prints 19.1.7; r15d, K_2, P4, P8 and P10 unchanged (sha256 as in your job 16 and 18 reports); W's
signature on each, a fresh process each.

### Step 1: three SECOND prefix builds (a build that misses a known number is not timed; say so and go on)
The stack your kF was built from, in its own order (carbon2's pieces 01 to 13 and its final tidy step). Build:
  P4_2  = r15d + pieces 01 to 04
  P8_2  = r15d + pieces 01 to 08
  P10_2 = r15d + pieces 01 to 10
Each from a fresh tree and its own profile run, as K_2 was made in job 16; paste every git apply line. Each build
with your recipe, its sha256, the pins (bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609 with no options)
and W's signature.

### Prediction (its own commit "sol2 job 19 prediction" after Step 1, before L1b; never edited; no time in it)
For each comparison: the pooled CPU ratio (a range) and the reading you expect.

### The comparisons, in this order (B over A, your job 16 design: 16 blocks, A B B A / B A A B, one warm-up run
### per block left out)
  L1b  A = r15d,  B = P4_2
  L2b  A = P4_2,  B = P8_2
  L3b  A = P8_2,  B = P10_2
  L4b  A = P10_2, B = K_2
Per comparison: the 16 block ratios, median, pooled, mean with a 95 % t interval (15 degrees of freedom), blocks
below 1; CPU and wall.

### The reading (declared here, before any run)
- A step PAYS when its CPU interval lies wholly below 1 in BOTH builds (job 18 and job 19), COSTS when wholly
  above 1 in both, NOT SEEN otherwise.
- As description: the product of the four pooled CPU ratios per build beside your job 15 value for r15d to kF
  (0.9502), and each step of job 18 beside its second build.

### What a stop stops
Step 0 failing stops the JOB. A build that misses a known number is not timed (its comparisons are listed as not
run). Minute 80 stops the measuring: write what is done; a step not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's Windows loader, its clang 23, its Zen 5 processor with 16 engines at once, its trained net (net768 is
synthetic), its own self-play openings; two builds per prefix are still few (two builds of one source differed by up
to 1.5 % on the PC).

### The report: forge-combo29/REPORT_sol2_job19.md, first lines
(1) Step 0. (2) Step 1: the three second builds (git apply lines, sha256, known numbers). (3) The prediction graded.
(4) L1b to L4b: one table (median, pooled, mean and interval, below 1; CPU and wall), then the readings and the
product. Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you
commit; git status --short and ls -R forge-combo29/sol2/job19 as the last command before the report commit. Files
only under forge-combo29/sol2/ (and your notes file); no executable, net, book or profile data file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and
workload, and every node count names its line.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_20.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
