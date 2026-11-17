# The v3 path's cost is the SEARCH SHAPE, not the evaluation (S-F118)

This tests a prediction from another seat by a different route, and the answer changes what Step 2 can achieve.

## Where the 6.8× actually lives

`bench 13`, `Threads 1`, `Hash 16`, 7 alternating rounds of all four configurations, **medians** (not means), and
the node count had to be identical in every run before any timing was kept.

| configuration | nodes | median time | median nps | per node |
|---|---|---|---|---|
| no net | 862,329 | 427 ms | 2,019,505 | 0.495 µs |
| PC20 | 587,276 | 311 ms | 1,888,347 | 0.530 µs |
| test net only | 4,151,906 | 2,118 ms | 1,960,295 | 0.510 µs |
| PC20 + test net | 3,652,372 | 2,111 ms | 1,730,162 | 0.578 µs |

**PC20 → PC20 + v3 net:**

* nodes **6.22×**
* time **6.79×** (6.69–6.81× across the four runs)
* nps **91.6 %** of the built-in figure — and across **four file-backed runs** of the full table (`nps_run1..4.txt`)
  the spread is **91.6 / 91.7 / 92.1 / 92.7 %**, i.e. the net's nodes cost **91.6–92.7 %** of what built-in nodes
  cost
* per-node cost **1.079–1.092×** — **7.9–9.2 % dearer**

So the v3 evaluation is **not slow**. It is within 9 % of the built-in net per node. The 6.8× wall-clock cost is
almost entirely **6.2× more nodes**, which is the net's opinion changing which moves the search selects — the search
shape, not overhead.

## What this does to Step 2

`refresh_from_pieces` was 4.79 % of `bench 13` and the whole v3 family 19.05 %. Even making the entire v3 evaluation
**free** would move `bench 13` from 2,111 ms to **1,709 ms** — a **19.1 %** gain (2,111 × (1 − 0.1905) = 1,709) against a
**6.8×** cost. **The ceiling on v3 micro-optimisation is ~19 % of this benchmark, and no amount of it can recover the
6.8×.** (I first wrote "~1,800 ms / 15 %" here; the arithmetic gives 1,709 ms / 19.1 %.)

That is worth saying plainly to whoever is chasing v3 speed for self-play throughput: the lever is the **node
count** (net quality, search parameters, eval scale), not the kernel. A faster kernel buys at most a sixth of what a
cheaper search shape would.

## A disagreement with seat 29, recorded as a disagreement

Seat 29's file-7 prediction (`forge-combo29/swarm/29/v3/prediction.txt`) commits:

* **P2**: all `nnue::v3::*` at **40–75 %** of bench-13 samples; *"KILLED if the v3 family is under 25 %"*.
* **P3**: nps under PC20+net at **15–60 %** of the PC20 no-net figure; *"KILLED if nps is above 75 %"*.

Both are killed by measurement here:

| their claim | mine | route |
|---|---|---|
| v3 family ≥ 25 % of samples | **19.05 %** | 43,000 `task-clock` samples |
| evaluation entry point ≥ 25 % | **16.66 % inclusive**, 3.32 % self | same profile, inclusive column |
| nps 15–60 % of built-in | **91.6 %** | 7 alternating rounds, medians |

Two independent routes — sample attribution and nps — agree, and they do not share a method that could be wrong the
same way. **I am reporting this as a disagreement to settle, not as a correction of their work.** They may have
measured a different workload, and the owner's PC is a Zen 5 with `-march=znver5` against my generic x86-64, so
their per-node figure could legitimately differ. What would settle it is the same four-row nps table on their build
and on the PC: it is cheap, it needs no profiler, and `nps` is on the bench line already.

## Method notes, because this is where I have been wrong before

* **Medians over 7 alternating rounds**, not one pair. My two earlier single-pair comparisons both misled me
  (`S-F74` "warm is slower"; `S-F115` a phantom 19 % regression that was load noise on a 4-core VM).
* **Node identity was a precondition**: every run in a row had to report the same node count, or the timings describe
  different searches and were discarded.
* **`nps` is the engine's own nodes/time**, so process start-up and shell overhead are excluded. That matters on this
  VM, where the first profiler I tried measured the wrapper instead of the engine (Trap 10).
* The node counts here are **not** a new finding: all four match file 7's published table, which Step 0 already
  verified (`S-F109`) and seat 29 independently confirmed (`29-F57`).

## What this does not claim

* Not that the v3 kernel is optimal — 9 % dearer per node is real and could be recovered.
* Not that seat 29 is wrong about their own build. The disagreement is about a prediction's kill conditions, and the
  resolution is a shared four-row nps table.
* Not that `bench 13` represents game play: it is 8 fixed positions at a fixed depth, and the 6.2× node ratio is a
  property of this set under PC20.
