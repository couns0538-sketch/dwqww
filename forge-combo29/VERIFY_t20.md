# VERIFY t20

Branch `grok47/t20-repeatable-search` at `a788bd149eada38a3147033a4d5c0838436771ef`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `9f48a760` changes only `REPORT_t20.md`. There is still no engine diff. The test was built and run again, on this commit and on the lock.

## Rule check

Files: `tests_t20/repeat_mate_test.cpp` and `REPORT_t20.md` only. Both mode 100644. No engine diff (`git diff` of `src` and `include` against the lock is empty). No executable, archive, script, workflow, or Python.

## Safety

The test links the engine and searches in-process. It does not write files, start a process, use the network, or read the environment. There is no engine diff to quote.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t20-repeatable-search/forge-combo29 -B /tmp/wt-t20-repeatable-search/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t20-repeatable-search/build_rel -j4
cmake -S /tmp/wt-t20-repeatable-search/forge-combo29 -B /tmp/wt-t20-repeatable-search/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t20-repeatable-search/build_san -j4
```

Both ended `Built target forge`.


The source matches the lock, so the pins matching is expected.

## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t20-repeatable-search/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 215 nps 1455190
info string bench depth 13 nodes 862329 time 433 nps 1991521
nodes 4865609
```


## Task test

`repeat_mate_test.cpp` linked to this commit's sanitizer objects and, separately, to the lock's sanitizer objects. Both exited 0 with stderr empty, and both ended:

```
PASS in-game state carries: nodes 13102 then 1774, after ucinewgame 13102
PASS hash resize: generation 2 -> 0, probe miss, hashfull 0, history kept (76 entries); Clear Hash generation 0 probe miss, history kept (95); depth 10 after resize matches ucinewgame, nodes 13102
PASS go mate
PASS stalemate KPk bestmove 0000 score cp 0 depth 64
PASS stalemate KQk bestmove 0000 score cp 0 depth 64
PASS checkmate KQk bestmove 0000 score mate 0 depth 64
t20 result: PASS
```

The test does not fail on the lock. The report says no engine change was required because `ucinewgame` already calls `Searcher::clear()`. That is what this run shows.

## Report claims

Reproduced: the test passes with no source change; a second depth-10 start-position search in the same game drops from 13102 nodes to 1774 and returns to 13102 after the clear; `go mate` and the terminal positions in the test pass. The report's description of stale history is the behavior the test prints (`nodes 13102 then 1774`), not a separate engine patch. No Elo or speed claim was checked.
