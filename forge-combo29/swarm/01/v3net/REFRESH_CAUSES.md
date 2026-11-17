# The refresh path has two causes, and my Step 2 hypothesis was wrong (S-F116)

Continues `REFRESH_RATIO.md`, and **corrects a claim I made there**. The page said the cache key was at fault and
that "a key that also tracked which pieces moved would hand back something one or two columns away". That is wrong,
and one measurement settles it.

## Splitting the counter by cause

`refresh_from_pieces` is called from exactly two places, which are different problems:

| call site | when | source tag |
|---|---|---|
| `make_valid` → `refresh_cached` (`nnue_v3.hpp:281`) | no valid ancestor within the stack | **cold** |
| `replay_ply` (`nnue_v3.hpp:268`) | the perspective's **king bucket changed** while replaying | **king** |

I added a `source` argument and two more counters to the same stats patch. Identity first, all four configurations:

| row | nodes | published | result |
|---|---|---|---|
| no net | 862,329 | 862,329 | PASS |
| PC20 | 587,276 | 587,276 | PASS |
| test net only | 4,151,906 | 4,151,906 | PASS |
| PC20 + test net | 3,652,372 | 3,652,372 | PASS |

## The split

| configuration | refreshes | **cold** | **king** |
|---|---|---|---|
| test net only | 6,087 | **2** | **6,085** |
| PC20 + test net | 6,485 | **2** | **6,483** |

**99.97 % of refreshes come from king-bucket changes.** The "no valid ancestor" path fires **twice in a whole
`bench 13`** — it is effectively dead code in this workload. Per node, the king path fires once every **563 nodes**.

## The internal check that makes this trustworthy

The two populations cost different amounts, exactly as the mechanism predicts, which is what tells me the tagging is
right and not an artefact:

| population | columns per refresh | what that means |
|---|---|---|
| cold | **29.5** (59 / 2) | a full rebuild from bias plus every man — the bench mean is 24.9 pieces, max 32 |
| king | **6.99** (45,294 / 6,483) | a cached diff, ~7 of ~25 pieces differ |

If both call sites were measuring the same thing these numbers would coincide. They differ by 4.2× in the direction
the code says they should.

## Why my hypothesis was wrong, and the code that refutes it

`feature_index` (`nnue_v3.cpp:518`) begins with the **bucket**:

```518:523:src/nnue_v3.cpp
int feature_index(KingKey key, Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = (perspective == White ? square : square ^ 56) ^ static_cast<int>(key.flip);
    return static_cast<int>(key.bucket) * InputsPerBucket + (relative_color * 6 + type) * 64 + relative_square;
}
```

`key.bucket * InputsPerBucket` is the leading term. **When the king moves to a different bucket, every feature's
weight index changes** — not just the king's own. So a rebuild is not waste caused by a lazy cache key; it is a
**correctness requirement** of the architecture. A cache that tracked which pieces moved would still have to
recompute every column, because every column points into a different slice of `w1`.

My earlier sentence was a plausible story about cache granularity that the code contradicts. It survived because I
wrote it while reading `refresh_from_pieces` and not while reading `feature_index`.

## What this means for Step 2, honestly

* The **upper bound** on any win from this path is `refresh_from_pieces`'s share of `bench 13`: **4.79 %**. Even
  making it free moves the v3 path from 19.05 % to 14.26 % of the benchmark.
* The **king path cannot be removed** — a bucket change requires new weights. What *can* be attacked is its cost:
  6.99 columns plus a fixed 1 KB copy-out per refresh.
* The **cold path is not worth touching**: 2 occurrences. A patch there would be unmeasurable, and filing it as a
  speed fix would be exactly the "test that cannot fire" shape of Trap 8.
* **Therefore the honest Step 2 target is the 1 KB `std::copy_n` at `nnue_v3.cpp:711` plus the ~7 column pass**, not
  the cache key. And before writing anything I should check whether the destination copy can be avoided at all —
  the accumulator could be built directly into its final slot rather than into the cache entry and then copied out.
  That is a real question; it is not yet a claim.

## The transferable lesson

**A mechanism story needs the line that implements it.** I had read the function where the cost appears
(`refresh_from_pieces`) but not the function that decides its size (`feature_index`), and the story I built from
half the code was wrong in the direction of "someone was careless". The engine was not careless: the bucket is part
of the weight layout. Cost 20 minutes of measurement to discover, and it would have cost a wasted Step 2 patch
otherwise.
