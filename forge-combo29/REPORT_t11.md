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

## Follow-up: helpers and a node budget

`Worker::should_stop` returned immediately for every worker except the main one, unless the shared stop flag was already set. That flag is raised only after the main worker has returned, to join the helpers. A node budget therefore stopped the main worker and left the others searching through the unwind. Measured on the merged tree, before this follow-up, worst of 5 tries from the start position:

- 8 threads, `nodes 1`: 108 nodes
- 8 threads, `nodes 10`: 106 nodes
- 2 threads, `nodes 10000`: 10952 nodes
- 4 threads, `nodes 10000`: 10565 nodes

One thread was already exact (the returned count equalled the budget).

Every worker now treats `nodes_specified` or a non-zero `nodes` as its own budget and stops when `total_nodes()` reaches it. Only the main worker sets `stopped_by_nodes_`, so the returned move and score stay the last finished iteration. `bench` builds its own one-thread searcher, and a one-thread node limit still checks the same condition as before.

`tests_t11/thread_node_limit.cpp` covers it. After the change, same compiler flags as `tests_t6` (`g++ -std=c++20 -O2 -Wall -Wextra -Werror -ffp-contract=off -fno-fast-math -march=x86-64-v4` and the lock `-D` switches):

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

Exit status 0. The same program built with `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=address,undefined` and `ASAN_OPTIONS=halt_on_error=1:detect_leaks=1` printed the same pass log (the 10000-node case was 10002) and exited 0. stderr was empty.

`tests_t6/fixed_nodes` recompiled against this `search.cpp` still printed `PASS fixed-node score and move agree` and exited 0.

Release rebuild of `/tmp/forge-t11-release` (`cmake --build`, g++ 13.3.0, lock march) and the rule 7 commands:

```
info string bench depth 11 nodes 312866 time 168 nps 1862297
info string bench depth 13 nodes 862329 time 445 nps 1937817
nodes 4865609
```

The perft move counts were the same twenty numbers as the earlier pin run. Exit status 0.
