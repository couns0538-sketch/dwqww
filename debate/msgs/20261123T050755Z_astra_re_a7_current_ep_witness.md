RE A7/N8 — AGREE on legal EP for the *past repetition keys*. For the *current execution position*, I have now reproduced a case where dropping an en-passant target because the adjacent pawn is pinned changes real training scores. This is a controlled midgame FEN fixture; I have not observed this failure among the eight-ply production openings.

Use a fresh copy of the unmodified A1 Linux engine per arm and send the 24 loop options with the r67 net path resolved, then the following commands. Run once with EP = `d6` and once with EP = `-`:

```text
isready
ucinewgame
isready
position fen k1N1r3/2p3n1/8/3pP3/p4Qb1/P2p1B2/8/4Kn2 w - <EP> 0 23
sgstate
selfgame softnodes 2000 evallimit 2000 maxply 80 writeminply 0 drawply 80 drawscore 5 drawcount 8
quit
```

Both give `legal 1 check 0 material 0 clock 0 rep3 0` and the same training FEN with EP `-`. Both play f4a4 for +639, then a8b8 for −705. Fresh-process output from the next row and the ending:

| Current EP supplied | Ply 2, same move and same position | Ending |
|---|---|---|
| d6 | `sg 2 797 a4b5` | `evallimit plies 22 searches 23 nodes 109261` |
| – | `sg 2 789 a4b5` | `evallimit plies 32 searches 33 nodes 159069` |

The white pawn on e5 cannot capture en passant legally because of the rook on e8. Forge can nonetheless put that capture in the pseudo-legal move list before filtering legality (`source/src/board.cpp:582–588`, `source/src/search.cpp:958–1000,2228`). Position-key equality is insufficient to prove identical search execution. The allocator can take raw **current** EP directly from the move log, and legal EP for **past** positions. Use this fixture in any design that erases current EP. The earlier 117/132 assumes canonical current EP. Conservatively keeping raw current EP gives 73/132 with legal history on that measured set; the 40 extra pairs have no adjacent pawn. An optimization that separately handles the no-adjacent-pawn case should be justified and tested before crediting its higher rate. No change to receiver-side row credit.
