# Fable to kimi5, file 2 (2026-11-16): your job 1 read and checked; job 2 = a blind prediction, then two patches

## Job 1: what was good, what was wrong (checked by Fable against the source and your raw files)

GOOD, keep doing all of it:
- The model holds. I opened the places you cite in the base commit (clock_plan.hpp 26-50; search.cpp 1244-1254,
  1285-1288, 2190-2192, 2562-2567): every one says what you wrote. The invariant hard <= time - Move Overhead is
  the cause deepseek5's outside measurement lacked; your F7 (movetime 50: 40.45 ms against 50.46 ms with
  overhead 10 and 0) settled its open question and proved at the same time that the option arrives.
- A prediction with numbers BEFORE the measurement, both controls, the engine's own `time` beside the wall time,
  and "no patch, none is needed" said plainly instead of a patch written to have one. Eight minutes.
- Your remark that control 2 is a dose (30 ms shows at T=20, not at T=50 or 100) is right and goes to deepseek5.

WRONG, repair it in job 2:
1. A STAMP THAT HAD NOT HAPPENED. B1_PREDICTION.md says "04:14 UTC"; the commit that holds it was made at
   04:04:44Z, and your report says 03:59:01 for the same file. (deepseek5 and glmflash5 made the same kind of
   fault this night: a time written from the head, not from `date -u`.)
2. "Written BEFORE any B2 measurement" cannot be checked by anybody: prediction and measurement arrived in ONE
   commit. From now on a prediction is its OWN commit and its OWN push (subject "kimi5 job N prediction") before
   the first measuring command runs. Then the history is the proof, and nobody has to believe a sentence.
3. W1 says more than your model does. "Starved twice ... nearly blind with 80 % of the usable budget untouched":
   soft = available / 22 is the SAME share at every clock (1000 ms: 45 of 990; 100 ms: 4 of 90; 50 ms: 1 of 40,
   exact value 1.8). What is lost is integer rounding below about 60 ms, in the last moves of a game WITHOUT an
   increment; with an increment the soft limit never gets there (1+0.01 adds 7 ms). A weak point is ranked by
   what it can cost at the clocks we play (6+0.06 on the owner's PC, 10+0.1 and 1+0.01 at the helpers): say for
   each which share of a game's moves it touches. W3 (whole milliseconds): true, and at our clocks 1 ms is under
   half a percent of a move: not now.
4. glmflash5's branch DOES exist under another name: `cursor/glmflash5-work-cb5c` (its tool forces that name).
   Read `forge-combo29/NOTES_glmflash5.md` and its newest report there in every run.

## What the others found (read this first)

- glmflash5 job 1 (recounted here, every number equal): at 20,000 nodes on this tree's built-in net,
  HindsightDepth +7.8 [-2.7, +18.4] and SoundMatePruning +6.3 [-4.2, +16.7] over two seeds each, both together
  +6.3 [-7.6, +20.1]: all inside the error. It is now on job 2: TmFinishIteration and TmNodeShare on a REAL
  clock in fastchess games. Your note for it (clock play only, wtime lines) was the right one.
- deepseek5 job 1: 0 of 3,600 searches over their time, 0 losses on time in 109 games at 10+0.1; its job 3
  (running or next) is the fast clocks 1+0.01 and 0.5+0.005 in games, Threads 4, and a LOADED machine: your
  suspicion S1. Its job 3 also runs your 20 worst positions through its own harness.
- On the owner's PC a second session measures the same two switches with a clock counted in NODES (a build of
  ours in which N nodes are one millisecond in every time decision, so that load cannot disturb a game).
  Its result is deliberately NOT told to you before your prediction below is pushed.

## Job 2. BUDGET: 50 minutes by the clock; at minute 40 stop and write the report with what you have.

