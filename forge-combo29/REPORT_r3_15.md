# TmFinishIteration

## Idea

On a game clock, iterative deepening should not start a depth that cannot finish, and it should play the move from the depth that already did. After a depth finishes, the next duration is guessed from the last two only.

Steady growth, where the later duration is at most twice the one before it, is extended one step: `last * last / prev`. A larger jump is one deep iteration, not a new rate. Compounding that jump guessed several times the real next iteration on this engine's own depth curves. After a jump the estimate is the geometric mean of the two durations, `sqrt(last * prev)`. The depth is not started when the estimate is strictly longer than the time still left in the soft deadline this search already uses. The hard limit is unchanged.

That rule was written for this engine from its own iteration sizes. No formula, constant, or table was taken from another engine. Fixed-depth, fixed-node, and movetime searches do not consult the guess. Neither does a ponder search before ponderhit.

## Option

One new UCI check, default false, printed in the `uci` answer:

`option name TmFinishIteration type check default false`

Left off, the soft-limit test in the search loop is the one that was already there.

## Decision

`forge::iteration_will_not_finish` in `forge-combo29/include/forge/tm_finish.hpp`.

It returns true (do not start) when the remaining budget is already used up, or when the estimate above is strictly longer than that budget. A non-positive duration is not a measurement, so the function returns false and the search does what it does today. A zero-millisecond reading clears the pair, because a 0 from the clock is not a duration to scale.

`Worker::search` calls it only when the option is on and a game clock (`wtime` / `btime`) is running, and only after the existing soft-deadline test has decided to go on. A skip prints

`info string TmFinishIteration hold depth D prev P last L remaining R`

and breaks. The best move stays the move from depth D.

## The 462 ms guess

The first version always used `last * last / prev`. On

`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`

with `go wtime 4000`, twelve option-off repeats and twelve option-on repeats showed the same nodes. The last three finished iterations were:

- depth 12: 26389 nodes, about 16 ms
- depth 13: 132862 nodes, about 84 ms
- depth 14: 62323 nodes, about 38 ms

Depth 13 is one wider tree (the score moved from -140 to -124 and the selective depth went from 24 to 30), not a new growth rate. The first captured hold was `prev 16 last 86`, and `86 * 86 / 16` is 462 ms. The twelve repeats sat at about 84 ms after 16 ms, and `84 * 84 / 16` is 441 ms. The node form of that compound, `132862 * 132862 / 26389`, is 668927 nodes. The next iteration searched 62323 nodes, close to the geometric mean of the two sizes, `sqrt(26389 * 132862)` = 59212.

The revised rule treats 84 > 2 * 16 as a spike. `sqrt(17 * 84)` is 37.8 ms. A fresh pair after the change:

- option on: `hold depth 13 prev 17 last 84 remaining 36`, bestmove e2a6, no depth 14
- option off: depth 14 finished at 171 ms after depth 13 at 132 ms, so that depth took 39 ms, bestmove e2a6

The guess is now 38 ms against a measured 39 ms. It still does not start depth 14, because 38 ms is longer than the 36 ms left, and the option-off depth took 39 ms. The old 462 ms figure was the compound of the spike. It was not the time the depth needed, and it was not why a 39 ms depth failed to fit in 36 ms.

The same shape showed up on the start position, `go wtime 6000`:

- option on: `hold depth 15 prev 21 last 81 remaining 29`
- `sqrt(21 * 81)` is 41.2 ms
- option off reached depth 16 and used 193 ms against 152 ms with the option on, so the skipped depth took 41 ms

41 ms does not fit in the 29 ms that were left. The old compound would have guessed `81 * 81 / 21` = 312 ms.

## Defaults, option off and on

Threads 1, Hash 16, OwnBook false, every other option at default. Release build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` with `CXX=g++`, because `/usr/bin/c++` on this machine is clang and did not link libstdc++.

Printed before the first edit, again with the option off and on before the spike change, and again after it:

- bench 11: 312866 nodes
- bench 13: 862329 nodes
- `go perft 5` from the start position: 4865609 nodes

`bench 13` with `TmFinishIteration` on is still 862329. Fixed-depth bench never enters the clock path, so that count does not show the option is live. The made-up timings and the clock holds are the proof.

## Made-up timings

`forge-combo29/tests_r3_15/tm_finish_test.cpp` calls the function with invented triples. Doubling still compounds (`prev 1, last 2, remaining 3` skips; `remaining 4` stays). A jump past twice the previous duration uses the mean (`prev 16, last 86, remaining 34` skips; `remaining 38` stays). A missing sample stays. A spent budget skips. Wide products that do not fit in 64 bits are covered. All of those cases passed, including under the sanitizer binary below.

The same program searched the start position to depth 6 with the option off and on. Both visits were 1703 nodes.

The clock portion drives `Searcher` across several `wtime` values until a hold appears. It checks that the three printed numbers make the function return true, that the played depth is that depth, that no deeper info line was printed, and that the move is legal. The same call with the option off prints no hold line. One release run held the start position at depth 15 with `prev 21 last 81 remaining 29` and then, with the option off, searched depth 16.

## Sanitizer

After the spike change, `forge-combo29/tests_r3_15/tm_finish_test.cpp` and the engine sources were compiled with `g++ -fsanitize=address,undefined` (`-O1 -g`, portable x86-64-v3, the same `FORGE_*` defines as the release build). The binary linked `libasan.so.8` and `libubsan.so.1`.

With `TmFinishIteration` on, Hash 16, and Threads 1, it searched 200 positions to depth 10. The positions were produced by walking legal moves from the start position with seed 15. Every returned move was legal. The made-up timing cases and a clock hold ran in that same process. AddressSanitizer and UndefinedBehaviorSanitizer reported nothing. Exit status was 0. An earlier sanitizer run of the compounding rule, before this change, had the same result.

## Diff size

80 changed lines in `forge-combo29/src` and `forge-combo29/include`: 77 added and 3 removed, including the header. `CMakeLists.txt` was not changed.

setoption name TmFinishIteration value true
