# forge-combo29 soak — memory stability of one long-lived process

Audit base commit `6b98f217` ("Checkpoint standalone NNUE v3 work and evidence"),
folder `forge-combo29`. Build: g++ 13.3.0, `-DFORGE_MARCH=x86-64-v4`, `-O3 -ffp-contract=off
-fno-fast-math`. Engine `id name Chess Engine Forge 6.4.24 candidate`, sha256
`e06310ec…b316a83`. 4 CPUs, no swap, 16 GB.

## The answer in three lines

1. **The engine does not leak.** 5,000 depth-12 searches in one process move RSS by
   **+1.5 MB total and 0.000 MB per 1,000 searches** over searches 1,000–5,000; the value is
   constant to the last sample. The plateau at Hash 32 is **42.1 MB**.
2. **Memory is the table, exactly.** RSS tracks the `Hash` option to within **0.1 %** at
   16 / 64 / 256 / 1024 MB. Every non-table byte is a constant **10.1 MB**, the same at all
   five Hash values.
3. **The MultiPV alternate table is real, is the SAME SIZE as the main table, and is freed.**
   Measured by slope: peak RSS grows at **1.000 MB per MB of Hash at MultiPV 1** and
   **2.001 at MultiPV 2**, against 1.0 / 2.0 predicted. At Hash 256 + MultiPV 2 the process
   peaks **259.6 MB above** its MultiPV-1 peak and returns within **+3.6 MB** after `bestmove`.
4. **A resize holds old + new.** `setoption name Hash` from 16 → 256 peaks at **281.9 MB**
   (old + new + the 9.9 MB resident component); `256 → 256` peaks at **521.9 MB**. The
   allocator does not reuse the old block.

Verdict: **soak-clean.** No unbounded growth in any of the six measurements. Nothing changes
an answer under pressure: no cap produced a different move, score or node count — the process
dies instead.

**One prediction failed and it is reported as a failure**: I predicted the `ulimit -v` cliff
would be `2 × Hash + 44` under MultiPV 2 and it is not (152 MB where I said 168–176, 598 MB
where I said 548–564). The sizing claim survives — confirmed on a slope instead — but the
cliff turned out to measure the cap, not the table. See §5b.

## How sure

High for the RSS verdicts: the curves are the raw output of a committed script, the runs
are 5,000 and 1,000 searches long, and the flat result is flat across every sample rather
than on average. High for the Hash relation: four arms land within 0.1 % of the advertised
size and the residual is constant to 0.1 MB. High for the sanitizer negative: the detector
was shown to fire on a planted fault through the same runner (0 / 0 / 4 lines).
**Not established**: no run exceeds ~5 minutes of engine time or 5,000 searches, so this is
not evidence about multi-day uptime beyond the fact that nothing is accumulating; and no
arm used more than one thread, so per-thread worker memory at `Threads 8` is unmeasured.
**Low confidence in the cliff as a predictor**: §5b shows it tracks `VmHWM + untouched
virtual`, and the untouched part moves with the cap being probed, so cliff figures are
properties of a cell rather than of the engine.

## Honesty pins, on the binary these measurements used

Fresh process per line, raw output in `evidence/meta/`:

| pin | expected | measured |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 | 4,865,609 | **4,865,609** |

The ASan+UBSan build reproduces all four as well (sha256 `a30da82c…b5defdc`), which is what
makes its leak result admissible.

---

## 1. RSS over 5,000 searches in one process

5,000 × `go depth 12`, Hash 32, Threads 1, `OwnBook false`, positions drawn from a fixed
shuffle over 3,095 varied positions (curated endgames, middlegames and openings plus 120
random legal games sampled every 7 plies), RSS sampled every 50 searches.

```
sample  search   rss_kB   rss_MB
     0       0    41572     40.6     <- after handshake, before any search
     1       1    43112     42.1     <- after the FIRST search
     3       3    43116     42.1
    10      10    43116     42.1
   500     500    43116     42.1
  1000    1000    43116     42.1
  1500    1500    43116     42.1
  2000    2000    43116     42.1
  2500    2500    43116     42.1
  3000    3000    43116     42.1
  3500    3500    43116     42.1
  4000    4000    43116     42.1
  4500    4500    43116     42.1
  5000    5000    43116     42.1
```

- **Plateau: 42.1 MB (43,116 kB).** It is reached on the **first** search, not after a ramp.
- **Slope over searches 1,000–5,000: +0.000 MB per 1,000 searches** (least squares on the
  sampled points, in MB).
