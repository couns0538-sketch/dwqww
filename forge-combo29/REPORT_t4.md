# REPORT t4 — clock parsing

## What was wrong

`parse_limits` in `forge-combo29/src/uci.cpp` read every `go` number except `nodes` into a 32-bit `int` with `std::from_chars`. `3000000000` does not fit. The conversion failed, the code substituted 0, and for the side to move that became `time_ms = 0`. The search then set a 1 ms hard budget and moved at once. The same reader rejects a leading `+`, so `movetime +80` failed and also became 0. A negative token already parsed and was then clamped with `std::max(0, value)`. A malformed token already became 0.

On the unchanged lock binary (`16833ecc`), `go depth 12 wtime 3000000000 btime 3000000000` stopped at depth 6 (`nodes 1703`, `bestmove d2d4`) instead of the depth-12 line (`nodes 56720`, `bestmove e2e4`). `go depth +8` stopped at depth 1. `go movetime +80` returned in under 2 ms. `go movetime 80` searched for about 80 ms.

## The fix

`movetime_ms`, `time_ms`, and `increment_ms` are `std::int64_t`. The parser accepts one leading `+`, parses the token into int64, and clamps. A value above int64 clamps to the top of that range and then to the clock ceiling. A negative clock clamps to 0. Junk, a second sign, or a missing number still yields 0, which is what a failed parse used to do. The ceiling is `INT64_MAX / 150`, so the existing time formula can multiply an increment by `TmIncrementPercent` (option maximum 150) and a soft limit by `TmHardSoftMultiple` (option maximum 20) without a signed 64-bit overflow. Depth, mate, and movestogo use the same reader and then their existing bounds: depth 1..64, mate 0..32, movestogo at least 1 and at most `INT_MAX`. `nodes` is unchanged. It already used `uint64_t`, and a failed parse still leaves the node limit unset.

## Files changed

- `forge-combo29/include/forge/search.hpp` — clock fields widened to `std::int64_t`
- `forge-combo29/src/uci.cpp` — 64-bit parse and clamp
- `forge-combo29/tests_t4/clock_commands.txt` — UCI transcript
- `forge-combo29/tests_t4/clock_expected.txt` — expected stable lines and time bounds
- `forge-combo29/tests_t4/check_clock.cpp` — reads engine stdout and checks the expected file
- `forge-combo29/REPORT_t4.md` — this report

Engine diff: 73 insertions and 19 deletions in `src/uci.cpp` and `search.hpp`.

## How to run the transcript

The engine reads the next command on its main thread, and that command stops a search that has not printed `bestmove` yet. Send `clock_commands.txt` one line at a time (skip blanks and `#` lines). Wait for `uciok`, `readyok`, or `bestmove` before the next line. Forward stdout to:

```
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -o check_clock forge-combo29/tests_t4/check_clock.cpp
./check_clock forge-combo29/tests_t4/clock_expected.txt
```

`check_clock` prints `pass` or `fail` and exits 0 or 1. It does not start a process and does not write a file. The runs below used a small driver that does that forwarding. The driver is not in the tree.

Setup for every clock run: `Threads 1`, `Hash 16`, `OwnBook false`. The transcript also sets `Move Overhead` to 0 so `movetime 80` is an 80 ms budget. A separate run below leaves the default overhead of 10 ms.

## Commands and output

Compiler: `g++` 13.3.0. Build of the patched engine:

```
CXX=g++ cmake -S forge-combo29 -B /tmp/forge-t4-rel -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-t4-rel -j 4
```

That configures with the default `-march=x86-64-v4` (this CPU has AVX-512 and BMI2) and links `forge`. Exit code 0.

### bench 11, bench 13, perft 5

```
printf '%s\n' uci 'setoption name Threads value 1' 'setoption name Hash value 16' 'setoption name OwnBook value false' isready 'bench 11' 'bench 13' 'position startpos' 'go perft 5' quit | /tmp/forge-t4-rel/forge
```

Exit code 0. Full stdout:

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
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 426 nps 2024246
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

`bench 11` = 312866 nodes, `bench 13` = 862329 nodes, `go perft 5` from the start position = 4865609 nodes.

### Clock transcript on the patched engine

```
python3 /tmp/run_clock_test.py /tmp/forge-t4-rel/forge /tmp/check_clock forge-combo29/tests_t4/clock_commands.txt forge-combo29/tests_t4/clock_expected.txt
```

