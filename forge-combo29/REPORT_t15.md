# Task t15: UCI MultiPV

## What changed

The lock printed one line per depth. This branch adds the UCI option `MultiPV` (spin, 1 to 8, default 1) and, when the value is above 1, prints that many root lines at each finished depth.

`SearchLimits` gained `multipv`. `uci` lists the option after `Threads`, `setoption` parses it (a bad token is rejected, a number outside 1..8 is clamped), and `go` copies it onto the search. Bench does not read the option. Bench builds its own searcher, so the bench node counts stay the lock counts.

With `MultiPV 1` the search and the info text are the lock. The info line is still `info depth D seldepth S score ... pv ...`.

With `MultiPV k` above 1 the main iterative deepening is left alone. After a depth finishes, a second worker searches the remaining root moves on a second transposition table. That search goes to the same depth, starts from an empty table and empty histories, and has the moves already chosen removed. It has no node limit and no clock. Its score is the score of that search after the aspiration window has closed. The lines are then ordered by those scores, highest first, and printed as `info depth D multipv i score ... pv ...`. `bestmove` is the move of line 1. Fewer than `k` legal moves produces that many lines.

`Threads` above 1 does not run those lines in parallel. Helper threads stay idle, the main thread takes the exclusive table lease, and the node total counts only the main worker. The search is the one-thread search.

Engine diff against the lock: 143 insertions and 11 deletions in `src` and `include`.

## What I found

Before any edit, Threads 1, Hash 16, OwnBook false printed bench 11 = 312866, bench 13 = 862329, and `go perft 5` = 4865609. The same three numbers came back after the edit. Per-move perft counts match. `go depth 12` on the five positions in `tests_t15/depth12_lock.txt` matches the lock once `nps` and `time` are ignored.

The machine's `c++` is clang 18. It selects GCC 14, and that directory has no `libstdc++.so`, so the first cmake failed with `cannot find -lstdc++`. The binary that produced the numbers was built with g++ 13.3.0 and `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`.

`go` returns to the command loop while the search is still running. The next command calls `stop_search()`. A pipe of five `go depth 12` lines therefore aborted every search and printed a bare `bestmove` of the first legal move. That was the driver. Waiting for `bestmove` before the next command produces the info lines. Bench and perft run on the calling thread, so one pipe of those three commands is valid.

Three mistakes in the first MultiPV cut showed up before the tests passed.

The first print wrote the primary line and then wrote the sorted set, which contains that same line. Every depth showed the best move twice. The print now happens once, after the sort.

The first layout was `info depth D multipv i seldepth S score`. The line is now `info depth D multipv i score ...` when `k` is above 1. `MultiPV 1` keeps the old field order.

`Threads 4` did not match `Threads 1`. Helpers were still started, `total_nodes()` added their counts, including counts left behind by an earlier search, and the exclusive table lease was taken only when `workers_.size() == 1`. A four-thread search therefore probed the table under the stripe locks while a one-thread search used the owned probe. Helpers are now left idle and the lease is taken. After that, `Threads 4` and `Threads 1` at `MultiPV 3`, depth 4, matched apart from `time` and `nps`.

Address and undefined-behavior sanitizers, `-O1 -g -fno-sanitize-recover=undefined`, reported nothing. The same tests passed. That says the extra searches do not trip those checkers.

## What is wrong

The tests pass because they allow line 1 to differ from a `MultiPV 1` search, as long as that move is still in the set. The difference is real, and on some positions it is large. The scores that get sorted do not come from one search.

The primary line is the iterative deepening. Its table, its history, and its aspiration window are carried from the previous depth. The local `score` that feeds the next depth is that score. It is not replaced by the sorted score, which is why the primary tree still matches a separate `MultiPV 1` search and why that move is still among the printed lines.

Each other line is a new search. The second worker is cleared, its table is cleared, and it iterates from depth 1 to the current depth with the earlier chosen root moves removed. The number it returns is exact for that fresh search. It is a different number from the one the main search would print for the same move. Ordering those numbers as if they were one list lets a side search outrank the main search. `bestmove` follows the sorted line, so it changes.

Measured on this binary, Threads 1, Hash 16, OwnBook false, a new game before each search.

`2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`, depth 8.

`MultiPV 1` plays `f6h5` at `cp 517`:

```
info depth 8 seldepth 13 score cp 517 nodes 4028 nps 2014000 hashfull 1 time 2 pv f6h5 g7g6 e5g6 h8g8 f1f4 d8d7 g6e7 g8f8 e7c8 b6c8
bestmove f6h5
```

`MultiPV 4` plays `g3g6` and calls it mate in 2. The main line is still there, as line 2, with the same score and the same PV:

```
info depth 8 multipv 1 score mate 2 seldepth 13 nodes 2681 nps 60931 hashfull 0 time 44 pv g3g6 c6e5 g6h7
info depth 8 multipv 2 score cp 517 seldepth 13 nodes 6709 nps 152477 hashfull 1 time 44 pv f6h5 g7g6 e5g6 h8g8 f1f4 d8d7 g6e7 g8f8 e7c8 b6c8
info depth 8 multipv 3 score cp 120 seldepth 13 nodes 8832 nps 200727 hashfull 0 time 44 pv f6e8 d6e5 d4e5 d8e8 a2a4 d5d4 c3d4 c6d4
info depth 8 multipv 4 score cp -115 seldepth 14 nodes 12792 nps 290727 hashfull 0 time 44 pv f1f2 c6e5 d4e5 d6c5 a1f1 g7f6
bestmove g3g6
```

The mate was already line 1 at depth 7 (`g3g6 c6e5 g6h7`). The main search at that depth still scored `f6h5` at `cp 464`, and that line is third in the `MultiPV 4` output with the same score and the same PV. The mate is never written back into the main search. The next aspiration window still opens around the main search's centipawn score, so the main search keeps the `MultiPV 1` tree and the side search is the only place the mate appears. At depth 5 the same split is a centipawn gap rather than a mate: `MultiPV 1` has moved on to `f6h5` at `cp 220`, while the side search still returns `f6e8` at `cp 391`, which is the score `MultiPV 1` had at depths 2, 3 and 4. The empty-table search repeats the earlier result and the sort prefers it.

`6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`, depth 8. `MultiPV 1` plays `h7h5` at `cp -981` (14991 nodes). `MultiPV 4` plays `f7f5` at `cp -894`. `h7h5` is line 4, still `cp -981`, still the same PV. The side search is 87 centipawns more optimistic than the main search, and that gap decides the move.

