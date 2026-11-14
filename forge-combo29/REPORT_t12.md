# t12: two-thread KRK mate miss

## What was found

With `Threads 2`, a depth-14 search of king and rook against king sometimes returns a centipawn score for a position that a `Threads 1` search mates. The miss is concentrated on longer mates. On `8/8/8/2R5/8/8/1k6/3K4 w - - 0 1` (mate 10, `d1d2`, score 31981 with one thread) the unchanged engine missed the mate score in 8 of 400 searches and again in 6 of 400. The 40-position test at 10 repeats is near the edge of that rate: one unchanged run missed 1 of 400, and a run at 40 repeats missed 1 of 1600. Both misses were that same position, a centipawn score on `d1d2`.

The shared hash table is the only search state the workers share. Two stores were wrong.

1. Replacement. A proved mate was replaced by a shallower store that does not prove mate. Bound 2 is a lower bound and bound 1 is an upper bound. A positive mate is proved only by a lower or exact bound. This entry was logged on the unchanged engine, then overwritten:

```
REPLACE 00 before depth 4 score 31997 bound 2 move d1c2 | incoming depth 1 score 451 bound 1 move a1a1
```

Depth 4 held a proved mate (31997, lower bound, `d1c2`). The incoming store is one ply deep, a centipawn upper bound, and an empty move (`a1a1` is from = to = 0). The old rule replaces the score when `depth + 4 > entry.depth`, so 1 + 4 > 4 and the mate is gone. The same log shows a depth-10 proof replaced by a depth-9 upper bound:

```
REPLACE 04 before depth 10 score 31987 bound 2 move d3c3 | incoming depth 9 score 31996 bound 1 move a1a1
```

An upper bound of a positive mate does not prove the mate (`score <= 31996` is true of ordinary scores too).

2. Cutoff. A non-mate bound stored by the other thread at the same depth was treated as proved. During the same unchanged run:

```
CUT ply 2 depth 13 tt_depth 13 score 442 bound 1 move a1a1 fen 8/8/8/1R6/8/2k5/8/3K4 w - - 2 2
```

The node is depth 13 and the table entry is depth 13. The upper bound 442 cuts the node off. The root then accepts a centipawn score for `d1d2` instead of the mate. One thread does not do this to itself often enough to miss; the second thread's iteration supplies the bound.

Other candidates, and why they are not the cause:

- A torn read (key from one position, data from another) does not fit the locked path. With two or more workers every probe and store holds the stripe mutex across the whole entry. The exclusive, unlocked path is taken only for one worker. Misses still happened on that locked path.
- Mate scores are already adjusted by ply on every store (`score_to_tt`) and every read (`score_from_tt`). The distances in the log fit that adjustment.
- A node that sees `stop` returns 0 before it stores. These searches are depth-limited, so `stop` is set only after the main worker has returned.
- Storing every non-mate upper bound one ply shallower, to discount pruned and reduced moves, made the hard position worse (3 of 400 on one run). Helpers' ordinary centipawn bounds are needed to find the mate. The bad event is a bound used at a depth the other thread has not finished proving.

Preserving proved mates without the cutoff change still left misses. The cutoff change is what dropped the hard position from 8 of 400 to 0 of 2000. Both changes are in the tree. Neither turns off hash sharing, clears history, lowers the thread count, or locks the whole search. Helpers still write and read the table.

## The change

While more than one worker is searching, a proved mate is kept against a shallower store and against a same-depth store that is not exact and does not itself prove mate. A deeper store, or a same-depth exact result, may still replace it. In that same multi-worker search, a non-mate table cutoff is used only when the stored depth is at least two plies deeper than the node; a mate cutoff is unchanged. One worker leaves both rules as they were, which is why `bench 11`, `bench 13`, and `go perft 5` stay on the lock's node counts. `FORGE_T12_MATE_TT` defaults to 1; 0 compiles the lock's replacement and cutoff.

## Files changed

- `forge-combo29/src/search.cpp`
- `forge-combo29/include/forge/search.hpp`
- `forge-combo29/tests_t12/krk_mate_test.cpp` (new)
- `forge-combo29/REPORT_t12.md` (this file)

Engine diff: 40 insertions, 5 deletions. No existing check was removed.

