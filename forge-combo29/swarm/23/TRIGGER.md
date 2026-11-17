# THE DRAWN-ROOT TRIGGER, in one page — lead with this

**The base build returns `bestmove` with 0 nodes and score `cp 0` if and only if the position at the END of the sent
move list — the one being searched — has occurred at least three times in that list.** That is the whole trigger,
established as a monotone threshold and not as a set of bailing fixtures (23-F125), and refined to follow the SEARCHED
position rather than the game's initial one (23-F140: 1 ply past a repetition → searched position occurs once → the
engine searches normally; 3 plies past → it occurs three times → the engine bails).

### Start here if you are deciding whether this affects you: it is not an endgame artefact

**On a DENSE MIDDLEGAME position with about thirty legal moves the threshold is the same.** `r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w - -`, cycle `f3g5 g8e7 g5f3 e7g8`:

| searched position occurs | nodes | verdict |
|---|---|---|
| 2 | 29,994 | searches |
| **3** | **0** | **BAIL** |
| 4 (12-ply list) | **0** | **BAIL** |

And it holds when the repeated position sits at the END of a long list rather than at the root — 10-ply preamble, 2 →
searches (17,399 nodes), 3/4/5 → bails (23-F141). So neither the branching factor nor the list position changes the rule.

### The clean arithmetic, on a sparse endgame where the counts are easiest to check

| true occurrences | nodes | verdict |
|---|---|---|
| 2 | 7,581 | searches |
| **3** | **0** | **BAIL** |
| 4 | 0 | BAIL |
| 5 | 0 | BAIL |
| 6 | 0 | BAIL |

Same board, same castling-neutral cycle, every fixture validated by `job59/validate.py` with two independent counters
agreeing and asserted to its exact count before the engine was called.

## The standard rebuttal to any future "this 0-node cell breaks the threshold" report

If a reader finds a position returning 0 nodes that is NOT a threefold, do not revise the threshold — first run the
confound test. **Re-send the same position with the variable under test REMOVED (here: with no move list at all) and see
whether the 0-node result persists. If it does, you have measured a different draw rule, not a counter-example.**

That is exactly how the one apparent counter-example in this seat was resolved (23-F132): bare kings returned 0 nodes at
TWO occurrences, and also returns 0 nodes with no history whatsoever, because insufficient material is an automatic
draw. One command separates the two. Other rules that produce genuine 0-node cells and are NOT the repetition threshold:
insufficient material (automatic), halfmove >= 100 (automatic, 23-F126), and a refused position (not a draw at all).
A threefold cell is the only one whose zero disappears when the move list is removed — **measured, not assumed
(23-F134)**: threefold with list = cp 0 / 0 nodes, same root as a bare FEN = cp 381 / 7,581 nodes; halfmove-100 = cp 0 /
0 nodes either way; insufficient material = cp 0 / 0 nodes either way. So the test distinguishes the repetition bail
from the two automatic draw rules, which persist.

## The three facts that complete it

1. **FIDE identity, not placement** — and the count that matters is the SEARCHED position's, not the root's. The key is placement + side to move + castling rights (plus en-passant only when a
   legal ep capture exists). A cycle that disturbs castling does not produce a repetition — the engine is correct to see
   one occurrence, and it does (23-F122).
2. **The move played is the engine's own generator index 0**, unsearched (23-F98, confirmed on a middlegame board at
   23-F100). Order is fully specified: piece types P→N→B→R→Q→K with absent types skipped; within pawns, single push →
   double push → capture; within a class, ascending from-square (23-F103/F106), 13/13 on a holdout and 5/5 in a
   predictor that was committed before the engine was asked (23-F105).
3. **The halfmove rule cuts in at 100, not 75** — so a seventy-five-move root is subsumed rather than ignored, and the
   `99` cell searches 200 nodes with `cp 0` before the hard cut at `100` (23-F126).

## What it costs

- **The score is largely SOUND.** On an **automatic** draw (insufficient material, where no claim exists) **both builds
  report `cp 0` — neither build is wrong** (23-F128's R4). On a **claimable** draw the two builds differ in whether to
  claim (base `cp 0`, PC `cp 425` on the R3 root): **both are defensible, and it is not a correctness defect in either
  build.** R3 is documented here in that form deliberately, and a later reader who turns it into a defect has changed the
  finding into something the evidence does not support. **BUT IT IS NOT A "POLICY" EITHER — 23-F169 refutes that reading:
  on a drawn root with NO forced win available the PC reports `cp 0`, i.e. it does claim. The `cp 425` on R3 was the
  MATE talking, not a rule against claiming. So the accurate contrast is "the PC finds the win where one exists and
  reports the draw where none does", which is correct behaviour, not a different policy.**
- **The `cp 0` CAN ALSO UNDERSTATE A WIN — the sharpest single case in the family (23-F171).** On a genuine threefold
  root where White has **mate in one** (`6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w`), the base reports `cp 0` and plays `f2f3`,
  **forfeiting the mate**; the PC reports `mate 1` and plays `b1b8`. So the score is defensible only as "drawn if the draw
  is claimed" — and a winning side never claims — while the MOVE loses a forced mate. A tool showing that `cp 0` tells a
  user a game is drawn that is won in one move.
- **The MOVE is where the base's damage is** — and the cost figure belongs to the MOVE, not to the score. Two DISJOINT
  12-position samples give medians of **~625 cp** and **~1,004 cp** with nine or ten of twelve at ≥ 300 cp (23-F101,
  23-F144), so the honest form is "roughly 600 to 1,000 cp, sample-dependent" rather than a single number. On a real
  self-play board the unsearched move lost **6 pawns of material** by allowing a queen capture (23-F60, re-verified under
  the corrected validator in 23-F129).
- **The PC's repair removes the 0-node path, which is what produced both losses** — and on ONE of two measured boards
  it also picks a materially better move (F60 board 1: base loses +6, PC +0) while on the other it is **material-neutral**
  (F60 board 2: base +1, PC +1, 23-F130). So the honest form of the advice is: the repair buys honesty about the score
  and removes the unsearched move; it does not reliably buy material safety. `go depth` only, two boards.

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

## Two axes this family could not test, and why they fail for the same reason

Both were attempted properly and closed honestly. Stated together because the shared reason is stronger than either
entry alone, and because it should stop the next reader attempting either.

| axis | what it needed | why it could not be built |
|---|---|---|
| **spacing** of the three occurrences (root at 0/4/8 vs 0/8/16 vs 0/4/12) | an anchor position reachable by **two paths of different length**, so the count can stay at three while the spacing changes | with one position anchoring both count and spacing, `A + B + A` always yields **four** occurrences, not three — for every neutral filler tried (23-F142) |
| **a mate that needs search** at a threefold root (mate in 3+) | a position with **both** a neutral repetition cycle and a forced mate of 3–7 plies | the quiet positions that admit a clean shuttle have mates 15–23 plies away; the busy positions that give short mates rarely admit a clean shuffle (23-F174) |

**The shared reason: repetition cycles live in quiet, sparse positions and short forced mates live in busy ones.** A board
that gives you one withholds the other. That is a fact about chess positions, not about this engine, and it is the reason
both axes are recorded as *untested with a structural reason* rather than as negative results.

What is NOT withheld: the mechanism itself. The base plays the generator's first move without looking (23-F98/F172), and
where that move forfeits a mate in 1 it did so on 4 of 4 fixtures — one back-rank structure, four variations (23-F175).
