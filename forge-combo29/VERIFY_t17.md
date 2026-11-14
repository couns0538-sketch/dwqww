# VERIFY t17

Branch `grok47/t17-rules-suite` at `7afa73cc4c34ea857b65077b697a51a568851d1c`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `3438c19e` changes only `REPORT_t17.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/board.hpp` (a `friend struct BoardStateProbe;`), `tests_t17/rules_suite.cpp`, `REPORT_t17.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 3 insertions, 0 deletions. URLs in the report are not in code that runs.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test searches and runs perft in-process.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t17-rules-suite/forge-combo29 -B /tmp/wt-t17-rules-suite/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t17-rules-suite/build_rel -j4
cmake -S /tmp/wt-t17-rules-suite/forge-combo29 -B /tmp/wt-t17-rules-suite/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t17-rules-suite/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t17-rules-suite/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 433 nps 1991521
nodes 4865609
```


## Task test

`rules_suite.cpp` linked to this commit's sanitizer objects except `uci.cpp.o`. Exit 0, stderr empty:

```
PASS PERFT start depth 5 engine 4865609 expected 4865609
PASS PERFT kiwipete depth 4 engine 4085603 expected 4085603
PASS PERFT pos3 depth 5 engine 674624 expected 674624
PASS PERFT pos4 depth 4 engine 422333 expected 422333
PASS PERFT pos5 depth 4 engine 2103487 expected 2103487
PASS PERFT pos6 depth 4 engine 3894594 expected 3894594
RESULT PASS fails=0
```

Lock headers, compile failed: `Board::compute_checkers() const` is private. The test does not compile on the lock.

## Report claims

Reproduced: the six perft counts, `RESULT PASS fails=0`, and the pins. The external perft pages cited in the report were not fetched. No Elo or speed claim was checked.