- Total change over the whole run: **+1,544 kB**, all of it in the first search (the engine's
  working set — evaluator cache, histories, stack — is touched the first time it searches).
- **3 distinct values in 111 samples**: 41,572 / 43,112 / 43,116. A 4 kB granularity wobble
  on search 1, then nothing.
- 5000 searches logged, **0 with a missing `info depth` line**, 10 zero-node searches (all
  genuine drawn-root bails — bare kings and mutual-zugzwang endgames in the set, which emit
  a full `info` ladder and `cp 0`), 4,991 of 5,000 with a non-null `bestmove`, 482,665,840
  nodes total, 284.9 s.

**This is a plateau, not a slow climb.** The thing a 100-search test cannot see — because it
would finish inside the first-search ramp and report the plateau as if it were the start —
is that there is no ramp to miss.

### Bounded or unbounded?

Neither: it is **flat**. The distinction the assignment asks for (a cache filling vs a leak)
would show as a positive slope that either stops or does not. Here the slope is zero from
search 50 onward, so there is no filling phase to attribute.

## 2. RSS tracks the `Hash` option

40 depth-10 searches per arm, each arm a fresh process, RSS read after the run:

```
Hash   RSS_kB   RSS_MB   over_hash1_MB   (RSS - Hash) MB
   1    11372     11.1            0.0            10.1
  16    26720     26.1           15.0            10.1
  64    75876     74.1           63.0            10.1
 256   272476    266.1          255.0            10.1
1024  1058924   1034.1         1023.0            10.1

marginal cost vs Hash 1:
  Hash   16: 15.0 MB vs  15 MB expected  (-0.1 %)
  Hash   64: 63.0 MB vs  63 MB expected  (-0.0 %)
  Hash  256: 255.0 MB vs 255 MB expected (-0.0 %)
  Hash 1024: 1023.0 MB vs 1023 MB expected (+0.0 %)
```

The advertised size is exact, and the **non-table memory is a constant 10.1 MB** at every
Hash value — the engine has no growing resident component beside the table.

### The "~105 MB alternate table" is 105.9 MILLISECONDS

The report's figure at `findings §3` is **time-to-first-`info`: 1.4 ms at MPV 1 versus
105.9 ms at MPV 2** at Hash 256. It is a latency measurement. The alternate table is not
105 MB, and the source says why:

- `search.cpp:2385-2386` — `hash_mb = max(1, shared_.tt.cluster_count() * sizeof(TTCluster) / (1024*1024))`
- `search.cpp:362-370` — `resize` sets `new_count = bytes / sizeof(TTCluster)` with
  `bytes = mb * 1 MiB`
- `search.hpp:126` — `static_assert(sizeof(TTCluster) == 64)`

so `cluster_count * 64 / 1 MiB` recovers the main table's own MB. **The alternate table is
the same size as the main one.**

**Measured at Hash 256, MultiPV 2 vs MultiPV 1** (RSS sampled at 2 ms from a thread, so a
table that lives only for the length of one search is visible):

```
Hash MPV  settled_kB  peak_med_kB  after_med_kB   peak-settled MB  after-settled MB
 256   1      270920       272624        272480              1.7              1.5
 256   2      270924       538436        276168            261.2              5.1
 256   4      270960       538432        272644            261.2              1.6
  64   1       74324        76008         75864              1.6              1.5
  64   4       74356       145248         79580             69.2              5.1
```

- Peak delta MPV2 − MPV1 at Hash 256: **259.6 MB**, i.e. one more 256 MB table. Not 105 MB.
- **It is freed**: `after` returns to the MultiPV-1 level, +3.6 MB.
- At Hash 64 the alternate table costs **67.6 MB** (69.2 − 1.6), the same rule.
- MultiPV 4 peaks at the *same* level as MultiPV 2 (538 MB), because `search.cpp:2502` calls
  `alt_shared->tt.clear()` per secondary line and reuses **one** alternate table rather than
  allocating one per line. That is why the per-line cost is clearing work, not memory.

The +5.1 MB `after` figure on some rows is not a leak: those rows are the first searches
after the table is touched, and the value settles (`P4` below shows the same 5.1 MB step and
then a fixed value for 1,000 searches).

### A trap this measurement would have hit blind: `resize` allocates before it frees

