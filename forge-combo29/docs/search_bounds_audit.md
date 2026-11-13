# Search bounds audit

Audit of alpha-beta / PVS, aspiration windows, transposition bounds, and aborted re-searches in `forge-combo29`. The lock search is unchanged when `PvBoundFix` and `AspirationKeepExact` stay at 0. Two corrections are always on because they do not change a completed search: an aborted aspiration attempt no longer pairs a new best move with the previous iteration's score, and a mate stored in the transposition table is ignored when the fifty-move rule cannot reach it.

This is not an Elo result. The bench numbers below are node-count pins. The recorded times are only how long that run took on this machine.

## What was reproduced

### Unfinished aspiration re-search

Baseline binary, NNUE off, OwnBook off, Hash 16, one thread, `ucinewgame` before the search. Start position, `go depth 10 nodes 2066`:

```
info depth 5 seldepth 8 score cp 3 nodes 1275 pv d2d3 e7e6 c1f4 d7d5 g1f3
info depth 6 seldepth 11 score cp 3 nodes 2066 pv g1f3 d7d5 d2d3 g8f6 c1f4 e7e6
bestmove g1f3
```

A finished depth 6 of the same position is `cp 18` and `e2e3` (2524 nodes). Depth 6 did not finish. The engine still printed depth 6 and played `g1f3`, while the score stayed at the depth-5 score of the move `d2d3`.

The same command on the patched engine prints `depth 6 score cp 17 pv g1f3 ...` and plays `g1f3`. The score belongs to that partial PV. It is higher than the last finished iteration, so the partial line replaces it. Depth, score, and PV are that same attempt. A partial whose score is not strictly higher is dropped, and the last finished iteration stands.

### PV-node pruning

Move pruning (late-move pruning, quiet futility, history, SEE, and the capture SEE / futility tests) runs on PV nodes below the root. A PV node then stores `BoundExact` when a move beats alpha, or `BoundUpper` when none does. A skipped legal move makes that bound false: the side to move can be scored too low, and after the negation the opponent's score is too high.

At the start position, depth 7, NNUE off, the main-search counter of those skips is 201 and the quiescence counter is 18 with `PvBoundFix` at 0. Both are 0 with `PvBoundFix` at 1. Quiescence futility and SEE use the same switch: a PV quiescence node can store `BoundExact` after skipping a capture.

`PvBoundFix` stays 0. Turning it on changes the tree. On the sample below, NNUE off, it changes the root score or the best move at depth 7 and at depth 9. One case is a proven mate, not a false one:

Position `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`. An exhaustive generation of legal moves, with no pruning, proves `g3g6` is mate in two: every black reply loses to a mate in one. The lock search reports mate 2 and `g3g6` at depth 7 (2725 nodes) and still does so at depth 10 (3229 nodes). With `PvBoundFix` at 1 the same mate is missed at depth 7 (`cp 148`, `f6e8`, 3359 nodes) and at depth 10 (`cp 133`, `f6e8`, 32191 nodes). It is found again at depth 11 (`g3g6`, 66435 nodes). Searching the moves the lock skips, including quiescence captures, changes reductions and move ordering, so the quiet mate is proved later and the node count grows. The switch is a bound correction with a tactical cost, not a strength patch.

Other depth-7 changes with the switch on (lock score and move, then the switch):

| Position | Lock | PvBoundFix 1 |
| --- | --- | --- |
| startpos | -7 `d2d4` | 10 `e2e3` |
| Kiwipete | -231 `d5e6` | -61 `d5e6` |
| `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` | 52 `b4f4` | 43 `b4f4` |
| `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8` | -274 `c4d5` | -278 `a1c1` |
| `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1` | -610 `g7g6` | -611 `g7g6` |
| `rnbq1rk1/pppp1ppp/5n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQ - 0 6` | 43 `e1g1` | 104 `f3e5` |
| `8/8/8/2k5/2p5/2K5/1R6/8 w - - 0 1` | 467 `b2d2` | 452 `b2b1` |

### Aspiration fail-low after a clamped beta

From depth 4 the window is the previous score ± `AspirationDelta` (18). A fail-low sets beta to `(alpha + beta) / 2`, then alpha to `max(score - delta, -Infinite)`. When the previous beta was already `Infinite` (32001), the midpoint can fall below the last exact score. Example used by the unit test: alpha 31972, beta 32001, fail-low score 31950, delta 18, last exact score 31990. The lock midpoint is 31986, which excludes 31990. Alpha becomes 31932. `AspirationKeepExact` holds beta at 31990 and leaves alpha at 31932. An ordinary window whose beta was not clamped is unchanged (the midpoint is the previous score). The switch stays 0. On the start position at depth 8, NNUE off, both settings search 8151 nodes and score 10.

