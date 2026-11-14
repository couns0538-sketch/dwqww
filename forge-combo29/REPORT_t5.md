# Task 5: two-thread KRK mate, and stale history

This is the account of what was wrong on the lock `16833ecc`, what the runs showed, and what this branch changes. The command log below is the evidence. Nothing here is an Elo or speed claim.

## What was wrong

Two separate faults. Both show up in king-and-rook endings at depth 14. A third fault showed up after the first fix: helper threads that no longer write the table were still spending a node-limited search's budget.

### 1. Two threads overwrite the mate in the shared table

`Searcher::search` starts one helper thread per worker after the main worker. Each helper gets its own copy of the board and searches the same position. They share one transposition table. On the lock, every worker stores into that table, and a probe that hits refreshes the entry's generation under the stripe lock.

A node stores one of three bounds (`Worker::search`, the assignment of `bound` just before `store_tt`):

- `BoundLower` when the score is at least beta. That is a fail-high. It says "the score is at least this," which stays true if every child score is itself sound.
- `BoundExact` when the node is a PV node (`beta - alpha > 1`) and some move was chosen.
- `BoundUpper` otherwise. That says "the score is at most this."

The root is a PV node. Later moves are searched with a zero window first, and a score above alpha is searched again with the full window.

The move loop prunes before it searches. Late-move pruning, quiet futility, history pruning, quiet SEE, capture futility, and capture SEE all `continue` over a legal move. The guard on that block is `!root_node`. It is not `!pv_node`. A PV node below the root can therefore skip a legal move and still store `BoundExact` or `BoundUpper`. The true score of a skipped move can only be higher, so those two bounds are too low. `BoundLower` from a real fail-high does not have that problem by itself.

`store_body` replaces the score when `bound == BoundExact`, or the position differs, or `depth + 4` exceeds the stored depth, or the generation differs. An exact bound replaces any depth. A helper that stored a shallow exact score, after skipping the mating move, overwrites the main thread's deeper mate entry.

The main thread then reads that entry. A non-PV node returns the table score immediately when the depth is enough and the bound matches (`BoundExact`, a lower bound at least beta, or an upper bound at most alpha). The root itself does not take that cutoff, because the cutoff requires `!pv_node`. The damage is inside the tree: a child returns the helper's score, alpha moves, and a different move becomes the one that is searched at full depth. The reported root score is then a centipawn score, or a different mate, or a different move.

A helper probe makes this worse even when the stored score is ignored. On a hit, `probe_body` writes the current generation into `gen_bound` if `refresh_generation` is true. Replacement picks the slot with the smallest `depth - 4 * relative_age`. A refreshed entry looks younger, so the main thread keeps the helper's slot and throws away a different one.

The task report was 57 misses in 400 two-thread runs, and 0 in 100 one-thread runs. No position list came with that report. The positions and counts below are the ones this branch ran. The two-thread miss is not one stable wrong move: a repeat of the same 30 runs names a different first failure. One thread, on a fresh worker, is stable.

### 2. One thread keeps history from the previous position

Each worker owns butterfly history, capture history, continuation history, a counter-move table, a correction table, and a material correction table. Butterfly history is indexed by side to move, from-square, and to-square (`ButterflyHistory` in `search.hpp`). Continuation history is indexed by the moved piece and the to-square. None of these keys include the position. Killers are cleared at the start of every search (the stack loop in `Worker::search`). The history tables were not.

They live until `Worker::clear()`, which `ucinewgame` calls. `Clear Hash` calls `clear_hash()`: the transposition table and the evaluation caches, not the history. So wiping the hash and searching the same ending again still uses the ordering learned from the previous position. History changes reductions (`history / LmrHistoryDivisor`), history pruning, and which quiet move is tried first. At depth 14 that is enough to search a different move, and to come back with a centipawn score where a fresh search had a mate.

`ucinewgame` hides the fault because it clears the tables. Bench hides it too: bench calls `clear()` before each of its positions.

### 3. After dropping helper stores, their nodes still ended the search

`should_stop` on the lock stops the main worker when `total_nodes()` reaches the limit. `total_nodes()` adds every worker's count. Helpers do not run the clock (`should_stop` returns immediately for a non-main worker unless the shared stop flag is set), but their nodes count toward `go nodes`.

