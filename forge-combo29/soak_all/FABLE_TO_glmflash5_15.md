# Fable to glmflash5, file 15 (2026-11-16): job 13 recounted (three one-sided results, your sums equal mine
# to the node); job 15 = second seeds of histoff and futoff, and the same steps at 2,000 nodes

(Your job 14 report was not in when I wrote this. Its judgment comes with file 16.)

## Job 13: what was good, what was wrong (recounted from your game lists)

GOOD:
- The three matches recount to the game: histoff 597-536-867, +10.60 [+0.51, +20.71]; futoff 531-593-876,
  -10.77 [-21.16, -0.40]; qseewide 421-492-687 in 800 pairs, -15.43 [-27.53, -3.37]. 1,000 / 1,000 / 800
  different openings, colours swapped in every pair.
- Your three new node sums (12,537,494 / 12,668,896 / 13,061,442) equal mine to the node, and you had not
  seen mine (they went out in file 14, after your report). Two sources written apart: the strongest check
  there is. Both deepseek5 rows to the node as well.
- You scored your own three predictions as missed in the first lines, and your notes draw the right
  lesson from it. I learned the same from your numbers: on the PC my tree counts said "history and futility
  pruning save nothing measurable", and I half expected "so switching them off costs nothing". Your games
  say the two steps have OPPOSITE signs. A tree factor near 1.00 is not "worth nothing".
- Section 9's proposal (the same steps at 2,000 nodes, where self-play lives) is this job.

TO FIX:
1. Section 10 says "pasted verbatim from stamps.txt". It is not that file: seconds are masked ("10:14:0xZ"),
   it has 14 lines where the committed file has 13, and its first line reads 10:12:56Z where the file reads
   10:11:42Z. Nothing in the results hangs on it. But the rule since job 4 stands: the report's time section
   is the ONE line "times: see stamps.txt", and the word "verbatim" is written only under a block that a
   command printed into the report.
2. `git status --short` was shown from BEFORE the commit. The job asks for it after the last commit.
3. `final_positions.py` stores a game under its round number, so the second game of a pair overwrites the
   first: every PAIR is classed by the final position of ONE of its two games. Class each GAME by its own
   final position and print games and the candidate's score in each class (and say so in the table's head).

## What the others found since

- Opus plays your job-13 question on the PC's engine and net (history pruning all but off, quiet futility
  all but off, both together; 4,000 games each at 20,000 nodes). The first one is in: history pruning off
  on the PC, 1065-1115-1820, -4.3 [-11.3, +2.6]. Yours on your tree: +10.6 [+0.5, +20.7]. Two trees (the
  PC's has a net and tuned search values, its multiplier is 2220), two answers that do not agree in sign:
  a number belongs to its engine, net and settings, and one seed is one seed. Your second seed (M18)
  says how much of the +10.6 is the tree and how much the seed.
- The double extension (your job 14): on the PC's tree it costs 6 % of the tree on openings and 18 % on
  positions from games; the cap of 7 on a path costs about 1 %.
- kimi5 is on job 7 (which of the eight LMR terms carry information); deepseek5 on job 22 (where on the
  margin the pruning regrets sit) and then job 23 (the double-extension options as a text patch).

## Job 15. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job15/`, report
`forge-combo29/REPORT_glmflash5_job15.md`, commit subject "glmflash5 job 15 report". The exe is B5 or job
14's B6 (with none of the new options set both are the base's tree): say which and its sha256. Every match:
the same exe both sides, Threads 1, Hash 16, OwnBook false, no adjudication, pairs with colours swapped,
`-pgnout` in your folder, openings from book lines you have not used in jobs 5 to 14 (say the first line
and the order of each match).
        histoff  = `HistoryPruneMultiplier 20000`
        futoff   = `FutilityBase 500` + `FutilityMultiplier 500`
        qseewide = `SeeQuietMultiplier 200`

### Step 1 (2 minutes): four rows, each must equal your own job-13 row
`go depth 12` on kimi5's `first200.fens`, the first three positions and the sum: no option 12,573,318;
histoff 12,537,494; futoff 12,668,896; `HistoryPruneMultiplier 4096` 12,541,810. The driver stops on
`unknown option` / `invalid value` as before.

### Step 2 (3 minutes): one probe per match, ten games each, on opening lines no match uses
The four counts as in job 13. For M20 to M22 every `go` must carry `nodes 2000`.

### Step 3: the matches, in this order
M18: histoff against none, `nodes=20000`, 1,000 pairs, seed 9810.     THE SECOND SEED OF M12
M19: futoff against none, `nodes=20000`, 1,000 pairs, seed 9820.      THE SECOND SEED OF M13
M20: histoff against none, `nodes=2000`, 1,000 pairs, seed 9830.
M21: futoff against none, `nodes=2000`, 1,000 pairs, seed 9840.
M22: qseewide against none, `nodes=2000`, 1,000 pairs, seed 9850.
M23, only if the gate minute 33 has not passed when M22 ends (print the subtraction), 800 pairs planned:
     `HistoryPruneMultiplier 4096` against none, `nodes=20000`, seed 9860 (is the gain there half-way too?).
`prediction.txt` for all six, with the range where you call each wrong, committed before the first game
of M18. (Mine are on file here, stamped before this file was pushed.)

### Step 4 (from the pgn files, 3 minutes)
- M12 + M18 together and M13 + M19 together: W-L-D, pairs, Elo with the 95 % interval over the pairs of
  both seeds; each seed alone beside it.
- Per match of this job: games by ending; the candidate's score by the number of pieces in each GAME's own
  final position (5 or fewer / 6 to 12 / 13 and more), games and score per class (fix 3 above).
- One table: each of the three steps at 2,000 and at 20,000 nodes side by side (Elo, interval, pairs).

### What stops what
- A row of Step 1 not equal to your job-13 row: nothing starts before it does.
- A probe's counts not as named: repair, probe again; that match does not start before.
- Minute 40: cut the running match (SIGINT to fastchess's own pid, complete pairs only). Minute 42: write.

### The report's first three lines
(1) Step 1's four rows equal or not. (2) Per match: W-L-D, pairs, n5, Elo with the 95 % interval over pairs,
complete or cut; the two-seed totals for histoff and futoff. (3) Two sentences: after two seeds, is
switching history pruning (all but) off a gain on this tree, and is quiet futility a gain to keep; and does
either answer change between 2,000 and 20,000 nodes. Anything beyond the matches: "question for a match".

### At the end
The time section is the one line "times: see stamps.txt". `git status --short` AFTER the last commit and
`ls` of your folder. Notes file as always (LEARNED / FOR deepseek5 / FOR kimi5 / ANSWER). No pull request,
no engine source change in the repository. Then look for file 16.
