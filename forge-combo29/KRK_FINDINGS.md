# KRK mate scores: what changed, what is true, and what is wrong

This note is on `grok47/t19-wide-net-parity` so the measurements stay with this branch. The engine sources in this branch are the lock plus the hidden-width change. Nothing here edits search. The KRK agent was still editing `search.cpp` on its own branch, so the fix was not pushed there.

The position the search gets wrong is king and rook versus lone king, NNUE off, Hash 16.

```
8/8/8/8/8/1R6/2k5/5K2 w - - 0 1
```

White king f1, white rook b3, black king c2.

## What the search reports

Built from the lock objects in `build/CMakeFiles/forge.dir/src/` (portable x86-64-v3, `FORGE_NNUE_HIDDEN=256`). `nnue::enabled` was set false. Hash 16. The driver calls `Searcher::search` and then plays the PV to see whether the final position is checkmate.

Threads 1:

| Depth | Score | UCI | Plies claimed | Move | PV ends in mate |
| --- | --- | --- | --- | --- | --- |
| 1–12 | about +425 to +459 | cp |  | `b3b4`, later `b3f3` | no |
| 13 | 31967 | mate 17 | 33 | `b3f3` | no, PV is 15 plies |
| 14 | 31967 | mate 17 | 33 | `b3f3` | no |
| 15 | 31967 | mate 17 | 33 | `b3f3` | no |
| 16–19 | 31975 | mate 13 | 25 | `b3f3` | no, PV is 17 plies |
| 20–22 | 31981 | mate 10 | 19 | `b3e3` | PV is 19 plies; the end of that line was not checked |
| 23–24 | 31983 | mate 9 | 17 | `b3e3` | yes, 17 plies, final position is checkmate |

Depth 13 line, the first jump:

```
info depth 13 seldepth 22 score mate 17 nodes 25568 ... pv b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

Seldepth 22. A search that never reached ply 33 still printed a 33-ply mate. The 15-ply PV does not checkmate. After those moves the side to move is black and the position is not mate.

Depth 24 is a real mate and the right first move, with the wrong distance. Score 31983 is 17 plies. The PV is 17 plies and the last position is checkmate. The shortest mate is 15 plies.

Threads 2, depth 14, same position, fresh searcher: `cp 529`, move `b3g3`, PV of 17 plies, not checkmate. Threads 1 at depth 14 has not proved a mate. The centipawn score is the search failing to prove one, which at depth 14 is expected: the shortest mate is 15 plies.

A known mate in one is reported correctly. `k7/8/1K6/8/8/8/8/7R w` at depth 6 returns score 31999, mate 1, `h1h8`, and the PV is checkmate.

## What is actually true

Distances below are plies until the lone king is checkmated, attacker minimizing, defender maximizing. Capturing the rook, stalemate, a repeated position key, or 100 half-moves is a draw. The table is retrograde. Every legal move comes from the lock `Board`. 399112 legal white-rook positions, 26 passes until the distances stopped changing. Kings that touch or share a square are illegal and are not in the table.

Checked against a mate in one: `k7/8/1K6/8/8/8/8/7R w` is 1 ply by `h1h8`. The engine agrees.

| Position | Plies left | UCI | One fastest move |
| --- | --- | --- | --- |
| `8/8/8/8/8/1R6/2k5/5K2 w` | 15 | mate 8 | `b3e3` |
| `8/8/8/8/8/5R2/2k5/5K2 b` (after `b3f3`) | 16 |  | `c2d2` |
| `8/8/8/8/8/3R4/1k1K4/8 w` | 7 | mate 4 | `d3e3` |
| `8/8/8/8/8/3R4/1k6/3K4 w` | 7 | mate 4 | `d1d2` |
| `8/8/8/8/8/3R4/1k6/3K4 b` | 8 |  | `b2b1` |

`b3f3` does force mate. It does not give check. Black to move after it still has 16 plies, so the whole line is 17 plies, UCI mate 9. The engine's "mate 17" is 33 plies, 16 plies longer than that line and 18 plies longer than the shortest win.

The depth-2 store that looked impossible is on `8/8/8/8/8/3R4/1k1K4/8 w`. Truth there is 7 plies (score at ply 10 would be `32000 - 17 = 31983`). A stored "15 plies remaining" is 8 plies longer than the truth. A lower bound of a longer mate can still be a weak true bound, because a shorter mate has a higher score. It is not evidence that the position is a 15-ply mate.

`8/8/8/8/8/3R4/1k6/3K4` is 7 plies with white to move and 8 with black to move. It is not a 14-ply loss.

Score coding used by the engine, from `search.cpp`:

```
MateValue = 32000
MateInMaxPly = 31872
mate_in(ply)  = 32000 - ply
mated_in(ply) = -32000 + ply
```

A positive mate score `S` means the side to move mates in `32000 - S` plies counted from the root, not from the current node. UCI mate `N` is `(plies + 1) / 2`. So mate 8 is 15 plies and score 31985. Mate 17 is 33 plies and score 31967. Mate 9 is 17 plies and score 31983.

`score_to_tt` adds the ply for a positive mate and subtracts it for a negative mate. `score_from_tt` does the reverse. A stored value of `32000 - remaining` is the ply-independent form. Reading it at a new ply puts the root distance back. That conversion is consistent. The wrong numbers are the distances being stored, not an extra add on every read.

## What is wrong

Quiescence copies a hash mate bound into the stand-pat score and can return it after searching no moves. A PV node then stores that number as an exact score at a depth that did not prove it.

In `qsearch`, after the non-PV cutoff, a hit replaces the static eval whenever the bound is exact, or a lower bound beats the eval, or an upper bound is below the eval:

```1032:1037:forge-combo29/src/search.cpp
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
        best_score = eval;
