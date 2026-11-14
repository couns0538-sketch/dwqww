# Task 6: fixed-node score and move

Branch `grok47/t6-fixed-node-score`, from `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`. Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. Engine change: 14 insertions and 4 deletions in `src/search.cpp` and `include/forge/search.hpp`.

## What was wrong

`go nodes N` searches by iterative deepening. Depth 1 runs to completion, then depth 2, and so on. A finished iteration is the only place that writes the published result. In `Worker::search` that commit is after the aspiration loop, around the current lines 1696–1704:

- `result.score` becomes that iteration's score
- `result.depth` becomes that iteration's depth
- `result.pv` and `result.best_move` become that iteration's PV
- `emit` prints one `info` line from those same values

The node budget is not checked only between iterations. `Worker::search` and `Worker::qsearch` call `should_stop` on every node when a node limit is set (`node_limit_specified_` is true for the main thread when `go nodes` was given). When the count reaches N, `aborted_` is set and the current node returns 0.

That return happens before the move that was in progress can update the root PV. The root PV is updated only after a root move's search returns and the score raises alpha (`search.cpp` around lines 1438–1450): `ss->pv[0] = move`, then the child PV is copied. So an abort leaves the root PV holding the last root move of this iteration that did finish and did raise alpha. Moves still being searched are not in that PV. The iteration's score is not written to `result`, because the commit at lines 1696–1704 is skipped once `aborted_` is set.

The lock then did a second, separate update. The abort block used to say that a partially searched iteration which had already raised alpha had found a move at least as good as the previous best. If the partial PV's first move differed from the previous PV's first move, the lock copied that partial PV into `result.best_move`, `result.pv`, and `result.ponder_move`. It did not copy a score. `result.score` and `result.depth` stayed at the last finished iteration. It then called `emit(depth, result.score, result.pv)`. The `depth` argument is the loop variable, so the printed `info` line carries the unfinished iteration's depth, the previous iteration's score, and the partial PV. UCI prints `bestmove` from `result.best_move`, so the move on that line matches the partial PV and does not match the score.

A training label taken from `go nodes` therefore pairs a move that belongs to an unfinished iteration with a score that belongs to the previous finished iteration. The score is not the value of the printed move, and the move is not the move the finished iteration chose. It is also not, in general, the move the unfinished depth would have chosen if it had been allowed to finish: later root moves can still raise alpha after the cut.

The copy was skipped when the partial PV's first move was already the finished iteration's move (`result.pv[0] == ss->pv[0]`). Those budgets look consistent on the lock. The bug shows up only after a different root move has raised alpha in the iteration that the node limit cuts off.

This path is specific to a stop that happens in the middle of an iteration. If the budget is reached after an iteration has already committed, the following `if (should_stop()) break` leaves that committed result alone. A completed `go depth` search never enters the abort block.

## What I found

