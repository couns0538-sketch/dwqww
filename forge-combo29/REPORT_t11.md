# Task 11: one branch with the four sound fixes

Base: `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Branch: `grok47/t11-integrate`.
`grok47/t5-krk-mate` was not merged.

## What was found

`git rev-parse` of the four tips matched the table. Full hashes:

- `origin/grok47/t1-capture-overflow` = `48644054dd67fd5abf547cd00de1c9943411baf9`
- `origin/grok47/t3-clock-parse` = `5e7fda216e1c03981ede2955f9cf14866f6c992a`
- `origin/grok47/t6-fixed-node-score` = `8c173a85c4a9298e8e5b1ce4b6e7bd8b214155dc`
- `origin/grok47/t8-nnue-file` = `3757595a97ede6978f39e826e33b85354c458ed3`

Each tip's merge-base with the lock is `16833ecc`. t3 also contains `06d211c9`. No tip hash differed from the table, so the table hashes were the ones merged.

Before any merge, the lock source was built and the three reference counts were printed. See "Baseline" below. They were `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609.

## The change

The four reviewed tips are merged, in table order, with `git merge --no-ff`. Nothing else was edited in the engine. The losing-capture buffer is the generator capacity, clock tokens are parsed as 64-bit values and clamped, a node-limited search keeps the move and the score from the last finished iteration, and `NnueFile` loads a net of the same shape from a file.

Engine diff against the lock (`git diff --numstat 16833ecc HEAD -- forge-combo29/src forge-combo29/include`), 213 insertions and 27 deletions, 240 changed lines:

```
8	0	forge-combo29/include/forge/nnue.hpp
8	3	forge-combo29/include/forge/search.hpp
43	0	forge-combo29/include/forge/uci_clock.hpp
107	12	forge-combo29/src/nnue.cpp
15	6	forge-combo29/src/search.cpp
32	6	forge-combo29/src/uci.cpp
```

## Where each block came from

`git merge` did not stop. The three files named in the task have hunks in different places, so the ort strategy joined them. There were no conflict markers. After the four merges, each file was diffed against both tips. The only remaining difference versus one tip is the other tip's hunk, and the single-owner files are identical to their tip.

### `forge-combo29/src/search.cpp`

- From t1 `48644054`: both `bad_captures_` declarations are `std::array<Move, MoveList::Capacity>` (`MoveList::Capacity` is 256), with the comment that a legal position can store more than 64 SEE-losing captures. The `#if FORGE_SDK_BADCAP_PREFIX` arm is unchanged.
- From t6 `8c173a85`: `should_stop` sets `stopped_by_nodes_` when the node budget trips; `search` clears that flag at the start; the abort path keeps a partial root move only when `stopped_by_nodes_` is false.
- Check: `git diff 48644054 HEAD -- forge-combo29/src/search.cpp` is the t6 hunk (11 insertions, 4 deletions). `git diff 8c173a85 HEAD -- forge-combo29/src/search.cpp` is the t1 hunk (4 insertions, 2 deletions).

### `forge-combo29/include/forge/search.hpp`

- From t3 `5e7fda21`: `movetime_ms`, `time_ms`, and `increment_ms` are `std::int64_t`, with the comment that `-1` means the limit was not given.
- From t6 `8c173a85`: `Worker` has `stopped_by_nodes_`, set only for a node-budget stop.
- Check: `git diff 5e7fda21 HEAD` is only the t6 field. `git diff 8c173a85 HEAD` is only the t3 type change.

### `forge-combo29/src/uci.cpp`

- From t3 `5e7fda21`: `#include "forge/uci_clock.hpp"`, and `wtime` / `btime` / `winc` / `binc` / `movetime` go through `parse_clock_ms`. `depth`, `nodes`, `mate`, and `movestogo` still use the 32-bit reader.
- From t8 `3757595a`: when NNUE is available, `uci` prints `option name NnueFile type string default <empty>`, and `setoption name NnueFile` calls `forge::nnue::load_file`, clears the hash on success, and prints `info string`.
- Check: `git diff 5e7fda21 HEAD` is the t8 option block (20 insertions, 1 deletion). `git diff 3757595a HEAD` is the t3 clock parser (12 insertions, 5 deletions).

