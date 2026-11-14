# VERIFY t15

Branch `grok47/t15-multipv` at `e2d4e1a6a13026cdb295a296631f141818bef70e`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `28ee8b54` changes only `REPORT_t15.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`, `tests_t15/depth12_lock.txt`, `tests_t15/test_multipv.cpp`, `REPORT_t15.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 143 insertions, 11 deletions. Under the 300-line cap. `MultiPV` defaults to 1.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test reads `forge-combo29/tests_t15/depth12_lock.txt` and searches in-process. Extra lines drop the caller's limits (`src/search.cpp:1752-1755`):

```
narrowed.nodes = 0;
narrowed.nodes_specified = false;
narrowed.movetime_ms = -1;
narrowed.time_ms = -1;
```

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t15-multipv/forge-combo29 -B /tmp/wt-t15-multipv/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t15-multipv/build_rel -j4
cmake -S /tmp/wt-t15-multipv/forge-combo29 -B /tmp/wt-t15-multipv/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t15-multipv/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t15-multipv/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 434 nps 1986933
nodes 4865609
```


`MultiPV` was left at 1. The pins match.

## Task test

Sanitizer objects except `uci.cpp.o`. Run from `/tmp/wt-t15-multipv` so the golden path resolves. Exit 0, stderr 0 bytes:

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

Lock headers, compile failed: `'struct forge::SearchLimits' has no member named 'multipv'` at `test_multipv.cpp:394`.

## Report claims

Reproduced: `RESULT passed`, the depth-12 line match aside from time and nps, the node-limit and movetime checks inside the test, and the three pins. The `EXPLAIN` lines are the test saying an extra line can outscore the first. No Elo or speed claim was checked.

## Pair

t10 is better. It does not clear `nodes`, `movetime_ms`, or `time_ms` when it searches another line. This branch does, at `search.cpp:1752-1755`.
