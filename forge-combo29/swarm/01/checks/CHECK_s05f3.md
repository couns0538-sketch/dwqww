# CHECK of seat 05 S-F3 — CONFIRMS the numbers, REFUTES the framing "applied about 9 plies early"

## Seat 05's claim (verbatim from its FINDINGS.md)
> The fifty-move draw is applied about 9 plies early: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at `go depth 10`
> scores `cp 472` for H=0..75, `cp 314` at H=90, then exactly `cp 0` from H=91

## What I did (harness written by me from that sentence, seat 05's script not read or copied)
`check_s05f3.py`: for each halfmove H, a fresh engine process, `position fen`, `isready` read to `readyok`,
`go depth 10`, read to `bestmove`, last `info depth` line recorded. Three boards: seat 05's KR v k and
KQ v k boards verbatim, plus a K v K control that must already be `cp 0` at H=0.
`check_s05f3_depth.py`: the same sweep at depths 4, 6, 8, 10, 12 around the predicted cliff.

## Result A — the numbers reproduce exactly
```
KR_vs_k: first exactly-zero score at halfmove 91; non-zero at [0, 50, 75, 80, 85, 88, 89, 90]
   seat 05 said 91 -> CONFIRMED on that number
KQ_vs_k: first exactly-zero score at halfmove 91; non-zero at [0, 50, 75, 80, 85, 88, 89, 90]
K_vs_K : first exactly-zero score at halfmove 0 (control: already drawn)
```
(raw: `checks/s05f3/check_s05f3.txt`, `checks/s05f3/check_s05f3.json`)

## Result B — but the cliff MOVES WITH DEPTH, so "9 plies early" is the search horizon
`is_draw()` (src/search.cpp:1302) is true at `halfmove_clock() >= 100`, and a depth-D search from H reaches
H + D - 1 at its deepest leaf (quiescence can reach one ply more). So the first H at which the draw is visible
is 101 - D, or one less when quiescence extends. Measured:

| depth | predicted 101-D | first exactly-zero H | last non-zero H | verdict |
|---|---|---|---|---|
| 4  | 97 | 96 | 95 | moves with depth |
| 6  | 95 | 95 | 94 | exact |
| 8  | 93 | 92 | 91 | moves with depth |
| 10 | 91 | 91 | 90 | exact (matches seat 05) |
| 12 | 89 | 89 | 88 | exact |

(raw: `checks/s05f3/check_s05f3_depth.txt`, `.json`; log `checks/s05f3_depth.log`)

A constant "9 plies early" would put the cliff at 91 for EVERY depth. It does not: it tracks 101 - D.

## Verdict
- **CONFIRMS** seat 05's measured numbers: the flip is at H=91 at depth 10 on that board, and at H=91 on its
  K+Q board too, with non-zero scores at H<=90.
- **REFUTES** the interpretation in the same sentence, "the fifty-move draw is applied about 9 plies early":
  the offset is exactly the remaining search depth (101 - D, minus one when quiescence reaches deeper), so
  nothing is being applied early. What seat 05 measured is the depth-10 horizon, not a rule misimplementation.
- This is the same family as my own S-F5 (root adjudication when the FEN itself says halfmove >= 100), but a
  DIFFERENT case: S-F5 fires at the root with no search at all; seat 05's cliff is a search horizon inside the
  tree. They do not contradict each other.

## What this check does NOT show
- It does not test whether a position that is a *forced win inside the remaining half-moves* is scored
  correctly below the cliff; I only looked at where the score becomes 0.
- Depth 4 and 8 land one halfmove lower than 101 - D. My explanation (quiescence reaching one ply further) is
  a hypothesis consistent with the data, not proven — I did not instrument the leaf ply.
