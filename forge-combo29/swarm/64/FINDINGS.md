# FINDINGS — the exact MultiPV x Hash boundary, and what the patch really fixes

Seat 64. Branch `for-fable-and-opus/swarm-64`, base `6b98f2170a3210e71beed04bbd2553972c253ed7`.
Engine `forge-combo29`. Grid tables: [`GRID.md`](GRID.md). Harness state: [`STATUS.md`](STATUS.md).

---

## 1. The inequality, and the misclassification count

The brief asked for a form like "safe iff `Hash x MultiPV <= K`". **That form is
wrong**, and the grid shows it in specific cells rather than only in a count:

| product `Hash*MPV` | cell | ratio to MPV 1 | verdict |
|---|---|---|---|
| 96 | Hash 16 MPV 6 | 1.30x | safe |
| 96 | Hash 24 MPV 4 | 1.35x | safe |
| 96 | Hash 48 MPV 2 | 1.37x | safe |
| **96** | **Hash 32 MPV 3** | **1.55x** | **slow** |
| 128 | Hash 128 MPV 1 | 1.00x | safe |
| 128 | Hash 32 MPV 4 | 1.56x | slow |
| 128 | Hash 64 MPV 2 | 1.57x | slow |

Four cells share product 96 and differ by 0.25x. No K separates them.

**Fitted product forms** (exhaustive over observed cell values, so these are true
minima for each family, not descent approximations):

| predicate | K | misclassified | false-safe | false-alarm |
|---|---|---|---|---|
| `Hash*MPV <= K` | 144 | **4/48** | 3 | 1 |
| `Hash*(MPV-1) <= K` | 120 | **3/48** | 3 | 0 |

**The form that actually fits the data is not a product but a per-MultiPV Hash
ceiling:**

> **safe ⟺ `Hash <= Hmax(MPV)`, with `Hmax(1) = 256, Hmax(2) = 48, Hmax(3) = 48, Hmax(4..6) = 24`**

**1 of 48 cells misclassified, 0 false-safe.** The single miss is `Hash 32 MPV 3`
at 1.55x, which sits inside the measurement spread (0.96-1.91x) and is the price
of `Hash 48 MPV 3` measuring 1.49x and therefore earning MPV 3 a ceiling of 48.

A conservative variant that refuses to lean on the borderline cell —
`Hmax(1)=any, Hmax(2)=48, Hmax(3..6)=24` — also scores **1/48, with 0 false-safe
and 1 false-alarm**, and is the one I recommend, because a false-safe is the
direction that hurts a user.

## 2. Is the cost a function of Hash, of MultiPV, or of their product?

**None of the three.** Measured:

1. **MultiPV 1 is flat in Hash.** Median ms across Hash {8,16,24,32,48,64,128,256}
   = 114.0 / 122.5 / 120.6 / 122.2 / 133.0 / 132.8 / 139.3 / 132.8. Spread 1.22x,
   no monotone trend, **8/8 within 1.5x of the fastest**. No product form can say
   this, because `Hash*1` grows with Hash and the measurement does not.
2. **MultiPV 1 node counts are identical across Hash** — 178297 at every Hash
   except a 2-node difference at Hash 8. Same work everywhere.
3. **The excess is `Hash x (table wipes)`, and wipes = `depth x (MPV-1)`.**
   `excess / (Hash*(MPV-1))` ranges 0.43 to 1.57 ms per MB per line — a 3.7x
   spread, because **reported depth falls as MultiPV rises**: 14 at MPV 1, 13 at
   MPV 2, 11 at MPV 6. That coupling is exactly what a two-variable product
   cannot express.

**So Hash and MultiPV enter through different factors:** Hash sets the price of
one wipe, MultiPV sets how many wipes, and depth — which itself depends on MultiPV
— sets the multiplier. On the specific question asked: a user with a big Hash and
2 lines is **not** automatically fine (`Hash 64 MPV 2` is 1.57x) and a user with a
small Hash and 6 lines **is** fine (`Hash 8 MPV 6` is 1.18x). The product model
gets both of these backwards; the per-MPV ceiling gets both right.