Once helpers no longer write the table, those nodes buy no cutoff for the main search. The main worker stops after it has searched only part of the requested budget. The one-thread search is unchanged, because with one worker `total_nodes()` is that worker's own count. This is why a two-thread and a four-thread `go nodes` search got shallower after the first patch, while `Threads 1` stayed on the lock's line.

## What the runs found

Hash 16, `OwnBook false`, `TTAccess::Exclusive`, depth 14, unless a line says otherwise. `UseNNUE` is off for the mate checks. The test links `Searcher` directly. Full transcripts are in the command log.

### The lock drops the mate, and it drops it differently each run

One thread, fresh worker, net off:

| position | one thread |
| --- | --- |
| `4K3/k7/8/8/2R5/8/8/8 w - - 0 1` | mate 7 `c4c6` |
| `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1` | mate 17 `b3f3` |
| `3k4/8/3K4/8/8/8/8/3R4 w - - 0 1` | mate 3 `d1d4` |

Depth 14 prints mate 17 on the second position. The test locks that score. The search extends, so the printed mate distance can be longer than the depth limit. The branch does not change that score.

Two threads on the lock, 30 runs, same positions. The latest run of `tests_t5/krk_mate_test.cpp`:

- First position: 21 of 30 disagreed. First failure `cp 451 c4b4`.
- Second position: 30 of 30 disagreed. First failure mate 14 `b3f3` (same move, a different score).
- Third position: 1 of 30 disagreed. First failure mate 3 `d1e1` (same mate distance, the other move).

An earlier run of the mate checks, before the node-budget check existed, failed 19 of 30 (`mate 9 e8d7`), 29 of 30 (`cp 481 b3b8`), and 1 of 30 (`mate 3 d1e1`). The fault is real. The particular wrong move is a race between the two searches.

With the net left on, one thread scores the first position `cp 476 e8e7`, not a mate. Two threads disagreed 20 of 20. The latest first failure was `cp 510 e8f7`. An earlier run's first failure was `cp 496 c4c5`. This is the same shared-table disagreement. It is not, on this position, a missed mate, because one thread never proved one.

### The history fault survives Clear Hash

The test searches the start position to depth 10, calls `clear_hash()`, then searches the same ending to depth 14. On the lock:

- First position: fresh mate 7 `c4c6`, after the start-position search `cp 433 c4b4`.
- Second position: fresh mate 17 `b3f3`, after it `cp 539 b3f3`. The move stayed. The mate score did not.
- Third position: stayed mate 3 `d1d4`. History did not move this one.

`clear_hash()` had already wiped the table and the evaluation caches. The thing that still changed the move is the history tables.

### A helper fail-high is enough to hide the mate

Putting helper stores back was measured and not kept. Each attempt reintroduced a centipawn score where one thread had a mate.

- Helpers store only `BoundLower`, and do not replace a current-generation exact entry: 10 of 30 and 16 of 30 (`cp 438 c4b4`, `cp 494 b3e3`).
- The main thread ignores a non-mate helper score, and a helper does not overwrite a main-thread entry: 11 of 30 and 18 of 30.
- Helpers write `BoundLower` only into an empty slot, an old-generation slot, or a slot that already holds a helper entry. A PV node ignores that entry completely. A non-PV node may return it when it is a deep enough fail-high. That still missed: 24 of 30 (`cp 458 c4b4`) and 30 of 30 (`cp 519 b3f3`). The mate-in-3 position stayed matched, 0 of 30. With the net on, 20 of 20 disagreed (`cp 540 e8d7` against `cp 476 e8e7`).

The last attempt is the one that shows why a "sound" lower bound is not enough at a fixed depth. A zero-window node returns the helper score because it is at least beta. The parent raises alpha. The mating move is then reduced. Its reduced search comes back at or below that alpha, so the full-depth search that would have proved the mate is skipped. The root reports the centipawn score. Mate in 3 is short enough that this does not happen. Mate 7 and mate 17 are not.

### The node limit

`go nodes 1000000`, start position, net on, one run. The client reads until `bestmove`.

Lock, this session:

