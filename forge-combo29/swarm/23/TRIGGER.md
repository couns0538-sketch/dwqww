# THE DRAWN-ROOT TRIGGER, in one page — lead with this

**The base build returns `bestmove` with 0 nodes and score `cp 0` if and only if the ROOT position's FIDE identity has
occurred at least three times.** That is the whole trigger, established as a monotone threshold and not as a set of
bailing fixtures (23-F125).

| true occurrences of the root | nodes | verdict |
|---|---|---|
| 2 | 7,581 | searches |
| **3** | **0** | **BAIL** |
| 4 | 0 | BAIL |
| 5 | 0 | BAIL |
| 6 | 0 | BAIL |

Same board, same castling-neutral cycle, every fixture validated by `job59/validate.py` with two independent counters
agreeing and asserted to its exact count before the engine was called.

## The three facts that complete it

1. **FIDE identity, not placement.** The key is placement + side to move + castling rights (plus en-passant only when a
   legal ep capture exists). A cycle that disturbs castling does not produce a repetition — the engine is correct to see
   one occurrence, and it does (23-F122).
2. **The move played is the engine's own generator index 0**, unsearched (23-F98, confirmed on a middlegame board at
   23-F100). Order is fully specified: piece types P→N→B→R→Q→K with absent types skipped; within pawns, single push →
   double push → capture; within a class, ascending from-square (23-F103/F106), 13/13 on a holdout and 5/5 in a
   predictor that was committed before the engine was asked (23-F105).
3. **The halfmove rule cuts in at 100, not 75** — so a seventy-five-move root is subsumed rather than ignored, and the
   `99` cell searches 200 nodes with `cp 0` before the hard cut at `100` (23-F126).

## What it costs

- **The score is largely SOUND.** On an automatic draw (insufficient material) both builds report `cp 0`; on a
  claimable draw the two builds differ in whether to claim, and both are defensible (23-F128).
- **The MOVE is where the base's damage is** — and the ~625 cp figure belongs to the MOVE, not to the score (23-F101:
  median over 12 deterministically sampled middlegame positions, ten of twelve ≥ 300 cp, measuring the cost of playing
  generator index 0). On a real self-play board the unsearched move lost **6 pawns of material** by allowing a queen
  capture (23-F60, re-verified under the corrected validator in 23-F129).
- **The PC's repair fixes BOTH on that board**: it searches ~20k nodes, reports `cp 0`, and plays a move that loses no
  material (23-F129). So the practical advice is that the repair is adequate for the move and the score where it was
  measured; whether it stays adequate where the unsearched move loses more than 6 pawns is untested.

## The one-line chain

Drawn-root defect: exists (23-F44) → present on the clock path (23-F57) → reached by an actual clock game (23-F58) →
the 0-node move is generator index 0 (23-F98) → **the bail fires iff the root has truly occurred three times, a monotone
threshold (23-F125)** → the score is right where the draw is automatic, and the cost is in the move (23-F128).

## The correction that produced this page

Everything here was blocked for hours by a defect in MY fixture validation: the occurrence key omitted the castling
field, so "root occurs 3 times" meant "placement+side occurs 3 times". Two boards that searched were miscounted as
threefolds. That one arithmetic defect generated **four successive scope explanations** — sparse endgames, castling as a
conditioner, material, halfmove — before it was found (23-F122/F123). The validator that prevents it is
`job59/validate.py`; the rules for using it are `FIXTURE_RULES.md`; the practical test is **check the castling field
along the LINE, not in the FEN**.
