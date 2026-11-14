# Task 7: load a net from a file

Branch `grok47/t7-nnue-file`, base `origin/lock/combo29-20261110` (`16833ecc`). This file is the account of what was wrong, what was measured, and what the branch changes. The command logs are below.

## What was wrong

### The lock cannot load a net

On the lock, the only network is the one compiled into `src/nnue_weights.inc`. That file is int16, scale 4096, hidden 256:

- `NnueW1[768 * 256]` (196608 values)
- `NnueB1[256]`
- `NnueW2[512]` (both perspectives)
- `NnueB2`, one int16, value 127

`nnue.cpp` copies those into a function-local `const` float table the first time `weights()` runs. `refresh`, `update`, and `evaluate` only read that table. The object is const, so a later call cannot replace it. `uci` prints `UseNNUE` and does not print `NnueFile`. Setting an unknown option is ignored. There is no reader for an external file of this shape.

That is why `tests_t7/nnue_file_test.cpp` fails against the lock. Compiled with the lock headers it stops at `forge::nnue::load_file` and `forge::nnue::use_compiled`, which are not members of `forge::nnue`. The compile errors are in the log below. The lock binary's own `uci` transcript also has no `option name NnueFile` line, and its pins are `bench 11` = 312866, `bench 13` = 862329, startpos `go perft 5` = 4865609.

The include also sets `FORGE_NNUE_RESIDUAL 1`. Search adds the network output to the hand-crafted evaluation. A file loader that only swapped weights, and left `residual()` as the compiled flag, evaluates a converted copy of this same net the same way. That is the round-trip the task asked for.

### A bad file must not replace the live net

The first cut of the loader had to refuse a wrong magic, a version other than 1, a hidden size other than the compiled 256, and a length other than the exact body. If it wrote the live table while still reading, a short file could leave a half-updated net. The loader now builds a temporary table and swaps it in only after the header and the body both check out. A failure returns before that swap.

Measured on the start position, the compiled net and the converted file both score 20 centipawns from the side to move. Raising the file's `B2` by 400 moved that score to 37 and moved `bench 11` from 312866 to 322107, so the load was actually reaching the search. After that, each of these left the score at 37 and, for the ones run through UCI, left the changed `bench 11` at 322107:

- magic byte changed (`wrong magic`)
- version byte changed from 1 to 2 (`wrong version`)
- hidden size changed from 256 to 128 (`wrong size`)
- one byte truncated (`wrong size`)
- path that does not exist (`cannot open`)

Setting the option back to `<empty>` restored the compiled score of 20 and the pins 312866, 862329, and 4865609.

### clear_hash() keeps the old net's correction

The first commit cleared the hash on a successful load, the same call `UseNNUE` uses. That is not enough once a search has already run.

`Searcher::clear_hash()` clears the transposition table and calls `Worker::clear_caches()`, which is only `evaluator_.clear()`. It does not touch `correction_history_` or `material_correction_`.

`Worker::corrected_eval()` still does this on every static eval:

```
correction = correction_history_[side][pawn_key]
if MaterialCorrectionWeight > 0:
    correction += material_correction_[side][material_key] * MaterialCorrectionWeight / 100
return raw_eval + correction / CorrectionGrain
```

`update_correction()` fills those tables from `best_score - static_eval` during search. The entries are an adjustment learned for the evaluation that was active then. After a different net is loaded, the new net's raw score is still added to the old adjustment. The same pawn key or material key then carries a correction that belonged to the previous network.

`Worker::clear()` assigns both tables to `{}`. `Searcher::clear()` calls that on every worker and also clears the transposition table. A successful `NnueFile` load, and an explicit return to the compiled-in net, now call `searcher.clear()`. A rejected file does not. `bench` is unaffected either way: it builds its own `Searcher(16)` and calls `clear()` before each position. Remeasured after this change, the unset option and the converted lock net both still give 312866, 862329, and 4865609.

`UseNNUE` still calls only `clear_hash()`. That older option has the same leftover-correction gap. This branch does not change it. The task was the file loader, and the pins for `UseNNUE` were left as they are.

## What changed

`NnueFile` is a string option, default `<empty>`, printed next to `UseNNUE` when a network is compiled in. Empty or `<empty>` copies `NnueW1`, `NnueB1`, `NnueW2`, and `NnueB2` back into the active float table with the same divisions the lock uses (`int16 / 4096`). Any other value is a path, including spaces, read the same way `Book File` reads a path.

The file is little-endian and exact length, 394770 bytes at hidden 256:

- 8 bytes `FORGENET`
- uint32 version, must be 1
- uint32 hidden size, must equal compiled `HiddenSize` (256 in this build)
- int16 `W1[768 * hidden]`, `B1[hidden]`, `W2[2 * hidden]`, `B2[1]`

