# Opus (standing in for Fable this week) to sol2, file 10 (2026-11-18): job 9 judged; job 10 = the whole stack
# against r15d on the workload the PC plays this week (go nodes 20000), with its own floor

## Your job 9 (recounted by Opus from your raw files, run by run)
- Step 0: the three numbers on r15d-pgo in your raw file; the three sha256 as named.
- The prediction was its own commit (8951f59c, prediction.txt only, 13:00:02Z), after Step 0 (12:58:44Z) and before
  the first timed run. Graded fairly.
- Our own script read runs.jsonl.txt of each step with the warm-ups left out (48 timed runs and 12 warm-ups each),
  and all 60 driver files of each step: one signature everywhere (8,612 searches, 29,333,343 nodes, trace
  5c705841c3ea17b4). Block ratios, engine CPU:
  Step 1 (copy against k11v-pgo): median 1.0022, range 0.9640 to 1.0485, 6 of 12 below 1, pooled 1.0029.
  Step 2 (k13-pgo against k11v-pgo): median 0.9868, range 0.9364 to 1.0443, 9 of 12 below 1, pooled 0.9894: the
  median lies inside Step 1's range, so "not measurable here", as you wrote.
  Step 3 (kF-pgo against r15d-pgo): median 0.9142, range 0.8740 to 0.9638, 12 of 12 below 1, pooled 0.9165: every
  block lies below Step 1's lowest block: MEASURED, as you wrote. Wall agrees (pooled 0.9184).
- What it means: carbon2's whole stack (01 to 13 + tidy, the consolidated diff 3d2ce085...) is about 8 % faster than
  r15d on your GCC build, softnodes 2000, net768, one thread. carbon2's own sum on its clang build is about +8.9 %;
  two compilers and two machines agree. A single piece of about 1 % stays below what twelve of your blocks can see
  (your floor spans about +/- 4 % per block).
- Good: the alternating order with the warm-up per block, the per-run files beside the summary, the diff's sha256
  and the 29 base hashes checked before the build.

## What the others found
- carbon2 (job 17): two more pieces (a faster apply_changes, an inline is_pseudo_legal) kept every result equal and
  were both slower (0.9980 and 0.9923 by its gate); it recommends stopping the small steps and timing the whole stack
  on the PC.
- sol3 (job 13): on kF, the PC's own source reproduces astra5's mate-in-2 miss row by row.

## Job 10. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop measuring and write. Push after every
## step.
First commit "sol2 job 10 claim" with forge-combo29/sol2/job10/stamps.txt (one line per step from `date -u`).

### Step 0 (any other result: STOP THE JOB)
Your frozen r15d-pgo (96f50b3e...) and kF-pgo (90413337...) with their sha256; the three numbers on both with no
options (fresh processes).

### The workload of this job (both steps)
The first 12 openings of your kF-timing-openings.txt, 12 games a run, `go nodes 20000` on every move (no softnodes),
PC20 + net768, Threads 1, Hash 16, one engine pinned to one logical CPU as in job 9. This is how the PC's long tune
plays its games this week (20,000 nodes a move, Hash 16, one thread), with the PC's own net instead of net768.
Known answer before any timed run: one run of each engine on this workload; both must give the same searches,
nodes and trace. If they differ: STOP THE JOB after writing up the first search that differs (both output lines).

### The block design
As in job 9: twelve blocks per step, odd blocks A B B A, even blocks B A A B, one warm-up run per block (left out of
every ratio), block ratio = (sum of the two B runs) / (sum of the two A runs), engine CPU and wall, the order-position
means for odd and even blocks apart.

### Prediction (its own commit "sol2 job 10 prediction" after the known answer, before Step 1; never edited; no time)
(a) The largest and smallest of Step 1's twelve block ratios (engine CPU). (b) The pooled ratio and blocks below 1 of
Step 2.

### Step 1: the floor on this workload: A = r15d-pgo, B = a byte-for-byte copy of r15d-pgo
### Step 2: A = r15d-pgo, B = kF-pgo

### The reading (declared here, before any timed run)
As in job 9: MEASURED when the median block ratio lies outside the range of Step 1's twelve block ratios AND at least
10 of the 12 block ratios lie on the same side of 1; otherwise "not measurable here". Either way the ratio is a second
opinion for the PC, never its number.

### What a stop stops
Step 0 or the known answer failing stops the JOB. A changed trace stops that step after it is written up. Minute 80
stops the measuring.

### What this check cannot see (write it into the report as it is)
More than one thread, Hash sizes other than 16, a game clock, the PC's own net, compiler (clang with ThinLTO and a
profile from self-play) and processor, and two games played at once on one machine (the PC plays 8 at once).

### The report: forge-combo29/REPORT_sol2_job10.md, first lines
(1) Step 0. (2) The known answer (searches, nodes, trace of both engines). (3) The prediction graded. (4) Steps 1 and
2: the runs' tables, the block ratios, median, count below 1, pooled ratio, the order-position means and the reading.
(5) Job 9's Step 3 and this Step 2 side by side: softnodes 2000 against nodes 20000. Then facts, suspicions, "what I
did not do", "what I am not sure about"; every number from a raw file you commit; `git status --short` and `ls -R
forge-combo29/sol2/job10` as the last command before the report commit. Files only under forge-combo29/sol2/ (and
your notes file); no executable, net, book or profile data file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol2-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and workload.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol2_11.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
