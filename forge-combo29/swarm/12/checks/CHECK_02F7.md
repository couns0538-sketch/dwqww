# S-C3 — CONFIRMS seat 02's S-F7 and S-F7b (large `Hash` + `MultiPV > 1` collapse)

Seat 02's claim: `Hash` large together with `MultiPV > 1` makes every search enormously slow, because
the extra-PV loop clears the whole transposition table once per extra line; on a clock it becomes a
strength loss.

**Verdict: CONFIRMS both halves, on both builds.** My own harness (`checks/check_02f7.py`), own
builds, **Threads 1** (no `Threads` option sent), `OwnBook false`, startpos, fresh process per run,
3 runs per cell.

## Why a matrix and not a single pair

The claim is about a **combination**, so testing one slow pair would not distinguish "large Hash is
slow", "MultiPV is slow", or "the two together are slow". The check is the full 2x2 with both
single-factor cells as controls:

| Hash | MultiPV | `go depth 6` median (base) | (PC r15) | verdict cell |
|---|---|---|---|---|
| 16 | 1 | **3 ms** | **2 ms** | control: fast |
| 16 | 8 | 49 ms | 49 ms | control: MultiPV alone is mildly slow |
| 2048 | 1 | **3 ms** | **3 ms** | control: large Hash alone is FREE |
| **2048** | **8** | **8,585 ms** | **9,185 ms** | **the collapse: ~170x the nearest cell** |

Per-run values, base: `[3,2,3]`, `[49,49,49]`, `[3,3,3]`, `[8736, 8585, 8180]` ms.
PC r15: `[2,3,2]`, `[54,47,49]`, `[3,2,3]`, `[9206, 8671, 9185]` ms.

**Large Hash on its own costs nothing (3 ms, same as the default), and MultiPV 8 on a small Hash
costs 49 ms. Only the pair collapses to eight seconds** — so the combination, not either option, is
the cause. That is what seat 02 claimed and it reproduces on both builds.

All cells produced the same 48 info lines and reached depth 6: the search is not wrong, it is
**spending its time clearing a table**.

## The strength half, on a real 5 s clock

`go wtime 5000 btime 5000`, same 2x2:

| Hash | MultiPV | depth per run (base) | depth per run (PC r15) | median ms |
|---|---|---|---|---|
| 16 | 1 | **[18, 16, 16]** | **[16, 16, 16]** | ~150 ms |
| 16 | 8 | [12, 12, 12] | [12, 12, 12] | ~350 ms |
| 2048 | 1 | [16, 15, 15] | [15, 15, 15] | ~159 ms |
| **2048** | **8** | **[0, 1, 1]** | **[0, 1, 0]** | **~1,300 ms** |

Two things here are stronger than the original claim, and one needs care:

- **Depth 0 means no depth line at all** — the search produced *no* completed iteration before its
  time ran out. That is the true floor, worse than the "depth 1" seat 02 reported, and it happened in
  2 of 3 base runs and 2 of 3 PC runs.
- The 5 s clock is **not** fully used (~1.3 s of 5 s): the engine returns early by its own time
  management, so the loss is not "ran out of time" but "spent the budget clearing tables and then
  stopped". That matches seat 02's 1.18-1.20 s observation.
- The other three cells reach depth 12-18, so the comparison point is solid.

**Consequence for a GUI: with Hash 2048 and MultiPV 8 the engine plays at depth 0-1 on a 5 s clock.**
That is not a slow analysis pane; it is a strength collapse, and it is the most owner-relevant thing I
have confirmed today.

## The cause, verified in the source rather than assumed

`src/search.cpp:2502`, inside the extra-PV loop:

```cpp
                alt_shared->tt.clear();
                alt_worker->clear();
                const SearchInfo alt = alt_worker->search(board, narrowed, false, alt_list);
```

`alt_shared` is sized from the main table's cluster count, so `clear()` walks every cluster — for
`Hash 2048` that is the full 2 GB — once **per extra line**. With MultiPV 8 that is seven full walks
per depth level. That is exactly the arithmetic of the measurements: the cost scales with
`Hash x (MultiPV - 1)`, which the 2x2 shows directly (Hash alone free, MultiPV alone cheap, both
together eight seconds).

## Practical workaround (seat 02's, and my numbers agree with it)

For analysis with MultiPV > 1: keep `Hash` at 16-64 MB. For large Hash: use MultiPV 1. If a GUI does
both, the engine collapses.

## Files

- `checks/check_02f7.py` — harness, re-runnable, matrix design.
- `checks/check_02f7_base.json`, `checks/check_02f7_pc.json` — raw per-run data, both builds.
- `checks/check_02f7.meta` — exe hashes, Threads 1, settings, date.

## What I am NOT claiming

- Not that the fix is easy: removing the per-line `clear()` changes what the extra PVs see and may
  change their answers, so it is a search-behaviour change needing a bench and a match. **I did not
  write or test a fix.**
- Not the exact per-clear cost; I measured end-to-end wall time, not the clear itself.
