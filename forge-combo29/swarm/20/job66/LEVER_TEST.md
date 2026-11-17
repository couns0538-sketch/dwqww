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

| Hash | repaired (alt table = main) | **repaired + alt capped at 64 MB** | ⚠ is this a fix? |
|---|---|---|---|
| 128 | 13.5 | **14.0** | **NO — diagnostic only** |
| 256 | 12.0 | **14.0** | **NO — diagnostic only** |
| 512 | **6.5** | **14.0** | **NO — diagnostic only** |
| **2048** | **1.0** | **14.0** | **NO — diagnostic only** |

> ⚠ **The flat 14.0 in the right-hand column is NOT a fix to adopt.** It is one main line's depth under a change that
> shrinks the table the ALTERNATE PV lines search — and the alternate lines are the whole point of a MultiPV analysis
> feature. Line quality for those lines is **unmeasured** (see the open requirement below). Read the column as
> *evidence about the mechanism*, never as a recommendation.

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

## THE OPEN REQUIREMENT, now measured — and the cap DOES change the alternate lines

I flagged line quality as unmeasured. I measured it on 5 positions at Hash 2048, MultiPV 3, comparing each line's
score between the repaired-uncapped and the capped build:

| position | uncapped (multipv 1 / 2 / 3) | **capped (1 / 2 / 3)** |
|---|---|---|
| 1 | **no lines at all** (depth 1, nothing published) | cp −292 / −293 / −316 |
| 2 | −261 / −322 / −348 | −251 / **−349** / **−359** |
| 3 | 201 / 188 / 177 | **278** / **262** / 176 |
| 4 | −528 / −536 / −540 | **−660** / **−733** / **−743** |
| 5 | −241 / −278 / −280 | **−573** / **−1029** / **−1055** |

**The differences are large and in BOTH directions** (position 3 improves by ~77 cp; position 5 degrades by ~330–775 cp).
So the cap does **not** leave the analysis untouched — it changes what the alternate lines report, substantially, on some
positions.

## Verdict: the cap is NOT a proposal, and now I know why
- **The mechanism is confirmed** (S-C42): the alternate table's size is the residual cost.
- **The cap is not a candidate fix**: it trades main-line depth for **large, unpredictable changes in the alternate
  lines' scores** — which is precisely the output a MultiPV analysis feature exists to provide. On position 5 the third
  line moves from −280 to −1055; whatever that position is, those are not interchangeable reports.
- **Note position 1 honestly:** the uncapped build published **no lines at all** at Hash 2048 (depth 1, nothing to
  report), so there the capped build is strictly more informative. That cuts the other way and I am not hiding it —
  it means the cap is not uniformly worse, it is **unpredictable**, which is a worse property for a feature than
  uniformly worse.

## The requirement this leaves open
A real fix has to **keep the alternate lines' search quality while removing the double allocation** — e.g. share one
table between the lines with disjoint generation stamps, or size the alternate table adaptively rather than at a fixed
cap. **I have not built or tested either.** The requirement is now precise: *restore main-line depth at large Hash
without moving the alternate lines' scores*, and the measurement above is the acceptance test.
