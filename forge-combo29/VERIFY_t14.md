# VERIFY t14

Branch `grok47/t14-eval-command` at `26f450b684178a7241bcab3b9a2a6b8886420daf`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

The commit since `ed31021d` changes only `REPORT_t14.md`. The engine, CMake, and README are unchanged from the previous check and were built and run again.

## Rule check

Files: `CMakeLists.txt`, `README.md`, `REPORT_t14.md`, `include/forge/eval.hpp`, `src/eval.cpp`, `src/uci.cpp`, `tests_t14/eval_cases.txt`, `tests_t14/test_eval.cpp`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 47 insertions, 0 deletions.

Outside the allowed set: `forge-combo29/CMakeLists.txt` and `forge-combo29/README.md`.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. `eval` prints one line. The test reads `eval_cases.txt`.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t14-eval-command/forge-combo29 -B /tmp/wt-t14-eval-command/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t14-eval-command/build_rel -j4
cmake -S /tmp/wt-t14-eval-command/forge-combo29 -B /tmp/wt-t14-eval-command/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t14-eval-command/build_san -j4
```

Both ended `Built target forge`.
The sanitizer build also ended `Built target test_t14_eval`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t14-eval-command/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 428 nps 2014787
nodes 4865609
```


## Task test

```
/tmp/wt-t14-eval-command/build_san/test_t14_eval /tmp/wt-t14-eval-command/forge-combo29/tests_t14/eval_cases.txt
```

Exit 0, stderr empty:

```
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
```

The same test against the lock headers failed to compile: `'EvalComponents' in namespace 'forge' does not name a type`.

Sanitizer UCI:

```
position startpos
eval
info string eval hce 18 nnue 20 total 38
position fen 4k3/8/8/8/8/8/8/4K2r w - - 0 1
eval
info string eval hce -438 nnue 95 total -343 incheck 1
```

The lock binary's `eval` command produced no output.

## Report claims

Reproduced: the 30-position summary, the two UCI lines, the lock's silence, and the three pins. No Elo or speed claim was checked.

## What to fix

Keep `eval` in `src` and `include`, and the test under `tests_t14/`. Do not change `CMakeLists.txt` or `README.md`. The test already links when compiled by hand against the objects.
