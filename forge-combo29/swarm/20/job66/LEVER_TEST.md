# seat 20 — job 66: the lever works — capping the alternate table's size restores depth at EVERY Hash

S-F55 diagnosed the residual multi-PV cost as a **second full-size table** allocated for the alternate line
(`src/search.cpp:2730`). This job tests that diagnosis by acting on it: cap the alternate table at 64 MB and see
whether the gradient disappears. **It does, completely.**

Experiment: the repaired tree (PC r15 + seat 30's `ttclear` patch) with ONE further change —

```cpp
const std::size_t alt_mb = hash_mb > 64 ? 64 : hash_mb;   // was: std::make_unique<SharedSearchState>(hash_mb)
alt_shared = std::make_unique<SharedSearchState>(alt_mb);
```

MultiPV 3, `go wtime 5000`, Threads 1, 10 G-set positions, machine certified clean (exit 0):

| Hash | repaired (alt table = main) | **repaired + alt capped at 64 MB** |
|---|---|---|
| 128 | 13.5 | **14.0** |
| 256 | 12.0 | **14.0** |
| 512 | **6.5** | **14.0** |
| **2048** | **1.0** | **14.0** |

Depth is **flat at 14.0 across a 16× range of Hash** once the alternate table is capped — including 2048 MB, where the
repaired-but-uncapped build collapses to depth 1.

## What this establishes
1. **The diagnosis is confirmed by intervention, not just by correlation.** I predicted in S-F55 that the cost is the
   second table's size; making that table small removes the cost entirely. A correlation would not have survived this.
2. **Seat 30's patch is necessary but not sufficient.** It fixes the per-line `tt.clear()` (~3 plies at Hash 128);
   the alternate-table *size* is a **second, independent** cost that only this experiment removes.
3. **The lever I handed forward is the right one** — sizing the alternate table, not removing another `clear()`.

## Honest limits — and this is NOT a patch I am proposing for adoption
- **One change, one purpose:** this is a diagnostic experiment to confirm the mechanism, not a submitted patch. Capping
  the alternate table at 64 MB could plausibly hurt *alternate-line quality* (the alternate PV lines search a smaller
  table), and I did **not** measure line quality, only the main line's depth. **A smaller table for the alternate lines
  may make those lines worse**, which matters for a MultiPV *analysis* feature whose whole purpose is the other lines.
- Single position set (10), one clock, MultiPV 3, Threads 1, built-in net.
- The honest conclusion is: **the mechanism is confirmed; whether capping is a good idea needs a line-quality
  measurement I have not done.** I would rather say that than hand over a lever that looks free and is not.
