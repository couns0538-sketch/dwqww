# Task t15: UCI MultiPV

## What was there

The locked engine printed one principal variation. `uci` had no `MultiPV` option. A finished depth was one line:

`info depth D seldepth S score ... nodes ... nps ... hashfull ... time ... pv ...`

`bestmove` was that line's first move.

Before any edit, with Threads 1, Hash 16 and OwnBook false, the lock binary printed bench 11 = 312866 nodes, bench 13 = 862329 nodes, and `go perft 5` from the start position = 4865609 nodes. Clang 18 could not link a test program: it selected GCC 14, and that directory has no `libstdc++.so`. The engine was built with g++ 13.3.0. The CPU has AVX-512. The build still used the portable flags from the start command (`-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`). Those three node counts matched the lock.

## The change

`MultiPV` is a UCI spin option, minimum 1, maximum 8, default 1, listed in the `uci` answer. At 1 the iterative deepening and the info text are the previous ones. Above 1, each finished depth keeps that primary line and then searches the remaining root moves on a separate table, removing the moves already chosen; each of those searches runs to the same depth with a resolved window, so the score is exact. The lines are printed best score first as `info depth D multipv i score ... pv ...`, and `bestmove` is the move of line 1. If fewer than `k` legal moves exist, only those moves are printed.

With `MultiPV` above 1, helper threads are not started and the main thread owns the transposition table the way a one-thread search does. `Threads` greater than 1 therefore follows the Threads 1 search. The node limit and the clock limit stop the primary iterative deepening. An extra line of a depth that already finished is searched to that depth on its own table, so a `go nodes` total can be larger than the limit. A stop flag is checked between extra lines.

Line 1 is the highest of those exact scores. The MultiPV 1 move is the iterative-deepening best move and stays in the set. A fresh search of a later line can score higher than that iterative-deepening score, so the ranked first move is not always the MultiPV 1 move. The test records each such depth.

Engine diff against the lock: 143 insertions and 11 deletions in `src` and `include` (`git diff --numstat`), under the 300-line cap.

## Files changed

- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/src/search.cpp`
- `forge-combo29/src/uci.cpp`
- `forge-combo29/tests_t15/test_multipv.cpp`
- `forge-combo29/tests_t15/depth12_lock.txt`
- `forge-combo29/REPORT_t15.md`

`depth12_lock.txt` is the lock binary's `go depth 12` transcript for the five positions below, captured before the edit.

## Build

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++
cmake --build build -j
```

The first configure, without `CMAKE_CXX_COMPILER=g++`, failed while linking the compiler test (`/usr/bin/ld: cannot find -lstdc++`). The g++ configure and build ended with `Built target forge` and exit code 0.

## Before the edit

Command:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 437 nps 1973292
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

Exit code 0. bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

## After the edit: the three numbers

Same command, same binary path after the rebuild:

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 442 nps 1950970
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

Exit code 0. bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. Per-move perft counts match the run above. `time` and `nps` are wall clock.

`uci` on this binary prints `option name MultiPV type spin default 1 min 1 max 8` and then `uciok`.

## Tests

The five depth-12 positions, in order, are the start position, `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`, `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8`, `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1`, and `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1`. The test compares that transcript with the lock file after replacing the `nps` and `time` numbers. It also checks ten positions at `MultiPV 4`, `go depth 8`, a position with two legal moves (`8/8/8/8/8/6k1/6r1/6K1 w - - 0 1`) at `MultiPV 4`, a mate in 1 (`6k1/5ppp/8/8/8/8/8/R6K w - - 0 1`), `go nodes 4000`, `go movetime 80`, and Threads 4 against Threads 1 at `MultiPV 3`, depth 4.

Command, from `/agent/repos/dwqww`:

```
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t15/test_multipv.cpp -pthread -o /tmp/test_t15
/tmp/test_t15
```

The compiler printed nothing and exited 0. Test output:

```
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
EXPLAIN b startpos depth 5 line 1 is e2e4 and MultiPV 1 is c2c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 5 line 1 is d5e6 and MultiPV 1 is e2a6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 7 line 1 is e2a6 and MultiPV 1 is d5e6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 4 line 1 is c1b1 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 6 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 7 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 4 line 1 is a5a6 and MultiPV 1 is b4c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 7 line 1 is a5a6 and MultiPV 1 is b4f4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 6 line 1 is a2a3 and MultiPV 1 is f1e2. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 8 line 1 is c4c5 and MultiPV 1 is a2a3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 5 line 1 is f6e8 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 7 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 8 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 5 line 1 is g7g5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 7 line 1 is g7g6 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 8 line 1 is f7f5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 4 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 5 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 6 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 depth 6 line 1 is h2h3 and MultiPV 1 is c3d5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
PASS b checked 10 positions at depth 8
PASS c two legal moves
PASS d mate in 1 line a1a8 mate 1
PASS nodes best d2d4
PASS movetime best d2d4
PASS threads 4 falls back to threads 1
explained 20
failures 0
RESULT passed
```

Exit code 0. At depth 8, line 1 differed from the separate MultiPV 1 search on three of the ten positions: `c4c5` instead of `a2a3`, `g3g6` instead of `f6h5`, and `f7f5` instead of `h7h5`. In each case the MultiPV 1 move was still one of the four lines. The mate in 1 line was `a1a8` with `score mate 1`. The two-move position printed two lines.

## Sanitizers

Command, from `/agent/repos/dwqww`:

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t15/test_multipv.cpp -pthread -o /tmp/test_t15_asan
/tmp/test_t15_asan
```

The compiler printed nothing and exited 0. Test output:

```
PASS a depth 12 info matches the lock except time and nps
PASS a bestmoves match the lock
EXPLAIN b startpos depth 5 line 1 is e2e4 and MultiPV 1 is c2c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 5 line 1 is d5e6 and MultiPV 1 is e2a6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1 depth 7 line 1 is e2a6 and MultiPV 1 is d5e6. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 4 line 1 is c1b1 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 6 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10 depth 7 line 1 is c3d5 and MultiPV 1 is h2h3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 4 line 1 is a5a6 and MultiPV 1 is b4c4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1 depth 7 line 1 is a5a6 and MultiPV 1 is b4f4. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 6 line 1 is a2a3 and MultiPV 1 is f1e2. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8 depth 8 line 1 is c4c5 and MultiPV 1 is a2a3. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 5 line 1 is f6e8 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 7 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1 depth 8 line 1 is g3g6 and MultiPV 1 is f6h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 5 line 1 is g7g5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 7 line 1 is g7g6 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b 6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1 depth 8 line 1 is f7f5 and MultiPV 1 is h7h5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 4 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 5 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8 depth 6 line 1 is d7c8r and MultiPV 1 is d7c8q. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
EXPLAIN b r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 depth 6 line 1 is h2h3 and MultiPV 1 is c3d5. Line 1 is the highest exact score. The other lines are fresh searches with earlier root moves removed, so one of them can outscore the iterative-deepening result. The MultiPV 1 move is still in the set.
PASS b checked 10 positions at depth 8
PASS c two legal moves
PASS d mate in 1 line a1a8 mate 1
PASS nodes best d2d4
PASS movetime best d2d4
PASS threads 4 falls back to threads 1
explained 20
failures 0
RESULT passed
```

Exit code 0. AddressSanitizer and UndefinedBehaviorSanitizer printed no error.

## Not verified

- `ponder` and `go infinite` together with `MultiPV` above 1.
- `wtime` / `btime` game clocks with `MultiPV` above 1. `go movetime 80` was run.
- `MultiPV` together with `searchmoves` or `go mate`.
- A `stop` that arrives while an extra line is searching. The flag is read between extra lines.
- A malformed `MultiPV` value, and values other than the ones the tests set (1, 3 and 4). The option clamps to 1..8.
- Hash sizes other than 16 MB for a `MultiPV` search.
- A GUI reading the lines.
- The node budget covering the extra lines. The limit stops the primary search; each extra line is a separate search to the depth that just finished.