On the start position, with `Threads 1`, `Hash 16`, `OwnBook false`, the lock binary printed this for `go nodes 155`:

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 49 nodes 155 nps 0 hashfull 0 time 0 pv c2c4 h7h6 d2d4
bestmove c2c4
```

Read as a label, that says depth 3, score +49, move `c2c4`. The three numbers do not come from one search result:

| source | depth | score | move | nodes |
| --- | --- | --- | --- | --- |
| finished depth 1 | 1 | +1 | `d2d4` | 26 |
| finished depth 2 | 2 | +49 | `d2d4` | 54 |
| `go nodes 155` on the lock | printed as 3 | +49, from depth 2 | `c2c4`, from the partial depth 3 | 155 at the cut |
| finished depth 3 | 3 | +18 | `e2e4` | 215 |

`c2c4` had raised alpha during depth 3 before the 155-node cut. Depth 3, run to the end, plays `e2e4` with score +18. The lock published neither the finished depth-2 pair (`d2d4`, +49) nor the finished depth-3 pair (`e2e4`, +18). The C++ API on the same budget returns `SearchInfo.depth == 2` and `SearchInfo.score == 49` with `best_move == c2c4`. The printed `info` depth is 3 because `emit` is passed the unfinished loop depth; the stored `result.depth` stays 2.

The same split appears on later iterations and on other positions. These are lock results, one thread, hash 16 MB, a fresh searcher each time. "Finished" is a separate search limited to the depth the node-limited search reported.

- Start position, 155, 175, and 195 nodes: reported depth 2, score 49, move `c2c4`. Finished depth 2 is `d2d4`, score 49. At 997 nodes: depth 4, score 30, move `c2c4`, against finished `e2e4`. At 1524, 1611, and 1698 nodes: depth 5, score 6, move `d2d4`, against finished `c2c4`.
- King and rook ending `8/8/8/8/4k3/8/3R4/4K3 w - - 0 1`, 401 nodes: depth 3, score 419, move `e1f2`. Finished depth 3 is `e1e2`, score 419.
- Italian `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3`, 88 and 97 nodes: depth 1, score 21, move `f1c4`, against finished `d2d4`. At 106 and 115 nodes the partial move has become `b1c3`, still with score 21. Later cuts mix `d2d4` with the depth-2 score 25 (finished move `b1c3`), `c2c3` with the depth-3 score 21 (finished move `d2d4`), `d2d4` with the depth-4 score 22 (finished move `c2c3`), and `d2d4` with the depth-5 score 20 (finished move `h2h3`).
- `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1`, 69 nodes: depth 1, score 83, move `b4c4`, against finished `a5a6`. At 608 and 638 nodes: depth 4, score 71, move `b4f4`, against finished `b4c4`.

Budgets inside the same span that still show the previous move pass on the lock. From the start position, 55 through 135 nodes still report `d2d4` with score 49, which is the finished depth-2 pair. The partial depth-3 search has not yet raised alpha with a different move. On the king and rook ending, every sampled budget between depth 2 (58 nodes, `e1f2`) and depth 3 (160 nodes, `e1e2`) also passed on the lock, because the partial move was still `e1f2`. A test that stops at the first move change in that ending does not see the bug. The 401-node cut, inside depth 4, does.

A budget of 1 node, before any root move completes, reports depth 0, score 0, and the first legal move on both the lock and this branch (`a2a3` from the start position, `d2d1` in the ending, `e2e3` in the pawn ending). There is no finished iteration and no partial PV to copy.

`go depth 3` from the start position finishes. Both binaries print depth 1 `d2d4` score 1, depth 2 `d2d4` score 49, depth 3 `e2e4` score 18 at 215 nodes, and `bestmove e2e4`.

One measurement trap: `go` returns to the UCI loop as soon as the worker thread is started. A pipe that sends `quit` on the next line sets the stop flag immediately. The search then aborts on the first node, prints no `info` line, and falls back to the first legal move, `bestmove a2a3`. That happens on the lock and on this branch. It is an external stop, not the node-limit bug. The `go nodes 155` lines above were read until `bestmove`, and `quit` was sent after that.

## What changed

`Worker` gained `stopped_by_nodes_`, cleared at the start of every `Worker::search`. `should_stop` sets it only in the node-budget branch, after the external-stop check and after helpers have already returned:

1. `shared_.stop` is an external `stop` or the searcher winding helpers down. It returns true and leaves the flag false.
2. A helper returns false. Helpers do not apply the node budget.
3. The main thread, over the node budget, sets `stopped_by_nodes_` and returns true.
4. A hard time limit returns true and leaves the flag false.

The abort block still copies the partial root PV, and still emits it with the previous score, when the flag is false. That is the clock stop and the external `stop`. A node-budget stop now breaks with the last committed iteration: same score, same depth, same PV, same best move, and no extra `info` line.

After the change, the same `go nodes 155` session prints:

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
```

The last `info` line and `bestmove` are the finished depth-2 result. The search still stops because of the node budget; it no longer advertises `c2c4` with depth 2's score.

Completed iterations are committed by the same statements as before. Bench and perft do not go through this abort block. With `Threads 1`, `Hash 16`, `OwnBook false`, bench 11 is 312866 nodes, bench 13 is 862329 nodes, and `go perft 5` from the start position is 4865609 nodes.

`tests_t6/fixed_nodes.cpp` builds a fresh 16 MB, 1-thread searcher for every call and uses `TTAccess::Exclusive`, the same table access one-thread UCI uses. For each depth through 6 it samples budgets between that depth's node count and the next depth's node count. A node-limited result whose reported depth is D must match a fresh depth-D search in score and move, and the reported PV must start with that move. The lock fails 27 of 176 budgets. This branch passes all 176. The AddressSanitizer and UndefinedBehaviorSanitizer binary printed the same pass log and no sanitizer diagnostic. The command logs below are those runs. The first log is the original test, which stopped at the first depth where the move changed. The second log is the test as it is now.

## Files

- `forge-combo29/src/search.cpp`
- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/tests_t6/fixed_nodes.cpp`
- `forge-combo29/REPORT_t6.md`

## Commands and output

The engine build, outside the repository so the tree stays source-only:

```
cmake -S forge-combo29 -B /tmp/forge-t6-fixed -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4
cmake --build /tmp/forge-t6-fixed -j
```

Pins, with `Threads 1`, `Hash 16`, `OwnBook false`. Bench uses its own 16 MB, 1-thread searcher. Node counts match the lock binary built from `16833ecc` the same way.

```
printf '%s\n' 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' 'isready' 'bench 11' 'bench 13' 'position startpos' 'go perft 5' 'quit' | /tmp/forge-t6-fixed/forge
```

```
readyok
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 424 nps 2033794
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