`refresh`, `update`, and `evaluate` still call `weights()` and have no new branch. The table is no longer a const object, so a successful load can replace the floats. With the option never set, the first fill is the compiled-in net, and the measured node counts match the lock.

Engine diff against the lock: 140 insertions and 11 deletions.

- `forge-combo29/include/forge/nnue.hpp` adds `load_file` and `use_compiled`
- `forge-combo29/src/nnue.cpp` holds the float table, the quantise loop, and the reader
- `forge-combo29/src/uci.cpp` advertises the option and calls `searcher.clear()` only after a successful load or restore

Tests:

- `forge-combo29/tests_t7/forgenet_convert.cpp` writes `nnue_weights.inc` out as that file
- `forge-combo29/tests_t7/nnue_file_test.cpp` checks the converted file, a changed `B2`, and the rejected files
- `forge-combo29/tests_t7/nnue_file_uci.txt` and `nnue_file_loaded_uci.txt` are the UCI transcripts

## What the measurements found

GCC 13.3.0, `-march=x86-64-v4`, `Threads 1`, `Hash 16`, `OwnBook false`. `time` and `nps` move between runs. The node counts are the result. No Elo claim.

- Lock binary, option absent: `bench 11` = 312866, `bench 13` = 862329, perft 5 = 4865609.
- This branch, option unset: the same three counts.
- Converted lock net, including the path `/tmp/forge t7/lock.forgenet`: the same three counts.
- Bad magic while the compiled net was active: `bench 11` stayed 312866.
- `B2` plus 400: start-position network output 20 became 37, and `bench 11` became 322107.
- Bad version after that load: `bench 11` stayed 322107.
- `<empty>` after that: 312866, 862329, and 4865609 again.
- `nnue_file_test` exited 0. The same test under AddressSanitizer and UndefinedBehaviorSanitizer exited 0 with no sanitizer report.

The full command output is in the sections below.

## Commands and output

Build used GCC 13.3.0. `c++` on this machine is Clang 18.1.3 and its first CMake probe failed with `cannot find -lstdc++`, so the pin binary was built with `CXX=g++`. The machine has AVX-512F and BMI2, so the default march `x86-64-v4` was used. Node counts are the measurement. The `time` and `nps` fields move between runs and are not a speed claim.

### Build the task 7 engine

```
CXX=g++ cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t7-build -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-t7-build -j
```

```
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-t7-build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
```

### Unset NnueFile: bench 11, bench 13, perft 5

`Threads 1`, `Hash 16`, `OwnBook false`. `bench` also constructs its own `Searcher(16)`, which is a 16 MB hash.

```
printf '%s\n' 'uci' 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' 'isready' 'bench 11' 'bench 13' 'position startpos' 'go perft 5' 'quit' | /tmp/forge-t7-build/forge
```

### output

```
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
option name NnueFile type string default <empty>
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
readyok
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 422 nps 2043433
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

Results: `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609.

### Converted lock net, rejected files, and restore

`forgenet_convert` wrote `/tmp/forge-t7-lock.forgenet` (394770 bytes). The same bytes were copied to `/tmp/forge t7/lock.forgenet` so the path contains a space. `/tmp/forge-t7-b2.bin` is that file with `B2` increased by 400. The bad files were written by `nnue_file_test`.

```
printf '%s\n' \
  'uci' \
  'setoption name Threads value 1' \
  'setoption name Hash value 16' \
  'setoption name OwnBook value false' \
  'isready' \
  'setoption name NnueFile value /tmp/forge-t7-bad-magic.bin' \
  'bench 11' \
  'setoption name NnueFile value /tmp/forge-t7-b2.bin' \
  'bench 11' \
  'setoption name NnueFile value /tmp/forge-t7-bad-version.bin' \
  'bench 11' \
  'setoption name NnueFile value <empty>' \
  'bench 11' \
  'bench 13' \
  'position startpos' \
  'go perft 5' \
  'setoption name NnueFile value /tmp/forge t7/lock.forgenet' \
  'bench 11' \
  'bench 13' \
  'position startpos' \
  'go perft 5' \
  'quit' | /tmp/forge-t7-build/forge
```

### output