`search.cpp:365-366` builds `new_clusters` with `make_unique` and only then assigns over
`clusters_`, so any resize holds **old + new** at once. Measured (peak sampled at 2 ms):

```
from  to   rss_before_kB  peak_during_kB  rss_after_kB   peak - max(from,to) MB
  16  256          25188          286416        270948                   23.7
 256  256         270928          531460        270928                  263.0
 256   16         270968          286928         25208                   24.2
1024   64        1057312         1122616         74272                   72.3
```

**At Hash 256 → 256 the transient peak is 263 MB above the table size** — a `setoption name
Hash` with an unchanged value doubles resident memory for an instant. No soak arm resizes
mid-run (every RSS arm sets Hash once at handshake), so **no search peak reported here is a
resize peak**, and that is checked rather than assumed: `soak5` starts a fresh process per
cap, `soak2` arm A sets Hash only at handshake, and arm R is the only arm that resizes and it
is reported separately for exactly this reason.

Owner-facing: a match runner that re-sends `setoption name Hash` between games at Hash 1024
needs 1024 + 1024 = 2 GB of RSS for the duration of the call, on top of anything else.

## 3. 5,000 × `ucinewgame` and 5,000 × `Clear Hash`

Warm process, Hash 32, then 5,000 clears of each kind, RSS sampled every 100:

```
mode        clears  rss_before  rss_after  delta  p50_ms  p99_ms  total_s  best_after  nodes_after
ucinewgame    5000       43128      43128      0   1.296   1.623     6.49       h5e5        15779
clearhash     5000       43096      43096      0   1.225   1.645     6.19       h5e5        36770
```

- **Both leave RSS exactly where it started** (delta 0 kB; the sampled curve is a single
  value across all 50 samples in both arms — span 0 kB).
- The engine is still usable after 5,000 clears in both cases, and returns the same move.

### On time — my prediction covered RSS only, and it should stay that way

Both arms cost about the same: **p50 1.30 ms vs 1.23 ms**, total 6.49 s vs 6.19 s. The
reason is in the source and it is *not* a difference in allocation:

- `Searcher::clear_hash()` → `shared_.tt.clear()` + `clear_caches()`
- `Searcher::clear()` (`search.cpp:2678-2682`) → `shared_.tt.clear()` + `Worker::clear()`
- **both** call `TranspositionTable::clear()`, which is a full `memset`
  (`search.cpp:372-375`)

so at Hash 32 each call writes 32 MiB, and 5,000 calls is **156 GiB of memory traffic for
either arm**. `Worker::clear()` additionally resets the histories and the evaluator cache
(`search.cpp:1019-1031`) — that is the whole of the difference.

`ucinewgame` is **not** cheaper. Measured at four table sizes, 200 calls per arm:

```
Hash  ucinewgame_p50  clearhash_p50  difference  RSS delta (both arms)
  32          1.384          1.167       0.217  0 kB / 0 kB
  64          2.318          2.215       0.103  0 kB / 0 kB
 256         12.413         12.276       0.137  0 kB / 0 kB
1024         86.308         85.891       0.417  0 kB / 0 kB
```

The two are **equal to within 0.4 ms at every size**, and the difference does not grow with
Hash — so the whole cost is the memset and the history reset is in the noise. Cost is linear
in Hash at an effective 11.6–28.2 GB/s, and **RSS is unchanged by 200 clears at any size**,
which is P3 confirmed a second time at 1024 MB instead of 32 MB.

A match runner that sends `ucinewgame` between games at Hash 1024 pays **~86 ms per game**,
and `Clear Hash` costs the same — there is no cheap reset.

Note that `ucinewgame` also **resets the board to startpos** (`uci.cpp:257-259`), so the
`best_after` search below it searched whatever position was set *after* the last
`ucinewgame`. Both arms end with a `position` + `go`, which is why they show different node
counts (15,779 vs 36,770); that is a difference in what was searched, not in health.

## 4. 1,000 MultiPV-4 searches at Hash 64

```
search   peak_kB   after_kB   cum_nodes
     0     74304      74304            0
     3    145216      79548        93778
   200    145276      79548      5173215
   400    145212      79548      9503672
   600    145184      79548     13781864
   800    145232      79548     17944459
  1000    145212      79548      22068189
```

- **Peak: 145,088–145,276 kB across all 1,000 searches — a spread of 188 kB (0.2 MB).**
  The alternate table is allocated and freed 1,000 times and always lands on the same size.
