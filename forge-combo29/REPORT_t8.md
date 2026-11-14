# Task 8: load an NNUE net from a file

## What was wrong

The lock (`origin/lock/combo29-20261110`, commit `16833ecc`) can evaluate only the network compiled into the binary. There is no UCI option, no command, and no function that reads a net from a file.

The weights live in `src/nnue.cpp`, in `weights()`. On the lock that function returns a function-local `static const Weights` filled once by a lambda. `const` is the defect that blocks a loader: after the first call, the object cannot be replaced. `refresh`, `update`, and `evaluate` all read that same object. A file load that built a second `Weights` would have nowhere to install it, and a search already running would keep using the compiled-in numbers.

The source of those numbers is `src/nnue_weights.inc`, included only by `nnue.cpp`. The include sets `FORGE_NNUE_RESIDUAL` to 1 and defines four `static const` int16 objects, scale 4096:

- `NnueW1[196608]`, which is `768 * 256` (input features times hidden size).
- `NnueB1[256]`.
- `NnueW2[512]`, which is `2 * 256` (side to move and opponent).
- `NnueB2`, a single `int16_t` whose value is 127. It is not an array.

The old lambda converted them with `static_cast<float>(q) / 4096`. `W1` and `B1` divide by `WeightScale`. `W2` and `B2` divide by `OutputScale`. Both constants are 4096. Any loader that used a different scale, a different order, or a 256-wide `B2` would change evaluation and then change the bench node counts.

UCI already had `UseNNUE`, a check that only turns evaluation on or off. It did not take a path. `setoption` already knew how to read a path with spaces, but only for `Book File`: the first token is taken with `operator>>`, then `getline` takes the rest of the line. A net path had no branch.

The accumulator is `std::array<float, HiddenSize>` with `HiddenSize` fixed at compile time. The lock build passes `-DFORGE_NNUE_HIDDEN=256`. A file that declares another hidden size cannot be installed in this binary. The feature columns, the bias, and the output weights would have the wrong length, and the incremental update loops index by the compiled `HiddenSize`.

## What I found

I read the lock `weights()` lambda, the four objects at the end of `nnue_weights.inc` (the `NnueB2` definition is line 8240), and the `setoption` path in `src/uci.cpp`.

`NnueB2` being one integer is the easy mistake. The task says the file holds the four arrays in order. The fourth value in this net is one little-endian int16, not 256 of them. The converter writes `write_i16(out, NnueB2)` once. The reader checks the file length before it allocates, so a 256-wide `B2` is rejected as `nnue: wrong size` and the current net stays.

The exact file length for this build is 394770 bytes:

`16 + 2 * (768 * 256 + 256 + 512 + 1) = 16 + 2 * 197377 = 394770`.

The 16-byte header is 8 bytes of magic `FORGENET` (no trailing NUL), a little-endian uint32 version, and a little-endian uint32 hidden size. Version must be 1. Hidden size must equal the compiled `HiddenSize`.

`setoption` calls `stop_search()` before it looks at the option name. `stop_search()` sets the stop flag, calls `searcher.stop()`, and joins the worker thread. The load therefore does not replace weights while a search thread is inside `evaluate`. A successful load then calls `searcher.clear_hash()`, because transposition entries were stored under the previous net. A failed load does not clear the hash and does not assign the static weights. The parsed numbers go into a temporary `Weights`, and that temporary is moved onto the live object only after magic, version, hidden size, and length have all been checked.

The first copy of `load_file` on this branch treated the stream as failed when `!input` was true or `gcount` did not equal the length. On this machine (g++ 13.3, libstdc++) that check did not reject the converted lock file: the sanitized test printed `ok load converted net` and both bench counts stayed on the lock numbers. I did not observe a false rejection here. I still removed `!input`. `istream::read` of the exact file length is allowed to set `eofbit` when the last byte is the end of the file. `operator!` is true when `failbit` is set, and some libraries set `failbit` as well once extraction stops at end of file, even if `gcount()` equals the request. The loader now accepts the buffer only when `gcount()` equals the length from `tellg`. A short read still returns `nnue: cannot open file` and leaves the current net in place.

The first test was weaker than that file format. It compared the evaluation of the start position and of the kiwipete position, so two positions could match while some other weight was wrong. It also restored the compiled-in net before the bad-file cases, so it never showed that a rejected file keeps a *different* net that had already been loaded. Its "oversized" file was one extra byte, which does not exercise the 2 MiB cap. The cap exists so a huge file is reported as `nnue: wrong size` before the loader allocates a buffer for it. The expected net is 394770 bytes, so the cap does not reject a valid file of this shape.

