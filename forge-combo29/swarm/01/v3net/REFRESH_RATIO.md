# The refresh path, measured: 6.99 columns per rebuild (S-F113, S-F114)

Continues `PROFILE_RESULT.md`. There, `refresh_from_pieces` cost **4.79 %** of `bench 13` — nearly as much as the
incremental update it backs up (7.41 %). This page answers *why*, using counters the engine was already keeping.

## What was dead, and the patch that revives it

`RefreshCache::refreshes` and `::columns` are incremented at `nnue_v3.cpp:694` and `:702/:707`, reset at `:644–645`,
and **read by nothing** (`grep -rln refreshes .` → 13 files, only two are code, the rest are the English verb or
archived copies).

`stats.patch.txt` (in this folder) adds a run-total pair plus one line of output:

```
info string v3 refresh_stats refreshes N columns M
```

printed **after** the bench line, which is left byte-identical. **Do not apply this patch to the repository** — it is
evidence for a measurement, not a fix. It applies cleanly (`patch -p1 --dry-run`, three files, no rejects) and it
changes no search decision.

## Identity first, because a counter read from a different search means nothing

All four of file 7's configurations reproduce their published `bench 13` numbers **exactly** on the stats build:

| row | nodes (stats build) | published | clean build | verdict |
|---|---|---|---|---|
| no net | 862,329 | 862,329 | 862,329 | PASS |
| PC20 | 587,276 | 587,276 | 587,276 | PASS |
| test net only | 4,151,906 | 4,151,906 | 4,151,906 | PASS |
| PC20 + test net | 3,652,372 | 3,652,372 | 3,652,372 | PASS |

Only the two net rows can report counters (without a v3 net the v3 path never runs), which is itself a small check:
`stats` is `None` exactly where it should be.

## The numbers

| configuration | refreshes | columns | **columns per refresh** |
|---|---|---|---|
| test net only | 6,087 | 44,898 | **7.38** |
| PC20 + test net | 6,485 | 45,353 | **6.99** |

PC20 changes the refresh count by 6.5 % (6,087 → 6,485), so search settings do move how often the path fires — worth
knowing before any patch perturbs them.

## What 6.99 means, and the mechanism behind it

`refresh_from_pieces` (`nnue_v3.cpp:689`) recomputes a perspective from a cache entry keyed on
`(perspective, king bucket)`. The entry holds **the piece set of the last position cached under that key**, so when a
new position arrives in the same king bucket but with a different piece placement, the function walks all 12 piece
types and column-add/subs every square that differs — then `std::copy_n` the whole 512-wide accumulator out.

* A rebuild from scratch would cost one column per man on the board. The bench set's **mean is 24.9 pieces** (8
  positions, 199 men: 32, 32, 28, 10, 30, 26, 9, 32), so a full rebuild is **~24.9 columns** on average and 32 at
  most.
* The cache costs **6.99**, so it saves **~72 %** against the mean (78 % against the 32-piece maximum). **The cache
  works; it is not a no-op.** My first draft quoted 78 % by comparing against 32 pieces without checking the bench
  positions — the mean is what the number should be measured against.
* But 6.99 columns is still ~7 columns of 1 KB each, **plus a fixed 1 KB copy-out**, on each of 6,485 occasions per
  `bench 13`. That is why a "backup path" costs 39.3 % as much as the incremental update it exists to avoid.

The interesting quantity is not 6.99 by itself, it is **why it is that high**. Seven differing pieces between
consecutive positions cached under one king bucket is a lot, and it points at the cache key: a key that only
distinguishes *king bucket* will hand back a stale placement and force a large diff, whereas a key that also
tracked which pieces moved would hand back something one or two columns away. **That is the Step 2 question, now
with numbers attached instead of a guess.**

## What I am not claiming

- Not that 6.99 columns is too many; I have no target to compare against.
- Not that the refresh path can be made cheap without breaking identity — that is what Step 2 has to prove, node by
  node, per file 7's rule that one moved node disqualifies a speed patch.
- Not that the 4.79 %/7.41 % split is memory-bound. The PMU counters are unavailable (Trap 10), so the split is
  time-attributed, not cause-attributed.

## The near-miss worth recording (S-F114)

The first instrumented run reported **2,570 ms** against the clean build's **2,161 ms** — a 19 % regression that would
have been a headline. Five runs each said otherwise:

```
instrumented: 2113 2118 2149 2104 2121
clean:        2136 2127 2125 2142 2117
```

Identical distributions, identical node counts. **The 2,570 was load noise on a 4-core shared VM.** This is the same
confound as my earlier "warm is slower" error (`S-F74`): a single pair of timings is not a comparison. Five
alternating runs are the minimum, and the node count must match before any timing is quoted at all.
