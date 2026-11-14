# t12: two-thread KRK mate miss

This file is the account of the bug. The command logs that support it are further down.

## What was wrong

Two workers search the same root and write one hash table. Each worker has its own history tables. The table is the only search result they share. With one worker the mate is stable. With two workers a depth-14 search of a long king-and-rook mate sometimes returns a centipawn score, or a mate score on a move that does not mate that fast.

The position that shows it is:

```
8/8/8/2R5/8/8/1k6/3K4 w - - 0 1
```

White king d1, black king b2, white rook c5. One thread, depth 14, hash 16, returns score 31981 and move `d1d2`. Score 31981 is mate in 10: mate scores use 32000, the distance in plies is `32000 - |score|`, and the move count is `(distance + 1) / 2`. Here the distance is 19 plies, which is mate in 10. Two threads, same limit, sometimes return about +450 to +480 centipawns for `d1d2` instead.

A hash entry is 16 bytes: position key, move, score, static eval, depth, and a packed generation/bound byte. The bound is the low 2 bits.

| Value | Bound | Meaning |
| --- | --- | --- |
| 0 | none | empty |
| 1 | upper | the true score is at most the stored score |
| 2 | lower | the true score is at least the stored score |
| 3 | exact | the true score is the stored score |

A mate score is any score at or outside 31872 (`32000 - 128`). That number is a mate only when the bound points the right way.

- Side to move can force mate: score `>= 31872` and the bound is lower or exact.
- Side to move is getting mated: score `<= -31872` and the bound is upper or exact.

An upper bound of `31996` does not prove a mate. It says the score is at most 31996, which is also true of an ordinary centipawn score. A lower bound of a large negative mate has the same problem in the other direction.

The lock's store does two things, and they are separate. First, if the incoming move is not empty, or the entry is a different position, it writes the move. Second, it replaces the score, depth, and bound when any of these is true: the new bound is exact, the position differs, the new depth is greater than the old depth minus 4 (`depth + 4 > entry.depth`), or the generation differs. A store three plies shallower therefore overwrites a deeper entry. An exact store overwrites any depth.

That rule is what deletes the mate. These two lines were logged on the unchanged engine, on the position above, before the incoming store was written. Bound 2 is lower. Bound 1 is upper. `a1a1` is the empty move (from and to are both square 0); an empty move does not overwrite a saved move when the position matches, but the score and bound still change.

```
REPLACE 00 before depth 4 score 31997 bound 2 move d1c2 | incoming depth 1 score 451 bound 1 move a1a1
```

Before the store the entry is a proved mate: depth 4, score 31997 (mate distance 3), lower bound, move `d1c2`. The incoming store is depth 1, score 451, upper bound. `1 + 4 > 4`, so the lock replaces the entry. After the store the table says depth 1, score 451, upper bound. The mate proof is gone.

```
REPLACE 04 before depth 10 score 31987 bound 2 move d3c3 | incoming depth 9 score 31996 bound 1 move a1a1
```

Before the store: depth 10, score 31987, lower bound, move `d3c3`. That is a proved mate. The incoming score 31996 looks like a mate, but the bound is upper, so it is not a proof. `9 + 4 > 10`, so it replaces the proof anyway. After the store the table says "score is at most 31996" at depth 9. A later search can treat that as an ordinary bound and never play the mating move.

The second fault is the cutoff, not the replacement. A non-PV node returns the table score immediately when the stored depth is at least the depth being searched, the halfmove clock is under 90, and the bound agrees with the window: exact, or a lower bound at least beta, or an upper bound at most alpha. Both workers use that rule on entries the other worker just wrote.

```
CUT ply 2 depth 13 tt_depth 13 score 442 bound 1 move a1a1 fen 8/8/8/1R6/8/2k5/8/3K4 w - - 2 2
```

This node is depth 13, two plies under a depth-14 root. The table entry is also depth 13. The bound is upper and the score is 442. When alpha is at least 442 the node returns 442 and does not search. The mating line is then worth about 442 centipawns. The root is searching an aspiration window around the previous centipawn score (one logged miss had alpha 465 and beta 501, and `d1d2` scored 475 inside that window). The iteration accepts 475. It never opens the window out to a mate.

One thread does not hit this often enough to miss. Its own depth-13 search finds the mate, so depth 14 starts inside a mate window and returns 31981, `d1d2`. The second thread is the extra writer. It is on its own iterative deepening of the same root, with different move ordering, and it stores a centipawn bound at the depth the first thread is still searching. The first thread then cuts off on that bound. Stopping the helper from writing the table made the miss worse, so the helper's entries are useful. The fault is trusting a centipawn bound at a depth the other thread has not finished.

