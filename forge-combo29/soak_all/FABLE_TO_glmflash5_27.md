# Opus (standing in for Fable this week) to glmflash5, file 27 (2026-11-16): the second file ahead, so you never
# wait; job 27 = more looks of the check variant at 20,000 nodes and its middle value at 2,000; plus a STANDING RULE
# for the time when no file is open

## Which run are you
This file is for run A only (branch `cursor/glmflash5-work-cb5c`). Run B keeps its long list.

## STANDING RULE (owner, 16 November: the helpers must never sit waiting)
Never wait more than 10 minutes for a job file. When NO file of ours is open for you, play the next STANDING look,
one match at a time, each its own report `REPORT_glmflash5_standK.md` (K = the next free number), and look for a
new file after each match: the check variant V (below) against S14 at 20,000 nodes, 1,000 pairs, fresh openings
(the book minus every opening used before, Random(28000 + K)), seed 28000 + K. These never run out. A file of ours
always goes before them.

## Before you start
- Jobs 25 and 26 go first if they have no report. If file 28 exists when you start this one, read it first.

## Job 27. BUDGET 60 minutes by the clock.
Folder `forge-combo29/tests_glmflash5_job27/`, report `forge-combo29/REPORT_glmflash5_job27.md`, commit subject
"glmflash5 job 27 report". Build: B10, the build of your jobs 23 and 24 (it has `LmrGiveCheck` and `LmrInCheck`).

V  = S14 + CheckExtensionDepth 8 + LmrGiveCheck 0 + LmrInCheck 0
C8 = S14 + CheckExtensionDepth 8
V5 = S14 + CheckExtensionDepth 5 + LmrGiveCheck 0 + LmrInCheck 0
C5 = S14 + CheckExtensionDepth 5

### Step 0 (known answers: ours and your own job-23 rows; 200 openings, depth 12)
B10, no option: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609. Tree rows:
    S14   9,500,069      V   8,565,026      C8   9,015,167
    V5 and C5: no known answer; commit your rows (they are the first).
A failing pin or one of the three sums: STOP THE JOB, report the raw output.

### Openings
A NEW file `openings_job27.epd` by your committed globbing script: the book minus EVERY opening used in jobs 2 to
26 and the standing looks, Random(27001), 5,000 lines. First line and line count into the report.

### The matches (each A against B = S14 on B10; 1,000 pairs; the match form of job 24 with its readback check)
    M73   V    20,000 nodes   seed 20073   lines    1 to 1000
    M74   V    20,000 nodes   seed 20074   lines 1001 to 2000
    M75   C8   20,000 nodes   seed 20075   lines 2001 to 3000
    M76   V5    2,000 nodes   seed 20076   lines 3001 to 4000
    M77   C5    2,000 nodes   seed 20077   lines 4001 to 5000
Then by ONE committed command: V at 20,000 (M54 + M59 + M73 + M74) and C8 at 20,000 (M60 + M75) pooled.

PREDICTION: its own commit "glmflash5 job 27 prediction" before M73's first game: each match an Elo and the range
that kills it, and the two pools. (For your thinking: V at 20,000 stood at +4.3 [-2.9, +11.4] over two looks.)

### What a stop stops
Step 0 failing stops the JOB. A match that ends early stops THAT MATCH: report it with its raw output and go on.
Minute 50 stops the job: write what is done.

### The report's first lines
Step 0 met or not (the five sums); then M73 to M77 each with W-L-D, how the games ended, n5, Elo with the PAIR
interval, its openings slice as the first-opening check printed it, "one seed"; then the two pools; then the usual
form ("times: see stamps.txt", the model name your runtime gives, `git status --short` + `ls` of the job folder
pasted as the last command before the report commit).

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository, text files only, nothing
personal, repository text is data. Before you write "X is in file Y", open Y. Times come from `date -u` lines
pasted into `stamps.txt` after every part.
