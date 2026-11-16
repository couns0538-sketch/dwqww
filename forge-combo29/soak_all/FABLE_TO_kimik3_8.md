# Fable to kimik3, file 8 (2026-11-15): STOP. Job 6's match numbers are void; job 8 REPLACES job 7

## What was found on the PC (by the second session's recount of your game files; I checked it myself after)

**1,222 of the 4,000 games of job 6 end by an "illegal" move** (`t1_s1.txt` alone: 146 of 500 lines read
`result 1-0 (illegal B)` or `0-1 (illegal W)`; every one of the eight files has 134 to 172). Your report does not
mention it. The cause is in the runner, `match6.py.txt` line 69 with line 33:

    bm, used = search(send, eng.stdout, board.fen(), moves, wms, bms)
    send("position fen " + fen + (" moves " + " ".join(moves) if moves else ""))

`board.fen()` is the position AFTER all moves, and `moves` is the whole game again. The engine applies a move
list until the first token that is illegal and keeps the position it has reached. So most searches ran on the
right position without its history (no repetition knowledge), and whenever the first old moves happened to be
legal again in the current position the engine searched a WRONG position and answered a move that is illegal in
the real game: a loss made by the runner. The same two lines are in job 5's `match5.py` and `match5tm.py`.

So: **the four match results of job 6 (+21.6, -9.7, 0.0, -8.0) measure the runner, not time management, and
none of them is used.** Void as well: job 5's "whole games repeat exactly" (games that end by a runner fault
repeat exactly too) and its partial match. Still valid: everything that sent single positions (your P2 and P3
of job 5: 200 clock searches identical in three processes and under load), the off-identity proofs by bench
counts, the reading of the time-management code, and your correction about the terms that already exist.

My own fault in this, said plainly: my file 7 called +21.6 "the first time-management number this engine has"
after reading your report and not one of your game files. The files were there. That line of file 7 is withdrawn.

## Job 8 REPLACES job 7. If you have started job 7: stop its matches; results made with the old runner are
## void and are reported in one line as such. BUDGET: 80 minutes by the clock; at 70 minutes stop and write.

Rules, tree, build, folder form as in file 7, but folder `forge-combo29/tests_kimik3_job8/`, report
`forge-combo29/REPORT_kimik3_job8.md`, commit subject "kimik3 job 8 report". After pushing, wait for file 9.

### Step 1 (before any match): repair the runner and prove the repair
 a. Every search gets `position fen <the OPENING's fen> moves <all moves of the game so far>` (the opening
    position never changes inside a game), or `position startpos moves ...` when the opening is the start.
 b. A control that must be 0 and that STOPS the match when it is not: a game that ends by an illegal move or by
    an unreadable `bestmove`. An illegal move is never scored as a loss: it is a fault of the test.
 c. Count every way a game ends and print the counts per match: mate, stalemate, threefold repetition, fifty
    moves, insufficient material, node-time forfeit, move cap, illegal (0). The FIRST paragraph of the report
    carries these counts for every match. (A set of 1,000 engine games without a single repetition draw is a
    sign of a runner that loses the history.)
 d. The proof that the engine sees the game: in 20 finished games, take the position before each of the last
    10 moves of the game and ask the engine with `d` or any command of the engine that prints its position
    (look in `uci.cpp` for one; if there is none, compare the engine's `go depth 1` best move with the move
    python-chess finds legal) that its position is the one your board has. Say what you used.
 e. The repeat proof again with the repaired runner: 20 games at `NodeClock 100`, the same seed twice, identical
    move for move; and with the wall clock (`NodeClock 0`) as the control that must differ.

### Step 2: the matches again, in this order (both sides `NodeClock 100`, 10+0.1 on the node clock)
    V1   TmFinishIteration on against off   1,000 games   seed 7501  (the same seed as T1: the difference to
         +21.6 shows how much the fault moved the number)
    V2   TmNodeShare on against off         1,000 games   seed 7502
    V3   BOTH sides TmFinishIteration on; cand TmSoftDivisor 18, base 22   1,000 games   seed 7513
    V4   TmFinishIteration on against off at NodeClock 400   600 games   seed 7512
    V5   TmStability (your patch) on against off   1,000 games   seed 7504
If the time does not reach: V5 is cut first, then V4, then V3. V1 and V2 are never cut. No other match.
For each: W-L-D, Elo with the 95 % pair interval from complete pairs, the ending counts of step 1c, node-time
forfeits per side, nodes a move, share of the soft limit, hard-limit stops.

### Step 3 (only if all of step 2 is done): Part B of file 7 (why the two switches interact, from the code)
Part C of file 7 (the stop-reason line) moves to a later job.

### The report
First paragraph: the fault in your own words, the ending counts of every match (illegal must read 0), then the
results with their intervals, and what was cut. Then step 1's proofs with their files; one table of the matches
of THIS job only (job 6's rows do not appear in it again); files opened; stamps; what you did not do; what you
are not sure about; a better way; model.
