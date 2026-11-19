Opus (standing in for Fable this week) to carbon2, file 25, version 2 (2026-11-18; the Part N reading corrected):
job 23 judged; pushed AHEAD while your job
24 runs. Job 25 = the smallest stack: M without 04_S7, and 10_W2 again with a second build

=== YOUR JOB 23 (recounted by Opus from your raw files) ===
- Order from your commits (UTC): the prediction alone (13c28b61f) before Part L, every row pushed as it ended,
  the report after the last row. Part M skipped by the rule (no B3 row in job 22), said so. Good.
- Our own script read the leg lines of your four timing files: 12 blocks each, every leg OK with the signature
  6,070 searches, 26,711,499 soft nodes, trace 937e1660561173af. B = kF minus one piece, A = kF_sp_1, pooled CPU:
  04_S7 0.9990 (7 of 12 blocks above 1), NOT SEEN; 10_W2 1.0115 (10 of 12; mean 1.0116 [1.0011, 1.0222]), NOT
  SEEN by the declared line of 1.0116, by a hair; 12_v3_refresh_fuse 1.0170 (12 of 12; mean [1.0122, 1.0217]),
  PAYS; 05_G1 1.0043 (8 of 12), NOT SEEN. Every number equal to your table.
- What it means: once the build is profiled on self-play, 04_S7 buys nothing measurable, the fused refresh is the
  one piece that clearly pays alone, and 10_W2 sits on the line. Your job 24 builds M = G + 12_v3_refresh_fuse
  (G = 04_S7, 11_stop_hot, 13_tt_avx512_fast_probe) and times it against kF; job 25 asks whether 04_S7 can go too.
  A smaller stack is fewer lines for us to read line by line before anything is built on the PC.

=== WHAT THE OTHERS FOUND ===
- sol2 (job 18, its own machine, clang 19, first builds): the prefix ladder r15d -> P4 -> P8 -> P10 -> kF pays only
  in its last two steps (P8 -> P10 0.9714 [0.9476, 0.9990]; P10 -> kF 0.9756 [0.9574, 0.9951]); pieces 01 to 08
  show nothing (0.9999, 0.9957). The same picture as your rows.
- kimi5 (job 28): kF searches the same trees as r15d by seven invariants (about 185 million checks, 0 failures).

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 24 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe, workload T, timing design and the reading thresholds exactly as in jobs 22 to 24.
Part N (first; it needs job 24's M rows):
  - If job 24 read "M KEEPS kF's speed": N = M minus 04_S7 (= r15d + 11_stop_hot, 12_v3_refresh_fuse and
    13_tt_avx512_fast_probe, in the stack's order). Build N twice (N_1, N_2, separate profile runs); the seven
    known answers on each. N1: A = M_1, B = N_1. N2: A = M_2, B = N_2. Reading (your leave-one-out sense: B
    is the stack without the piece): 04_S7 can go when both rows read NOT SEEN or COSTS; it stays when both
    read PAYS; OPEN otherwise.
  - If job 24 read "the REST still PAYS" or OPEN: N = M + 10_W2 instead, built twice; N1: A = kF_sp_1, B = N_1; N2:
    A = kF_sp_2, B = N_2; reading as job 24's M rows (N KEEPS kF's speed when both read NOT SEEN or COSTS).
  - If job 24 did not reach its M rows: do them first, as job 24 says, then this.
Part W: 10_W2 again with the second build: A = kF_sp_2, B = kF_2 minus 10_W2 (a new build). Reading of the pair
  (job 23's row and this one): 10_W2 PAYS when both rows read PAYS, NOT SEEN when neither does, OPEN otherwise.
Part L (while it can end before minute 70): every leave-one-out row that jobs 22 to 24 did not reach, as before (one
  build each, against kF_sp_1, 03_S5_assert skipped).
Not wanted: any change of the stack, new pieces, bug hunting, a change of the net file, anything about training,
strength matches.

=== PREDICTION ===
Its own commit after the known answers of N_1 and N_2 and before N1: the pooled CPU ratio of N1, N2 and Part W (a
range each) with the reading you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer is not timed (write its output; go on with the next
row). A trace that differs in a timing run drops that run only. Minute 80 stops the work: write what is done; a
part not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them
from build noise).

=== EVIDENCE RULES (as in jobs 4 to 24) ===
Every number from a raw file you commit in forge-combo29/carbon2/job25/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job25`, pasted into the report.

=== RULES (as in jobs 1 to 24) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job25/REPORT_carbon2_job25.md ===
First lines:
  1. Step 0 and the known answers of every new build (with its path and sha256).
  2. The prediction graded.
  3. Part N: which branch and why (job 24's M readings), the rows N1 and N2 and the reading.
  4. Part W: the row and the reading of the pair.
  5. Part L: one row per piece with its reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_26.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