### Fifty-move mate bounds

`score_from_tt` adjusts mate scores by ply and did not look at the halfmove clock. A stored mate whose distance is greater than `99 - min(clock, 99)` is now treated as a miss, so the node is searched. The test plants exact TT scores at clock 80 (room 19):

| Stored score | Meaning | Result |
| --- | --- | --- |
| 31981 | mate distance 19 | cutoff, score 31981 |
| 31980 | mate distance 20 | not a cutoff (search returned 18) |
| -31980 | loss in 20 plies | not a cutoff (search returned 18) |
| 40 | centipawn exact | cutoff, score 40 |

Distance 19 is accepted and distance 20 is rejected at clock 80. That is one ply short of the draw, on purpose: a mate that only just fits is searched again. Clocks of 90 and above already refuse a TT cutoff through `TTEntry::score_usable`. Bench FENs use clock 0. At clock 0 the filter only drops mates longer than 99 plies. The pin node counts did not move, so those searches never used such a mate.

## Fixes

| Change | Default | Why it can stay on |
| --- | --- | --- |
| Aborted root attempt returns the best move that finished. The driver keeps a partial PV only when its score is strictly above the last finished iteration, and then records that attempt's depth. A stale PV is cleared when a node is entered already aborted. | always | Bench searches are not aborted. Pins match. |
| `score_from_tt` rejects mate scores the fifty-move rule cannot reach. | always | Pins match, including mates that do fit. |
| `PvBoundFix`: skip move pruning on PV nodes in the main search and in quiescence. | 0 | Changes nodes and root scores. |
| `AspirationKeepExact`: fail-low beta does not drop below the last exact score. | 0 | Changes the window only after a clamped beta. Left off so the lock tree stays bit-exact. |

Both switches are UCI spin options (`0` or `1`) because tunables are exposed in this build.

## Tests and pins

`forge_search_tests` (NNUE off, hash 16, one thread) covers the window arithmetic, the planted fifty-move cutoffs, the PV-prune counter, the score changes with `PvBoundFix`, a node-limit scan of three positions through depth 8, the exhaustive mate proof, the `nodes 2066` regression, and a depth-8 search with `AspirationKeepExact`. CTest runs it as `search_bounds`. Result: `all passed`.

Build: `g++-13`, `NDEBUG`, the same `FORGE_*` defines as the engine, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`. Clang 18 on this machine does not link (it looks for a GCC 14 libstdc++ that is not installed).

Lock pins, Threads 1, Hash 16, this binary. Net on: 312866 / 862329 / 3024920 / 12389307 / 34048354 at depths 11 / 13 / 16 / 20 / 22. Net off: 375354 / 907205 / 2448617 / 13573040 / 24506465. Start-position perft 5: 4865609.

## Left as they are

- A quiescence stand-pat fail-high stores `BoundLower` with `pv` false, and only when the position was not already in the table. Capture futility and SEE on PV quiescence nodes are under `PvBoundFix` and stay at the lock behaviour while that switch is 0.
- Null-move and probcut cutoffs are not always written back. A singular multicut returns `singular_beta` without a store. Both match the existing search and were not retuned.
- The PVS shape is unchanged: the first move at a PV node is a full window; later moves are a zero window, then a full window if they beat alpha, including when the zero window already failed high. A full-window re-search can replace that fail-high.
- A TT move can be replaced when the stored score is not replaced. That affects ordering only.
- Mate-distance pruning before the TT probe, internal iterative reduction storing the reduced depth, and two-fold repetition inside the tree are unchanged.
- An unfinished iteration may still change the best move when the partial score is strictly higher. That partial is not a completed depth: at `nodes 2066` the patched engine plays `g1f3` at 17 centipawns, while a finished depth 6 plays `e2e3` at 18.
- `PvBoundFix` does not make the search exact. Late-move reductions and null move remain, and a quiescence stand-pat can still cut a PV node. Leaving the switch at 0 preserves the lock, including the earlier mate on `g3g6`.
- The fifty-move filter does not serve mates at clocks 90–99, because `score_usable` already blocks those cutoffs. It also refuses a mate that lands on the last ply of the rule.
