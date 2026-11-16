# seat 20 — job 65: the residual cost above 128 MB is a SECOND TABLE, not cache pressure

Job 64 found that even with seat 30's `tt.clear()` repair, MultiPV 3 still loses depth as Hash grows (flat 14.0 to
Hash 128, then 12.0 at 256 and 10.0 at 512). I described that as "residual table-size cost — allocation, cache/TLB
pressure". **That was a guess, and it is wrong.** This job isolates it.

## The isolation: MultiPV 1 has no per-line anything — is it affected?

Repaired build, `go wtime 5000`, Threads 1, 10 G-set positions:

| Hash | **MultiPV 1** median | **MultiPV 3** median |
|---|---|---|
| 16 | **17.0** | 14.0 |
| 128 | **17.0** | 14.0 |
| 512 | **17.0** | 10.0 |
| **2048** | **16.5** | **1.0** |

**MultiPV 1 is FLAT — 17.0, 17.0, 17.0, 16.5 — across a 128× range of table size.** So a big table does **not** cost
depth for a normal search on this machine. My "table-size cost" explanation is refuted by its own control.

## What it actually is, from the source

`src/search.cpp:2726-2732`:
```cpp
if (multipv > 1 && is_main()) {
    const std::size_t hash_mb = std::max<std::size_t>(
        1, shared_.tt.cluster_count() * sizeof(TTCluster) / (1024U * 1024U));
    alt_shared = std::make_unique<SharedSearchState>(hash_mb);   // <-- a SECOND FULL-SIZE TABLE
    alt_worker = std::make_unique<Worker>(*alt_shared, 0);
}
```
With MultiPV > 1 the engine allocates a **second transposition table the same size as the first** for the alternate
line. At Hash 2048 MB the process therefore allocates and first-touches **two 2 GB tables** before the first line is
searched. That is what swallows the clock at 2048 MB — and it is **not** the `clear()` seat 30 removed, so the repair
cannot fix it.

The shape matches exactly:
- **16–128 MB**: the second table is cheap → flat;
- **256–512 MB**: allocating and first-touching a second large table costs plies;
- **2048 MB**: the allocation alone exceeds a 5 s budget → depth 1, *even repaired*.

## The corrected statement
The multi-PV gradient has **two independent causes**:
1. **the per-line `tt.clear()`** — about 3 of the 4–5 plies at Hash 128, **removed by seat 30's patch** (S-C35/S-C40);
2. **a second full-size table allocated for the alternate line** — the residual cost above ~128 MB, **not removed** by
   that patch (this job), which is why the repaired build still collapses at 2048 MB.

## What the owner should take from it
The repair is still worth having (no cost at safe sizes, +2.5/+3 plies at 64/128). But **"huge Hash with MultiPV" is
expensive for a structural reason** — the engine doubles the table — so it stays a bad idea even repaired. If a further
improvement were wanted, the lever is to size or share that alternate table, not to remove another `clear()`.

## Limits
- One build (repaired), 10 positions, one clock, MultiPV 1 vs 3, Threads 1. The **MultiPV 1 column is the control** that
  makes the refutation sound.
- I did not time the allocation directly; I inferred it from the code and the depth-by-Hash shape and say "inferred"
  rather than claiming a measurement of it.
