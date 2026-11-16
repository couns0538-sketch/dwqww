# ⚠ ANALYSIS WARNING — large Hash + MultiPV can return a move with NO SEARCH behind it

**Read this before your next analysis session. It does not affect your matches.**

## The configuration that fails

| setting | value |
|---|---|
| engine | PC build (r15), Threads 1 |
| `Hash` | **2048 MB** (measured; the failure was NOT reproduced at 256 MB) |
| `MultiPV` | **8** (not reproduced at 3) |
| clock | any — measured with `go wtime 5000 btime 5000` |

## Scope — which settings actually fail
Measured in two independent runs: the **0-node failure needs a very large Hash with a high MultiPV.**
**`MultiPV 3` with `Hash 256` did NOT produce a single 0-node answer** (0/5 idle, 0/5 with three CPU hogs, on two
positions) — so that plausible GUI setting is affected by the *depth* collapse but not by the 0-node failure.
The 0-node failure was measured at **Hash 2048 + MultiPV 8**; treat 256 MB + MultiPV 3 as "slower and shallower",
and 2048 MB + MultiPV 8 as "can return a move with no search".

## The failure rate (10 fresh processes per arm, one position, `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b`)

| configuration | idle PC | **busy PC (3 CPU hogs)** |
|---|---|---|
| **Hash 2048 + MultiPV 8** | **1 of 10** runs returned a 0-node answer | **6 of 10** runs returned a 0-node answer |
| **Hash 16 + MultiPV 1** (healthy control) | **0 of 10** | **0 of 10** |

A "0-node answer" means the engine returned a `bestmove` with **zero nodes searched** — the move has nothing behind
it. In the failing configuration the returned **move also varies** between runs (`b8a8` / `d5d4`), so the same
position can give you different recommendations on consecutive analyses.

## Why it happens
With MultiPV above 1 the engine clears the transposition table for each additional line. At 256–2048 MB that clearing
costs more than the move's whole time budget, so on a contended machine the clock expires before any depth is
published and the engine falls back to its first move. Measured depths in the failing cells: **1 to 7 instead of 17**
(and sometimes 0 nodes).

## The fix — either is sufficient
- **`MultiPV 1` at any Hash size.** Safe in every cell measured (depth 16–17 at Hash 16, 256 and 2048).
- **`Hash` at 16 MB with MultiPV above 1.** Safe up to MultiPV 8 (depth 12).

The unsafe region is only the combination of a large Hash **and** MultiPV > 1. Do not use one without checking the
other.

## Your matches are NOT affected
The matches run **MultiPV 1**, so none of this applies to game play. It is an **analysis-path** problem only.

## How sure this is
- Counts are exact: 10 processes per arm, fresh process each, `Threads 1`, one position, one clock.
- The healthy control never failed (0/10 in both conditions), so the failure belongs to the configuration and not to
  the machine or the harness.
- Full per-run data and raw output: `job53/ZERO_NODE_UNDER_LOAD.md`, `job53/zero_node.json`, `job53/run.log`.
- Supporting runs: `job50/MULTIPV_HASH.md` (the depth collapse grid), `job51/MOVE_QUALITY.md` (the move is 46 cp
  worse in one cell), `job52/CLASS_TEST.md` (2 of 6 positions materially worse; the rest unchanged).
- Limits: the 1/10 → 6/10 rate is measured on **one** position at Hash 2048 + MultiPV 8. A second position (P2)
  was run under the same load at Hash 256 + MultiPV 3 and showed **no** 0-node answers, which is why the scope above
  is narrowed to the very large Hash. The 0-node failure is thus demonstrated at 2048/8 on one position, and NOT
  demonstrated at 256/3 on two.