## Counts

Unchanged lock, `Threads 2`, `Hash 16`, depth 14, fresh hash each search:

| Run | Misses |
| --- | --- |
| 40 positions × 10 | 0, then 1, then 0 (the 1 was `8/8/8/2R5/8/8/1k6/3K4`, run 2, `cp 445 d1d2`) |
| 40 positions × 40 | 1 of 1600 (same position, run 7, `cp 476 d1d2`) |
| that position × 400 | 8, and a later run 6 |

Same tests after the change:

| Run | Misses |
| --- | --- |
| 40 × 10, three times | 0, 0, 0 |
| 40 × 40, three times | 0, 0, 0 |
| that position × 2000 | 0 |
| address and undefined sanitizers, 40 × 10 | 0, no sanitizer report |

`Threads 1`, `Hash 16`, `OwnBook false` after the change: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

## Commands and output

The test program links the engine sources and drives `Searcher` directly. It keeps 40 legal KRK positions whose one-thread depth-14 search returns a positive mate and whose move still mates in a depth-18 search of the reply, then searches each with two threads. A miss is a non-mate score, or a move that does not mate at depth 18. Depth 18 is required because `d1e2` in the mate-10 position really mates, and a depth-14 reply search still returns a centipawn score for it.

### Reference counts after the change

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j4
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

```
info string bench depth 11 nodes 312866 time 237 nps 1320109
info string bench depth 13 nodes 862329 time 576 nps 1497098
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

The same three node counts were printed by this command on the lock before any engine edit.

### Unchanged engine, 40 × 10

The binary was the lock's `search.cpp` plus `tests_t12/krk_mate_test.cpp`. Three runs, filtered to the miss lines. The position list is the same one printed in full in the after-change run below.

```
/tmp/t12/krk_lock 2 16 10 40
```

```
runs 400
misses 0
score_misses 0
move_misses 0

miss 8/8/8/2R5/8/8/1k6/3K4 w - - 0 1 run 2 cp 445 d1d2 no-mate-score
runs 400
misses 1
score_misses 1
move_misses 0

