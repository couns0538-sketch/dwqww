# CORRECTION AND FINAL MECHANISM (seat 25, clock-99 defect)

This file supersedes the conclusion of `is_zero_right.py` and the last section of `MECHANISM.md`. I got the rule
wrong for a few minutes and the engine is wrong for the same reason, which is why it is worth writing down
exactly.

## The rule, checked rather than assumed

I had written that white at clock 99 can "take a draw" with a quiet move and that the engine reporting `cp 0` was
therefore right. That is wrong. python-chess, which encodes FIDE rules, is explicit:

```
position after white's quiet a1a2: r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 b - - 100 1
  is_game_over(claim_draw=False) : False        <-- NOT automatically over
  is_game_over(claim_draw=True)  : True         <-- the draw is CLAIMABLE
  black's legal moves            : 25
  after black's pawn push h7h6   : clock=0, game_over=False   <-- black REFUSES the draw and plays on
```

The fifty-move draw must be **claimed**. A side that is winning simply makes a capture or pawn move, the clock
resets to 0, and the game continues. Black has 11 such moves here. So white's quiet move does **not** secure a
draw: black declines it.

## Therefore

**`cp 0` at clock 99 is WRONG**, and my original S-F3 finding stands exactly as first reported. White is lost
(-155 cp at clock 0) and cannot force a draw, because the only "draw" available needs the opponent's consent.

## The mechanism, restated correctly

`is_draw` (src/search.cpp:1426-1436) is called on a child whose clock is 100 and returns TRUE, so that child is
scored 0. That test is where the mistake enters, and it is the same mistake I made: it treats a
**claimable** draw as if it were a **forced** one. A claimable draw is only worth what the opponent allows. The
fifty-move rule belongs to the side that wants the draw; scoring it 0 unconditionally means the side that does
NOT want it is not asked.

Consequence at the root, all measured:
- 18 quiet root moves -> children at clock 100 -> each scored 0 -> the root takes 0 as the maximum.
- 9 reset root moves -> scored -212 .. -488 (they keep the game going, which is correct: white is lost).
- The root therefore reports `cp 0` for a position worth -155 cp, with a 1-ply PV, at every depth 1..6.
- The engine's chosen move (a1a2, a quiet rook shuffle) is one of the "drawn" ones.

That is the defect in one sentence: **a claimable fifty-move draw is scored as a forced draw, so at clock 99 a
lost position is valued at 0 and the engine plays to reach a draw the opponent can simply decline.**

## Confidence and what stays open
- The rule check above is decisive for the RULE (claimable, refusable). Verified in python-chess and consistent
  with FIDE article 9.3.
- The chain quiet-move -> clock-100 child -> `is_draw` TRUE is directly observed in the instrumentation
  (109 `is_draw TRUE` lines, all `clock=100 fifty=1`, on that one search).
- I did NOT patch `is_draw` to confirm that changing it fixes the score. A candidate repair (text only, for the
  owner to judge): a fifty-move "draw" should only be scored 0 when the position is also a draw for the side that
  would have to claim it, i.e. it should not be treated as terminal for a side that can still reset the clock -
  which in practice means the rule should not terminate the line at all while a reset is available to either
  side within the horizon.
- I still do not claim this loses games against a resisting opponent; I claim the score and the move are wrong,
  and that the position is reachable by a legal 99-ply sequence (S-F11).

## The mechanism tested against its own predictions (all three confirmed)

If the diagnosis is right (a CLAIMABLE fifty-move draw scored as forced), then three things must follow:

| prediction | test | result |
|---|---|---|
| P-a: at clock 100 with reset moves available, a lost position must ALSO be cp 0 | board A at clock 100 (9 resets available) | `cp 0` in 251 nodes, plays a1a2 - confirmed |
| P-b: at clock 100 with NO reset possible, cp 0 is CORRECT | K+R vs K+R, no captures/pawn moves: `4k3/8/8/8/8/8/8/R3K2r w - - 100 1` | `cp 0` in 32 nodes - confirmed correct |
| P-c: the fault scales with quiet moves, so a board whose best moves are RESETS must stay non-zero | board V3 at clock 99 | `cp 549` in 3,918 nodes - confirmed |

Evidence: `predict_test.py`, output `predict_test.txt`.

P-b is the important one for the diagnosis: at clock 100 with no reset move anywhere, cp 0 is right, and the
engine says 0. So the engine's clock-100 test is not universally wrong - it is wrong exactly when a reset move
exists somewhere, which is precisely the "claimable, not forced" distinction. That is what makes this a
diagnosis rather than a story.

A note on my own honesty: I wrote, in `is_zero_right.py`, that "cp 0 at clock 99 is CORRECT for white". That was
wrong, and I withdrew it in the commit that added this file. The rule check in this file is the one that stands.
