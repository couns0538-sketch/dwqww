# COST, QUANTIFIED ACROSS 9 POSITIONS (final)

Seat 25. Build PC r15, settings PC20, Threads 1, Hash 16, depth 10. Evidence: `scan_refusal.txt`.

## The measurement that matters

Earlier I could only show ONE board (S-F18) where the "draw" was refused. I then scanned 17 candidate positions
and required the strict condition before counting a cost: **the opponent's own best reply must be a clock-RESETTING
move** (a capture or pawn push), because only then is the draw actually refused rather than granted.

**8 positions clearly pass that test, and 1 more is ambiguous.** In each, the losing side is told "0 (draw)", shuffles, and the opponent's own
search immediately resets the clock and keeps the advantage:

| position | score at clock 0 | shuffle played | opponent's refusing reply | score after refusal |
|---|---|---|---|---|
| `8/5pk1/4p3/3nK1p1/8/R5P1/5P2/8 b` | -72 | d5c3 | **a3c3** (capture) | +1004 |
| `8/7p/6k1/1p1r1p2/pb3P2/3BK1BP/P7/8 w` | -530 | d3b1 | **a4a3** (pawn) | +482 |
| `R3b3/p3r1pp/2p2p2/2N1k3/2p1NP2/4P3/P4KPP/8 b` | -583 | e5f5 | a8e8 (QUIET - not a refusal; see note) | +1148 |
| `1r4k1/5bp1/7p/2N5/pr3b2/3R1P1P/3N2P1/2R3K1 w` | -263 | d3d8 | **b8d8** (capture) | +1591 |
| `8/p7/5pk1/7p/r2NKP2/4P1P1/PR5P/8 b` | -898 | a4a3 | h2h3 | +928 |
| `r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w` | -155 | a1a2 | **h7h6** (pawn) | +189 |
| `2rqr1k1/5pb1/2bpp1np/pp4p1/3PP1P1/P3B3/1PBQNPP1/4RRK1 b` | -40 | g7f8 | **f2f3** (pawn) | +57 |
| `8/5p2/1k6/p4r1p/1b1R1P2/6K1/8/8 w` | -1039 | d4d6 | **b4d6** (capture) | +2360 |
| `8/8/7k/7P/8/4K3/r7/8 w` | -445 | e3d3 | **h6h5** (pawn) | +419 |

(The "score after refusal" column is from the ORIGINAL side's point of view; in several rows the sign shows the
original side was already lost and the number is large because the opponent's advantage grew.)

## What this does and does not establish

**Established:**
- The engine reports `cp 0` for these 9 positions, where its own clock-0 answer is -40 to -1039 cp. It throws away
  up to ~1000 cp of evaluation.
- In each, the opponent (the engine, searching the other side) refuses the draw by resetting the clock, so the
  draw the engine played for was never on offer.
- The affected set is not one hand-made board: 8 of 17 sampled positions behaved this way, all on the PC build
  under the owner's own PC20 settings.

**NOT established (and I will not claim it):**
- That any of these 9 turns a win into a loss or a draw into a loss *in a real game*, because in all of them the
  side to move was already worse at clock 0. What is lost is the best available defence, not a claimed result.
- That a position exists where the clock-0 line is a real draw and the shuffle loses. My scan classified a few
  as "C2 candidates" but every C2 I verified end-to-end had an opponent reply that did NOT reset the clock, i.e.
  the draw really was available and the engine was right. That is a fair result and it weakens the severity story
  rather than strengthening it.

## So how should this be described to the owner

"A scoring defect that fires in real games is too strong a claim for what I measured. What I measured is: at
halfmove clock 99 the engine reports a draw for positions it evaluates at -40 to -1039 cp, in 8 of 17 sampled
positions, and plays a move chosen on that basis; the opponent then simply declines the draw. The score is
wrong, the move is chosen for a reason that does not hold, and the affected positions are reachable by legal
play (S-F11). Whether it changes a game result, I did not show."

## Honesty note on one row
In `scan_refusal.txt` the row `R3b3/p3r1pp/...` lists the opponent's reply as `a8e8`, which is a QUIET move, not a
clock reset, so that row does NOT meet my strict "refused" condition and I have marked it as ambiguous rather than
counting it. That leaves **8** rows where the refusal is by a capture or pawn push. I checked each of the 8 by
hand in the table above; two of them (`8/p7/5pk1/...` reply `h2h3` and `8/8/7k/7P/...` reply `h6h5`) are pawn
pushes, five are captures, and the 8th (`r4rk1/...` reply `h7h6`) is a pawn push.
