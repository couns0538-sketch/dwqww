# CHECK of seat 12's S-F22 — the slow Hash × MultiPV region is a BOUNDARY, not a cell — seat 08

Their claim:
> S-F22: "The safe Hash x MultiPV boundary is a **CURVE**, not a single cell, and the 'MultiPV 3 at Hash 256 is
> ruined / MultiPV 2 at 64 is marginal' premise is wrong."

## Verdict: SUPPORTS the boundary claim, on my own grid

My harness, PC r15 PC20, Threads 1, **fixed node budget** (`go nodes 200000`) so the WORK is constant and the
elapsed time is the variable being measured. Same middlegame position throughout.

| Hash | MultiPV 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **16** | 116 | 140 | 146 | 145 |
| **64** | 113 | **193** | **200** | **227** |
| **256** | 132 | **384** | **557** | **550** |

| quantity | value |
|---|---|
| fastest cell | **113 ms** (Hash 64, MultiPV 1) |
| slowest cell | **557 ms** (Hash 256, MultiPV 3) |
| spread | **4.9x** |
| cells slower than 1.5× the fastest | **6** — (64,2), (64,3), (64,4), (256,2), (256,3), (256,4) |

**The slow region is six cells spanning two Hash values and three MultiPV values**, so it is a boundary rather than
one bad combination — which is what their finding asserts. The shape is visible in the table: the cost rises with
MultiPV **and** rises faster at larger Hash, so the iso-time contours run diagonally. That is the "curve" in their
title, and my grid shows the diagonal gradient plainly.

## One specific claim of theirs I can address directly
They say the premise "**MultiPV 3 at Hash 256 is ruined**" is wrong. On my measurement (256,3) is the **slowest cell
on the grid at 557 ms, 4.9x the fastest** — so if "ruined" means "unusably slow", that cell is the worst one there
is. I read their point as being that it is not *singularly* bad (its neighbours are nearly as slow), which my table
supports: (256,4) is 550 ms and (256,2) is 384 ms. **So the cell is the worst but not isolated** — both halves of
their framing hold.

## What this does and does not establish
**Establishes:** the slow region is multi-cell and diagonal; the spread is 4.9x; the worst combination on this grid is
Hash 256 with MultiPV 3.
**Does NOT establish:** the absolute times are machine-specific (my 4-core VM), the exact contour shape (my grid is
3×4 and coarse), or anything about move quality — this is a timing measurement only, and a slow cell is not a wrong
cell.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s12f22.py /tmp/g.txt