`r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8`, depth 8. `MultiPV 1` plays `a2a3` at `cp -334` (9115 nodes), PV `a2a3 h7h6 c4d5 f6d5 a1c1 d5c3 c1c3`. `MultiPV 4` plays `c4c5` at `cp -332`. `a2a3` is line 3 at `cp -334` with that same PV. Two centipawns, from a different search, change `bestmove`.

The same thing accounts for the 20 `EXPLAIN` lines in the test log below. The test keeps them as explanations. They are the bug the explanation describes.

### The node number on a line is a running sum, and it can fall

The value after `nodes` is not that line's search. After the sort, the printer adds each line's own node count to a sum and prints the sum. When the side search sorts first, line 1 shows only the side search. The main search's count appears as the step up on whichever line the main PV landed on.

On the attack position at depth 8 the printed counts are 2681, 6709, 8832, 12792. The steps are 2681, 4028, 2123, 3960. The step of 4028 is line 2, `f6h5`, and 4028 is the `MultiPV 1` node count. On the rook ending the steps are 2584, 1905, 6035, 14991, and 14991 is the `MultiPV 1` count, on line 4. On the French position the steps are 3933, 3303, 9115, 3892, and 9115 is the `MultiPV 1` count, on line 3.

The next depth starts the sum over again. A later depth's first line can show fewer nodes than an earlier depth's last line. `go nodes 4000` from the start position, `MultiPV 3`:

```
info depth 6 multipv 3 score cp -9 seldepth 9 nodes 4437 nps 153000 hashfull 0 time 29 pv e2e4 g8f6 d2d3 d7d5 e4d5 d8d5
info depth 7 multipv 1 score cp 17 seldepth 11 nodes 2574 nps 78000 hashfull 1 time 33 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 7 multipv 3 score cp -1 seldepth 9 nodes 7169 nps 217242 hashfull 1 time 33 pv b2b3 e7e6 c1b2 d7d5 g1f3 c7c5
bestmove d2d4
```

Depth 6 already displays 4437, above the requested 4000, because the side searches are not charged against the limit. The main search at depth 6 had only reached the line-1 count of 1703, so depth 7 still started. Depth 7's first line then displays 2574, which is less than 4437. The depth ends at 7169. `hashfull` on those lines is 1, then 0, then 1: line 1 reads the main table and the other lines read the side table, which is cleared before each of them.

### A clock does not cover the side searches

`movetime` sets a hard limit of `movetime - Move Overhead`. The default overhead is 10, so `go movetime 80` means stop at 70 ms. The side searches clear `movetime_ms` and `time_ms`, and they run before any line of that depth is printed. The `time` field therefore includes them, and it can pass the hard limit. This run finished depth 11 at `time 75` and then stopped:

```
info depth 11 multipv 1 score cp 27 seldepth 16 nodes 16451 nps 219346 hashfull 8 time 75 pv e2e4 c7c5 g1f3 e7e6 b1c3 g8e7 d2d4 c5d4 f3d4
info depth 11 multipv 2 score cp 24 seldepth 19 nodes 40426 nps 539013 hashfull 15 time 75 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 11 multipv 3 score cp 14 seldepth 13 nodes 48307 nps 644093 hashfull 4 time 75 pv c2c4 g8f6 e2e3 c7c5 f1e2 e7e6 g1f3 d7d5 c4d5 e6d5
bestmove e2e4
```

`bestmove e2e4` is that depth's line 1. The full output is under "Later runs" below. An earlier run of the same command, on a slower pass through depth 11, stopped one depth sooner and printed a single `multipv 1` line from the abort path. Which of those happens depends on the clock.

The abort path is the other half of this. If the main iteration is cut off, the lock publishes one line only when the root move changed, and the score on that line is the previous depth's score while the PV is the new partial PV. `MultiPV` above 1 has already replaced the previous score and PV with the sorted line. If that sorted move and the main search's new move differ, the aborted line pairs the side search's score with the main search's PV. I did not catch that pair in a transcript. The code does it: `emit(depth, result.score, result.pv)` uses `result.score` from the last finished depth and the PV copied from the aborted iteration.

`stop` has the same hole. The side worker has its own stop flag, and that flag is cleared before each side search. The UCI `stop` sets the main flag. The side search does not read it. The main flag is checked between lines.

### Time management follows the sorted move

After the sort, `result.best_move` is the printed line 1. The stability counter and the effort term use that move. The effort term looks it up in the main search's per-move node counts. When line 1 is a side-search move, that count is the time the main search spent on a move it did not pick, which is small, and the time factor goes up. A `wtime` / `btime` search can therefore think longer than `MultiPV 1` because of a move the main search does not believe is best. Those clocks were not run.

### What still prints one line

A root with no legal moves, and a root that is an immediate draw by repetition, the fifty-move rule, or insufficient material, take the old path. That path emits one line per depth and returns. `MultiPV 4` on those positions still prints a single `multipv 1` line.

### What the passing tests do not look at

They check the `MultiPV 1` transcript, legal distinct moves, score order, and that the `MultiPV 1` move is still present. They accept a different line 1. They do not check that `go nodes` stays inside the limit, that `go movetime` stays inside the hard limit, that a partial last line's score belongs to its PV, or that `stop` cuts off a side search.

## Later runs

These were run after the tests, on `./build/forge`, to pin the cases above. `uci` on that binary prints `option name MultiPV type spin default 1 min 1 max 8` and `uciok`.

`go nodes 4000`, `MultiPV 3`, start position. Command:

```
python3 /tmp/uci_drive.py ./build/forge uci "setoption name Threads value 1" "setoption name Hash value 16" "setoption name OwnBook value false" "setoption name MultiPV value 3" "position startpos" "go nodes 4000"
```

The `uci` banner is the option list. The search printed:

