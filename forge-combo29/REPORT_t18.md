# t18: UCI reader fuzz

The UCI loop survived every hand-written case and all 200000 generated lines. No crash, no hang over 5 seconds, and no AddressSanitizer or UndefinedBehaviorSanitizer report. No search or parsing behaviour was changed.

## What changed

`main` was split so the existing command loop is `forge::uci_loop(std::istream&)`. The engine still calls it with `std::cin` and still writes to `std::cout`. A test can pass another stream and run the same reader. The fuzz found nothing to fix, so the loop body is the lock's loop.

## What was found

No engine defect. The first two driver attempts failed in the test, before any search of the engine's behaviour was in doubt:

- The 2000-move line used pawn pushes that are not legal on the second lap (`e2e4` after the pawns had already moved). The driver now repeats `g1f3 g8f6 f3g1 f6g8`, which stays legal.
- That cycle array has 4 entries and the index used `% 6`. UndefinedBehaviorSanitizer reported `uci_fuzz.cpp` index 4 out of bounds. The index is now `% 4`.

`go wtime 3000000000` (above 2^31) was fed in part A. It did not crash or hang. This branch still parses clocks with `std::from_chars` into `int`, so an out-of-range token becomes 0. That parse is the known clock fix on `grok47/t3-clock-parse` and was not ported. The losing-capture list `bad_captures_[64]` was not searched; that overflow is the known fix on `grok47/t1-capture-overflow`.

## Driver limits

Part A is fed unchanged. Part B rewrites generated lines only:

- A generated `go` that is not `perft` is capped with `nodes 200`. If the line ends on a keyword that would swallow the next token (`depth`, `nodes`, `movetime`, `wtime`, `btime`, `winc`, `binc`, `movestogo`, `mate`), the driver inserts `0` before `nodes 200`.
- Generated `go perft` with a depth outside 0..2 is replaced by `go perft 1`.
- Generated `bench` whose depth would run deeper than 2, or that does not parse, is replaced by `bench 1`. `bench -3` and `bench 2` are kept, because the engine clamps the negative value to depth 1.

Generated option values for `Hash` stay in `{1, 16, 0, -1, non-numeric}` and `Threads` stay in `{1, 2, 0, -5, non-numeric}`, so the run does not allocate a 2048 MB table or 256 workers. A line whose first token is `quit` is not generated; `quit` is the last command of each session.

Seed `361192554478` (`0x5418C0FFEE`). Part B lines: 200000. Generator: SplitMix64 in the test, not a system random source.

## Files

- `forge-combo29/include/forge/uci.hpp` (new)
- `forge-combo29/src/uci.cpp` (loop entry point only; +13 / -2)
- `forge-combo29/tests_t18/uci_fuzz.cpp` (new)
- `forge-combo29/REPORT_t18.md` (this file)

Engine source touched is well under 300 lines. No existing check was weakened or deleted.

## Commands and output

Reference numbers before the edit (same three node counts):

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 179 nps 1747854
info string bench depth 13 nodes 862329 time 509 nps 1694163
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

Reference numbers after the edit:

```
cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
[ 11%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 22%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 155 nps 2018490
info string bench depth 13 nodes 862329 time 411 nps 2098124
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

`bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609.

Sanitizer build. Same macros as the release CMake (`FORGE_PORTABLE` / `x86-64-v3`). Compiler diagnostics: none. Exit status 0. The objects below are what the 200000-line binary was linked from; `uci_fuzz.o` was rebuilt after the `% 4` fix and the engine objects were not rebuilt after that because `src/` did not change again.

```
c++ -std=c++20 -O1 -g -fno-omit-frame-pointer \
  -fsanitize=address,undefined -fno-sanitize-recover=address,undefined \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -I forge-combo29/include \
  -DFORGE_UCI_NO_MAIN -DNDEBUG \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -Wall -Wextra -Wno-unused-parameter \
  -c forge-combo29/tests_t18/uci_fuzz.cpp -o /tmp/t18obj/uci_fuzz.o && \
c++ -fsanitize=address,undefined -fno-sanitize-recover=address,undefined -pthread \
  /tmp/t18obj/bitboard.o /tmp/t18obj/board.o /tmp/t18obj/book.o /tmp/t18obj/eval.o \
  /tmp/t18obj/eval_params.o /tmp/t18obj/nnue.o /tmp/t18obj/search.o /tmp/t18obj/uci.o \
  /tmp/t18obj/uci_fuzz.o -o /tmp/uci_fuzz_t18
```

Part A only (0 generated lines), after the driver fixes. Exit status 0.

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1 /tmp/uci_fuzz_t18 0
```

```
seed=361192554478 generated_lines=0
part_a hand_written=193
part_a cases=193 ok time_ms=188
part_b seed=361192554478 lines=0 ok time_ms=30
SANITIZERS clean
```

Pilot of 10000 generated lines on the same binary. Exit status 0.

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1 /tmp/uci_fuzz_t18 10000
```

```
seed=361192554478 generated_lines=10000
part_a hand_written=193
part_a cases=193 ok time_ms=171
part_b seed=361192554478 lines=10000 ok time_ms=11010
SANITIZERS clean
```

Full part A (193 lines) and part B (200000 lines). Exit status 0. Leak detection was on. No sanitizer report.

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1 /tmp/uci_fuzz_t18
```

```
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=172
part_b 10000
part_b 20000
part_b 30000
part_b 40000
part_b 50000
part_b 60000
part_b 70000
part_b 80000
part_b 90000
part_b 100000
part_b 110000
part_b 120000
part_b 130000
part_b 140000
part_b 150000
part_b 160000
part_b 170000
part_b 180000
part_b 190000
part_b seed=361192554478 lines=200000 ok time_ms=222245
SANITIZERS clean
```

Part A covers the required shapes: illegal and malformed moves, 2000 legal moves plus a final illegal token, 2000 copies of an illegal move, `position` with no argument, `position fen` with too few fields, `go` with no arguments, `depth 0`, `depth -5`, `depth 999999`, `nodes 0`, `movetime 0`, `movetime -1`, `wtime 1 btime 1`, `wtime 0`, `movestogo 0`, `mate 0`, unknown words, keywords with no number, `setoption` with no name, no value, and a 100000-character value, `stop` and `ponderhit` before any search, `ucinewgame` immediately after `go depth 999999`, empty lines, tabs, a 1048576-byte line, and bytes 128..255.

## Not verified

- ThreadSanitizer. AddressSanitizer and UndefinedBehaviorSanitizer were clean; concurrent races were not instrumented.
- `bench` with no depth (the engine default is 13) and `bench` depths above 2, under the sanitizer. Those runs were not started because a depth-13 bench can pass the 5 second per-command budget once ASan slows the search. Release `bench 11` and `bench 13` were run, without sanitizers.
- `go perft` above depth 2 under the sanitizer. Release `go perft 5` was run, without sanitizers.
- `Hash` values that resize the table to 2048 MB, and `Threads` above 2.
- The known position that overflows `bad_captures_` (fixed on `grok47/t1-capture-overflow`).
- A 64-bit clock parse. `go wtime 3000000000` did not crash; an out-of-range token still becomes 0 on this branch.
- Whether the printed `bestmove` matches a reference engine. The test checks that the process returns, not that the move is the same.
