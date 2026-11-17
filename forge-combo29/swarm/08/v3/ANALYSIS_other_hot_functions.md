# Does the same removable-test pattern exist in the other two v3 hot functions? — seat 08

The count-dispatch patch showed a removable per-lane test is worth **+1.2 % at 8.47 % share**. So the coordinator's
question is right: check the other two v3 hot functions for the same shape. **Answer: one of them has it, one does
not.**

## `refresh_from_pieces` (6.78 % share) — NO removable per-lane test

```cpp
for (int piece = WP; piece <= BK; ++piece) {
    Bitboard removed = entry.pieces[pi] & ~pieces[pi];
    Bitboard added   = pieces[pi] & ~entry.pieces[pi];
    while (removed != 0) { const int sq = pop_lsb(removed); sub_column(...); ++cache.columns; }
    while (added   != 0) { const int sq = pop_lsb(added);   add_column(...); ++cache.columns; }
    entry.pieces[pi] = pieces[pi];
}
std::copy_n(entry.values.data(), hidden, destination);
```

**There is no lane predicate to hoist.** The loop bounds (`removed`/`added` bit counts) are **data-dependent** — the
number of changed pieces varies per call — so there is no small fixed set to specialise on, which is exactly what made
the count-dispatch patch work. `add_column`/`sub_column` are already a single 512-bit loop each.

**A different inefficiency does exist here, and I am NOT taking it:** for *k* changed pieces the code performs *k*
separate load-and-store passes over `entry.values` (1 KB per pass). Batching them into one pass would cut the loads.
I am leaving it because (a) it is a bigger rewrite than a hoist, and (b) with a short remaining window a rewrite that
moves one node would cost more than it could gain. **Recorded as an opportunity, not attempted.**

## `evaluate` / `output_sum_avx512` (7.34 % share) — ONE candidate, and it is small

```cpp
alignas(64) std::int32_t lanes[32];
_mm512_store_si512(..., lanes);
_mm512_store_si512(..., lanes + 16);
std::int64_t sum = 0;
for (const std::int32_t lane : lanes) sum += lane;   // <-- 32 scalar adds per evaluate
return sum;
```

**This is the one removable per-lane tail in the file**: a store to memory followed by a 32-iteration scalar sum, per
`evaluate` call (2,556,881 calls on bench 13). The same question as the last patch: how much is a per-lane test worth
here?

**Predicted size, before measuring:** 32 scalar adds x 2.56 M calls = ~82 M adds. At ~0.3 ns each that is ~25 ms of
~2100 ms, about **1.2 %** — the same order as the last patch. **But the compiler may already vectorise that sum loop**,
in which case the patch buys nothing. That is the kill condition: if the bench moves by less than 0.5 %, the compiler
was already doing it and I report a rejection.

## What I will measure, and what I will NOT claim
Identity first on a clean-tree build (all eight benches, three evals, the 200-opening sum 27,944,084), then speed by
the same two-build-each protocol as Step 3. **If identity fails or the bench gain is under 0.5 %, it is a rejection
with numbers, not a win** — the same standard the last patch had to meet.
