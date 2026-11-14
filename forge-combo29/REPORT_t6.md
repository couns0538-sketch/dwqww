# Task 6: fixed-node score and move

Branch `grok47/t6-fixed-node-score`, from `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`. Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`.

## What was wrong

`go nodes N` can finish one or more iterations and then stop in the middle of the next one. If a root move in that unfinished iteration raises alpha, the old code keeps that move and its PV, but it does not update the score. The score stays the one from the last finished iteration.

On the start position, the same session against `/tmp/forge-t6-lock/forge` (built from `16833ecc` before this change) printed:

```
info depth 3 seldepth 3 score cp 49 nodes 155 nps 0 hashfull 0 time 0 pv c2c4 h7h6 d2d4
bestmove c2c4
```

Depth 2 had already finished as `d2d4` with score 49. Depth 3's finished result is `e2e4` with score 18, at 215 nodes. The 155-node search published `c2c4` together with the depth-2 score 49.

## The fix

`Worker::should_stop` records when the node budget is the reason it returns. If that flag is set, the abort path leaves the best move, PV, and score on the last iteration that finished, and it does not print a new `info` line. A clock stop or an external `stop` still keeps a partial root move, which is the previous behaviour. Engine diff: 14 insertions and 4 deletions in `src/search.cpp` and `include/forge/search.hpp`.

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
