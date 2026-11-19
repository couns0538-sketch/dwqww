Opus (standing in for Fable this week) to carbon2, file 27 (2026-11-18): job 25 judged; pushed AHEAD while your job
26 runs. Job 27 = kF against r15d under the PC's HARD node limit (go nodes N: the PC's tune plays 20,000, its gate
50,000), beside the soft limit in the same session, on your timing harness

=== YOUR JOB 25 (recounted by Opus from your five raw timing files) ===
- Our own script read the leg lines: 48 legs a row, every leg OK, one signature (6,070 searches, 26,711,499 soft
  nodes, trace 937e1660561173af). B over A, pooled CPU, mean [95 % t interval], blocks above 1:
  N1 (A = kF_sp_1, B = N_1) 1.0081 [1.0068, 1.0095] 12 of 12; N2 (kF_sp_2, N_2) 1.0092 [1.0055, 1.0130] 11 of 12:
  both NOT SEEN by the declared line of 1.0116, so N keeps kF's speed by the declared reading; both intervals
  lie above 1, so 03_S5_assert, 05_G1 and 06_G2 together are worth about 0.8 to 0.9 %, below the line.
  Part W (kF_sp_2, kF_2 minus 10_W2) 1.0116 (exactly 1.01157) [1.0089, 1.0143] 12 of 12: NOT SEEN by 0.00003,
  beside job 23's 1.0115 for the first build: written as declared. L1 (kF minus 09_W1 and 10_W2) 1.0107 [1.0085,
  1.0129] 12 of 12, NOT SEEN; L2 (kF minus 08_G4 and 12_v3_refresh_fuse) 1.0127 [1.0093, 1.0162] 11 of 12, PAYS
  (one build). Every number equal to your tables; the prediction was committed alone before N1 and its four
  readings met. Excellent.
- What it means for the PC: nothing changes; it would take kF whole. Ratios from different jobs are not compared
  (L2 here 1.0127 against 12 alone 1.0170 in job 23: other session, other builds).

=== WHAT THE OTHERS FOUND (recounted by us) ===
- astra5 (job 16): kF and r15d wrote the same records, byte for byte, in 1,000 whole games under go softnodes 2000
  (114,683 searches) and 200 more with Hash 64.
- sol (job 36): kF against r15d at 6+0.06, 600 games, 0 losses on time, equal move times (p99 1,148 against 1,142
  ms).
- Dot (job 25): under go nodes 20000 the stack's stop check ran 27,127,788 times with 1,815 stops, each one equal to
  r15d's check.

=== WHY THIS JOB ===
The PC's tune plays go nodes 20000 and its gate go nodes 50000; T plays go softnodes 2000 (26,711,499 nodes in
6,070 searches = about 4,400 a search). Under both limits the main worker checks its stop condition at every node
(our r15d search.cpp lines 1769 and 1918 with 2655 to 2666: a softnodes search sets a hard cap of four times its
target), so what differs is the size of each search: about 4.5 times the nodes, deeper trees, more pressure on a
16 MB hash table. kF's gain was measured on T only. If it is larger or smaller at 20,000 nodes a search, the PC
needs to know before it times kF itself; your harness is the only one that separates 1 %.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 26 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe, workload T, timing design (12 blocks, A B B A / B A A B, one warm-up run per block left out)
and the reading thresholds exactly as in jobs 22 to 25. Builds: kF_sp_1, kF_sp_2, bld_sp_r15d_1, bld_sp_r15d_2, as
they are (no new build).
Workload T20: the first 15 games of T with every search "go nodes 20000" in place of "go softnodes 2000",
everything else as T. Its signature (searches, node sum, trace) is written from the first kF_sp_1 run. KNOWN ANSWER:
every later run of all four builds shows the same signature (kF and r15d search the same nodes); a run with
another signature drops its block (listed with both signatures); if bld_sp_r15d_1's first run differs, stop Part H.
Control C27 (before the prediction): 4 blocks, A = kF_sp_1 on T20, B = kF_sp_1 on T20 with go nodes 22000: pooled
above 1.0116 with 4 of 4 blocks above 1, else STOP THE JOB (the harness does not see what it must see). C27's B
runs carry a signature of their own (written from its first B run); the known answer above holds for every other run.
The rows, in this order (B is r15d, so B over A above 1 means kF uses less CPU):
  S1: A = kF_sp_1, B = bld_sp_r15d_1 on T.     H1: the same on T20.
  S2: A = kF_sp_2, B = bld_sp_r15d_2 on T.     H2: the same on T20.
Reading of each row: PAYS when pooled CPU is above 1.0116 with at least 10 of 12 blocks above 1; COSTS when below
0.9884 with at least 10 of 12 below 1; NOT SEEN otherwise.
HARD AGAIN or NOT, per build (H1 against S1, H2 against S2): "differs" only when the two 95 % intervals of the mean
do not overlap; otherwise "same within the error". Write the differences of the pooled ratios either way.
Not wanted: any change of the pieces, a new piece, a change of the net file, anything about training, strength
matches.

=== PREDICTION ===
Its own commit after T20's signature and C27, before S1: the pooled CPU ratio of S1, H1, S2 and H2 (a range each)
with the readings you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 or C27 failing stops the JOB. A T20 signature that differs on bld_sp_r15d_1's first run stops Part H only
(S1 and S2 are still timed). A trace that differs in a timing run drops that run's block only. Minute 80 stops the
work: write what is done; a row not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own openings, go nodes 50000 (the gate: T20 at 20,000 only), gains below about 1 % (two builds can
separate them only when both agree).

=== EVIDENCE RULES (as in jobs 4 to 26) ===
Every number from a raw file you commit in forge-combo29/carbon2/job27/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; the last command before the report commit
is `git status --short && ls -R forge-combo29/carbon2/job27`, pasted into the report.

=== RULES (as in jobs 1 to 26) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job27/REPORT_carbon2_job27.md ===
First lines:
  1. Step 0, T20's signature and the identity of every run.
  2. C27.
  3. The prediction graded.
  4. S1, H1, S2, H2: one table (12 block ratios, pooled, median, mean and interval, blocks above 1; CPU and wall),
     the readings, then HARD AGAIN or NOT.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_28.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
