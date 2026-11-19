Opus (standing in for Fable this week) to carbon2, file 23 (2026-11-18): pushed AHEAD while your job 22 runs (the
owner wants a job always waiting for every helper); job 22 is judged in the head of the file after its report.
Job 23 = the smallest stack that keeps kF's speed: M = your group G plus every piece that PAYS in your job 22 B3

=== WHY ===
Next week the PC reads kF line by line. Job 22 asks which pieces pay one at a time; job 23 builds the stack of only
those and asks whether it keeps kF's speed. If it does, the PC reads M and leaves the rest out.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 22 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe, workload T, timing design and the reading thresholds exactly as in job 22 (PAYS above 1.0116
with at least 10 of 12 blocks above 1; COSTS below 0.9884 with at least 10 of 12 blocks below 1; NOT SEEN
otherwise; in every row A is the larger stack, B the smaller one).
Part M (first): M = your job 22 group G (with the pieces it needed) plus every piece whose job 22 B3 row read
  PAYS. Name the pieces and their order. If no B3 row read PAYS, M = G: say so, skip Part M and go to Part L.
  Build M twice by the recipe (M_1, M_2, separate profile runs); the seven known answers on each.
  M1: A = kF_sp_1, B = M_1. M2: A = kF_sp_2, B = M_2. Reading: M KEEPS kF's speed when both rows read NOT SEEN or
  COSTS; the REST still PAYS when both read PAYS; OPEN otherwise.
  R1: A = M_1, B = your r15d build of job 21's floor row (r15d with nothing of kF). M pays against r15d when R1
  reads PAYS.
Part L (while it can end before minute 70): every leave-one-out row your job 22 B3 did not reach, as in B3 (one
  build each, against kF_sp_1, largest measured gain first, 03_S5_assert skipped). One row each with its reading.
Not wanted: any change of the stack, new pieces, bug hunting, a change of the net file, anything about training,
strength matches.

=== PREDICTION ===
Its own commit after the known answers of M_1 and M_2 and before M1 (or before Part L when M = G): the pooled CPU
ratio of M1, M2 and R1 (a range each) with the reading you expect. Never edited afterwards; no time and no commit id
in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer is not timed (write its output; go on with the next
row). A trace that differs in a timing run drops that run only. Minute 80 stops the work: write what is done; a
part not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them
from build noise).

=== EVIDENCE RULES (as in jobs 4 to 22) ===
Every number from a raw file you commit in forge-combo29/carbon2/job23/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job23`, pasted into the report.

=== RULES (as in jobs 1 to 22) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job23/REPORT_carbon2_job23.md ===
First lines:
  1. Step 0 and the known answers of every new build (with its path and sha256).
  2. The prediction graded.
  3. Part M: the pieces of M, the rows M1, M2 and R1 and the readings.
  4. Part L: one row per piece with its reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_24.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
