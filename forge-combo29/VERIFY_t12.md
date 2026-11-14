# VERIFY t12

Branch `grok47/t12-krk-root-cause` at `0d928468f48805ef8ff25c8b9c682d5d66898ad6`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `5485588b` changes only `REPORT_t12.md`. The engine and the test were built and run again.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `tests_t12/krk_mate_test.cpp`, `REPORT_t12.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 68 insertions, 5 deletions.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test searches in-process.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t12-krk-root-cause/forge-combo29 -B /tmp/wt-t12-krk-root-cause/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t12-krk-root-cause/build_rel -j4
cmake -S /tmp/wt-t12-krk-root-cause/forge-combo29 -B /tmp/wt-t12-krk-root-cause/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t12-krk-root-cause/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t12-krk-root-cause/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 168 nps 1862297
info string bench depth 13 nodes 862329 time 438 nps 1968787
nodes 4865609
```


## Task test

`krk_mate_test.cpp` linked to sanitizer objects except `uci.cpp.o`. `ASAN_OPTIONS=detect_leaks=0`.

```
/tmp/tests/t12_branch 2 16 10 40
```

```
examined 49
t1_mates 40
runs 400
misses 0
score_misses 0
move_misses 0
```

Exit 0. Stderr 0 bytes. The mate-10 position `8/8/8/2R5/8/8/1k6/3K4 w - - 0 1` was one of the 40 (`mate 10 d1d2`).

Lock objects, same test source and arguments:

```
examined 49
t1_mates 40
runs 400
misses 0
score_misses 0
move_misses 0
```

Exit 0. Stderr 0 bytes. The same mate-10 position was in the lock's 40 as well. No AddressSanitizer or UndefinedBehaviorSanitizer diagnostic on either link.

This run does not show the test failing on the lock. The report says a 40 by 10 sample on the lock can be 0 misses.

## Report claims

Reproduced: branch misses 0 of 400, the three pins, and the test's own exit 0. Not reproduced this run: a lock miss. The report's table says one 40 by 10 lock run was 0, then 1, then 0, and that the mate-10 position alone missed 8 of 400 and later 6 of 400. That isolated repeat was not run. No Elo or speed claim was checked.
