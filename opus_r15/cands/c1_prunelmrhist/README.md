# C1 PruneLmrHist - quiet pruning at the history-adjusted LMR depth (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c1_prunelmrhist\forge_ltopgo_c1plh.exe` + `setoption name PruneLmrHist value 1`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c1_prunelmrhist.patch` (src/search.cpp only, +10 / -1), applies with `patch -p1` to git d4f4312.

## What it changes
In the move loop's shallow-depth pruning block, for quiet moves only, the depth that quiet futility pruning,
history pruning and quiet SEE pruning test (`lmr_depth = depth - reduction(...)`) gets the same per-move history term
LMR itself applies: `lmr_depth = max(0, lmr_depth + clamp(history / LmrHistoryDivisor, -2, 2))`. LMP (move-count
pruning), captures and every other rule are unchanged. Option `PruneLmrHist` (spin 0..1, default 0).

## Why it should gain
The lock decides whether to prune a quiet move from a depth estimate that leaves out the one per-move part of its
own LMR formula: the real search gives a quiet move with a strong history up to two plies more depth
(`r -= clamp(history / 6000, -2, 2)`), but the pruning tests see the bare table reduction. So good-history quiet moves
are futility- or SEE-pruned as if they were searched two plies shallower than they would be, and bad-history moves
survive pruning although LMR would search them two plies shallower. Letting the pruning tests use the depth the move
would really get makes the two halves of the move loop agree: good moves are kept, bad moves are dropped earlier,
which at STC turns saved nodes into depth where it matters (ON bench d16 2,071,386 vs 3,024,920 nodes; node counts
are not strength).

## OFF identity
With `PruneLmrHist 0` the new block is skipped and `lmr_depth` is the lock's value, so the tree is the lock's: kit
OFF node identity ALL OK, bench d11-d22 and perft = the lock pins (pin_check), plain = LTO+PGO per depth.

## Own review (structured self-review, NOT independent)
- Bounds: `history` is the sum of three int16 tables (|h| <= 49,152); the divisor has min 1000, so no division by
  zero; the clamp keeps the term in [-2, 2]; `lmr_depth` stays >= 0. The SEE threshold `-24 * d * d` with d <= 65
  stays far inside int.
- C++ integer division truncates toward zero: a history of -5,999 gives 0 (same rule as LMR's own term).
- Early in a game the histories are near 0: no change there. With reduction 0 (first moves) lmr_depth may reach
  depth + 2: futility then needs a larger margin (less pruning) - harmless.
- Thread safety: reads only the worker's own tables, as before.
- PGO: the kit profile is trained with the option OFF (frozen workload v1), so the ON branch is cold-optimised; a
  small ON speed cost is possible (same for every R13-R15 option line).
- Risk: more pruning of bad-history quiets that are actually good (history is noisy at low depth); the clamp keeps
  the change to at most two plies of depth either way.