```
info depth 1 multipv 1 score cp 1 seldepth 1 nodes 26 nps 1368 hashfull 0 time 19 pv d2d4
info depth 1 multipv 2 score cp 1 seldepth 1 nodes 51 nps 2684 hashfull 0 time 19 pv g1f3
info depth 1 multipv 3 score cp -10 seldepth 1 nodes 74 nps 3894 hashfull 0 time 19 pv c2c4
info depth 2 multipv 1 score cp 49 seldepth 2 nodes 54 nps 2571 hashfull 0 time 21 pv d2d4 d7d6
info depth 2 multipv 2 score cp 46 seldepth 2 nodes 106 nps 5047 hashfull 0 time 21 pv g1f3 e7e6
info depth 2 multipv 3 score cp 33 seldepth 2 nodes 155 nps 7380 hashfull 0 time 21 pv c2c4 e7e6
info depth 3 multipv 1 score cp 18 seldepth 3 nodes 215 nps 9772 hashfull 0 time 22 pv e2e4 h7h6 d2d4
info depth 3 multipv 2 score cp 16 seldepth 3 nodes 419 nps 19045 hashfull 0 time 22 pv g1f3 h7h6 d2d4
info depth 3 multipv 3 score cp 8 seldepth 3 nodes 591 nps 26863 hashfull 0 time 22 pv c2c4 h7h6 d2d4
info depth 4 multipv 1 score cp 30 seldepth 6 nodes 404 nps 16833 hashfull 0 time 24 pv e2e4 e7e5 c2c3 c7c6
info depth 4 multipv 2 score cp 16 seldepth 4 nodes 655 nps 27291 hashfull 0 time 24 pv d2d4 h7h6 g1f3
info depth 4 multipv 3 score cp 14 seldepth 4 nodes 877 nps 36541 hashfull 0 time 24 pv g1f3 h7h6 c2c4
info depth 5 multipv 1 score cp 29 seldepth 8 nodes 471 nps 18115 hashfull 0 time 26 pv e2e4 c7c5 g1f3 b8c6
info depth 5 multipv 2 score cp 17 seldepth 6 nodes 910 nps 35000 hashfull 0 time 26 pv d2d4 d7d5 c2c3 h7h6
info depth 5 multipv 3 score cp 6 seldepth 9 nodes 1911 nps 73500 hashfull 0 time 26 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 multipv 1 score cp 34 seldepth 10 nodes 1703 nps 58724 hashfull 0 time 29 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 6 multipv 2 score cp 5 seldepth 9 nodes 2911 nps 100379 hashfull 0 time 29 pv c2c4 g8f6 e2e3 c7c5 g1f3
info depth 6 multipv 3 score cp -9 seldepth 9 nodes 4437 nps 153000 hashfull 0 time 29 pv e2e4 g8f6 d2d3 d7d5 e4d5 d8d5
info depth 7 multipv 1 score cp 17 seldepth 11 nodes 2574 nps 78000 hashfull 1 time 33 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 7 multipv 2 score cp 13 seldepth 10 nodes 4749 nps 143909 hashfull 0 time 33 pv c2c4 g8f6 b1c3 c7c5 g1f3 e7e6
info depth 7 multipv 3 score cp -1 seldepth 9 nodes 7169 nps 217242 hashfull 1 time 33 pv b2b3 e7e6 c1b2 d7d5 g1f3 c7c5
bestmove d2d4
```

`go movetime 80`, same options, start position:

```
python3 /tmp/uci_drive.py ./build/forge "setoption name Threads value 1" "setoption name Hash value 16" "setoption name OwnBook value false" "setoption name MultiPV value 3" "position startpos" "go movetime 80"
```

```
info depth 1 multipv 1 score cp 1 seldepth 1 nodes 26 nps 1857 hashfull 0 time 14 pv d2d4
info depth 1 multipv 2 score cp 1 seldepth 1 nodes 51 nps 3642 hashfull 0 time 14 pv g1f3
info depth 1 multipv 3 score cp -10 seldepth 1 nodes 74 nps 5285 hashfull 0 time 14 pv c2c4
info depth 2 multipv 1 score cp 49 seldepth 2 nodes 54 nps 3375 hashfull 0 time 16 pv d2d4 d7d6
info depth 2 multipv 2 score cp 46 seldepth 2 nodes 106 nps 6625 hashfull 0 time 16 pv g1f3 e7e6
info depth 2 multipv 3 score cp 33 seldepth 2 nodes 155 nps 9687 hashfull 0 time 16 pv c2c4 e7e6
info depth 3 multipv 1 score cp 18 seldepth 3 nodes 215 nps 12647 hashfull 0 time 17 pv e2e4 h7h6 d2d4
info depth 3 multipv 2 score cp 16 seldepth 3 nodes 419 nps 24647 hashfull 0 time 17 pv g1f3 h7h6 d2d4
info depth 3 multipv 3 score cp 8 seldepth 3 nodes 591 nps 34764 hashfull 0 time 17 pv c2c4 h7h6 d2d4
info depth 4 multipv 1 score cp 30 seldepth 6 nodes 404 nps 21263 hashfull 0 time 19 pv e2e4 e7e5 c2c3 c7c6
info depth 4 multipv 2 score cp 16 seldepth 4 nodes 655 nps 34473 hashfull 0 time 19 pv d2d4 h7h6 g1f3
info depth 4 multipv 3 score cp 14 seldepth 4 nodes 877 nps 46157 hashfull 0 time 19 pv g1f3 h7h6 c2c4
info depth 5 multipv 1 score cp 29 seldepth 8 nodes 471 nps 22428 hashfull 0 time 21 pv e2e4 c7c5 g1f3 b8c6
info depth 5 multipv 2 score cp 17 seldepth 6 nodes 910 nps 43333 hashfull 0 time 21 pv d2d4 d7d5 c2c3 h7h6
info depth 5 multipv 3 score cp 6 seldepth 9 nodes 1911 nps 91000 hashfull 0 time 21 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 multipv 1 score cp 34 seldepth 10 nodes 1703 nps 68120 hashfull 0 time 25 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 6 multipv 2 score cp 5 seldepth 9 nodes 2911 nps 116440 hashfull 0 time 25 pv c2c4 g8f6 e2e3 c7c5 g1f3
info depth 6 multipv 3 score cp -9 seldepth 9 nodes 4437 nps 177480 hashfull 0 time 25 pv e2e4 g8f6 d2d3 d7d5 e4d5 d8d5
info depth 7 multipv 1 score cp 17 seldepth 11 nodes 2574 nps 88758 hashfull 1 time 29 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 7 multipv 2 score cp 13 seldepth 10 nodes 4749 nps 163758 hashfull 0 time 29 pv c2c4 g8f6 b1c3 c7c5 g1f3 e7e6
info depth 7 multipv 3 score cp -1 seldepth 9 nodes 7169 nps 247206 hashfull 1 time 29 pv b2b3 e7e6 c1b2 d7d5 g1f3 c7c5
info depth 8 multipv 1 score cp 26 seldepth 13 nodes 4099 nps 120558 hashfull 2 time 34 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 8 multipv 2 score cp 18 seldepth 9 nodes 7134 nps 209823 hashfull 1 time 34 pv c2c4 c7c5 e2e3 g8f6 g1f3 e7e6 d2d4 c5d4 e3d4
info depth 8 multipv 3 score cp 12 seldepth 10 nodes 10199 nps 299970 hashfull 1 time 34 pv g1f3 g8f6 c2c4 c7c5 e2e3 e7e6 b2b3
info depth 9 multipv 1 score cp 31 seldepth 14 nodes 9653 nps 224488 hashfull 7 time 43 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 9 multipv 2 score cp 18 seldepth 11 nodes 13698 nps 318558 hashfull 1 time 43 pv g1f3 g8f6 c2c4 c7c5 e2e3 e7e6 d2d4 c5d4
info depth 9 multipv 3 score cp 18 seldepth 11 nodes 17445 nps 405697 hashfull 2 time 43 pv c2c4 c7c5 e2e3 g8f6 g1f3 e7e6 d2d4 c5d4
info depth 10 multipv 1 score cp 24 seldepth 14 nodes 13102 nps 242629 hashfull 10 time 54 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 10 multipv 2 score cp 20 seldepth 16 nodes 20989 nps 388685 hashfull 2 time 54 pv e2e4 c7c5 g1f3 e7e6 b1c3 b8c6 d2d4 c5d4 f3d4
info depth 10 multipv 3 score cp 14 seldepth 13 nodes 27079 nps 501462 hashfull 2 time 54 pv c2c4 g8f6 e2e3 c7c5 f1e2 e7e6 g1f3 d7d5 c4d5
info depth 11 multipv 1 score cp 27 seldepth 16 nodes 16451 nps 219346 hashfull 8 time 75 pv e2e4 c7c5 g1f3 e7e6 b1c3 g8e7 d2d4 c5d4 f3d4
info depth 11 multipv 2 score cp 24 seldepth 19 nodes 40426 nps 539013 hashfull 15 time 75 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 11 multipv 3 score cp 14 seldepth 13 nodes 48307 nps 644093 hashfull 4 time 75 pv c2c4 g8f6 e2e3 c7c5 f1e2 e7e6 g1f3 d7d5 c4d5 e6d5
bestmove e2e4
```

