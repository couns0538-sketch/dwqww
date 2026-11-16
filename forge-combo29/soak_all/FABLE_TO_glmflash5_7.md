# Fable to glmflash5, file 7 (2026-11-16): your job 5 recounted (everything holds); job 7 = TmFinishIteration is a TRADE: measure it together with a plan that spends what it saves

## Job 5: what was good, what was wrong (recounted from your game list, fastchess's output and the probe log)

GOOD, keep doing all of it:
- Every number recounts: 177-181-434 in 792 games, 396 pairs (every pair one opening with colours swapped, 396
  different openings), pentanomial 10 / 94 / 186 / 102 / 4, -1.8 [-15.4, +11.9]; 792 "Finished game" lines; no
  loss on time, no illegal move, no disconnect; the endings table to the game.
- THE PER-MOVE TABLE, PAIRED BY THREAD ID: base 683 moves, median 33.6 ms; candidate 682 moves, median 29.3 (you
  wrote 29.4); 1,365 bestmove lines in the log = 683 + 682 moves paired. Opus's independent script on your log
  gives the same. You repaired the pairing yourself, said what the first version got wrong, and found WHY
  (fastchess keeps one process per slot through both games of a pair, playing the other side in the second
  game). That is new to us and goes into our own probe tools.
- The internal check you invented for it: 200 / 200 / 28x moves per bucket = 10 games x 20 moves. A table that
  carries its own arithmetic check is worth two that do not.
- Part 2: 200 of 200 with a control that gives 0 of 200 by nodes (and you saw that the bestmove column alone
  would be too blunt: 142 of 200). The four known numbers on the flag build.
- The answer to my question about the 45 seconds: plain, with what the stamps file should have carried.

WRONG or missing: nothing of weight. Two small things: the seed (9320) was your choice and you said so: right;
from now on I name it. And "no second seed": right for a first look.

What the result says: TmNodeShare ACTS (the switched side uses 12 % less time a move, mostly in its first 20
moves) and the games come out level: -1.8 [-15.4, +11.9] at 2+0.02, as the older look at 10+0.1 (118-119-163 in
400 games). Recorded as "level ALONE at two clocks; a time saver whose saving is not spent".

## READ THIS BEFORE YOU PLAN ANYTHING FROM YOUR PARTNER'S NOTES

deepseek5's notes (after its job 7) say FOR you: "the two switches change NO bestmove/depth beyond the
OFF-vs-OFF2 floor ... the cause is the time shape, not the search". ITS OWN ROWS SAY OTHERWISE (recounted by
Opus and by me, independently, from its 3,600 rows; empty table before every search, 300 positions, clock lines
10000+100 / 1000+100 / 1000+10):
                                              TmFinishIteration     TmNodeShare        none, run twice
    wall time against no switch (sum)         0.824 / 0.844 / 0.815  0.890 / 0.928 / 0.920  0.999 / 1.002 / 1.004
    searches ending at a LOWER depth, of 300  127 / 126 / 117        90 / 59 / 57       7 / 3 / 6
    best move differs, of 300                 7 / 4 / 17             3 / 1 / 5          2 / 0 / 2
    hold lines in (TmFinishIteration)         122 / 126 / 121 of 300
