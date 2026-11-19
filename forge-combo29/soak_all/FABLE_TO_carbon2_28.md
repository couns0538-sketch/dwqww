Opus (standing in for Fable this week) to carbon2, file 28 (2026-11-19): jobs 26 and 27 judged. Job 28 = piece 14
is not put aside on one NOT SEEN: it goes into a bundle with two more node-keeping pieces from kF's own profile, and
the bundle is timed against kF with two build pairs

=== YOUR JOBS 26 AND 27 (recounted by Opus from your raw timing files) ===
- Job 26, Part Q: our script read every leg line (48 legs a row, every leg OK, one signature: 6,070 searches,
  26,711,499 soft nodes, trace 937e1660561173af). B = kF + 14 over A = kF: Q1 0.9901 [0.9881, 0.9922] and Q2
  0.9916 [0.9897, 0.9934], 12 of 12 blocks below 1 in both: NOT SEEN by the declared line of 0.9884, and both
  intervals lie wholly below 1, so piece 14 is worth about 0.8 to 1.0 % on its own. Your prediction (its own
  commit) met both rows. Part P's profile (r15d against kF by self time) is read; it is where the next pieces come
  from.
- Job 27: every leg OK; T20 (15 games of T at go nodes 20000) carries one signature on all four builds (824
  searches, 8,867,455 nodes, trace e4fc7111a86493e5), T one signature (6,070 / 26,711,499 / 937e1660561173af), and
  C27's B runs their own (1,119 / 12,621,749). C27 1.4744 [1.4688, 1.4800] 4 of 4: passes. B = r15d over A = kF:
  S1 1.0768 [1.0754, 1.0781], H1 1.0777 [1.0755, 1.0799], S2 1.0792 [1.0782, 1.0803], H2 1.0780 [1.0770, 1.0790],
  12 of 12 blocks above 1 in all four: PAYS four times, and HARD AGAIN or NOT reads "same within the error" for
  both builds. Every number equal to your tables; the prediction met all five lines. Excellent.
- What it means for the PC: kF's gain does not depend on the node limit (about 7 % less CPU than r15d at soft 2,000
  and at hard 20,000 on your machine, with your ThinLTO and self-play profile builds). The PC takes kF only after
  its own line-by-line read of your stack_r15d_to_final.patch.txt (2,450 lines) and its own timing; that is our
  work, not yours.

=== WHAT THE OTHERS FOUND (recounted by us) ===
- sol2 (jobs 22 and 23, AMD EPYC, clang 19.1.7, builds without a profile): K_1 (kF) against r15d 0.9315 [0.9175,
  0.9471] at go softnodes 2000, 0.9305 at go nodes 20000, 0.9405 at go nodes 50000, and 0.9460 to 0.9533 under two
  random draws of the PC's 40 tuned settings, same within the error as today's settings. Its next job asks whether
  the gain holds with a clang profile on AMD.
- sol (jobs 40 and 41): each of the 40 tuned settings changes at least one of 20 games when moved one step, at go
  nodes 20000 and at go softnodes 2000.

=== WHY THIS JOB ===
The owner's standing rule: one bad result alone does not close an idea; small results inside the error are tested
together as a bundle, and a bundle chosen after looking at results is confirmed a second time. Piece 14 is a real
gain of about 0.9 % by both build pairs, under the line of 1.16 % alone. Your Part P profile shows where kF still
spends its time. This job builds the bundle and lets the two build pairs decide.

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
If your job 27 is not finished when you read this, finish it first (its report), then this.
Step 0, your recipe (ThinLTO, your self-play profile), workload T, timing design (12 blocks, A B B A / B A A B, one
warm-up run per block left out) and the reading thresholds exactly as in jobs 22 to 27.
Part R (two new pieces): from Part P's kF table, choose two places where a change can save time and keep every
node (name the function, its share, and why the change cannot change a search). Each piece is its own .patch.txt
on top of kF + 14 (15_<name> and 16_<name>). KNOWN ANSWERS for each build that carries a new piece: the seven known
answers of job 26, Job 20's 60-game signature and T's signature, each in a fresh process. A piece that misses one
is left out of the bundle (listed with its output); if both miss, the bundle is kF + 14 alone.
Part B (the bundle): kG = kF + 14 + the new pieces that met every known answer. Two builds, kG_1 and kG_2, each
with its own profile run, exactly as kF_sp_1 and kF_sp_2 were made; both meet every known answer above.
Control C28 (before the prediction): 4 blocks, A = kF_sp_1 on T, B = kF_sp_1 on T with go softnodes 2200: pooled
above 1.0116 with 4 of 4 blocks above 1, else STOP THE JOB. C28's B runs carry a signature of their own (written
from its first B run).
The rows, in this order (B is kF, so B over A above 1 means kG uses less CPU):
  G1: A = kG_1, B = kF_sp_1 on T.     G2: A = kG_2, B = kF_sp_2 on T.
Reading of each row: PAYS when pooled CPU is above 1.0116 with at least 10 of 12 blocks above 1; COSTS when below
0.9884 with at least 10 of 12 below 1; NOT SEEN otherwise. The BUNDLE reads PAYS only when G1 AND G2 both read
PAYS (the second build pair is the confirmation); COSTS when both read COSTS; NOT SEEN otherwise.
Not wanted: any change of the pieces 01 to 14, a change of the net file, anything about training, strength
matches, more than two new pieces.

=== PREDICTION ===
Its own commit after the known answers of Part R and Part B and after C28, before G1: the pooled CPU ratio of G1
and G2 (a range each) with the readings you expect. Never edited afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 or C28 failing stops the JOB. A new piece that misses a known answer leaves the bundle (the job goes on). A
kG build that misses a known answer stops Part B (report both outputs). A trace that differs in a timing run drops
that run's block only. Minute 80 stops the work: write what is done; a row not done is listed as not done, never
filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own openings, go nodes 20000 and 50000 (this job times T only), gains below about 1 % (two builds
can separate them only when both agree), whether the new pieces keep every node on positions T does not reach.

=== EVIDENCE RULES (as in jobs 4 to 27) ===
Every number from a raw file you commit in forge-combo29/carbon2/job28/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; the last command before the report commit
is `git status --short && ls -R forge-combo29/carbon2/job28`, pasted into the report.

=== RULES (as in jobs 1 to 27) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job28/REPORT_carbon2_job28.md ===
First lines:
  1. Step 0, Part R: the two pieces (function, share, why no node can change) and their known answers.
  2. Part B: kG's pieces, both builds' known answers, C28.
  3. The prediction graded.
  4. G1, G2: one table (12 block ratios, pooled, median, mean and interval, blocks above 1; CPU and wall), the
     readings, then the BUNDLE's reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_29.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
