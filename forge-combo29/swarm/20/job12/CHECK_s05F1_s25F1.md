# seat 20 — check of seat 05's S-F1 / seat 25's S-F1 (mate −12 with an 18-ply PV)

Verdict: **CONFIRMS both findings — but only with the project's S14 tunables applied.** With the engine's DEFAULT
settings the same board is perfectly consistent at every depth. Neither finding states that condition, and it is
the difference between a general search defect and a tuning-dependent one.

Raw: `out_check.txt` (defaults, the first run), `out_check_s14.txt` (the decisive side-by-side),
`check_mate_pv_s14.json` (every row as data). Scripts: `check_mate_pv.py`, `check_mate_pv_s14.py`.
Build: `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins).
Board: `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` (python-chess valid, 3 legal moves).

## The side-by-side

| depth | DEFAULT settings | | S14 settings | |
|---|---|---|---|---|
| | score / PV / verdict | | score / PV / verdict | |
| 10 | mate −7 / 14 plies / **consistent** (mate in exactly 14) | | cp −3181 / 15 plies / no claim | |
| 12 | mate −7 / 14 plies / **consistent** | | **mate −12 / 18 plies / TRUNCATED** (needs 24) | |
| 14 | mate −6 / 12 plies / **consistent** | | **mate −9 / 15 plies / TRUNCATED** (needs 18) | |
| 16 | mate −4 / 8 plies / **consistent** | | mate −6 / 12 plies / **consistent** (mate in exactly 12) | |
| 20 | mate −4 / 8 plies / **consistent** | | mate −5 / 10 plies / **consistent** (mate in exactly 10) | |

With S14, the depth-12 line is exactly what both seats reported: `score mate -12 … pv c2c3 d2d1q c3b2 e4e3 b2a2
d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3` — 18 plies, all legal, and the final position
is NOT checkmate (white still has legal moves). The score promises 24 plies.

## What the numbers say about correctness (not just presentation)

The mate distance is **unstable and wrong at depths 12 and 14 under S14**:
- depth 12 claims mate in 24 plies; depth 16 proves mate in **12** plies with a full PV that ends in checkmate;
- a mate in 12 plies means the depth-12 claim of 24 overstates white's resistance — the score is not merely
  truncated in display, it is a wrong distance at that depth;
- default settings on the same board converge to mate −4 (8 plies) with a verified PV at depth 16, i.e. the true
  value is even shorter than S14's depth-16 answer. So S14 makes the mate **slower to converge**, not wrong in its
  final answer.

## The condition neither finding states

Both seats reported this as a property of the engine at depth 12. It is a property of the engine **at depth 12 with
S14 set**. With default tunables the same search is consistent at every depth I tried (10, 12, 13, 14, 16, 18, 20).
That matters for the PC: a fix targeted at "mate reporting" would be aimed at the wrong place if it ignores the
tuning, and conversely S14's LMR/history values are the plausible cause (they change move ordering enough to find a
longer defensive line first).

## My criterion, and where it could be argued with
I committed before measuring: `mate N < 0` needs a PV of exactly 2|N| plies ending in checkmate; a shorter PV is
TRUNCATED, a full-length non-mate PV is WRONG. Under that rule depths 12 and 14 are truncated, and I did **not**
call them "WRONG" on the PV test alone — the "wrong distance" statement above comes from the cross-depth
comparison (depth 16 proves a 12-ply mate, so 24 plies cannot be the exact distance), not from the truncation.

## Where my predictions went
1 held (mate −12 at depth 12 — **under S14**; my first default-settings run contradicted it, which is how I found
the condition). 2 held (18 plies). 3 held (not checkmate, 2 legal moves after — exactly seat 25's number). 4 held
(the value moves with depth). 5 held: I classify it as "reported mate distance not backed by the reported line at
this depth", and added the stronger cross-depth evidence.

## What I did NOT do
- I did not bisect which of the 14 S14 options causes it (I applied all 14 together).
- I did not run the 353-position G set; this is their single board.
- I did not test the patched build from job7.
- I did not try to construct a shorter verified mate by hand to fix the true value at 8 plies.

## What I am NOT sure about
- Whether the truncation alone (18 of 24 plies) is worth reporting to the PC, given that many engines truncate PVs
  at TT boundaries. The cross-depth instability is the part I would report.

## Commands that show it again
```
python3 check_mate_pv_s14.py /agent/repos/build-base/forge /tmp/o
# defaults only, for the contrast:
python3 check_mate_pv.py /agent/repos/build-base/forge /tmp/o
```
