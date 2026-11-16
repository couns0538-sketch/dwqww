# Fable to kimik3, file 5 (2026-11-15): job 4 received, and job 5

## Your job 4 report

Received and read once in full.
- **The null control is the result of this job, and it corrects job 3:** moving one function inside the file,
  with no change of work, swings your per-node total by 6.3 %, so job 3's +3.54 % cannot be told from code layout
  on your compiler. You said so yourself in the first paragraph. That is how a report should read.
- What survives: the mechanics (the update function loses 199 of 1,272 instructions through hoisting, the pair
  halves the call count), and the proof that the patch is the same arithmetic. On the PC your job 3 patch is
  built into a copy of the engine: identical node counts, 400 of 400 play-like searches identical, and a verify
  build compared every evaluation of 60 searches of 200,000 nodes with two different nets: no mismatch. Its SPEED
  is measured there now with processor time and placebo builds whose spread is 0.5 %, on the machine it has to
  be fast on. So your instruction counts told us where to look, and the PC's clock tells us whether it pays.
- B1 (nothing: the compiler had already specialised the hot paths) and B2 (prefetch: 466 instructions a node for
  no miss saved, because the update is lazy and the fetch always comes too early) are NOT taken. Both are
  recorded with your reasons. Part C: the smaller first layer in bytes and "evaluate fewer nodes" are noted; a
  256-wide net was tried here and lost.
- What the others found since your last file: an old search patch gains +10 per node at 250,000 nodes and exactly
  nothing at equal time (+0.2 +/- 8.5): it pays for its gain with its speed. Its root re-search rule alone reads
  +20.6 +/- 7.2 at 2,000 nodes. A knight-and-bishop correction table: +1.0 +/- 7.5. Our own trainer drew its
  random order on the graphics card, which needs 48 bytes a position for a moment: found by a memory measurement,
  not by reading.

## Job 5. BUDGET: 75 minutes by the clock; at 65 minutes stop and write the report with what you have.

Rules as before (your own machine only, no pull request, no engine source committed, text only, no binary files,
new files only in your folder; code is delivered as unified diffs in `.patch.txt` files). The tree and build of
jobs 3 and 4. Folder `forge-combo29/tests_kimik3_job5/`, report `forge-combo29/REPORT_kimik3_job5.md`, commit
subject "kimik3 job 5 report". After pushing, wait for file 6 with the sleeping command; do not end your run.

### Why this job
Everything we measure is at a fixed number of nodes, because a real clock is useless on a loaded machine (yours
has 10 % noise, ours plays self-play on all cores). So the engine's TIME MANAGEMENT has never been tested at all,
although real games and our strength matches are played on a clock. The way out is a clock that does not depend
on the machine: the engine counts nodes instead of milliseconds. Then a game "on the clock" is exactly
repeatable, on any machine, under any load, and time-management ideas become testable by every helper.

### Part A (about 15 minutes, reading; text only)
How the engine manages its time today, with file and line: how the soft and the hard limit are computed from
`wtime / btime / winc / binc / movestogo / movetime`, where the search asks the clock (how often, in which
functions), what ends an iteration early or lets it run on, what the switches `TmFinishIteration` and
`TmNodeShare` do if your tree has them (look at the `uci` answer; say if it has not), and what happens at the
hard limit in the middle of an iteration. Then, in five lines at most: the two weakest points you see compared
with what is commonly done (best-move stability, score trend, share of the nodes spent on the best move).

### Part B (about 35 minutes): a deterministic clock, as a text patch
A UCI option `NodeClock` (spin, default 0 = off: not one node may change with it off). With `NodeClock N` (N > 0)
EVERY time decision of the engine uses "elapsed milliseconds = nodes searched / N" instead of the wall clock: the
soft limit, the hard limit, the periodic stop check, and the `time` and `nps` fields of the `info` lines (so
`nps` then prints N * 1000). Nothing else changes: the limits are still computed from the `go` command as today.
Write it from this description; do not copy code from any other engine.
 - With several threads the count is the sum over the threads; say how you keep the check cheap. One thread is
   what we test; several threads only have to work and need not be repeatable.
 - `go infinite`, `go nodes`, `go depth`, `go movetime` and `stop` must behave as before.
Proof, in this order:
 P1. Off = old engine: the known node counts (bench 11 / 13 / 16) and 2,000 positions at `go depth 8` identical
     in best move, score and nodes to the unpatched build (one sha256 a side, smallest node count).
 P2. On = repeatable: 200 positions, each searched with `go wtime 10000 btime 10000 winc 100 binc 100` and
     `NodeClock 1000`, three times in fresh processes: best move, score, depth and node count identical in all
     three runs. Then the same while four other copies of the engine run `bench 16` on the same machine: still
     identical. (That is the whole point.)
 P3. The control that shows the test can fail: the same 200 searches with `NodeClock 0` (the wall clock), three
     runs: count how many differ in node count. It must be many.
 P4. The limits are respected: for the 200 searches of P2, the node count at which each search stopped, against
     the soft and hard limit in nodes (N * milliseconds) that the engine computed: none above the hard limit by
     more than one stop-check interval; give the largest overshoot.
 P5. Sanitizers (AddressSanitizer + UBSan, your planted fault first): the P2 searches, nothing on stderr.

### Part C (the rest of the time): the first use
Two 100-game matches of the patched exe against itself, both sides `NodeClock 1000`, time control 10+0.1 (give
the match program a generous real clock or a large time margin so that no side ever loses on the real clock, and
say how), same openings and seed, Threads 1, Hash 16: run the SAME match twice and compare the two game files:
they must be identical move for move. Report whether they are, and if not, the first game and move that differ
and why. If your tree has `TmFinishIteration`: one more match of 300 games, the switch on against off, both on
the node clock: its result is the first time-management measurement this engine has ever had.

### The report
First paragraph in plain words: does the node clock make clock searches and whole games repeatable (P2, Part C),
is the engine with the option off unchanged (P1), and what was cut. Then Part A; the patch (`nodeclock.patch.txt`)
with every place where the wall clock was replaced, by file and line; P1 to P5 with their numbers; Part C; files
of the repository you opened; stamps; what you did not do; what you are not sure about; a better way; model.
