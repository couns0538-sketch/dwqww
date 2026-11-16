# THE MECHANISM, EXACT

Seat 25, area 5. Instrumented build (EXPERIMENT patch, stderr-only, behind `FORGE_CLOCK99_DEBUG`), PC r15 source
under PC20 settings, Threads 1, Hash 16. This answers the question I had left open as S-F14 and it CORRECTS how
I had been describing the fault.

## The answer, in one sentence

At halfmove clock 99 the engine is not taking a hidden shortcut and not mis-reading the score: **every quiet root
move leads to a child at clock 100, `is_draw` correctly returns draw for that child, the root therefore scores the
position 0, and that is a legitimate maximum over its children - but the engine never compares it against the fact
that white is really -153 cp, because it has no way to prefer a reset move it has just scored as worse.**

## The evidence, in order

**1. No root shortcut fires.** The instrumentation at every root early-return site, on the breaking board at
clock 99:
```
[DBG root] clock=99 legal=27 cands=27 root_drawn=0 insuf=0 rep=0 cands_empty=0
[DBG ROOT ITER SEARCHED] depth=1 score=0 pv_len=1 clock=99
... depth=2..6: score=0 pv_len=1
```
There is no `[DBG ROOT-SHORTCUT PATH TAKEN]` line and no `[DBG EMERGENCY/HARDLIMIT PATH]` line. So `root_drawn`
is false, `root_candidates` has all 27 moves, and the search RUNS. My earlier "root shortcut" reading (S-F14) was
inferred from the node count and the 1-ply PV; the instrumentation shows that reading was WRONG in mechanism,
though the observation (0 score, tiny nodes) was right.

**2. `is_draw` fires on the CHILDREN, at clock 100, as the rule says.** 109 `is_draw TRUE` lines on that search,
every one of them `clock=100 fifty=1 rep=0 insuf=0 nomove=0`, e.g.
`fen=r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 b - - 100 1` (white played a quiet rook move a1a2).
So: quiet move -> child clock 100 -> correctly a draw.

**3. Every root move searched ALONE, at depth 6, same settings (`experiment_4.txt`):**
```
a1a2 quiet -> cp    0  (pv 1)
a1c1 quiet -> cp    0  (pv 1)
a1b1 quiet -> cp    0  (pv 1)
e3e4 reset -> cp -356  (pv 4)
a3a4 reset -> cp -218  (pv 5)
h2h3 reset -> cp -220  (pv 5)
g2g3 reset -> cp -476  (pv 4)
b2b3 reset -> cp -212  (pv 4)
h2h4 reset -> cp -224  (pv 4)
g2g4 reset -> cp -245  (pv 5)
b2b4 reset -> cp -488  (pv 5)
```
The root's reported 0 IS the maximum of its children (0 > -212...). **So the root arithmetic is consistent.**

**4. The same board at clock 0, same experiment:** the best single move is -159 and the root reports -174; the
position's real value is in the -150s. So at clock 99 the whole position is being valued at 0 when it is worth
-153 cp to white.

**5. Why the zero is wrong rather than merely pessimistic:** at clock 99 the side to move can still RESET the
counter, and I showed (`experiment_2.txt`) that after a reset the game continues with white +166..+823. The
search values each reset move at -212..-488 because after the reset it assesses the *resulting position* (which
it searches with the clock back at 0) as bad for white. So both numbers are individually defensible; what is not
defensible is reporting **cp 0** for a position white cannot draw: nothing can force the fifty-move draw here,
because white is not obliged to play a quiet move, and every quiet move is only "drawn" if black cooperates.

## Precise formulation of the defect (this replaces S-F14's guess)

`is_draw` is called on a node whose clock is 100 and returns "draw" for it. That is correct **for that node**. But
the parent then treats the resulting 0 as an ordinary score and takes the max over its children - so a line that
reaches clock 100 by a quiet move is worth exactly 0 to the parent, equal to a real draw, and a REAL draw is worth
0 too. At clock 99 the maximiser therefore prefers "quiet move, child is a fifty-move draw" (0) over any reset
move the search happens to value below 0, and reports 0 for a position that is lost.

The root cause is not a wrong `is_draw`. It is that **the fifty-move draw score of 0 is not distinguished from a
 draw in the parent's comparision**, so at clock 99 a lost position is reported as a draw whenever every reset
move looks worse than 0. In a real game this is exactly the situation where the engine will shuffle and claim a
draw it is not entitled to (it must first actually reach clock 100 without a reset, which it cannot force).

## What remains unproven
- I have not shown a position where this costs a game against a resisting opponent (the reachability proof shows
  the position is reachable, not that the engine loses from it).
- I have not tested whether the PC's `FORGE_FIX_ROOT_DRAWN` was intended to cover exactly this and does not.
- The mechanism explanation above is consistent with every measurement I have; I did not patch the engine to
  confirm a fix.