```

A mate score is far below a normal eval, so an upper-bound mate always wins that test. `best_score` becomes the mate. If every capture is pruned, or there is no capture, the loop searches nothing. The checkmate return only runs when the side to move is in check and `move_count == 0`. Otherwise the function stores and returns `best_score`. The mate bound has become the value of the node.

An instrumented copy of this file (compiled under `/tmp`, not committed) logged the first two such returns during the depth-13 search, NNUE off:

```
QSBOUND ply 13 score -31983 ttbound 1 ttdepth 4 alpha -495 beta -471 moves 0
        fen 8/8/8/8/8/8/2KR4/k7 b
QSBOUND ply 15 score -31979 ttbound 1 ttdepth 6 alpha -495 beta -477 moves 0
        fen 8/8/8/8/8/8/3R4/1k1K4 b
```

`ttbound 1` is `BoundUpper`. `moves 0` means the mate score was returned with no move searched. The window is still a centipawn window. For the first of those two positions the true distance is 4 plies, and `-31983` at ply 13 is remaining 4, so that particular bound happened to be tight. The mechanism does not require the bound to be tight. The next store shows the loose one becoming exact.

The main search stores a PV score as exact whenever any move raised alpha and the score did not reach beta:

```1482:1485:forge-combo29/src/search.cpp
    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
        store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
```

Quiescence uses the same rule at depth 0 (`search.cpp` line 1103). Beta at that moment was -441, a centipawn. A mate score for the loser sits below that beta, so it does not fail high. It does raise alpha. The node writes `BoundExact` and the depth it was called with.

The first exact write of the poisoned entry in the depth-13 search:

```
ORIGIN ply 7 depth 6 score -31979 alpha -31979 beta -441
       moves 3 pvlen 6 move b2a1 incheck 0
       fen 8/8/8/8/8/3R4/1k6/3K4 b - - 7 4
```

`score_to_tt(-31979, 7)` is `-31986`. At ply 7 that score claims 14 plies remaining (`32000 - 31979 - 7`). The true distance of this position is 8 plies. The PV is 6 plies long on a depth-6 node, so the extra distance came from the leaf, not from six moves of proof. The same entry is later read at other plies (`ttdepth 6`, stored `-31986`, bound exact) and the root ends up on score 31967.

31967 is `32000 - 33`. It is what you get by taking a 15-ply-remaining value (`31985`) and applying `score_from_tt` at ply 18: `31985 - 18 = 31967`. The root then prints mate 17. The PV that comes with it is the moves that were actually walked, 15 of them, and those moves do not mate.

A second store bug pairs that score with the wrong move. Both `store_body` copies write the move before they decide whether the score and depth replace the old entry:

```327:328:forge-combo29/src/search.cpp
    if (!move.is_none() || !same_position) entry->move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {
```

The same two lines are at 396–397 in the other copy. A shallow store can replace the move of a deeper mate and leave the mate score in place. `b3f3` on the root is a move that wins in 17 plies, while the score next to it says 33. The move and the score are not one result.

`BoundExact` is also an unconditional replace: a shallow exact entry overwrites a deeper one of the same position. Combined with the quiescence stand-pat, a depth-0 or depth-6 exact mate can occupy the entry the next iteration trusts.

## What a fix has to do

Helpers still have to read and write the shared hash. Turning the hash off, clearing history every search, or dropping to one thread does not fix this. Threads 1 already produces the false mate 17.

The small change that matches the trace:

- In quiescence, a non-exact mate bound may still cut a non-PV node when it fails high or fails low. It must not become the stand-pat value that is returned after searching no moves.
- A mate may be stored as `BoundExact` only when this node's searched depth can prove that many plies. A fail-high of a longer mate can stay `BoundLower`. That bound is weak, and it is still true if a shorter mate exists.
- Write `entry->move` only when the score and depth are replaced, or when the old move is empty. Do it in both copies of the store.

None of that is applied on this branch.
