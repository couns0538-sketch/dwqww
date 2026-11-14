# Search-strength checkpoint 3

Date: 2026-11-13. A correctness fix for one position class. No Elo result, and no candidate is promoted.

## Source identities

- Base: `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`.
- This branch: `cursor/forge-search-strength-20261113-9558`. Not pushed to `main`, `lock/combo29-20261110`, the Fable branch, or another agent's branch.
- Portable binary: g++ 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. The pre-fix binary used for the failing run is the checkpoint 2 executable.

## Other agents read this round

Fetched immediately before this note:

- Correctness: `cursor/forge-correctness-20261113-e6b6` at `dff76c5808d0ceb7fc3940d1758991c3c33fb26d` (unchanged since checkpoint 2). Their bare-king skip applies only when more than one worker is searching, because a per-node gate on one worker moved depth 13 to 862954 net on and 907307 net off. Their resume also records the one-thread miss and leaves it unfixed. This branch does not copy that patch. Their branch was not written.
- NNUE: `cursor/forge-nnue-eval-20261113-22cc` at `36b644d8484cdcfaad95247a8966b2d8bb9f4236`. The new commits lock the v3 int16 refresh and the trainer's final-test path. They do not change this search. Their branch was not written.
- History index: `cursor/forge-history-index-20261113-712a` at `da51693e0fbac616c73c454a9bd2cf93f1f4ee24`. `docs/history-index/findings/BUGS.md` names the 64-slot capture buffer, the position-prefix discard, and the zero-node terminal report. Those three are already fixed on the correctness tip above. The qsearch-stalemate prediction is recorded there as not live on combo29. This pass re-ran that probe (`score cp 0`). Their branch was not written.
- No evidence or benchmarking branch was on `origin` at this fetch.

## What was searched, and what is not a new bug

Movegen, make/unmake keys, and `gives_check` on legal moves were compared with independent checks earlier in this session (perft against python-chess, 144166 legal moves with 0 key mismatches and 0 check mismatches). Those passes are not repeated here.

`Clear Hash` after the pawn endgame left the KRK miss unchanged, including the node count (36827 at depth 14, hash sizes 1, 16, and 128). The transposition table and the evaluation cache are not what keeps the mate out. The state that survives `Clear Hash` is the history and correction tables.

The 64-slot `bad_captures_` overflow is real on this branch and already fixed on the correctness tip. It is not patched again here. SEE differences against a full exchange minimax match the lock's LVA algorithm and were not changed.

## The miss

Position `4R3/8/8/k2K4/8/8/8/8 w - - 0 1` is mate in 3 with `d5c5`. UseNNUE true, Hash 16, Threads 1.

Fresh search on the pre-fix binary: depth 10 already returns `d5c5` mate 3 (10491 nodes). Depths 6 through 9 return `e8e4` with a centipawn score, which is an unfinished search, not the bug.

A depth-9 search of an unrelated position, then this position at depth 14 with no `ucinewgame`, returned `e8e4` on the pre-fix binary:

| Earlier position | Depth 14 result | Nodes |
|---|---|---|
| `8/8/8/8/3k4/8/3K4/3Q4 w - - 0 1` | `e8e4` cp 442 | 32101 |
| `4k3/8/8/8/8/8/4P3/4K3 w - - 0 1` | `e8e4` mate 10 | 36827 |
| `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3` | `e8e4` cp 462 | 27276 |

The mate-10 line is a longer rook mate, not mate in 3. Two fresh workers missed the same mate on 8 of 40 depth-14 searches (scores included cp 457, mate 10, and mate 9), which is the same failure the correctness log measured at 57/400.

## The change

`root_bare_king_` is set from the root position. Late-move pruning and late-move reduction are skipped only when that bit is set and the node itself still faces a lone king. A bare king that appears only after trades inside a lock bench does not take the new path. That is why a one-worker per-node gate moves the benches and this one does not.

`forge-combo29/tests/krk_bare_king.py` is the regression. It is not a speed test and not a match.

## Results on the patched binary

Same protocol, UseNNUE true, Hash 16:

- Fresh depth 10: `d5c5` mate 3, 8972 nodes. Fresh depth 14: `d5c5` mate 3, 11884 nodes. The fresh KRK tree is smaller than the pre-fix depth-10 count because the mate score cuts the rest. This position is not in the lock benches.
- After each of the three depth-9 searches: `d5c5` mate 3, nodes 11568, 11884, and 11866.
- Threads 2, 40 fresh depth-14 searches: 0 misses.
- Threads 2 after the pawn endgame: `d5c5` mate 3, 15333 nodes.

`check_pins.sh` on `/tmp/forge-plain/forge`:

- net on: 312866, 862329, 3024920, 12389307, 34048354
- net off: 375354, 907205, 2448617, 13573040, 24506465
- startpos perft 5: 4865609
- `PINS MATCH combo29`

Depth 13 alone, pre-fix and patched: 862329 net on, 907205 net off.

No match was played. This is not an Elo claim.
