# What changed, what was found, and what was wrong

Date: 2026-11-14. Branch `cursor/forge-search-strength-20261113-9558`, cut from `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`. This file explains the results. It is not an Elo claim. No match was played on this machine.

The numbers behind each section are in `search_strength/CHECKPOINT.md`, `search_strength/CHECKPOINT-2.md`, and `search_strength/CHECKPOINT-3.md`.

## What was wrong

The position

```
4R3/8/8/k2K4/8/8/8/8 w - - 0 1
```

is a rook-and-king mate in 3. White king on d5, white rook on e8, black king on a5. The move is `d5c5`. The line `d5c5 a5a4 e8e3 a4a5 e3a3` is checkmate. A fresh one-thread search with the network on already plays that mate at depth 10.

The pre-fix engine did not keep playing it.

After one depth-9 search of a different position, with no `ucinewgame` in between, the same engine at depth 14 played `e8e4` instead:

| Search that ran first | What depth 14 then played | Score | Nodes |
|---|---|---|---|
| `8/8/8/8/3k4/8/3K4/3Q4 w - - 0 1` | `e8e4` | cp 442 | 32101 |
| `4k3/8/8/8/8/8/4P3/4K3 w - - 0 1` | `e8e4` | mate 10 | 36827 |
| `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3` | `e8e4` | cp 462 | 27276 |

`e8e4` is a legal rook move, and it is a win, but it is the long way. Searching only that move, on the patched binary at depth 18, scores it mate in 9 (5,270,234 nodes). The depth-14 report of mate 10 was not that proved distance. Its printed line was

```
e8e4 a5b6 d5d6 b6b5 e4g4 b5b6 g4b4 b6a6 d6c5 a6a5 b4h4 a5a6 c5c6 a6a7 h4a4 a7b8
```

Sixteen plies. The position at the end of that line, `1k6/8/2K5/8/R7/8/8/8 w - - 16 9`, is not checkmate. The search had stopped calling the position a short mate and was following a longer rook shuffle.

Two fresh workers, no earlier search, missed the same mate on 8 of 40 depth-14 runs. The misses were `e8e4` at cp 457, cp 458, cp 467, cp 474, mate 9, or mate 10. The correctness log, read at `dff76c58`, had already measured 57 misses out of 400 on two threads. One fresh thread did not miss: 0 misses at depth 10 and above in the fresh runs here.

Depths 6, 7, 8, and 9 on a fresh thread also print `e8e4` with a centipawn score. That is the search stopping before it can see three moves. It is not the fault below. The fault is a depth that already finds `d5c5` from empty tables, and then does not find it once those tables are no longer empty, or once a second worker is searching.

## Why the search dropped the mate

`ucinewgame` calls `Searcher::clear()`, which zeroes the history tables. A later `position` plus `go` does not. The tables that survive are:

- main history, indexed by side, from-square, and to-square
- capture history
- continuation history
- counter-move table
- pawn-structure correction
- material correction

`setoption name Clear Hash` calls `clear_hash()`. That zeroes the transposition table and the evaluation cache (`clear_caches()` is `evaluator_.clear()`). It does not touch the six tables above. After the pawn endgame, clearing the hash and then searching the rook ending at depth 14 still played `e8e4` mate 10, at the same 36827 nodes, for hash sizes 1, 16, and 128. The hash is not what kept the mate out. The history and correction tables are.

Those tables are supposed to carry information from one move of a game to the next. Here they carried information from an unrelated position. Quiet moves that were good in the earlier search get a bonus. In the rook ending that bonus makes `e8e4` look urgent and `d5c5` look late.

Late moves are then thrown away or searched too shallow to see mate in 3. Both of these are in `Worker::search` in `forge-combo29/src/search.cpp`:

- The shallow-pruning block (late-move pruning, quiet futility, history pruning, and the SEE skip) runs only below the root, and only while the side to move still has a piece other than pawns. A quiet move with a bad history value is skipped when `history < -HistoryPruneMultiplier * depth`. A quiet move past the late-move threshold is not searched at all.
- Late-move reduction runs from depth 2. At the root the first two moves are not reduced (`move_count > 2`). Every later root move is. If the reduced search does not beat alpha, the move is never searched at full depth. A mate that sits behind that reduction is invisible.

The root itself does not use the shallow-pruning block. The mate is lost one ply deeper, or at the root because `d5c5` is no longer one of the first two moves and the reduced search fails low.

A second worker misses the same mate with empty history tables. Fresh two-thread searches missed 8 of 40 times. A fresh one-thread search at the same depth did not miss. The workers share the transposition table, so a shallow score from one worker is visible to the other, and the pruning above can then drop `d5c5`. This branch did not log those writes. What was measured is the miss. The shared table is the state that exists on a fresh two-thread search and does not exist on a fresh one-thread search.

## What was changed

`root_bare_king_` is set once, from the root position, at the start of `Worker::search`:

```cpp
root_bare_king_ = popcount(board.occupied(opposite(board.side_to_move()))) == 1;
```

Inside the recursive search the pruning and the reduction are skipped only when that bit is set and the node still faces a lone king:

