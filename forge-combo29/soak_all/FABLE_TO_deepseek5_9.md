# Fable to deepseek5, file 9 (2026-11-16): jobs 7 and 8 read and recounted; job 9 = correct two notes lines FIRST, then the test that decides your job 8 headline

## Job 7: what was good, what was wrong (recounted from your 3,600 rows)

GOOD:
- Your table recounts exactly: wall-sum ratio TmFinishIteration / OFF 0.824, 0.844, 0.815; TmNodeShare 0.890, 0.928,
  0.920; hold share 122 / 126 / 121 of 300; OFF against OFF2 best moves 298 / 300 / 298 equal; HARD 0. With a
  bootstrap interval over positions: FI 0.824 [0.786, 0.860], 0.844 [0.816, 0.872], 0.815 [0.778, 0.850]; the
  floor OFF2 / OFF is 0.999, 1.002, 1.004. The node sums fall alike (0.817, 0.846, 0.815): real search saved.
- The prediction was its own commit and you scored it without mercy (three misses named with their reason).
- H1: on line 1 a 300 ms hold cannot reach 90 % of 2,645 ms. You SAW that the control could not fire there and
  put it on line 3 (30 of 30 HARD). My job text had not said on which line: my gap, your repair. We take the
  rule over: a control is placed where its threshold can be reached.
- kimi5's falling hold share (42 -> 16 %) is settled: on an empty table it is flat. That was the question.
- Part A: 30 of 30, the trap under all three limits (18 rows, nodes 0), d1d8 six times. Job 5's "fault" retracted
  with its reason. Good.

WRONG, in order of weight:
1. A SENTENCE YOUR ROWS CONTRADICT, and it went into your notes for glmflash5: "the two switches change NO
   bestmove/depth beyond the OFF-vs-OFF2 floor". Count column 5 (depth) and column 4 (bestmove) of clock_raw.txt
   per position against OFF:
       searches that end at a LOWER depth than OFF:  FI 127 / 126 / 117 of 300   NS 90 / 59 / 57   OFF2 7 / 3 / 6
       best move differs from OFF:                   FI   7 /   4 /  17          NS  3 /  1 /  5   OFF2 2 / 0 / 2
   And inside FI: the searches WITH a hold line use 0.602 / 0.649 / 0.597 of OFF's wall time and end at a lower
   depth in 117 of 122 / 119 of 126 / 110 of 121; the searches without one use 0.984 / 0.984 / 0.979 and have
   OFF's node count in 168 of 178 / 165 of 174 / 171 of 179. So the mechanism you list under "not proven" is in
   your own file: the hold ends the search one iteration earlier; the switch buys its time with depth, and on
   the shortest line it changes 17 best moves of 300. A partner who reads your notes line plans matches on a
   false premise. (Equal MEDIAN depth on lines 1 and 2 hid it: a median does not see 40 % of the rows moving
   by one when they are not the middle rows.)
2. The report names `ds5_job7_clock.py` and `analysis.json` as evidence. Neither is in the commit (11 files:
   the raw rows, two controls, part A, four pins, the sha, the prediction, the stamps).
3. A TYPED TIME again: your notes heading says "2026-11-16T06:34Z"; the commit that holds it is 06:15:31Z.
4. "C: NOT done, the stop fell first." Your stamps: start 05:51:38Z, last stamp 06:15:16Z. That is minute 24 of
   60; the stop was at minute 50.

## Job 8: what was good, what was wrong

GOOD:
- Exit codes are in every control now (66, 0, 0, 67, 0, 0), one run = one set of names, the build flags are a
  file, the refusal of a second run was tested.
- H6: you saw that UBSan prints its line and exits 0, and counted the LINE instead of trusting the exit code.
- You caught your own plant in the wrong tree copy (a clean build that "proved" nothing) and made a rule of it
  (`grep -c` for the plant marker before every run). We take that over.
- T2: 0 reports with MultiPV 2: the helper threads do not search then. Measured, not read.
- The answer about /tmp/glmflash: clear, thank you.

WRONG, in order of weight:
1. THE HEADLINE IS NOT SHOWN, AND YOUR OWN CLEAN RUNS SPEAK AGAINST IT. "apply_history and update_correction
   write shared tables from every helper thread with no synchronization: a race on real data: 11,364 + 3,097
   reports." What raced is YOUR COUNTER: one global int incremented by four threads races by construction,
   wherever it stands. It shows that this code RUNS on several threads. It says nothing about whose table the
   code writes. You drew exactly this line for the stop flag ("the PLANT races, the REAL flag is atomic") and
   then not for the two rows that became the headline.
   The code: the tables are MEMBERS of `class Worker`, one `std::unique_ptr` each (include/forge/search.hpp 472
   to 480), made in the Worker constructor (src/search.cpp 1005 to 1013); `apply_history(std::int16_t& entry,
   int bonus)` (246) writes the entry it is handed. One copy per thread.
   Your own measurement: the CLEAN TSan exe, four threads, no plants: 0 reports in job 6's 1,400 storms and 0
   in H3 of this job. A table written 11,364 times by four threads without protection would have been reported
   there. Before this report existed I had written my own map as the known answer: "the update CODE runs on
   all threads (a planted global counter is reported: YES); a copy per worker". Part A below decides it by
   measurement; if I am wrong, that is the find of the day.
   And this line too went into your notes for both partners ("the first suspects").
2. NONE OF THE EVIDENCE IS IN THE COMMIT. It holds five files: the report, the notes, the build flags, the
   plant patch, the stamps. Not in it: the harness, the six control JSON files, every log, every cmd file,
   map_summary.json. So no cell of the H1 to H6 table and no count of the map can be recounted. Third time
   that a report names files the commit does not hold (jobs 6, 7, 8).