```
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
option name NnueFile type string default <empty>
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
readyok
info string ERROR NnueFile: wrong magic
info string bench depth 11 nodes 312866 time 160 nps 1955412
info string NnueFile loaded /tmp/forge-t7-b2.bin
info string bench depth 11 nodes 322107 time 161 nps 2000664
info string ERROR NnueFile: wrong version
info string bench depth 11 nodes 322107 time 157 nps 2051636
info string NnueFile: compiled-in network
info string bench depth 11 nodes 312866 time 152 nps 2058328
info string bench depth 13 nodes 862329 time 417 nps 2067935
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
info string NnueFile loaded /tmp/forge t7/lock.forgenet
info string bench depth 11 nodes 312866 time 152 nps 2058328
info string bench depth 13 nodes 862329 time 417 nps 2067935
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

After the successful-load path was changed to `Searcher::clear()`, the same binary was built again and remeasured: unset `bench 11` = 312866, `bench 13` = 862329, perft = 4865609; a bad magic stayed at `bench 11` = 312866; the converted file at `/tmp/forge t7/lock.forgenet` repeated 312866, 862329, and 4865609.

A bad magic left the compiled-in net in place (`bench 11` stayed 312866). Loading the touched `B2` changed `bench 11` to 322107. A bad version left that changed net in place (322107 again). `<empty>` restored 312866, 862329, and perft 4865609. Loading the converted lock net, including through a path with a space, produced the same three counts.

### C++ test

```
g++ -std=c++20 -O1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 -I /agent/repos/dwqww/forge-combo29/include -I /agent/repos/dwqww/forge-combo29/src /agent/repos/dwqww/forge-combo29/tests_t7/forgenet_convert.cpp -o /tmp/forgenet_convert
/tmp/forgenet_convert /tmp/forge-t7-lock.forgenet
g++ -std=c++20 -O2 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 -I /agent/repos/dwqww/forge-combo29/include -I /agent/repos/dwqww/forge-combo29/src /agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp /tmp/forge-t7-build/CMakeFiles/forge.dir/src/nnue.cpp.o /tmp/forge-t7-build/CMakeFiles/forge.dir/src/board.cpp.o /tmp/forge-t7-build/CMakeFiles/forge.dir/src/bitboard.cpp.o -o /tmp/nnue_file_test
/tmp/nnue_file_test /tmp/forge-t7-lock.forgenet
```

```
-rw-r--r-- 1 ubuntu ubuntu 394770 Nov 14 05:45 /tmp/forge-t7-lock.forgenet
compiled 20
loaded 20
ok converted net matches compiled eval
changed 37
ok changed b2 changes eval
ok bad magic kept current net (wrong magic)
ok bad version kept current net (wrong version)
ok bad hidden kept current net (wrong size)
ok short file kept current net (wrong size)
ok missing file kept current net (cannot open)
restored 20
ok use_compiled restores eval
all checks passed
```

Exit status 0. Start-position network output was 20 centipawns for both the compiled net and the converted file. Adding 400 to `B2` moved it to 37, and every rejected file left it at 37 until `use_compiled()`.

### AddressSanitizer and UndefinedBehaviorSanitizer

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 -I /agent/repos/dwqww/forge-combo29/include -I /agent/repos/dwqww/forge-combo29/src /agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp /agent/repos/dwqww/forge-combo29/src/nnue.cpp /agent/repos/dwqww/forge-combo29/src/board.cpp /agent/repos/dwqww/forge-combo29/src/bitboard.cpp -o /tmp/nnue_file_test_asan
/tmp/nnue_file_test_asan /tmp/forge-t7-lock.forgenet
```

### output

```
compiled 20
loaded 20
ok converted net matches compiled eval
changed 37
ok changed b2 changes eval
ok bad magic kept current net (wrong magic)
ok bad version kept current net (wrong version)
ok bad hidden kept current net (wrong size)
ok short file kept current net (wrong size)
ok missing file kept current net (cannot open)
restored 20
ok use_compiled restores eval
all checks passed
```

Exit status 0. The sanitizer runtime printed no error.

### The same test against the lock

Compiled from a `git archive` of `origin/lock/combo29-20261110` at `16833ecc`, headers only:

```
g++ -std=c++20 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -I /tmp/lock-tree/forge-combo29/include -c /agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp -o /tmp/nnue_file_test_locksrc.o
```

### output (exit 1)