Exit code 0. Engine stderr was empty. Full combined stdout (engine lines, then the checker):

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
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 1001000 hashfull 0 time 1 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
info depth 13 seldepth 23 score cp 26 nodes 72062 nps 2058914 hashfull 46 time 35 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 f8b4 d4c6 b7c6 f1e2 b4c3 b2c3 d7d5
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 2074285 hashfull 61 time 49 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
info depth 13 seldepth 23 score cp 26 nodes 72062 nps 2058914 hashfull 46 time 35 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 f8b4 d4c6 b7c6 f1e2 b4c3 b2c3 d7d5
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 2032800 hashfull 61 time 50 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
info depth 13 seldepth 23 score cp 26 nodes 72062 nps 2058914 hashfull 46 time 35 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 f8b4 d4c6 b7c6 f1e2 b4c3 b2c3 d7d5
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 2074285 hashfull 61 time 49 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
bestmove d2d4
info depth 1 seldepth 3 score cp -27 nodes 29 nps 0 hashfull 0 time 0 pv g8f6
info depth 2 seldepth 3 score cp 1 nodes 61 nps 0 hashfull 0 time 0 pv g8f6 d2d3
info depth 3 seldepth 4 score cp -10 nodes 220 nps 0 hashfull 0 time 0 pv e7e5 d2d3 g8f6
info depth 4 seldepth 5 score cp 15 nodes 450 nps 0 hashfull 0 time 0 pv g8f6 d2d3 e7e5 c2c3
info depth 5 seldepth 8 score cp -1 nodes 1093 nps 0 hashfull 0 time 0 pv e7e5 c2c3 g8f6 d2d3 d7d6
info depth 6 seldepth 9 score cp -21 nodes 2682 nps 2682000 hashfull 1 time 1 pv e7e5 g1f3 b8c6 d2d4 e5d4 f3d4
info depth 7 seldepth 11 score cp -16 nodes 3303 nps 3303000 hashfull 1 time 1 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4
info depth 8 seldepth 12 score cp -16 nodes 4489 nps 2244500 hashfull 1 time 2 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4 f3d4
info depth 9 seldepth 13 score cp -13 nodes 8567 nps 2141750 hashfull 5 time 4 pv e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1e2
info depth 10 seldepth 21 score cp -18 nodes 14583 nps 2083285 hashfull 8 time 7 pv e7e6 d2d4 d7d5 b1c3 f8b4 e4d5 e6d5 g1f3 g8f6 f1d3
bestmove e7e6
info depth 1 seldepth 3 score cp -27 nodes 29 nps 0 hashfull 0 time 0 pv g8f6
info depth 2 seldepth 3 score cp 1 nodes 61 nps 0 hashfull 0 time 0 pv g8f6 d2d3
info depth 3 seldepth 4 score cp -10 nodes 220 nps 0 hashfull 0 time 0 pv e7e5 d2d3 g8f6
info depth 4 seldepth 5 score cp 15 nodes 450 nps 0 hashfull 0 time 0 pv g8f6 d2d3 e7e5 c2c3
info depth 5 seldepth 8 score cp -1 nodes 1093 nps 0 hashfull 0 time 0 pv e7e5 c2c3 g8f6 d2d3 d7d6
info depth 6 seldepth 9 score cp -21 nodes 2682 nps 2682000 hashfull 1 time 1 pv e7e5 g1f3 b8c6 d2d4 e5d4 f3d4
info depth 7 seldepth 11 score cp -16 nodes 3303 nps 3303000 hashfull 1 time 1 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4
info depth 8 seldepth 12 score cp -16 nodes 4489 nps 2244500 hashfull 1 time 2 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4 f3d4
info depth 9 seldepth 13 score cp -13 nodes 8567 nps 2141750 hashfull 5 time 4 pv e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1e2
info depth 10 seldepth 21 score cp -18 nodes 14583 nps 2083285 hashfull 8 time 7 pv e7e6 d2d4 d7d5 b1c3 f8b4 e4d5 e6d5 g1f3 g8f6 f1d3
bestmove e7e6
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 0 hashfull 0 time 0 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2025714 hashfull 36 time 28 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 2413250 hashfull 7 time 4 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 2183666 hashfull 10 time 6 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 2179545 hashfull 15 time 11 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2025714 hashfull 36 time 28 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
info depth 13 seldepth 23 score cp 26 nodes 72062 nps 2058914 hashfull 46 time 35 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 f8b4 d4c6 b7c6 f1e2 b4c3 b2c3 d7d5
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 2032800 hashfull 61 time 50 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
info depth 15 seldepth 28 score cp 27 nodes 212340 nps 1966111 hashfull 121 time 108 pv e2e4 c7c5 c2c3 b8c6 g1f3 e7e5 f1b5 g8e7 e1g1 a7a6 b5c6 e7c6 d2d4 c5d4 c3d4
bestmove e2e4
ok 1 wall_ms 1.67974 depth 8 best d2d4
ok 2 wall_ms 27.7167 depth 12 best e2e4
ok 3 wall_ms 27.8316 depth 12 best e2e4
ok 4 wall_ms 27.9808 depth 12 best e2e4
ok 5 wall_ms 27.807 depth 12 best e2e4
ok 6 wall_ms 0.00437 depth 3 best e2e4
ok 7 wall_ms 79.8665 depth 14 best e2e4
ok 8 wall_ms 80.1461 depth 14 best e2e4
ok 9 wall_ms 79.8786 depth 14 best e2e4
ok 10 wall_ms 1.00612 depth 6 best d2d4
ok 11 wall_ms 0.598689 depth 6 best d2d4
ok 12 wall_ms 0.983109 depth 6 best d2d4
ok 13 wall_ms 0.79714 depth 6 best d2d4
ok 14 wall_ms 0.977066 depth 6 best d2d4
ok 15 wall_ms 7.50428 depth 10 best e7e6
ok 16 wall_ms 7.4173 depth 10 best e7e6
ok 17 wall_ms 28.3506 depth 12 best e2e4
ok 18 wall_ms 120.32 depth 15 best e2e4
pass
```

### Same transcript on the unchanged lock

The lock binary is `/tmp/forge-lock`, built from `16833ecc` (`origin/lock/combo29-20261110`) before this edit:

```
CXX=g++ cmake -S forge-combo29 -B /tmp/forge-lock-build -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-lock-build -j 4
cp /tmp/forge-lock-build/forge /tmp/forge-lock
python3 /tmp/run_clock_test.py /tmp/forge-lock /tmp/check_clock forge-combo29/tests_t4/clock_commands.txt forge-combo29/tests_t4/clock_expected.txt
```

Exit code 1. Checker verdict (8 failures). The lines above each `fail` in the captured stdout are the engine's own `info` / `bestmove` lines; the failures quote the last `info` line:

```
fail 1: exact mismatch
  wall_ms 0.00177 depth 1
  best bestmove d2d4
  info info depth 1 seldepth 1 score cp 1 nodes 26 pv d2d4
  expected best d2d4
  expected info info depth 8 seldepth 13 score cp 26 nodes 4099 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
