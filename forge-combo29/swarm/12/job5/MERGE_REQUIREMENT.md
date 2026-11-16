# MERGE REQUIREMENT — a claimable-draw change must go INSIDE the root-drawn guard, never layered on top

**Read this before attempting any claimable-draw change.** It records a measured interaction, so the
next person does not have to rediscover it. Seat 12, area 2. Threads 1.

## The requirement

> **Any change that stops `Worker::is_draw` treating a *claimable* fifty-move or repetition draw as a
> *forced* one must be made INSIDE the `FORGE_FIX_ROOT_DRAWN` path (i.e. as one deliberate change to
> the root-drawn logic), and must NOT be applied as a separate patch layered on top of it.**

Layering is not merely "imperfect": it produces a **third, wrong answer** on a mate-in-one root
(see evidence 3 below), so a layered build is worse than either fix alone on that position.

## Why — the three pieces of evidence, all measured

Builds: base 6b98f217; PC r15 = base + `pc_r15.patch` (`-DFORGE_MATE_ALPHA_GUARD=1`). The
claimable-draw patch was applied with `patch -p1 --fuzz=0`; the root-drawn switch was turned off with
`-DFORGE_FIX_ROOT_DRAWN=0` (it is `#ifndef`-guarded, so no source edit), and the switch was **proven
active** before the comparison was believed.

### Evidence 1 — the fifty-move failure case

```
r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 w - - 99 1
```

A lost position at clock 99 where the side to move has reset moves available. Unpatched both builds
say `cp 0`. With a correct claimable-draw rule it must not be 0.

### Evidence 2 — the two must-be-zero cases that FAIL when layered on r15

| case | FEN | required | layered on r15 (root fix ON) | root fix OFF |
|---|---|---|---|---|
| losing side to move at a threefold (it may claim, so `cp 0` is right) | reached by moves to `4k3/8/8/8/8/8/R3P3/4K3 b - - 9 44` | **cp 0** | **cp -1237 ✘** | cp 0 ✔ |
| clock 100 with NO reset available anywhere (the claim really cannot be avoided) | `4k3/8/8/8/8/8/8/R3K2r w - - 100 1` | **cp 0** | **cp -450 / 11,419 nodes ✘** | cp 0 / 0 nodes ✔ |

Everything else was identical between the two builds: cases 1 and 2 of the four-case set gave the
same scores, and the K v K forced-draw control stayed `cp 0` in 0 nodes on both. So the two failures
are attributable to the root-drawn path and to nothing else.

### Evidence 3 — the case that makes this a requirement rather than advice

```
6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40     White has mate in one (Ra8#)
```

| build | answer |
|---|---|
| stock PC r15 (root fix ON, no claimable-draw change) | `a1a8` / **mate 1** / 180 nodes — correct |
| root fix ON **+ layered** claimable-draw patch | `a1a7` / **cp 488** / 7,625 nodes — **wrong, and wrong in a new way** |
| root fix OFF + claimable-draw patch | `g1e2` / cp 0 / 0 nodes — the old 0-node adjudication, also wrong for the mate but at least a known behaviour |

The middle row is the important one: layering turns a **correct mate score into +488**. Neither patch
does that on its own. A layered build can therefore be worse than either change alone, on a position
where the engine had the mate right before.

## Also worth knowing before starting

- **The cost of a correct version is not free.** Across four patched builds the honesty pins moved
  identically: bench 11 312866 → **353312**, bench 13 862329 → **979723**, bench 16 3024920 →
  **2893009**, perft 5 unchanged. Correcting the fifty-move condition and disabling the root-drawn fix
  both left those numbers **bit-identical**, which places the cost in the **repetition branch** of
  `is_draw`, not in the root path or the fifty-move term.
- **Where the logic lives:** `Worker::is_draw`, `src/search.cpp` (`halfmove_clock() >= 100` and
  `is_repetition(root_history_index_)` in one return), plus the root early-return guarded by
  `FORGE_FIX_ROOT_DRAWN`. The two must be decided together.
- **The one-condition correction that makes the base tree correct** (for reference, not as a patch to
  apply blindly): the fifty-move node is terminal only when **no** legal move resets the counter — no
  pawn move and no capture anywhere. Requiring **all** moves to reset is the opposite case and was my
  first error.

## Files that carry the raw evidence

- `job5/root_off_report.md` — the interaction experiment (root fix on vs off, switch proof).
- `job5/four_cases_root_off.txt` — the four-case table, raw.
- `job5/pins_root_off.txt` — pins for the root-off build.
- `job5/experiment_report.md` — the base-tree correctness experiment.
- `job5/fix_report.md` — the first (not-ready) attempt, including my polarity error.
- `job4/pc_node_level_finding.md` — the underlying defect and its depth sweep.

## Not claimed

- That the merged version has been written or that it works.
- That a merged version keeps this pin cost; it may not.
- That `cp 488` is understood beyond "the two changes interact" — it was reported, not investigated.
