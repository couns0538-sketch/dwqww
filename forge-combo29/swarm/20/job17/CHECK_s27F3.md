# seat 20 — check of seat 27's S-F3 (`hashfull` samples only the first 1000 clusters)

Verdict: **CONFIRMS seat 27's S-F3**, and pins it more sharply than their version: at depth 12 the NODE COUNT is
identical across table sizes (87,135 at every Hash), so the changing `hashfull` cannot be a real occupancy
difference — it is purely the sampling window.

Raw: `check_s27f3.json`. Script: `check_s27f3.py` (uses `AUDIT/hardened.py`: fresh process per search, reads to
`bestmove` before `quit`, and **asserts** that both `hashfull` and `nodes` were actually present before recording —
the fail-loud rule from seat 19's silent-parse warning).

## The measurements (fresh process each, `OwnBook false`)

**midgame `r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1`, `go depth 12`**

| Hash | bestmove | score | nodes | hashfull |
|---|---|---|---|---|
| 16 | e1c1 | cp 428 | 87,135 | **44** |
| 64 | e1c1 | cp 428 | 87,135 | 12 |
| 256 | e1c1 | cp 428 | 87,135 | 3 |
| 1024 | e1c1 | cp 428 | 87,135 | **1** |

Same position, same search, same score, **same node count** — hashfull falls 44 → 12 → 3 → 1, i.e. roughly ×1/4 as the
table quadruples.

**startpos `go depth 12`**: nodes 56,720 at every Hash; hashfull 36 → 7 → 1 → **0**. At Hash 1024 the engine reports
`hashfull 0` while having just filled a real table with 56,720 nodes.

**deeper searches** (`go depth 18`, midgame): hashfull 840 / 332 / 83 / 22, and here the node counts DO differ a
little at Hash 16 (1,933,418 vs 2,311,260) — a 16 MB table is genuinely too small at depth 18, so that row is a real
occupancy effect on top of the sampling one. I state both rather than only the convenient one.

## The source, quoted (src/search.cpp:562-572, 6b98f217)
```
int TranspositionTable::hashfull() const {
    int count = 0;
    const std::size_t sample = std::min<std::size_t>(1000, cluster_count_);
    for (std::size_t i = 0; i < sample; ++i) {
        const auto lock = lock_stripe(i);
        for (const TTEntry& entry : clusters_[i].entries) {
            if (entry.occupied() && entry.generation() == generation_) ++count;
        }
    }
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}
```
`sample` is capped at 1000 clusters and the loop starts at index 0, so the statistic is taken over exactly the first
1000 clusters — 1/64 of a 1024 MB table, 1/16 of a 64 MB table. The scaling `count * 1000 / (4 * sample)` then
divides by the SAMPLE, not the table, so the result is a per-sample percentage of a fixed window.

## Why it matters
`hashfull` is what a GUI shows as "table used" and what a tester might use to decide a search is table-limited.
At Hash 512 or 1024 it reads near 0 no matter how full the table is, which can make a genuine table shortage look
like a near-empty table. It is a reporting defect, not a search defect: the searches themselves are unaffected.

## Where my predictions went
1 held (large drop, ratio ≈ table ratio). 2 held at depth 12 on both positions (identical nodes and bestmove);
2 did **not** hold at depth 18 midgame, where a 16 MB table really is too small — recorded above.
3 held (Hash 1024 reports 0–4 even on long searches). 4 held (`min(1000, cluster_count_)` quoted).

## What I did NOT do
- I did not test Hash values below 16 or above 1024.
- I did not verify that `cluster_count_` really scales with the Hash option (I infer it from the ×1/4 behaviour).
- I did not compare against another engine's convention for hashfull.

## What I am NOT sure about
- Whether the PC intends `hashfull` as "fraction of the whole table" (then this is a bug) or as "activity on a fixed
  sample" (then it is a naming problem). Either way the number a GUI shows is misleading at large Hash.

## Commands that show it again
```
python3 check_s27f3.py /agent/repos/build-base/forge /tmp/o
sed -n '562,572p' /agent/repos/base/forge-combo29/src/search.cpp
```