fail 2: exact mismatch
  wall_ms 0.688017 depth 6
  best bestmove d2d4
  info info depth 6 seldepth 10 score cp 34 nodes 1703 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
  expected best e2e4
  expected info info depth 12 seldepth 23 score cp 30 nodes 56720 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
fail 3: exact mismatch
  wall_ms 1.08763 depth 6
  best bestmove d2d4
  info info depth 6 seldepth 10 score cp 34 nodes 1703 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
  expected best e2e4
  expected info info depth 12 seldepth 23 score cp 30 nodes 56720 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
ok 4 wall_ms 27.6527 depth 12 best e2e4
fail 5: exact mismatch
  wall_ms 0.774937 depth 6
  best bestmove d2d4
  info info depth 6 seldepth 10 score cp 34 nodes 1703 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
  expected best e2e4
  expected info info depth 12 seldepth 23 score cp 30 nodes 56720 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
ok 6 wall_ms 0.080852 depth 3 best e2e4
fail 7: wall time outside 60..3000 ms
  wall_ms 0.541425 depth 6
  best bestmove d2d4
  info info depth 6 seldepth 10 score cp 34 nodes 1703 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
ok 8 wall_ms 80.5593 depth 14 best e2e4
fail 9: wall time outside 60..3000 ms
  wall_ms 1.17565 depth 6
  best bestmove d2d4
  info info depth 6 seldepth 10 score cp 34 nodes 1703 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
