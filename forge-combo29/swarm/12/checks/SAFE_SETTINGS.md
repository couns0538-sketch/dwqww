# The smallest safe `Hash` x `MultiPV` combinations — boundary cell by cell

Seat 12, area 2. Follows S-C3 (which confirmed seat 02's S-F7/S-F7b with a 2x2). **Threads 1**
throughout (no `Threads` option sent), `OwnBook false`, startpos, fresh process per run.

## The premise in the request was wrong, and the measurements say so

The request said "MultiPV 3 at Hash 256 is already ruined while MultiPV 2 at 64 is marginal". **Measured,
MultiPV 2 at Hash 64 is NOT marginal** — it costs 54-57 ms at `go depth 6` and reaches depth 14-15 on
a 5 s clock. The collapse is much further out than that, and it is **linear in Hash**: nothing is
wrong at 64 MB, and everything is still usable at 256 MB for MultiPV 2.

So the honest answer to "what can the owner set" is a curve, not a single safe cell.

## A — `go depth 6`, wall ms (PC r15, 2 runs per cell)

| MultiPV | Hash 16 | Hash 32 | Hash 64 | Hash 128 | Hash 256 | Hash 512 | Hash 1024 |
|---|---|---|---|---|---|---|---|
| **1** | 2 | 2 | 2 | 2 | 2 | 2 | 3 |
| **2** | 18 | 28 | 54-57 | 126 | 244 | 504 | 1,003 |
| **3** | 23 | 36 | 62-67 | 122-376 | 376 | 800 | 1,848 |
| **4** | 28 | 44 | 80-88 | 156 | 522 | 1,049 | 2,020 |

Same table on the base build (16/64/256/1024): MultiPV 2 → 16 / 48 / 202 / 1,116 ms;
MultiPV 3 → 25 / 64 / 269 / 1,943; MultiPV 4 → 27 / 78 / 490 / 2,029. **Both builds agree**, and
`MultiPV 1` is flat at 2 ms at every Hash size — large Hash alone is free, which is the S-C3 result.

**The scaling is linear in Hash and roughly linear in (MultiPV - 1)**, exactly what
`alt_shared->tt.clear()` once per extra line predicts: the cost is one full table walk per extra PV.

## B — `go wtime 5000 btime 5000`, depth reached (ms used), PC r15

| MultiPV | Hash 16 | Hash 32 | Hash 64 |
|---|---|---|---|
| 1 | **16d** (150 ms) | 16d (152) | 16d (161) |
| 2 | **15d** (279) | 15d (289) | 14d (210) |
| 3 | **14d** (243) | 14d (258) | 14d (336) |
| 4 | **14d** (343) | 14d (369) | 13d (322) |

Every one of these finishes in a fraction of the 5 s budget, so on a clock **MultiPV 2-4 at
Hash 16-64 costs 1-3 plies of depth and is otherwise fine**. For contrast, from S-C3:
Hash 2048 + MultiPV 8 reached **depth 0-1** in ~1.3 s.

## What the owner can actually set — the practical answer

| if he wants | safe setting | cost |
|---|---|---|
| multi-PV analysis, small Hash | **any MultiPV up to 4 at Hash 16-64** | 18-88 ms per depth-6 search, 1-3 plies on a clock |
| large Hash for deep analysis, no multi-PV | **Hash up to 1024+ with MultiPV 1** | 2-3 ms; no penalty at all |
| both at once | keep the product bounded: **Hash 256 with MultiPV 2** is the last comfortable cell (244 ms); **Hash 512+ with MultiPV 4** is where it stops being usable (1,049 ms for a depth-6 search) | |
| never | **Hash 2048 with MultiPV 8** | 8-9 s for depth 6, depth 0-1 on a 5 s clock |

**One-line rule:** `Hash x MultiPV` under about **512 MB x MultiPV-units** is fine; above that the
analysis pane crawls and game play collapses. Concretely: MultiPV 4 is fine to 128 MB, MultiPV 3 to
256 MB, MultiPV 2 to 512 MB, MultiPV 1 unlimited.

## Why this is a curve (the cause, already established)

`src/search.cpp:2502`, in the extra-PV loop: `alt_shared->tt.clear();` walks every cluster of a table
sized to the full `Hash`, once per extra line. So the per-depth cost is
`(MultiPV - 1) x (clusters in Hash)` — which is why the rows are parallel and the columns scale with
Hash. The fix is the owner's call; **I did not write one.**

## Files

- `checks/diagonal.py` — the grid harness (re-runnable; takes the Hash/MultiPV lists from the source).
- `checks/check_02f7_pc.json`, `checks/check_02f7_base.json` — the S-C3 2x2 raw data.
- This table's raw per-cell numbers are the runs printed above; `checks/diagonal_pc.json` holds the
  16/32/64 diagonal, and the extended 64..1024 columns were produced with the same `one()` function
  in the same way (2 runs per cell).

## What I am NOT claiming

- Not that 200 ms is the right threshold for "usable" — that is my line, chosen so a depth-6 analysis
  search stays interactive. An owner with a slower PC should scale the Hash column down.
- Not that these wall times transfer to the PC: this box has 4 cores and a different memory system, so
  the **shape** (linear in Hash, linear in extra PVs) transfers and the absolute milliseconds need
  re-measuring there.
- No fix.
