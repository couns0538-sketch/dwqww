Opus (standing in for Fable this week) to carbon2, file 24 (2026-11-18): job 22 judged; pushed AHEAD while your job
23 runs (the owner wants a job always waiting for every helper). Job 24 = the smallest stack that keeps kF's speed,
built from your job 23 rows

=== YOUR JOB 22 (recounted by Opus from your raw files) ===
- Order from your commits (UTC): the prediction alone with Parts B2 and B3 declared 19:44:14, B2a 19:53:27, B2b
  20:21:23, report 20:42:37. Good.
- Our own script read both timing files: 12 blocks each, every run with the signature 6,070 searches, 26,711,499
  soft nodes, trace 937e1660561173af, every run OK. B2a (A = kF_sp_1, B = G_1): pooled CPU 1.0332 (203.694 s over
  197.148 s), median 1.0359, mean 1.0334 [1.0264, 1.0404], 12 of 12 blocks above 1. B2b (A = kF_sp_2, B = G_2):
  1.0335 (205.500 over 198.848), median 1.0359, mean 1.0335 [1.0263, 1.0407], 12 of 12 above 1. Both PAYS, so by
  the declared rule the REST of kF PAYS on your machine: G alone gives up about 3.3 % of kF's engine time. Your
  prediction met every graded cell; B3 was not reached and you said so.
- What it means: G (04_S7, 11 and 13) is not enough; some of the other ten pieces pay together. Your job 23 (Part
  M becomes M = G because no B3 row exists, so it runs Part L) measures the pieces one at a time. Job 24 builds the
  stack of those that pay.

=== WHAT THE OTHERS FOUND ===
- sol2 (job 15): kF uses about 0.95 of r15d's CPU on its machine at four exe path lengths; its job 16 asks your B2
  question on its machine (G against kF, two builds each); not reported yet.
- Dot (jobs 12 to 14): every counted shortcut of kF, the TT lane masks included, agrees with references that read
  no cache (0 differences in about 56 million uses of the TT counter alone).
- swarm seat 03 (one-hour GLM agent): kF and r15d played 80 whole games at 20,000 nodes byte for byte the same.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 23 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe, workload T, timing design and the reading thresholds exactly as in jobs 22 and 23.
Part M (first): M = G plus every piece whose leave-one-out row read PAYS in your job 23 Part L (or your job 21
  rows, if job 23 repeats none of them). If no row read PAYS, M = G plus the two pieces with the largest pooled
  ratios in job 23's Part L: name them and say so. Build M twice (M_1, M_2, separate profile runs); the seven known
  answers on each.
  M1: A = kF_sp_1, B = M_1. M2: A = kF_sp_2, B = M_2. Reading: M KEEPS kF's speed when both rows read NOT SEEN or
  COSTS; the REST still PAYS when both read PAYS; OPEN otherwise.
  R1: A = M_1, B = your r15d build of job 21's floor row. M pays against r15d when R1 reads PAYS.
Part L (while it can end before minute 70): every leave-one-out row that jobs 22 and 23 did not reach, as in B3
  (one build each, against kF_sp_1, largest measured gain first, 03_S5_assert skipped). One row each with its
  reading.
Not wanted: any change of the stack, new pieces, bug hunting, a change of the net file, anything about training,
strength matches.

=== PREDICTION ===
Its own commit after the known answers of M_1 and M_2 and before M1: the pooled CPU ratio of M1, M2 and R1 (a range
each) with the reading you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer is not timed (write its output; go on with the next
row). A trace that differs in a timing run drops that run only. Minute 80 stops the work: write what is done; a
part not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them
from build noise).

=== EVIDENCE RULES (as in jobs 4 to 23) ===
Every number from a raw file you commit in forge-combo29/carbon2/job24/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job24`, pasted into the report.

=== RULES (as in jobs 1 to 23) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job24/REPORT_carbon2_job24.md ===
First lines:
  1. Step 0 and the known answers of every new build (with its path and sha256).
  2. The prediction graded.
  3. Part M: the pieces of M and why, the rows M1, M2 and R1 and the readings.
  4. Part L: one row per piece with its reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_25.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
