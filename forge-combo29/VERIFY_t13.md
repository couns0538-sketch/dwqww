# VERIFY t13

Branch `grok47/t13-thread-sanitizer` at `87228469411670ea5ccfc7154ce181dd55d599df`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

The commit since `a847f237` adds `WHAT_WAS_WRONG_t13.md` and touches `REPORT_t13.md`. The engine was not changed by that commit. It was built and run again.

## Rule check

Files: `REPORT_t13.md`, `WHAT_WAS_WRONG_t13.md`, `include/forge/bitboard.hpp`, `src/bitboard.cpp`, `tests_t13/race_driver.cpp`, `tests_t13/startup_race.cpp`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 8 insertions, 6 deletions.

Outside the allowed set: `forge-combo29/WHAT_WAS_WRONG_t13.md`.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The engine change is a `std::once_flag` around table init:

```
src/bitboard.cpp:140
    static std::once_flag once;
    std::call_once(once, [] {
```

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t13-thread-sanitizer/forge-combo29 -B /tmp/wt-t13-thread-sanitizer/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t13-thread-sanitizer/build_rel -j4
cmake -S /tmp/wt-t13-thread-sanitizer/forge-combo29 -B /tmp/wt-t13-thread-sanitizer/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t13-thread-sanitizer/build_san -j4
```

Both ended `Built target forge`.


ThreadSanitizer was not built. The required sanitizer configure is address and undefined.

## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t13-thread-sanitizer/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 168 nps 1862297
info string bench depth 13 nodes 862329 time 443 nps 1946566
nodes 4865609
```


## Task test

`startup_race` on lock sanitizer objects, exit 1. Stderr:

```
SUMMARY: AddressSanitizer: SEGV /tmp/wt-lock/forge-combo29/include/forge/bitboard.hpp:188 in forge::attacks::bishop(int, unsigned long)
```

The stack names `tests_t13/startup_race.cpp:20`, the concurrent `Board` constructor. Also: `runtime error: load of null pointer of type 'Bitboard'`.

This commit, exit 0, stderr empty:

```
startup constructors 4 bad 0
stopped-search move d2d4 score 32 depth 8 legal
PASS startup
```

`race_driver 10 20` printed `PASS failures 0` on this commit and on the lock, both exit 0, stderr empty. It does not show the startup race. The startup test does.

## Report claims

Reproduced: the lock startup SEGV, this commit's `PASS startup`, and `race_driver` passing on both. Not run: ThreadSanitizer. The new `WHAT_WAS_WRONG_t13.md` restates that race; the startup test is the part that was run. No Elo or speed claim was checked.

## What to fix

Put that explanation in `REPORT_t13.md` or under `tests_t13/`. Remove `WHAT_WAS_WRONG_t13.md` from the branch diff.
