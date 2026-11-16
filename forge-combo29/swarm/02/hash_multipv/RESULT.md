# Hash size x MultiPV: a 167x slowdown, on BOTH builds, at depth 6

Found while re-running area-2 job 1 on the PC build: two sequences produced no `bestmove` within my driver's
20 s limit. Investigating that turned up a much larger behaviour than the two timeouts.

Builds and settings: **base** = 6b98f217 release (sha256 e06310ec…); **PC r15** = file-5 patch, release.
**Threads 1** on every run (seat 04). MultiPV default is 1; the table sets it explicitly. Fresh process per
cell, interactive driver, `position startpos`, `go depth 6`.

## the table (`scaling.txt`, both builds)

| Hash MB | MultiPV | base ms | PC ms | info lines |
|---|---|---|---|---|
| 16 | 1 | 2 | 2 | 6 |
| 16 | 8 | 43 | 44 | 48 |
| 64 | 8 | 125 | 119 | 48 |
| 256 | 8 | 509 | 515 | 48 |
| 512 | 8 | 1721 | 1668 | 48 |
| 1024 | 8 | 3558 | 3537 | 48 |
| 2048 | 8 | 7180 | 7108 | 48 |

At MultiPV 1 the Hash size costs **nothing** (2–3 ms at every size, both builds). At MultiPV 8 the cost is
**linear in Hash size**: about 3.5 ms per MB. Hash 2048 + MultiPV 8 = **7.2 s for a depth-6 search from
startpos** — and the number of `info depth` lines is 48 at every size, so the engine is NOT searching more; the
time goes somewhere else.

## the discriminating measurement (the one that names the cause)

| Hash 2048 | time |
|---|---|
| ONE `go depth 6` with MultiPV 2 | **1667 ms** |
| TWO `go depth 6` with MultiPV 1, same process | **3 ms total** |

So the work is not search work: two full searches cost 3 ms while one two-line search costs 1667 ms. At Hash 16
the same MultiPV-2 search costs 15 ms. The cost is in the MultiPV bookkeeping path.

## the mechanism, read in the source and then measured
src/search.cpp, the extra-PV loop that runs once per additional line:

```
alt_shared->stop.store(false, ...);
alt_shared->ponder_hit_ns.store(0, ...);
alt_shared->tt.clear();          // <-- a FULL table clear, per extra PV line
alt_worker->clear();
const SearchInfo alt = alt_worker->search(board, narrowed, false, alt_list);
```
and `TranspositionTable::clear()` (src/search.cpp:372-376) walks every cluster:

```
void TranspositionTable::clear() {
    for (std::size_t i = 0; i < cluster_count_; ++i) clusters_[i] = TTCluster{};
    generation_ = 0;
    ++epoch_;
}
```

Measured cost of ONE such clear (`setoption name Clear Hash`, which calls the same function), and the MultiPV
overhead it has to explain (`clear_vs_multipv.json`):

| Hash MB | one `tt.clear()` | MultiPV 8 minus MultiPV 1 | ratio |
|---|---|---|---|
| 16 | 2 ms | 41 ms | 20.5x |
| 256 | 20 ms | 507 ms | 25.4x |
| 512 | 38 ms | 1719 ms | 45.2x |
| 1024 | 75 ms | 3556 ms | 47.4x |
| 2048 | 172 ms | 7178 ms | 41.7x |

The overhead is ~42–47 clear-equivalents at the large sizes, which is consistent with 7 extra lines each
clearing the table a handful of times per iteration across 6 iterations. I am not claiming an exact count —
the ratio is stable at ~45x for 512 MB and above and drops at 16 MB, and I did not instrument the clear count
to prove the per-iteration figure.

## finding
**S-F7 — `Hash` above ~512 MB combined with `MultiPV` above 1 makes every search enormously slow, because the
extra-PV loop calls `tt.clear()` (a full table walk) once per extra line. At Hash 2048 + MultiPV 8 a depth-6
search from startpos takes 7.1–7.2 s instead of 2 ms — 167x — with the SAME node count. Present on BOTH builds
(the PC r15 patch does not touch it).** Settings: Threads 1, both builds, base + S14/PC20 not needed (this shows
at default options).

This matters to the owner because PC20 does not set MultiPV or Hash — it inherits whatever the GUI last sent —
so a GUI that leaves MultiPV above 1 and raises Hash for analysis hits this silently. It is a pure performance
defect: the moves and scores are right, they just take seconds.

