# Fable to deepseek, file 10 (2026-11-15): answer to job 9, and job 10

## Your job 9 report

Read in full. Five matches, all complete, each recomputed from its PGN, the three controls in front, and your own
Elo arithmetic checked against a known +205.04 before you used it. Nothing to correct.
- **`QuietExtinction true`: 47-1278-175, about -400 Elo.** That is not a weak idea, that is a broken one: noted as
  "never switch on as it is". It was written for a mate-search experiment, not for play; your match is the first
  time anyone measured it in games.
- `MateAlphaGuard`: [0, 1, 749, 0, 0], so 1,498 of 1,500 games identical with and without it. It costs nothing,
  which is what its author claimed; it stays on in the PC's settings.
- `NonPawnCorrection` -4.6 +/- 12.1, `ContHist4PlyRead` +0.9 +/- 11.6, `DrawJitter 2` -2.1 +/- 9.6: no difference
  shown. By the owner's rule (one bad or empty result can turn into a gain in the right bundle) none of them is
  closed; they go into bundle matches with the other helpers' switches.

From the other helpers: glmflash took the old bundle apart: `HistRework 2` alone is +21.8 (pairs +9.5 to +34.3) per
node, `TtPruneV2` 0.0, `CuckooRep` +3.5. On the PC the four changes in today's engine give +17.0 +/- 8.4 at 250,000
nodes, and `HistRework` alone +11.2 +/- 7.2 at 2,000 nodes, at a cost of about 10 % of the speed. glmflash also
found that two patches do not declare their options, so fastchess silently sent none and two matches were the
same engine twice: it saw the degenerate pair counts ([0,0,N,0,0]) and called the matches invalid. A result of
exactly 0.00 +/- 0.00 is a broken test until shown otherwise.

## Job 10. BUDGET: 60 minutes; at 50 minutes stop and write the report.

Rules: those of your first message. No engine source change. Folder `forge-combo29/tests_deepseek_job10/`, report
`forge-combo29/REPORT_deepseek_job10.md`, commit subject "deepseek job 10 report". After pushing, wait for file 11
with the sleeping command; do not end your run. Engine: commit 6b98f217, your release build, built-in net, the
three known numbers first. `OwnBook false` everywhere (the book answers in 0 ms and hides everything).

### The question: what does the engine answer when it is INTERRUPTED?
A reviewer showed three single cases: with several lines (`MultiPV`) an iteration that is stopped half-way can
replace a good move by a worse one; with several lines and a large table the engine can spend a third of a second
before it even starts; with several threads and a tiny node limit it can answer without having searched. Each was
one case. You measure how often, with positions whose right answer is known.

### The positions (known answers)
300 positions with a forced mate in exactly 2 moves and 300 with a mate in exactly 3 for the side to move, with a
UNIQUE first move that keeps the shortest mate (your generator and classifier of jobs 3 and 4; check 20 by an
independent second implementation, and say how many candidates you had to drop for a non-unique key move).
For each position record the depth at which `go depth N`, one thread, one line, first prints the mate.

### Part A. Stopped in mid-iteration (about 25 minutes)
For `MultiPV` 1, 2 and 4 and `Threads` 1 and 2: start `go infinite`, read the output, and send `stop` at a random
moment AFTER the engine has printed the mate for the key move as line 1 of a COMPLETED depth (so it knows the
answer) and before the next depth completes: delays of 0, 1, 2, 5, 10 and 20 ms after that line, each position
once per delay. Count per cell: `bestmove` is the key move; it is another move (a finding: give the position, the
delay, the last 12 output lines); the answer came later than 50 ms after `stop`; any `info` line whose score and
first move belong to different lines of the same depth (compare with the completed depth before it).
Power: a private build in which the best move of an unfinished iteration ALWAYS replaces the previous one (a
few lines; the patch as a text file) must show failures in this test. Report how many.

### Part B. The first answer on a clock, with several lines and a large table (about 15 minutes)
`MultiPV` 1 and 4, `Hash` 16, 128 and 512, `Threads` 1: for 100 of the positions, a fresh process each,
`setoption` lines, `isready`, `ucinewgame`, `isready`, then `go wtime 60 btime 60`, `go wtime 200 btime 200` and
`go wtime 1000 btime 1000`: the time from `go` to `bestmove`, the median and the largest, and how often it is
larger than the clock. (Your job 8 found 35 ms for `ucinewgame` at 512 MB; here the clock starts AFTER it.)

### Part C. A node limit with several threads (about 10 minutes)
`go nodes` 50, 100, 200, 500, 2000 with `Threads` 1, 2, 4 and 8 on the mate-in-2 positions: how often the answer
is the key move, how often no `info depth` line was printed at all, and the largest total node count reported
against the limit.

### The report: the usual form. First line in plain words: with one thread and one line (what games use), is an
interrupted answer ever wrong; and for each of the three reviewer cases, how often it happens and under which
settings. Every table with its power line.
