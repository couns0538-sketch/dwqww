# t18: UCI reader fuzz

The UCI loop survived every hand-written case and all 200000 generated lines. No crash, no hang over 5 seconds, and no AddressSanitizer or UndefinedBehaviorSanitizer report. No search or parsing behaviour was changed.

## What changed

Two edits to `src/uci.cpp`. The loop body (command parsing, search, book, options) was not rewritten.

The first edit (`c90c9cb2`) renamed `int main()` to `forge::uci_loop(std::istream&)` and changed `std::getline(std::cin, line)` to `std::getline(in, line)`. A new `main` called `forge::uci_loop(std::cin)`. That made the reader callable from the test, and a normal run still read stdin, but it was the wrong shape for this lock. `README.md` says every engine change is a default-0 switch with the lock code under `#else`. That edit had no switch. The default build no longer contained the lock's `main`. `windows_build/SOURCE_INPUTS.sha256` still records the lock file:

```
13c7c87a377ec30616f9a733bc5d74072c697c6e48db9eb39d751409f3cc0f97  src/uci.cpp
```

The edited file does not hash to that. The manifest was not rewritten. This branch is not a new lock.

The second edit (`d1d10b3e`) puts the test entry behind `FORGE_UCI_TEST_LOOP`, which defaults to 0. With the switch off, the compiled function is still `int main()` and the read is still `std::getline(std::cin, line)`. With the switch on, the same body is `forge::uci_loop(std::istream&)` and the read is `std::getline(in, line)`. The fuzz compile adds `-DFORGE_UCI_TEST_LOOP=1 -DFORGE_UCI_NO_MAIN`, so the test supplies `main` and the engine does not. The release CMake build does not define the switch. Output stays on `std::cout` in both builds.

`include/forge/uci.hpp` only declares `uci_loop`. The default build does not include it. `tests_t18/uci_fuzz.cpp` is the driver. Engine source touched stays under 300 lines. No existing check was weakened or deleted.

The first copy of this report also described a sanitizer link that compiled only `uci_fuzz.cpp` and reused objects already in `/tmp/t18obj`. A clean tree cannot rebuild from that command. The command later in this file compiles `bitboard.cpp`, `board.cpp`, `book.cpp`, `eval.cpp`, `eval_params.cpp`, `nnue.cpp`, `search.cpp`, `uci.cpp`, and `uci_fuzz.cpp`, then links them. That command was run.

## What was found

The engine reader did not crash, hang past 5 seconds, or trip AddressSanitizer or UndefinedBehaviorSanitizer. Part A was 193 hand-written lines. Part B was 200000 lines from SplitMix64 with seed `361192554478` (`0x5418C0FFEE`). Search and parsing behaviour were left as they are.

Two failures happened in the driver, while it was building a line, before that line was sent to the engine. Two known engine defects were seen or left alone and were not patched on this branch. They already have fixes on other branches.

## What was wrong

### 1. The long move list was not a legal game

Part A has to send one `position startpos moves` line with 2000 moves and then one illegal token. The first generator repeated this six-move lap:

`e2e4 e7e5 e1e2 e8e7 e2e1 e7e8`

The first four plies are legal. White's pawn goes to e4, Black's pawn goes to e5, the white king steps to e2, the black king steps to e7. The next two plies put the kings back. On the second lap the next token is `e2e4` again. The e2-pawn is already on e4, so e2 is empty. `Board::parse_uci` rejects it.

The driver checks each token on its own board before it appends the token. At ply 6 it printed `legal-move cycle broke` with that move and the FEN, and exited. The engine was not the program that failed. The line never reached `uci_loop`.

The line now repeats a four-move knight shuttle that returns to the start position:

`g1f3 g8f6 f3g1 f6g8`

After four plies both knights are home, so the same four tokens stay legal for all 2000 plies (500 laps). The line then appends `not-a-move`. The engine's `apply_position` rejects that token, prints `info string illegal move not-a-move`, and leaves the board where the last legal move put it. That path returned.