ok 10 wall_ms 0.890894 depth 6 best d2d4
ok 11 wall_ms 1.02961 depth 6 best d2d4
ok 12 wall_ms 0.876785 depth 6 best d2d4
ok 13 wall_ms 1.00477 depth 6 best d2d4
ok 14 wall_ms 1.01199 depth 6 best d2d4
fail 15: exact mismatch
  wall_ms 0.981892 depth 5
  best bestmove e7e5
  info info depth 5 seldepth 8 score cp -1 nodes 1093 pv e7e5 c2c3 g8f6 d2d3 d7d6
  expected best e7e6
  expected info info depth 10 seldepth 21 score cp -18 nodes 14583 pv e7e6 d2d4 d7d5 b1c3 f8b4 e4d5 e6d5 g1f3 g8f6 f1d3
ok 16 wall_ms 7.80347 depth 10 best e7e6
ok 17 wall_ms 27.9409 depth 12 best e2e4
fail 18: wall time outside 70..3000 ms
  wall_ms 6.36214 depth 10
  best bestmove d2d4
  info info depth 10 seldepth 14 score cp 24 nodes 13102 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
fail 8
```

Failures are the cases the old parser turns into 0: `depth +8`, `wtime 3000000000`, `wtime 2147483648`, a value bigger than int64, `movetime +80`, `movetime +00080`, Black `btime 3000000000`, and `winc 3000000000`. `wtime 2147483647` (still inside a signed 32-bit int), plain `movetime 80`, negative and malformed tokens, and the opponent's clock still match on the lock.

### AddressSanitizer and UndefinedBehaviorSanitizer

```
CXX=g++ cmake -S forge-combo29 -B /tmp/forge-t4-asan -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" \
  && cmake --build /tmp/forge-t4-asan -j 4