```
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp: In function ‘int main(int, char**)’:
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:51:23: error: ‘load_file’ is not a member of ‘forge::nnue’
   51 |     if (!forge::nnue::load_file(good_path, error)) return fail("load converted lock net: " + error);
      |                       ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:67:23: error: ‘load_file’ is not a member of ‘forge::nnue’
   67 |     if (!forge::nnue::load_file(changed_path, error)) return fail("load changed net: " + error);
      |                       ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:77:22: error: ‘load_file’ is not a member of ‘forge::nnue’
   77 |     if (forge::nnue::load_file("/tmp/forge-t7-bad-magic.bin", error)) return fail("bad magic was accepted");
      |                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:86:22: error: ‘load_file’ is not a member of ‘forge::nnue’
   86 |     if (forge::nnue::load_file("/tmp/forge-t7-bad-version.bin", error)) return fail("bad version was accepted");
      |                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:96:22: error: ‘load_file’ is not a member of ‘forge::nnue’
   96 |     if (forge::nnue::load_file("/tmp/forge-t7-bad-hidden.bin", error)) return fail("bad hidden was accepted");
      |                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:105:22: error: ‘load_file’ is not a member of ‘forge::nnue’
  105 |     if (forge::nnue::load_file("/tmp/forge-t7-short.bin", error)) return fail("short file was accepted");
      |                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:111:22: error: ‘load_file’ is not a member of ‘forge::nnue’
  111 |     if (forge::nnue::load_file("/tmp/forge-t7-missing.bin", error)) return fail("missing file was accepted");
      |                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t7/nnue_file_test.cpp:115:18: error: ‘use_compiled’ is not a member of ‘forge::nnue’
  115 |     forge::nnue::use_compiled();
      |                  ^~~~~~~~~~~~
```

Linking the test with the lock `nnue.cpp` (compiled to `/tmp/lock-nnue.o`) also fails:

### output (exit 1)

```
/usr/bin/ld: /tmp/cciNiZO9.o: in function `main':
nnue_file_test.cpp:(.text+0x4f0): undefined reference to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)'
/usr/bin/ld: nnue_file_test.cpp:(.text+0x7eb): undefined reference to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)'
/usr/bin/ld: nnue_file_test.cpp:(.text+0xa06): undefined reference to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)'
/usr/bin/ld: nnue_file_test.cpp:(.text+0xc87): undefined reference to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)'
/usr/bin/ld: nnue_file_test.cpp:(.text+0xf1f): undefined reference to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)'
/usr/bin/ld: /tmp/cciNiZO9.o:nnue_file_test.cpp:(.text+0x1198): more undefined references to `forge::nnue::load_file(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >&)' follow
/usr/bin/ld: /tmp/cciNiZO9.o: in function `main':
nnue_file_test.cpp:(.text+0x1447): undefined reference to `forge::nnue::use_compiled()'
collect2: error: ld returned 1 exit status
```

### Unchanged lock binary, same bench commands

```
CXX=g++ cmake -S /tmp/lock-tree/forge-combo29 -B /tmp/forge-lock-build -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-lock-build -j
printf '%s\n' 'uci' 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' 'isready' 'bench 11' 'bench 13' 'position startpos' 'go perft 5' 'quit' | /tmp/forge-lock-build/forge
```

The lock `uci` list has `UseNNUE` and no `NnueFile`. Node counts match the pins:

### output

```
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
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
readyok
info string bench depth 11 nodes 312866 time 239 nps 1309062
info string bench depth 13 nodes 862329 time 991 nps 870160
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

## Review notes that were checked and not applied

A review asked for three further changes. They were checked against the lock source and the required file layout. They were not applied.

A default-off compile switch, with the lock code under `#else`, is what `README.md` asks of engine edits. This task's build line is `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release` with no extra `-D`. A switch that defaults to 0 would leave `NnueFile` out of that binary, so the converted-net bench could not be run on the build the task names. `CMakeLists.txt` is also outside the files this task may edit, so the specified command cannot turn a default-off switch on.

The version-1 layout given for the file is magic, version, hidden size, then the four int16 arrays. There is no residual-mode field. The lock include sets `FORGE_NNUE_RESIDUAL` to 1, and `residual()` still returns that. A converted copy of the lock net is therefore still added to the hand-crafted evaluation, which is why its bench matches. Rejecting every file because the mode is not stored would reject that converted lock net. Adding a mode byte would make a legal version-1 file the wrong length.

`available()` is true only when `nnue_weights.inc` was compiled in. The lock ships that file. Search skips the network when `available()` is false. A build that omits the include is not the lock binary. Making `available()` a runtime flag, so a file could turn the network on in that build, would change the gate the pin searches go through.

## What was not verified

- No Elo was measured, and the `nps` lines are not a speed result.
- AddressSanitizer and UndefinedBehaviorSanitizer were run on `nnue_file_test`, not on `bench` or `go perft`.
- The Clang driver `c++` was not used for the pin binary. Its CMake compiler test failed with `cannot find -lstdc++` before any engine source was compiled.
- The Windows lock recipe (clang, ThinLTO, PGO) was not built.
- A file whose hidden size is not the compiled 256 is rejected. This does not load a differently shaped network.
- The lock build does not compile an int8, HalfKA, v2, or v3 net path. `NnueFile` replaces the float table those builds do not include.
