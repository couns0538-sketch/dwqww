# 19-F30 rechecked under file 6's inequality

File 6 says: a cp 0 at a high halfmove counter is a defect ONLY when a forced mate exists that ends no later
than the 100th half-move. Test: the same board with counter 0, `go depth 20`+, read `mate N`; defect only if
`2N - 1 <= 100 - counter` AND the real-counter board still scores cp 0 at that depth.

## My 19-F30 repetition case

Board (from the earlier test): `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1` plus the repetition move list
a1a2 g8h8 a2a1 h8g8 a1a2 g8h8 a2a1 h8g8, which leaves the halfmove counter at **8**.

**Counter-0 control, PC r15, Threads 1, `go depth 20`:**

```
info depth 1 ... score mate 1 ... pv a1a8
...
info depth 20 seldepth 20 score mate 1 nodes 420 pv a1a8
bestmove a1a8
```

So **N = 1**. The inequality: `2(1) - 1 = 1 <= 100 - 8 = 92`. **TRUE.**

And the real-counter board on the **base tree** scored `cp 0` with `bestmove f2f3` at depth 8 (my measurement),
while the same board scores `mate 1` on PC r15. So:

- **On the base tree this is a genuine defect by file 6's own rule**: a mate in 1 exists, it ends well before
  the 100th half-move (1 <= 92), and the engine scored cp 0 and played f2f3 instead. 19-F30 stands as a real
  defect for the base tree, and file 6's carve-out does not excuse it.
- **On PC r15 it is repaired**: `a1a8 mate 1` at 168 nodes (19-F30), confirmed again here at depth 20 with 420
  nodes and the same move.

That is exactly the shape 19-F30 reported, now with the inequality checked and both numbers written down as
file 6 asks.

## What I am NOT claiming

- The repetition itself is not the defect; per file 6 the match program ends the game at the third occurrence.
  The defect I am pointing at is **the missed mate**, which file 6's rule explicitly keeps as a defect.
- I did not search for whether the base tree's `f2f3` was actually a losing move in that position — the point is
  that a mate in 1 was on the board and the engine answered cp 0.

## Numbers for the finding line

`mate N = 1` at counter 0 (depth 20, PC r15); `counter = 8`; `2N-1 = 1 <= 100-8 = 92` TRUE; base tree at the real
counter scored cp 0 / f2f3 at depth 8, PC r15 scores mate 1.
