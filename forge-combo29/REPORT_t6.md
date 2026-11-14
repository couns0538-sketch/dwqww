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

## Not verified

- A movetime or `wtime` game in which a partial root move used to replace the finished move. That path is still the old `if` body; only a node-budget stop skips it. Wall-clock stops are not repeatable on this machine, so they were not compared byte for byte.
- `go nodes` with more than one thread.
- A node budget that expires before depth 1 finishes. The reported score stays 0 and the move stays the first legal root move.
- The lock's Windows ThinLTO/PGO build, and `-DFORGE_PORTABLE=ON`.
- No Elo or speed claim. `time` and `nps` in the bench lines above are this run only.
