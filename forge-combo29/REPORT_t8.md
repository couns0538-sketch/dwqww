# Task 8: load an NNUE net from a file

The lock engine can evaluate only the network compiled in from `src/nnue_weights.inc`. There is no way to point it at another net of the same shape.

`NnueFile` is a string UCI option, default `<empty>`. An empty value or `<empty>` installs the compiled-in net. Any other value is read as a `FORGENET` file: 8-byte magic, little-endian uint32 version 1, little-endian uint32 hidden size, then little-endian int16 `W1`, `B1`, `W2`, and one int16 `B2`. The hidden size must equal the compiled `HiddenSize` (256) and the file must be exactly 394770 bytes. A wrong magic, version, or size prints `info string` with the reason and leaves the current net in place. A successful load replaces the live weights, clears the hash, and prints `info string loaded nnue <path>`. With the option left unset, the weight conversion is the same division by 4096 as before, so bench and perft stay on the lock counts.

## Files changed

- `forge-combo29/include/forge/nnue.hpp`
- `forge-combo29/src/nnue.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t8/nnue_convert.cpp` (writes `nnue_weights.inc` as a `FORGENET` file)
- `forge-combo29/tests_t8/nnue_file_test.cpp`
- `forge-combo29/tests_t8/expected_uci.txt`
- `forge-combo29/REPORT_t8.md`

Engine diff: 135 insertions, 13 deletions.

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

## What was not verified

- The engine binary itself was not rebuilt with AddressSanitizer or UndefinedBehaviorSanitizer. The sanitizer run is the test program above.
- No net with a hidden size other than 256 was installed. A file that declares hidden size 128 is rejected as `nnue: wrong size`.
- The reader was not run on a big-endian machine. The integers are decoded from little-endian bytes on this x86-64 host.
- No strength or speed comparison was made. The `nps` figures above are the engine's own printout for those runs.