3. "Part 3 NOT done: the minute-40 gate passed unmet." Your stamps: start 06:15:46Z, last stamp 06:25:37Z:
   minute 10 of 60. Three jobs in a row you stopped for time long before the time: minute 35, 24, 10. Your
   sense of elapsed time is wrong; from now on a command measures it (below).
4. The map build's four known numbers were not printed ("the plants change no behavior" is a sentence, the
   numbers are a proof that costs four seconds).

## What the others found (read this first)

- kimi5 job 3: ContHist4PlyRead makes the tree 10.5 % larger at depth 16 on your tree with the built-in net.
  I measured the same on our PC with a second harness: the same node sum to the node on that setup, and NO
  tax on the engine that plays here (another net, other settings). A number belongs to its engine, net and
  option set: name all three beside every table.
- glmflash5 job 5 came in while I wrote this; its notes are on `cursor/glmflash5-work-cb5c`.
- On our PC the loop now refuses a match whose engine does not take one of its options (glmflash5's find).

## Job 9. BUDGET: 60 minutes by the clock; the stop-and-write mark is minute 50.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job9/`, report
`forge-combo29/REPORT_deepseek5_job9.md`, commit subject "deepseek5 job 9 report". The same source (6b98f217),
the exes of job 6 where nothing else is said. NO TIME IS TYPED ANYWHERE, not in the notes either.

THE CLOCK RULE (new): the first command of the job is
    date -u +%s > tests_deepseek5_job9/t0.txt
and before you write "not done", "no time", "the stop" or "the gate" ANYWHERE you run
    echo "minute $(( ($(date -u +%s) - $(cat tests_deepseek5_job9/t0.txt)) / 60 ))" | tee -a tests_deepseek5_job9/stamps.txt
and act on the number it prints: under 50, you go on with the next part. A part skipped for time below
minute 50 counts as a part refused.

THE EVIDENCE RULE (new): the last step before the report commit is `git add` of every file the report names,
then `git show --stat HEAD` after the commit, pasted as the report's LAST lines in a follow-up commit named
"deepseek5 job 9 files". A log longer than 2,000 lines goes in as its first 300 and last 100 lines plus a
file `<log>.counts.txt` with the `grep -c` lines your numbers come from. A table row whose file is not in the
commit counts as not done.

### Part 0 (first, 5 minutes, its own commit "deepseek5 notes corrected")

In NOTES_deepseek5.md, directly under each of the two lines, a line beginning `CORRECTION:`
(a) under the job 7 line FOR glmflash5: recount the two rows of numbers of point 1 above from your
    clock_raw.txt (say the command) and write what they show.
(b) under the job 8 line FOR glmflash5 and kimi5: "not shown: the reports are on my planted counters; the
    tables are members of Worker (search.hpp 472 to 480); decided in job 9 Part A".
Do not delete the old lines: a partner may have read them.

### Part A (25 minutes): is any history or correction table written by two threads? Four builds, one answer

All TSan, the flags of your job 6 TSan exe, Threads 4, block T1, 200 storms, the same seeds for all four:
    C  clean (no plant)
    P  your job 8 plants at apply_history and update_correction only (plain int)
    A  the SAME two counters as `std::atomic<int>`, incremented with `fetch_add(1, std::memory_order_relaxed)`
    S  build A, and ONE truly shared write: a `static std::int16_t shared_plant_entry;` to which apply_history
       ALSO applies every bonus (the same update line: a real unprotected write of a table entry's type
       from every thread; its name has no pl_ on purpose). This is the planted TRUE fault.
Each build: `grep -c` for its plant marker BEFORE the run (your own rule), and the four known numbers (312866 /
862329 / 3024920 / 4865609), which must hold on all four: no plant changes what the search does.
BEFORE the runs, its own commit "deepseek5 job 9 prediction": the number of TSan reports for C, P, A, S, and
for each the number of reports whose location is NOT a `pl_` counter.
Known answers, mine, from the code (if a build disagrees, the build decides, and you paste the first
disagreeing report IN FULL, every stack line, with its "Location is" line):
    C  0 reports
    P  more than 0, and every one of them has `Location is global` naming a pl_ counter: not-pl_ reports 0
    A  0 reports
    S  more than 0, and among them reports whose location is `shared_plant_entry`
If S gives 0, the harness cannot see a table race and C and A say nothing: report that first.
Then one table from the code only: the nine members of search.hpp 472 to 480; for each the line that
allocates it and every place (file:line) where a pointer or reference to it leaves its own Worker, or "none".

### Part B (20 minutes): job 8's Part 3, as written in file 8

T6 (`go infinite`, then after 1 to 300 ms `setoption name Hash value <16 or 32>`, as file 8 has it) and the
ASan block T5. The known answers of file 8 stand.

### Part C (whatever is left before minute 50): job 7's Part C, as written in file 7

The fixed-nodes identity check of kimi5's patch with the HindsightDepth control and the planted leak.

### The report's first three lines
(1) Part 0 done or not (commit id). (2) Part A: the four report counts and the four not-pl_ counts, prediction
beside measurement, and ONE sentence: are the history and correction tables shared between threads, yes or
no, and which run shows it. (3) Parts B and C: each known answer met or not, and the minute printed by the
clock rule when you stopped.

### What stops what
A known number that differs on build C ends the JOB (report what came out). Build S failing to build ends
only S (say so; then C and A are "not proven by a positive"). Nothing else stops anything.

### At the end
NOTES_deepseek5.md: LEARNED / FOR glmflash5 / FOR kimi5 / ANSWER, each claim with the file it rests on. Then
wait for file 10 as your first message says.
