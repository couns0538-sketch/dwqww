# VERIFY t13

Branch `grok47/t13-thread-sanitizer` at `a847f23765d9404725449a9c8f3fe3c7c78685f2`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `include/forge/bitboard.hpp`, `src/bitboard.cpp`, `tests_t13/race_driver.cpp`, `tests_t13/startup_race.cpp`, `REPORT_t13.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 8 insertions, 6 deletions. `attacks::init` now uses `std::call_once` instead of a `static bool` stored before the tables are filled.

## Safety

The engine change is a `std::once_flag`. The tests start threads:

```
std::vector<std::thread> construction;
std::thread stopper([&searcher] { searcher.stop(); searcher.reset_stop(); });
```

`race_driver.cpp` says it uses no files, processes, or network. No registry, environment access, or obfuscation.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`. ThreadSanitizer was not built. The required sanitizer configure is address and undefined.

## Pins

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 432 nps 1996131
nodes 4865609
```

## Task test

`startup_race` on lock sanitizer objects, exit 134:

```
runtime error: load of null pointer of type 'Bitboard'
SUMMARY: AddressSanitizer: SEGV /tmp/verify/src/forge-combo29/include/forge/bitboard.hpp:188 in forge::attacks::bishop(int, unsigned long)
```

The stack names `tests_t13/startup_race.cpp:20` and `:19`, the concurrent `Board` constructor.

This commit, exit 0, no sanitizer report:

```
startup constructors 4 bad 0
stopped-search move e2e4 score 16 depth 8 legal
PASS startup
```

`race_driver` (depth 10, 20 positions, Threads 2 then 4) printed `PASS failures 0` on both this commit and the lock, exit 0, with no ASan/UBSan report. It does not, by itself, show the startup race. The startup test does.

## Report claims

Reproduced: the lock crashes when several threads construct the first `Board`, and this commit does not; bench and perft pins match. Not reproduced: any ThreadSanitizer log in the report. This run did not execute `-fsanitize=thread`. No Elo or speed claim was checked.
