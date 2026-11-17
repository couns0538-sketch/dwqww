# Predictions, registered before any instrumented run

Written at build time, before the trace build existed and before a single counter was read.
Kept unedited below this line so the match/mismatch verdict has something to be against.

## The constraint supplied with the assignment

Prior data: `Hash 16` vs `64` differ 0/24 cells at `go nodes 50000`, 2/24 at 200k, 17/24 at
500k, 24/24 at 1M, 40/40 at 2M. `Hash 1` differs **already at 50k, 11/24**.

The assignment reads this asymmetry as evidence *against* a collision account: if collisions
were the cause, `Hash 1` should be "the last to be clean at low budgets, not the first to be
dirty."

## Where I disagree, stated before measuring

Under any collision account, the **smallest** table is the **first** to be dirty, because for a
fixed position set and node budget the load factor is inversely proportional to table size.
`Hash 1` being dirty at a budget where `Hash 16` is clean is the *signature* of collision
pressure, not its refutation. It is only evidence against collisions if the dirty cells at
`Hash 1`/50k turn out to have **zero** evictions, i.e. if the table is empty enough that
collisions cannot have happened yet.

So my reading of "the clue" is the opposite of the assignment's, and the measurement below is
set up to settle it rather than to confirm either reading. Concretely: count evictions at
`Hash 1`/50k. If they are ~0 and the cell is dirty, the collision account is dead. If they are
plentiful, it survives and the asymmetry argues for it.

## Candidate mechanisms, and what each predicts at `Hash 1` / 50k specifically

| # | Mechanism | Prediction at Hash 1, 50k | Prediction at Hash 16, 50k | Prediction at Hash 64, 1M |
|---|---|---|---|---|
| A | Occupancy collisions: distinct positions in one cluster evict each other | **non-zero evictions**, and dirty cells have more of them than clean cells | zero evictions | non-zero evictions |
| B | Key-tag truncation: `key32` is the low 32 bits, so a *different* position can be accepted as a hit ("false hit") | ~0 (needs two keys sharing low-32 bits in one cluster; birthday over 4×16384 slots) | ~0 | ~0 |
| C | Shallow-entry shadowing: a hit on a shallower entry supplies `tt_move` and a wrong score | non-zero `hit_depth_lt` | non-zero but smaller | non-zero |
| D | Replacement-policy damage: `depth - 4*age` at equal age evicts the shallowest, so depth-0 qsearch entries die first — harmless — but at high load the victim is a real search entry | evicted-depth histogram skews to 0 at 50k | histogram all zeros | histogram has mass at depth ≥ 1 |
| E | Something that is not collisions at all (e.g. a size-dependent arithmetic path) | any | any | any |

`A` and `D` are the same mechanism seen at two resolutions. `B` is a correctness claim, not a
strength claim, and would be a finding regardless of whether it explains the divergence. `C`
is load-independent and therefore cannot explain a threshold that moves with budget — if `C`
is the only counter that moves, the honest answer is that no counter explains the divergence.

## Falsifiable headline predictions

1. **Evictions at `Hash 1`/50k are non-zero.** If zero, mechanism A is dead and the
   assignment's reading wins on that point.
2. **False hits (mechanism B) are zero or near-zero at every size and budget.** Any
   non-zero count is a bug report in its own right; I predict I will not get one.
3. **`hit_depth_lt` does not track the divergence.** It should be roughly monotone in nodes
   at *every* size, so it will be high at Hash 16/1M (dirty) *and* at Hash 16/50k (clean).
   If it is the only counter that separates the cells, the counters do **not** explain it.
4. **The evicted-depth histogram at `Hash 16`/500k stays at zero mass for depth ≥ 1**, which
   means Hash 16 is not losing real search entries at that budget — so if Hash 16 is dirty
   there, collisions cannot be the cause and the answer must be "not established".
5. **The `hashfull` number quoted in the earlier report is not comparable across sizes**:
   `hashfull()` samples `min(1000, cluster_count)` clusters, so it measures 6.1% of `Hash 1`
   and 0.006% of `Hash 1024`. I predict this defect is real and independent of everything else.

Prediction 4 is the one that can kill my own preferred mechanism. It is the one I would most
like to be wrong about, which is why it is written down first.