runs 400
misses 0
score_misses 0
move_misses 0
```

A later full run of the same command was 0 of 400. At 10 repeats the miss is not in every sample, so the load was raised.

### Unchanged engine, 40 × 40

```
/tmp/t12/krk_lock 2 16 40 40
```

```
settings threads 2 hash_mb 16 runs 40 target 40 depth 14
candidates 10987
t1 8/8/8/8/8/8/1k6/3KR3 w - - 0 1 mate 5 e1e3
t1 8/8/8/8/8/8/1k6/3K1R2 w - - 0 1 mate 5 f1f3
t1 8/8/8/8/8/8/1k6/3K2R1 w - - 0 1 mate 5 g1g3
t1 8/8/8/8/8/8/1k6/3K3R w - - 0 1 mate 5 h1h3
t1 8/8/8/8/8/3R4/1k6/3K4 w - - 0 1 mate 5 d3e3
t1 8/8/8/8/8/4R3/1k6/3K4 w - - 0 1 mate 5 e3f3
t1 8/8/8/8/8/5R2/1k6/3K4 w - - 0 1 mate 5 f3d3
t1 8/8/8/8/8/6R1/1k6/3K4 w - - 0 1 mate 5 g3h3
t1 8/8/8/8/8/7R/1k6/3K4 w - - 0 1 mate 5 d1d2
t1 8/8/8/8/R7/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/2R5/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/3R4/8/1k6/3K4 w - - 0 1 mate 5 d4d3
t1 8/8/8/8/4R3/8/1k6/3K4 w - - 0 1 mate 5 e4e3
t1 8/8/8/8/5R2/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/6R1/8/1k6/3K4 w - - 0 1 mate 5 g4g3
t1 8/8/8/8/7R/8/1k6/3K4 w - - 0 1 mate 5 h4h3
t1 8/8/8/2R5/8/8/1k6/3K4 w - - 0 1 mate 10 d1d2
t1 8/8/8/3R4/8/8/1k6/3K4 w - - 0 1 mate 5 d5d3
t1 8/8/8/4R3/8/8/1k6/3K4 w - - 0 1 mate 5 e5e3
t1 8/8/8/5R2/8/8/1k6/3K4 w - - 0 1 mate 5 f5f3
t1 8/8/8/6R1/8/8/1k6/3K4 w - - 0 1 mate 5 g5g3
t1 8/8/8/7R/8/8/1k6/3K4 w - - 0 1 mate 5 h5h3
progress examined 25 mates 22
t1 8/8/3R4/8/8/8/1k6/3K4 w - - 0 1 mate 5 d6d3
t1 8/8/4R3/8/8/8/1k6/3K4 w - - 0 1 mate 5 e6e3
t1 8/8/5R2/8/8/8/1k6/3K4 w - - 0 1 mate 5 f6f3
t1 8/8/6R1/8/8/8/1k6/3K4 w - - 0 1 mate 5 g6g3
t1 8/8/7R/8/8/8/1k6/3K4 w - - 0 1 mate 5 h6h3
t1 8/3R4/8/8/8/8/1k6/3K4 w - - 0 1 mate 8 d1d2
t1 8/4R3/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 e7e3
t1 8/5R2/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 f7f3
t1 8/6R1/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 g7g3
t1 8/7R/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 h7h3
t1 3R4/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 d8d3
t1 4R3/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 e8e3
t1 5R2/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 f8f3
t1 6R1/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 g8g3
t1 7R/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 h8h3
t1 8/8/8/8/8/8/1k6/4KR2 w - - 0 1 mate 7 e1d2
t1 8/8/8/8/8/8/1k6/4K1R1 w - - 0 1 mate 7 e1d2
t1 8/8/8/8/8/8/1k6/4K2R w - - 0 1 mate 7 e1d2
examined 49
t1_mates 40
miss 8/8/8/2R5/8/8/1k6/3K4 w - - 0 1 run 7 cp 476 d1d2 no-mate-score
runs 1600
misses 1
score_misses 1
move_misses 0
```

### Unchanged engine, the mate-10 position alone

A separate driver, not part of the commit, searched only `8/8/8/2R5/8/8/1k6/3K4 w - - 0 1` at depth 14 with two threads and a fresh 16 MB hash, and counted results that were not a positive mate score.

```
T12_LABEL=lock /tmp/t12/exp_lock 400 2
```

```
lock score_misses 8 / 400
```

Repeated later:

```
lock score_misses 6 / 400
```

### Logged entry, unchanged engine

The `REPLACE` and `CUT` lines were printed by a temporary copy of the lock's `search.cpp` (logging only, compiled outside the repo). The committed sources have no logging. Two hundred searches of the mate-10 position, two threads, hash 16, depth 14:

```
log score_misses 1 / 200
```

```
REPLACE 00 before depth 4 score 31997 bound 2 move d1c2 | incoming depth 1 score 451 bound 1 move a1a1
CUT ply 1 depth 11 tt_depth 11 score -447 bound 2 move b2c3 fen 8/8/8/1R6/8/8/1k6/3K4 b - - 1 1
CUT ply 1 depth 11 tt_depth 11 score -447 bound 2 move b2b3 fen 8/8/8/8/8/8/1kR5/3K4 b - - 1 1
CUT ply 2 depth 11 tt_depth 11 score 442 bound 2 move d2c3 fen 8/8/8/2R5/8/k7/3K4/8 w - - 2 2
CUT ply 1 depth 12 tt_depth 12 score -430 bound 2 move b2b3 fen 8/8/8/8/8/8/1kR5/3K4 b - - 1 1
CUT ply 2 depth 13 tt_depth 13 score 442 bound 1 move a1a1 fen 8/8/8/1R6/8/2k5/8/3K4 w - - 2 2
CUT ply 1 depth 12 tt_depth 12 score -430 bound 2 move b2c3 fen 8/8/8/7R/8/8/1k6/3K4 b - - 1 1
CUT ply 2 depth 11 tt_depth 11 score 442 bound 1 move d1d2 fen 8/2R5/8/8/8/1k6/8/3K4 w - - 2 2
CUT ply 2 depth 12 tt_depth 12 score 473 bound 2 move d2c3 fen 8/8/8/2R5/8/k7/3K4/8 w - - 2 2
REPLACE 01 before depth 7 score -31990 bound 1 move a2b1 | incoming depth 6 score -31999 bound 2 move a2b1
REPLACE 02 before depth 9 score 31989 bound 2 move b5c5 | incoming depth 7 score 31998 bound 1 move a1a1
REPLACE 03 before depth 10 score -31988 bound 1 move a3a2 | incoming depth 8 score -31997 bound 2 move a3a2
REPLACE 04 before depth 10 score 31987 bound 2 move d3c3 | incoming depth 9 score 31996 bound 1 move a1a1
REPLACE 05 before depth 6 score 31997 bound 2 move h5h4 | incoming depth 0 score 31997 bound 1 move a1a1
REPLACE 06 before depth 5 score 31993 bound 2 move a5h5 | incoming depth 1 score 0 bound 1 move a1a1
REPLACE 07 before depth 5 score 31993 bound 2 move a5h5 | incoming depth 4 score 31993 bound 1 move a1a1
REPLACE 08 before depth 6 score -31992 bound 1 move a1a1 | incoming depth 5 score -31992 bound 2 move a1b1
REPLACE 09 before depth 6 score 31991 bound 2 move c5a5 | incoming depth 5 score 31991 bound 1 move a1a1
REPLACE 10 before depth 6 score 31997 bound 2 move h5h4 | incoming depth 0 score 31997 bound 1 move a1a1
REPLACE 11 before depth 7 score 31997 bound 2 move b1b3 | incoming depth 0 score 31997 bound 1 move a1a1
```

### After the change, 40 × 10, three times

```
/tmp/t12/krk_after 2 16 10 40
```

First run, in full. The second and third runs were byte-identical (`diff -q` printed nothing).

```
settings threads 2 hash_mb 16 runs 10 target 40 depth 14
candidates 10987
t1 8/8/8/8/8/8/1k6/3KR3 w - - 0 1 mate 5 e1e3
t1 8/8/8/8/8/8/1k6/3K1R2 w - - 0 1 mate 5 f1f3
t1 8/8/8/8/8/8/1k6/3K2R1 w - - 0 1 mate 5 g1g3
t1 8/8/8/8/8/8/1k6/3K3R w - - 0 1 mate 5 h1h3
t1 8/8/8/8/8/3R4/1k6/3K4 w - - 0 1 mate 5 d3e3
t1 8/8/8/8/8/4R3/1k6/3K4 w - - 0 1 mate 5 e3f3
t1 8/8/8/8/8/5R2/1k6/3K4 w - - 0 1 mate 5 f3d3
t1 8/8/8/8/8/6R1/1k6/3K4 w - - 0 1 mate 5 g3h3
t1 8/8/8/8/8/7R/1k6/3K4 w - - 0 1 mate 5 d1d2
t1 8/8/8/8/R7/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/2R5/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/3R4/8/1k6/3K4 w - - 0 1 mate 5 d4d3
t1 8/8/8/8/4R3/8/1k6/3K4 w - - 0 1 mate 5 e4e3
t1 8/8/8/8/5R2/8/1k6/3K4 w - - 0 1 mate 7 d1d2
t1 8/8/8/8/6R1/8/1k6/3K4 w - - 0 1 mate 5 g4g3
t1 8/8/8/8/7R/8/1k6/3K4 w - - 0 1 mate 5 h4h3
t1 8/8/8/2R5/8/8/1k6/3K4 w - - 0 1 mate 10 d1d2
t1 8/8/8/3R4/8/8/1k6/3K4 w - - 0 1 mate 5 d5d3
t1 8/8/8/4R3/8/8/1k6/3K4 w - - 0 1 mate 5 e5e3
t1 8/8/8/5R2/8/8/1k6/3K4 w - - 0 1 mate 5 f5f3
t1 8/8/8/6R1/8/8/1k6/3K4 w - - 0 1 mate 5 g5g3
t1 8/8/8/7R/8/8/1k6/3K4 w - - 0 1 mate 5 h5h3
progress examined 25 mates 22
t1 8/8/3R4/8/8/8/1k6/3K4 w - - 0 1 mate 5 d6d3
t1 8/8/4R3/8/8/8/1k6/3K4 w - - 0 1 mate 5 e6e3
t1 8/8/5R2/8/8/8/1k6/3K4 w - - 0 1 mate 5 f6f3
t1 8/8/6R1/8/8/8/1k6/3K4 w - - 0 1 mate 5 g6g3
t1 8/8/7R/8/8/8/1k6/3K4 w - - 0 1 mate 5 h6h3
t1 8/3R4/8/8/8/8/1k6/3K4 w - - 0 1 mate 8 d1d2
t1 8/4R3/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 e7e3
t1 8/5R2/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 f7f3
t1 8/6R1/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 g7g3
t1 8/7R/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 h7h3
t1 3R4/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 d8d3
t1 4R3/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 e8e3
t1 5R2/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 f8f3
t1 6R1/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 g8g3
t1 7R/8/8/8/8/8/1k6/3K4 w - - 0 1 mate 5 h8h3
t1 8/8/8/8/8/8/1k6/4KR2 w - - 0 1 mate 7 e1d2
t1 8/8/8/8/8/8/1k6/4K1R1 w - - 0 1 mate 7 e1d2
t1 8/8/8/8/8/8/1k6/4K2R w - - 0 1 mate 7 e1d2
examined 49
t1_mates 40
runs 400
misses 0
score_misses 0
move_misses 0
```

### After the change, 40 × 40, three times

```
/tmp/t12/krk_after 2 16 40 40
```

Each run printed the same position list as above, then:

```
examined 49
t1_mates 40
runs 1600
misses 0
score_misses 0
move_misses 0
```

The three stdout files were byte-identical.

### After the change, the mate-10 position × 2000

```
T12_LABEL=more /tmp/t12/exp_after 2000 2
```

```
more score_misses 0 / 2000
```

### Sanitizers

```
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include -c forge-combo29/src/search.cpp forge-combo29/src/nnue.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/bitboard.cpp forge-combo29/tests_t12/krk_mate_test.cpp
g++ -O1 -g -fsanitize=address,undefined search.o nnue.o board.o book.o eval.o eval_params.o bitboard.o krk_mate_test.o -pthread -o /tmp/t12/krk_asan
/tmp/t12/krk_asan 2 16 10 40
```

Stdout was byte-identical to the release 40 × 10 listing above (`misses 0`). Stderr was empty (0 bytes). Exit status 0.

## Review follow-up

Four review notes, and what changed.

The test now returns 1 when `misses` is not 0, and 0 when it is. The three repeats below exited 0.

`FORGE_T12_MATE_TT` defaults to 1. Setting it to 0 compiles the lock replacement (`keep` is false) and the lock cutoff (`tt_need` is `depth`). The default is 1, not 0: the build file cannot be edited, and a default of 0 would leave the miss in the engine this task has to fix. One worker is the lock path either way. With the switch off, the mate-10 position missed 10 of 400. With it on, the counts below are 0.

A same-depth exact result may replace a one-sided mate bound. A same-depth upper or lower bound that does not prove mate still cannot. The mate-10 position stayed at 0 of 400 after that change, and the 40-position test stayed at 0 of 400 three times.

`protect_mates_` is an atomic flag. The search releases it when the flag is set and acquires it in `keep_proved_mate`, so a store that overlaps the end of the search does not race the restore.

```
T12_LABEL=h /tmp/t12/exp_after 400 2
```

```
h score_misses 0 / 400
```

```
/tmp/t12/krk_after 2 16 10 40
```

Three runs, each exit 0:

```
runs 400
misses 0
score_misses 0
move_misses 0
```

```
T12_LABEL=off /tmp/t12/exp_off 400 2
```

```
off score_misses 10 / 400
```

Reference counts after this follow-up, same command as above:

```
info string bench depth 11 nodes 312866 time 185 nps 1691167
info string bench depth 13 nodes 862329 time 506 nps 1704207
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

Address and undefined sanitizers, same test, after this follow-up: stdout ended in `misses 0`, stderr was empty, exit 0.

## What could not be verified

- ThreadSanitizer was not run on the final sources. The two-worker path holds the stripe mutex for each probe and store; that is why a torn entry is not the cause named above, and it is not a sanitizer result.
- Thread counts other than 1 (the reference command) and 2 (the mate test).
- KRK positions outside the 40 the test kept, and mates longer than those positions.
- A clocked search, or any strength or speed comparison.
