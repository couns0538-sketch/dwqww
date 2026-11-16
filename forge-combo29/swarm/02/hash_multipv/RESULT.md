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