### 2. The cycle index walked off a 4-element array

After the knight shuttle replaced the pawn lap, the table was:

```cpp
const char* cycle[] = {"g1f3", "g8f6", "f3g1", "f6g8"};
```

That array has 4 entries, indices 0..3. The loop still indexed it with `i % 6`, left over from the six-move lap. At `i == 4`, `4 % 6` is 4. `cycle[4]` is one past the end.

The driver is compiled with `-fsanitize=undefined`. UndefinedBehaviorSanitizer reported an index 4 out of bounds on that array in `tests_t18/uci_fuzz.cpp`. This was the test reading its own table. It was not an engine read.

The index is now `i % cycle_len` with `cycle_len` equal to 4. At `i == 4` the index is 0, which is `g1f3`, in range, and legal from the start position.

### 3. The first engine edit replaced the lock's `main` in every build

`c90c9cb2` compiled `forge::uci_loop` into the default binary. `main` became a one-line wrapper. A GUI still got the same commands and the same node counts, but the lock rule is that the old code stays on the `#else` side of a switch that defaults to 0. There was no switch, so turning fuzzing off was impossible: the new entry point was the only entry point.

That is also why `sha256sum -c windows_build/SOURCE_INPUTS.sha256` cannot pass for `src/uci.cpp` on this branch. The hash above is the lock file. Adding the `if`s changes the file bytes even though the default compile is `main` reading `std::cin` again. The manifest stays the lock record.

`d1d10b3e` is the correction. Default compile:

```cpp
int main() {
    ...
    while (std::getline(std::cin, line)) {
```

Test compile (`-DFORGE_UCI_TEST_LOOP=1`):

```cpp
int uci_loop(std::istream& in) {
    ...
    while (std::getline(in, line)) {
```

The release binary was rebuilt with the switch unset. `bench 11` is 312866, `bench 13` is 862329, `go perft 5` is 4865609.

### 4. A clock that does not fit in `int` becomes 0

Part A sends `go wtime 3000000000`. `3000000000` is above `INT_MAX` (`2147483647`). In `parse_limits`, `read_int` does `std::from_chars` into an `int`. The value does not fit, `from_chars` sets an error, and `read_int` returns 0. The `wtime` arm then does `std::max(0, 0)` and, when White is to move, stores `limits.time_ms = 0`.

The command did not crash and did not hang. The wrong part is the value: a clock the token can spell is stored as no time. Parsing those clocks in 64 bits is the change on `grok47/t3-clock-parse`. It was not brought onto this branch. Search behaviour here stays the lock's behaviour.

### 5. Losing captures still go into a 64-slot array

`MovePicker` keeps captures that fail the static-exchange test in `bad_captures_`, a `std::array<Move, 64>`. The write is `bad_captures_[bad_count_++]` with no test that `bad_count_` is still below 64. `FORGE_SDK_BADCAP_PREFIX` defaults to 0 on this lock, so that array is the live path. More than 64 losing captures in one node writes past the array.

This fuzz did not search a position that produces that many losing captures, so the run did not hit the write. The repair is on `grok47/t1-capture-overflow` and was not ported. Nothing in `search.cpp` was edited here.

## Driver limits

Part A is fed unchanged. Part B rewrites generated lines only:

- A generated `go` that is not `perft` is capped with `nodes 200`. If the line ends on a keyword that would swallow the next token (`depth`, `nodes`, `movetime`, `wtime`, `btime`, `winc`, `binc`, `movestogo`, `mate`), the driver inserts `0` before `nodes 200`.
- Generated `go perft` with a depth outside 0..2 is replaced by `go perft 1`.
- Generated `bench` whose depth would run deeper than 2, or that does not parse, is replaced by `bench 1`. `bench -3` and `bench 2` are kept, because the engine clamps the negative value to depth 1.

