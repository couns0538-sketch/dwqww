# S-F16 — the REPETITION side of the same defect: the engine plays for a draw the opponent can simply decline

Seat 12, area 2. This extends seat 25's mechanism (`swarm-25: debug/MECHANISM.md`, `debug/CORRECTION.md`)
from the fifty-move counter to **threefold repetition**, and it is the test my earlier negative S-F15
could not do.

**Threads 1 throughout** (no `Threads` option sent). Builds: base release 6b98f217, and PC r15
(base + `pc_r15.patch`, `-DFORGE_MATE_ALPHA_GUARD=1`), pinned 8/8 in `job3/PC_BUILD.md`.

## The mechanism, in seat 25's frame

Seat 25 established: `Worker::is_draw` (`src/search.cpp:1426-1436`) returns draw for a node whose
halfmove clock is 100, and that is *correct for that node* — but the fifty-move draw must be
**claimed**, so the opponent who is winning simply plays a pawn move or capture and the clock resets.
Scoring it 0 unconditionally treats a claimable draw as a forced one, and a lost position at clock 99
is then valued at 0.

The same `is_draw` return contains `board.is_repetition(root_history_index_)`. A threefold is *also*
claimable, by either side, and is also refusable: the opponent who is winning simply deviates. So the
same defect should appear on the repetition side.

## The position that shows it

```
4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40     then moves  a1a2 e8d8 a2a1 d8e8 a1a2 e8d8 a2a1
-> 3k4/8/8/8/8/8/4P3/R3K3 b - - 7 43   black to move, black is a rook down
```

Black's move `d8e8` brings the position back for the **third** time. The resulting node is

```
4k3/8/8/8/8/8/4P3/R3K3 w - - 8 44     White to move, White is a rook up
```

— threefold true (python-chess confirms), **White to move and winning**. White would **not** claim a
draw; White plays `Ra1-d1` or anything else and continues to win. So Black's `d8e8` is not a draw and
must not be scored as one.

## Measured — the three-way comparison that isolates it

| case | base | PC r15 | what it means |
|---|---|---|---|
| **`d8e8` only** (creates the threefold; White to move and winning) | **cp 0 / 20 nodes** | **cp 0 / 20 nodes** | the child was scored as a *forced* draw |
| `d8c8` only (same root, **no** repetition) | cp -1044 / 5,832 | cp -1072 / 10,757 | the same position, searched properly: Black is lost |
| the same board by plain FEN, no history | cp **+1128** / 14,216 | cp **+1209** / 22,827 | White is winning, exactly as the material says |

The middle row is the control that matters: from the *same root*, with the *same side to move*, a
non-repeating Black move is scored about **-1050** and the repeating one is scored **0**. The
difference is entirely the repetition term. And the third row shows what the position is really
worth — **+1128 for White** — so scoring Black's move 0 understates by more than 1000 cp.

## It is not a horizon effect, and no depth fixes it

Root search, depths 6 to 20, both builds, identical at every depth:

| depth | base | PC r15 |
|---|---|---|
| 6 | cp 0 / 38 nodes / pv d8e8 | cp 0 / 38 / d8e8 |
| 8 | cp 0 / 50 | cp 0 / 50 |
| 10 | cp 0 / 64 | cp 0 / 64 |
| 12 | cp 0 / 96 | cp 0 / 96 |
| 16 | cp 0 / 220 | cp 0 / 220 |
| **20** | **cp 0 / 342 / pv d8e8** | **cp 0 / 342 / d8e8** |

The PV never grows past one ply and the node count only creeps: the search is cut at the child every
time. **More time cannot recover this** — this is the same non-horizon property I measured for the
fifty-move case (`job4/pc_node_level_depth_sweep.txt`, depths 6-24 all `cp 0`), now on the repetition
side.

## The consequence in a game

Black, a rook down, plays `d8e8` believing the game is drawn. White, who is winning, plays any
non-repeating move — the engine's own next ply would be White's choice, and White has no reason to
cooperate. So the engine has chosen a move whose value rests on the opponent's consent. That is
exactly seat 25's sentence for the fifty-move case, and it holds here word for word.

## Which build, and what is already fixed

- **The root door is repaired on r15** and this is *not* that door: at the root, when the *losing*
  side is to move at a threefold, `cp 0` is **correct** (the loser claims). I verified that separately:
  the losing side to move at a threefold gives `cp 0` on both builds, correctly.
- **The claimable-draw door is open on both builds**, and `FORGE_FIX_ROOT_DRAWN` does not touch it,
  because the zero is produced by `is_draw` **one ply down**, not by the root adjudication — the same
  reason my S-F14 (fifty-move) is still open.

## So: rotation and fifty-move share one flaw

**Yes.** Both are `is_draw` returning draw for a *claimable* draw, and both are wrong for the same
reason (the drawing side must consent). The evidence is parallel:

| | fifty-move | repetition |
|---|---|---|
| where | `is_draw`, clock >= 100 | `is_draw`, `is_repetition` |
| my position | `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` | `3k4/8/8/8/8/8/4P3/R3K3 b - - 7 43` (after 7 plies) |
| engine | cp 0 / 36 nodes | cp 0 / 20 nodes |
| truth | mate -1 for the loser | about -1050 for the loser |
| control with the drawing resource removed | clock 100, no reset anywhere: cp 0 correct | non-repeating sibling move: cp -1044 |
| depth sweep | 6-24 all cp 0 | 6-20 all cp 0 |
| repaired on r15? | **no** | **no** |

## The fix, in one sentence

**In `Worker::is_draw`, do not return draw for a claimable fifty-move or repetition node when the side
to move can still avoid the draw (a clock reset, or a deviation from the repetition) — i.e. score the
draw as available only to the side that would want it, so the winning side's continuation is not
short-circuited to 0.**

Cost and risk: `is_draw` is on the hottest path in the search, so this needs care and a bench; I have
**not** written or tested that patch.

## How to see it again

```
python3 forge-combo29/swarm/12/job5/repetition_claimable.py
```

Raw committed: `job5/repetition_claimable.txt` (the three-way comparison, both builds),
`job5/repetition_depth_sweep.txt` (depths 6-20, both builds).

## Suspicions, not proven

- Whether a position of this shape occurs in the owner's games; unknown without his PGNs.
- Whether `Board::is_repetition(root_history_index_)` can also fire on a *single* prior occurrence in
  a way that reaches this path more often than a genuine threefold; I did not audit its counting.
- Whether the repetition claim is also refusable in the engine's own model of the *opponent's*
  options; I measured the score, not the internals of the root history bookkeeping.

## What I got wrong earlier, and correct here

My S-F15 said the repetition member "could not be triggered". That was true only for the case I
tried — a **fifty-move-clock repetition at the root where the losing side was to move**, which is
correctly scored because the loser claims. The member *is* reachable, but it needs the **winning**
side to be to move at the repeated child, which takes a move sequence that creates the repetition
with the opponent's move. S-F15 is superseded by S-F16 and I have said so in FINDINGS.md.