## What changed

`include/forge/nnue.hpp` declares `bool load_file(std::string_view path, std::string& error)`. An empty path or the text `<empty>` restores the compiled-in net and clears `error`. Any other path is a file. On failure `error` is one of `nnue: cannot open file`, `nnue: bad magic`, `nnue: unsupported version`, or `nnue: wrong size`, and the function returns false without changing the live net.

`src/nnue.cpp` splits the old lambda into `quantize`, `make_builtin`, and `live_weights`. `quantize` is the old conversion: `W1` and `B1` divided by `WeightScale`, `W2` and `B2` divided by `OutputScale`. `make_builtin` calls `quantize` on `NnueW1`, `NnueB1`, `NnueW2`, and `NnueB2`. `live_weights` is no longer `const`, so a later load can assign a new `Weights`. `weights()` still returns a const reference, and the evaluation code is unchanged. `read_i16` copies the little-endian bits into an `int16_t` with `memcpy`, so a negative weight is not a signed overflow. The live net is replaced only by `live_weights() = std::move(incoming)` after the buffer has been checked.

`src/uci.cpp` advertises `option name NnueFile type string default <empty>` next to `UseNNUE`, only when `nnue::available()` is true, which is the same condition the lock used for `UseNNUE`. The `setoption` branch parses the path the same way `Book File` does, including a space in the path. Failure prints `info string` plus the error and keeps the current net. Success clears the hash. A real path also prints `info string loaded nnue <path>`. Restoring `<empty>` does not print that line.

With the option left unset, the first search still runs `make_builtin()`, which is the old division. Measured with `Threads 1`, `Hash 16`, and `OwnBook false`: `bench 11` is 312866, `bench 13` is 862329, and `go perft 5` from the start position is 4865609. The same three numbers were printed after `setoption name NnueFile value` of the file produced from `nnue_weights.inc`. Perft does not evaluate, so it is a control that the search driver was not disturbed. The bench match is the check that the loaded floats search like the compiled-in net.

`tests_t8/nnue_convert.cpp` reads the same include and writes the `FORGENET` file. `tests_t8/nnue_file_test.cpp` links the engine, compares every int16 in that file with `NnueW1`, `NnueB1`, `NnueW2`, and `NnueB2`, then loads a copy whose `B2` is 2000 higher and checks that an evaluation changes. After that different net is the current one, the test rejects a bad magic, a version other than 1, a hidden size of 128, a truncated file, an extra byte, a missing path, an empty file, an 8-byte header, and a file larger than 2 MiB. The evaluation stays on the shifted net through all of those rejections. An empty path and `<empty>` then restore the compiled-in evaluation. Compiled against the lock header, which has no `load_file`, the test fails to build.

## Files changed

- `forge-combo29/include/forge/nnue.hpp`
- `forge-combo29/src/nnue.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t8/nnue_convert.cpp` (writes `nnue_weights.inc` as a `FORGENET` file)
- `forge-combo29/tests_t8/nnue_file_test.cpp`
- `forge-combo29/tests_t8/expected_uci.txt`
- `forge-combo29/REPORT_t8.md`

Engine diff against the lock: 137 insertions, 13 deletions in `nnue.hpp`, `nnue.cpp`, and `uci.cpp`.

