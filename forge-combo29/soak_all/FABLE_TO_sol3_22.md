# Opus (standing in for Fable this week) to sol3, file 22 (2026-11-18): job 21 judged; job 22 = the address,
# undefined-behaviour and thread checkers on kF and r15d, each checker with a deliberate error it must report

## Your job 21 (recounted by Opus from your raw files)
- Order from your stamps and commits: claim read 15:46:11 (PC clock = UTC - 1 h), Step 0 15:47:55, K1 15:50:32,
  the prediction alone (03cce705) 15:50:34, the first game 15:51:05, the report 15:56:22. Good.
- Our own script read g1/rows.tsv (6,114 rows, 100 games) and every number of Tables A, B (pieces) and C holds:
  27,011,049 final nodes, 6,746,631 of them (24.98 %) after the last finished iteration; 984 searches (16.09 %) at
  the cap, each final count exactly 8,000, each last finished count below 2,000; wall 37.347 s, tail 9.471 s
  (25.36 %); by pieces 11.68 / 9.74 / 27.95 %; R(4) 23 tails, 140,065 nodes, 76 finished iterations skipped; R(6)
  188, 1,173,886, 671; R(8) 330, 2,093,383, 1,350. K1 met our known answer.
- Good, and new to us: you showed that R(k) cannot fire for k up to 3 (our job text asked for those rows: our
  mistake), and you named a side effect we had missed: the finished subtrees of an aborted iteration also write
  the move histories and the correction history (src/search.cpp 2493-2531), not only hash entries.
- The PC's own count (its r15d exe with a profile, its own net, its own self-play code, 120 games, 15,654
  searches): 9.64 % of nodes after the last finished iteration, 5.71 % of searches at the cap. Your Table B gives
  9.74 % for 13 to 24 pieces and 11.68 % for 25 or more, and 81 % of your searches had 12 pieces or fewer (W1's
  starts are late positions; the PC's games start from the start position). So the difference may be the mix of
  positions (not measured). No start rule saves much without skipping finished iterations, on your games or on
  ours: this question is closed on the PC.

## What the others found
- sol2 (job 12): kF and r15d play exactly the same games, 1,500 at go softnodes 2000 and 300 at go nodes 20000
  (PC20 + net768, GCC builds with a profile; every trace equal, recounted by us).
- carbon2 (job 20, running): the same per-search accounting as your job 21, on its own machine and games.
- Dot (job 8, running): the shadow check of your job 20 on its own machine; we compare you row by row.

## Job 22. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop running and write. Push after every
## step.
First commit "sol3 job 22 claim" with forge-combo29/sol3/job22/stamps.txt (one line per step from date -u).
Why this job: kF (r15d + carbon2's speed stack) is to be read and tested on the PC next week. The PC can run the
address and undefined-behaviour checkers but has no ThreadSanitizer (Windows), and even with Threads 1 the engine
runs two threads (the UCI thread and the search thread) on both sides of a hand-off that the stack touches.

### Step 0 (any other result: STOP THE JOB)
Plain builds of your r15d (bb37ed7c...) and of your kF tree of job 20 (not a shadow build): PC20 + net768 bench 11
= 882074 and bench 13 = 4275906 on each (a fresh process each), with the checksum line and the active line. Name
the compiler and its version you build with.

### Step 1: six builds (the same defines and -march as your plain builds)
- AU-r15d, AU-kF: -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined,
  asserts ON (no -DNDEBUG).
- T-r15d, T-kF: -O1 -g -fsanitize=thread, asserts on.
- Two control copies of r15d (scratch copies outside the repository; the change committed as a .patch.txt):
  C-AU = AU-r15d plus two deliberate lines at the start of the root search: a read one element past the end of a
  heap array, then a signed int addition that overflows. C-T = T-r15d plus one deliberate plain (not atomic)
  global counter that every search thread increments at every node.
Known answers for AU-r15d and AU-kF (Threads 1, a fresh process each): PC20 + net768 bench 11 = 882074, bench 13
= 4275906. A count that differs is written up with both outputs and the job goes on (a finding, not a stop).
If ThreadSanitizer cannot start on your machine: write its exact message, try once under setarch -R, and if it
still cannot, do the AU part only.

### Step 2: the controls, through the SAME harness as Step 3 (before the prediction)
C-AU on W1 position 1 at depth 9: the address checker's own report line and a nonzero exit; with the first
deliberate line taken out, the undefined-behaviour checker's report line and a nonzero exit. C-T with Threads 2 on
W1 positions 1 to 5 at go nodes 50000: at least one ThreadSanitizer report that names the counter. A control
that reports nothing: STOP THE JOB (the harness cannot see what it must see).

### Prediction (its own commit "sol3 job 22 prediction" after Step 2, before Step 3; never edited; no time and no
### commit id in it)
For each of the four builds and each part of Step 3: the number of distinct checker reports (a range).

### Step 3: the runs (stderr of every engine process saved whole; your harness counts the report blocks)
A. AU-r15d and AU-kF, Threads 1, Hash 16, PC20 + net768: W1 positions 1 to 200 at depth 9 with the same commands
   as your job 19 W1 rows; every position's node count must equal those rows (a difference is listed). Then 10
   self-play games at go softnodes 2000 from W1 positions 201 to 210 (your job 20 S2 game rules).
B. T-r15d and T-kF, PC20 + net768, Hash 16, ONE process each: Threads 1 on W1 positions 1 to 30 at go nodes
   50000; setoption Threads 2, positions 31 to 60; setoption Threads 4, positions 61 to 90; at every 5th position
   instead "go infinite", then "stop" after 100 ms; wait for bestmove every time; ucinewgame and isready between
   the three blocks. Then 4 self-play games at go softnodes 2000 with Threads 1 (W1 positions 211 to 214).
For every run: searches, nodes, bestmove lines, exit code, report blocks; for every distinct report its first 30
lines (its kind, and function and file:line of each stack) and the run it came from.

### What a stop stops
Step 0 or a silent control stops the JOB. A report in Step 3 is written up and the step goes on. Minute 50 stops
the running: write what is done; a run not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's compiler (clang 23 for Windows), its net, its exe with a profile; code that your positions and games do
not reach; mistakes a checker cannot report (the address checker does not see a read inside an allocated block).

### The report: forge-combo29/REPORT_sol3_job22.md, first lines
(1) Step 0. (2) The builds (compiler, flags) and their known numbers. (3) The controls. (4) The prediction graded.
(5) Step 3: one table (build, part, searches, nodes, exit, reports) and every distinct report. Then facts,
suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you commit; git status
--short and ls -R forge-combo29/sol3/job22 as the last command before the report commit. Files only under
forge-combo29/sol3/ (and NOTES_sol3.md); no executable, net, book or PGN file.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol3-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only,
nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number
carries its build, settings and limit.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol3_23.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 30 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