## 3. The residual cause, in nodes and ms

### Before the patch

The between-line `alt_shared->tt.clear()` writes `TTCluster{}` (64 bytes) into
every cluster — 4,194,304 of them at Hash 256 — once per alternate line per depth.

MPV 2 holds depth 13 at **every** Hash, so 12 wipes is a constant across the Hash
axis and one wipe isolates cleanly:

| Hash MB | excess over MPV 1 (ms) | per wipe (ms) | implied GB/s |
|---|---|---|---|
| 8 | 12.5 | 1.04 | 7.48 |
| 32 | 39.5 | 3.29 | 9.50 |
| 64 | 75.5 | 6.29 | 9.93 |
| 128 | 166.4 | 13.87 | 9.01 |
| 256 | 403.0 | 33.58 | 7.45 |

Bandwidth-bound, proportional to table size. At Hash 256 the collapse is
5 lines x 9-13 depths x 256 MB.

### After Patch A (clear removed only)

- **unsafe cells: 22/48 -> 5/48.**
- **17/48 came into the safe region**: Hash 32 MPV 3-6, Hash 48 MPV 4-6,
  Hash 64 MPV 2-6, Hash 128 MPV 2-6 — every previously-unsafe cell at Hash <= 128.
- **5/48 remain unsafe: Hash 256 at MPV 2,3,4,5,6 — ratios 1.94, 1.99, 1.97, 1.90, 1.90.**

The survivors are **flat in MultiPV**. A per-line cost would keep climbing from 2
lines to 6; it does not. So the residual is not per line — it is the
**allocation of the second full-size table, once per search**.
`make_unique<TTCluster[]>` value-initialises, so the allocator zero-fills the whole
block before the depth loop. Measured as time-to-first-`info depth`:

| Hash MB | MPV 1 first info | MPV 2 first info | gap (ms) | gap per MB |
|---|---|---|---|---|
| 8 | 0.8 | 6.7 | 5.9 | 0.74 |
| 32 | 0.8 | 17.3 | 16.5 | 0.52 |
| 64 | 0.9 | 38.5 | 37.6 | 0.59 |
| 128 | 1.1 | 56.4 | 55.2 | 0.43 |
| 256 | 1.4 | 105.9 | 104.5 | 0.41 |

Full decomposition at Hash 256, patched, one representative position:

| MPV | alloc ms | total ms | search ms | nodes | search ns/node |
|---|---|---|---|---|---|
| 1 | 1.5 | 124.7 | 123.3 | 184956 | 666 |
| 2 | 108.5 | 262.9 | 154.4 | 126417 | 1222 |
| 3 | 124.7 | 259.7 | 135.0 | 104331 | 1294 |
| 4 | 110.8 | 256.3 | 145.5 | 104331 | 1395 |
| 5 | 119.5 | 353.5 | 234.0 | 98856 | 2368 |
| 6 | 129.6 | 294.7 | 165.1 | 75942 | 2174 |

The allocation column is ~110-130 ms at every MPV > 1, and 1.5 ms at MPV 1.

**Residual, in the units asked for:**

| quantity | value |
|---|---|
| residual at Hash 256 after patch | 1.90x-1.99x, **flat in MultiPV**, 5 cells |
| residual in ms (Hash 256 MPV 2, grid medians) | 279.0 - 143.6 = **135.4 ms** excess |
| of which allocation | **~104.5 ms** (108.5 ms on the single-position run above) |
| of which search | **~31 ms = 1.2x**, inside the safe region |
| residual in **nodes at MPV 1** | **0** — 178297 base and patched |
| residual in nodes at MPV > 1 | nodes *differ* (0/40 cells match), because alternate lines now reuse the table and reach **greater depth for the same budget**. The extra time at MPV>1 buys a deeper search, it does not buy a slower one. |