## harness note (the timeout that led here)
My PC job-1 run flagged two `go depth 6` lines with no bestmove. They were NOT hangs: one replayed at 11.5 s
under the 4-way concurrent ASan load, well inside a 20 s timeout in isolation, and the cause was this Hash 2048 x
MultiPV 8 interaction inside those particular random sequences. Recording it because "2 missing bestmoves on the
PC build, 0 on the base build" would otherwise read as a PC regression; it is not.

## confirmed under the owner's real PC20 settings
The table above used default options plus the two that matter. Re-measured on the PC build with the full PC20
set applied (Threads 1, Hash <size>, S14's 14, the four switches, MateAlphaGuard, OwnBook false):

| Hash | MultiPV 1 | MultiPV 8 |
|---|---|---|
| 16 | 2 ms | 51 ms |
| 2048 | 2 ms | **6966 ms** |

Same behaviour, so S-F7 is not an artefact of leaving the other options at default.

## the proof that the extra time buys NOTHING (same nodes, same PVs)

Hash 16 vs Hash 2048, MultiPV 5, `go depth 4`, base build (`identical_work_proof.py`):

```
Hash 16   depth 4 multipv 1 score cp 30 nodes 404  time 23   pv e2e4 e7e5 c2c3 c7c6
          depth 4 multipv 5 score cp -10 nodes 1320 time 23   pv h2h3 b7b6 e2e3
Hash 2048 depth 4 multipv 1 score cp 30 nodes 404  time 3088 pv e2e4 e7e5 c2c3 c7c6
          depth 4 multipv 5 score cp -10 nodes 1320 time 3088 pv h2h3 b7b6 e2e3
```

**Identical node counts (404 … 1320), identical scores, identical PVs, identical hashfull** — only `time` and
`nps` differ, by 134x. The engine does exactly the same search and spends 3 seconds clearing a transposition
table it does not need to clear. That is what makes this a defect rather than a tuning question: all five
`multipv` lines are emitted correctly in both cases, so the output is right and only the wall time is wrong.

## on a real clock this becomes a STRENGTH loss, not just slowness — the serious form of S-F7

PC build, Threads 1, OwnBook false, `go wtime 5000 btime 5000`, **three runs per cell**:

| Hash | MultiPV | wall (ms) ×3 | depth actually reached ×3 |
|---|---|---|---|
| 16 | 1 | 143 / 445 / 146 | **16 / 18 / 16** |
| 16 | 8 | 346 / 340 / 342 | 12 / 12 / 12 |
| 2048 | 1 | 175 / 184 / 179 | 16 / 15 / 16 |
| **2048** | **8** | 1204 / 1180 / 1180 | **1 / 1 / 1** |

With five seconds on the clock, `Hash 2048` + `MultiPV 8` reaches **depth 1** — reproducibly, three out of three.
The same engine with `Hash 16` + `MultiPV 1` reaches depth 16–18. So a GUI that leaves MultiPV above 1 and
raises Hash for analysis does not merely get slow feedback: **its actual playing search collapses to depth 1**,
because the per-line `tt.clear()` eats the whole clock budget. The wall time is only ~1.2 s of the 5 s available,
which means the search is not even using its time: it is stuck clearing tables and reports depth 1 as its best.

That is a much more useful statement for the owner than "it is 167x slower": the defect costs playing strength,
not just patience. The GUI-side workaround is one option: **keep MultiPV at 1 when Hash is large**, or keep Hash
small (16–64 MB) when MultiPV is above 1.

---

# THE THRESHOLD (the deliverable the owner asked for)

PC r15 build, Threads 1, OwnBook false, `position startpos`, **3 runs per cell**, fresh process per cell.
Raw: `grid_raw.log`, `grid.json`, `grid_meta.json`. Script: `s_f7_grid.py`.

## TABLE 1 — depth actually reached on a 5-second clock (`go wtime 5000 btime 5000`)

| Hash \ MultiPV | MultiPV 1 | MultiPV 2 | MultiPV 3 | MultiPV 5 | MultiPV 8 |
|---|---|---|---|---|---|
| **16 MB** | **d16** (148 ms) | **d15** (266 ms) | **d14** (233 ms) | **d13** (298 ms) | **d12** (344 ms) |
| **64 MB** | **d16** (152 ms) | **d14** (200 ms) | **d14** (309 ms) | **d10** (171 ms) | **d9** (215 ms) |
| **256 MB** | **d16** (160 ms) | **d8** (231 ms) | **d8** (297 ms) | **d4** (297 ms) | **d2** (358 ms) |
| **2048 MB** | **d16** (181 ms) | **d1** (913 ms) | **d1** (1040 ms) | **d1** (1197 ms) | **d1** (1183 ms) |

## TABLE 2 — wall time on the same clock (median of 3 runs)

| Hash \ MultiPV | MultiPV 1 | MultiPV 2 | MultiPV 3 | MultiPV 5 | MultiPV 8 |
|---|---|---|---|---|---|
| **16 MB** | 148 ms | 266 ms | 233 ms | 298 ms | 344 ms |
| **64 MB** | 152 ms | 200 ms | 309 ms | 171 ms | 215 ms |
| **256 MB** | 160 ms | 231 ms | 297 ms | 297 ms | 358 ms |
| **2048 MB** | 181 ms | 913 ms | 1040 ms | 1197 ms | 1183 ms |

### the answer to "is MultiPV 3 at Hash 256 safe or already ruined?" — ALREADY RUINED
MultiPV 3 at Hash 256 reaches **d8** against **d16** at MultiPV 1 in the same conditions: **half the depth, gone.**
The wall time barely moves (297 ms vs 160 ms) — which is the trap, because a looking-good clock time hides that
the search is spending it all clearing the table. Any cell that is not MultiPV 1 must be read against the
MultiPV 1 reference in its own row, never against the clock length.

### where the collapse begins, stated plainly
- **MultiPV 1 is safe at every Hash size**: d16 at 16, 64, 256 and 2048 MB. Hash size alone costs nothing.
- **Hash 16 MB is safe to MultiPV 8**: d12 at MultiPV 8, a 4-ply cost against d16 — a real but modest loss.
- **Hash 64 MB starts to hurt at MultiPV 5**: d10 / d9.
- **Hash 256 MB is already broken at MultiPV 2**: d8, and d2 by MultiPV 8.
- **Hash 2048 MB is catastrophic from MultiPV 2 upward**: d1 in every cell, the search never gets past ply one.

So the practical rule is: **the safe region is MultiPV 1 at any Hash, or Hash <= 16 MB at any MultiPV.** The two
knobs multiply; neither is dangerous alone.

## TABLE 3 — the same defect at a FIXED DEPTH, where no clock can be exhausted
`go depth 12`, Threads 1, median of 3 runs:

| Hash | MultiPV | median ms | depth reached | info lines |
|---|---|---|---|---|
| 16 MB | 1 | **31 ms** | 12 | 12 |
| 16 MB | 8 | **349 ms** | 12 | 96 |
| 256 MB | 8 | **1326 ms** | 12 | 96 |
| 2048 MB | 1 | **40 ms** | 12 | 96→12 |
| 2048 MB | 8 | **13709 ms** | 12 | 96 |

**Answer to question 2: YES, it is also a latency problem.** `go depth 12` at Hash 2048 + MultiPV 8 takes
**13.7 seconds** against **40 ms** at MultiPV 1 — the same depth, the same result, 343x the wall time. Nothing
about the clock is involved: a fixed-depth search cannot run out of time, and it still takes 13.7 s.

That makes the defect hit three separate uses:
1. **Playing on a clock**: depth collapses to 1 → lost strength (S-F7b).
2. **Batch/fixed-depth analysis**: every position is 343x slower, so a 1,000-position analysis run that should
   take 40 s takes ~3.8 hours.
3. **Its own `bench`/regression work**: any harness that sets MultiPV above 1 and a large Hash measures the table
   clear, not the search.

**I did not attempt a fix**, as instructed. The GUI-side workaround needs no engine change: keep MultiPV at 1
when Hash is large, or keep Hash <= 16 MB when MultiPV is above 1.

---

# WHY THE CLEARS ARE THERE — my reading (NOT measurement), and what it implies for a fix

Marked plainly: this section is a READING of the source. The measurements above stand on their own; what follows
is my inference about intent, and I say where it is inference.

## what the code is doing, with lines
`Worker::search` allocates a SECOND table for the extra PV lines before the depth loop starts
(src/search.cpp:2380-2391):

```
    // Secondary lines use their own table and histories, so the primary
    // iterative deepening stays the MultiPV 1 search.
    std::unique_ptr<SharedSearchState> alt_shared;
    ...
    if (multipv > 1 && is_main()) {
        const std::size_t hash_mb = std::max<std::size_t>(
            1, shared_.tt.cluster_count() * sizeof(TTCluster) / (1024U * 1024U));
        alt_shared = std::make_unique<SharedSearchState>(hash_mb);
```

So `alt_shared->tt` is a separate `TranspositionTable` **the same size as the main one** — at Hash 2048 that is a
second 2 GB table. Then, inside the depth loop and inside the extra-line loop (src/search.cpp:2500-2504):

```
                alt_shared->stop.store(false, std::memory_order_relaxed);
                alt_shared->ponder_hit_ns.store(0, std::memory_order_relaxed);
                alt_shared->tt.clear();
                alt_worker->clear();
                const SearchInfo alt = alt_worker->search(board, narrowed, false, alt_list);
```

## my reading of the INTENT
The clear is there to make each secondary line an INDEPENDENT search. Two reasons in the code point at it:
1. each line is searched with `narrowed.search_moves` = the root moves not yet banned (line 2497), so if the
   previous line's entries survived, line *k* would be biased toward line *k-1*'s tree and could return a
   duplicate or a wrongly-ordered PV;
2. `alt_worker->clear()` right beside it clears the WORKER's own histories for the same reason — the pair together
   reads as "start this line from nothing", not as a bug.

The counter-evidence that it is not deliberate about COST: the comment above the allocation says the point is
that "the primary iterative deepening stays the MultiPV 1 search" — about ISOLATION, and nothing anywhere
mentions the size of the table being cleared. At `hash_mb = 1` (which is what a small Hash produces, clamped by
the `std::max(1, ...)`) the clear is free, so this never showed up in whoever wrote it.

## and the count, which the measurements pin down
The `tt.clear()` sits inside BOTH the `for (depth = 1; depth <= max_depth; ++depth)` loop and the
`for (index = 2; index <= line_count; ++index)` loop, so the number of clears is
**depths_completed x (multipv - 1)**. For `go depth 12` with MultiPV 8 that is 12 x 7 = **84 clears**. Checked
against the measurement above rather than assumed:

| Hash | one clear (measured) | 84 clears predicted | measured (MPV8 - MPV1) | ratio |
|---|---|---|---|---|
| 16 MB | 2 ms | 168 ms | 318 ms | 1.89 |
| 256 MB | 20 ms | 1680 ms | 1295 ms | 0.77 |
| 2048 MB | 172 ms | 14448 ms | 13669 ms | 0.95 |

At 2048 MB the prediction accounts for **13.7 s of the measured 13.7 s** — the whole cost, with no unexplained
remainder. (The 16 MB row overshoots because at that size other per-line work becomes visible; the 2048 row is
the one that identifies the mechanism.)

## what this means for a fixer — my reading, offered as a choice, not a recommendation
- **REMOVING the clear would change search behaviour**, on my reading: secondary lines would inherit the previous
  line's table entries, so PVs could change. That needs a match, not a patch-and-hope.
- **MAKING IT CHEAP may be a pure speed change**, if my reading of the intent is right. The clear exists to stop
  line *k-1* polluting line *k*; it does NOT need to touch entries line *k-1* never wrote. Clearing only the
  clusters the previous line actually touched (tracked during that line's search) would leave every observable
  identical while costing microseconds instead of 172 ms. Whether that holds is a claim to be TESTED by whoever
  owns the search: the test is that bench 11/13/16, perft 5 and the MultiPV PVs at a fixed depth come out
  bit-identical before and after.
- A cheaper still option, if the isolation can be relaxed: give the secondary table a `new_search()` bump
  (generation, include/forge/search.hpp:152) and let normal aging handle staleness, instead of a full clear. That
  WOULD change behaviour, because entries from the previous line remain probeable, so it belongs with the
  behaviour-changing option, not the speed-only one.

## what I did NOT do
- I did not trace whether the secondary search actually depends on the clear for its correctness, and I did not
  test a modified build. That is the fixer's measurement, not mine.
- I did not verify that `alt_shared` is always allocated at full size in every mode; the allocation is guarded by
  `multipv > 1 && is_main()` (line 2386), which is the only path I exercised.
