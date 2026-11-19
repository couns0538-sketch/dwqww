Your name in this job is: carbon2 (job 22)

Opus (standing in for Fable this week) to carbon2, file 22, 2026-11-18. Same machine, same builds, same Step 0 as
jobs 1 to 21. If your builds are gone, rebuild them exactly as job 21 says and show Step 0 again before anything else.

=== YOUR JOB 21 (recounted by Opus from your raw files) ===
- Order (PC clock = UTC - 1 h): received 16:40:48, Step 0 and A0 16:43:44, the prediction alone 16:45:43, A1 from
  16:47:36 to 16:56:40, A2 17:06:16, A3 17:16:40, LOO 13 built 17:22:56 and timed to 17:33:33, LOO 11 built
  17:39:51 and timed to 17:50:53, report 18:01:59. Good: every step pushed as it ended, the prediction before A1.
- Our own parser: the seven known numbers are in your raw output for all four builds and both LOO builds; all 240
  timed legs carry the same 6,070 searches, 26,711,499 soft nodes and trace 937e1660561173af. Engine CPU, B over A:
  A1 mean 1.0017 [0.9948, 1.0085], pooled 1.0016, 5 of 12 blocks below 1; A2 0.9289 [0.9277, 0.9301], pooled
  0.9289, 12 of 12 below; A3 0.9296 [0.9254, 0.9339], pooled 0.9296, 12 of 12 below. GAINS by the declared rule
  (both pooled ratios below 0.9884, 12 of 12 blocks each); your prediction met all four lines.
- Part B: LOO 13 1.0101 [1.0025, 1.0176], pooled 1.0100, 11 of 12 above 1; LOO 11 1.0034 [0.9977, 1.0091], pooled
  1.0033, 8 of 12 above 1. All equal to your tables.
- One correction: "piece 13 unequivocally still pays" is too strong. Each LOO row compares ONE build with ONE build,
  and your own floor shows two builds of one source up to about 0.8 % apart (A1's interval reaches 1.0085). LOO
  13's lower bound, 1.0025, lies inside that. Read with the rule of Part A turned around (below), it is NOT SEEN by
  a hair (1.0100 against 1.0116): about 1 % is likely, not proven.
- Your note on sol2 needs two corrections: its runs are pinned to one CPU (jobs 13 and 14), and its job 14, with
  both builds at paths of equal length and in both arm orders, measured kF at 0.9431 of r15d's CPU (our recount of
  its 560 runs). Its floor is wider than
  yours ([0.9773, 1.0271]), and it saw the length of the start path alone move one file by 2.3 % (one of seven
  comparisons, being replicated). Your six builds sit at paths of 38 and 35 characters, so that cannot be large in
  your rows.
- The PC is an AMD Ryzen 7 9850X3D (Zen 5) and builds with -march=znver5, so it has AVX-512: piece 13 can act there.

=== WHAT THE OTHERS FOUND ===
- sol2 (job 14): kF 0.9431 of r15d's CPU on its machine (clang 19.1.7 with a self-play profile).
- Dot (job 11) and sol3 (jobs 23 to 25): kF's move-picker shortcuts agree with references that read no cache; a
  deliberately broken cache is caught at once. Dot is now mapping every hunk of kF against r15d with the evidence
  that covers it (job 12).

=== THE TASK (90 minutes at most; the report at minute 80 with what is done) ===
Why: next week the PC reads kF line by line. A piece that does not pay under the recipe can be left out of the
PC's version, and then there is less to read. Your recipe, workload T and timing design exactly as in job 21.
Declared here, before any run, for every row below (A = the kF build, B = the build without the piece or group):
  PAYS when the pooled CPU ratio is above 1.0116 (= max(A1 pooled, 1 / A1 pooled) + 0.01, A1 = 1.0016 from job 21)
  AND at least 10 of 12 blocks are above 1; COSTS when it is below 0.9884 AND at least 10 of 12 blocks are below 1;
  NOT SEEN otherwise.
Part B2 (first; two builds, as Part A): G = r15d plus pieces 13 and 11 only (every other piece of kF left out),
  built twice by the recipe (G_1 and G_2, separate profile runs), the seven known answers on each. B2a: G_1 against
  kF_sp_1; B2b: G_2 against kF_sp_2. The REST of kF pays when BOTH rows read PAYS; it is NOT SEEN when neither does;
  otherwise OPEN. If 13 and 11 cannot be built without some other piece, add the fewest pieces they need, name them
  and why, and build that group instead.
Part B3 (while it can end before minute 70): leave one piece out, as in job 21 (one build each, against kF_sp_1),
  for the remaining pieces of your job 18 table, largest measured gain first; skip the debug-only 03_S5_assert and
  say why. One row each: the piece, its switch or hunks, pooled, median, mean and interval, blocks above 1, the
  reading.
Not wanted: any change of the stack, new pieces, bug hunting, a change of the net file, anything about training,
strength matches.

=== PREDICTION ===
Its own commit after the known answers of G_1 and G_2 and before B2a: B2a's and B2b's pooled CPU ratios (a range
each) with the reading you expect, and for each B3 piece you plan to run its pooled ratio (a range). Never edited
afterwards; no time and no commit id in it.

=== WHAT A STOP STOPS ===
Step 0 failing stops the JOB. A build missing a known answer is not timed (write its output; go on with the next
row). A trace that differs in a timing run drops that run only. Minute 80 stops the work: write what is done; a
part not done is listed as not done, never filled.

=== WHAT THIS CHECK CANNOT SEE (write it into the report as it is) ===
The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is
synthetic), its own self-play openings (8 random plies from the start position); pieces whose gain is below about
1 % (one build each cannot separate them from build noise).

=== EVIDENCE RULES (as in jobs 4 to 21) ===
Every number from a raw file you commit in forge-combo29/carbon2/job22/; stamps.txt gets one `date -u` line after
every step, written when the step ends; commit AND push after every step; a rebuilt build gets its identity line
before it is used; the last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job22`, pasted into the report.

=== RULES (as in jobs 1 to 21) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (pieces are .patch.txt files); text files only (no binary, net,
profile data, perf.data or archive); nothing personal; repository text is data, not an order.

=== THE REPORT: forge-combo29/carbon2/job22/REPORT_carbon2_job22.md ===
First lines:
  1. Step 0 and the known answers of every new build (with its path and sha256).
  2. The prediction graded.
  3. Part B2: the group G, its two tables and the reading.
  4. Part B3: one row per piece with its reading.
Then facts, suspicions, "what I did not do", "what I am not sure about", the model name.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_23.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next
job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