```cpp
const bool bare_king_opponent =
    root_bare_king_ && popcount(board.occupied(opposite(board.side_to_move()))) == 1;
```

In the rook ending the root opponent is the black king, so the bit is set. White-to-move nodes in that search do not late-move prune and do not reduce. Black-to-move nodes still do, because White has a king and a rook. The history tables are left as they were. The transposition table is left as it was.

A check of "lone king" at every node, including nodes inside ordinary games, is a different change. Lines in the lock benches trade down to king and rook against a lone king. The correctness branch measured that wider gate on one worker: depth 13 became 862954 with the network and 907307 without it. The pins are 862329 and 907205. They did not apply it. This branch does not apply it either. The root bit stays false on all eight bench positions, so those trades keep the old pruning. Depth 13 on the pre-fix binary and on the patched binary was 862329 and 907205.

After the change, same settings (network on, hash 16):

- Fresh depth 10: `d5c5` mate 3, 8972 nodes. Fresh depth 14: `d5c5` mate 3, 11884 nodes.
- Each of the three depth-9 searches above, then depth 14: `d5c5` mate 3, nodes 11568, 11884, and 11866.
- Two threads, 40 fresh depth-14 searches: 0 misses.
- Two threads after the pawn endgame: `d5c5` mate 3, 15333 nodes.

`forge-combo29/scripts/check_pins.sh` printed `PINS MATCH combo29`. Net on: 312866, 862329, 3024920, 12389307, 34048354. Net off: 375354, 907205, 2448617, 13573040, 24506465. Startpos perft 5: 4865609. The regression is `forge-combo29/tests/krk_bare_king.py`.

What this change does not do: it does not repair a mate in a position whose root opponent has more than a king. History from an unrelated search can still reorder that tree. The correctness tip later read at `f6760ff6` clears the history tables at every root (`ffc19fa3`) and also waits for the attack tables before a second thread uses them. Those edits are theirs. They are not in this branch. Clearing history at every root would also wipe the tables between moves of one game. This branch keeps the tables and only stops the pruning in a search that already starts against a lone king.

## What else was found

These are measurements or checks. They are not the mate fault above, and none of them is promoted.

### Enhanced transposition counts

`FORGE_ETC_STATS` is default off and takes no cutoff. It counts children whose table entry would already prove a cutoff. The full-child probe costs more wall time than the share of nodes under those children at bench 16 (about 4.5% time, 1.74% nodes) and bench 20 (about 12.4% time, 5.44% nodes). At bench 22 the point estimate is 7.87% time against 10.08% nodes. A rough interval on that gap reaches about 1.5 points, under the dossier's 2-point line. A hash-move-only peek covers under 1% of nodes and its time is inside the noise. `FORGE_ETC` and `EtcDepth` are unused. The dossier this was checked against is `fable52-search-gap-20261109` at `56a76b153bb88026f2d83d65df6e422b0f3298f9`. Its own verdict was already that there is no qualified gap. These benches do not reopen a cutoff.

### Ply-4 continuation history

The search already writes continuation history at ply 4, at half the usual bonus, and used to read only plies 1 and 2. `FORGE_CONT4_READ` is default off. With it on, the extra term is added to quiet ordering only. An earlier build also fed ply 4 into the history value that late-move reduction uses. That mixed ordering with reductions and was discarded. The switch that remains changes the tree: net-on node ratios against the pins run from 0.614 to 1.081, and some best moves change. On `8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1` the plain binary plays `a1b2` at depth 16 and `a1b1` at 22 and 28. The ordering build plays `a1b1` at all three. One position. Not a match. The switch stays off.

### Checks that matched

On the plain binary, perft against python-chess matched on the standard suites and on 1200 positions from random walks. Incremental keys, pawn keys, and null-move keys matched a full recompute on 144166 legal moves, with 0 mismatches. `gives_check` and `is_legal` matched make/unmake on those same legal moves. Forty random mate-in-1 positions at depth 2 were all found. The quiet stalemate `g5g6` in `7k/8/5K2/6Q1/8/8/8/8 w - - 0 1` scores 0, including at depth 1, because `is_draw` treats a side with no legal move and no check as a draw before stand-pat.

### Real defects that this branch did not patch

They are already fixed on the correctness branch. Patching them again here would be a second copy.

- `bad_captures_` is `std::array<Move, 64>`. The picker writes it with no size test. Their test position has 69 noisy moves and 68 losing ones. With libstdc++ assertions the pre-fix picker aborts. Their tip sizes the array to 256.
- `position startpos moves NOTAMOVE` from a checkmated board used to leave the engine in mate. Their tip keeps the legal prefix.
- `go perft` used to ignore `stop`. Their tip watches for it.
- `go nodes 0` on a stalemate used to print an `info depth` line. Their tip answers before that report.
- `attacks::init` set a flag before the magic tables were filled. Eight threads constructing the first `Board` segfaulted. Their tip at `f6760ff6` fills the tables under `std::call_once`.

SEE against a full exchange minimax differs by 300 centipawns on two queen-takes-pawn positions (`-500` against `-800`). The engine matches the usual least-valuable-attacker algorithm with the 0/1 slack. Changing it would change the lock tree. It was left as it is.