| threads | last completed line | best move |
| --- | --- | --- |
| 1 | depth 19, cp 15, 920173 nodes, `d2d4` | `d2d4` |
| 2 | depth 19, cp 13, 968560 nodes, `e2e4` | `e2e4` |
| 4 | depth 18, cp 16, 980627 nodes, `d2d4` | `d2d4` |

An earlier lock run of the same command finished at depth 17 for both two threads (`cp 22 e2e4`) and four threads (`cp 11 d2d4`). One thread matched both times: depth 19, cp 15, `d2d4`, 920173 nodes. The multi-thread node-limited result on the lock is not stable, for the same reason the mate is not stable: the helpers write the table.

The previous patch on this branch (helpers do not store, and the limit still counts every thread) made it worse and stable in the wrong direction: two threads finished at depth 16, cp 35, `e2e4`; four threads at depth 15, cp 27, `e2e4`. One thread stayed depth 19, cp 15, `d2d4`. The 30000-node test in the same binary printed depth 11, cp 24, `d2d4`, 30000 nodes for one thread, and depth 10, cp 24, `d2d4`, 30861 nodes for two threads.

## What changed

Helpers still search on a depth-limited search and on a clock search. They still read the table. They do not store, and a helper probe does not refresh generation. The main thread's store path is the same replacement rule as the lock.

`Worker::store_tt` returns immediately when `!is_main()`. `Worker::probe_tt` calls `probe(key, false)` for a helper, so the generation write in `probe_body` is skipped. The same `is_main()` guard is on the `#else` store sites. Those sites are compiled out of this build (`FORGE_SPD_TT_NOTLS=1`). The one-thread path still calls `probe_owned` / `store_owned` when it holds the exclusive lease, and the locked `probe` / `store` otherwise.

Every search, on every worker, calls `clear_histories()` before the root. That zeros butterfly history, capture history, continuation history, counter moves, correction history, and material correction. `Worker::clear()` calls the same function, so `ucinewgame` still clears them. Bench already cleared them before each position, which is why the bench node counts did not move.

A search with `nodes_specified` or a non-zero `nodes` does not start helpers. `should_stop` compares the limit with `local_nodes_`, the main worker's own count. When no helper is started, the exclusive lease is taken for an `Exclusive` search, which is the same store path a one-thread search uses. `go nodes 1000000` then finishes on the same line at 1, 2, and 4 threads: depth 19, cp 15, 920173 nodes, `d2d4`. The 30000-node test prints depth 11, cp 24, `d2d4`, 30000 nodes for both one and two threads.

Two behavior changes are intentional. History no longer carries from the previous move into the next search, so a game plays without that leftover ordering. A node-limited search with `Threads` above 1 runs as the one-thread search of that many nodes; the helpers are not started, because they cannot publish a sound entry and their nodes were ending the search early. A depth-limited search still starts them. They do not share cuts, so a clock search does not get a deeper main tree from the extra threads.

### Files

- `forge-combo29/include/forge/search.hpp` — `probe` takes `refresh_generation`; `store_tt` drops helper writes; `probe_tt` does not refresh on a helper.
- `forge-combo29/src/search.cpp` — generation refresh is conditional; `clear_histories` runs at the start of every search; the node limit uses the main worker's count; a node-limited search does not launch helpers.
- `forge-combo29/tests_t5/krk_mate_test.cpp` — fails on the lock, passes here.
- `forge-combo29/REPORT_t5.md` — this file.

Engine diff against `16833ecc` (`git diff --numstat -- forge-combo29/src forge-combo29/include`): `search.hpp` 13 insertions and 2 deletions, `search.cpp` 38 insertions and 20 deletions. No change to `CMakeLists.txt`.

### What stayed the same

The main thread still stores exact, upper, and lower bounds under the same replacement rule, including `BoundExact` replacing any depth. The pruning is unchanged. One-thread bench and perft match the lock: `bench 11` = 312866, `bench 13` = 862329, start-position `go perft 5` = 4865609. The depth-14 mate test now matches the one-thread move and score on every two-thread run (0 mismatches in 30, and 0 in 20 with the net on), and the history check matches the fresh search after a start-position search plus `clear_hash()`.

## Commands

