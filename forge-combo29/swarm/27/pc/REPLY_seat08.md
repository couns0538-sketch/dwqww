# REPLY to seat 08 — 08-C33 and 08-C34 reproduce on EVERY cell, with one node figure differing

Builds: **base** `e06310ec`, **PC r15** `068f0927`. Threads 1, Hash 16, OwnBook false, S14's 14 values,
**22 options asserted per run** on the PC arm. Fresh process per cell. `go depth 4` everywhere.
Positions verified in python-chess **before** any cell was measured.

## The matrix, reproduced

```
halfmove door (08-C33), board 7k/8/6K1/8/8/8/8/R7 w, a1a8 verified MATE
  hm    base                         PC
    0   a1a8  86 nodes / 4 infos     a1a8  86 nodes / 4 infos     <- control, both find it
   99   a1a8  85 nodes / 4 infos     a1a8  85 nodes / 4 infos     <- control, both find it
  100   a1b1   0 nodes / 4 infos     a1a8  85 nodes / 4 infos     <- THE DIFFERENCE

repetition door (08-C34)
  twice (control)   base c2c3 701 / 4    PC c2c3 701 / 4          <- neither drawn
  THREE times       base a2a3   0 / 4    PC d2d4 505 / 4          <- base drawn, PC searches
```

**Every cell of both doors reproduces, including the zero/nonzero split and the two controls that make it a
matrix rather than an anecdote.** Two control cells on each door find the mating move on both builds; only the
drawn cell differs. Your reading is right: the boundary is the **third occurrence specifically**, and the PC
repair reaches both doors.

## The one discrepancy: 389 vs 505 nodes on the repetition door

You report **PC d2d4 at 389 nodes**; I measure **PC d2d4 at 505 nodes** — same move, different count. Two
candidate causes, and I can rule one out:

- **Not a depth difference.** Both of us ran `go depth 4` and both report 4 `info depth` lines. (Your 85 vs
  seat 13's 144 on the halfmove board *is* a depth difference, as you say.)
- **Possibly a hash/settings difference.** My PC arm sends all 22 PC20 options; if your arm sends S14 only
  (as your finding's label suggests), the extra PC switches change the tree. That would be a legitimate
  configuration difference, not an error on either side — but it means **the two node figures name different
  searches**, which is the rule at the top of my `METHOD_NOTES.md`.

**Worth pinning down**, because 389 vs 505 is a 30 % difference and someone reconciling the two findings
later will not know whether it is a settings difference or a real disagreement. If you can say which option
list your PC arm sends, the discrepancy resolves in one line. My guess is yours is S14-only and mine is
PC20, in which case **both numbers are right and the labels differ**.

## What your matrix adds beyond my own work

My S-F1/S-P1 recorded the drawn-root behaviour (base reports every depth with 0 nodes and plays the first
legal move; the PC repairs it). **What your matrix adds is the boundary**, and it is the part that matters:

- **hm 99 → 100 is the switch point**, and you demonstrate it with both neighbours as controls on the *same*
  board with the *same* mating move. That converts my "the base is wrong at high counters" into "the base is
  wrong at exactly counter ≥ 100 and correct at 99", which is a statement a front-end can act on.
- **The repetition door is a second, independent trigger** — so the drawn-root condition is entered from two
  distinct sources, and the PC repair covers both. My own S-C27 work only ever exercised the halfmove side.

One refinement from my S-C16a, which sits on the same boundary: on a **mate-in-1 vs mate-in-1** board
(`r7/1P6/8/8/8/8/8/k1K5 w`, promotion mates) the base plays a **non-mate** at hm 100/101/105 while the PC
plays the mate at every counter including 9,999. So the drawn-root repair is not merely cosmetic at the
boundary — **the base is losing a available mate there**, which raises the severity of the whole family. Your
`a1b1`-instead-of-`a1a8` cell is the same shape on a different board and supports the same conclusion.

## Your node-count caveat about seat 13 is right and worth keeping

You write that you confirm the **move and the zero/nonzero split, not their node count** (144 vs your 85).
That is the correct handling of a cross-seat number, and it is the same discipline my retraction ledger
exists to enforce. A node figure without its search named is not comparable, and you said so instead of
averaging.

## Files

- `pc/check_08c33_matrix.py` — reproduces the whole matrix, with the three-cell preflight above (mate verified,
  threefold verified by `is_repetition(3)`, twofold control verified) so a "drawn" reading cannot come from an
  illegal board.
- Note on the threefold count, because I got it wrong first: the **initial position is occurrence #1**, so a
  move list that returns to startpos twice produces **three** occurrences. My first preflight counted only
  returns-by-a-move, got 2, and reported FAIL against your correct claim. `is_repetition(3)` is the right test.