### Files owned by one branch

- `forge-combo29/include/forge/uci_clock.hpp`: t3 only. `git diff 5e7fda21 HEAD` is empty.
- `forge-combo29/include/forge/nnue.hpp` and `forge-combo29/src/nnue.cpp`: t8 only. `git diff 3757595a HEAD` is empty.
- `tests_t1/`, `tests_t3/`, `tests_t6/`, `tests_t8/`, and `REPORT_t1.md`, `REPORT_t3.md`, `REPORT_t6.md`, `REPORT_t8.md`: copied by the merges. Diff against the owning tip is empty.
- No file from `grok47/t5-krk-mate` is present.

## Commands and output

The first `cmake` probe failed: `/usr/bin/c++` is Clang 18.1.3, it selected GCC 14, and `libstdc++.so` for that install was missing (`cannot find -lstdc++`). `g++-14` and `libstdc++-14-dev` were installed. The builds below are after that. `build/` in the repo is the untracked portable build and is not part of the branch. Other binaries are under `/tmp`.

Host CPU has AVX-512 (`avx512f` and the related flags in `/proc/cpuinfo`). The lock default `-march=x86-64-v4` was used for the g++ engine and for the tests. The Start line's portable Clang build was also rebuilt after the merge and printed the same three node counts.

### Baseline, before the merges