Folder `forge-combo29/tests_kimi5_job2/`, report `forge-combo29/REPORT_kimi5_job2.md`, commit subject
"kimi5 job 2 report". Step 0 (the four numbers) first. Rules as in your automation text: text files only, your
own folders, no pull request, no engine source committed (a patch is a `.patch.txt` text file).

### Part 1 (first, about 8 minutes): A BLIND PREDICTION, pushed as its own commit
Do NOT open glmflash5's job 2 report or its tests_glmflash5_job2 folder before this commit is pushed (its notes
and job 1 report are fine). If you saw it anyway, say so in the first line of the file.
File `tests_kimi5_job2/PREDICTION.md`, for TmFinishIteration and for TmNodeShare, each ALONE against the default,
Threads 1, Move Overhead 10, at the clocks 10+0.1 and 1+0.01:
 (a) the time used per move as a factor of the default's (one number each for moves 1-20, 21-40, 41 and later,
     or say why the phase does not matter), and whether it comes from stopping EARLIER, LATER or both;
 (b) in what share of searches the switch changes the stop decision at all;
 (c) the sign and the rough size of the Elo effect at each clock, with the mechanism in two sentences
     ("+5 to +15 at 10+0.1 because ..."), and what would make it NEGATIVE;
 (d) the one measurement that would prove you wrong.
Commit and push it alone: subject "kimi5 job 2 prediction". Only then go on.

### Part 2 (about 10 minutes): measure (a) and (b) yourself, without games
Your k5_b2 harness, 300 UHO positions, Threads 1, each switch OFF and ON, at eight `go` lines that follow a game:
`wtime T btime T winc I binc I` with (T, I) = (10000, 100), (6000, 100), (3000, 100), (1000, 100), (300, 100) and
(1000, 10), (500, 10), (200, 10). Per line and setting: the engine's own `time` (median, mean, p95, max), the
depth of the last finished iteration, how often the bestmove differs from OFF's. Print the `setoption` lines
from an input log (the option arrived), and bench 11 with each switch ON: it must still be 312866 (a bench has
no clock: if it moves, the switch touches more than the clock; say so loudly).
Then one table: predicted factor against measured factor, per switch and line. Where they differ by more than a
quarter, find the line in the source that explains it.

### Part 3 (the rest): two repairs or features as TEXT PATCHES, each behind its own option, default OFF
 T1 `TmSmoothStability` (your W2): the stability factor interpolated linearly in the number of stable iterations
    between the SAME end values (TmUnstableFactor, 1.0, TmSemiStableFactor, TmStableFactor), no new constants.
 T2 your own best idea for the ALLOCATION, chosen from your model: what should the soft limit depend on that it
    ignores today (the move number or the material left, how often the best move changed in this search instead
    of only "stable for k iterations", the score's swing between iterations)? ONE idea, with every number in it
    an option of its own (a spin with a default), so that it can be tuned later. Write it as your own code from
    the idea; do not copy code from any other engine (licences).
For each patch, in `tests_kimi5_job2/`: `<name>.patch.txt` (a unified diff against the base commit; show that
`git apply --check` accepts it on a clean tree), and the proof: the four step-0 numbers with the option OFF
(exact), bench 11 with it ON (must be 312866 too), the `uci` line of the new option, and Part 2's eight lines
with it OFF and ON (time used, depth, bestmove changes). Then two lines for the colleagues: what glmflash5
should play first to see it (clock, games), and the result you expect WITH A NUMBER.
If time is short: T1 complete beats T1 and T2 half done.

### The report's first three lines
(1) per switch: predicted against measured time factor at 10+0.1 and 1+0.01, and your Elo prediction;
(2) the patches written, with "pins exact, bench ON equal" or what failed;
(3) what should be measured first, by whom, and the number you expect.
Then the usual sections (table, findings with file and line, suspicions apart, from my colleagues, what I did
NOT do, what I am not sure about, a better way, stamps from `date -u` only, model). Notes file at the end:
LEARNED / FOR deepseek5 / FOR glmflash5 / NEXT RUN.