`go depth 3` on the lock binary and on this binary printed the same three info lines and `bestmove e2e4` (215 nodes). `time`, `nps`, and `hashfull` were 0 in that run.

`go` runs on a worker thread, so the next line in a pipe (including `quit`) stops the search before it prints. The node-limit lines below were read until `bestmove`:

```
bash -c 'coproc eng { /tmp/forge-t6-fixed/forge; }
echo "setoption name Threads value 1" >&"${eng[1]}"
echo "setoption name Hash value 16" >&"${eng[1]}"
echo "setoption name OwnBook value false" >&"${eng[1]}"
echo "isready" >&"${eng[1]}"
echo "position startpos" >&"${eng[1]}"
echo "go nodes 155" >&"${eng[1]}"
while IFS= read -r line <&"${eng[0]}"; do printf "%s\n" "$line"; case "$line" in bestmove*) break;; esac; done
echo quit >&"${eng[1]}"'
```

This binary:

```
readyok
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
```

The C++ test was compiled against the lock sources first (exit 1). `c2c4` was reported with the finished depth-2 score 49.

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -I forge-combo29/include forge-combo29/tests_t6/fixed_nodes.cpp forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp -o /tmp/fixed_nodes_lock -pthread
/tmp/fixed_nodes_lock
```

```
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
span depth 2 nodes 54 -> depth 3 nodes 215
nodes 55 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 75 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 95 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 115 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 135 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 155 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
nodes 175 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
nodes 195 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
span depth 2 nodes 58 -> depth 3 nodes 160
nodes 59 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 71 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 83 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 95 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 107 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 119 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 131 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 143 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 155 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
FAIL failures 3
```

The same command with the patched `search.cpp` (output `/tmp/fixed_nodes`, exit 0):

```
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
span depth 2 nodes 54 -> depth 3 nodes 215
nodes 55 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 75 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 95 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 115 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 135 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 155 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 175 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 195 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
span depth 2 nodes 58 -> depth 3 nodes 160
nodes 59 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 71 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 83 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 95 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 107 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 119 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 131 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 143 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 155 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
PASS fixed-node score and move agree
```

AddressSanitizer and UndefinedBehaviorSanitizer, same sources, `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined`. Exit 0. The sanitizers printed nothing. The test output was the same pass log as above, including the same node counts.

## Broader budgets

The first test stopped at the first depth where the best move changed. The same mismatch also happens later, and on other positions. `tests_t6/fixed_nodes.cpp` now walks every depth through 6 on four positions and samples eight budgets inside each iteration. Engine sources were not changed for this pass, so the bench and perft numbers above still belong to this `search.cpp`.

Lock sources (`16833ecc` `search.cpp` and `search.hpp`, same `g++ -O3` line as the first test, output `/tmp/fixed_nodes_lock`, exit 1):

```
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
nodes 1 depth 0 score 0 move a2a3
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
nodes 155 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
nodes 175 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
nodes 195 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
depth 4 score 30 move e2e4 nodes 404
depth 5 score 6 move c2c4 nodes 1001
nodes 997 depth 4 score 30 move c2c4 finished-score 30 finished-move e2e4 FAIL
depth 6 score 34 move d2d4 nodes 1703
nodes 1524 depth 5 score 6 move d2d4 finished-score 6 finished-move c2c4 FAIL
nodes 1611 depth 5 score 6 move d2d4 finished-score 6 finished-move c2c4 FAIL
nodes 1698 depth 5 score 6 move d2d4 finished-score 6 finished-move c2c4 FAIL
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
nodes 1 depth 0 score 0 move d2d1
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
depth 4 score 410 move e1f2 nodes 406
nodes 401 depth 3 score 419 move e1f2 finished-score 419 finished-move e1e2 FAIL
depth 5 score 417 move e1e2 nodes 919
depth 6 score 420 move e1e2 nodes 1572
fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3
depth 1 score 21 move d2d4 nodes 42
nodes 1 depth 0 score 0 move a2a3
depth 2 score 25 move b1c3 nodes 117
nodes 88 depth 1 score 21 move f1c4 finished-score 21 finished-move d2d4 FAIL
nodes 97 depth 1 score 21 move f1c4 finished-score 21 finished-move d2d4 FAIL
nodes 106 depth 1 score 21 move b1c3 finished-score 21 finished-move d2d4 FAIL
nodes 115 depth 1 score 21 move b1c3 finished-score 21 finished-move d2d4 FAIL
depth 3 score 21 move d2d4 nodes 213
nodes 178 depth 2 score 25 move d2d4 finished-score 25 finished-move b1c3 FAIL
nodes 190 depth 2 score 25 move d2d4 finished-score 25 finished-move b1c3 FAIL
nodes 202 depth 2 score 25 move d2d4 finished-score 25 finished-move b1c3 FAIL
depth 4 score 22 move c2c3 nodes 384
nodes 340 depth 3 score 21 move c2c3 finished-score 21 finished-move d2d4 FAIL
nodes 361 depth 3 score 21 move c2c3 finished-score 21 finished-move d2d4 FAIL
nodes 382 depth 3 score 21 move c2c3 finished-score 21 finished-move d2d4 FAIL
depth 5 score 20 move h2h3 nodes 889
nodes 637 depth 4 score 22 move d2d4 finished-score 22 finished-move c2c3 FAIL
nodes 700 depth 4 score 22 move d2d4 finished-score 22 finished-move c2c3 FAIL
nodes 763 depth 4 score 22 move d2d4 finished-score 22 finished-move c2c3 FAIL
nodes 826 depth 4 score 22 move d2d4 finished-score 22 finished-move c2c3 FAIL
depth 6 score 31 move d2d4 nodes 1628
nodes 1534 depth 5 score 20 move d2d4 finished-score 20 finished-move h2h3 FAIL
nodes 1626 depth 5 score 20 move d2d4 finished-score 20 finished-move h2h3 FAIL
fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1
depth 1 score 83 move a5a6 nodes 20
nodes 1 depth 0 score 0 move e2e3
depth 2 score 237 move b4c4 nodes 70
nodes 69 depth 1 score 83 move b4c4 finished-score 83 finished-move a5a6 FAIL
depth 3 score 167 move b4c4 nodes 128
depth 4 score 71 move b4c4 nodes 397
depth 5 score 101 move b4f4 nodes 642
nodes 608 depth 4 score 71 move b4f4 finished-score 71 finished-move b4c4 FAIL
nodes 638 depth 4 score 71 move b4f4 finished-score 71 finished-move b4c4 FAIL
depth 6 score 92 move b4f4 nodes 870
FAIL failures 27 checks 176
```

Patched sources, same `-O3` command, `/tmp/fixed_nodes`, exit 0. Passing budgets are not printed. 176 budgets were checked.

```
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
nodes 1 depth 0 score 0 move a2a3
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
depth 4 score 30 move e2e4 nodes 404
depth 5 score 6 move c2c4 nodes 1001
depth 6 score 34 move d2d4 nodes 1703
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
nodes 1 depth 0 score 0 move d2d1
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
depth 4 score 410 move e1f2 nodes 406
depth 5 score 417 move e1e2 nodes 919
depth 6 score 420 move e1e2 nodes 1572
fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3
depth 1 score 21 move d2d4 nodes 42
nodes 1 depth 0 score 0 move a2a3
depth 2 score 25 move b1c3 nodes 117
depth 3 score 21 move d2d4 nodes 213
depth 4 score 22 move c2c3 nodes 384
depth 5 score 20 move h2h3 nodes 889
depth 6 score 31 move d2d4 nodes 1628
fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1
depth 1 score 83 move a5a6 nodes 20
nodes 1 depth 0 score 0 move e2e3
depth 2 score 237 move b4c4 nodes 70
depth 3 score 167 move b4c4 nodes 128
depth 4 score 71 move b4c4 nodes 397
depth 5 score 101 move b4f4 nodes 642
depth 6 score 92 move b4f4 nodes 870
PASS fixed-node score and move agree checks 176
```

AddressSanitizer and UndefinedBehaviorSanitizer, same sources, `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined` instead of `-O3`, output `/tmp/fixed_nodes_san`, exit 0. `diff -u /tmp/fixed_nodes.txt /tmp/fixed_nodes_san.txt` was empty. The sanitizers printed nothing.

A separate sweep with a finer step (`span / 12` instead of `span / 8`) through depth 8 on the king and rook ending, and depth 6 on the other three positions, also passed on the patched engine and failed 40 budgets on the lock. That program was not kept; the checked-in test is the run above.

## Not verified

- A movetime or `wtime` game in which a partial root move used to replace the finished move. That path is still the old `if` body; only a node-budget stop skips it. Wall-clock stops are not repeatable on this machine, so they were not compared byte for byte.
- `go nodes` with more than one thread.
- A node budget of 1, measured above on all four positions. Both engines report depth 0, score 0, and the first legal root move. A budget that finishes one root move and then stops still inside depth 1 was not isolated beyond those samples.
- The lock's Windows ThinLTO/PGO build, and `-DFORGE_PORTABLE=ON`.
- No Elo or speed claim. `time` and `nps` in the bench lines above are this run only.