## Build

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t8-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-t8-build -j && g++ --version | head -1
```

```
-- Configuring done (0.0s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-t8-build
[100%] Built target forge
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

The host CPU supports AVX-512, so the lock default `-march=x86-64-v4` was used. `FORGE_PORTABLE` was not set.

## Converter

```
g++ -std=c++20 -I/agent/repos/dwqww/forge-combo29/include -I/agent/repos/dwqww/forge-combo29/src -DFORGE_NNUE_HIDDEN=256 /agent/repos/dwqww/forge-combo29/tests_t8/nnue_convert.cpp -o /tmp/nnue_convert
/tmp/nnue_convert /tmp/t8/lock.fnn
```

```
wrote /tmp/t8/lock.fnn hidden 256
```

## AddressSanitizer and UndefinedBehaviorSanitizer

```
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -fsanitize=address,undefined \
  -I/agent/repos/dwqww/forge-combo29/include \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 \
  /agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp \
  /agent/repos/dwqww/forge-combo29/src/nnue.cpp \
  /agent/repos/dwqww/forge-combo29/src/board.cpp \
  /agent/repos/dwqww/forge-combo29/src/bitboard.cpp \
  -o /tmp/nnue_file_test
/tmp/nnue_file_test /tmp/t8/lock.fnn
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

Exit status 0. The sanitizers printed nothing.

The same test does not compile against the lock header (`git show origin/lock/combo29-20261110:forge-combo29/include/forge/nnue.hpp`, which has no `load_file`):

```
g++ -std=c++20 -fsyntax-only -I/tmp/lock-include -I/agent/repos/dwqww/forge-combo29/include -DFORGE_NNUE_HIDDEN=256 /agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp
```

Exit status 1:

```
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp: In function ‘int main(int, char**)’:
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:60:38: error: ‘load_file’ is not a member of ‘forge::nnue’
   60 |     const bool loaded = forge::nnue::load_file(net_path, error);
      |                                      ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:76:25: error: ‘load_file’ is not a member of ‘forge::nnue’
   76 |     expect(forge::nnue::load_file(shifted_path, error), "load shifted bias");
      |                         ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:80:25: error: ‘load_file’ is not a member of ‘forge::nnue’
   80 |     expect(forge::nnue::load_file("", error) && error.empty(), "empty path restores built-in net");
      |                         ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:87:26: error: ‘load_file’ is not a member of ‘forge::nnue’
   87 |     expect(!forge::nnue::load_file(net_path + ".magic", error) && error == "nnue: bad magic",
      |                          ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:94:26: error: ‘load_file’ is not a member of ‘forge::nnue’
   94 |     expect(!forge::nnue::load_file(net_path + ".version", error) && error == "nnue: unsupported version",
      |                          ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:101:26: error: ‘load_file’ is not a member of ‘forge::nnue’
  101 |     expect(!forge::nnue::load_file(net_path + ".hidden", error) && error == "nnue: wrong size",
      |                          ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:107:26: error: ‘load_file’ is not a member of ‘forge::nnue’
  107 |     expect(!forge::nnue::load_file(net_path + ".short", error) && error == "nnue: wrong size",
      |                          ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:113:26: error: ‘load_file’ is not a member of ‘forge::nnue’
  113 |     expect(!forge::nnue::load_file(net_path + ".extra", error) && error == "nnue: wrong size",
      |                          ^~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp:116:26: error: ‘load_file’ is not a member of ‘forge::nnue’
  116 |     expect(!forge::nnue::load_file(net_path + ".missing", error) && error == "nnue: cannot open file",
      |                          ^~~~~~~~~
```

## Bench and perft

Options sent before the searches: `OwnBook false`, `Threads 1`, `Hash 16`. The first `go perft 5`, `bench 11`, and `bench 13` use the compiled-in net. The second pair loads `/tmp/t8/lock.fnn`. Rejected files follow, then `<empty>` restores the compiled-in net and `bench 11` is repeated.

```
{
  printf '%s\n' \
    'uci' \
    'setoption name OwnBook value false' \
    'setoption name Threads value 1' \
    'setoption name Hash value 16' \
    'isready' \
    'position startpos' \
    'go perft 5' \
    'bench 11' \
    'bench 13' \
    'setoption name NnueFile value /tmp/t8/lock.fnn' \
    'isready' \
    'position startpos' \
    'go perft 5' \
    'bench 11' \
    'bench 13' \
    'setoption name NnueFile value /tmp/t8/lock.fnn.magic' \
    'setoption name NnueFile value /tmp/t8/lock.fnn.version' \
    'setoption name NnueFile value /tmp/t8/lock.fnn.hidden' \
    'setoption name NnueFile value /tmp/t8/lock.fnn.short' \
    'setoption name NnueFile value /tmp/t8/missing.fnn' \
    'setoption name NnueFile value <empty>' \
    'isready' \
    'bench 11' \
    'quit'
} | /tmp/forge-t8-build/forge
```

Exit status 0. stderr was empty. Full stdout:

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
info string bench depth 11 nodes 312866 time 170 nps 1840388
info string bench depth 13 nodes 862329 time 449 nps 1920554
info string loaded nnue /tmp/t8/lock.fnn
readyok
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
info string bench depth 11 nodes 312866 time 154 nps 2031597
info string bench depth 13 nodes 862329 time 483 nps 1785360
info string nnue: bad magic
info string nnue: unsupported version
info string nnue: wrong size
info string nnue: wrong size
info string nnue: cannot open file
readyok
info string bench depth 11 nodes 312866 time 161 nps 1943267
```

Node counts, compiled-in net and the converted lock file:

- `go perft 5` from the start position: 4865609
- `bench 11`: 312866
- `bench 13`: 862329

After the rejected files and `NnueFile <empty>`, `bench 11` was 312866 again.

A path containing a space also loads. Command:

```
cp /tmp/t8/lock.fnn "/tmp/t8/lock net.fnn"
printf '%s\n' 'uci' 'setoption name OwnBook value false' 'isready' 'setoption name NnueFile value /tmp/t8/lock net.fnn' 'isready' 'bench 11' 'quit' | /tmp/forge-t8-build/forge
```

The lines that matter:

```
option name NnueFile type string default <empty>
readyok
info string loaded nnue /tmp/t8/lock net.fnn
readyok
info string bench depth 11 nodes 312866 time 169 nps 1851278
```

## Follow-up

This is the measurement after the `gcount` change and the stronger test. On the first version, `!input` did not reject `/tmp/t8/lock.fnn` on this libstdc++. The change is the acceptance condition described above: keep the bytes when `gcount` equals the length. The new test compares every converted int16 with `nnue_weights.inc`, and it checks that a bad file leaves the shifted net in place.

Sanitized test, after rebuilding with `-I forge-combo29/src` so the test can include `nnue_weights.inc`:

```
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -fsanitize=address,undefined \
  -I/agent/repos/dwqww/forge-combo29/include \
  -I/agent/repos/dwqww/forge-combo29/src \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_SLIDER_PEXT=1 \
  /agent/repos/dwqww/forge-combo29/tests_t8/nnue_file_test.cpp \
  /agent/repos/dwqww/forge-combo29/src/nnue.cpp \
  /agent/repos/dwqww/forge-combo29/src/board.cpp \
  /agent/repos/dwqww/forge-combo29/src/bitboard.cpp \
  -o /tmp/nnue_file_test
/tmp/nnue_file_test /tmp/t8/lock.fnn
```

```
ok load converted net
ok startpos eval matches built-in net
ok kiwipete eval matches built-in net
ok converted file size
ok converted file magic
ok converted file version
ok converted file hidden size
ok w1 matches compiled-in net
ok b1 matches compiled-in net
ok w2 matches compiled-in net
ok b2 matches compiled-in net
ok load shifted bias
ok shifted bias changes an evaluation
ok bad magic keeps the current net
ok eval unchanged after bad magic
ok wrong version keeps the current net
ok wrong hidden size keeps the current net
ok truncated file keeps the current net
ok oversized file keeps the current net
ok missing file keeps the current net
ok empty file keeps the current net
ok header-only file keeps the current net
ok file over 2MiB keeps the current net
ok eval unchanged after rejected files
ok empty path restores built-in net
ok <empty> restores built-in net
ok restored eval matches built-in net
PASS
```

Exit status 0. The sanitizers printed nothing. The same source still fails to compile against the lock header: `load_file` is not a member of `forge::nnue`.

Release engine rebuilt with `cmake --build /tmp/forge-t8-build -j`, then the same UCI options as above. stderr was empty. Node lines:

```
nodes 4865609
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 433 nps 1991521
info string loaded nnue /tmp/t8/lock.fnn
nodes 4865609
info string bench depth 11 nodes 312866 time 151 nps 2071960
info string bench depth 13 nodes 862329 time 415 nps 2077901
info string nnue: bad magic
info string nnue: wrong size
info string nnue: wrong size
info string bench depth 11 nodes 312866 time 183 nps 1709650
```

The whole engine was also built with AddressSanitizer and UndefinedBehaviorSanitizer:

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t8-asan -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build /tmp/forge-t8-asan -j
```

`ASAN_OPTIONS=halt_on_error=1:detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 /tmp/forge-t8-asan/forge` with `Threads 1`, `Hash 16`, `OwnBook false`, the converted file, a file larger than 2 MiB, and `<empty>`. Exit status 0. stderr was empty (0 bytes). Node lines:

```
nodes 4865609
info string bench depth 11 nodes 312866 time 1861 nps 168117
info string bench depth 13 nodes 862329 time 4929 nps 174950
info string loaded nnue /tmp/t8/lock.fnn
info string bench depth 11 nodes 312866 time 1799 nps 173911
info string bench depth 13 nodes 862329 time 5147 nps 167540
info string nnue: wrong size
info string bench depth 11 nodes 312866 time 1786 nps 175176
```

## What was not verified

- No net with a hidden size other than 256 was installed. A file that declares hidden size 128 is rejected as `nnue: wrong size`.
- The reader was not run on a big-endian machine. The integers are decoded from little-endian bytes on this x86-64 host.
- No strength or speed comparison was made. The `nps` figures above are the engine's own printout for those runs.
