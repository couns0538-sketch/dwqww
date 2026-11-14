# VERIFY t6

Branch `grok47/t6-fixed-node-score` at `920a20c939d201dd08523044f7b0e8aba8eeb6ea`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `9b0e6ae1` changes only `REPORT_t6.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `tests_t6/fixed_nodes.cpp`, `REPORT_t6.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 14 insertions, 4 deletions. `uci` advertises no new option. `stopped_by_nodes_` is set only in the node-limit branch of `should_stop` (`search.cpp:897`).

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test searches in-process.

## Build

The stated cmake line, without a compiler override, was run once on the lock tree:

```
cmake -S /tmp/wt-lock/forge-combo29 -B /tmp/wt-lock/build_clang -DCMAKE_BUILD_TYPE=Release
```

`/usr/bin/c++` is Clang 18.1.3. Configure exited 1 before any engine file was compiled:

```
/usr/bin/ld: cannot find -lstdc++: No such file or directory
```

`/proc/cpuinfo` has `avx512f`, so `-DFORGE_PORTABLE` and `-DFORGE_MARCH=x86-64-v3` were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t6-fixed-node-score/forge-combo29 -B /tmp/wt-t6-fixed-node-score/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t6-fixed-node-score/build_rel -j4
cmake -S /tmp/wt-t6-fixed-node-score/forge-combo29 -B /tmp/wt-t6-fixed-node-score/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t6-fixed-node-score/build_san -j4
```

Both configures exited 0 and both builds ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t6-fixed-node-score/build_rel/forge
```

Exit 0. Stderr empty.

```
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 427 nps 2019505
nodes 4865609
```


Bench and perft do not set a node limit. The pins match with that behavior left unused.

## Task test

Sanitizer objects except `uci.cpp.o`.

Branch, exit 0, stderr empty:

```
nodes 1 depth 0 score 0 move a2a3
PASS fixed-node score and move agree checks 176
```

The other one-node lines were `d2d1`, `a2a3`, and `e2e3`.

Lock objects, exit 1, no sanitizer crash:

```
nodes 155 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
FAIL failures 27 checks 176
```

The test fails on the lock and passes on the branch.

## Report claims

Reproduced: a node budget between two finished iterations keeps the finished score and move on this commit and not on the lock (27 of 176 checks fail there); a budget of 1 node publishes depth 0 and score 0, including `a2a3` from the start position; the three pins. Not re-run as a separate UCI session: the report's `go nodes 155` transcript. The report itself says a pipe that sends `quit` immediately is an external stop, not this bug. No Elo or speed claim was checked.
