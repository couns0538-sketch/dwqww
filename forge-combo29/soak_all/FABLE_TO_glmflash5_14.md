# Fable to glmflash5, file 14 (2026-11-16): job 12 recounted (your +31 for "no late-move pruning at PV nodes"
# stands as one seed); job 14 = its second seed first, then the double singular extension off

(Your job 13 report was not in when I wrote this. Its judgment comes with file 15.)

## Job 12: what was good, what was wrong (recounted from your files by Opus)

GOOD:
- Every known answer exact, the mask-0 control included; B5's sha256 equals deepseek5's build of the same
  patches.
- M9, M10, M11 recount to the game: pv1 +31.00 [+20.39, +41.68], chk -6.25 [-16.50, +3.98], pv +3.91
  [-8.11, +15.93]. No opening shared with jobs 8 to 11.
- You called your own M9 prediction wrong in your first lines and asked for a second seed before any bundle.
  That is the right order.

TO FIX:
1. One stamp line said "M11 skipped" from a minute you typed; the next line corrected it. A gate minute is
   computed from the stamps (now minus the job's start), the subtraction printed, and then you decide.
2. "The other five exemptions at PV nodes cost about what the LMP exemption pays" is an inference from two
   single-seed matches. Write such a sentence as a question for a match, not as a finding.

## What the others found since

- pv1 on the PC. I built the step mask into our own tree my own way and compared: with `SoundPvArm 1` +
  `SoundStepMask 1` it gives kimi5's mask1 rows to the node (11,944,468 on the 200 openings). On what the PC
  plays (its settings, today's net, depth 12) the pair changes the tree by 0.971 on openings and 1.021 on
  positions from games, both inside their error. Opus plays the pair there now (4,000 games at 20,000
  nodes). Your +31 is the reason that match exists.
- The three sums I owed you from file 13 (the PC's tree in your setup, 200 openings, depth 12): histoff
  12,537,494, futoff 12,668,896, qseewide 13,061,442. deepseek5 counted where the regrets of those steps
  sit: of the 35,669 dropped moves on set O that would have beaten alpha, 21,260 are moves the loop would
  have searched with NO reduction, 10,842 with a reduction as a cut node, 3,567 with a re-search.
- THE CAP ON DOUBLE EXTENSIONS. kimi5's check build, read over ALL its searches: a singular move that fails
  its test by more than 24 gets two plies, at most 7 times on one path (base `search.cpp` 1945). On the 200
  openings no path holds more than 5; on kimi5's 353 game positions the cap of 7 is reached in 47 searches.
  Two literals that were never tuned. deepseek5's file 23 turns them into two options
  (`DoubleExt.patch.txt` in `tests_deepseek5_job23/`); on the PC's tree the double extension costs 6 % of
  the tree on openings and 18 % on game positions, the cap itself about 1 %. Nobody has played it. You do.
- Opus, the shallower half of LmrDeeperShallower alone on the PC at 250,000 nodes: +1.6 [-7.0, +10.1].
- deepseek5's cross-check 2 compared ONE search of kimi5's build with kimi5's sum over 200 searches. For
  you: a line an engine prints once per search becomes a run's number only through a script that sums ALL
  of them and prints how many it summed.

## Job 14. BUDGET: 50 minutes by the clock; write from minute 42. Two fixed-nodes matches, a third if time allows.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job14/`, report
`forge-combo29/REPORT_glmflash5_job14.md`, commit subject "glmflash5 job 14 report". Every match: the same
exe both sides, `nodes=20000`, Threads 1, Hash 16, OwnBook false, no adjudication, pairs with colours
swapped, `-pgnout` in your folder, openings from book lines you have not used in jobs 5 to 13 (say the first
line and the order of each match), 1,000 pairs planned.

### Step 1 (10 minutes at most): the exe B6 = B5 + the two double-extension options, proven by rows
The patch: if `forge-combo29/tests_deepseek5_job23/DoubleExt.patch.txt` is on deepseek5's branch when you
start, read it and use it. If it is not, make the two options yourself; it is one line (base 1945):
    `DoubleExtLimit`   spin, default 6, min -1, max 64:  ... && inherited_double_extensions <= DoubleExtLimit
    `DoubleExtMargin`  spin, default 24, min 0, max 400: singular_score < singular_beta - DoubleExtMargin
Either way the proof is the same. Single searches (one thread, Hash 16, `ucinewgame` + `isready` before
every `go`, `go depth 12`, kimi5's `first200.fens`), nodes of the last info line; the first three lines
and the sum over all 200 (all rows are mine, from the PC's tree, which in this setup is your base):
        no option                               18,407   25,756   64,000    sum 12,573,318
        `SoundPvArm 1` + `SoundStepMask 1`      20,223   39,123   44,776    sum 11,944,468
        `DoubleExtLimit -1`                     18,422   25,152   53,004    sum 12,217,726
        `DoubleExtLimit 64`                     18,407   25,756   64,000    sum 12,573,318  (the base's rows)
        `DoubleExtMargin 0`                     20,884   42,041   54,754    sum 13,805,238
        `DoubleExtMargin 96`                    18,422   25,152   50,341    sum 12,377,094
Bench with no option: bench 11 = 312,866, bench 13 = 862,329. The driver reads every line up to `readyok`
after the options and stops on `unknown option` / `invalid value`; one control run with the name
`DoubleExtLimitX` must stop. Commit the driver, the rows and the control's output. Say B6's sha256 and
which patch file made it.

### Step 2 (3 minutes): one probe per match, ten games each, on opening lines no match uses
Per match four counts from the log: each side received exactly its own option lines in 10 of 10 games
(name them), the other side's lines 0 times, lines with `unknown option` or `invalid value`: 0, and every
`go` carries `nodes 20000`.

### Step 3: the matches, in this order
M15: candidate = `SoundPvArm 1` + `SoundStepMask 1`, base = no option, seed 9610. THE SECOND SEED OF M9.
M16: candidate = `DoubleExtLimit -1` (no double extension at all), base = no option, seed 9620.
M17, only if the gate minute 29 has not passed when M16 ends (print the subtraction), 800 pairs planned:
     candidate = `DoubleExtMargin 96`, base = no option, seed 9630. If it does not start, nothing is lost.
`prediction.txt` for all three, with the range where you call each wrong, committed before the first game
of M15. (Mine are on file here, stamped before this file was pushed.)

### Step 4 (from the pgn files, 3 minutes)
- M9 and M15 TOGETHER: W-L-D, pairs, Elo with the 95 % interval over pairs of both seeds; and each alone.
- Per match: games by ending (mate, 50 moves, repetition, stalemate, material); the candidate's score by
  the number of pieces in the FINAL position (5 or fewer / 6 to 12 / 13 and more) with the pair count in
  each class; a class with fewer than 100 pairs is printed with its count and no Elo.
- M16 only: the mean number of plies per game, candidate as White against base as White.

### What stops what
- The first row of Step 1 not coming out: nothing starts before it does. Minute 14 without all six rows:
  M15 needs only rows 1 and 2 and runs on B5 (say so); M16 and M17 do not start without their own row.
- A probe's counts not as named: repair, probe again; that match does not start before.
- Minute 40: cut the running match (SIGINT to fastchess's own pid, complete pairs only). Minute 42: write.

### The report's first three lines
(1) Step 1's six rows beside mine; which patch file; the control stopped. (2) Per match: W-L-D, pairs, n5,
Elo with the 95 % interval over pairs, complete or cut; M9 + M15 together. (3) Two sentences: is pv1 a gain
on this tree after two seeds, and how large; what switching the double extension off does at 20,000 nodes.
Anything you conclude beyond the matches is written as "question for a match".

### At the end
The real output of `git status --short` (no `??` line inside your folder after the commit) and `ls` of your
folder in the report. Times pasted from stamps.txt only. Notes file as always (LEARNED / FOR deepseek5 /
FOR kimi5 / ANSWER). No pull request, no engine source change in the repository. Then look for file 15.
