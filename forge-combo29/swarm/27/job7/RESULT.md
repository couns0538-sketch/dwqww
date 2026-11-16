# job 7 - S-F8 split recorded, and the mechanism of the no-op restriction named

## 1. Recorded as current state (seat 10 owns the split)

| defect | what | seat 10 id |
|---|---|---|
| A | the restricted root computes a WRONG SCORE with an empty table (Clear Hash changes no node: 21,640 both ways) | 10-F17 |
| B | a restricted search POLLUTES THE SHARED TABLE for a later unrestricted search | 10-F15 |
| A min | `searchmoves e2e4`: cp 16/26/23/27 at d8/10/12/14 vs unrestricted 26/24/30/23 | 10-F18 |
| A max | restricting to ALL 20 legal moves still differs: cp 23 / d2d4 vs cp 30 / e2e4 | 10-F14 |

My `job5/searchmoves_iir.PARTIAL.patch.txt` addresses **A only, partially**; it does nothing about **B**.

## 2. Aspiration RULED OUT (my ablation, job7/f2)

`AspirationDelta 18` gaps: +10, -2, +7, -4. `AspirationDelta 200` gaps: +31, +6, +2, -6. Widening the
window does not shrink the gap -> the aspiration feedback is not the causing term.

## 3. Mechanism of the NO-OP restriction, named and reproducible

`job7/f3_all20_mechanism.py` on three builds (all fresh processes, paced, asserting their info line):

| build | unrestricted | all 20 restricted | verdict |
|---|---|---|---|
| base | cp 30 / 56720 / e2e4 | cp 23 / 21640 / d2d4 | DIFFERS |
| IIR stopped at a restricted root | cp 30 / 56720 / e2e4 | cp 24 / 70142 / d2d4 | DIFFERS |
| IIR stopped AND root TT store restored | cp 30 / 56720 / e2e4 | **cp 30 / 56720 / e2e4** | **EQUALS** |

So for a restriction that excludes nothing, the whole error is the two deliberate differences at a
restricted root: the extra reduced ply (IIR, because there is no hash move) and the skipped root store.
That also explains 10-F12 (a repeated restricted search shrinks 21,640 -> 17,847: something does write
the table, just not the restricted root).

## 4. The honest limit - S-F8 STAYS OPEN

On the SAME third build, `searchmoves d2d4 e2e4` gives cp 26 / 32441 against cp 30 / 56720. A restriction
that excludes something is NOT explained by IIR + the store. I did not find that cause and did not guess.

## 5. Caution for whoever reads 10-F18 next (S-F8c)

At depths 8 and 10 the unrestricted search plays **d2d4** while the restricted one plays **e2e4**. A "gap"
between cp 26 (d2d4) and cp 16 (e2e4) compares two DIFFERENT MOVES and is not a score error at all. The
sign flip in 10-F18 is confounded with the move changing. The clean like-for-like case is all-20 (10-F14),
which section 3 explains.

## 6. On my own patch

`searchmoves_iir.PARTIAL.patch.txt` is not a fix and is not a prerequisite for fixing B. I did not save the
IIR+store pair as a patch: it leaves the general case open (section 4) and the store half removes an
intentional design decision that belongs to Opus.

Raw: job7/f1 (IirDepth bound), job7/f2 (aspiration ablation), job7/f3 (all-20 mechanism).
