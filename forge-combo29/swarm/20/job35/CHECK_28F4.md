# seat 20 — job 35: confirmation of seat 28's S-F4 at Threads 1 (repetition door)

Queue entry 3. Seat 28's S-F4: the 0-node root adjudication also fires on `board.is_repetition()`, so a mate-in-1
board reached a **third** time by legal moves answers `f2f3`/`cp 0`/0 nodes where the identical board as a plain
FEN answers the mate.

**Confirmed at `Threads 1`, 3 runs per cell, fresh process per run, on both builds.**

Board `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1` (mate by `d1d8`), cycle `g1h1 g8h8 h1g1 h8g8`:

| case | base 6b98f217 + S14 | PC r15 + PC20 |
|---|---|---|
| plain FEN (control, no history) | d1d8 / mate 1 / 168 n ×3 | d1d8 / mate 1 / 168 n ×3 |
| **second** occurrence (one cycle) | d1d8 / mate 1 / 168 n ×3 | d1d8 / mate 1 / 168 n ×3 |
| **third** occurrence (two cycles) | **f2f3 / cp 0 / 0 n ×3** | **d1d8 / mate 1 / 162 n ×3** |

## What this establishes
1. **S-F4 reproduces exactly at Threads 1** on the base tree: only the third occurrence collapses, and the second is
   searched normally — which is the "`matches >= 2`" rule Opus's file 3 describes, measured rather than quoted.
2. **The control passes**: the plain-FEN row proves my harness gets the mate in 168 nodes, so the `f2f3 / 0 nodes`
   row is the repetition door and not a broken FEN or an unparsed answer.
3. **The PC build repairs it**: the third occurrence answers the mate in 162 nodes instead of 0. Note the small node
   difference from the plain-FEN control (162 vs 168) — the repetition history changes the tree slightly but the
   answer and the mate score are right, and it is stable across 3 runs.
4. Together with S-C17 (seat 30's quiet board) and my S-F33, the drawn-root repair on the PC build is now confirmed
   by **three** independent harnesses on **three** different kinds of position (mate board, quiet board,
   repetition-history board).

## Honest limits
- One cycle construction of mine; seat 28 used their own. Both reproduce the same behaviour, which is the point.
- `Threads 1` only, as the rule requires; no score above one thread appears here.
- PC20 is a bundle — per my S-F38 the mate-distance effect is `MateAlphaGuard`, but I have **not** isolated which
  switch closes this repetition door, and I am not claiming the guard does.