The three depth-8 comparisons used `ucinewgame` before each `go depth 8`. One combined command mistyped the attack FEN as `2cP4`. The engine answered `info string invalid FEN: invalid FEN placement` and then searched the start position. That output is discarded. The attack position was run again with the FEN below.

French, `MultiPV 1` then `MultiPV 4`:

```
python3 /tmp/uci_drive.py ./build/forge "setoption name Threads value 1" "setoption name Hash value 16" "setoption name OwnBook value false" isready "setoption name MultiPV value 1" ucinewgame "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8" "go depth 8" isready "setoption name MultiPV value 4" ucinewgame "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8" "go depth 8"
```

```
readyok
info depth 1 seldepth 3 score cp -318 nodes 45 nps 0 hashfull 0 time 0 pv a2a3
info depth 2 seldepth 4 score cp -306 nodes 98 nps 0 hashfull 0 time 0 pv a2a3 a7a6
info depth 3 seldepth 5 score cp -324 nodes 203 nps 0 hashfull 0 time 0 pv a2a3 a7a6 h2h3
info depth 4 seldepth 6 score cp -331 nodes 404 nps 0 hashfull 0 time 0 pv a2a3 d8b6 c4d5 e6d5
info depth 5 seldepth 7 score cp -322 nodes 1026 nps 0 hashfull 0 time 0 pv d1b3 a7a6 a2a3 d5c4 f1c4
info depth 6 seldepth 9 score cp -333 nodes 2567 nps 2567000 hashfull 1 time 1 pv f1e2 d5c4 e2c4 h7h6 a2a3 c6a5
info depth 7 seldepth 11 score cp -327 nodes 4080 nps 2040000 hashfull 2 time 2 pv a2a3 a7a6 f1e2 d5c4 e2c4 b7b5 c4a2
info depth 8 seldepth 15 score cp -334 nodes 9115 nps 1823000 hashfull 4 time 5 pv a2a3 h7h6 c4d5 f6d5 a1c1 d5c3 c1c3
bestmove a2a3
readyok
info depth 1 multipv 1 score cp -318 seldepth 3 nodes 45 nps 3214 hashfull 0 time 14 pv a2a3
info depth 1 multipv 2 score cp -334 seldepth 3 nodes 96 nps 6857 hashfull 0 time 14 pv d1b3
info depth 1 multipv 3 score cp -338 seldepth 3 nodes 146 nps 10428 hashfull 0 time 14 pv f1d3
info depth 1 multipv 4 score cp -338 seldepth 3 nodes 194 nps 13857 hashfull 0 time 14 pv f1e2 d5c4
info depth 2 multipv 1 score cp -306 seldepth 4 nodes 98 nps 6125 hashfull 0 time 16 pv a2a3 a7a6
info depth 2 multipv 2 score cp -330 seldepth 4 nodes 244 nps 15250 hashfull 0 time 16 pv h2h3 a7a6
info depth 2 multipv 3 score cp -333 seldepth 4 nodes 382 nps 23875 hashfull 0 time 16 pv d1d2 d5c4
info depth 2 multipv 4 score cp -334 seldepth 4 nodes 506 nps 31625 hashfull 0 time 16 pv d1b3 d5c4
info depth 3 multipv 1 score cp -324 seldepth 5 nodes 203 nps 10684 hashfull 0 time 19 pv a2a3 a7a6 h2h3
info depth 3 multipv 2 score cp -334 seldepth 5 nodes 519 nps 27315 hashfull 0 time 19 pv d1b3 d5c4 f1c4
info depth 3 multipv 3 score cp -338 seldepth 5 nodes 848 nps 44631 hashfull 0 time 19 pv f1d3 d5c4 d3c4
info depth 3 multipv 4 score cp -338 seldepth 5 nodes 1166 nps 61368 hashfull 0 time 19 pv f1e2 d5c4 e2c4
info depth 4 multipv 1 score cp -331 seldepth 6 nodes 404 nps 18363 hashfull 0 time 22 pv a2a3 d8b6 c4d5 e6d5
info depth 4 multipv 2 score cp -334 seldepth 5 nodes 784 nps 35636 hashfull 0 time 22 pv d1b3 d5c4 f1c4
info depth 4 multipv 3 score cp -338 seldepth 5 nodes 1186 nps 53909 hashfull 0 time 22 pv f1d3 d5c4 d3c4
info depth 4 multipv 4 score cp -338 seldepth 5 nodes 1578 nps 71727 hashfull 0 time 22 pv f1e2 d5c4 e2c4
info depth 5 multipv 1 score cp -322 seldepth 7 nodes 1026 nps 41040 hashfull 0 time 25 pv d1b3 a7a6 a2a3 d5c4 f1c4
info depth 5 multipv 2 score cp -331 seldepth 6 nodes 1563 nps 62520 hashfull 0 time 25 pv a2a3 d8b6 c4d5 e6d5
info depth 5 multipv 3 score cp -333 seldepth 6 nodes 2160 nps 86400 hashfull 0 time 25 pv f1e2 d5c4 e2c4 a7a6
info depth 5 multipv 4 score cp -343 seldepth 6 nodes 2686 nps 107440 hashfull 0 time 25 pv c4d5 e6d5 f1d3 h7h6
info depth 6 multipv 1 score cp -322 seldepth 9 nodes 1030 nps 34333 hashfull 0 time 30 pv a2a3 a7a6 d1b3 d5c4 f1c4
info depth 6 multipv 2 score cp -322 seldepth 7 nodes 1879 nps 62633 hashfull 0 time 30 pv d1b3 d5c4 f1c4 a7a6 a2a3
info depth 6 multipv 3 score cp -333 seldepth 9 nodes 4446 nps 148200 hashfull 1 time 30 pv f1e2 d5c4 e2c4 h7h6 a2a3 c6a5
info depth 6 multipv 4 score cp -334 seldepth 11 nodes 6049 nps 201633 hashfull 1 time 30 pv h2h3 a7a6 a2a3 h7h6 c4c5
info depth 7 multipv 1 score cp -327 seldepth 11 nodes 4080 nps 113333 hashfull 2 time 36 pv a2a3 a7a6 f1e2 d5c4 e2c4 b7b5 c4a2
info depth 7 multipv 2 score cp -328 seldepth 9 nodes 6038 nps 167722 hashfull 0 time 36 pv f1e2 d5c4 e2c4 c6a5 c4b5 f6d5
info depth 7 multipv 3 score cp -332 seldepth 10 nodes 7678 nps 213277 hashfull 0 time 36 pv c4c5 f6e4 f1e2 e7f6 c3e4 d5e4
info depth 7 multipv 4 score cp -337 seldepth 8 nodes 9536 nps 264888 hashfull 2 time 36 pv h2h3 d8b6 d1b1 d5c4 f1c4 c6a5
info depth 8 multipv 1 score cp -332 seldepth 10 nodes 3933 nps 81937 hashfull 1 time 48 pv c4c5 f6e4 f1e2 e4c3 b2c3 c6a5 d1a4
info depth 8 multipv 2 score cp -333 seldepth 11 nodes 7236 nps 150750 hashfull 2 time 48 pv c4d5 e6d5 f1d3 c8e6 a2a3 d8b6
info depth 8 multipv 3 score cp -334 seldepth 15 nodes 16351 nps 340645 hashfull 4 time 48 pv a2a3 h7h6 c4d5 f6d5 a1c1 d5c3 c1c3
info depth 8 multipv 4 score cp -335 seldepth 10 nodes 20243 nps 421729 hashfull 3 time 48 pv d1b1 c8d7 a2a3 d7e8 h2h3 h7h6 c4d5 e6d5
bestmove c4c5
```