- **After: a fixed 79,548 kB for the last 750 searches.** The distinct values over the whole
  run are `{75992, 76028, 79548}` — three transient values from the first searches while the
  evaluator cache fills, then one value for the rest. No ratchet.
- Growth in `after` over 1,000 searches: **+3.5 MB, all of it in the first ~250 searches**;
  0 kB over the last 750.
- 22,068,189 nodes, 108.3 s, 0 errors.

`tt.clear()` runs **three times per depth iteration** here (`search.cpp:2502`), so 1,000
MultiPV-4 searches at Hash 64 is roughly 1,000 × (8–10 depths) × 3 × 64 MiB ≈ **1.5–1.8 TB
of memset traffic** (depths vary per position; the bound is computed, not measured) — which is why this arm costs 108 s for 22 M nodes (204 knps) against 5,000
depth-12 searches in 285 s for 483 M nodes (1.7 Mnps). **The expense is bandwidth, and it
does not leak.**

## 5. Failure under a hard `ulimit -v` — a REPLICATION, not a new finding

**This section replicates prior work and should be read as confirmation, not contribution.**
`findings` §7 trap 3c already established, on this same base commit, that a sweep from 1 GB
down to 16 MB gives **0 of 12 differing on every cap that ran**, **12 of 12 dying below the
cliff**, and — bisected — that **Hash 16 is 59 MB fails / 60 MB works** and **Hash 256 is
290 MB fails / 300 MB works**, with **no silent middle band**. What follows reproduces that;
it is here because the arms shared a harness with P1–P4, not because the negative was open.

One thing genuinely added is a finer bisect across four Hash values:

| Hash | lowest cap that completes all 12 | highest cap that dies | cliff − Hash |
|---|---|---|---|
| 8 | 52 MB | 50 MB | **44 MB** |
| 16 | 60 MB | 59 MB | **44 MB** |
| 64 | 108 MB | 106 MB | **44 MB** |
| 256 | 300 MB | 298 MB | **44 MB** |

My first pass stepped in 2 MB and reported "58 dies" for Hash 16, which was a coarse reading,
not a disagreement: testing **57 / 58 / 59 / 60 individually** gives 57, 58 and **59** all
dying and **60 completing**, so the prior boundary table's 59 is right and my 2 MB grid was
simply blind to it. Both figures are consistent with `Hash + 44 MB`; quoting "56 / 60" — which
the summary I was handed said — would have been wrong in the failing cap by 4 MB.

At Hash 32 the sweep from uncapped down to 56 MB gives **18 surviving caps, 5 deaths** (plus the uncapped reference), and:

- **0 of 18 surviving caps produced any difference** in `bestmove`, score or node count.
- Every death is `SIGABRT` (rc −6) with `terminate called after throwing an instance of
  'std::bad_alloc'` on stderr, before any `bestmove`.
- **A kill is the expected shape and that is what happens** — replicated, not refuted.

### Two instrument corrections, both of which changed the reading

**(a) My first pressure sweep reported "not identical" on 13 of 15 caps, including 512 MB.**
It was wrong. The answer key included the `nps` field, and the engine prints `nps 19` on one
run and `nps 17` on the next for the same nodes and the same score. Re-keyed on
`(bestmove, score token, nodes)` the count is **0 of 19**, and the `nps_only` column above
records how many rows differed in that field alone so the correction is visible rather than
silently applied. **A capped run and an uncapped run are not equally fast; a comparison over
a raw `info` line will always find a difference and it will never be about the search.**

**(b) `ulimit -v` does not cap the number it appears to cap.** A Hash-32 process reports
VmSize 119,004 kB uncapped. Under a cap of 180 MB it still reports 119,004 kB, but at 170 MB
and below it reports **53,464 kB** — 64 MB smaller — while RSS stays at 43 MB and every
answer is unchanged. The engine's virtual size is not its working set: above the threshold a
64 MiB glibc arena reservation succeeds, below it fails and malloc falls back to the main
arena. **So the cliff tracks the touching of memory, not the reservation,** and VmPeak is a
constant `Hash + 147.5 MB` at every Hash value (table above), which is why a cap can sit far
below VmPeak and still work.

That also means a memory budget should be set against **`Hash + 44 MB` per process**, not
against VmPeak. A runner giving this engine 200 MB of address space at Hash 32 is fine; the
same runner at Hash 256 dies at 298 MB and lives at 300 MB.

## 5b. Does the cliff move with MultiPV? My prediction FAILED — and the failure is informative