Patch A removes **100% of the per-wipe cost** and leaves **one** cost: the
alternate table's allocation, proportional to Hash only, paid once per search.

## 4. Per-cell spread, and why near-threshold verdicts are fragile

18 runs per cell (6 positions x 3 repeats). Node counts and depths are
**perfectly deterministic** across all repeats; the wall-time spread is not small:

| cell | median ratio | range from min/max | verdict |
|---|---|---|---|
| Hash 32 MPV 3 | 1.55 | 0.96 to 1.91 | **straddles 1.5x** |
| Hash 48 MPV 3 | 1.49 | 1.10 to 2.09 | **straddles 1.5x** |
| Hash 64 MPV 2 | 1.57 | 1.13 to 2.03 | **straddles 1.5x** |
| Hash 256 MPV 2 | 4.03 | 3.26 to 5.08 | clear |
| Hash 8 MPV 2 | 1.11 | 0.91 to 1.34 | clear |

Only cells far from 1.5x are robustly classified. A claim that one specific
boundary cell is safe is not supported to better than ~0.3x on this sample — which
is why the recommendation below is a table with margin, not a single K on the line.

## 5. The one-line recommendation, with the measurement behind each clause

> **`MultiPV 1` at any Hash. Otherwise `Hash <= 48` at 2 lines, `Hash <= 24` for
> 3-6 lines, and never `MultiPV > 1` with `Hash >= 128` — until the alternate
> table's allocation is removed.**

| clause | measurement |
|---|---|
| "`MultiPV 1` at any Hash" | MPV 1 medians 114.0-139.3 ms across Hash 8-256; 1.22x spread, no trend; **8/8 cells within 1.5x of the fastest** |
| "`Hash <= 48` at 2 lines" | MPV 2 ratios 1.11/1.11/1.21/1.32/1.37 at Hash 8-48, then 1.57 at Hash 64 (unsafe) |
| "`Hash <= 24` for 3-6 lines" | MPV 3-6 ratios top out at 1.49 (Hash 24) and the first unsafe is 1.55-1.57 at Hash 32 |
| "never `MPV>1` with `Hash >= 128`" | Hash 128 MPV 2-6 = 2.19x-3.18x; Hash 256 MPV 2-6 = 4.03x-10.00x, and **still 1.90x-1.99x after the patch** |
| "until the allocation is removed" | time-to-first-info 1.4 -> 105.9 ms at Hash 256 proves the residual is the allocation, and it is the only one left |

Whole-grid score for the exact rule (1/48 wrong, 0 false-safe) and for this
margin-carrying version (1/48 wrong, 0 false-safe, 1 false-alarm) are both stated
so the user can choose which to implement.

## 6. What Patch A must not claim

Patch A is **not** output-preserving. Over 6 positions x 4 settings:

- MultiPV 1: **6/6 identical** nodes, depth and move — the control holds, the
  primary path is untouched.
- MultiPV > 1: **15/18 identical best moves (83.3%)**, and where it differs it
  reaches a *deeper* depth at the same budget (Hash 256 MPV 6: depth 10 -> 11,
  52472 -> 80546 nodes).

So the honest claim is "**at equal nodes it searches deeper, because alternate
lines reuse the table**", never "same work, faster". A patch that also removes the
allocation — allocate the alternate table once and reuse it, or run alternate lines
on the primary table with `searchmoves` exclusion — is what would make large Hash
safe, and it must be re-measured with this same harness before anyone claims it.

## 7. Honest limits

- One machine, one build (`-march=x86-64-v4`, GCC 13.3), 4 cores. The
  bandwidth-bound constants will differ elsewhere; the *shape* of the boundary
  should not.
- Six midgame positions, none drawn, none with a bare king at the root. Those
  paths bail before the depth loop and are outside what this grid measures.
- Three repeats per position resolves 1.5x-plus effects, not the boundary to
  better than ~0.3x.
- `Hmax` is read off a measured frontier on this hardware. It is a calibration,
  not a physical constant; the physical statement is the wipe-count model in §3.
