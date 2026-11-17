# SoftNodes

`go softnodes N` is a UCI go command for labelling training data. It is off during normal play. Bench, `go depth`, and `go nodes` do not set it.

## Where the idea comes from

A training label is a move and a score from one finished iterative-deepening iteration. This search already keeps that pair when `go nodes` cuts a search off mid-iteration, and then throws the partial iteration away. That is the right pair, and it is also a wall: the search never finishes the iteration that actually crosses the budget.

Soft nodes uses the same finished-iteration rule with the budget as a target. Once N nodes have been searched, the current iteration runs to completion and the search stops. The reported move and score are that iteration's. A single iteration can still be much larger than N, so there is a hard stop at 4N. The 4× ceiling is the bound set for this task. It is the same shape this searcher already uses for a clock (a soft target, then a hard multiple), applied to nodes only when this command is present. No evaluation weight, reduction table, or search constant was taken from another engine.

## What the command does

- `go softnodes N` sets a soft budget of N and a hard budget of 4N (saturated at the top of a 64-bit count).
- After each finished iteration, if the node count is at least N, the search stops.
- Reaching 4N aborts inside the iteration through the existing node stop, which keeps the previous finished move and score.
- The engine then prints `info string softnodes nodes <count>` with the nodes actually searched, and `bestmove` for the last finished iteration.
- `go nodes` still hard-stops at its own N. It does not print that line.

The depth cap stays 64. A very narrow tree can reach that cap before N nodes. The 200-position run below used N = 1000 and did not hit that case.

## Default pins

Threads 1, Hash 16, OwnBook false, every other option left at default. Printed on the unmodified tree at e04556dd, and again after this change:

- bench 11 = 312866
- bench 13 = 862329
- `go perft 5` from the start position = 4865609

The three numbers matched both times. Release build:

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j`

Source diff in `src` and `include`: 27 insertions, 4 deletions.

## Tests

`tests_r3_12/softnodes_test.cpp` speaks UCI to the binary. It builds 200 positions by playing legal moves from the start position. CMakeLists.txt is unchanged, so the harness is compiled on its own:

`g++ -std=c++20 -O2 -DNDEBUG -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -I forge-combo29/include forge-combo29/tests_r3_12/softnodes_test.cpp forge-combo29/src/board.cpp forge-combo29/src/bitboard.cpp -o softnodes_test`

`softnodes_test ./build/forge softnodes` (Threads 1, Hash 16, OwnBook false):

- 200 searches of `go softnodes 1000`. Every node count was between 1000 and 4000 inclusive. Every move was legal. The move and the score matched a fresh `go depth D` at the depth of the last finished iteration.
- `go nodes 400` on the start position did not print a softnodes line. Its last finished info line reported 215 nodes.
- Result: `SOFTNODES_PASS 200 budget 1000`.

Those 200 softnodes searches were also run on a binary built with `-fsanitize=address,undefined`, with leak detection left off. The process exited 0.

Sanitizer build, extra flags `-fsanitize=address,undefined -fno-omit-frame-pointer` on compile and link. `softnodes_test ./build-asan/forge depth10` with `ASAN_OPTIONS=halt_on_error=1:detect_leaks=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`:

- 200 searches of `go depth 10`.
- Every returned move was legal.
- The engine exited 0. No address or undefined-behavior diagnostic was printed.
- Result: `DEPTH10_LEGAL_PASS 200`.

Re-checked on 2026-11-14 at 14:36 UTC, still on this branch, engine sources unchanged since the command landed. The three pins printed again as 312866, 862329, and 4865609. `SOFTNODES_PASS 200 budget 1000` repeated, including three back-to-back runs with the same sample (1627 nodes, depth 7, d2c1). `go nodes` on the start position stayed a hard cut: budgets 100, 400, 1000, and 3000 finished at 54, 215, 404, and 2574 nodes, with no softnodes line, and each move and score matched `go depth` at that depth. The same budgets under `go softnodes` finished at 215, 404, 1001, and 4099 nodes, all inside [N, 4N], at a depth at least as deep as the hard cut, with the same move and score as `go depth` there. `go softnodes 0` and `go nodes 0` both returned a2a3 and did not search. One position's next iteration would have passed 4N; `go softnodes 1929` stopped at exactly 7716 nodes, kept depth 7 and b1e4, and matched `go depth 7`. The sanitized `go depth 10` run was repeated with halt-on-error and leak detection: `DEPTH10_LEGAL_PASS 200`, exit 0, no diagnostic.

No strength claim.

go softnodes 1000
sample nodes 1627 (N = 1000, 4N = 4000)

## Follow-up: label measurement

The machine has AVX-512F and BMI2, so this run used the default Release build from CMakeLists (`-march=x86-64-v4`, portable left off). Nothing in CMakeLists was edited, and no `FORGE_*` macro was overridden. On that binary, with Threads 1, Hash 16, and OwnBook false, the pins were again bench 11 = 312866, bench 13 = 862329, and `go perft 5` from the start position = 4865609.

`tests_r3fu_12/label_measure.cpp` walks 10,000 positions from seed `0x5212f00d5eed`. Each game plays 8 to 12 seeded legal moves from the start position, then both sides play `go depth 4` for up to 70 plies. The positions are `tests_r3fu_12/positions.txt`. Each position was then searched with `go nodes 5000`, `go softnodes 5000`, and one `go depth 16` reference, from a cleared table. Per-position rows are `tests_r3fu_12/shard_0.txt` through `shard_3.txt`. The totals are `tests_r3fu_12/summary.txt`.

`go nodes` does not print the count after a hard cut. The mean below uses 5000 when the cut stops the next iteration, and the finished info count when depth 64 ends under 5000. `go softnodes` uses the printed `info string softnodes nodes` count. 51 positions finished depth 64 under 5000 for both commands. 66 soft searches stopped at exactly 20000. None went over 20000.

Mates are left out of the mean absolute score difference. That leaves 9545 centipawn pairs for each command. Best-move agreement is over all 10,000 positions. These numbers compare the two budgets with the depth-16 search. They are not a strength result.

- `go nodes 5000`: mean absolute score difference 1487197/9545 = 155.8090 cp, best-move agreement 5670/10000, mean nodes 49857722/10000 = 4985.7722.
- `go softnodes 5000`: mean absolute score difference 1293511/9545 = 135.5171 cp, best-move agreement 6211/10000, mean nodes 79019155/10000 = 7901.9155.

`label_measure <engine> check 4` recomputes the summary from the shards and exits non-zero if a row breaks the node contract or the stored summary differs. A summary with one changed total exited 1; the restored file exited 0.
