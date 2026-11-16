# Fable to deepseek, file 14 (2026-11-15): job 13 received, and job 14

## Your job 13 report

Received and read (first reading; the full reading follows in file 15). I note what your first line says: this
queue is now worked by a GLM 5.3 Flash model on the owner's instruction, and job 12's state left with the earlier
helper's machine. Understood; the queue keeps its name `deepseek` and its branch.
- **The two history terms overlap almost completely.** Both together against none: +9.0 [+1.7, +16.4] over two
  seeds that agree (+8.5 and +9.6); continuation history four plies back on top of the pawn history: +2.3 [-8.5,
  +13.0]; the pawn history on top of the continuation term: -2.4 [-13.0, +8.1]. So the bundle is worth what its
  better half is worth. That answers the owner's bundle question for these two with numbers: they are recorded
  as "one gain of about +9 on the plain tree, not two", and neither is ported on top of the newer switch set,
  where the pawn history alone already read +1.7.
- **The merge is proven the way the job asked** (both off = the four known answers and one sha256 over 2,000
  positions; each option alone = its own known numbers), and the compiler found the real conflict (the call both
  patches rewrote). The same job text went to another helper; if its merge and numbers agree with yours, that is
  the independent check.
- Your "dash-sentinel" fault hit a third time (a probe whose base side carried a literal `-`). Put the fix into
  your driver once, as a test that runs before any match: a probe line with an empty option list must build the
  same command as one without the field.
- NOTE: both sessions on the PC sleep from about 23:00 to 02:00 UTC tonight. If no file 15 comes after your
  report, keep waiting with the sleeping command as long as your run allows; the owner restarts you in the
  morning with the restart line, which finds the newest job by itself.

## Job 14. BUDGET: 90 minutes by the clock (from the moment you read this file); at 80 minutes stop and write.

Rules as in the first message of this queue (your own machine only, no pull request, no engine source committed,
new files only in your folder, text only, no binary files). Folder `forge-combo29/tests_deepseek_job14/`, report
`forge-combo29/REPORT_deepseek_job14.md`, commit subject "deepseek job 14 report". After pushing, wait for file 15
with the sleeping command; do not end your run.

### Why
Another helper (kimik3) wrote a "node clock": a UCI option `NodeClock N` that makes the engine count N nodes as
one millisecond in every time decision. With it a search "on the clock" and whole games repeat exactly on any
machine under any load, so the engine's TIME MANAGEMENT can be measured for the first time. Its author proved
that on its own machine. Before the patch is read line by line and built on the owner's PC, a second helper
repeats the proof independently and then uses the clock for a question its author does not test.

### Step 0
Base: commit `6b98f217` (`forge-combo29/src`, `include`, `CMakeLists.txt`), Release, g++, built WITH the C++
definition `-DFORGE_NNUE_V3=1` (the patch was written on that build; say if it also applies and passes without).
Known answers on the unpatched build: `bench 11` 312866, `bench 13` 862329, `bench 16` 3024920, `go perft 5`
4865609. The patch: `forge-combo29/tests_kimik3_job5/nodeclock.patch.txt` on branch
`for-fable-and-opus/kimik3-work` (fetch the branch by name; read only that folder and
`forge-combo29/REPORT_kimik3_job5.md`). Apply it; report how it applied (offsets, rejects).

### Part A (about 30 minutes): the proof again, by other hands
 A1. Option off = the old engine: the four known answers, and 2,000 positions (the first 2,000 lines of
     `UHO_Lichess_4852_v1.epd`, `go depth 9`) identical to the unpatched build in best move, score and nodes: one
     sha256 a side, the smallest node count.
 A2. Option on = repeatable: 100 of those positions, each with `go wtime 10000 btime 10000 winc 100 binc 100`
     and `NodeClock 100`, in three fresh processes: best move, score, depth and node count identical in all
     three. Then once more while four copies of the engine run `bench 16` beside it: still identical.
 A3. The control that shows the test can fail: the same 100 searches with `NodeClock 0` (the wall clock), three
     runs: how many differ in node count (it must be many).
 A4. The limits: for the 100 searches of A2 the node count at which each stopped; the largest and the mean, and
     how that compares with (10000 / 22 + 75) * 100 nodes, the soft limit its author describes (remaining / 22
     plus 0.75 of the increment).
 A5. Whole games: 20 games of the patched exe against itself, both sides `NodeClock 100`, time control 10+0.1,
     a generous real clock (say how you made sure nobody can lose on real time), played twice with the same
     seed: the two game files identical move for move, or the first game and move that differ.
Wait for every `bestmove` before the next command: a search is cut when more input is already waiting.

### Part B (about 45 minutes): the first measurement of how much time a move should get
The soft limit divides the remaining time by 22. Look in the `uci` answer and in the source whether that number
is a tunable option (its author calls it `TmSoftDivisor`); quote the line. If it is:
    V1   divisor 16 against 22     1,000 games   seed 7411   (more time early, less later)
    V2   divisor 30 against 22     1,000 games   seed 7412   (less time early, more later)
    V3   the better of the two against 22 again, 1,000 games, seed 7413 (a second seed; if time is left)
All on the node clock: both sides `NodeClock 100`, time control 10+0.1, Threads 1, Hash 16, `OwnBook false`, UHO
openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication. For each match:
W-L-D, Elo with the 95 % pair interval from complete pairs, losses on node time per side, the mean nodes a move
of each side, and the mean number of moves a game. If the divisor is NOT a tunable, say so and play instead:
time control 5+0.05 against itself as a plain check that results at two time controls are both repeatable
(20 games twice each), and stop there.

### The report
First paragraph in plain words: does the node clock hold up in other hands (A1 to A5, one line each), what the
divisor matches say with their intervals, and what was cut. Then the parts in order with their numbers and files;
one table of all matches; files of the repository you opened; stamps from the clock; what you did not do; what
you are not sure about; a better way; model.
