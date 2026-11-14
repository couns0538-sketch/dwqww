# Task t13: ThreadSanitizer on the locked multi-thread search

Engine tree: `forge-combo29` on `lock/combo29-20261110` (commit `16833ecc`).
Compiler for the sanitizer builds: Ubuntu clang 18.1.3. CPU has AVX-512; the release binary was still built with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, the same switches as the start command.

## What I found

The driver searches 20 positions (openings, middlegames, endings, and two forced mates) to depth 10 with Hash 16, first with 2 threads and then with 4. ThreadSanitizer reported **no data races**. The same driver built with `-fsanitize=address,undefined` reported nothing and exited 0.

Every transposition-table probe and store in that configuration takes the stripe mutex (`TranspositionTable::lock_stripe` in `src/search.cpp`). The main worker skips the stripe lock only when it holds `ExclusiveLease`, and `Searcher::search` takes that lease only for `TTAccess::Exclusive` with exactly one worker. The driver uses the default `TTAccess::Shared` with 2 and then 4 workers, so every worker locks. ThreadSanitizer staying silent on about 10^5 to 10^6 TT accesses per run is the check that those locks actually cover the entry fields.

History tables, correction tables, the evaluation cache, the search stack, and the root-move effort arrays are owned by each `Worker`. The shared stop flag, ponder-hit time, and per-worker node counters are `std::atomic`. Helpers are started after `new_search()` and are joined before the next search. No group B or group C race was reported, so no atomic, thread-local copy, or pass-by-value change was made.

## Torn hash entry (group A)

A hit is a copy of one 16-byte `TTEntry` made while the stripe lock is held, accepted only when `key32` equals `verification_key(key)` and the entry is occupied (`probe_body` in `src/search.cpp`). A store writes `key32` and the payload in that same critical section (`store_body`). Another worker cannot observe a key from one position mixed with data from another, because it cannot read or write that cluster until the writer releases the stripe. `__builtin_prefetch` does not load an entry into the search; Clang's ThreadSanitizer does not treat it as a memory access, and this run did not report it.

The code already refuses a mismatched key. I did not add a second "key combined with the data" word, and I did not add locks. There is no extra bench-time cost. The wall times below are the two pinned runs; they are not a speed claim.

## The change

No engine source was changed. ThreadSanitizer, ASan, and UBSan were clean on the locked search with 2 and 4 threads, and the stripe lock plus the `key32` check already stops a torn hash entry from being used. The only added files are this report and `tests_t13/race_driver.cpp`.

## Files changed

- `forge-combo29/tests_t13/race_driver.cpp` (added)
- `forge-combo29/REPORT_t13.md` (added)

No file under `forge-combo29/src` or `forge-combo29/include` was edited.

## Races before

Distinct pairs of source lines reported by ThreadSanitizer on the unmodified engine: **none**.

| Group | File:line | Why |
| --- | --- | --- |
| A | (no report) | Shared hash table. Probes and stores are locked; see the torn-entry section. |
| B | (no report) | Histories, counters, stop flag, node counts, and best-move data did not race. |
| C | (no report) | Startup, options, output, and thread start/stop did not race in this driver. |

## Races after

No engine edit. The driver was run again under ThreadSanitizer. Distinct reports: **none**. Nothing remains to explain as a surviving race.

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

## What I could not verify

- Concurrent first entry into `attacks::init` (`src/bitboard.cpp`). The flag is a plain `static bool` set before the tables are filled. This driver builds every root `Board` on the calling thread before helpers start, and copies do not call `init`, so ThreadSanitizer never entered that window.
- A non-portable build (`FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`). Sanitizer and release runs used the portable x86-64-v3 flags.
- Multi-thread best-move stability. Lazy SMP is allowed to return different legal moves; only the single-thread rule 7 node counts are pinned.
- Any bench-time cost of a combined-key checksum. It was not added.