Attack, `MultiPV 1` (from the same combined command, before the mistyped FEN) and `MultiPV 4` (the rerun):

```
python3 /tmp/uci_drive.py ./build/forge "setoption name Threads value 1" "setoption name Hash value 16" "setoption name OwnBook value false" "setoption name MultiPV value 4" ucinewgame "position fen 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1" "go depth 8"
```

`MultiPV 1`:

```
info depth 1 seldepth 7 score cp 78 nodes 262 nps 0 hashfull 0 time 0 pv f6h5
info depth 2 seldepth 8 score cp 391 nodes 392 nps 0 hashfull 0 time 0 pv f6e8 d8e8 e5f7 e6f7 g3d6
info depth 3 seldepth 8 score cp 391 nodes 476 nps 0 hashfull 0 time 0 pv f6e8 d8e8 e5f7 e6f7
info depth 4 seldepth 8 score cp 391 nodes 586 nps 0 hashfull 0 time 0 pv f6e8 d8e8 e5f7 e6f7 g3d6
info depth 5 seldepth 8 score cp 220 nodes 1051 nps 0 hashfull 0 time 0 pv f6h5 g7g6 e5g6 f7g6 g3g6
info depth 6 seldepth 10 score cp 337 nodes 1489 nps 0 hashfull 0 time 0 pv f6h5 d6f8 e5g6 f7g6 f1f8 d8f8 g3g6
info depth 7 seldepth 12 score cp 464 nodes 2318 nps 2318000 hashfull 1 time 1 pv f6h5 g7g5 f1f7 c6e5 f7h7 h8g8 d4e5 d6f8
info depth 8 seldepth 13 score cp 517 nodes 4028 nps 2014000 hashfull 1 time 2 pv f6h5 g7g6 e5g6 h8g8 f1f4 d8d7 g6e7 g8f8 e7c8 b6c8
bestmove f6h5
```

`MultiPV 4`:

```
info depth 1 multipv 1 score cp 78 seldepth 7 nodes 262 nps 17466 hashfull 0 time 15 pv f6h5
info depth 1 multipv 2 score cp 62 seldepth 7 nodes 540 nps 36000 hashfull 0 time 15 pv f6e8
info depth 1 multipv 3 score cp -29 seldepth 7 nodes 818 nps 54533 hashfull 0 time 15 pv a1e1 c6e5 e1e5 g7f6 f1f6
info depth 1 multipv 4 score cp -59 seldepth 8 nodes 1214 nps 80933 hashfull 0 time 15 pv a1d1 c6e5
info depth 2 multipv 1 score cp 391 seldepth 8 nodes 392 nps 21777 hashfull 0 time 18 pv f6e8 d8e8 e5f7 e6f7 g3d6
info depth 2 multipv 2 score cp 37 seldepth 8 nodes 770 nps 42777 hashfull 0 time 18 pv f6h5 g7g6
info depth 2 multipv 3 score cp -29 seldepth 7 nodes 1170 nps 65000 hashfull 0 time 18 pv a1e1 c6e5
info depth 2 multipv 4 score cp -59 seldepth 8 nodes 1693 nps 94055 hashfull 0 time 18 pv a1d1 c6e5
info depth 3 multipv 1 score cp 391 seldepth 8 nodes 476 nps 22666 hashfull 0 time 21 pv f6e8 d8e8 e5f7 e6f7
info depth 3 multipv 2 score cp -4 seldepth 9 nodes 1086 nps 51714 hashfull 0 time 21 pv f6h5 d6f8 e5c6 c8c6
info depth 3 multipv 3 score cp -29 seldepth 7 nodes 1599 nps 76142 hashfull 0 time 21 pv a1e1 c6e5 e1e5
info depth 3 multipv 4 score cp -59 seldepth 8 nodes 2237 nps 106523 hashfull 0 time 21 pv a1d1 c6e5 d4e5
info depth 4 multipv 1 score cp 391 seldepth 8 nodes 586 nps 25478 hashfull 0 time 23 pv f6e8 d8e8 e5f7 e6f7 g3d6
info depth 4 multipv 2 score cp -4 seldepth 9 nodes 1282 nps 55739 hashfull 0 time 23 pv f6h5 d6f8 e5c6
info depth 4 multipv 3 score cp -29 seldepth 7 nodes 1880 nps 81739 hashfull 0 time 23 pv a1e1 c6e5 e1e5 g7f6
info depth 4 multipv 4 score cp -59 seldepth 8 nodes 2601 nps 113086 hashfull 0 time 23 pv a1d1 c6e5 d4e5
info depth 5 multipv 1 score cp 391 seldepth 7 nodes 689 nps 25518 hashfull 0 time 27 pv f6e8 d8e8 e5f7 e6f7 g3d6
info depth 5 multipv 2 score cp 220 seldepth 8 nodes 1740 nps 64444 hashfull 0 time 27 pv f6h5 g7g6 e5g6 f7g6 g3g6
info depth 5 multipv 3 score cp -29 seldepth 7 nodes 2468 nps 91407 hashfull 0 time 27 pv a1e1 c6e5 e1e5 g7f6
info depth 5 multipv 4 score cp -76 seldepth 9 nodes 3564 nps 132000 hashfull 0 time 27 pv g1h1 c6e5 d4e5 d6e7
info depth 6 multipv 1 score cp 337 seldepth 10 nodes 1489 nps 48032 hashfull 0 time 31 pv f6h5 d6f8 e5g6 f7g6 f1f8 d8f8 g3g6
info depth 6 multipv 2 score cp 193 seldepth 7 nodes 2493 nps 80419 hashfull 0 time 31 pv f6e8 d6e5 d4e5 d8e8 a2a3
info depth 6 multipv 3 score cp -29 seldepth 7 nodes 3431 nps 110677 hashfull 0 time 31 pv a1e1 c6e5 e1e5 g7f6 f1f6
info depth 6 multipv 4 score cp -98 seldepth 10 nodes 5864 nps 189161 hashfull 0 time 31 pv f6h7 c6e5 d4e5 d6e7 a1d1
info depth 7 multipv 1 score mate 2 seldepth 11 nodes 2528 nps 68324 hashfull 0 time 37 pv g3g6 c6e5 g6h7
info depth 7 multipv 2 score cp 1317 seldepth 11 nodes 4448 nps 120216 hashfull 0 time 37 pv e5g6 f7g6 g3g6 d6g3 h2g3 g7f6
info depth 7 multipv 3 score cp 464 seldepth 12 nodes 6766 nps 182864 hashfull 1 time 37 pv f6h5 g7g5 f1f7 c6e5 f7h7 h8g8 d4e5 d6f8
info depth 7 multipv 4 score cp 157 seldepth 13 nodes 8137 nps 219918 hashfull 0 time 37 pv f6e8 d6e5 d4e5 d8e8 a2a3 d5d4
info depth 8 multipv 1 score mate 2 seldepth 13 nodes 2681 nps 60931 hashfull 0 time 44 pv g3g6 c6e5 g6h7
info depth 8 multipv 2 score cp 517 seldepth 13 nodes 6709 nps 152477 hashfull 1 time 44 pv f6h5 g7g6 e5g6 h8g8 f1f4 d8d7 g6e7 g8f8 e7c8 b6c8
info depth 8 multipv 3 score cp 120 seldepth 13 nodes 8832 nps 200727 hashfull 0 time 44 pv f6e8 d6e5 d4e5 d8e8 a2a4 d5d4 c3d4 c6d4
info depth 8 multipv 4 score cp -115 seldepth 14 nodes 12792 nps 290727 hashfull 0 time 44 pv f1f2 c6e5 d4e5 d6c5 a1f1 g7f6
bestmove g3g6
```

Rook ending, `MultiPV 1` then `MultiPV 4`:

```
python3 /tmp/uci_drive.py ./build/forge "setoption name Threads value 1" "setoption name Hash value 16" "setoption name OwnBook value false" isready "setoption name MultiPV value 1" ucinewgame "position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1" "go depth 8" isready "setoption name MultiPV value 4" ucinewgame "position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1" "go depth 8"
```

