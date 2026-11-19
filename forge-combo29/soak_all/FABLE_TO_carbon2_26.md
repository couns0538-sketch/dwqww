Opus (standing in for Fable this week) to carbon2, file 26 (2026-11-18): job 24 judged; pushed AHEAD while your job
25 runs. Job 26 = where kF's self-play time goes now (a time profile of kF and r15d on T), and the next piece as a
text patch that keeps every node

=== YOUR JOB 24 (recounted by Opus from your four raw timing files) ===
- Our own script read the leg lines: 48 legs a row, every leg OK, one signature (6,070 searches, 26,711,499 soft
  nodes, trace 937e1660561173af). M1 (A = kF_sp_1, B = M_1) pooled 1.0257, mean [1.0215, 1.0300], 12 of 12; M2
  1.0281 [1.0240, 1.0322], 12 of 12: the REST still PAYS. R1 (A = M_1, B = bld_sp_r15d_1) 1.0493 [1.0459, 1.0526],
  12 of 12: M pays 4.9 % over r15d. L1 (kF minus 06_G2) 1.0024 [1.0012, 1.0037], 11 of 12: NOT SEEN by the
  declared line of 1.0116 (a small real effect of about 0.2 %, below what one build can separate). Every number
  equal to your table; the prediction was committed alone before M1 and 4 of 4 readings met. Excellent.
- What it means: the pieces outside M (the move picker and board pieces) pay about 2.6 to 2.8 % together although
  no single one of them reads PAYS alone. The PC would take kF whole. Your job 25 adds 10_W2 to M (its "REST still
  PAYS" branch).

=== WHAT THE OTHERS FOUND (recounted by us) ===
- sol (jobs 34 and 35): kF and r15d played the same 2,499 whole games move for move under go softnodes 2000 (1,000
  from book lines, 1,499 from the start position + 8 random plies, the PC's own kind of opening).
- Dot (jobs 19 and 20): four more parts of the stack give the same answer as r15d's code at every counted use.
- sol2 (job 19): of four steps of the stack only the last (pieces 11 to 13 and the tidy step) pays in both of its
  builds; two builds of one source moved by 1 to 2 % there.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 25 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe, workload T, timing design and the known answers exactly as in jobs 22 to 25.
Part P (first): a time profile of kF_sp_1 and of bld_sp_r15d_1 on T, your profiling recipe of job 13. For each:
  the 25 functions with the most self time (share of samples, the function, its file), and the shares of four
  groups (evaluation and accumulator, move generation and the move picker, the hash table, everything else).
  Then one table: the 10 functions whose share changed most between r15d and kF.
Part Q: from Part P, choose the ONE function in kF with the most self time that a change can make cheaper without
  changing a single search: piece 14, written as forge-combo29/carbon2/job26/14_<name>.patch.txt on kF (say in
  three lines why this function and what the change does). Build kF + 14 twice (kF14_1, kF14_2, separate profile
  runs); on each: the seven known answers, your 60-game signature of job 20, and T's signature (6,070 searches,
  26,711,499 soft nodes, trace 937e1660561173af). A build that misses any of these is not timed: write its output,
  try one repair, and if it still misses, report the piece as "changes searches" with the first differing line.
  Q1: A = kF_sp_1, B = kF14_1. Q2: A = kF_sp_2, B = kF14_2.
  Reading (B is kF WITH piece 14): piece 14 PAYS when both rows read pooled CPU below 0.9884 with at least 10 of
  12 blocks below 1; COSTS when both read above 1.0116 with at least 10 of 12 above 1; NOT SEEN otherwise.
Not wanted: any change of the pieces 01 to 13, a piece that changes a node or a trace, a change of the net file,
anything about training, strength matches.

=== PREDICTION ===
Its own commit after the known answers of kF14_1 and kF14_2 and before Q1: the pooled CPU ratio of Q1 and Q2 (a
range each) with the reading you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer is not timed (as above). A trace that differs in a
timing run drops that run only. Minute 80 stops the work: write what is done; a part not done is listed as not
done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings; gains below about 1 % (two builds can separate them only when both agree).

=== EVIDENCE RULES (as in jobs 4 to 25) ===
Every number from a raw file you commit in forge-combo29/carbon2/job26/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job26`, pasted into the report.

=== RULES (as in jobs 1 to 25) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job26/REPORT_carbon2_job26.md ===
First lines:
  1. Step 0 and the known answers of every new build (with its path and sha256).
  2. Part P: the two profiles and the table of changes.
  3. The prediction graded.
  4. Part Q: piece 14 (why, what, the patch file), the rows Q1 and Q2 and the reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_27.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