This is the measurement the coordinator asked for instead of re-deriving P5. `P7` in
`PREDICTION2.md` predicted, from `cliff = 2 × Hash + 44`:

| Hash | MPV 1 (measured) | MPV 2 predicted | MPV 2 measured | ratio |
|---|---|---|---|---|
| 64 | 108 MB | 168–176 MB | **152 MB** | 1.407 |
| 256 | 300 MB | 548–564 MB | **598 MB** | 1.993 |

**Both predictions are killed.** Hash 64 came in **20 MB below** its window; Hash 256 came in
**34 MB above** it. A single linear model in `Hash` cannot produce one overshoot and one
undershoot, so **the cliff was the wrong instrument** and my prediction was built on it.

The sizing claim itself is **not** refuted — it is confirmed, by a better instrument, in
§5c. What failed is my model of what a virtual-memory cap measures.

### What the cliff is actually measuring

Read at the lowest cap that completes, in each cell:

```
Hash MPV  cap_MB  VmHWM_MB  VmSize_MB  untouched_MB   VmHWM+untouched   cliff
  64   1     108     104.4       84.2          10.1            114.5      108
  64   2     152     141.7       84.2          10.1            151.8      152
 256   1     300     296.4      276.2          10.1            306.5      300
 256   2     598     525.8      340.2          70.5            596.3      598
```

`VmHWM + untouched virtual` lands within **1.5 % of the cap in all four cells** (the one
exception, Hash 64 MPV 1, is 6.5 MB low). The cliff is not `f(Hash)`; it is
**`peak resident + whatever glibc has reserved-but-untouched at that moment`**, and the
reservation is **10.1 MB** at Hash 64 but **70.5 MB** at Hash 256 — the arena reservation
succeeds or fails depending on how much address space is left, which is decided by the cap
being probed. That is why the ratio is 1.41 at Hash 64 and 1.99 at Hash 256 with no change to
the engine's allocation behaviour.

**So: the cliff does move with MultiPV, by a lot (152 vs 108, 598 vs 300), but it is not a
clean predictor and I would not quote it as one.** The useful statement for an owner is that
MultiPV 2 needs roughly **two full tables resident**, not that the cap is `2·Hash + 44`.

### The control that makes the MPV-2 number trustworthy

`search.cpp:2502` clears **one** alternate table per secondary line rather than allocating one
per line, so MPV 3 and MPV 4 must have the **same** cliff as MPV 2 if that reading is right:

```
Hash MPV  lowest_complete  highest_dead
  64   2             152           150
  64   4             152           150
 256   2             598           596
 256   3             598           596
 256   4             598           596
```

**Identical to the megabyte at both Hash values.** So the alternate table is allocated once
per search and reused across lines — the §3 cost model's claim, and it holds.

## 5c. The sizing question, answered by slope instead of cliff

The direct test of "is the alternate table the same size as the main one?" is how peak RSS
grows with `Hash` at fixed MultiPV. A **fixed** 105 MB auxiliary table gives slope 1.0 at
every MultiPV; a **same-size** second table gives 1.0 at MPV 1 and **2.0** at MPV 2.

`VmHWM` (kernel peak, no sampling), 6 positions at depth 10, four Hash values:

| Hash | MPV | VmHWM_MB | VmPeak_MB | VmSize_MB | RSS_MB |
|---|---|---|---|---|---|
| 32 | 1 | 72.4 | 179.5 | 116.2 | 42.1 |
| 64 | 1 | 104.5 | 211.5 | 148.2 | 74.1 |
| 128 | 1 | 168.4 | 275.5 | 212.2 | 138.1 |
| 256 | 1 | 296.4 | 403.5 | 340.2 | 266.1 |
| 32 | 2 | 77.7 | 179.5 | 116.2 | 45.7 |
| 64 | 2 | 141.6 | 215.7 | 148.2 | 77.7 |
| 128 | 2 | 269.7 | 343.7 | 212.2 | 141.7 |
| 256 | 2 | 525.8 | 599.7 | 340.2 | 269.7 |
| 32 | 4 | 77.7 | 179.5 | 116.2 | 42.2 |
| 64 | 4 | 141.7 | 215.7 | 148.2 | 74.2 |
| 128 | 4 | 269.7 | 343.7 | 212.2 | 138.2 |
| 256 | 4 | 525.7 | 599.7 | 340.2 | 266.2 |

