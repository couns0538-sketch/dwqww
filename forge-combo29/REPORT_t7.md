# Task 7: load a net from a file

## What was wrong

The lock engine evaluates only the network compiled in from `src/nnue_weights.inc` (int16, scale 4096, hidden 256: `NnueW1[768*256]`, `NnueB1[256]`, `NnueW2[512]`, scalar `NnueB2`). There is no UCI way to replace that table. On the unchanged lock binary, `uci` does not print `NnueFile`, and `tests_t7/nnue_file_test.cpp` does not compile against the lock headers because `forge::nnue::load_file` and `forge::nnue::use_compiled` do not exist.

## The fix

`NnueFile` is a string option, default `<empty>`, shown next to `UseNNUE`. Empty or `<empty>` copies the compiled-in weights back. Any other value is read as a little-endian file: 8 bytes `FORGENET`, uint32 version 1, uint32 hidden size, then int16 `W1`, `B1`, `W2`, and one `B2`. The hidden size must be this build's `HiddenSize` and the file length must be exactly 16 + 2 * (768 * hidden + hidden + 2 * hidden + 1), which is 394770 bytes at hidden 256. The int16 values are turned into floats with the same divisions the lock uses (`value / 4096`). The new table is built first and swapped in only after the whole file checks out, so a bad read cannot tear the live weights. A wrong magic, version, or size, or a file that cannot be opened, prints `info string ERROR NnueFile: ...` and leaves the active net and the hash alone. A successful load or an explicit return to the compiled-in net calls `Searcher::clear()`. That drops the transposition table, the evaluator cache, and the correction histories `corrected_eval()` would otherwise keep adding from the previous network. A rejected file does not clear them. `refresh`, `update`, and `evaluate` still read the same weight table; they gained no new branch.

## Files

Engine source, 139 insertions and 11 deletions:

- `forge-combo29/include/forge/nnue.hpp`
- `forge-combo29/src/nnue.cpp`
- `forge-combo29/src/uci.cpp`

Tests and this report:

- `forge-combo29/tests_t7/forgenet_convert.cpp` writes `nnue_weights.inc` out as a FORGENET file
- `forge-combo29/tests_t7/nnue_file_test.cpp`
- `forge-combo29/tests_t7/nnue_file_uci.txt`
- `forge-combo29/tests_t7/nnue_file_loaded_uci.txt`
- `forge-combo29/REPORT_t7.md`

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

## Review notes not taken

Three later review notes were not applied. A default-off compile switch would remove `NnueFile` from the CMake build this task measures, and `CMakeLists.txt` is outside the files this task may edit. The version-1 layout has no residual-mode field; the lock net is residual, and keeping `residual()` on the compiled value is what makes the converted file match the pins. Builds without `nnue_weights.inc` are not the lock binary. Turning `available()` into a runtime flag would change the search gate the pins depend on.

## What was not verified

- No Elo was measured, and the `nps` lines are not a speed result.
- AddressSanitizer and UndefinedBehaviorSanitizer were run on `nnue_file_test`, not on `bench` or `go perft`.
- The Clang driver `c++` was not used for the pin binary. Its CMake compiler test failed with `cannot find -lstdc++` before any engine source was compiled.
- The Windows lock recipe (clang, ThinLTO, PGO) was not built.
- A file whose hidden size is not the compiled 256 is rejected. This does not load a differently shaped network.
- The lock build does not compile an int8, HalfKA, v2, or v3 net path. `NnueFile` replaces the float table those builds do not include.