Working directory: `/agent/repos/dwqww`. Compiler: `g++-13` (this machine's Clang 18 does not link). CPU supports the lock `-march=x86-64-v4` build. The test binary is not part of the branch.

### Test linked to the unchanged lock (`16833ecc`)

`search.cpp` and `search.hpp` were taken from that commit. The other translation units are unchanged from it. Exit status 1.

```
mkdir -p /tmp/lock_inc/forge
git show 16833ecc:forge-combo29/include/forge/search.hpp > /tmp/lock_inc/forge/search.hpp
git show 16833ecc:forge-combo29/src/search.cpp > /tmp/lock_search.cpp
g++-13 -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I /tmp/lock_inc -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  /tmp/lock_search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test_lock && /tmp/krk_mate_test_lock; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 433 c4b4
history FAIL
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 cp 539 b3f3
history FAIL
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 21 first cp 451 c4b4
threads FAIL
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 30 first mate 14 b3f3
threads FAIL
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 1 first mate 3 d1e1
threads FAIL
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 20 first cp 510 e8f7
threads FAIL
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 10 cp 19 g1f3 total 30000
node budget FAIL
FAILED 7
EXIT:1
```

`3k4/8/3K4/8/8/8/8/3R4` did not change after a start-position search on the lock. The other two history cases did. Two threads missed or changed the one-thread result on the longer mates and with the net left on (there the one-thread score is a centipawn score, not a mate). The first wrong two-thread move is not stable across runs. An earlier run of the mate checks, before the node-budget check existed, failed 19 of 30 (`mate 9 e8d7`), 29 of 30 (`cp 481 b3b8`), 1 of 30 (`mate 3 d1e1`), and 20 of 20 (`cp 496 c4c5`).

### Test linked to this change

Same command, output `/tmp/krk_mate_test`. Exit status 0.

```
g++-13 -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test && /tmp/krk_mate_test; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
history ok
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
history ok
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 11 cp 24 d2d4 total 30000
node budget ok
ok
EXIT:0
```

The same test, linked to the previous patch (helpers already do not store, but the node limit still counts every thread), passed the mate and history checks and then failed the node budget. Exit status 1. That binary was `search.cpp` from this branch with only the stop condition put back to `total_nodes()`.

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
history ok
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
history ok
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 10 cp 24 d2d4 total 30861
node budget FAIL
FAILED 1
EXIT:1
```

### AddressSanitizer and UndefinedBehaviorSanitizer

`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, same defines. No sanitizer diagnostic. Exit status 0.

```
g++-13 -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 \
  -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
  -I forge-combo29/include \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/book.cpp \
  forge-combo29/src/search.cpp \
  forge-combo29/tests_t5/krk_mate_test.cpp \
  -pthread -o /tmp/krk_mate_test_asan && /tmp/krk_mate_test_asan; echo EXIT:$?
```

```
fresh 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
after-startpos 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
history ok
fresh 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
after-startpos 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
history ok
fresh 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
after-startpos 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
history ok
t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 mate 7 c4c6
threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 30 mismatches 0
threads ok
t1 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 mate 17 b3f3
threads2 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1 runs 30 mismatches 0
threads ok
t1 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 mate 3 d1d4
threads2 3k4/8/3K4/8/8/8/8/3R4 w - - 0 1 runs 30 mismatches 0
threads ok
nnue-t1 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 cp 476 e8e7
nnue-threads2 4K3/k7/8/8/2R5/8/8/8 w - - 0 1 runs 20 mismatches 0
threads ok
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 11 cp 24 d2d4 total 30000
node budget ok
ok
EXIT:0
```

### Engine build, bench 11, bench 13, perft 5

`Threads 1`, `Hash 16`, `OwnBook false`. Bench builds its own 16 MB, one-thread searcher. Perft is from the start position.

```
cmake -S forge-combo29 -B /tmp/forge-t5 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++-13 && cmake --build /tmp/forge-t5 -j4
```

Configure and compile completed. The link line ended with `[100%] Built target forge`.

```
printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-t5/forge
```

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
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 423 nps 2038602
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

Pins: `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609.

## Helper stores and node-limited depth

These are the measurements behind the account above. A review of the first patch asked for helper threads to publish results again. Sharing a fail-high brings the mate miss back, so those attempts were not kept.

Helpers storing only `BoundLower`, and not replacing a current-generation exact entry, missed the mate 10 of 30 and 16 of 30 times (`cp 438 c4b4`, `cp 494 b3e3`). Ignoring those centipawn scores in the main thread, and refusing to overwrite a main-thread entry, still missed (11 of 30 and 18 of 30). A later attempt let helpers write `BoundLower` only into an empty, old, or already-helper slot, let a non-PV node cut off on a deep enough fail-high, and made every PV node ignore the helper entry. That still missed: 24 of 30 (`cp 458 c4b4`) and 30 of 30 (`cp 519 b3f3`). The mate-in-3 position stayed matched, 0 of 30. With the net left on, the same attempt missed the one-thread score 20 of 20 (`cp 540 e8d7` against `cp 476 e8e7`). The extra cutoffs change which moves the main line searches at full depth, and the depth-14 mate becomes a centipawn score. The patch still drops helper stores.

`go nodes 1000000` from the start position, Hash 16, `UseNNUE true`, `OwnBook false`. The client reads until `bestmove`, then sends `quit`. One run each.

Lock binary `/tmp/forge-lock-t5/forge` (unchanged `16833ecc`):

| threads | last completed info | bestmove |
| --- | --- | --- |
| 1 | depth 19 score cp 15 nodes 920173 pv d2d4 | d2d4 |
| 2 | depth 19 score cp 13 nodes 968560 pv e2e4 | e2e4 |
| 4 | depth 18 score cp 16 nodes 980627 pv d2d4 | d2d4 |

An earlier lock run of the same command finished at depth 17 for both two and four threads (`cp 22 e2e4`, `cp 11 d2d4`). The lock's multi-thread node-limited result is not stable. One thread is stable: this run's depth-19 line matches the earlier one (`cp 15 d2d4`, 920173 nodes).

This patch, `/tmp/forge-t5/forge`, threads 1, 2, and 4 each finished at the same search line. Threads 1 printed:

```
info depth 19 seldepth 30 score cp 15 nodes 920173 nps 1921029 hashfull 464 time 479 pv d2d4 g8f6 c2c4 e7e6 g1f3 b7b6 b1c3 c8b7 e2e3 g7g6 f1e2 f8g7 b2b4 e8g8 c1a3 a7a6 a1c1 d7d6 e1g1
bestmove d2d4
```

Threads 2 printed that same depth-19 line, including `nps` and `time`. Threads 4 printed the same depth, score, nodes, `hashfull`, and pv, with `nps 1917027` and `time 480`. The depth-17 and depth-18 lines matched on all three (`cp 18` at 600227 nodes, `cp 15` at 846653 nodes). A node-limited search does not start helpers, so the reported node count stays on the one-thread search. A depth-limited search still starts them; they read the table and do not write it. This is not a speed claim. Helpers still do not share cuts on a clock search.

## Not verified

- The reported 57 of 400 and 0 of 100 counts. No position list came with the task. The counts above are the runs in `tests_t5/krk_mate_test.cpp` only.
- A king-and-rook position where `UseNNUE true` and `Threads 1` at depth 14 already prints a mate, and `Threads 2` used to miss it. On `4K3/k7/8/8/2R5/8/8/8 w - - 0 1` the net-on one-thread search scores `cp 476`, not a mate. Two threads now repeat that same score and move (0 mismatches in 20). The missed-mate runs are with `UseNNUE false`.
- More than two threads on the depth-14 mate positions. `go nodes 1000000` was run at four threads; that search does not start helpers, so it matches the one-thread line.
- Clock-limited games. History is cleared at the start of those searches too, and the helpers still start. Bench and perft do not cover a timed game, and this run did not measure whether the extra threads make the main search slower on the clock.
- Playing strength or speed. Nothing here is an Elo or NPS claim. The bench `nps` lines are the raw timer output.
- The release binary under AddressSanitizer. The sanitizer run is the test at `-O1`. The `#else` path of `FORGE_SPD_TT_NOTLS` is compiled out of this build (`FORGE_SPD_TT_NOTLS=1`); it has the same helper-write guards in source and was not linked.
- Clang, and any non-Linux host.
