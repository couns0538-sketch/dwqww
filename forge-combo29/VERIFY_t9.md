# VERIFY t9

Branch `grok47/t9-eval` at `ff4d8498c6d77b3e53a899fd3a88ab984748ee77`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

This branch was not in the previous status file.

## Rule check

Files: `include/forge/eval.hpp`, `src/eval.cpp`, `src/uci.cpp`, `tests_t9/eval_test.cpp`, `eval_commands.txt`, `eval_expected.txt`, `REPORT_t9.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 22 insertions, 0 deletions (`eval.hpp` 6, `eval.cpp` 13, `uci.cpp` 3). `uci` does not advertise a new option. `eval` is a command.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. `eval_report` builds one string and the UCI loop prints it (`src/uci.cpp:379`). The test calls `eval_report` in-process.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t9-eval/forge-combo29 -B /tmp/wt-t9-eval/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t9-eval/build_rel -j4
cmake -S /tmp/wt-t9-eval/forge-combo29 -B /tmp/wt-t9-eval/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t9-eval/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t9-eval/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 429 nps 2010090
nodes 4865609
```


There is no new option to leave at a non-default. The pins match.

## Task test

`eval_test.cpp` linked to this commit's sanitizer objects except `uci.cpp.o`. Exit 0, stderr empty:

```
info string eval hce 18 nnue 20 sum 38
info string eval hce -52 nnue 63 sum 11
info string eval hce -52 nnue off sum -52
```

That is `tests_t9/eval_expected.txt`. `38 = 18 + 20` and `11 = -52 + 63`.

The same source against the lock headers failed to compile: `'eval_report' is not a member of 'forge'`.

Release UCI, the commands in `eval_commands.txt`, exit 0:

```
info string eval hce 18 nnue 20 sum 38
info string eval hce -52 nnue 63 sum 11
info string eval hce -52 nnue off sum -52
```

The lock release binary, `eval` then `quit`, printed no line containing `eval`.

## Report claims

Reproduced: the three lines and the sums, start-position hce 18 / nnue 20 / sum 38, the position after `e2e4` (hce -52, nnue 63, sum 11), `UseNNUE false` printing `nnue off` with sum equal to hce, the test not compiling on the lock, and the three pins. Not checked: whether those sums equal `Worker::static_evaluate`. The report says they do not have to. No Elo or speed claim was checked.
