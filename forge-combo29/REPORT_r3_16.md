# TmNodeShare

## Where the idea comes from

Clock play should spend longer when the root is split and stop sooner when one move already owns the search. That is the usual chess-clock heuristic. This task asks for it as a soft-target change: lengthen the soft target when the best root move holds a minority of the root nodes, shorten it when that move holds most of them, and keep the result within the hard limit.

This engine already does a different form of the same idea on every clock search. `TmEffortBase` scales the existing soft factor from the best move's share of `local_nodes_`. `TmNodeShare` leaves that factor in place and does not use its numbers. The new scale is `decide_node_share_timing` in `include/forge/tm_node_share.hpp`. The share is an integer thousandth of the sum of the per-root-move node counters. Under half lengthens the soft target, over half shortens it, and exactly half leaves it alone. Zero percent of the nodes is 3/2 of the soft target. One hundred percent is 1/2. A positive result is at least 1 ms, and when the hard limit is positive the result is at most that hard limit. Those fractions were chosen here so the unit tests can check exact milliseconds. No code, constants, or tables were taken from another engine.

## Behaviour

The `uci` answer lists one new check, off by default:

```
option name TmNodeShare type check default false
```

With the option off, the iteration-stop comparison is the original expression. Fixed-depth and fixed-node searches never enter the clock block, so their node counts stay on the old path.

With the option on, `Worker::search` calls `decide_node_share_timing` only inside the existing `time_managed_` block, after the older factor is computed. That block is sudden-death and movestogo clocks. Movetime, depth, nodes, infinite, and ponder before ponderhit do not use it. The adjusted soft target is then multiplied by the existing stability, effort, falling-eval, and minimum factor. The hard stop inside the search is unchanged. If the allocated soft target is already above the hard limit, a positive hard limit pulls the returned target down to the hard limit, including on a 50 percent share.

## Pins

Threads 1, Hash 16, OwnBook false, every other option at its default. Release build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. The compiler was g++-13 because `/usr/bin/c++` is Clang 18 and its GCC 14 library directory has no `libstdc++` link.

Before any source change:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

After the change, with `TmNodeShare` left false:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

bench 13 with `TmNodeShare` set true is 862329. It did not change. Bench is a fixed-depth search, and this option runs only on clock play.

## Tests

`tests_r3_16/tm_node_share_test.cpp` calls the decision function with made-up soft, hard, elapsed, and node counts. 1020 checks passed, including every best-move share from 0/1000 through 1000/1000 on a 4000 ms soft target.

`tests_r3_16/legal_depth10_test.cpp` sets the same flag and searches 200 positions to depth 10 at Threads 1 and Hash 16. The positions are legal-move walks from the start position. The binary was compiled with `-fsanitize=address,undefined`. All 200 returned moves were legal. AddressSanitizer and UndefinedBehaviorSanitizer printed no errors. The process exited 0.

Two UCI clock commands with the option on also returned legal moves: `a2a3` for `go wtime 300 btime 300 winc 10 binc 10` from the start, and `e2e3` for `go wtime 200 btime 200 movestogo 5` from `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1`. That only shows the clock path returns a move.

`src` and `include` changed by 83 lines (81 added, 2 removed), including the new header. `CMakeLists.txt` was not edited.

No games were played, so this report has no strength result.

setoption name TmNodeShare value true
