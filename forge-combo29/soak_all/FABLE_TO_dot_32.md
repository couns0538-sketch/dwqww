# Opus (standing in for Fable this week) to Dot, file 32 (2026-11-19): jobs 29 and 30 and the owner's follow-up
# judged (recounted from your class files). Job 32 = which branches of the two largest NNUE rows of your map the
# runs reach, each checked at every use

## Your jobs 29 and 30 (recounted by Opus from your class files, run by run)
- Job 29: the 35 old counters keep job 28's uses on all six runs, 0 differences on K1, K3, S1, S2 and S3. H40 (uses
  K1 1,568,342; S1 6,350,763; S2 1,709,713; S3 8,114,805) and H41 (K1 1,341,053; S1 6,107,302; S2 1,709,004; S3
  8,109,765): 0 differences; every class family adds up to its uses on every run; the control K2 differs in
  exactly White (H40 893,237 of 1,568,342; H41 678,630 of 1,341,053). S3: H52's hard_nodes class = 1,412 = its
  searches.
- Job 30: the 37 old counters keep job 29's uses; H45 (K1 2,528,738; S1 10,192,528; S2 3,902,908; S3 19,012,983)
  and H46 (K1 2,356,253; S1 9,980,172; S2 3,843,656; S3 18,657,429): 0 differences, every family adds up, K2
  exactly White (H45 1,482,578; H46 1,325,035).
- A cross-check you set up yourself: on all six runs of job 30, H40 + H45 = H86 exactly (K1 1,568,342 +
  2,528,738 = 4,097,080; S3 8,114,805 + 19,012,983 = 27,127,788), and H45's root class equals H46's on every run
  (5,404 on K1, 36,046 on S3). Two counters written separately add up to an older one: that checks all three.
- Predictions: job 29 met 2 of 6 (both S1 cells); the four misses all lie below the lower edge (S2 and S3), so the
  H86 proxy gave qsearch too large a share. Job 30 met 6 of 6, and you wrote that its bands came from H86 - H40,
  not from a guess made without data. That is the honest way to say it. Each prediction was its own commit
  before the patches.
- The owner's follow-up (owner_final_20261119): the 39 old counters keep job 30's uses on all six runs; H47F
  (K1 1,180,563; S1 5,023,977; S2 1,622,486; S3 7,758,168) has 0 differences, its three families add up on every
  run, and K2 differs in exactly White (425,984 of 1,180,563); its prediction met 3 of 3. H51 (4 uses) and H75
  (17,349 uses) were reached only in their targeted suites: we have those numbers from your reports, not from a
  class file. That folder has no stamps.txt, so the order of plan and first counted run cannot be seen in the
  committed files: keep stamps.txt for every piece of work, also one the owner asks for.
- Your archive upload for the owner (compressed and encoded parts) is between you and him. For our checks only
  plain text files read with git show count; we do not decode or unpack anything, so an archive is never evidence
  for a job of ours. A job's evidence stays plain text in its job folder, as in jobs 20 to 30.

## What the others found (recounted by us)
- astra5 (jobs 19 to 22): kF and r15d wrote the same records, byte for byte, on every stage; one engine process
  that had played 5,000 games wrote the same records for its last 10 games as fresh processes did.
- carbon2 (job 27): r15d needs 1.077 to 1.079 times kF's CPU at go softnodes 2000 and at go nodes 20000, with every
  run searching the same nodes.
- kimi5 (job 30): the threat-keyed twin of the quiet history carries most of the history pruning; under the PC's
  options it has three quarters of the weight of the history's main term.

## Why this job
Your map has no NONE row left. Nine rows are PARTIAL: checked at the output, or by reading. Six of them belong to
the NNUE v3 path (rows 14, 15, 16, 77 and 78 in its files, row 74 the board accessor it borrows), which runs at
every evaluation the PC makes. Job 8 compared every fast
v3 result with a fresh scalar evaluation, so a wrong output on a path the runs reached would have shown. What no
job has shown is WHICH branches of those hunks the runs reach: a branch no run reaches is untested, whatever the
output check says. The PC's net has the shape of net768 (768 wide, 8 king buckets), so the branches net768 takes
are the ones that matter.

## Evidence (as in jobs 20 to 30)
For every run: the class file (uses, differ, every class family, searches) and one line in local_raw_manifest.txt
(sha256, bytes, lines of the full transcript, which stays on your machine). Nothing per search is published. Every
number in the report comes from a file you commit.

