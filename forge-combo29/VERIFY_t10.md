# VERIFY t10

Branch `grok47/t10-multipv` at `f6de2baa0d6efbdf69c87ba2f155067afab4219d`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `935b359e` changes only `REPORT_t10.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`, `tests_t10/multipv_test.cpp`, `REPORT_t10.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 134 insertions, 12 deletions. Under the 300-line cap. `uci` advertises `option name MultiPV type spin default 1 min 1 max 8`.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test searches in-process. Extra lines are searched with the same limits object; this diff does not zero `nodes`, `movetime_ms`, or `time_ms` for them.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t10-multipv/forge-combo29 -B /tmp/wt-t10-multipv/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t10-multipv/build_rel -j4
cmake -S /tmp/wt-t10-multipv/forge-combo29 -B /tmp/wt-t10-multipv/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t10-multipv/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t10-multipv/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 170 nps 1840388
info string bench depth 13 nodes 862329 time 455 nps 1895228
nodes 4865609
```


`MultiPV` was left at 1. The pins match.

## Task test

Sanitizer objects except `uci.cpp.o`. Branch exit 0, stderr empty. The last lines were:

```
nodes560 best e2e4 score 18 nodes 560 lines 3
ok a node limit keeps the last complete MultiPV set
ok MultiPV stays inside searchmoves
ok a check search ranks the legal evasions
failures=0
```

Lock headers, compile failed: `'const struct forge::SearchInfo' has no member named 'lines'`.

Sanitizer UCI, option left at default, commands sent and `quit` held until `bestmove`:

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 26000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 27000 hashfull 0 time 2 pv d2d4 d7d6
bestmove d2d4
```

No `multipv` token. Stderr empty.

## Report claims

Reproduced: default MultiPV keeps a one-line depth-2 search (`d2d4`, 26 then 54 nodes), the in-process test's `failures=0`, a node limit that keeps the last complete set, and the three pins. Not re-run: every MultiPV example position in the report beyond the test. No Elo or speed claim was checked.

## Pair

t10 is better than t15. t15 copies the limits and then clears them for every extra line (`search.cpp:1752-1755`):

```
narrowed.nodes = 0;
narrowed.nodes_specified = false;
narrowed.movetime_ms = -1;
narrowed.time_ms = -1;
```
