# COST OF THE CLOCK-99 DEFECT, AND THE REPAIR'S CONSEQUENCE

Seat 25, area 5. Build PC r15, settings PC20, Threads 1, Hash 16, depth 10. Evidence: `cost.txt`, `cost2.txt`.

## 1. The cost, quantified

### The asymmetry (a real result, and the reason the fault is narrower than I first thought)

A WON position at clock 99 does NOT collapse. Three winning boards, clock 0 vs clock 99:

| board | clock 0 | clock 99 |
|---|---|---|
| queen up | cp +2232 (d1f3, 24,872 nodes) | cp +1965 (a2a4, 13,415 nodes) |
| rook + 2 pawns up | cp +423 (b2b3) | cp +417 (b2b3) |
| queen + rook up | cp +2570 (a2a4) | cp +2563 (a2a4) |

So the shortcut does not hurt the winning side. That is expected, and it is diagnostic: a claimable draw scored
as 0 is only *attractive* to the side that is losing, so the fault can only bite the losing side.

### The cost on the losing side, end to end

Board `r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w`, white is lost:

```
clock  0 : cp -155   nodes 15,261   best d1c1
clock 98 : cp -102   nodes 18,859   best a1c1
clock 99 : cp    0   nodes    341   best a1a2
clock 100: cp    0   nodes    341   best a1a2
```

Then the decisive sequence, with the engine playing BOTH sides:

1. white plays its clock-99 choice `a1a2` (a quiet shuffle) -> clock reaches 100, black to move
2. black's search says `cp +180` for black, and it plays **`h7h6`** - a pawn push, which is clock-RESETTING
3. clock returns to 0 and white is still lost: the engine now scores the position `cp -189` for white

So the "draw" white played for was never available: it required black's consent, and black's own search refuses it
instantly because black is winning. White has thrown away its clock-0 defensive try (`d1c1`, -155) for a shuffle
that leads to -189.

**How it should be described:** this is a scoring and move-choice defect that costs the losing side its best
defensive continuation. It is NOT "the engine claims a draw and the game is drawn" - the draw is never awarded. I
am not calling it game-losing outright, because on these boards white was already lost; what it loses is the
difference between a -155 defence and a -189 one, and in a position where a real drawing resource existed it would
lose that too. To find such a position you would need one where the clock-0 best move reaches a genuine draw and
the clock-99 shuffle does not - that is the case worth searching for next, and I have not found one.

## 2. The repair: what it means, not just its form

You asked: if a claimable draw is not terminal, does the search need to know about it at all, or should the
fifty-move test leave `is_draw` entirely and live only at the root?

**My answer: remove it from `is_draw`; do not put it at the root either.**

Reasons, in order of weight:

1. **A claimable draw is not a terminal position.** `is_draw` is a *node-terminality* test: it answers "can this
   node be scored without searching?". A claimable draw cannot, because whether it happens depends on a decision
   the opponent has not made yet. Putting a non-terminal condition in a terminality test is the bug itself, not a
   placement question.

2. **At the root it would be wrong in the same way.** At clock 99 the root is not drawn (the side to move can
   reset); at clock 100 it is *claimable* by the side to move only if that side wants it. A root test would have
   to ask "does the side to move prefer a draw to playing on?", which is a search question, not a root question.
   The search already answers it correctly once the child is not pre-scored as 0.

3. **The rule still has to be represented, just not as terminality.** The honest model is: the fifty-move counter
   is a *resource* that bounds how long a line can stay quiet. The engine already tracks `halfmove_clock` per node
   and already stores `rule50_clock` in the TT and gates re-use with `near50` (src/search.cpp:1444, 1646-1651).
   The counter does its work there. What must not happen is turning it into a hard 0.

**Risk of my choice, stated plainly:**
- A line that runs quiet to the horizon becomes worth its static evaluation again instead of 0. At the horizon
  that slightly *overvalues* positions that are about to be drawn - the search will think a dead-drawn
  opposite-coloured-bishop endgame is still worth its eval. That is a known, bounded inaccuracy, and it is the
  direction the PC's own `FORGE_FIX_ROOT_DRAWN` already chose for the root (a drawn root is searched like any
  other), so the repair is consistent with the owner's existing decision rather than a new policy.
- Searching the fifty-move region costs nodes that used to be free. The 341-node answers become 15k-19k-node
  answers. On the clock that is real; the engine's time manager already handles it, but a movetime search in such
  a position will now return shallower results than before.
- The one thing this does NOT fix: a genuinely forced fifty-move draw (no reset available to either side) would
  then also be searched instead of short-circuited. That is strictly wasteful, and it is the case where
  `EvalRule50Damp` and `near50` TT gating already keep the cost down. If the owner wants that case cheap, the
  correct place for a hard 0 is exactly there and only there: clock >= 100 AND neither side has a capture or pawn
  move - which is a predicate `is_draw` can legitimately test, unlike a bare clock comparison.

**One-line summary of the repair:** test "no reset move exists anywhere" instead of "the clock reached 100"; a
clock value alone is not terminality.

## What I did NOT do
- I did not implement or test that repair (the patch stays EXPERIMENT and unchanged, as instructed). The
  predicate above is a proposal with a stated risk, not a verified fix.
- I did not find a position where the clock-99 shuffle loses an AVAILABLE draw. That is the case that would make
  the defect clearly game-losing, and it is the first thing I would search for with more time.
