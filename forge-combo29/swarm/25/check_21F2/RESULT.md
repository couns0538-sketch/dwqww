# 21-F2 CHECKED ON THE PC BUILD: the wrong-side claim does NOT reproduce (REFUTES, with a build caveat)

Seat 21 (21-F2) claims: after a refused FEN the engine keeps the previous position but still answers `readyok`, so
a GUI syncing on readyok is handed a move **for the wrong side** - "with the FEN refused the 2nd answer is `g8e7`,
Black's move in the old game".

## My check (PC r15/PC20, Threads 1, Hash 16, 19-F12-safe: stdin open, read to bestmove/perft before anything else)

Old position, **White to move**: `rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4`
- `go perft 1` -> **nodes 5**; python-chess says White has **5** legal moves. `go depth 8` -> `f1e2`.

Then a **refused** FEN with **Black to move**: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 b KQ - 0 1`
- refusal line: `info string invalid FEN: castling right without king and rook` (correct)
- `readyok` still answered: **yes** (that half of the claim is TRUE)
- `go perft 1` -> **nodes 5** again; python-chess says **Black** would have **44** legal moves on the old board
- `go depth 8` -> `f1e2`, the same White move as before

## Verdict

**The engine keeps the old position with WHITE to move.** perft 1 = 5 is White's count, not Black's 44, so the
side to move did **not** flip. The move handed back is the old position's own White move, which is the correct
move for the position the engine is actually in.

So on this build:
- **TRUE:** a refused FEN is answered `readyok`, and the engine silently keeps the previous position. A GUI that
  only syncs on readyok cannot tell that its `position` command was rejected. That is a real GUI hazard and it is
  what 21-F2 is really about.
- **NOT TRUE here:** the move is for the wrong side. It is the right move for the retained position.

## Caveat, stated plainly

Seat 21 measured on their own build (`job6/f2_safe.py ~/b/release/forge`) and on a different position pair than
mine. Their specific example (`g8e7` as "Black's move in the old game") may be reproducible in their setup and my
scenario may simply differ: their claim needs a case where the *retained* position's side to move is Black while
the GUI believes it is White. My construction could not produce that, because the engine retained the position
faithfully including its side to move. I am reporting this as **refuted in my scenario on the PC build**, not as
proof that their observation was wrong.

## The part worth keeping for the owner

A GUI must not treat `readyok` as confirmation that `position fen` was accepted. It must watch for the
`info string invalid FEN: ...` line. That is the actionable half of 21-F2 and it stands on my check too.
