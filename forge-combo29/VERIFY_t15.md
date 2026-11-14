# VERIFY t15

Branch `grok47/t15-multipv` at `28ee8b54e2dc44423aafe9f28eac62f4e684fe98`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. `grok47/t10-multipv` is the better MultiPV change.

## Rule check

`git diff --name-status 16833ecc...28ee8b54`:

```
A	forge-combo29/REPORT_t15.md
M	forge-combo29/include/forge/search.hpp
M	forge-combo29/src/search.cpp
M	forge-combo29/src/uci.cpp
A	forge-combo29/tests_t15/depth12_lock.txt
A	forge-combo29/tests_t15/test_multipv.cpp
```

All mode 100644. No executable, archive, script, workflow, or Python file is in the diff. Engine source: `search.hpp` 2 insertions, `search.cpp` 129 insertions and 11 deletions, `uci.cpp` 12 insertions (154 changed lines). Under the 300-line cap.

## Safety

No network use, process start, registry or environment access, or obfuscated code. The test reads a checked-in transcript and does not write a file:

```
std::ifstream golden_file("forge-combo29/tests_t15/depth12_lock.txt");
```

`tests_t15/test_multipv.cpp` line 217. The engine change prints extra root lines and adds the UCI option at `src/uci.cpp:168`:

```
"option name MultiPV type spin default 1 min 1 max 8\n"
```

Each extra line is a new search with the clock and the node limit cleared (`src/search.cpp:1752-1756`):

```
narrowed.nodes = 0;
narrowed.nodes_specified = false;
narrowed.movetime_ms = -1;
narrowed.time_ms = -1;
narrowed.infinite = false;
```

That is search behavior, not a file or process side effect.

## Build

Clang 18.1.3 failed the stated cmake line with `cannot find -lstdc++` (see VERIFY_t12.md). g++ 13.3.0 Release and ASan/UBSan:

```
cmake -S /tmp/wt-t15/forge-combo29 -B /tmp/wt-t15/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t15/build_rel -j
cmake -S /tmp/wt-t15/forge-combo29 -B /tmp/wt-t15/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t15/build_san -j
```

Both ended `Built target forge` and `BUILD_EXIT:0`. `avx512f` is present, so portable march flags were not added.

## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t15/build_rel/forge
```

```
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 424 nps 2033794
nodes 4865609
```

Exit 0. MultiPV was left unset. `uci` prints `option name MultiPV type spin default 1 min 1 max 8` and the lock's option list has no MultiPV line. Tasks 6, 7, 8, and 10 keep these three counts with their own options at the default; there is still no `grok47/t9` branch.

## Task test

Sanitizer objects except `uci.cpp.o`, same sanitizer flags, `ASAN_OPTIONS=detect_leaks=0`. Run from `/tmp/wt-t15` so the golden path resolves.

```
/tmp/tests/t15_branch
```

```
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
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

Exit 0. Stderr was 0 bytes. Twenty `EXPLAIN` lines were printed. The first was:

```
EXPLAIN b startpos depth 5 line 1 is e2e4 and MultiPV 1 is c2c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
```

Lock include tree, compile failed, exit 1:

```
error: ‘struct forge::SearchLimits’ has no member named ‘multipv’
```

The first diagnostic is `test_multipv.cpp:296`. The test does not compile on the lock and passes here.

## Report claims

Reproduced: default pins, `RESULT passed` with `failures 0` and `explained 20`, the start-position explain line above, mate line `a1a8`, and an empty sanitizer stderr. Not run as separate UCI sessions: `ponder`, `go infinite`, `wtime`/`btime`, `searchmoves`, `go mate`, `stop` during an extra line, or a malformed MultiPV value. No Elo or speed claim was checked.

## Same task as t10

`grok47/t10-multipv` (`935b359e`, already PASS) searches the extra root lines inside the same search and checks the stop flag between them. This branch disables helper threads when MultiPV is above 1, which avoids racing those lines, and then clears nodes, movetime, and the clock for every extra line. A timed search can finish the primary iteration and keep searching the other lines with no limit. t10 is the better of the two.