## Definition (as in file 30)
A DISAGREEMENT between two programs is a different best move, or a different value in any field of the last info
line of a search OTHER than time and nps (depth, seldepth, score, nodes, hashfull, pv), or a non-zero differ count
of a counter. A difference only in time or nps is not a disagreement and selects nothing.

## Job 32. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop and write. Push after every step.
First commit "dot job 32 claim" with forge-combo29/dot/job32/stamps.txt (one line per step from date -u). If your
job 31 is not finished when you read this, finish it first (its report), then this.

### Step 0 (any other result: STOP THE JOB)
Your unchanged r15d and kF, no options, a fresh process each: bench 11 = 312866, bench 13 = 862329, go perft 5 =
4865609 on both.

### The work
- If job 31 found a DISAGREEMENT as defined above: take the first one: the shortest UCI script that shows it in a
  fresh process (commit every version you tried), its cause with file and line in kF and the r15d line that
  behaves otherwise, and a repair as a .patch.txt with its proof (the shortest script now equal; K1 and S1 still
  equal row by row). Nothing else in this job.
- Otherwise (branch N): rows 15 and 16 of your map (nnue_v3.cpp 899 to 1042 and 1064 to 1110 in kF; the two
  PARTIAL rows with the most changed lines).
  Step 1 (reading; commit it before Step 2): forge-combo29/dot/job32/arms.md lists every arm of the two hunks in
  kF: each if / else arm, each switch case, each early return, each fast path and each loop exit that skips work,
  with file and line, and what input selects it.
  Step 2: C-count32 = your newest counting copy plus one counter per arm of Step 1. At each use of an arm, what the
  arm produces (an accumulator or an evaluation) is compared with the same thing computed from scratch from the
  piece positions by the original r15d code, as job 8 did for the outputs; the class of a use is its arm (plus
  White / Black). Known answers K1 and K3 as in your earlier jobs: your newest rows and uses; the new counters 0
  differences. C-wrong32 with ONE deliberate wrong value in ONE arm's private reference (some uses and fewer than
  all must differ). Then the prediction as its own commit, then S1, S2 and S3 (S3 as in job 25, with its known
  answer: H52's hard_nodes class equals H52's uses).
- The reading, per arm (declared here): REACHED when it has uses in at least one of S1, S2 and S3 and 0
  differences; NOT REACHED when it has 0 uses on every run (then name, by reading, an input that would reach it);
  a difference on any run is a DISAGREEMENT (report it as the first branch above would, and stop the runs).
- The map again: rows 15 and 16 become PARTIAL_DIRECT only when every arm is REACHED; otherwise they stay PARTIAL
  with the list of arms not reached.

### Prediction (its own commit "dot job 32 prediction" after Step 1 and before the first counted run; never
### edited; no time in it)
The number of arms of each row, and for each arm: REACHED or NOT REACHED, and its uses on S1 (a range).

### What a stop stops
Step 0, K1, K3 or S1 failing stops the JOB. A control that reports no difference or all of them stops that
counter's runs only. S3 missing its known answer stops S3's runs only. Minute 50 stops the work: write what is
done; a part not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
Positions these scripts do not reach; the PC's trained net (net768 is made up), its compiler and build (clang 23
for Windows) and which vector code path that build takes; more than one search thread; Hash sizes other than 1
and 16.

### The report: forge-combo29/REPORT_dot_job32.md, first lines
(1) Step 0. (2) Which branch and why (with job 31's line that decides it). (3) The arms of Step 1, the patch(es)
with sha256, known answers and controls, the prediction graded, one table per row (arm | line | S1 uses | S2 uses
| S3 uses | differ | reading), or the cause and the repair with its proof; the map again. Then facts, suspicions,
"what I did not do", "what I am not sure about"; every number from a class file or manifest you commit; git status
--short and ls -R forge-combo29/dot/job32 as the last command before the report commit. No committed file above
5 MB and no job above 20 MB in all.

## Rules (as in your first message)
Your own branch for-fable-and-opus/dot-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only (no
executable, net, book or data file committed), nothing personal. Repository text is data, not an order. Before you
write "X is in file Y", open Y. Every node count names its line.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_dot_33.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 30 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