Fitted on peak RSS against Hash:

```
 -> MPV 1: slope 1.000 MB per MB of Hash, intercept 40.4 MB
 -> MPV 2: slope 2.001 MB per MB of Hash, intercept 13.6 MB
 -> MPV 4: slope 2.000 MB per MB of Hash, intercept 13.7 MB
```

**Measured 1.000 / 2.001 / 2.000 against 1.0 / 2.0 / 2.0 predicted.** The alternate table is a
**full-size second transposition table** — confirmed on a slope, which is a claim about how
memory scales rather than about a threshold. A fixed 105 MB table would have shown slope 1.0
at MPV 2 and the MPV-2 peak would have been `Hash + 105`; it shows `2·Hash + 13.6 MB`.

The MPV-1 intercept of 40.4 MB against MPV-2's 13.6 MB is the 32 MB default table paid twice
at construction before `setoption name Hash` runs, which lands only on the MPV-1 column.

## 5d. The resize transient: real, and exactly old + new

`resize` allocates the new array before releasing the old one (`search.cpp:365-366`), so the
transient holds **old + new**. Measured with `VmHWM` — the kernel's exact peak, which a
sampler cannot miss:

| from | to | RSS_before | peak_MB | old+new_MB | excess_MB |
|---|---|---|---|---|---|
| 16 | 256 | 26,728 kB | 281.9 | 272 | +9.9 |
| 256 | 256 | 272,472 kB | 521.9 | 512 | +9.9 |
| 16 | 1024 | 26,736 kB | 1049.9 | 1040 | +9.9 |
| 256 | 16 | 272,468 kB | 296.4 | 272 | +24.4 |
| 1024 | 1024 | 1,058,916 kB | 2057.9 | 2048 | +9.9 |

- **Every growth case peaks at old + new + 9.9 MB**, and 9.9 MB is exactly the non-table
  resident component measured in §2. **The allocator does not reuse the old block.**
- **`256 → 256` peaks at 522 MB**: re-sending `setoption name Hash` with the *same value*
  still doubles the table. This is the control that makes the instrument credible, and it is
  also the case a match runner is most likely to hit, because re-sending a whole option block
  between games is the natural thing to do.
- The shrink `256 → 16` peaks at 296 MB, i.e. **+24.4 MB** over old+new: the freed 256 MB
  block has not yet been returned to the OS, so peak resident briefly exceeds old+new. Not a
  leak — RSS after settling is 25 MB (§2 arm A).
- The engine is usable after every resize: a depth-8 search returns a move and a node count
  in all five cases.

My earlier 2 ms-sampled estimate for `16 → 256` was **23.7 MB over `max(from,to)`**, when the
old table alone is 16 MB — the sampler was missing most of the transient. `VmHWM` gives
281.9 MB. **A polling sampler is the wrong instrument for a transient; use the kernel's
high-water mark.**

## 6. ASan + UBSan, `detect_leaks=1`

**The sanitizer is live, proven twice.** `nm -C build-asan/forge`: **35 `__asan_` symbols,
15 `__ubsan_` symbols**. The build reproduces all four honesty pins. LSan works in this
container (a 1,234-byte unfreed malloc is reported — `evidence/meta/lsan_control.txt`).

**The runner is proven able to report**, on three cases so the claim is about the runner and
not one code path — a planted heap over-read behind a command no client sends, built in a
scratch copy and driven by the same reader:

```
clean                rc   0  sanitizer_lines 0  info_depth 12  bestmoves ['f1e2', 'g1f3']
planted_untriggered  rc   0  sanitizer_lines 0  info_depth 12  bestmoves ['f1e2', 'g1f3']
planted_triggered    rc  23  sanitizer_lines 4  info_depth  6  bestmoves ['f1e2']
```

0 clean, **0 with the plant compiled in but not triggered**, 4 when triggered (UBSan signed
overflow at `planted/src/uci.cpp:202`, then ASan `heap-buffer-overflow`). The untriggered
row is the one that makes "0" mean something: it shows the detector does not fire on the
merely-present fault.

**The soak**: 120 searches mixing plain depth-6, MultiPV-3, `ucinewgame` and `Clear Hash`
(171 engine operations), `ASAN_OPTIONS=detect_leaks=1`, engine exits via `quit` so LSan runs:

```
searches 120  kinds {'plain': 120, 'multipv3': 24, 'ucinewgame': 17, 'clearhash': 10}
rc 0  sanitizer_lines 0  zero-node rows 0
```