Generated option values for `Hash` stay in `{1, 16, 0, -1, non-numeric}` and `Threads` stay in `{1, 2, 0, -5, non-numeric}`, so the run does not allocate a 2048 MB table or 256 workers. A line whose first token is `quit` is not generated; `quit` is the last command of each session.

Seed `361192554478` (`0x5418C0FFEE`). Part B lines: 200000. Generator: SplitMix64 in the test, not a system random source.

## Files

- `forge-combo29/include/forge/uci.hpp` (new)
- `forge-combo29/src/uci.cpp` (default-off `FORGE_UCI_TEST_LOOP`; lock `main` stays on the `#else` side)
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

Same three counts after `FORGE_UCI_TEST_LOOP` was made default-off (the release binary does not define the switch):

```
cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
[ 11%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 22%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 155 nps 2018490
info string bench depth 13 nodes 862329 time 413 nps 2087963
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

First sanitizer link. Same macros as the release CMake (`FORGE_PORTABLE` / `x86-64-v3`). This command recompiled only the test and linked engine objects already sitting in `/tmp/t18obj`. It is not enough to rebuild from a clean tree. The complete compile is in the next section. Compiler diagnostics: none. Exit status 0.

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

Complete sanitizer build from this tree, after `FORGE_UCI_TEST_LOOP` was defaulted to 0. Every engine translation unit is compiled here. `uci.cpp` is the only one built with `-DFORGE_UCI_TEST_LOOP=1 -DFORGE_UCI_NO_MAIN`. The other units use the same flags as the release portable build. The compiler printed nothing. The shell then printed `LINK_OK` and the part-A result below. Exit status 0.

```
set -e
mkdir -p /tmp/t18obj
FLAGS=(-std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=address,undefined -ffp-contract=off -fno-fast-math -march=x86-64-v3 -I forge-combo29/include -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -Wall -Wextra -Wno-unused-parameter)
c++ "${FLAGS[@]}" -c forge-combo29/src/bitboard.cpp -o /tmp/t18obj/bitboard.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/board.cpp -o /tmp/t18obj/board.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/book.cpp -o /tmp/t18obj/book.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/eval.cpp -o /tmp/t18obj/eval.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/eval_params.cpp -o /tmp/t18obj/eval_params.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/nnue.cpp -o /tmp/t18obj/nnue.o &
c++ "${FLAGS[@]}" -c forge-combo29/src/search.cpp -o /tmp/t18obj/search.o &
c++ "${FLAGS[@]}" -DFORGE_UCI_TEST_LOOP=1 -DFORGE_UCI_NO_MAIN -c forge-combo29/src/uci.cpp -o /tmp/t18obj/uci.o &
c++ "${FLAGS[@]}" -c forge-combo29/tests_t18/uci_fuzz.cpp -o /tmp/t18obj/uci_fuzz.o &
wait
c++ -fsanitize=address,undefined -fno-sanitize-recover=address,undefined -pthread \
  /tmp/t18obj/bitboard.o /tmp/t18obj/board.o /tmp/t18obj/book.o /tmp/t18obj/eval.o \
  /tmp/t18obj/eval_params.o /tmp/t18obj/nnue.o /tmp/t18obj/search.o /tmp/t18obj/uci.o \
  /tmp/t18obj/uci_fuzz.o -o /tmp/uci_fuzz_t18
echo LINK_OK
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1 \
UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1 \
/tmp/uci_fuzz_t18 0
```

```
LINK_OK
seed=361192554478 generated_lines=0
part_a hand_written=193
part_a cases=193 ok time_ms=166
part_b seed=361192554478 lines=0 ok time_ms=28
SANITIZERS clean
```

Full part A and part B on that binary. Exit status 0. No sanitizer report.

```
ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1:print_stacktrace=1 /tmp/uci_fuzz_t18
```

```
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=171
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
part_b seed=361192554478 lines=200000 ok time_ms=216664
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
