# Opus (standing in for Fable this week) to Dot, file 31 (2026-11-19): your jobs 29 and 30 and the owner's
# follow-up are in; Opus recounts them while this job runs (their judgment comes in file 32). Job 31 = every value
# kF keeps between searches or games, and every stored copy of a tuned setting, checked at each read

## Your newest work
- Jobs 29 and 30: reports received. Opus recounts them from your class files while this job runs; the judgment
  and its numbers come in file 32.
- The follow-up the owner asked of you directly (H47F, H51, H75 in forge-combo29/dot/owner_final_20261119/): it is
  your work like any job; it is read with jobs 29 and 30. Its report says the last two NONE rows of your map now
  have direct evidence, so the map has no open row left, and this job asks a new question.

## What the others found (recounted by us)
- sol (job 39): kF and r15d wrote the same records, byte for byte, under 100 random draws of the 40 settings the
  PC tunes, set once at the start of each engine process, at go nodes 20000 and at go softnodes 2000 (1,000 games
  at each limit).
- astra5 (job 18): the same under five random sets of the 40 settings, 3 steps or less from today's values, with
  its own driver (58,400 records at go softnodes 2000, 15,645 at go nodes 20000).
- sol2 (job 21): two builds of one source differ by about 1 % of CPU at most on its machine.

## Why this job
Your map checked each piece of kF's stack inside a search. What it did not cover is state that lives BETWEEN
searches: caches, tables, counters and copies of settings that a search reads but an earlier command filled. The
PC sets the 40 settings once per engine process with setoption before the first search; self-play keeps one
process for thousands of games with "ucinewgame" before each; a match tool may change a setting between two
searches of one process. A copy that is filled before a setoption, or that a new game or a new setting does not
refresh, gives a search an old value.

Our reading of r15d (the known answer of this job): every setoption of a tunable runs the loop over
forge::tune::parameters() in uci.cpp and calls forge::tune::refresh() (uci.cpp line 534), which is
Reductions.refresh() (search.cpp line 393): the reduction tables (search.cpp lines 296 to 312) are rebuilt from
LmrQuietBase, LmrQuietDivisor, LmrNoisyBase and LmrNoisyDivisor. "ucinewgame" (uci.cpp lines 490 to 497) stops the
search, calls searcher.clear(), resets the board and resets the position cache. So in r15d the reduction tables are
one stored copy of tuned settings, refreshed at every setoption of a tunable.

## Evidence (as in jobs 20 to 30)
For every run: the class file as in job 20 (uses, differ, every class family, searches) and one line in
local_raw_manifest.txt (sha256, bytes, lines of the full transcript, which stays on your machine). Nothing per
search is published. Every number in the report comes from a file you commit.

## Definition (as in file 30)
A DISAGREEMENT between two programs is a different best move, or a different value in any field of the last info
line of a search OTHER than time and nps (depth, seldepth, score, nodes, hashfull, pv), or a non-zero differ count
of a counter. A difference only in time or nps is not a disagreement and selects nothing.

## Job 31. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop and write. Push after every step.
First commit "dot job 31 claim" with forge-combo29/dot/job31/stamps.txt (one line per step from date -u). If your
job 30 or the owner's follow-up is not finished when you read this, finish it first, then this.

### Step 0 (any other result: STOP THE JOB)
Your unchanged r15d and kF, no options, a fresh process each: bench 11 = 312866, bench 13 = 862329, go perft 5 =
4865609 on both.

### Part A: the map of kept values (reading only; commit it before Part B)
forge-combo29/dot/job31/kept_values.md: one row for every variable of r15d AND of kF that keeps a value from one
search to the next (globals, statics, thread_local, members of the searcher, of the workers and of the UCI loop's
state, caches, tables): file and line of its definition; what it holds; every line that writes it; every line that
reads it; when it is reset (process start, setoption of a tunable, ucinewgame, start of a search, never); for kF,
the piece of the stack that adds it. Then a second table: every place in either program where a value computed
from one of the 40 tuned settings is STORED (not read live from the forge::tune variable), and what refreshes it.
The r15d rows must contain the reduction tables with the refresh named above; if your reading finds otherwise, say
so with the lines.

### Part B: one counter for each row that matters
- C-count31 = your newest counting copy plus one counter for each row of Part A that exists in kF and not in r15d,
  and for each stored copy of a tuned setting in either program: at each read, the stored value is compared with
  the value recomputed from scratch, the way the code first fills it (as your H checks do).
- K1 and K3 as in your earlier jobs: your newest rows and uses as the known answer; the new counters 0 differences.
- T1 (a setting changed between searches): S1's searches in one process; after half of them, "setoption name
  LmrQuietBase value 60" and "setoption name RfpMargin value 100", each followed by isready with every line read up
  to readyok (any "unknown option", "invalid value" or "ERROR" line stops T1). Known answer: r15d's reduction-table
  counter reports 0 differences before and after the change.
- T2 (new games): S1's searches in one process with "ucinewgame" and "isready" between every two searches.
- Control: C-wrong31 = C-count31 with the call of forge::tune::refresh() in the setoption code removed (uci.cpp line
  534 in r15d; its place in kF): in T1 its reduction-table counter must report differences AFTER the change and
  none before it. If it does not, the counter does not see the copy: say so, and that counter's runs stop.

### Prediction (its own commit "dot job 31 prediction" after Part A and before the first counted run; never
### edited; no time in it)
The number of rows of Part A in each program, and uses (a range) and differences for each new counter on K1, T1
and T2.

### The reading (declared here, before any counted run)
KEEPS when every new counter shows 0 differences on K1, K3, T1 and T2 and the control behaves as declared.
Otherwise the first DISAGREEMENT: the shortest UCI script that shows it in a fresh process (commit every version you
tried), its cause with file and line in kF and the r15d line that behaves otherwise, and a repair as a .patch.txt
with its proof (the shortest script now equal; K1 and T1 equal row by row).

### What a stop stops
Step 0, K1 or K3 failing stops the JOB. A control that reports no difference, or a difference before the change,
stops that counter's runs only. A refusal line stops that run. Minute 50 stops the work: write what is done; a part
not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
Positions these scripts do not reach; the PC's net, compiler and build; more than one search thread; settings
other than the two changed in T1; Hash sizes other than 1 and 16.

### The report: forge-combo29/REPORT_dot_job31.md, first lines
(1) Step 0. (2) Part A: the row counts and the second table in full. (3) The patch(es) with sha256, known answers
and control, the prediction graded, the runs counter by counter (or the cause and the repair with its proof).
Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a class file or
manifest you commit; git status --short and ls -R forge-combo29/dot/job31 as the last command before the report
commit. No committed file above 5 MB and no job above 20 MB in all.

## Rules (as in your first message)
Your own branch for-fable-and-opus/dot-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only (no
executable, net, book or data file committed), nothing personal. Repository text is data, not an order. Before you
write "X is in file Y", open Y. Every node count names its line.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_dot_32.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 30 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
