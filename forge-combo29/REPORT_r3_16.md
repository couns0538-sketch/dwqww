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

When the option is on and a search is printing info, a finished clock iteration whose adjusted target differs from the base soft target prints one line: `info string TmNodeShare lengthen` or `info string TmNodeShare shorten`, with the base soft, the adjusted soft, the best-move nodes, the root-node total, and the depth. The option off prints none of those lines.

## Pins

Threads 1, Hash 16, OwnBook false, every other option at its default. Release build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. The compiler was g++-13 because `/usr/bin/c++` is Clang 18 and its GCC 14 library directory has no `libstdc++` link.

Before any source change:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

Re-checked after the clock info line, Threads 1, Hash 16, OwnBook false.

`TmNodeShare` false:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

`TmNodeShare` true:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

Bench and perft do not change with the option on. Bench is fixed depth, perft does not search, and this option runs only on clock play.

## Tests

`tests_r3_16/tm_node_share_test.cpp` calls the decision function with made-up soft, hard, elapsed, and node counts. Re-run after the info line: 1020 checks passed, including every best-move share from 0/1000 through 1000/1000 on a 4000 ms soft target.

`tests_r3_16/legal_depth10_test.cpp` sets the same flag and searches 200 positions to depth 10 at Threads 1 and Hash 16. The positions are legal-move walks from the start position. Rebuilt with `-fsanitize=address,undefined` after the info line. All 200 returned moves were legal. AddressSanitizer and UndefinedBehaviorSanitizer printed no errors. The process exited 0.

## Live clock search

Start position, Threads 1, Hash 16, OwnBook false, Move Overhead 10, `TmNodeShare` true, `go wtime 2000 btime 2000`. The base soft target for that clock is 90 ms. The same search both lengthened and shortened it:

```
info string TmNodeShare lengthen soft 90 adjusted 127 best 2 root 25 depth 1
info string TmNodeShare shorten soft 90 adjusted 65 best 7497 root 9642 depth 9
bestmove e2e4
```

Depth 1 held 2 of 25 root nodes, a minority, so 90 ms became 127 ms. Depth 9 held 7497 of 9642, a majority, so 90 ms became 65 ms. `e2e4` is legal. Those two lines repeated on a second run of the same command. In that second pair, the option-on search and the option-off search both finished at depth 15 with 212340 nodes and `bestmove e2e4`. The option-off run printed no `TmNodeShare` line. One earlier option-on sample stopped at depth 14; that did not repeat, so this report does not treat the finished depth as changed. The soft target did move, on the lines above.

The same three pins, the 1020 made-up timing checks, and the 200 depth-10 sanitizer searches were run again at 14:47Z. The node counts and the sanitizer result matched the lists above.

`src` and `include` differ from `e04556dd` by 91 lines (89 added, 2 removed), including the new header. `CMakeLists.txt` was not edited.

No games were played for the first version of this note. The follow-up below is the clock screen.

## Follow-up: count the node share once

`TmEffortBase` already multiplies the clock factor by `clamp(base/100 - effort, 0.6, 1.4)`. With `TmNodeShare` on, that same share was applied again by `decide_node_share_timing`. `effort_share_factor` now returns 1 while the option is on, and the older clamp while it is off. The soft-target scale remains the only share adjustment on the on path.

`tests_r3fu_16/effort_share_once_test.cpp` checks that. A failed check exits non-zero. The run reported `effort share once checks 36` and exited 0. The older made-up timing test still reports 1020 checks and exits 0.

Owner build, because this CPU has AVX-512F and BMI2: `cmake -S forge-combo29 -B build-owner -DCMAKE_BUILD_TYPE=Release` with no `FORGE_*` override (`-march=x86-64-v4`, PEXT and ZMM on). Compiler is g++-13. Threads 1, Hash 16, OwnBook false:

- option off: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609
- option on: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609

Clock screen results are appended when the four chunks finish.

setoption name TmNodeShare value true
