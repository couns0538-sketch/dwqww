# seat 20 — job 51: are the collapsed cells' moves WORSE, or merely different? — ONE of each

The owner's question, answered per move. Board `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`
(Black to move). The collapsed cells (S-C27) played `f6d7` and `b8a8` where healthy cells played `g7g6`.

## Two independent scorings

**A. MultiPV 4 at the healthy settings** (Hash 16, depth 16, Threads 1) — each root move scored from ONE search:

| root move | score |
|---|---|
| **`g7g6`** (the healthy move) | **cp −273** |
| `e5e4` | cp −311 |
| `f5e6` | cp −327 |
| `b8b7` | cp −328 |

(`f6d7` and `b8a8` were not in the top four, so MultiPV 4 does not score them.)

**B. Each move restricted with `searchmoves`, depth 16, Hash 16, Threads 1 — 5 repetitions each, all bit-stable:**

| move | 5 runs | vs `g7g6` |
|---|---|---|
| `g7g6` | cp −297 ×5 | — |
| **`f6d7`** | cp −293 ×5 | **+4 cp (marginally BETTER)** |
| **`b8a8`** | cp −343 ×5 | **−46 cp (WORSE)** |

**The restriction's own perturbation** (measured the way my S-C23 requires): the healthy move scores cp −273 under
MultiPV and cp −297 under `searchmoves`, so a restriction costs about **24 cp** of apparent accuracy. That is the
noise band any comparison must exceed.

## The verdict — split, and this is the honest answer
1. **`f6d7` is NOT worse.** It is +4 cp against `g7g6` under identical restrictions — far inside the 24 cp band,
   i.e. **a different move, not a worse one.** So the Hash-256/MultiPV-8 cell is a *depth* collapse only.
2. **`b8a8` IS worse by 46 cp**, which is ~2× the restriction perturbation and stable across 5 runs. That is a
   **real quality loss**, not noise, so the Hash-2048/MultiPV-3-and-8 cells are a **QUALITY defect in the analysis
   path**, not merely a shallow one.

## How to describe it from here
- **Hash 256 + MultiPV ≥ 3**: depth collapse (searches ~5 % of the depth) with a move that is *equally good* —
  a wasted-budget defect, visible as depth 1–7 instead of 17.
- **Hash 2048 + MultiPV ≥ 3**: **quality defect** — the engine recommends a move that is 46 cp worse at the same
  depth, reproducibly. In analysis output that is a wrong recommendation, and it should be described that way.
- Both are avoided identically: MultiPV 1 at any Hash, or Hash ≤ 16 MB with MultiPV > 1.

## Limits and what would strengthen it
- One position, one depth (16), one build (PC r15 + built-in net). The 46 cp figure is this position's; the *class*
  of defect (a materially worse move) is what I would carry to other positions.
- The MultiPV-vs-restriction perturbation (24 cp) was measured on one move; a bigger board sample would tighten it.
  Even so, 46 cp exceeds it with 5/5 stability.
- `Threads 1`, as required. All scores single-threaded.