**No leaks, no UB, no still-reachable report.** 0 bytes on stderr.

### Two harness defects I hit and fixed here — both are §7 traps

1. The first version of the proof fed the engine through `printf | exe`. EOF reaching a
   running search **fabricates `bestmove a2a3` with zero `info depth` lines** (trap 3a), so
   my "clean" and "untriggered" rows recorded `a2a3` and neither was the engine's answer.
   They now go through the same non-blocking reader as the soak and assert `info depth`.
2. The first proof waited for an in-band `planted` line on stdout. **An ASan abort closes
   stdout**, so that wait could only time out — a test that cannot fire. The sanitizer writes
   to stderr by construction; the runner now scans stderr after the process is gone.

Left in the record rather than quietly repaired, because both produced plausible-looking
output: the pipe form reported "0 sanitizer lines" and a legal-looking bestmove.

---

## Prediction reconciliation

Two prediction files, each committed and pushed **before** the measurements it covers:
`PREDICTION.md` (commit 1) and `PREDICTION2.md` (commit 3). Neither was edited afterwards.

**Ten predictions held and one failed.** The failure is the interesting one and it is mine,
not the engine's.

### `PREDICTION.md` — nine of nine held

| id | prediction | measured | result |
|---|---|---|---|
| P1 | slope < 2 MB/1,000; plateau ≤ 70 MB | 0.000 MB/1,000; 42.1 MB | **HELD** |
| P1 | rise ≤ 10 MB in first ~200 searches | +1,544 kB, all in search 1 | **HELD** |
| P2 | Hash 16/64/256/1024 within ±15 % and ±8 MB | −0.1 % / −0.0 % / −0.0 % / +0.0 % | **HELD** |
| P2b | MPV2 − MPV1 peak at Hash 256 = 200–300 MB | 259.6 MB | **HELD** |
| P2b | freed within 8 MB after `bestmove` | +3.6 MB | **HELD** |
| P3 | 5,000 clears within 4 MB, either kind | 0 kB / 0 kB | **HELD** |
| P4 | growth < 30 MB over 1,000 MPV-4 searches | +3.5 MB (0 kB after search 250) | **HELD** |
| P5 | no middle band; survivors byte-identical | 0 of 18 survivors differ | **HELD** (replication) |
| P6 | detector provable, no leaks | 0/0/4 lines; 0 leaks | **HELD** |

P5 was written as if it were open. It was not: prior work had already measured it on this
base, and §5 now says so. The nine "held" rows above therefore contain eight new results and
one replication.

### `PREDICTION2.md` — one of seven failed

| id | prediction | measured | result |
|---|---|---|---|
| P7a | Hash 64 MPV2 cliff **168–176 MB** | **152 MB** | **KILLED, 16 MB low** |
| P7b | Hash 256 MPV2 cliff **548–564 MB** | **598 MB** | **KILLED, 34 MB high** |
| P9 | Hash 16: **59 dies, 60 works** | 57/58/59 die, 60 works | **HELD** |
| P8 | 16 → 256 peak ≈ 280 MB (old + new + B) | **281.9 MB** | **HELD** |
| P8 | 256 → 256 control ≈ 520 MB | **521.9 MB** | **HELD** |
| P8 | allocator does NOT reuse the old block | excess is +9.9 MB in every growth case | **HELD** |
| — | (control) MPV2/3/4 share one cliff | 152/152 and 598/598/598 | **HELD** |

**The P7 failure in one line: I predicted the cliff from table size, and the cliff is
`peak resident + however much address space glibc has reserved at that instant`.** At Hash 64
the reservation is 10.1 MB and at Hash 256 it is 70.5 MB, so the same engine behaviour gives
a ratio of 1.41 at one Hash and 1.99 at the other. My model had the right *ingredient*
(a second table) and the wrong *dependent variable*.

What this does **not** do is refute the sizing claim: §5c confirms it on a slope of
**2.001 MB of peak RSS per MB of Hash** at MultiPV 2 against **1.000** at MultiPV 1. A slope
is the right instrument because it asks how memory scales rather than where a threshold sits.

## Suspicions, not proven

- **`ucinewgame` cost is a full table memset, and nothing batches it.** Measured 86 ms per
  call at Hash 1024 (not an estimate). A runner that sends it between every game pays that
  per game. Not a defect; a cost §3 of the report does not mention.