ASAN_OPTIONS=halt_on_error=1:detect_leaks=1:abort_on_error=1 \
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:abort_on_error=1 \
python3 /tmp/run_clock_test.py /tmp/forge-t4-asan/forge /tmp/check_clock forge-combo29/tests_t4/clock_commands.txt forge-combo29/tests_t4/clock_expected.txt
```

Build exit code 0. Test exit code 0. Engine stderr was empty (no ASan or UBSan diagnostic). Full stdout:

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
info depth 1 seldepth 1 score cp 1 nodes 26 nps 26000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 27000 hashfull 0 time 2 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 53750 hashfull 0 time 4 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 67333 hashfull 0 time 6 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 91000 hashfull 0 time 11 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 106437 hashfull 0 time 16 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 122571 hashfull 1 time 21 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 136633 hashfull 2 time 30 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 101000 hashfull 0 time 4 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 143000 hashfull 0 time 7 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 154818 hashfull 0 time 11 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 160875 hashfull 1 time 16 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 163960 hashfull 2 time 25 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 166431 hashfull 7 time 58 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 170155 hashfull 10 time 77 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 172482 hashfull 15 time 139 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 168809 hashfull 36 time 336 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 71666 hashfull 0 time 3 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 80800 hashfull 0 time 5 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 111222 hashfull 0 time 9 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 121642 hashfull 0 time 14 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 135473 hashfull 1 time 19 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 146392 hashfull 2 time 28 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 163610 hashfull 7 time 59 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 167974 hashfull 10 time 78 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 171250 hashfull 15 time 140 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 167315 hashfull 36 time 339 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 101000 hashfull 0 time 4 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 143000 hashfull 0 time 7 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 154818 hashfull 0 time 11 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 151411 hashfull 1 time 17 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 157653 hashfull 2 time 26 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 169350 hashfull 7 time 57 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 170155 hashfull 10 time 77 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 172482 hashfull 15 time 139 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 168809 hashfull 36 time 336 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 26000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 53750 hashfull 0 time 4 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 67333 hashfull 0 time 6 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 91000 hashfull 0 time 11 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 106437 hashfull 0 time 16 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 122571 hashfull 1 time 21 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 136633 hashfull 2 time 30 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 155693 hashfull 7 time 62 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 161753 hashfull 10 time 81 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 166493 hashfull 15 time 144 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 165364 hashfull 36 time 343 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 71666 hashfull 0 time 3 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 80800 hashfull 0 time 5 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 111222 hashfull 0 time 9 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 131000 hashfull 0 time 13 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 143000 hashfull 1 time 18 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 151814 hashfull 2 time 27 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 166431 hashfull 7 time 58 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 165848 hashfull 10 time 79 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 26000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 71666 hashfull 0 time 3 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 80800 hashfull 0 time 5 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 111222 hashfull 0 time 9 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 131000 hashfull 0 time 13 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 135473 hashfull 1 time 19 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 151814 hashfull 2 time 27 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 163610 hashfull 7 time 59 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 167974 hashfull 10 time 78 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 134666 hashfull 0 time 3 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 143000 hashfull 0 time 7 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 154818 hashfull 0 time 11 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 160875 hashfull 1 time 16 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 163960 hashfull 2 time 25 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 172375 hashfull 7 time 56 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 172394 hashfull 10 time 76 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
info depth 1 seldepth 3 score cp -27 nodes 29 nps 0 hashfull 0 time 0 pv g8f6
info depth 2 seldepth 3 score cp 1 nodes 61 nps 61000 hashfull 0 time 1 pv g8f6 d2d3
info depth 3 seldepth 4 score cp -10 nodes 220 nps 73333 hashfull 0 time 3 pv e7e5 d2d3 g8f6
info depth 4 seldepth 5 score cp 15 nodes 450 nps 90000 hashfull 0 time 5 pv g8f6 d2d3 e7e5 c2c3
info depth 5 seldepth 8 score cp -1 nodes 1093 nps 121444 hashfull 0 time 9 pv e7e5 c2c3 g8f6 d2d3 d7d6
info depth 6 seldepth 9 score cp -21 nodes 2682 nps 149000 hashfull 1 time 18 pv e7e5 g1f3 b8c6 d2d4 e5d4 f3d4
info depth 7 seldepth 11 score cp -16 nodes 3303 nps 150136 hashfull 1 time 22 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4
info depth 8 seldepth 12 score cp -16 nodes 4489 nps 154793 hashfull 1 time 29 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4 f3d4
info depth 9 seldepth 13 score cp -13 nodes 8567 nps 158648 hashfull 5 time 54 pv e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1e2
info depth 10 seldepth 21 score cp -18 nodes 14583 nps 160252 hashfull 8 time 91 pv e7e6 d2d4 d7d5 b1c3 f8b4 e4d5 e6d5 g1f3 g8f6 f1d3
bestmove e7e6
info depth 1 seldepth 3 score cp -27 nodes 29 nps 0 hashfull 0 time 0 pv g8f6
info depth 2 seldepth 3 score cp 1 nodes 61 nps 0 hashfull 0 time 0 pv g8f6 d2d3
info depth 3 seldepth 4 score cp -10 nodes 220 nps 110000 hashfull 0 time 2 pv e7e5 d2d3 g8f6
info depth 4 seldepth 5 score cp 15 nodes 450 nps 112500 hashfull 0 time 4 pv g8f6 d2d3 e7e5 c2c3
info depth 5 seldepth 8 score cp -1 nodes 1093 nps 156142 hashfull 0 time 7 pv e7e5 c2c3 g8f6 d2d3 d7d6
info depth 6 seldepth 9 score cp -21 nodes 2682 nps 157764 hashfull 1 time 17 pv e7e5 g1f3 b8c6 d2d4 e5d4 f3d4
info depth 7 seldepth 11 score cp -16 nodes 3303 nps 165150 hashfull 1 time 20 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4
info depth 8 seldepth 12 score cp -16 nodes 4489 nps 166259 hashfull 1 time 27 pv e7e5 g1f3 b8c6 b1c3 g8f6 d2d4 e5d4 f3d4
info depth 9 seldepth 13 score cp -13 nodes 8567 nps 164750 hashfull 5 time 52 pv e7e6 g1f3 d7d5 e4d5 e6d5 d2d4 g8f6 f1e2
info depth 10 seldepth 21 score cp -18 nodes 14583 nps 163853 hashfull 8 time 89 pv e7e6 d2d4 d7d5 b1c3 f8b4 e4d5 e6d5 g1f3 g8f6 f1d3
bestmove e7e6
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 101000 hashfull 0 time 4 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 125125 hashfull 0 time 8 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 131000 hashfull 0 time 13 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 143000 hashfull 1 time 18 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 157653 hashfull 2 time 26 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 166431 hashfull 7 time 58 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 170155 hashfull 10 time 77 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
info depth 11 seldepth 19 score cp 24 nodes 23975 nps 172482 hashfull 15 time 139 pv d2d4 e7e6 c2c4 g8f6 e2e3 f8e7 g1f3 b7b6 f1e2 c8b7 e1g1 c7c5
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 168308 hashfull 36 time 337 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 107500 hashfull 0 time 2 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 101000 hashfull 0 time 4 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 143000 hashfull 0 time 7 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 154818 hashfull 0 time 11 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 160875 hashfull 1 time 16 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 163960 hashfull 2 time 25 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
info depth 9 seldepth 14 score cp 31 nodes 9653 nps 172375 hashfull 7 time 56 pv d2d4 e7e6 c2c4 g8f6 g1f3 c7c5 d4d5 d7d6 e2e3 e6d5
info depth 10 seldepth 14 score cp 24 nodes 13102 nps 172394 hashfull 10 time 76 pv d2d4 e7e6 c2c4 g8f6 g1f3 f8e7 b1c3 d7d5 e2e3 b8d7 c4d5
bestmove d2d4
ok 1 wall_ms 28.0382 depth 8 best d2d4
ok 2 wall_ms 336.002 depth 12 best e2e4
ok 3 wall_ms 338.628 depth 12 best e2e4
ok 4 wall_ms 336.316 depth 12 best e2e4
ok 5 wall_ms 342.63 depth 12 best e2e4
ok 6 wall_ms 1.45269 depth 3 best e2e4
ok 7 wall_ms 79.3487 depth 10 best d2d4
ok 8 wall_ms 84.9221 depth 10 best d2d4
ok 9 wall_ms 82.5581 depth 10 best d2d4
ok 10 wall_ms 0.002095 depth 1 best d2d4
ok 11 wall_ms 0.00308 depth 2 best d2d4
ok 12 wall_ms 0.449775 depth 2 best d2d4
ok 13 wall_ms 1.72066 depth 3 best e2e4
ok 14 wall_ms 0.276918 depth 2 best d2d4
ok 15 wall_ms 90.524 depth 10 best e7e6
ok 16 wall_ms 89.5969 depth 10 best e7e6
ok 17 wall_ms 337.333 depth 12 best e2e4
ok 18 wall_ms 123.303 depth 10 best d2d4
pass
```