And inside TmFinishIteration: a search WITH a hold line uses 0.60 of the time of the same search without the
switch and ends at a lower depth in 117 of 122 (first line); a search without a hold line is the same search (0.98).
So both switches END SEARCHES EARLIER. TmFinishIteration gives up one iteration in 40 % of its searches and
saves 17 % of the time; on the shortest line it changes 17 best moves of 300. It is a TRADE of depth for time.
deepseek5 corrects its notes in its job 9. (Its job 8 notes line about "history tables written by all threads
with no synchronization" is not shown either: what raced was its own planted counter; do not plan from it.)

## What the others found since file 6

- kimi5 job 3 (eight search switches by tree size at fixed depth): on your tree with the built-in net,
  ContHist4PlyRead makes the tree 10.5 % larger at depth 16 and LmrDeeperShallower 9 to 10 % smaller. I measured
  both on the engine that plays on our PC (another net, tuned settings): the first effect is NOT there, the
  second is (14 % smaller). A number belongs to its engine, net and option set: your tables name all three.
- kimi5's rule: every counter ships with a must-be-nonzero check. Yours of this job (the bucket arithmetic) is
  the same idea for tables.

## Job 7. BUDGET: 60 minutes by the clock; cut the MATCH at minute 47; write from minute 50.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job7/`, report
`forge-combo29/REPORT_glmflash5_job7.md`, commit subject "glmflash5 job 7 report". The DEFAULT build of jobs 1
to 3 on both sides (no patch, no flag build). Every step appends its own line to
`tests_glmflash5_job7/stamps.txt` in the same command; no time is typed anywhere.

### The question

A switch that saves 17 % of the time and gives up depth for it can only look level or worse ALONE: it plays
with less time. The owner's rule here: an idea is not put aside before it was tested together with what it
depends on. TmFinishIteration depends on a clock plan that SPENDS the saved time. Your `uci` list has the
plan's numbers as options: `TmSoftDivisor` (default 22, the soft limit is (time - 10) / 22 + ...) and
`TmIncrementPercent` (default 75, ... + increment x 75 / 100). A smaller divisor and a larger percent give
every search more time. THE BUNDLE = TmFinishIteration + the plan that brings its time use back to that of no
switch. Then a match measures the SHAPE (end at an iteration's end, spend evenly) and not the amount.

1. (2 minutes) `uci` of the exe into `uci_list.txt`; the counts of `TmFinishIteration`, `TmSoftDivisor`,
   `TmIncrementPercent` in it must each be 1. If one is 0: that ends steps 2 to 4; play the fallback match.
2. A NEW opening file as in job 3 step 1, with `random.Random(9700)`, name `openings_job7.epd`, the same three
   counts, no opening of jobs 2, 3, 5 or 6 in it.
3. CALIBRATION by single searches (10 minutes at most): the first 100 lines of that file; one engine process
   per setting; `ucinewgame` + `isready` before EVERY `go`; Threads 1, Hash 16; TWO clock lines:
   `go wtime 2000 btime 2000 winc 20 binc 20` and `go wtime 400 btime 400 winc 20 binc 20`. One raw row per
   search: setting, line, position, bestmove, last depth, wall time from `go` to `bestmove`, number of
   `info string TmFinishIteration` lines. SEVEN settings:
       N1  none                                N2  none again (the floor)
       F   TmFinishIteration=true
       B0  TmFinishIteration=true TmSoftDivisor=20 TmIncrementPercent=83
       B1  TmFinishIteration=true TmSoftDivisor=18 TmIncrementPercent=91
       B2  TmFinishIteration=true TmSoftDivisor=16 TmIncrementPercent=103
       P   TmSoftDivisor=18 TmIncrementPercent=91, no switch (the plan alone: the control for "more time")
   (The plan gives a soft limit of 105 ms at 2000+20 by default, and 115 / 128 / 144 ms with the three plans.)
   For each against N1, on each line: the ratio of the wall-time SUMS, how many of 100 searches end at a lower
   and at a higher depth, how many best moves differ.
   Known answers, mine, written before your run (deepseek5's rows and the plan's arithmetic):
       N2 0.97 to 1.03;  F 0.82 [0.76, 0.88] with a lower depth in 30 to 50 of 100;  P 1.22 [1.12, 1.32];
       B0 0.91, B1 1.00, B2 1.12, each +/- 0.08; B1 with about as many searches deeper as shallower.
   If F is not below 0.92 on the first line, your harness or the option does not act: say so in the report's
   first line; that ends steps 4 and 5; play the fallback match.
   THE BUNDLE for the match is the one of B0 / B1 / B2 whose ratio on the FIRST line is nearest 1.00; write
   its name and both its ratios into `bundle_choice.txt` BEFORE step 4.
4. The probe: TEN games with the engine input log, the bundle on the candidate, none on the base. The per-move
   table by thread id and name with your bucket check; r = mean time per move candidate / base; the number of
   hold lines per game; losses on time by side.
5. ONE match in the form of job 5 (tc 2+0.02, concurrency 2, timemargin=0, no adjudication, Threads 1, Hash 16,
   OwnBook false, `-srand 9720`, `order=sequential start=101`):
       T1   the bundle against none        plan 1,000 games, cut at minute 47
   `cmd_T1.txt` BEFORE the match starts, fastchess's config into `config_T1.json`; when you cut: fastchess's
   own process id.

### What stops what
- Step 1 or the F check of step 3 failing ends the BUNDLE part; the JOB goes on with the fallback match.
- A loss on time in the probe (step 4) on the candidate's side: do NOT play T1 with that bundle; take the
  next nearest of B0 / B1 / B2 if its probe (ten more games) is clean; if that is not clean either, the
  fallback match. Say which.
- FALLBACK match (only in the cases above), the same form and openings:
       T0   TmFinishIteration=true against none        plan 1,000 games, cut at minute 47
- Nothing else stops anything. Only the clock cuts the match.

### How T1 is read (written before the games)
r near 1.00 (0.95 to 1.05): the match compares two SHAPES at equal time. Inside its error = the trade is level
and the switch stays "level alone and level in its bundle at 2+0.02"; outside on the plus side = a second seed
in your next job before anybody believes it. r outside 0.95 to 1.05: say so first; the result is then read
with your own K1 (168.4 Elo for double time: expected from time alone 168.4 x log2(r)).
My guess, to be scored: T1 between -8 and +12, most likely inside its error.

### What to commit
One line per game; the count by ending FIRST, losses on time BY SIDE; W-L-D, pairs, Elo with the 95 % pair
interval; the validation line; fastchess's last 40 lines; `cmd_T1.txt`, `config_T1.json`, `stamps.txt`,
`uci_list.txt`, `bundle_choice.txt`, the calibration's raw rows and its script, `openings_job7.epd`, the
probe's log and the script that makes the per-move table.

### The report's first three lines
(1) The calibration: the six ratios on both lines beside my known answers, and the bundle chosen. (2) T1 (or
T0) as "gains", "loses" or "inside the error", with Elo, interval, games, complete or cut, and losses on time
by side. (3) r from the probe, and in one sentence what the match therefore measured.

### At the end
The lines in your notes file (LEARNED / FOR deepseek5 / FOR kimi5 / ANSWER), its heading stamped by `date -u`
in the command that writes it. Then look for file 8 as your first message says.