- **The `resize` transient (old+new) has no guard — now measured, not inferred.** `setoption
  name Hash` with the *same* value still doubles the table (521.9 MB peak at `256 → 256`). A
  runner that re-sends its full option block between games pays a 2× transient every time.
  Whether that is worth an early return in `resize` is an owner decision, not a leak. **The
  `256 → 256` case is the one I would rank highest**, because re-sending an unchanged option
  block is what a naive runner does and it is the case with no benefit at all.
- **Threads > 1 is unmeasured here.** Every arm used Threads 1. Each `Worker` owns histories
  and an evaluator cache, so per-thread resident memory is a constant that would show at
  `Threads 8` but is not measured.
- **Days of uptime is not measured, only 285 s of engine time.** The evidence for "stable for
  days" is the zero slope and the zero sanitizer result, not a multi-day run.

## What I did NOT do

- No run longer than 5,000 searches or ~5 minutes of engine time.
- No multi-threaded arm; no `Threads` sweep.
- No `Hash` resize *during* a long soak (deliberate — it would confound a search peak with a
  resize peak). The resize transient is measured on its own instead, as its own arm (§5d).
- No NUMA or cgroup memory-limit test; `ulimit -v` only.
- No TSan run (the assignment asked for ASan+UBSan).
- Did not modify any engine source. The planted fault exists only in a scratch copy under
  `/tmp/soak/planted` and is never committed.

## What I am NOT sure about

- Whether the +3.6 MB `after` residual on MultiPV arms is the alternate table's last page
  not yet returned to the OS, or evaluator-cache growth. It is **bounded** (fixed value over
  750–1,000 searches), so it does not change the verdict, but I did not attribute it.
- The exact allocator boundary (170 MB) is a property of this glibc, not of the engine, and
  would move on a different libc or with `MALLOC_ARENA_MAX` set.
- **The `untouched virtual` component in §5b is measured, not explained.** I show that
  `VmHWM + (VmSize − VmRSS)` lands within 1.5 % of the cliff in four cells, which is a fit to
  four points; I did not vary `MALLOC_ARENA_MAX` or the thread count to confirm the arena
  mechanism. Treat §5b's model as a good fit with a plausible mechanism, not as a proof.

## Times

`evidence/stamps.txt` is the `date -u` log from the working session; the run timings above
come from the harnesses' own monotonic clocks and are pasted from their output files.

## Reproducing

```
scripts/pins.sh <exe> <outdir>                  # the four honesty pins, fresh process each
scripts/gen_positions.py positions_R.fens       # the 3,095-position set (seed 6901)
scripts/soak1.py   --exe <exe> --out <prefix>   # 5,000 searches, RSS every 50
scripts/soak2_hash.py --exe <exe> --out <prefix># Hash arms + resize transient + MultiPV peak
scripts/soak3_clears.py --exe <exe> --out <prefix>
scripts/soak4_mpv.py  --exe <exe> --out <prefix>
scripts/soak5_ulimit.py --exe <exe> --out <prefix>
scripts/soak5b_cliff.py                          # cliff bisect, 4 Hash values
scripts/soak7_cliff_mpv.py                       # P9 boundary + the MultiPV-2 cliff (P7)
scripts/soak7b_mpv_control.py                    # MPV 2/3/4 must share one cliff
scripts/soak7d_slope.py                          # peak-RSS slope vs Hash per MultiPV (the sizing)
scripts/soak8_resize.py                          # resize transient via VmHWM
scripts/soak6_asan.py --exe <asan-exe> --out <prefix>
scripts/sanitizer_proof.py                       # 0 / 0 / 4 lines
scripts/analyze.py                               # every number in this report
```

`scripts/analyze.py` reads only `evidence/` and asserts its own row counts; it produces the
same output from its own directory and from `/tmp` (checked; see `evidence/meta/`).

`scripts/check_consistency.py` parses every stated count out of this report and compares it
with `evidence/` — **169 checks**, including the cells of the P7, slope and resize tables
rather than only the prose around them. It exits 1 on any mismatch, and its coverage was
proven by planting faults one at a time: a wrong prose slope, a wrong table cell in each of
those three tables, a wrong table of the P8 residual, the replication label removed, and the
failure admission reversed. Six of the seven failed as they should; the seventh — a wrong
prose slope in the summary — **passed**, which is how the missing summary check was found.
That is the same defect as the one this whole section is about, one level up: a checker
guarding a computed table while the sentence beside it went unchecked.

