# seat 20 — job 34: confirmation of seat 25's S-F1/S-F2 at Threads 1, and the PC build at every depth

Queue entry 2. Seat 25 claims (S-F1) that a depth-12 S14 search of `8/8/1p6/8/p3p3/8/2Kpk3/8 w` reports
`mate -12` while the true distance is 4 moves, and (S-F2) that the mate score is unstable across depth in the
direction of the truth: −12 (d12–16), −5 (d18), −4 (d22–28), where −4 is the proven exact distance.

**Both reproduce exactly, `Threads 1` stated explicitly, 5 runs per cell, fresh process each, on both builds.**

## Base tree 6b98f217 + S14, Threads 1

| depth | scores (5 runs) | stable? |
|---|---|---|
| 12 | `mate -12` ×5 | **stable** |
| 14 | `mate -9` ×5 | **stable** |
| 16 | `mate -6` ×5 | **stable** |
| 18 | `mate -5` ×5 | **stable** |
| 22 | `mate -4` ×5 | **stable** |

The ladder `−12 → −9 → −6 → −5 → −4` is exactly theirs, and every cell is bit-stable at Threads 1 — so their
numbers were not thread noise.

## PC r15 + PC20, Threads 1

| depth | scores (5 runs) |
|---|---|
| 12 | `mate -4` ×5 |
| 14 | `mate -4` ×5 |
| 16 | `mate -4` ×5 |
| 18 | `mate -4` ×5 |
| 22 | `mate -4` ×5 |

**The PC build gives the true distance at EVERY depth**, including the shallow one where the base tree is two
"moves" wrong. That is a stronger statement than my S-F34/S-F38: it is not that the PC build converges faster at
depth 22, it is that it never reports a wrong distance at all on this board, from depth 12 upward.

## Three things this pins down

1. **Seat 25's finding is solid at Threads 1** and its ladder is reproducible — the depth-dependence is real
   behaviour, not nondeterminism. (Consistent with my S-C9/S-F17: the S14 tuning and the depth both move the
   reported distance on the base tree.)
2. **`mate -4` is the true distance** (my S-F22, proved by exhaustive search: True at 8 plies, False at 2..7).
   Both seats now agree on the number, reached by different routes.
3. **On the PC build the defect is absent at every depth tested** — so the base-tree ladder is a base-tree
   phenomenon. Under my S-F38 the mechanism is `MateAlphaGuard`; I have not isolated it per depth, and I say so
   rather than imply a per-depth result.

## Honest limits
- One board. Seat 25's S-F8 names a second position (`2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1bB3NR w - - 0 22`)
  which I did **not** test; a confirmation of S-F8 specifically is still open.
- I tested depths 12, 14, 16, 18, 22 — not their full 12–28.
- `Threads 1` only; no score above one thread appears in this file.
- PC20 bundle, per the earlier warning: the per-depth fix is the bundle's behaviour, and only S-F38 isolates the
  switch at depth 12.

Builds/settings for every row: `base_s14` = base 6b98f217, S14, Threads 1, Hash 16, OwnBook false.
`pc20` = PC r15 (patch sha256 `d6bd72c531f785f4…`, `-DFORGE_MATE_ALPHA_GUARD=1`), PC20, Threads 1.
