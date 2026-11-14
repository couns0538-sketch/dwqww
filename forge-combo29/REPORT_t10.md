# Task 10: MultiPV

## What was wrong

The engine could report only one root move. Self-play had no UCI way to ask for the next-best opening moves.

## Fix

`MultiPV` is a UCI spin option from 1 to 8, default 1. At 1 the search loop is the same as before and info lines stay in the old form. Above 1, after each finished depth, the main worker searches the remaining root moves with the earlier choices removed and prints `info depth D seldepth S multipv i score ... pv ...`. `bestmove` stays the first line. A value outside 1..8 is clamped. A malformed value is rejected and the previous setting is kept.

Engine diff: 60 insertions and 1 deletion (`git diff --numstat`), under the 300-line cap.

## Files changed

- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/src/search.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t10/multipv_test.cpp`
- `forge-combo29/REPORT_t10.md`

## Build

Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`. CPU flags include `avx512f` and `bmi2`, so the default `-march=x86-64-v4` was used. The build directory is outside the repo.

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/forge-t10-new -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build /tmp/forge-t10-new -j
```

```
[ 11%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
EXIT:0
```

The lock binary used for comparison was built the same way from a copy of `16833ecc` (`origin/lock/combo29-20261110`) taken before these edits. Its build also ended with `Built target forge` and `EXIT:0`.

## bench 11, bench 13, and perft 5

Same command against the new binary and the lock binary. `bench` builds its own 16 MB, one-thread searcher. The three `setoption` lines are the settings required for the reference run.

```
printf '%s\n' \
  'setoption name Threads value 1' \
  'setoption name Hash value 16' \
  'setoption name OwnBook value false' \
  'isready' \
  'bench 11' \
  'bench 13' \
  'position startpos' \
  'go perft 5' \
  'quit' | /tmp/forge-t10-new/forge
```

```
readyok
info string bench depth 11 nodes 312866 time 174 nps 1798080
info string bench depth 13 nodes 862329 time 454 nps 1899403
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

Same command piped to `/tmp/forge-lock`:

```
readyok
info string bench depth 11 nodes 312866 time 221 nps 1415683
info string bench depth 13 nodes 862329 time 461 nps 1870561
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

`bench 11` is 312866 nodes, `bench 13` is 862329 nodes, and `go perft 5` is 4865609 nodes. The per-move perft counts match. `time` and `nps` are wall-clock and differ between the two runs.

## MultiPV 1 search output

`go` runs on a background thread, and the following `quit` was sent only after `bestmove`. Commands, in order, to each binary: `setoption name Threads value 1`, `setoption name Hash value 16`, `setoption name OwnBook value false`, `isready`, `position startpos`, `go depth 8`.

New binary:

```
readyok
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 0 hashfull 0 time 0 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 2574000 hashfull 1 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
bestmove d2d4
```

Lock binary:

```
readyok
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 3 seldepth 3 score cp 18 nodes 215 nps 0 hashfull 0 time 0 pv e2e4 h7h6 d2d4
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
info depth 5 seldepth 9 score cp 6 nodes 1001 nps 1001000 hashfull 0 time 1 pv c2c4 e7e5 e2e3 g8f6 d2d4
info depth 6 seldepth 10 score cp 34 nodes 1703 nps 1703000 hashfull 0 time 1 pv d2d4 d7d5 e2e3 g8f6 c2c4 d5c4
info depth 7 seldepth 11 score cp 17 nodes 2574 nps 1287000 hashfull 1 time 2 pv d2d4 d7d5 e2e3 g8f6 c2c4 c7c6 h2h3
info depth 8 seldepth 13 score cp 26 nodes 4099 nps 2049500 hashfull 2 time 2 pv d2d4 d7d5 c2c4 c7c6 e2e3 g8f6 h2h3 h7h6 c4d5
bestmove d2d4
```

Depth, seldepth, score, nodes, hashfull, pv, and `bestmove` match on every line. There is no `multipv` token. The only differences are wall-clock `nps` and `time` on the depth-5 and depth-7 lines.

The `uci` greeting gains one line, `option name MultiPV type spin default 1 min 1 max 8`. That line is part of the new option.

## MultiPV above 1

Commands sent to the new engine, waiting for `uciok`, `readyok`, each `bestmove`, and the invalid-option line before the next command:

```
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
isready
setoption name MultiPV value 2
position startpos
go depth 2
setoption name MultiPV value xyz
ucinewgame
position startpos
go depth 1
setoption name MultiPV value 9
ucinewgame
position startpos
go depth 1
setoption name MultiPV value 1
ucinewgame
position startpos
go depth 2
```

Full output:

```
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name MultiPV type spin default 1 min 1 max 8
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
info depth 1 seldepth 1 multipv 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 1 seldepth 1 multipv 2 score cp 1 nodes 51 nps 0 hashfull 0 time 0 pv g1f3
info depth 2 seldepth 2 multipv 1 score cp 49 nodes 79 nps 0 hashfull 0 time 0 pv d2d4 d7d6
info depth 2 seldepth 2 multipv 2 score cp 46 nodes 106 nps 0 hashfull 0 time 0 pv g1f3 e7e6
bestmove d2d4
info string invalid value for option MultiPV
info depth 1 seldepth 1 multipv 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 1 seldepth 1 multipv 2 score cp 1 nodes 51 nps 0 hashfull 0 time 0 pv g1f3
bestmove d2d4
info depth 1 seldepth 1 multipv 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 1 seldepth 1 multipv 2 score cp 1 nodes 51 nps 0 hashfull 0 time 0 pv g1f3
info depth 1 seldepth 1 multipv 3 score cp -10 nodes 74 nps 0 hashfull 0 time 0 pv c2c4
info depth 1 seldepth 1 multipv 4 score cp -11 nodes 95 nps 0 hashfull 0 time 0 pv e2e4
info depth 1 seldepth 1 multipv 5 score cp -15 nodes 113 nps 0 hashfull 0 time 0 pv h2h3
info depth 1 seldepth 1 multipv 6 score cp -16 nodes 129 nps 0 hashfull 0 time 0 pv e2e3
info depth 1 seldepth 1 multipv 7 score cp -16 nodes 146 nps 0 hashfull 0 time 0 pv b1c3
info depth 1 seldepth 1 multipv 8 score cp -20 nodes 161 nps 0 hashfull 0 time 0 pv d2d3
bestmove d2d4
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
```

`MultiPV 2` prints two lines per depth, and `bestmove d2d4` is the first move of `multipv 1`. `xyz` is rejected and the following search still has two lines. `9` is clamped to 8, so depth 1 prints `multipv 1` through `multipv 8` and `bestmove` is still `d2d4`. Setting it back to 1 removes the token. That depth-2 search visits 26 then 54 nodes, the same counts as the lock's depth-2 lines above.

The same `MultiPV 2` / `go depth 2` commands on the lock binary print no `multipv` token:

```
readyok
info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 hashfull 0 time 0 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 0 hashfull 0 time 0 pv d2d4 d7d6
bestmove d2d4
```

## Test on the lock source

`tests_t10/multipv_test.cpp` was compiled against the lock headers (`/tmp/forge-lock-src/include`, the `16833ecc` snapshot):

```
g++ -std=c++20 -c -I /tmp/forge-lock-src/include /agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp -o /tmp/multipv_test_lock.o
```

Exit status 1. Full output:

```
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In function ‘forge::SearchInfo {anonymous}::search_of(const forge::Board&, int, int, bool, std::string*)’:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:44:29: error: ‘struct forge::SearchLimits’ has no member named ‘multipv’
   44 |     if (set_multipv) limits.multipv = multipv;
      |                             ^~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In function ‘bool {anonymous}::lines_are_distinct_legal_roots(const forge::Board&, const forge::SearchInfo&)’:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:59:14: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   59 |     if (info.lines.empty() || info.lines[0].pv.empty()) return false;
      |              ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:59:36: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   59 |     if (info.lines.empty() || info.lines[0].pv.empty()) return false;
      |                                    ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:60:32: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   60 |     if (info.best_move != info.lines[0].pv.front() || info.score != info.lines[0].score) return false;
      |                                ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:60:74: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   60 |     if (info.best_move != info.lines[0].pv.front() || info.score != info.lines[0].score) return false;
      |                                                                          ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:61:38: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   61 |     for (std::size_t i = 0; i < info.lines.size(); ++i) {
      |                                      ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:62:18: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   62 |         if (info.lines[i].pv.empty() || !legal_root(board, info.lines[i].pv.front())) return false;
      |                  ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:62:65: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   62 |         if (info.lines[i].pv.empty() || !legal_root(board, info.lines[i].pv.front())) return false;
      |                                                                 ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:64:22: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   64 |             if (info.lines[i].pv.front() == info.lines[j].pv.front()) return false;
      |                      ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:64:50: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   64 |             if (info.lines[i].pv.front() == info.lines[j].pv.front()) return false;
      |                                                  ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In function ‘void {anonymous}::print_lines(const std::string&, const forge::SearchInfo&)’:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:72:63: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   72 |               << " nodes " << info.nodes << " lines " << info.lines.size() << '\n';
      |                                                               ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:73:38: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   73 |     for (std::size_t i = 0; i < info.lines.size(); ++i) {
      |                                      ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:74:59: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   74 |         std::cout << "  " << (i + 1) << " score " << info.lines[i].score << " pv";
      |                                                           ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:75:44: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   75 |         for (const forge::Move move : info.lines[i].pv) std::cout << ' ' << forge::Board::move_to_uci(move);
      |                                            ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In function ‘int main()’:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:96:25: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   96 |     expect(explicit_one.lines.empty() && baseline.lines.empty(), "MultiPV 1 does not publish extra lines");
      |                         ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:96:51: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   96 |     expect(explicit_one.lines.empty() && baseline.lines.empty(), "MultiPV 1 does not publish extra lines");
      |                                                   ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:99:65: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
   99 |     expect(clamped_zero.nodes == baseline.nodes && clamped_zero.lines.empty(), "MultiPV 0 is clamped to 1");
      |                                                                 ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:104:18: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  104 |     expect(three.lines.size() == 3, "depth 1 MultiPV 3 returns three lines");
      |                  ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:106:26: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  106 |     bool ordered = three.lines.size() == 3;
      |                          ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:107:39: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  107 |     for (std::size_t i = 1; i < three.lines.size(); ++i) ordered = ordered && three.lines[i].score <= three.lines[i - 1].score;
      |                                       ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:107:85: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  107 |     for (std::size_t i = 1; i < three.lines.size(); ++i) ordered = ordered && three.lines[i].score <= three.lines[i - 1].score;
      |                                                                                     ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:107:109: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  107 |     for (std::size_t i = 1; i < three.lines.size(); ++i) ordered = ordered && three.lines[i].score <= three.lines[i - 1].score;
      |                                                                                                             ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:116:18: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  116 |     expect(eight.lines.size() == 8, "MultiPV above 8 is clamped to 8");
      |                  ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:121:23: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  121 |     expect(last_depth.lines.size() == 2, "the result keeps the last depth's lines");
      |                       ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:133:16: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  133 |     expect(all.lines.size() == legal.size(), "MultiPV stops when the legal root moves run out");
      |                ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:134:24: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  134 |     bool covered = all.lines.size() == legal.size();
      |                        ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:136:44: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  136 |         const bool found = std::any_of(all.lines.begin(), all.lines.end(), [&](const forge::SearchInfo::MultiPvLine& line) {
      |                                            ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:136:63: error: ‘const struct forge::SearchInfo’ has no member named ‘lines’
  136 |         const bool found = std::any_of(all.lines.begin(), all.lines.end(), [&](const forge::SearchInfo::MultiPvLine& line) {
      |                                                               ^~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:136:105: error: ‘MultiPvLine’ in ‘struct forge::SearchInfo’ does not name a type
  136 |         const bool found = std::any_of(all.lines.begin(), all.lines.end(), [&](const forge::SearchInfo::MultiPvLine& line) {
      |                                                                                                         ^~~~~~~~~~~
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In lambda function:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:138:11: error: expected ‘{’ before ‘;’ token
  138 |         });
      |           ^
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp: In function ‘int main()’:
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:138:11: error: expected ‘)’ before ‘;’ token
  138 |         });
      |           ^
      |           )
/agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp:136:39: note: to match this ‘(’
  136 |         const bool found = std::any_of(all.lines.begin(), all.lines.end(), [&](const forge::SearchInfo::MultiPvLine& line) {
      |                                       ^
COMPILE_EXIT:1
```

## Test with this change

The test is linked to the Release objects of every `src/*.cpp` except `uci.cpp` (that file has `main`). Flags match the engine build.

```
g++ -O3 -DNDEBUG -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -I/agent/repos/dwqww/forge-combo29/include \
  -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_SEARCH_SPEED2=1 \
  -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/bitboard.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/board.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/book.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/eval.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/eval_params.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/nnue.cpp.o \
  /tmp/forge-t10-new/CMakeFiles/forge.dir/src/search.cpp.o \
  /agent/repos/dwqww/forge-combo29/tests_t10/multipv_test.cpp \
  -pthread -o /tmp/forge-t10-new/multipv_test
/tmp/forge-t10-new/multipv_test
```

```
default best e2e4 score 30 nodes 404 lines 0
multipv1 best e2e4 score 30 nodes 404 lines 0
ok the depth-4 search visits nodes
ok MultiPV 1 visits the same nodes as the default
ok MultiPV 1 plays the default move
ok MultiPV 1 reports the default score
ok MultiPV 1 reports the default pv
ok MultiPV 1 does not publish extra lines
ok MultiPV 1 info text has no multipv token
ok MultiPV 1 still prints info lines
ok MultiPV 0 is clamped to 1
depth1-multipv3 best d2d4 score 1 nodes 74 lines 3
  1 score 1 pv d2d4
  2 score 1 pv g1f3
  3 score -10 pv c2c4
ok depth 1 MultiPV 3 returns three lines
ok the three lines are distinct legal root moves
ok depth-1 lines are ordered by score
ok info prints multipv 1 before score
ok info prints multipv 2 before score
ok info prints multipv 3 before score
ok MultiPV 3 does not print a fourth line
depth1-multipv100 best d2d4 score 1 nodes 161 lines 8
  1 score 1 pv d2d4
  2 score 1 pv g1f3
  3 score -10 pv c2c4
  4 score -11 pv e2e4
  5 score -15 pv h2h3
  6 score -16 pv e2e3
  7 score -16 pv b1c3
  8 score -20 pv d2d3
ok MultiPV above 8 is clamped to 8
ok the eight lines are distinct legal root moves
depth3-multipv2 best e2e4 score 18 nodes 278 lines 2
  1 score 18 pv e2e4 h7h6 d2d4
  2 score 18 pv d2d4 h7h6 e2e4
ok the result keeps the last depth's lines
ok both last-depth lines are legal root moves
cramped legal 3
  h8g7
  h8h7
  h8g8
cramped-multipv8 best h8h7 score -97 nodes 10 lines 3
  1 score -97 pv h8h7
  2 score -105 pv h8g7
  3 score -109 pv h8g8
ok the cramped fen parses
ok the cramped position has fewer than 8 legal moves
ok MultiPV stops when the legal root moves run out
ok every legal root move is one of the lines
failures=0
```

Exit status 0.

## AddressSanitizer and UndefinedBehaviorSanitizer

The test and the engine sources except `uci.cpp` were compiled together with `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined` and the same `-D` flags as the Release build, including `-DNDEBUG` and `-march=x86-64-v4`.

```
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
  /tmp/forge-t10-asan/multipv_test
```

```
default best e2e4 score 30 nodes 404 lines 0
multipv1 best e2e4 score 30 nodes 404 lines 0
ok the depth-4 search visits nodes
ok MultiPV 1 visits the same nodes as the default
ok MultiPV 1 plays the default move
ok MultiPV 1 reports the default score
ok MultiPV 1 reports the default pv
ok MultiPV 1 does not publish extra lines
ok MultiPV 1 info text has no multipv token
ok MultiPV 1 still prints info lines
ok MultiPV 0 is clamped to 1
depth1-multipv3 best d2d4 score 1 nodes 74 lines 3
  1 score 1 pv d2d4
  2 score 1 pv g1f3
  3 score -10 pv c2c4
ok depth 1 MultiPV 3 returns three lines
ok the three lines are distinct legal root moves
ok depth-1 lines are ordered by score
ok info prints multipv 1 before score
ok info prints multipv 2 before score
ok info prints multipv 3 before score
ok MultiPV 3 does not print a fourth line
depth1-multipv100 best d2d4 score 1 nodes 161 lines 8
  1 score 1 pv d2d4
  2 score 1 pv g1f3
  3 score -10 pv c2c4
  4 score -11 pv e2e4
  5 score -15 pv h2h3
  6 score -16 pv e2e3
  7 score -16 pv b1c3
  8 score -20 pv d2d3
ok MultiPV above 8 is clamped to 8
ok the eight lines are distinct legal root moves
depth3-multipv2 best e2e4 score 18 nodes 278 lines 2
  1 score 18 pv e2e4 h7h6 d2d4
  2 score 18 pv d2d4 h7h6 e2e4
ok the result keeps the last depth's lines
ok both last-depth lines are legal root moves
cramped legal 3
  h8g7
  h8h7
  h8g8
cramped-multipv8 best h8h7 score -97 nodes 10 lines 3
  1 score -97 pv h8h7
  2 score -105 pv h8g7
  3 score -109 pv h8g8
ok the cramped fen parses
ok the cramped position has fewer than 8 legal moves
ok MultiPV stops when the legal root moves run out
ok every legal root move is one of the lines
failures=0
```

Exit status 0. The sanitizer printed no error.

## What was not verified

- `Threads` greater than 1 together with `MultiPV` greater than 1. Extra lines run only on the main worker. Helper threads still search one line and share the transposition table. That mix was not run.
- A clock-limited game with `MultiPV` greater than 1. The extra lines search more nodes after a finished iteration, so they use time. `MultiPV` 1 leaves the clock path as it was. No timed game was played.
- The first line of a `MultiPV` greater than 1 search at depths after 1 against a `MultiPV` 1 search of the same position. The extra searches write child transposition-table entries and history before the next depth, so a later first line can differ. At depth 1 the measured first line matches the single-PV search (`d2d4`, 26 nodes).
- Elo and speed. The `nps` numbers above are wall-clock readings from these runs, not a speed claim.