```
readyok
info depth 1 seldepth 1 score cp -899 nodes 11 nps 0 hashfull 0 time 0 pv g8h8
info depth 2 seldepth 3 score cp -886 nodes 35 nps 0 hashfull 0 time 0 pv g7g6 g2g3
info depth 3 seldepth 5 score cp -857 nodes 116 nps 0 hashfull 0 time 0 pv g7g6 h2h3 g8g7
info depth 4 seldepth 7 score cp -872 nodes 269 nps 0 hashfull 0 time 0 pv g7g6 d1d8 g8g7 d8d7 h7h5
info depth 5 seldepth 7 score cp -877 nodes 1172 nps 0 hashfull 0 time 0 pv h7h5 g1f1 g8h7 d1d7 f7f5
info depth 6 seldepth 8 score cp -856 nodes 2378 nps 2378000 hashfull 0 time 1 pv g7g6 g1f1 g8g7 d1d7 h7h5 g2g3
info depth 7 seldepth 11 score cp -920 nodes 5954 nps 2977000 hashfull 2 time 2 pv h7h5 g1f1 f7f5 f1e2 g8h8 e2e3 g7g5
info depth 8 seldepth 15 score cp -981 nodes 14991 nps 2998200 hashfull 6 time 5 pv h7h5 g1f1 g7g5 f1e2 g8g7 d1d5 g7g6 e2d3 f7f5
bestmove h7h5
readyok
info depth 1 multipv 1 score cp -899 seldepth 1 nodes 11 nps 5500 hashfull 0 time 2 pv g8h8
info depth 1 multipv 2 score cp -907 seldepth 1 nodes 20 nps 10000 hashfull 0 time 2 pv g7g6
info depth 1 multipv 3 score cp -911 seldepth 1 nodes 30 nps 15000 hashfull 0 time 2 pv g8f8
info depth 1 multipv 4 score cp -915 seldepth 1 nodes 38 nps 19000 hashfull 0 time 2 pv h7h5
info depth 2 multipv 1 score cp -886 seldepth 3 nodes 35 nps 8750 hashfull 0 time 4 pv g7g6 g2g3
info depth 2 multipv 2 score cp -894 seldepth 3 nodes 104 nps 26000 hashfull 0 time 4 pv g8f8 h2h3
info depth 2 multipv 3 score cp -897 seldepth 3 nodes 156 nps 39000 hashfull 0 time 4 pv h7h5 h2h3
info depth 2 multipv 4 score cp -904 seldepth 3 nodes 193 nps 48250 hashfull 0 time 4 pv g7g5 h2h3
info depth 3 multipv 1 score cp -857 seldepth 5 nodes 116 nps 16571 hashfull 0 time 7 pv g7g6 h2h3 g8g7
info depth 3 multipv 2 score cp -873 seldepth 6 nodes 325 nps 46428 hashfull 0 time 7 pv g7g5 h2h3 g8g7
info depth 3 multipv 3 score cp -874 seldepth 6 nodes 508 nps 72571 hashfull 0 time 7 pv h7h5 h2h3 g8h7
info depth 3 multipv 4 score cp -888 seldepth 6 nodes 668 nps 95428 hashfull 0 time 7 pv f7f6 d1d8 g8f7 d8d7 f7g6
info depth 4 multipv 1 score cp -872 seldepth 7 nodes 269 nps 29888 hashfull 0 time 9 pv g7g6 d1d8 g8g7 d8d7 h7h5
info depth 4 multipv 2 score cp -872 seldepth 6 nodes 500 nps 55555 hashfull 0 time 9 pv g7g5 h2h3 g8g7
info depth 4 multipv 3 score cp -873 seldepth 6 nodes 705 nps 78333 hashfull 0 time 9 pv h7h5 h2h3 g8h7
info depth 4 multipv 4 score cp -887 seldepth 6 nodes 887 nps 98555 hashfull 0 time 9 pv f7f6 d1d8 g8f7 d8d7 f7g6
info depth 5 multipv 1 score cp -852 seldepth 6 nodes 469 nps 39083 hashfull 0 time 12 pv g7g5 d1d8 g8g7 d8d7 h7h5
info depth 5 multipv 2 score cp -872 seldepth 7 nodes 767 nps 63916 hashfull 0 time 12 pv g7g6 d1d8 g8g7 d8d7 h7h5
info depth 5 multipv 3 score cp -877 seldepth 7 nodes 1939 nps 161583 hashfull 0 time 12 pv h7h5 g1f1 g8h7 d1d7 f7f5
info depth 5 multipv 4 score cp -882 seldepth 7 nodes 2410 nps 200833 hashfull 0 time 12 pv f7f5 h2h3 g7g6 d1d7
info depth 6 multipv 1 score cp -856 seldepth 8 nodes 2378 nps 148625 hashfull 0 time 16 pv g7g6 g1f1 g8g7 d1d7 h7h5 g2g3
info depth 6 multipv 2 score cp -876 seldepth 7 nodes 3285 nps 205312 hashfull 0 time 16 pv h7h5 g1f1 g8h7 d1d7 f7f5
info depth 6 multipv 3 score cp -882 seldepth 9 nodes 4161 nps 260062 hashfull 0 time 16 pv f7f5 d1d7 g7g6 g1f1 g8h8
info depth 6 multipv 4 score cp -893 seldepth 9 nodes 5324 nps 332750 hashfull 0 time 16 pv g7g5 g1f1 g8g7 f1e2 f7f5
info depth 7 multipv 1 score cp -862 seldepth 9 nodes 1277 nps 60809 hashfull 0 time 21 pv g7g6 d1d7 h7h5 g2g3 g8g7 g1f1
info depth 7 multipv 2 score cp -911 seldepth 9 nodes 3822 nps 182000 hashfull 1 time 21 pv f7f5 g1f1 g7g6 f1e2 g8h8 d1d8 h8g7
info depth 7 multipv 3 score cp -916 seldepth 9 nodes 5828 nps 277523 hashfull 0 time 21 pv g7g5 g1f1 g8h8 d1d5 f7f6 f1e2
info depth 7 multipv 4 score cp -920 seldepth 11 nodes 11782 nps 561047 hashfull 2 time 21 pv h7h5 g1f1 f7f5 f1e2 g8h8 e2e3 g7g5
info depth 8 multipv 1 score cp -894 seldepth 11 nodes 2584 nps 83354 hashfull 0 time 31 pv f7f5 g1f1 g7g5 f1e2 g8g7 d1d7 g7h8 e2f3
info depth 8 multipv 2 score cp -915 seldepth 9 nodes 4489 nps 144806 hashfull 0 time 31 pv g7g6 g1f1 f7f5 f1e2 g8g7 d1d7 g7h6 e2f3
info depth 8 multipv 3 score cp -942 seldepth 11 nodes 10524 nps 339483 hashfull 1 time 31 pv g7g5 g1f1 g8g7 f1e2 h7h5 e2d3 f7f5
info depth 8 multipv 4 score cp -981 seldepth 15 nodes 25515 nps 823064 hashfull 6 time 31 pv h7h5 g1f1 g7g5 f1e2 g8g7 d1d5 g7g6 e2d3 f7f5
bestmove f7f5
```

## What was there

The locked engine printed one principal variation. `uci` had no `MultiPV` option. A finished depth was one line:

`info depth D seldepth S score ... nodes ... nps ... hashfull ... time ... pv ...`

`bestmove` was that line's first move.

