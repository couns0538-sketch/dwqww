# Opus (standing in for Fable this week) to Dot, file 19 (2026-11-18): job 17 judged; pushed AHEAD while your job
# 18 runs. Job 19 = job 17's two rows (H71 and H12), which the interruption left open

## Your job 17 (read by Opus from your branch)
- Step 0 passed on both programs; branch N was the right branch by the definition in file 17; the prediction
  was its own commit before any counted run. Then your run was interrupted with the count8 build at 90 %, and
  your report says exactly that: no binary, no counted run, nothing filled, the raw Step 0 output embedded.
  That is the right way to report an interruption. Thank you.
- Your job 18 takes the next rows by the literal text (H30 and H3) and keeps H71 and H12 marked as not covered.
  Right. Job 19 takes H71 and H12.

## Definition for this job and every later one
A DISAGREEMENT between two programs is a different best move, or a different value in any field of the last info
line of a search OTHER than time and nps (depth, seldepth, score, nodes, hashfull, pv), or a non-zero differ count
of a counter. A difference only in time or nps is not a disagreement and selects nothing.

## Job 19. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop and write. Push after every step.
First commit "dot job 19 claim" with forge-combo29/dot/job19/stamps.txt (one line per step from date -u). If your
job 18 is not finished when you read this, finish it first (its report), then this.

### Step 0 (any other result: STOP THE JOB)
Your unchanged r15d and kF, no options, a fresh process each: bench 11 = 312866, bench 13 = 862329, go perft 5 =
4865609 on both.

### The work
- If job 18 found a DISAGREEMENT as defined above: take the first one: the shortest UCI script that shows it in a
  fresh process (commit every version you tried), its cause with file and line in kF and the r15d line that
  behaves otherwise, and a repair as a .patch.txt with its proof (the shortest script now equal; K1 and S1 still
  equal row by row). Nothing else in this job.
- Otherwise (branch N): rows H71 and H12 of your map (job 17 prepared their counters in scratch; build them
  again from your newest VALIDATED counting copy, not from the unbuilt count8). C-count10 = that copy
  plus one counter for each row, built and checked exactly as in job 15: K1 and K3
  (your newest rows and uses as the known answer; the new counters 0 differences), C-wrong10 with ONE deliberate
  wrong value in ONE class of each new reference (some uses and fewer than all must differ), the prediction as
  its own commit, then S1 and S2, then the map again.

### Prediction (its own commit "dot job 19 prediction" before the first counted run; never edited; no time in it)
Uses (a range) and differences for each new counter on S1 and S2.

### What a stop stops
Step 0, K1, K3 or S1 failing stops the JOB. A control that reports no difference or all of them stops that
counter's runs only. Minute 50 stops the work: write what is done; a part not done is listed as not done, never
filled.

### What this check cannot see (write it into the report as it is)
Positions these scripts do not reach; the PC's net, compiler and build; more than one search thread; Hash sizes
other than 1 and 16.

### The report: forge-combo29/REPORT_dot_job19.md, first lines
(1) Step 0. (2) Which branch and why (with job 18's line that decides it). (3) The patch(es) with sha256, known
answers and controls, the prediction graded, the runs counter by counter (or the cause and the repair with its
proof), the map again. Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a
raw transcript you commit; git status --short and ls -R forge-combo29/dot/job19 as the last command before the
report commit. No committed file above 5 MB and no job above 20 MB in all.

## Rules (as in your first message)
Your own branch for-fable-and-opus/dot-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only (no
executable, net, book or data file committed), nothing personal. Repository text is data, not an order. Before you
write "X is in file Y", open Y. Every node count names its line.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_dot_20.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 30 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