Compiler: Clang 18.1.3. Flags are the Start line (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`).

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Configure and link ended with `[100%] Built target forge`. Program output:

```
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 449 nps 1920554
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

### Release build after the merges (g++ 13.3.0, lock default march)

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t11-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/forge-t11-release -j
```

```
-- The CXX compiler identification is GNU 13.3.0
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-t11-release
[100%] Built target forge
```

Exit status of the build was 0.

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-t11-release/forge
```

```
info string bench depth 11 nodes 312866 time 160 nps 1955412
info string bench depth 13 nodes 862329 time 428 nps 2014787
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

Exit status 0. `bench 11` is 312866. `bench 13` is 862329. `go perft 5` from the start position is 4865609.

The same three commands against the rebuilt portable Clang binary `./build/forge` printed `bench 11` time 163 nodes 312866, `bench 13` time 423 nodes 862329, and the same perft move counts ending in `nodes 4865609`. Exit status 0. The `nps` figures are the engine's own timing for that run.

### tests_t1

Flags from `REPORT_t1.md`: `-std=c++20 -O1 -g -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 -fsanitize=address,undefined -fno-sanitize-recover=address,undefined`, plus `NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`. Sources: `tests_t1/bad_capture_overflow.cpp` and `src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp`. `uci.cpp` is not linked (it has `main`).

```
g++ -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -I forge-combo29/include \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=address,undefined \
  forge-combo29/tests_t1/bad_capture_overflow.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp \
  forge-combo29/src/search.cpp -o /tmp/t11/bad_capture_overflow -pthread
ASAN_OPTIONS=halt_on_error=1:detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/t11/bad_capture_overflow
```

Compiler printed nothing. Exit status of the compiler was 0. Program output:

```
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
```

Exit status 0. No ASan or UBSan diagnostic.

### tests_t3

```
g++ -std=c++20 -Wall -Wextra -Werror -I forge-combo29/include forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/t11/clock_parse_test
/tmp/t11/clock_parse_test
```

```
clock_parse_test passed
```

Exit status 0. Compiler printed nothing.

```
g++ -std=c++20 -Wall -Wextra -Werror -fsanitize=address,undefined -g -I forge-combo29/include forge-combo29/tests_t3/clock_parse_test.cpp -o /tmp/t11/clock_parse_test_asan
/tmp/t11/clock_parse_test_asan
```

```
clock_parse_test passed
```

Exit status 0. Compiler printed nothing. No sanitizer diagnostic.

UCI clocks on `/tmp/forge-t11-release/forge`, with `Threads 1`, `Hash 16`, `OwnBook false`. The engine was a coprocess. Each `go` was read until `bestmove` or until 150 ms, and a still-running search was then sent `stop`. Timestamps below are milliseconds from the start of that read. `uci` also printed `option name NnueFile type string default <empty>` and then `uciok`.

`go nodes 155` (the t6 engine check, same session):

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
```

No depth-3 info line. The move is `d2d4`, the depth-2 move, with score 49.

`go wtime 3000000000 btime 3000000000` was still printing info at 150 ms (last line: depth 17, time 146, 267732 nodes). `stop` was sent. `bestmove d2d4` followed.

`go movetime +80` returned `bestmove d2d4`. The last info line was `time 38`. The `bestmove` line was read at 77 ms.

`go movetime -5` returned `bestmove e2e4`. The engine's last info `time` was 0. The reader timestamp of `bestmove` was 42 ms, which is the bash read loop, not the engine clock.

`go movetime abc` returned `bestmove e2e4` with engine `time` 0.

`go movetime +-80` returned `bestmove e2e4` with engine `time` 1.

`go movetime -+80` returned `bestmove e2e4` with engine `time` 0.

`go movetime 999999999999999999999abc` returned `bestmove e2e4` with engine `time` 0.

`go movetime 9223372036854775808x` returned `bestmove e2e4` with engine `time` 0.

`position startpos moves e2e4` then `go wtime 1 btime 3000000000` was still printing info at 150 ms (last line: depth 17, time 149, 262108 nodes, pv starting `c7c5`). `stop` was sent. `bestmove c7c5` followed.

### tests_t6

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 \
  -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include forge-combo29/tests_t6/fixed_nodes.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp \
  forge-combo29/src/search.cpp -o /tmp/t11/fixed_nodes -pthread
/tmp/t11/fixed_nodes
```

```
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
span depth 2 nodes 54 -> depth 3 nodes 215
nodes 55 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 75 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 95 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 115 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 135 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 155 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 175 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 195 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
span depth 2 nodes 58 -> depth 3 nodes 160
nodes 59 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 71 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 83 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 95 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 107 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 119 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 131 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 143 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 155 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
PASS fixed-node score and move agree
```

Exit status 0.

Same sources with `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined` instead of `-O3`, output `/tmp/t11/fixed_nodes_asan`. The program printed the same pass log, including the same node counts, and exited 0. The sanitizers printed nothing.

### tests_t8

```
g++ -std=c++20 -I forge-combo29/include -I forge-combo29/src -DFORGE_NNUE_HIDDEN=256 forge-combo29/tests_t8/nnue_convert.cpp -o /tmp/t11/nnue_convert
/tmp/t11/nnue_convert /tmp/t8/lock.fnn
```

```
wrote /tmp/t8/lock.fnn hidden 256
```

```
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -fsanitize=address,undefined \
  -I forge-combo29/include \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 \
  forge-combo29/tests_t8/nnue_file_test.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/board.cpp forge-combo29/src/bitboard.cpp \
  -o /tmp/t11/nnue_file_test
/tmp/t11/nnue_file_test /tmp/t8/lock.fnn
```

```
ok load converted net
ok startpos eval matches built-in net
ok kiwipete eval matches built-in net
ok converted file is non-empty
ok load shifted bias
ok shifted bias changes an evaluation
ok empty path restores built-in net
ok restored eval matches built-in net
ok bad magic keeps the current net
ok eval unchanged after bad magic
ok wrong version keeps the current net
ok wrong hidden size keeps the current net
ok truncated file keeps the current net
ok oversized file keeps the current net
ok missing file keeps the current net
ok eval unchanged after rejected files
PASS
```

Exit status 0. The sanitizers printed nothing. stderr of the later UCI run was empty.

UCI on `/tmp/forge-t11-release/forge`, the command from `REPORT_t8.md` (`OwnBook false`, `Threads 1`, `Hash 16`, perft and bench, then `NnueFile` set to the converted file, the rejected files written by the test, then `<empty>`). Exit status 0. The lines that carry the result:

```
option name NnueFile type string default <empty>
nodes 4865609
info string bench depth 11 nodes 312866 time 169 nps 1851278
info string bench depth 13 nodes 862329 time 442 nps 1950970
info string loaded nnue /tmp/t8/lock.fnn
nodes 4865609
info string bench depth 11 nodes 312866 time 151 nps 2071960
info string bench depth 13 nodes 862329 time 416 nps 2072906
info string nnue: bad magic
info string nnue: unsupported version
info string nnue: wrong size
info string nnue: wrong size
info string nnue: cannot open file
info string bench depth 11 nodes 312866 time 157 nps 1992777
```

The perft move list was the same 20 counts as the pin run, both before and after the file load. After the rejected files and `NnueFile <empty>`, `bench 11` was 312866 again.

A path with a space:

```
cp /tmp/t8/lock.fnn "/tmp/t8/lock net.fnn"
printf '%s\n' 'uci' 'setoption name OwnBook value false' 'isready' 'setoption name NnueFile value /tmp/t8/lock net.fnn' 'isready' 'bench 11' 'quit' | /tmp/forge-t11-release/forge
```

```
option name NnueFile type string default <empty>
info string loaded nnue /tmp/t8/lock net.fnn
info string bench depth 11 nodes 312866 time 171 nps 1829625
```

Exit status 0.

### Engine built with `-fsanitize=address,undefined`

```
cmake -S forge-combo29 -B /tmp/forge-t11-asan -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build /tmp/forge-t11-asan -j
```

```
-- The CXX compiler identification is GNU 13.3.0
[100%] Built target forge
```

Build exit status 0. `CMakeLists.txt` still adds `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`.

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-t11-asan/forge
```

```
info string bench depth 11 nodes 312866 time 2030 nps 154121
info string bench depth 13 nodes 862329 time 5032 nps 171369
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

Exit status 0. stderr was empty: no ASan error, no UBSan error, no leak report.

The same sanitized binary, with `ASAN_OPTIONS=halt_on_error=1:detect_leaks=0` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`, was then given `Threads 1`, `Hash 16`, `OwnBook false`:

```
readyok
info depth 1 seldepth 1 score cp 1 nodes 26 nps 13000 hashfull 0 time 2 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 27000 hashfull 0 time 2 pv d2d4 d7d6
bestmove d2d4
info string loaded nnue /tmp/t8/lock.fnn
readyok
info string nnue: bad magic
readyok
bestmove c2c4
```

`go nodes 155` stopped on the depth-2 result (`d2d4`, score 49). `NnueFile` loaded `/tmp/t8/lock.fnn` and rejected the bad-magic file. `go movetime +80` ran until the engine's `time` field reached 73 and then printed `bestmove`. stderr was empty.

The sanitized test binaries are the t1, t3, t6, and t8 runs above. All four exited 0 with no sanitizer diagnostic.

## Not verified

- `go wtime 3000000000` was stopped at 150 ms. It was not left to run for 3000000000 ms.
- Wall-clock stops (movetime or `wtime` cutting a partial root move) were not compared byte for byte with the lock. The node-limit path is what t6 changes; the clock path is still the previous branch of that `if`.
- The Windows ThinLTO/PGO lock executable was not rebuilt. No Elo comparison and no speed comparison. The `nps` numbers above are the engine's printout for these runs.
- `grok47/t5-krk-mate` was not merged, as specified.

## Follow-up on this branch: helpers and a node budget

Branch: `cursor/helper-node-limit-eea5`, stacked on `grok47/t11-integrate`.
Two commits, and nothing else in the engine:

- `d16ab008` Stop helper threads when the node budget is spent.
- `c34ebf0c` Clear worker node counts before a new search starts.

`bench` is still one thread, so the three reference counts stay `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609. The t6 rule (a node limit keeps the move and the score of the last finished iteration) is unchanged for the worker whose result is returned.

### What was wrong: helpers never looked at the budget

`Searcher::search` starts one `std::thread` per helper, then runs worker 0 on the calling thread. Every worker searches the same root. They share one transposition table and one `shared_.stop` flag. The node counter is split: each worker increments its own `local_nodes_`, and `should_stop` copies that into an atomic `nodes_` so the others can add it. `total_nodes()` is this worker's `local_nodes_` plus every other worker's `nodes_`.

On `grok47/t11-integrate`, `Worker::should_stop` was:

```cpp
bool Worker::should_stop() {
    nodes_.store(local_nodes_, std::memory_order_relaxed);
    if (shared_.stop.load(std::memory_order_relaxed)) return true;
    if (!is_main()) return false;
    if (node_limit_specified_ && total_nodes() >= node_limit_) {
        stopped_by_nodes_ = true;
        return true;
    }
    if (hard_limit_ms_ > 0) {
        if (pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0) return false;
        if (elapsed_ms() >= hard_limit_ms_) return true;
    }
    return false;
}
```

`if (!is_main()) return false;` sits above the node-budget test. A helper returns from `should_stop` for exactly one reason: `shared_.stop` is already true. It never reads `node_limit_`. The clock test below that line is also main-only, and that part is left as it was. Time management stays on worker 0.

`shared_.stop` is not raised when the budget is hit. It is raised in `Searcher::search` after worker 0 has returned, so the helpers can be joined:

```cpp
SearchInfo result = workers_.front()->search(board, worker_limits, emit_info, all);
const bool external_stop = shared_.stop.load(std::memory_order_relaxed);
shared_.stop.store(true, std::memory_order_relaxed);
for (auto& helper : helpers) helper.join();
shared_.stop.store(external_stop, std::memory_order_relaxed);
return result;
```

The order that follows from those two pieces:

1. All workers enter the tree. `qsearch` and `search` call `should_stop` on every node when a node limit is set (`node_limit_specified_` is true), and otherwise every 1024 local nodes. Helpers do call it. The call publishes their count and then returns false.
2. Worker 0 is the only one that compares `total_nodes()` with the budget. When the sum reaches it, worker 0 sets `aborted_` and unwinds its own stack.
3. While worker 0 is unwinding, the helpers are still in the tree. Their next `should_stop` still returns false, because `shared_.stop` is still false. They keep generating moves, probing the table, and adding to `local_nodes_`.
4. Worker 0 stores `result.nodes = total_nodes()` at the bottom of `Worker::search` and returns. That number is the count UCI prints. The helpers are still running when it is taken.
5. Only then does `Searcher::search` set `shared_.stop` and join. The nodes the helpers visit between the snapshot and the join are searched and then thrown away. They are not even in the printed total. The printed overshoot is a lower bound on the work.

So `go nodes N` with `Threads` greater than 1 stopped the main worker and left the others searching until that worker had finished leaving the tree. A budget of one node still let seven helpers walk a wide root. A budget of 10000 still let them add the whole unwind.

Measured on the merged tree, before `d16ab008`, worst of 5 tries. Fresh `Searcher` each try, hash 16, depth cap 16. Start position `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`:

- 1 thread, budget 1, 50, 200, 1000: the returned count equalled the budget. The main-only check was already exact.
- 8 threads, budget 1: 108 nodes.
- 8 threads, budget 10: 106 nodes.
- 2 threads, budget 10000: 10952 nodes.
- 4 threads, budget 10000: 10565 nodes.

108 for a budget of 1 is the helpers' work during the short time worker 0 takes to notice the sum, unwind, and return. The two larger budgets overshoot by 952 and 565, which is the same window on a deeper unwind. One thread has no helper, so it never had this hole.

### What changed for that hole

`d16ab008` moves the budget test above the helper return. Every worker now stops when the shared count reaches the budget. Only worker 0 sets `stopped_by_nodes_`:

```cpp
bool Worker::should_stop() {
    nodes_.store(local_nodes_, std::memory_order_relaxed);
    if (shared_.stop.load(std::memory_order_relaxed)) return true;
    if (node_limit_specified_ && total_nodes() >= node_limit_) {
        if (is_main()) stopped_by_nodes_ = true;
        return true;
    }
    if (!is_main()) return false;
    // clock test, unchanged, still main-only
}
```

`stopped_by_nodes_` has to stay a main-only flag. The abort path in worker 0's iterative deepening uses it. A clock stop or an external `stop` may keep a root move that already raised alpha in the unfinished iteration. A node-budget stop must not: `go nodes` has to report the move and the score of one finished iteration. That is the t6 fix. Helpers do not return a `SearchInfo` to UCI, so a helper that hit the budget must stop searching and must not write that flag. Worker 0 still writes it, and its abort path is the same `if (!stopped_by_nodes_ && ss->pv_length > 0 && ...)` block t6 added.

A few nodes can still land past the budget. The check and the increment are not one atomic step: a worker can pass the check at `total == limit - 1` and then be one of several threads that increment. The test allows that slack (16 on a one-node 8-thread search, 32 on a 10000-node 4-thread search). It does not allow the old hundreds.

`tests_t11/thread_node_limit.cpp` after `d16ab008`, compiled as `tests_t6` is (`g++ -std=c++20 -O2 -Wall -Wextra -Werror -ffp-contract=off -fno-fast-math -march=x86-64-v4` and the lock `-D` switches):

```
threads 1 budget 1 nodes 1
ok one thread stops on the exact count
threads 1 budget 50 nodes 50
ok one thread stops on the exact count
threads 1 budget 200 nodes 200
ok one thread stops on the exact count
threads 1 budget 1000 nodes 1000
ok one thread stops on the exact count
threads 1 budget 1 nodes 1
ok one thread stops on the exact count
threads 1 budget 50 nodes 50
ok one thread stops on the exact count
threads 1 budget 200 nodes 200
ok one thread stops on the exact count
threads 1 budget 1000 nodes 1000
ok one thread stops on the exact count
threads 8 budget 1 worst 1
ok eight threads stop a one-node budget
threads 4 budget 10000 worst 10003
ok four threads stay near a large budget
threads 8 budget 10 rook worst 11
ok eight threads stop a ten-node budget
PASS thread node limit
```

Exit status 0. The same program with `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=address,undefined` and `ASAN_OPTIONS=halt_on_error=1:detect_leaks=1` printed the same pass log (the 10000-node case was 10002) and exited 0. stderr was empty.

`tests_t6/fixed_nodes` recompiled against this `search.cpp` still printed `PASS fixed-node score and move agree` and exited 0.

Release rebuild of `/tmp/forge-t11-release` (`cmake --build`, g++ 13.3.0, lock march) and the rule 7 commands:

```
info string bench depth 11 nodes 312866 time 168 nps 1862297
info string bench depth 13 nodes 862329 time 445 nps 1937817
nodes 4865609
```

The perft move counts were the same twenty numbers as the earlier pin run. Exit status 0.

### What was wrong after that: the next search could see the previous count

Making every worker enforce the budget opened a second hole. It was reported on the pull request for this branch. The counters the new check reads are not zero when `Searcher::search` is entered a second time.

Each worker clears itself at the top of its own `Worker::search`:

```cpp
local_nodes_ = 0;
nodes_.store(0, std::memory_order_relaxed);
```

and publishes the final count at the bottom:

```cpp
nodes_.store(local_nodes_, std::memory_order_relaxed);
result.nodes = total_nodes();
```

`Searcher` keeps the same `Worker` objects for the life of the process. UCI does too: one `Searcher`, many `go` commands. After a search, every `nodes_` atomic still holds that worker's final count. The next search clears a worker only when that worker's thread has entered `Worker::search` and executed the two lines above.

`Searcher::search` starts the helper threads first and only then calls worker 0. A helper that gets into the tree quickly calls `should_stop`, and `total_nodes()` adds `worker->nodes()` for every worker that is not itself. A worker that has been started but has not reached its own `nodes_.store(0)` still exposes the previous search. The new check treats that leftover as nodes already spent.

Concrete shape. Eight threads, first search budget 20000, second search budget 500, same `Searcher`.

- Search 1 ends with about 20000 published across the eight atomics. Several thousand can sit in one worker.
- Search 2 launches the seven helpers, then starts worker 0.
- Helper A runs the two clearing lines, builds the root, and reaches `should_stop`.
- Helper B's thread is not inside `Worker::search` yet. B's atomic still says, for example, 4000.
- A's `total_nodes()` is at least 4000. The budget is 500, so A sets `aborted_` and leaves the tree. It contributes nothing to the new search.
- Worker 0 can do the same if it samples the budget before the late workers have stored 0. It then unwinds immediately, `stopped_by_nodes_` is true, and the returned search is the last finished iteration of a search that barely started. The printed node count can sit under the requested budget, because the search stopped on a sum that belonged to the previous `go`. If a late atomic is still old at the moment `result.nodes` is stored, the printed count can also sit far above the new budget, because the old thousands are added in.

The window is the gap between "thread has been created" and "that worker has executed `nodes_.store(0)`". `should_stop` used to sit behind `if (!is_main()) return false`, so a helper never acted on a stale sum. After `d16ab008` it does.

On this host the window was hard to hit. A probe before the reset, 8 threads, one warm search of 30000 nodes (returned 30005) and then 30 searches of 500, stayed on the new budget every time: 500, 501, 502, or 503. The clear is the first thing `Worker::search` does, and the budget check happens only after root move generation, so the other threads had usually stored 0 before anyone sampled them. That run does not show the early abort. It also does not close the hole. A worker that is slow to be scheduled, which is the normal case once the machine is busy or `Threads` is high, still publishes the previous search into the new budget. The check has no way to tell those nodes from new ones.

### What changed for the stale count

`c34ebf0c` clears every worker on the launching thread, before any helper is started:

```cpp
void Worker::reset_node_count() {
    local_nodes_ = 0;
    nodes_.store(0, std::memory_order_relaxed);
}
```

```cpp
// A helper can read the budget before another worker enters search() and
// clears the count it published last time. Zero every counter first.
for (auto& worker : workers_) worker->reset_node_count();
std::vector<std::thread> helpers;
for (std::size_t i = 1; i < workers_.size(); ++i) {
    helpers.emplace_back(...);
}
```

The stores happen before `std::thread`'s constructor. Thread start happens after those stores, so the first `should_stop` in the new search adds zeros, not the previous search. `local_nodes_` is written here only while no search thread is running. After the launch, each worker writes only its own `local_nodes_`. The per-worker clear at the top of `Worker::search` is still there; it is no longer the first time the atomic becomes zero.

`tests_t11/thread_node_limit.cpp` now keeps one 8-thread searcher. It searches a budget of 20000, then the same object ten times with a budget of 500. After `c34ebf0c`:

```
reused warm nodes 20005
ok warm search reaches its budget
reused rep 0 nodes 502
reused rep 1 nodes 500
reused rep 2 nodes 500
reused rep 3 nodes 500
reused rep 4 nodes 500
reused rep 5 nodes 503
reused rep 6 nodes 502
reused rep 7 nodes 503
reused rep 8 nodes 500
reused rep 9 nodes 502
PASS thread node limit
```

Exit status 0. Each reused search is inside 500..532, which is the same slack as the other multi-thread cases. The one-thread budgets in that run were still exact (1, 50, 200, 1000 on both positions). The 8-thread budget of 1 returned a worst of 2. The 4-thread budget of 10000 returned a worst of 10003. The 8-thread rook position, budget 10, returned a worst of 10.

The same source built with `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=address,undefined`, `ASAN_OPTIONS=halt_on_error=1:detect_leaks=1`, and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1` printed `PASS thread node limit` and exited 0. The sanitizers printed nothing. The warm search was 20005 and the ten reused searches were 500, 502, or 503.

After this reset, the release binary and the rule 7 commands printed:

```
info string bench depth 11 nodes 312866 time 189 nps 1655375
info string bench depth 13 nodes 862329 time 504 nps 1710970
nodes 4865609
```

Exit status 0. The perft move counts were the same twenty numbers.

### What this branch does not change

- One thread still stops on the exact count. `bench` builds that one-thread searcher, so the pins are the same search as before.
- The clock test in `should_stop` is still main-only. Helpers still stop on the shared flag when the clock expires, which is the path that already existed.
- A node-budget abort on worker 0 still refuses the partial root move. `tests_t6/fixed_nodes` passed against this `search.cpp`.
- The four merged fixes (capture buffer, clock parser, fixed-node score, `NnueFile`) are untouched. `grok47/t5-krk-mate` is still absent.