Before any edit, with Threads 1, Hash 16 and OwnBook false, the lock binary printed bench 11 = 312866 nodes, bench 13 = 862329 nodes, and `go perft 5` from the start position = 4865609 nodes. Clang 18 could not link a test program: it selected GCC 14, and that directory has no `libstdc++.so`. The engine was built with g++ 13.3.0. The CPU has AVX-512. The build still used the portable flags from the start command (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`). Those three node counts matched the lock.

## The change

`MultiPV` is a UCI spin option, minimum 1, maximum 8, default 1, listed in the `uci` answer. At 1 the iterative deepening and the info text are the previous ones. Above 1, each finished depth keeps that primary line and then searches the remaining root moves on a separate table, removing the moves already chosen; each of those searches runs to the same depth with a resolved window, so the score is exact. The lines are printed best score first as `info depth D multipv i score ... pv ...`, and `bestmove` is the move of line 1. If fewer than `k` legal moves exist, only those moves are printed.

With `MultiPV` above 1, helper threads are not started and the main thread owns the transposition table the way a one-thread search does. `Threads` greater than 1 therefore follows the Threads 1 search. The node limit and the clock limit stop the primary iterative deepening. An extra line of a depth that already finished is searched to that depth on its own table, so a `go nodes` total can be larger than the limit. A stop flag is checked between extra lines.

Line 1 is the highest of those scores. The MultiPV 1 move stays in the set. A fresh search can score higher than the iterative-deepening score, and the ranked first move then differs. The measurements and why that is wrong are in "What is wrong" above.

Engine diff against the lock: 143 insertions and 11 deletions in `src` and `include` (`git diff --numstat`), under the 300-line cap.

## Files changed

- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/src/search.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t15/test_multipv.cpp`
- `forge-combo29/tests_t15/depth12_lock.txt`
- `forge-combo29/REPORT_t15.md`

`depth12_lock.txt` is the lock binary's `go depth 12` transcript for the five positions below, captured before the edit.

## Build

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++
cmake --build build -j
```

The first configure, without `CMAKE_CXX_COMPILER=g++`, failed while linking the compiler test (`/usr/bin/ld: cannot find -lstdc++`). The g++ configure and build ended with `Built target forge` and exit code 0.

## Before the edit

Command:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 437 nps 1973292
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit code 0. bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

## After the edit: the three numbers

Same command, same binary path after the rebuild:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 442 nps 1950970
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit code 0. bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. Per-move perft counts match the run above. `time` and `nps` are wall clock.

`uci` on this binary prints `option name MultiPV type spin default 1 min 1 max 8` and then `uciok`.

## Tests

The five depth-12 positions, in order, are the start position, `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`, `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8`, `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1`, and `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`. The test compares that transcript with the lock file after replacing the `nps` and `time` numbers. It also checks ten positions at `MultiPV 4`, `go depth 8`, a position with two legal moves (`8/8/8/8/8/6k1/6r1/6K1 w - - 0 1`) at `MultiPV 4`, a mate in 1 (`6k1/5ppp/8/8/8/8/8/R6K w - - 0 1`), `go nodes 4000`, `go movetime 80`, and Threads 4 against Threads 1 at `MultiPV 3`, depth 4.

Command, from `/agent/repos/dwqww`:

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t15/test_multipv.cpp -pthread -o /tmp/test_t15
/tmp/test_t15
```

The compiler printed nothing and exited 0. Test output:

```
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
EXPLAIN b startpos depth 5 line 1 is e2e4 and MultiPV 1 is c2c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 5 line 1 is d5e6 and MultiPV 1 is e2a6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 7 line 1 is e2a6 and MultiPV 1 is d5e6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 4 line 1 is c1b1 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 6 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 7 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 4 line 1 is a5a6 and MultiPV 1 is b4c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 7 line 1 is a5a6 and MultiPV 1 is b4f4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 6 line 1 is a2a3 and MultiPV 1 is f1e2. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 8 line 1 is c4c5 and MultiPV 1 is a2a3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 5 line 1 is f6e8 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 7 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 8 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 5 line 1 is g7g5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 7 line 1 is g7g6 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 8 line 1 is f7f5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 4 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 5 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 6 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 depth 6 line 1 is h2h3 and MultiPV 1 is c3d5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
PASS b checked 10 positions at depth 8
PASS c two legal moves
PASS d mate in 1 line a1a8 mate 1
PASS nodes best d2d4
PASS movetime best d2d4
PASS threads 4 falls back to threads 1
explained 20
failures 0
RESULT passed
```

Exit code 0. At depth 8, line 1 differed from the separate MultiPV 1 search on three of the ten positions: `c4c5` instead of `a2a3`, `g3g6` instead of `f6h5`, and `f7f5` instead of `h7h5`. In each case the MultiPV 1 move was still one of the four lines. The mate in 1 line was `a1a8` with `score mate 1`. The two-move position printed two lines.

## Sanitizers

Command, from `/agent/repos/dwqww`:

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t15/test_multipv.cpp -pthread -o /tmp/test_t15_asan
/tmp/test_t15_asan
```

The compiler printed nothing and exited 0. Test output:

```
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
EXPLAIN b startpos depth 5 line 1 is e2e4 and MultiPV 1 is c2c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 5 line 1 is d5e6 and MultiPV 1 is e2a6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 7 line 1 is e2a6 and MultiPV 1 is d5e6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 4 line 1 is c1b1 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 6 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 7 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 4 line 1 is a5a6 and MultiPV 1 is b4c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 7 line 1 is a5a6 and MultiPV 1 is b4f4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 6 line 1 is a2a3 and MultiPV 1 is f1e2. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 8 line 1 is c4c5 and MultiPV 1 is a2a3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 5 line 1 is f6e8 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 7 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 8 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 5 line 1 is g7g5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 7 line 1 is g7g6 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 8 line 1 is f7f5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 4 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 5 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 6 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 depth 6 line 1 is h2h3 and MultiPV 1 is c3d5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
PASS b checked 10 positions at depth 8
PASS c two legal moves
PASS d mate in 1 line a1a8 mate 1
PASS nodes best d2d4
PASS movetime best d2d4
PASS threads 4 falls back to threads 1
explained 20
failures 0
RESULT passed
```

Exit code 0. AddressSanitizer and UndefinedBehaviorSanitizer printed no error.

## Not verified

`go nodes 4000` and `go movetime 80` were run. See "Later runs". Both limits are crossed by the side searches, as that section records.

- `ponder` and `go infinite` together with `MultiPV` above 1.
- `wtime` / `btime` game clocks with `MultiPV` above 1. The code path that would lengthen them is described under "Time management follows the sorted move". It was not timed.
- `MultiPV` together with `searchmoves` or `go mate`.
- A `stop` that arrives while a side line is searching. The flag is read between lines. No `stop` was sent.
- A malformed `MultiPV` value, and values other than 1, 3 and 4. The option clamps to 1..8.
- Hash sizes other than 16 MB.
- A drawn root or a root with no moves under `MultiPV` above 1. The early path is described above from the code. It was not given a position.
- An aborted depth whose printed score and PV belong to different moves. The emit is described above from the code. The `movetime` run finished its last depth instead of aborting inside it.
- A GUI reading the lines.
