# VERIFY t5

Branch `grok47/t5-krk-mate` at `7f824bd0ab8f84a83d659980a92b04da31d01e96`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `143edfb6` changes only `REPORT_t5.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `tests_t5/krk_mate_test.cpp`, `REPORT_t5.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 51 insertions, 22 deletions.

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
cmake -S /tmp/wt-t5-krk-mate/forge-combo29 -B /tmp/wt-t5-krk-mate/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t5-krk-mate/build_rel -j4
cmake -S /tmp/wt-t5-krk-mate/forge-combo29 -B /tmp/wt-t5-krk-mate/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t5-krk-mate/build_san -j4
```

Both configures exited 0 and both builds ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t5-krk-mate/build_rel/forge
```

Exit 0. Stderr empty.

```
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 440 nps 1959838
nodes 4865609
```


## Task test

`krk_mate_test.cpp` linked to sanitizer objects except `uci.cpp.o`.

Lock, exit 1, stderr empty of sanitizer diagnostics:

```
history FAIL
history FAIL
history ok
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 26 first mate 9 e8d7
threads FAIL
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 30 first cp 469 b3b6
threads FAIL
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 20 first mate 9 e8d7
threads FAIL
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 11 cp 18 d2d4 total 30000
node budget FAIL
FAILED 6
```

This commit, exit 0, stderr empty:

```
history ok
history ok
history ok
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 11 cp 24 d2d4 total 30000
node budget ok
ok
```

The test fails on the lock and passes on the branch.

## Report claims

Reproduced: history carried across positions fails on the lock and passes here; two-thread KRK mismatches on the lock are 0 here; a 30000-node search is depth 11, cp 24, `d2d4` on both thread counts here, and depth 10 / cp 18 on the lock's second thread; the three pins. The report's longer mate-distance table was not re-run position by position beyond this test. No Elo or speed claim was checked.