### Default Move Overhead (10 ms), patched engine

Not part of `clock_commands.txt`. `Threads 1`, `Hash 16`, `OwnBook false`, overhead left at the default 10. `movetime +80` and `movetime 80` both ran for about 70 ms and printed the same final line. `wtime 3000000000` still finished depth 12 at 56720 nodes.

```
# go movetime +80  wall_ms=69.53
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 1992941 hashfull 61 time 51 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
bestmove e2e4

# go movetime 80  wall_ms=69.98
info depth 14 seldepth 23 score cp 23 nodes 101640 nps 2032800 hashfull 61 time 50 pv e2e4 c7c5 g1f3 b8c6 b1c3 g7g6 d2d4 c5d4 f3d4 f8g7 d4c6 b7c6 f1c4 d7d6
bestmove e2e4

# go depth 12 wtime 3000000000 btime 3000000000  wall_ms=27.58
info depth 12 seldepth 23 score cp 30 nodes 56720 nps 2100740 hashfull 36 time 27 pv e2e4 c7c5 g1f3 b8c6 b1c3 e7e6 d2d4 c5d4 f3d4 g8f6 f1e2 f8e7
bestmove e2e4
```

## What I could not verify

- No game match, so no Elo statement. No speed claim. Bench NPS above is the number the engine printed, not a comparison.
- A clock of 3000000000 ms was not played out. That budget is about 34 days. Depth-capped searches show it is not treated as 0. They do not print the parsed integer, so they do not by themselves prove the stored value is exactly 3000000000 rather than another value large enough to finish depth 12. The field is int64 and 3000000000 fits in it.
- `go nodes` still uses its existing `uint64_t` parser. `nodes +100` does not set a node limit. I left that path alone.
- `movestogo` above `INT_MAX` now clamps to `INT_MAX` (the search already caps the used value at 50). The old parser turned that overflow into 1. I did not run a game to show the difference.
- Depth or mate values that do not fit in a 32-bit int now clamp to 64 or 32. The old parser turned them into the failed-parse value, which then clamped to depth 1 or mate 0. I did not run those, because a depth-64 search is not a useful check.
- Not built with the Windows clang ThinLTO+PGO lock recipe. This run is Linux g++ 13.3.0, Release, `-march=x86-64-v4`.
