# TmFinishIteration

## Idea

On a game clock, iterative deepening should not start a depth that cannot finish, and it should play the move from the depth that already did. After a depth finishes, the next duration is guessed from the last two only: scale the later duration by the growth from the one before it, `last * last / prev`, in exact arithmetic. If that guess is strictly longer than the time still left for this move, the next depth is not started.

That is the usual clock rule for iterative deepening. The estimate, and the choice to compare it with the soft deadline this search already uses (soft limit times the stability factor), were written for this engine. No formula, constant, or table was taken from another engine.

The hard limit is unchanged. Fixed-depth, fixed-node, and movetime searches do not consult the guess. Neither does a ponder search before ponderhit.

## Option

One new UCI check, default false, printed in the `uci` answer:

`option name TmFinishIteration type check default false`

Left off, the soft-limit test in the search loop is the one that was already there.

## Decision

`forge::iteration_will_not_finish` in `forge-combo29/include/forge/tm_finish.hpp`.

It returns true (do not start) when the remaining budget is already used up, or when both durations are positive and `last * last > remaining * prev`. A non-positive duration is not a measurement, so the function returns false and the search does what it does today. A zero-millisecond reading clears the pair, because a 0 from the clock is not a duration to scale.

`Worker::search` calls it only when the option is on and a game clock (`wtime` / `btime`) is running, and only after the existing soft-deadline test has decided to go on. A skip prints

`info string TmFinishIteration hold depth D prev P last L remaining R`

and breaks. The best move stays the move from depth D.

## Defaults, option off

Threads 1, Hash 16, OwnBook false, every other option at default. Printed from the untouched binary before the edit, and again from the patched binary at the end:

- bench 11: 312866 nodes
- bench 13: 862329 nodes
- `go perft 5` from the start position: 4865609 nodes

Release build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` and `cmake --build build -j`, with `CXX=g++`. `/usr/bin/c++` on this machine is clang and did not link libstdc++.

## Bench 13 with the option on

`setoption name TmFinishIteration value true`, then `bench 13`, still printed 862329 nodes. Fixed-depth bench never enters the clock path, so that count does not show the option is live. The made-up timings and the clock search below are the proof.

## Made-up timings

`forge-combo29/tests_r3_15/tm_finish_test.cpp` calls the function with invented triples. Among them: (100, 400, 1600) stays, (100, 400, 1599) skips, a missing sample stays, a spent budget skips, and products past 64 bits go both ways. All 20 cases passed.

The same program searched the start position to depth 6 with the option off and on. Both visits were 1703 nodes.

## Clock search

UCI, Threads 1, Hash 16, OwnBook false, option on. Position `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`, `go wtime 4000`.

Depth 13 finished at about 133 ms with move e2a6. The engine then printed:

`info string TmFinishIteration hold depth 13 prev 16 last 86 remaining 34`

`86 * 86 = 7396` and `34 * 16 = 544`, so the function says depth 14 cannot finish. No `info depth 14` was printed. bestmove was e2a6.

The same `go` with the option off did print `info depth 14` (time 172) and then stopped, still with e2a6. That depth was started only while the option was off. The ratio had guessed about 462 ms for it; the measured depth 14 took about 38 ms. The option follows the ratio. This is not a strength result.

The unit test also runs a clock search through `Searcher` on the start position across several `wtime` values. It checks that a hold line's three numbers make the function return true, that the played depth is that depth, that no deeper info line was printed, and that the move is legal. The same call with the option off prints no hold line.

## Sanitizer

`forge-combo29/tests_r3_15/tm_finish_test.cpp` and the engine sources were compiled with `g++ -fsanitize=address,undefined` (`-O1 -g`, portable x86-64-v3, the same `FORGE_*` defines as the release build). The binary linked `libasan.so.8` and `libubsan.so.1`.

With `TmFinishIteration` on, Hash 16, and Threads 1, it searched 200 positions to depth 10. The positions were produced by walking legal moves from the start position with seed 15. Every returned move was legal. The made-up timing cases and a clock hold ran in that same process. AddressSanitizer and UndefinedBehaviorSanitizer reported nothing.

## Diff size

74 changed lines in `forge-combo29/src` and `forge-combo29/include`: 71 added and 3 removed, including the new header. `CMakeLists.txt` was not changed.

setoption name TmFinishIteration value true
