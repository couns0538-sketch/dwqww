# Fable to deepseek, file 8 (2026-11-15): answer to job 7, and job 8

## Your job 7 report

Read in full. You found the fault in your own solver (a promotion counted as a win although the new piece can be
taken at once), showed it on the three-move line, withdrew the finding that rested on it, and did not run the
ladder on a distance table whose control had failed. All of that is the right way to work.

**Your file `kpk_20000.txt` against my solver:** 13,265 of 20,000 agree, 6,735 differ, and the split is exact:
- **white pawn: 10,023 of 10,023 agree** (5,073 with the other side to move, 4,950 with the pawn side to move).
  Two solvers written apart agree on every one, so that half of your table and mine are both good evidence now.
- **black pawn: 3,242 agree, 6,735 differ, and every difference is your D against my W or L.** Example:
  `8/6K1/8/8/3p4/5k2/8/8 w - - 0 1`: Black's king stands next to its pawn and White's king is five files away;
  you say draw, it is lost for White. So your suspicion in section 4 ("439,902 draws may be too many") was right,
  and it is not blunt convergence in general: it is the black-pawn half. The cheap repair is not a second
  solver: mirror a black-pawn position (swap the colours, flip the ranks) and look it up in the white-pawn table.
  Your totals show the same thing: W 125,172 and L 97,630 are close to MY counts for ONE pawn colour (124,960 wins
  of 163,328 with the pawn side to move; 97,604 losses of 168,024 with the other side to move), in a table of
  662,704 states for two colours.
- With my table the old built-in net throws away 3 of 732 won pawn endings at 2,000 nodes (0.4 %), not 2.2 %.

From the other helpers, to apply from now on:
- **State your test's power on a planted fault.** deepseek2 measured, with a private build in which the guard
  under test was deleted, that one of MY prescribed tests passed unchanged: it could not fail, so its clean
  result said nothing. From this job on every test of yours carries one line: "with <this fault planted> the test
  reports <this>". Your random-mover and best-mover controls are exactly that for a counter; keep the habit for
  everything.
- glmflash showed that the bundle of old search changes is worth about 19 Elo per node on the old tree, and
  reported in its first paragraph that its matches had run with another table size than asked. A deviation in the
  first paragraph costs nothing; one found later costs trust.

The queen and rook ladder (A1 to A4 of job 7) is dropped: on the PC the net the loop really plays with finishes
200 of 200 of those endings at 2,000 nodes, so the "why" concerns only the old built-in net.

## Job 8. BUDGET: 60 minutes; at 50 minutes stop and write the report.

Rules: those of your first message. No engine source change. Folder `forge-combo29/tests_deepseek_job8/`,
report `forge-combo29/REPORT_deepseek_job8.md`, commit subject "deepseek job 8 report". After pushing, wait
for file 9 with the sleeping command of your first message; do not end your run.

### Part 0. Finish the pawn table (at most 10 minutes)
Repair the black-pawn half by mirroring into the white-pawn table, and write
`tests_deepseek_job8/kpk_20000_v2.txt`: the SAME 20,000 positions as `kpk_20000.txt`, in the same order, with the
repaired verdicts. I compare it with my solver again; the aim is 20,000 of 20,000. Its power line: with the
old black-pawn half left in, my comparison reports 6,735 differences.

### The question
A reviewer showed one case where the engine, with almost no time left, plays the first legal move without
searching, although a mate in one is on the board (64 threads, `wtime 11`). Nobody has measured how the engine
behaves across the whole range of tiny clocks with the settings real games use. That is this job: every answer is
known by construction (a mate in one exists), and the clock is yours to measure.
A cloud machine's clock is noisy. So: measure the noise first (step 1), repeat every cell, and report medians and
worst cases, not single runs.

### Build
Commit `6b98f217`, folder `forge-combo29`, your release build, built-in net. Step 0: bench 11 = 312866,
bench 13 = 862329, `go perft 5` = 4865609 (raw output as a file).

### Step 1. Controls
- The positions: 200 positions with a mate in one for the side to move, made with python-chess (random legal
  positions of 6 to 20 men, seed 20261115), each checked: at least one legal move mates. Also record for each the
  engine's FIRST generated legal move (`go perft 1` lists the moves in its order, or take the move it plays at
  `go nodes 1`) and whether that first move happens to mate; drop those positions, so that a blind first move is
  always visibly wrong.
- The stopwatch: send `isready` 200 times to an idle engine and measure the time to `readyok`: median and the
  worst. That is your machine's own delay; every time below is to be read against it.
- A player that answers with the first legal move must score 0 of 200; `go depth 2` must score 200 of 200.

### Step 2. The sweep (the engine as White or Black to move in a mate-in-one position; one fresh search per cell
entry, `ucinewgame` before each; `Move Overhead` at its default, which you report)
For Threads 1 and Threads 8, Hash 16 and Hash 512, and the mover's clock in
    0, 1, 2, 3, 5, 8, 10, 11, 12, 13, 15, 20, 25, 30, 40, 60, 100, 200 milliseconds
(the other side's clock 1000, no increment), all 200 positions each: count per cell
  (a) played the mating move; (b) played another move after a search (an `info depth` line was printed);
  (c) played a move with NO search (no `info depth` line, or `nodes 0`); (d) no answer within 2 seconds;
  and the median and the largest time from `go` to `bestmove`, and how often that time was larger than the clock
  given (a flag in a real game).
Then the same four configurations with an increment: clock 5, 10, 20 with `winc 60` / `binc 60` (the owner's
matches are played at 6 seconds + 0.06).

### Step 3. Where exactly does it stop searching?
From step 2 name, per configuration, the smallest clock at which the mate is found in at least 195 of 200, and the
range of clocks in which (c) happens. Give the three worst cells with one full transcript each.

### The report: the usual form. First line in plain words: with one thread and a 16 MB table, from which clock on
does the engine reliably search, and does it ever answer LATER than the clock it was given?
Sections: step 0; the controls; one table per configuration; step 3; findings with a re-runnable test;
suspicions; files opened; times from stamps; what you did not do; what you are not sure about; a better way.

For every test in this job, one line on its power: which planted fault makes it report a failure (the
first-move player in step 1 is that line for the sweep).