Short mates (mate in 1 to 5) almost never miss at depth 14. The search proves them before the bad entry matters. The miss needs a mate near the horizon, which is why it shows up on this mate in 10.

## What was found

The test builds at least 40 legal KRK positions whose one-thread depth-14 search returns a positive mate, and whose move still mates in a depth-18 search of the reply. It then searches each position with two threads, hash 16, depth 14, and a cleared table every time. A miss is a non-mate score, or a move that does not mate at depth 18. The reply is searched at 18 because `d1e2` in the position above really does mate, and a depth-14 search of the reply still returns a centipawn score. Calling that a non-mating move would be a bad test, not an engine miss.

On the unchanged lock, two threads, hash 16, depth 14:

| Run | Misses |
| --- | --- |
| 40 positions × 10 | 0, then 1, then 0. The one miss was the mate-10 position, run 2, `cp 445 d1d2` |
| 40 positions × 40 | 1 of 1600, same position, run 7, `cp 476 d1d2` |
| that position alone × 400 | 8, and a later run 6 |
| that position × 200, with the store/cutoff log | 1, and the `REPLACE` / `CUT` lines above |

Ten repeats of 40 positions is only 10 tries at the one hard position, so a run can be 0. Forty repeats of that position alone is where the miss is obvious.

These were checked and are not the cause.

- Torn read. With two or more workers every probe and every store holds the stripe mutex for the whole entry. The unlocked path is used only when one worker is searching. The miss happens on the locked path, so the key and the data are not coming from two positions.
- Missing ply adjustment. Every store goes through `score_to_tt` and every read through `score_from_tt`. A positive mate is stored as `score + ply` and read back as `score - ply`. The distances in the log match that. Nothing in the log is a mate that overflowed the 16-bit score.
- A search cut off by `stop`. A node that sees the stop flag returns 0 and does not store. These runs are depth-limited. The stop flag is set only after the main worker has already returned its result.
- "Do not store a pruned upper bound." Saving every non-mate upper bound one ply shallower, so a reduced or pruned child could not look fully searched, made the hard position worse: 3 of 400 on one run. The ordinary centipawn bounds are how the search finds the mate. The bad event is using one at a depth the other thread has not proved.
- Keeping the mate proof and leaving the cutoff alone. The mate still disappeared. The same-depth centipawn cutoff was still enough to make the root return a centipawn score.
- Full-window search, with aspiration turned off for two threads. The root still sometimes scored `d1d2` as a centipawn value. The window is how a centipawn result gets accepted. It is not what makes the tree return that value.
- Helper threads not writing the table. That is the earlier rejected change. It threw away useful entries and the miss got worse.

Preserving the proved mate and refusing a non-mate cutoff unless the entry is at least two plies deeper is the pair that removed the miss. Mate cutoffs are unchanged, so a real mate still cuts off at the depth it was stored.

## What changed

`forge-combo29/src/search.cpp` and `forge-combo29/include/forge/search.hpp`.

While more than one worker is searching, `keep_proved_mate` refuses a store that would erase a proved mate. A shallower store is refused. A same-depth store is refused when it is not exact and does not itself prove mate. A deeper store may replace the mate, so a wrong mate can still be corrected. A same-depth exact score may also replace it, because that search finished inside its window. The flag that turns this on is `protect_mates_`. It is set before the workers start and cleared after they join. It is atomic: a store that overlaps the end of the search loads it with acquire, and the search stores it with release.

In the same multi-worker search, a non-mate cutoff requires `tt_depth >= depth + 2` instead of `tt_depth >= depth`. A mate score still cuts off at `tt_depth >= depth`. One worker uses `tt_depth >= depth` and does not set `protect_mates_`, so its replacement and cutoff are the lock's. That is why `bench 11`, `bench 13`, and `go perft 5` stay on the lock's node counts.

`FORGE_T12_MATE_TT` defaults to 1. Compiling with `-DFORGE_T12_MATE_TT=0` forces `keep` false and `tt_need = depth`, which is the lock. The default is 1 because this change cannot edit the build file, and a default of 0 would leave the miss in the built engine. With the switch off, the mate-10 position missed 10 of 400. With it on, the counts below are 0.

Helpers still read the table and still write it. Nothing clears history or correction tables. The thread count is not lowered inside the engine. There is no sleep and no lock around the whole search.

`forge-combo29/tests_t12/krk_mate_test.cpp` is the program that builds the 40 positions and counts the misses. It returns 1 when the miss count is not 0.

`Threads 1`, `Hash 16`, `OwnBook false` after the change: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

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
