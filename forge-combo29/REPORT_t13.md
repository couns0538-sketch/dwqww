# Task t13: ThreadSanitizer on the locked multi-thread search

Engine tree: `forge-combo29` on `lock/combo29-20261110` (commit `16833ecc`).
Compiler for the sanitizer builds: Ubuntu clang 18.1.3. CPU has AVX-512; the release binary was still built with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, the same switches as the start command.

## What I found

The driver searches 20 positions (openings, middlegames, endings, and two forced mates) to depth 10 with Hash 16, first with 2 threads and then with 4. ThreadSanitizer reported **no data races**. The same driver built with `-fsanitize=address,undefined` reported nothing and exited 0.

Every transposition-table probe and store in that configuration takes the stripe mutex (`TranspositionTable::lock_stripe` in `src/search.cpp`). The main worker skips the stripe lock only when it holds `ExclusiveLease`, and `Searcher::search` takes that lease only for `TTAccess::Exclusive` with exactly one worker. The driver uses the default `TTAccess::Shared` with 2 and then 4 workers, so every worker locks. ThreadSanitizer staying silent on about 10^5 to 10^6 TT accesses per run is the check that those locks actually cover the entry fields.

History tables, correction tables, the evaluation cache, the search stack, and the root-move effort arrays are owned by each `Worker`. The shared stop flag, ponder-hit time, and per-worker node counters are `std::atomic`. Helpers are started after `new_search()` and are joined before the next search. That search reported no group B race and no group C race.

A second driver, `tests_t13/startup_race.cpp`, constructs the first `Board` on four threads at once. That is group C. `attacks::init` stored `static bool initialized = true` and then filled the attack tables. Another thread observed the flag, returned, and used `PawnTable`, `KnightTable`, `KingTable`, and a still-null bishop magic pointer. ThreadSanitizer reported those races and the process died with `SEGV` in `attacks::bishop` (`include/forge/bitboard.hpp:188`). The same tables are process-wide, so a torn fill can change later move generation.

## Torn hash entry (group A)

A hit is a copy of one 16-byte `TTEntry` made while the stripe lock is held, accepted only when `key32` equals `verification_key(key)` and the entry is occupied (`probe_body` in `src/search.cpp`). A store writes `key32` and the payload in that same critical section (`store_body`). Another worker cannot observe a key from one position mixed with data from another, because it cannot read or write that cluster until the writer releases the stripe. `__builtin_prefetch` does not load an entry into the search; Clang's ThreadSanitizer does not treat it as a memory access, and this run did not report it.

The code already refuses a mismatched key. I did not add a second "key combined with the data" word, and I did not add locks. There is no extra bench-time cost. The wall times below are the two pinned runs; they are not a speed claim.

## The change

Search with 2 and 4 threads did not need a lock or a new hash checksum: the stripe mutex plus `key32` already stops a torn hash entry from being used. Startup did. `attacks::init` now fills the tables inside `std::call_once`, so a second thread waits until the magic pointers and attack arrays are published. The fill itself is the same code as before. Bench node counts are unchanged. Engine diff is 8 insertions and 6 deletions.

## Files changed

- `forge-combo29/src/bitboard.cpp` (`std::call_once` around the existing fill)
- `forge-combo29/include/forge/bitboard.hpp` (comment only)
- `forge-combo29/tests_t13/race_driver.cpp` (added)
- `forge-combo29/tests_t13/startup_race.cpp` (added)
- `forge-combo29/REPORT_t13.md` (added)

## Races before

`race_driver` (20 positions, depth 10, Threads 2 then 4) on the unmodified engine: **no reports**. Groups A and B are empty. The shared hash table is locked on probe and store; prefetch does not load an entry.

`startup_race` on the unmodified engine, grouped by the pair of source lines. All of these are group C (startup). ThreadSanitizer stopped at the null bishop pointer, so later table pairs were not printed.

| Group | Read | Write | What |
| --- | --- | --- | --- |
| C | `src/bitboard.cpp:138` `initialized` | `src/bitboard.cpp:139` `initialized = true` | The flag is published before the fill. |
| C | `include/forge/bitboard.hpp:184` `pawn` | `src/bitboard.cpp:152` `PawnTable` | Reader uses the table while the writer is still storing it. |
| C | `include/forge/bitboard.hpp:181` `knight` | `src/bitboard.cpp:145` `KnightTable` | Same. |
| C | `include/forge/bitboard.hpp:182` `king` | `src/bitboard.cpp:149` `KingTable` | Same. |
| C | `include/forge/bitboard.hpp:188` `bishop` | fill still inside `init` | Null magic pointer. `SEGV`, process aborted. |

## Races after

`std::call_once` makes one thread finish the fill before any other thread returns from `init`. Re-runs:

- `startup_race` under ThreadSanitizer: exit 0, stderr empty, `PASS startup`. The info lines and `stop`/`reset_stop` from a second thread produced no report.
- `startup_race` under `-fsanitize=address,undefined`: exit 0, stderr empty, `PASS startup`.
- `race_driver` under ThreadSanitizer and under address/undefined: exit 0, stderr empty, `PASS failures 0`. The two mate fixtures must score at least `MateInMaxPly` (a loss for White is a failure). Later re-runs still printed 31999 and 31997.
- The UCI binary, including `src/uci.cpp`, under ThreadSanitizer: Threads 2 and 4, `go depth`, `go infinite` with `isready` during the search then `stop`, and `go ponder` then `ponderhit`. Stderr empty, exit 0. No group C report in option handling, the UCI worker, or `bestmove` output.

No report remains.

## Reference numbers

Rule 7, before any added file and again after this report, on `./build/forge`:

- `bench 11` = 312866
- `bench 13` = 862329
- `go perft 5` from the start position = 4865609

## Commands and output

Setup that was not an engine test: the first `cmake` failed because clang could not find `-lstdc++` (it selected GCC 14's lib directory, which had no `libstdc++.so`). `sudo apt-get install -y libstdc++-14-dev g++-14` fixed that. Linking `-fsanitize=thread` then failed for missing `libclang_rt.tsan-x86_64.a`; `sudo apt-get install -y libclang-rt-18-dev` provided it. `llvm-18` was installed so ThreadSanitizer could print file and line. A one-file ThreadSanitizer self-test (`int g; ++g` from two threads) reported `WARNING: ThreadSanitizer: data race` at that increment, so a silent engine run is not a dead runtime.

### Release configure, build, and rule 7 before any change

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
```

```
-- The CXX compiler identification is Clang 18.1.3
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 176 nps 1777647
info string bench depth 13 nodes 862329 time 445 nps 1937817
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit status 0.

### ThreadSanitizer driver (before), unmodified engine

Objects were compiled with:

```
-std=c++20 -O1 -g -fsanitize=thread -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -pthread
-DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1
-DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1
-DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -Iforge-combo29/include
```

Sources: `bitboard.cpp`, `board.cpp`, `book.cpp`, `eval.cpp`, `eval_params.cpp`, `nnue.cpp`, `search.cpp`, `tests_t13/race_driver.cpp` (not `uci.cpp`, which defines `main`). Linked as `/tmp/forge_t13/race_driver`.

```
TSAN_OPTIONS="halt_on_error=0:exitcode=0:log_path=/tmp/forge_t13/tsan_before:history_size=4:symbolize=1" /tmp/forge_t13/race_driver
```

No `tsan_before.*` log was created (ThreadSanitizer writes that file only when it reports). Stdout:

```
threads 2 depth 10 start move g1f3 score 18 nodes 24011 depth_reached 10 legal
threads 2 depth 10 e4 move c7c5 score -28 nodes 18962 depth_reached 10 legal
threads 2 depth 10 sicilian move g1f3 score 28 nodes 7761 depth_reached 10 legal
threads 2 depth 10 french move b1c3 score 33 nodes 38751 depth_reached 10 legal
threads 2 depth 10 kings-indian move b1c3 score 37 nodes 20309 depth_reached 10 legal
threads 2 depth 10 ruy move a7a6 score -27 nodes 36977 depth_reached 10 legal
threads 2 depth 10 qgd move g1f3 score 9 nodes 36984 depth_reached 10 legal
threads 2 depth 10 italian-middle move c3d5 score 59 nodes 42000 depth_reached 10 legal
threads 2 depth 10 caro-middle move f1d3 score 11 nodes 50515 depth_reached 10 legal
threads 2 depth 10 kiwipete move e2a6 score -126 nodes 107590 depth_reached 10 legal
threads 2 depth 10 tactical-middle move f6h5 score 610 nodes 24982 depth_reached 10 legal
threads 2 depth 10 queens-middle move f3e5 score 105 nodes 61591 depth_reached 10 legal
threads 2 depth 10 rook-end move b4f4 score 184 nodes 20714 depth_reached 10 legal
threads 2 depth 10 kp-end move e3e4 score 394 nodes 11362 depth_reached 10 legal
threads 2 depth 10 krk move e1d2 score 475 nodes 36588 depth_reached 10 legal
threads 2 depth 10 pawn-end move d1e2 score 226 nodes 7645 depth_reached 10 legal
threads 2 depth 10 opposite-bishops move c3b4 score 8 nodes 34014 depth_reached 10 legal
threads 2 depth 10 queen-end move d2d8 score 1106 nodes 41328 depth_reached 10 legal
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 342 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6b6 score 31997 nodes 932 depth_reached 10 legal mate_ok
threads 4 depth 10 start move d2d4 score 27 nodes 26557 depth_reached 10 legal
threads 4 depth 10 e4 move c7c5 score -26 nodes 21550 depth_reached 10 legal
threads 4 depth 10 sicilian move g1f3 score 29 nodes 16974 depth_reached 10 legal
threads 4 depth 10 french move e4d5 score 18 nodes 39807 depth_reached 10 legal
threads 4 depth 10 kings-indian move b1c3 score 42 nodes 41560 depth_reached 10 legal
threads 4 depth 10 ruy move g8e7 score -31 nodes 73359 depth_reached 10 legal
threads 4 depth 10 qgd move g1f3 score 27 nodes 54585 depth_reached 10 legal
threads 4 depth 10 italian-middle move c3d5 score 60 nodes 88721 depth_reached 10 legal
threads 4 depth 10 caro-middle move f1d3 score 2 nodes 35834 depth_reached 10 legal
threads 4 depth 10 kiwipete move e2a6 score -126 nodes 115547 depth_reached 10 legal
threads 4 depth 10 tactical-middle move f6h5 score 679 nodes 42231 depth_reached 10 legal
threads 4 depth 10 queens-middle move f3e5 score 118 nodes 54325 depth_reached 10 legal
threads 4 depth 10 rook-end move b4f4 score 209 nodes 28357 depth_reached 10 legal
threads 4 depth 10 kp-end move e3e4 score 401 nodes 20929 depth_reached 10 legal
threads 4 depth 10 krk move e1f2 score 453 nodes 71024 depth_reached 10 legal
threads 4 depth 10 pawn-end move d1c2 score 250 nodes 14925 depth_reached 10 legal
threads 4 depth 10 opposite-bishops move c3e5 score -8 nodes 57136 depth_reached 10 legal
threads 4 depth 10 queen-end move d2d4 score 1001 nodes 89909 depth_reached 10 legal
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 684 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6b6 score 31997 nodes 2051 depth_reached 10 legal mate_ok
PASS failures 0
```

Process status was recorded as `DONE:0`. Best moves differ across runs because helper threads race the main thread until `stop` is set. The driver checks that each best move is legal, and that both mate positions return a mate score. It does not require the same move twice.

### ThreadSanitizer driver again (after)

Same binary, same sources. Stderr was captured separately and was empty (0 bytes).

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/race_driver
```

Exit status 0. Stdout:

```
threads 2 depth 10 start move d2d4 score 15 nodes 16745 depth_reached 10 legal
threads 2 depth 10 e4 move c7c5 score -23 nodes 24655 depth_reached 10 legal
threads 2 depth 10 sicilian move b1c3 score 22 nodes 10704 depth_reached 10 legal
threads 2 depth 10 french move e4d5 score 14 nodes 29222 depth_reached 10 legal
threads 2 depth 10 kings-indian move b1c3 score 34 nodes 20603 depth_reached 10 legal
threads 2 depth 10 ruy move g8e7 score -24 nodes 34589 depth_reached 10 legal
threads 2 depth 10 qgd move e2e3 score 5 nodes 58406 depth_reached 10 legal
threads 2 depth 10 italian-middle move c3d5 score 54 nodes 41776 depth_reached 10 legal
threads 2 depth 10 caro-middle move a2a4 score -6 nodes 33083 depth_reached 10 legal
threads 2 depth 10 kiwipete move e2a6 score -129 nodes 103950 depth_reached 10 legal
threads 2 depth 10 tactical-middle move f6h5 score 616 nodes 21836 depth_reached 10 legal
threads 2 depth 10 queens-middle move f3e5 score 183 nodes 50184 depth_reached 10 legal
threads 2 depth 10 rook-end move b4f4 score 139 nodes 18455 depth_reached 10 legal
threads 2 depth 10 kp-end move e3e4 score 342 nodes 9843 depth_reached 10 legal
threads 2 depth 10 krk move e1f2 score 435 nodes 30533 depth_reached 10 legal
threads 2 depth 10 pawn-end move d1c2 score 228 nodes 6520 depth_reached 10 legal
threads 2 depth 10 opposite-bishops move f2e1 score -21 nodes 25603 depth_reached 10 legal
threads 2 depth 10 queen-end move d2d8 score 972 nodes 49674 depth_reached 10 legal
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 342 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6c7 score 31997 nodes 1269 depth_reached 10 legal mate_ok
threads 4 depth 10 start move e2e4 score 26 nodes 46319 depth_reached 10 legal
threads 4 depth 10 e4 move c7c5 score -26 nodes 27924 depth_reached 10 legal
threads 4 depth 10 sicilian move g1f3 score 26 nodes 17683 depth_reached 10 legal
threads 4 depth 10 french move e4d5 score 16 nodes 90967 depth_reached 10 legal
threads 4 depth 10 kings-indian move b1c3 score 39 nodes 23472 depth_reached 10 legal
threads 4 depth 10 ruy move a7a6 score -22 nodes 62159 depth_reached 10 legal
threads 4 depth 10 qgd move g1f3 score 24 nodes 41624 depth_reached 10 legal
threads 4 depth 10 italian-middle move a2a3 score 29 nodes 101606 depth_reached 10 legal
threads 4 depth 10 caro-middle move f1d3 score -5 nodes 52996 depth_reached 10 legal
threads 4 depth 10 kiwipete move e2a6 score -116 nodes 156276 depth_reached 10 legal
threads 4 depth 10 tactical-middle move f6h5 score 695 nodes 36684 depth_reached 10 legal
threads 4 depth 10 queens-middle move f3e5 score 147 nodes 76300 depth_reached 10 legal
threads 4 depth 10 rook-end move b4f4 score 183 nodes 28763 depth_reached 10 legal
threads 4 depth 10 kp-end move e3e4 score 365 nodes 14197 depth_reached 10 legal
threads 4 depth 10 krk move e1d2 score 441 nodes 64201 depth_reached 10 legal
threads 4 depth 10 pawn-end move d1c2 score 229 nodes 12449 depth_reached 10 legal
threads 4 depth 10 opposite-bishops move c3e5 score 0 nodes 87362 depth_reached 10 legal
threads 4 depth 10 queen-end move d2d8 score 1016 nodes 94375 depth_reached 10 legal
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 720 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 2125 depth_reached 10 legal mate_ok
PASS failures 0
```

### Address and undefined sanitizers

Same sources and the same `-O1 -g` defines, with `-fsanitize=address,undefined` instead of thread. Binary: `/tmp/forge_t13/race_driver_asan`.

```
ASAN_OPTIONS="halt_on_error=0:detect_leaks=1" UBSAN_OPTIONS="halt_on_error=0:print_stacktrace=1" /tmp/forge_t13/race_driver_asan
```

Exit status 0. Stderr was empty (0 bytes). Stdout:

```
threads 2 depth 10 start move e2e4 score 15 nodes 27657 depth_reached 10 legal
threads 2 depth 10 e4 move c7c5 score -26 nodes 24702 depth_reached 10 legal
threads 2 depth 10 sicilian move f1e2 score 22 nodes 9357 depth_reached 10 legal
threads 2 depth 10 french move e4d5 score 40 nodes 45316 depth_reached 10 legal
threads 2 depth 10 kings-indian move b1c3 score 37 nodes 19795 depth_reached 10 legal
threads 2 depth 10 ruy move g8e7 score -28 nodes 38766 depth_reached 10 legal
threads 2 depth 10 qgd move g1f3 score 32 nodes 47765 depth_reached 10 legal
threads 2 depth 10 italian-middle move c3d5 score 51 nodes 33914 depth_reached 10 legal
threads 2 depth 10 caro-middle move f1d3 score 3 nodes 21023 depth_reached 10 legal
threads 2 depth 10 kiwipete move e2a6 score -130 nodes 88867 depth_reached 10 legal
threads 2 depth 10 tactical-middle move f6h5 score 538 nodes 16318 depth_reached 10 legal
threads 2 depth 10 queens-middle move f3e5 score 151 nodes 31966 depth_reached 10 legal
threads 2 depth 10 rook-end move b4f4 score 122 nodes 28044 depth_reached 10 legal
threads 2 depth 10 kp-end move e3e4 score 378 nodes 10357 depth_reached 10 legal
threads 2 depth 10 krk move e1e2 score 447 nodes 34319 depth_reached 10 legal
threads 2 depth 10 pawn-end move d1c2 score 227 nodes 8733 depth_reached 10 legal
threads 2 depth 10 opposite-bishops move f2e1 score 0 nodes 32292 depth_reached 10 legal
threads 2 depth 10 queen-end move d2d8 score 1056 nodes 45377 depth_reached 10 legal
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 21501 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6c7 score 31997 nodes 888 depth_reached 10 legal mate_ok
threads 4 depth 10 start move e2e3 score 19 nodes 45075 depth_reached 10 legal
threads 4 depth 10 e4 move e7e6 score -26 nodes 43259 depth_reached 10 legal
threads 4 depth 10 sicilian move g1f3 score 21 nodes 42706 depth_reached 10 legal
threads 4 depth 10 french move e4e5 score 12 nodes 44325 depth_reached 10 legal
threads 4 depth 10 kings-indian move e2e3 score 27 nodes 28312 depth_reached 10 legal
threads 4 depth 10 ruy move g8e7 score -21 nodes 36973 depth_reached 10 legal
threads 4 depth 10 qgd move g1f3 score 24 nodes 66319 depth_reached 10 legal
threads 4 depth 10 italian-middle move c3d5 score 51 nodes 71562 depth_reached 10 legal
threads 4 depth 10 caro-middle move c4d5 score -5 nodes 44945 depth_reached 10 legal
threads 4 depth 10 kiwipete move d5e6 score -142 nodes 143824 depth_reached 10 legal
threads 4 depth 10 tactical-middle move f6h5 score 635 nodes 36490 depth_reached 10 legal
threads 4 depth 10 queens-middle move d4c5 score 109 nodes 81953 depth_reached 10 legal
threads 4 depth 10 rook-end move b4f4 score 102 nodes 25810 depth_reached 10 legal
threads 4 depth 10 kp-end move e3e4 score 386 nodes 21244 depth_reached 10 legal
threads 4 depth 10 krk move e1d2 score 459 nodes 46527 depth_reached 10 legal
threads 4 depth 10 pawn-end move d1e2 score 241 nodes 11075 depth_reached 10 legal
threads 4 depth 10 opposite-bishops move c3e5 score 0 nodes 60557 depth_reached 10 legal
threads 4 depth 10 queen-end move e3d3 score 1072 nodes 62099 depth_reached 10 legal
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 198 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 1503 depth_reached 10 legal mate_ok
PASS failures 0
```

### Rule 7 after the investigation

Same `./build/forge` binary (no engine object was rebuilt).

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 154 nps 2031597
info string bench depth 13 nodes 862329 time 420 nps 2053164
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit status 0.

### Startup race before the fix

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/startup_race
```

Exit status 66. Stdout was empty because the process aborted during construction. Stderr (summaries; the full stacks name the same pairs):

```
WARNING: ThreadSanitizer: data race
  Read of size 1 ... forge::attacks::init() bitboard.cpp:138
  Previous write of size 1 ... forge::attacks::init() bitboard.cpp:139
SUMMARY: ThreadSanitizer: data race .../src/bitboard.cpp:138:9 in forge::attacks::init()

WARNING: ThreadSanitizer: data race
  Read ... forge::attacks::pawn ... include/forge/bitboard.hpp:184
  Previous write ... forge::attacks::init() bitboard.cpp:152
SUMMARY: ... bitboard.hpp:184:12 in forge::attacks::pawn(forge::Color, int)

WARNING: ThreadSanitizer: data race
  Read ... forge::attacks::knight ... include/forge/bitboard.hpp:181
  Previous write ... forge::attacks::init() bitboard.cpp:145
SUMMARY: ... bitboard.hpp:181:59 in forge::attacks::knight(int)

WARNING: ThreadSanitizer: data race
  Read ... forge::attacks::king ... include/forge/bitboard.hpp:182
  Previous write ... forge::attacks::init() bitboard.cpp:149
SUMMARY: ... bitboard.hpp:182:57 in forge::attacks::king(int)

ThreadSanitizer:DEADLYSIGNAL
ERROR: ThreadSanitizer: SEGV on unknown address 0x000000000000
    #0 forge::attacks::bishop(int, unsigned long) include/forge/bitboard.hpp:188
SUMMARY: ThreadSanitizer: SEGV .../include/forge/bitboard.hpp:188:12 in forge::attacks::bishop(int, unsigned long)
==4825==ABORTING
```

### Rule 7 after `call_once`

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 155 nps 2018490
info string bench depth 13 nodes 862329 time 410 nps 2103241
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Exit status 0. Node counts match rule 7. The times are this run's wall clock, not a speed claim.

### Startup race after the fix

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/startup_race
```

Exit status 0. Stderr 0 bytes. Stdout:

```
startup constructors 4 bad 0
info depth 1 seldepth 1 score cp 1 nodes 52 nps 17333 hashfull 0 time 3 pv d2d4
info depth 2 seldepth 2 score cp 43 nodes 236 nps 59000 hashfull 0 time 4 pv g1f3 h7h6
info depth 3 seldepth 3 score cp 18 nodes 726 nps 145200 hashfull 0 time 5 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 35 nodes 1120 nps 140000 hashfull 0 time 8 pv d2d4 d7d5 g1f3 c7c6
info depth 5 seldepth 8 score cp 2 nodes 3309 nps 206812 hashfull 0 time 16 pv e2e3 g8f6 g1f3 c7c6 d2d4
info depth 6 seldepth 8 score cp 15 nodes 4474 nps 194521 hashfull 0 time 23 pv d2d4 d7d5 g1f3 g8f6 a2a3 h7h6
info depth 7 seldepth 9 score cp 5 nodes 8888 nps 253942 hashfull 0 time 35 pv e2e4 g8f6 b1c3 d7d5 e4d5 f6d5 g1f3
info depth 8 seldepth 14 score cp 18 nodes 17018 nps 226906 hashfull 5 time 75 pv g1f3 e7e6 e2e3 g8f6 d2d4 c7c5 c2c4 c5d4 e3d4
stopped-search move g1f3 score 18 depth 8 legal
PASS startup
```

```
ASAN_OPTIONS="halt_on_error=0:detect_leaks=1" UBSAN_OPTIONS="halt_on_error=0:print_stacktrace=1" /tmp/forge_t13/startup_race_asan
```

Exit status 0. Stderr 0 bytes. Stdout:

```
startup constructors 4 bad 0
info depth 1 seldepth 1 score cp 1 nodes 52 nps 52000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 216 nps 216000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 851 nps 425500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 1220 nps 406666 hashfull 0 time 3 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 2104 nps 526000 hashfull 0 time 4 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 9 score cp 15 nodes 4909 nps 818166 hashfull 0 time 6 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6
info depth 7 seldepth 10 score cp 29 nodes 8414 nps 1051750 hashfull 1 time 8 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 g1f3
info depth 8 seldepth 13 score cp 15 nodes 10577 nps 961545 hashfull 3 time 11 pv d2d4 g8f6 c2c4 e7e6 g1f3 c7c5 e2e3 b7b6
stopped-search move d2d4 score 15 depth 8 legal
PASS startup
```

### Depth-10 driver again after the fix

Both binaries were relinked with the new `bitboard.o`. Stderr was empty for both. Exit status 0.

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/race_driver
```

```
threads 2 depth 10 start move d2d4 score 23 nodes 20349 depth_reached 10 legal
threads 2 depth 10 e4 move c7c5 score -27 nodes 28911 depth_reached 10 legal
threads 2 depth 10 sicilian move g1f3 score 26 nodes 14484 depth_reached 10 legal
threads 2 depth 10 french move e4d5 score 36 nodes 44995 depth_reached 10 legal
threads 2 depth 10 kings-indian move g1f3 score 46 nodes 19016 depth_reached 10 legal
threads 2 depth 10 ruy move g8e7 score -32 nodes 30989 depth_reached 10 legal
threads 2 depth 10 qgd move g1f3 score 30 nodes 33827 depth_reached 10 legal
threads 2 depth 10 italian-middle move c3d5 score 47 nodes 59686 depth_reached 10 legal
threads 2 depth 10 caro-middle move f1e2 score 3 nodes 33018 depth_reached 10 legal
threads 2 depth 10 kiwipete move e2a6 score -125 nodes 92629 depth_reached 10 legal
threads 2 depth 10 tactical-middle move f6h5 score 737 nodes 27208 depth_reached 10 legal
threads 2 depth 10 queens-middle move f3e5 score 126 nodes 31474 depth_reached 10 legal
threads 2 depth 10 rook-end move b4f4 score 224 nodes 23486 depth_reached 10 legal
threads 2 depth 10 kp-end move e3e4 score 374 nodes 9331 depth_reached 10 legal
threads 2 depth 10 krk move e1f2 score 458 nodes 48685 depth_reached 10 legal
threads 2 depth 10 pawn-end move d1e2 score 230 nodes 7062 depth_reached 10 legal
threads 2 depth 10 opposite-bishops move c3e5 score 12 nodes 28516 depth_reached 10 legal
threads 2 depth 10 queen-end move d2h2 score 1099 nodes 49663 depth_reached 10 legal
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 342 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6c7 score 31997 nodes 1277 depth_reached 10 legal mate_ok
threads 4 depth 10 start move d2d4 score 22 nodes 35148 depth_reached 10 legal
threads 4 depth 10 e4 move c7c5 score -29 nodes 41176 depth_reached 10 legal
threads 4 depth 10 sicilian move g1f3 score 20 nodes 40595 depth_reached 10 legal
threads 4 depth 10 french move b1d2 score 39 nodes 58256 depth_reached 10 legal
threads 4 depth 10 kings-indian move b1c3 score 52 nodes 33619 depth_reached 10 legal
threads 4 depth 10 ruy move a7a6 score -28 nodes 61430 depth_reached 10 legal
threads 4 depth 10 qgd move g1f3 score 19 nodes 55219 depth_reached 10 legal
threads 4 depth 10 italian-middle move c3d5 score 49 nodes 48161 depth_reached 10 legal
threads 4 depth 10 caro-middle move f1d3 score 9 nodes 40123 depth_reached 10 legal
threads 4 depth 10 kiwipete move e2a6 score -111 nodes 134640 depth_reached 10 legal
threads 4 depth 10 tactical-middle move f6h5 score 674 nodes 54412 depth_reached 10 legal
threads 4 depth 10 queens-middle move f3e5 score 154 nodes 57852 depth_reached 10 legal
threads 4 depth 10 rook-end move b4f4 score 190 nodes 37013 depth_reached 10 legal
threads 4 depth 10 kp-end move e3e4 score 388 nodes 16606 depth_reached 10 legal
threads 4 depth 10 krk move e1f2 score 458 nodes 33788 depth_reached 10 legal
threads 4 depth 10 pawn-end move d1e2 score 240 nodes 11335 depth_reached 10 legal
threads 4 depth 10 opposite-bishops move f2e2 score -9 nodes 76626 depth_reached 10 legal
threads 4 depth 10 queen-end move d2d8 score 1047 nodes 51643 depth_reached 10 legal
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 684 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 2178 depth_reached 10 legal mate_ok
PASS failures 0
```

```
ASAN_OPTIONS="halt_on_error=0:detect_leaks=1" UBSAN_OPTIONS="halt_on_error=0:print_stacktrace=1" /tmp/forge_t13/race_driver_asan
```

```
threads 2 depth 10 start move d2d4 score 20 nodes 17484 depth_reached 10 legal
threads 2 depth 10 e4 move c7c5 score -28 nodes 22798 depth_reached 10 legal
threads 2 depth 10 sicilian move g1f3 score 26 nodes 7060 depth_reached 10 legal
threads 2 depth 10 french move e4d5 score 16 nodes 44175 depth_reached 10 legal
threads 2 depth 10 kings-indian move b1c3 score 31 nodes 16704 depth_reached 10 legal
threads 2 depth 10 ruy move c6d4 score -45 nodes 27992 depth_reached 10 legal
threads 2 depth 10 qgd move g1f3 score 20 nodes 34323 depth_reached 10 legal
threads 2 depth 10 italian-middle move c3d5 score 50 nodes 33761 depth_reached 10 legal
threads 2 depth 10 caro-middle move c4d5 score -2 nodes 18063 depth_reached 10 legal
threads 2 depth 10 kiwipete move d5e6 score -128 nodes 120354 depth_reached 10 legal
threads 2 depth 10 tactical-middle move g3g6 score 31997 nodes 21148 depth_reached 10 legal
threads 2 depth 10 queens-middle move d4c5 score 143 nodes 37325 depth_reached 10 legal
threads 2 depth 10 rook-end move b4f4 score 175 nodes 24841 depth_reached 10 legal
threads 2 depth 10 kp-end move e3e4 score 371 nodes 8954 depth_reached 10 legal
threads 2 depth 10 krk move e1d2 score 439 nodes 42796 depth_reached 10 legal
threads 2 depth 10 pawn-end move d1c2 score 228 nodes 7206 depth_reached 10 legal
threads 2 depth 10 opposite-bishops move c3a1 score -16 nodes 43039 depth_reached 10 legal
threads 2 depth 10 queen-end move e3e2 score 1119 nodes 79710 depth_reached 10 legal
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 26925 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6b6 score 31997 nodes 939 depth_reached 10 legal mate_ok
threads 4 depth 10 start move d2d4 score 20 nodes 32273 depth_reached 10 legal
threads 4 depth 10 e4 move c7c5 score -21 nodes 34019 depth_reached 10 legal
threads 4 depth 10 sicilian move g1f3 score 19 nodes 14080 depth_reached 10 legal
threads 4 depth 10 french move e4d5 score 24 nodes 42052 depth_reached 10 legal
threads 4 depth 10 kings-indian move b1c3 score 32 nodes 30083 depth_reached 10 legal
threads 4 depth 10 ruy move g8e7 score -16 nodes 38993 depth_reached 10 legal
threads 4 depth 10 qgd move g1f3 score 14 nodes 67258 depth_reached 10 legal
threads 4 depth 10 italian-middle move c3d5 score 58 nodes 68498 depth_reached 10 legal
threads 4 depth 10 caro-middle move f1e2 score 3 nodes 34623 depth_reached 10 legal
threads 4 depth 10 kiwipete move e2a6 score -89 nodes 140060 depth_reached 10 legal
threads 4 depth 10 tactical-middle move f6h5 score 590 nodes 30183 depth_reached 10 legal
threads 4 depth 10 queens-middle move d4c5 score 147 nodes 88146 depth_reached 10 legal
threads 4 depth 10 rook-end move b4f4 score 174 nodes 34051 depth_reached 10 legal
threads 4 depth 10 kp-end move e3e4 score 372 nodes 11619 depth_reached 10 legal
threads 4 depth 10 krk move e1d2 score 450 nodes 62569 depth_reached 10 legal
threads 4 depth 10 pawn-end move d1c2 score 229 nodes 9467 depth_reached 10 legal
threads 4 depth 10 opposite-bishops move c3e5 score 0 nodes 30008 depth_reached 10 legal
threads 4 depth 10 queen-end move d2d8 score 1071 nodes 49951 depth_reached 10 legal
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 198 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 2041 depth_reached 10 legal mate_ok
PASS failures 0
```

### UCI worker under ThreadSanitizer

`src/uci.cpp` is linked into this binary. `OwnBook` is false, so the book does not answer. Stderr was empty. Process exit status 0.

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/forge_tsan
```

Commands and the engine's replies:

```
>> uci
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name Clear Hash type button
uciok
>> isready
readyok
>> setoption name Hash value 16
>> setoption name Threads value 2
>> setoption name OwnBook value false
>> setoption name Ponder value true
>> ucinewgame
>> position startpos
>> go depth 6
info depth 1 seldepth 1 score cp 1 nodes 52 nps 17333 hashfull 0 time 3 pv d2d4
info depth 2 seldepth 2 score cp 43 nodes 135 nps 33750 hashfull 0 time 4 pv g1f3 h7h6
info depth 3 seldepth 3 score cp 18 nodes 344 nps 68800 hashfull 0 time 5 pv e2e4 h7h6 d2d4
info depth 4 seldepth 5 score cp 35 nodes 823 nps 91444 hashfull 0 time 9 pv d2d4 d7d5 g1f3 c7c6
info depth 5 seldepth 7 score cp 6 nodes 2241 nps 124500 hashfull 0 time 18 pv c2c4 c7c5 h2h3 g8f6 g1f3
info depth 6 seldepth 9 score cp 18 nodes 2767 nps 125772 hashfull 0 time 22 pv c2c4 c7c5 h2h3 g8f6 g1f3 h7h6
bestmove c2c4 ponder c7c5
>> position fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1
>> go depth 6
info depth 1 seldepth 1 score mate 1 nodes 1477 nps 0 hashfull 0 time 0 pv a1a8
info depth 6 seldepth 6 score mate 1 nodes 216 nps 216000 hashfull 0 time 1 pv a1a8
bestmove a1a8
>> setoption name Threads value 4
>> position startpos
>> go infinite
>> isready
info depth 11 seldepth 19 score cp 25 nodes 60795 nps 236556 hashfull 24 time 257 pv e2e4 c7c5 g1f3 d7d6 f1e2 g8f6 b1c3 b8c6 e1g1 c8d7 h2h3
readyok
>> stop
bestmove e2e4 ponder c7c5
>> position fen k7/8/2K5/8/8/8/8/7R w - - 0 1
>> go depth 4 ponder
>> ponderhit
info depth 4 seldepth 6 score cp 513 nodes 929 nps 232250 hashfull 0 time 4 pv c6d5 a8b7 h1h4 b7c8
bestmove c6d5 ponder a8b7
>> quit
```

The `uci` reply also listed every exposed tunable option between `UseNNUE` and `Clear Hash`. Those lines are the option table from `uci.cpp` and contained no sanitizer text. The mate search printed `info depth 2` through `info depth 5` as `score mate 1` with pv `a1a8` before the depth-6 line shown above. `go infinite` printed `info depth 1` through `info depth 10` before the depth-11 line, and `readyok` arrived while that search was still running.

### Winning-mate check

`race_driver` now requires `info.score >= MateInMaxPly` on the two white-to-move mates. `is_mate_score` would also accept a loss. Re-run after that change:

```
TSAN_OPTIONS="halt_on_error=0:symbolize=1" /tmp/forge_t13/race_driver
```

Exit status 0, stderr 0 bytes. Mate lines:

```
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 343 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6b6 score 31997 nodes 1270 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 702 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 2339 depth_reached 10 legal mate_ok
PASS failures 0
```

```
ASAN_OPTIONS="halt_on_error=0:detect_leaks=1" UBSAN_OPTIONS="halt_on_error=0:print_stacktrace=1" /tmp/forge_t13/race_driver_asan
```

Exit status 0, stderr 0 bytes. Mate lines:

```
threads 2 depth 10 mate-1 move a1a8 score 31999 nodes 27828 depth_reached 10 legal mate_ok
threads 2 depth 10 mate-2 move c6c7 score 31997 nodes 774 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-1 move a1a8 score 31999 nodes 15983 depth_reached 10 legal mate_ok
threads 4 depth 10 mate-2 move c6c7 score 31997 nodes 1612 depth_reached 10 legal mate_ok
PASS failures 0
```

## What I could not verify

- A non-portable build (`FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`). Sanitizer and release runs used the portable x86-64-v3 flags.
- Multi-thread best-move stability. Lazy SMP is allowed to return different legal moves; only the single-thread rule 7 node counts are pinned.
- Any bench-time cost of a combined-key checksum. It was not added. The locked probe already copies the entry and checks `key32`.
