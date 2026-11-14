# VERIFY t12

Branch `grok47/t12-krk-root-cause` at `5485588b3b6147340d82a2a10059dc473645c821`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

`git diff --name-status 16833ecc...5485588b`:

```
A	forge-combo29/REPORT_t12.md
M	forge-combo29/include/forge/search.hpp
M	forge-combo29/src/search.cpp
A	forge-combo29/tests_t12/krk_mate_test.cpp
```

All four are mode 100644. No executable, archive, script, workflow, or Python file is in the diff. Engine source is `search.hpp` 15 insertions and `search.cpp` 53 insertions, 5 deletions (73 changed lines). Under the 300-line cap.

## Safety

The diff adds a transposition-table flag and a replacement rule. It has no network use, process start, registry or environment access, obfuscated code, or file write. The new default is a compile-time switch, left on:

```
#ifndef FORGE_T12_MATE_TT
#define FORGE_T12_MATE_TT 1
#endif
```

`include/forge/search.hpp` lines 23-30. One worker leaves `protect_mates_` false, so that path keeps the lock replacement. The test searches in-process.

## Build

The stated cmake line, without a compiler override, failed on this machine. `/usr/bin/c++` is Clang 18.1.3:

```
cmake -S /tmp/wt-lock/forge-combo29 -B /tmp/wt-lock/build_clang -DCMAKE_BUILD_TYPE=Release
```

```
/usr/bin/ld: cannot find -lstdc++: No such file or directory
EXIT:1
```

Release and sanitizer builds were configured with g++ 13.3.0. `/proc/cpuinfo` has `avx512f`, so `-DFORGE_PORTABLE` and `-DFORGE_MARCH=x86-64-v3` were not added.

```
cmake -S /tmp/wt-t12/forge-combo29 -B /tmp/wt-t12/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t12/build_rel -j
cmake -S /tmp/wt-t12/forge-combo29 -B /tmp/wt-t12/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t12/build_san -j
```

Both ended `Built target forge` and `BUILD_EXIT:0`.

## Pins

Threads 1, Hash 16, OwnBook false:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t12/build_rel/forge
```

```
info string bench depth 11 nodes 312866 time 180 nps 1738144
info string bench depth 13 nodes 862329 time 473 nps 1823105
nodes 4865609
```

Exit 0. The same three node counts came from the lock release binary. The perft listing ends `g1h3: 198502` and then `nodes 4865609`. No new UCI option. The single-thread bench and perft stay on the lock counts with `FORGE_T12_MATE_TT` left at 1.

## Task test

`tests_t12/krk_mate_test.cpp` was compiled with the sanitizer flags and include tree, then linked to the sanitizer objects except `uci.cpp.o` (the test has its own `main`). `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. LeakSanitizer was off.

This commit:

```
/tmp/tests/t12_branch 2 16 10 40
```

```
settings threads 2 hash_mb 16 runs 10 target 40 depth 14
candidates 10987
progress examined 25 mates 22
examined 49
t1_mates 40
runs 400
misses 0
score_misses 0
move_misses 0
```

Exit 0. Stderr was 0 bytes. Forty `t1` lines were printed. The same forty lines were printed by the lock link.

Lock objects, same test source, same arguments:

```
/tmp/tests/t12_lock 2 16 10 40
```

```
examined 49
t1_mates 40
miss 8/8/8/2R5/8/8/1k6/3K4 w - - 0 1 run 0 cp 483 d1e2 no-mate-score
runs 400
misses 1
score_misses 1
move_misses 0
```

Exit 1. Stderr was 0 bytes. No AddressSanitizer or UndefinedBehaviorSanitizer diagnostic on either link. The test fails on the lock and passes here.

## Report claims

Reproduced: the three pin counts; one 40×10 run of the unchanged engine missing the mate on `8/8/8/2R5/8/8/1k6/3K4`; one 40×10 run after the change with `misses 0`; sanitizer stderr empty and exit 0 on that run.

Not the same sample as the report. The report's unchanged miss on that position was `cp 445 d1d2`. This run printed `cp 483 d1e2`. The three repeats, the 40×40 runs, the 2000-search run, and a build with `FORGE_T12_MATE_TT` set to 0 were not run. ThreadSanitizer was not run. No Elo or speed claim was checked.

This is a different task from `grok47/t5-krk-mate`. t5's test is the history and node-budget KRK check. This test is the two-thread table replacement.
