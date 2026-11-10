# opus_finny_cache — SPEC (names fixed before any code; 2026-11-09 Vienna)

Scope: a Finny-table-style lazy accumulator refresh cache. It must be node-identical (bit-exact eval), default OFF, and built on parent P (= trial_w6 source, commit 7ce10a05), independent of the SMP pack and of int8.

## 1. Names (reserved; nothing is registered by this pack)
| kind | name | default | note |
|---|---|---|---|
| compile-time switch | `FORGE_NNUE_FINNY` | `0` | would be `#ifndef/#define FORGE_NNUE_FINNY 0` in `include/forge/nnue.hpp` (one flip line for kit copies) |
| UCI option | `NnueFinnyCache` | `false` (type check) | advertised only when the switch is 1 |

Both names are free in QA's files and in the trial_w6 source (INVENTORY.md). **This pack contains no engine code (§2)**, so neither name appears in any source.

## 2. Gate decision (plan decision D3, measured; BENCH.md)
- **The trial_w6 network is king-independent.**
  - `nnue::feature_index(perspective, piece, square)` uses only the piece's colour relative to the perspective, the piece type and the square, flipped vertically for Black. That is 768 inputs per perspective, with no king bucket and no king-file orientation.
  - The accumulators are float and every weight is `int/4096`, so a partial sum is exact while |sum| < 2^12. That bound is **not verified here** for all inputs; the verdict does not depend on it, but a float cache would (§3.3).
- **Refresh sites in P** (`src/search.cpp`):
  1. the root of every `Worker::search` (`nnue::refresh(board, ss->accumulator)`), once per `go` per worker;
  2. the fallback in `Worker::static_evaluate` when no valid ancestor exists. During a search the root accumulator is always valid, so this fallback is never reached.
- Every in-tree evaluation replays the recorded dirty pieces from the nearest valid ancestor, i.e. it is incremental.
- **Measured** on an instrumented scratch copy of P (never shipped):

  | run | refreshes | of which in-tree |
  |---|---|---|
  | bench 16 | 8 = 8 roots | 0 |
  | 300 FENs at depth 13 | 300 = 300 roots | 0 |
  | 20 FENs at Threads 4 | 80 = 20 × 4 roots | 0 |

  Refresh work is about 0.016 % of the accumulator work: 300 refreshes of about 32 columns against 27.25 M incremental updates.
- **Consequence.**
  - A Finny cache has no in-tree refresh to replace. The only refresh it could serve is the root refresh (one per search per worker). Even a perfect cache saves well under 0.1 % of eval time, which no timing on this PC can resolve (the job rule: noisy timings cannot establish a 0.1 % gain).
  - **Verdict: NOT APPLICABLE on trial_w6. No engine code, no builds, no option registered.**
  - This is a property of this network, not of the idea. §3 is the exact design for a network where it does apply.

## 3. Design for a king-dependent network (prepared for the owners; not coded here)
### 3.1 Key: when an entry is "sufficient"
An entry may stand in for a fresh refresh of one perspective only if every input to that perspective's feature-index function, apart from piece placement, is the same:
- the **perspective** (colour);
- the **feature bucket** of that perspective, as the network defines it. For HalfKA K32H3^ (INVENTORY.md) that is the 32 mirrored king buckets × 3 material states, i.e. the material state is part of the key;
- the **orientation**: the horizontal-mirror flag when the bucket map mirrors by king file;
- the **network identity**: a generation counter bumped on every successful load or reload, on a `UseNNUE` or architecture switch, and on a net option change, together with the network's architecture id.

For trial_w6, bucket and orientation do not exist, so the key would be (perspective, network generation).

### 3.2 Entry content
For each key: the accumulator of that perspective (the network's type and width), the piece bitboards per (colour, type) that this accumulator represents, the network generation at fill time, and a `valid` flag.

### 3.3 Refresh through the cache, and when it is bit-exact
1. `acc = entry.acc`.
2. For each (colour, type): subtract the columns of `entry.bb & ~board.bb`, then add the columns of `board.bb & ~entry.bb`.
3. Store `entry.acc = acc` and `entry.bb = board.bb`.

**Exactness rule.**
- Integer accumulators with wrapping adds give exactly the fresh result.
- Float accumulators give it only if every partial sum is exactly representable. For int/4096 weights that means `|partial| < 2^(24-12)`. This must be proven per network: from the weight file, take the maximum over all inputs of |bias| + the 32 largest |column| values.
- If exactness cannot be proven, the cache must not be used. A cache that drifts is a failed speed-only qualification, not an acceptable approximation.

### 3.4 Event table: valid, dirty, invalidated, discarded
| event | king-dependent network (e.g. HalfKA) | trial_w6 (768 inputs, no buckets) — what P does |
|---|---|---|
| quiet move, capture, en passant, promotion, castling rook | incremental via dirty pieces; cache untouched | the same: `dirty_pieces` removes the mover, removes the captured piece (en-passant square for EP), adds the promotion piece or the mover, and moves the rook on castling |
| king move inside the same bucket and orientation | incremental | incremental (the king is an ordinary feature) |
| king move, or castling, into another bucket or orientation | that perspective: refresh through `cache[new key]`; the other perspective stays incremental | cannot happen (no buckets) |
| material-state change (K32H3^: the opponent's queen captured or promoted) | the bucket changes: refresh through the cache | cannot happen |
| null move | no piece change: child = parent; cache untouched | the same (`record_null_move`: `dirty.count = 0`, replayed as a copy) |
| make / unmake | lazy accumulator stack per ply; unmake pops it (no cache access) | the same (`record_move` marks the child invalid; `static_evaluate` walks back) |
| search start (root) | refresh through the cache (diff against the last board stored for that key) | **the only refresh site in P** |
| ucinewgame, Clear Hash | entries cache a pure function of (board, network), so they may stay. For warm-state proofs, a fixed choice: keep. Exactness makes either choice node-identical | not applicable |
| network reload, `UseNNUE`, architecture change | invalidate all entries (generation bump; a generation mismatch means discard and refill) | not applicable |
| Threads change | per-worker caches are created and destroyed with their worker | not applicable |
| thread isolation | one cache per worker, thread-private, no atomics; never shared between workers | not applicable |
| discard | key or generation mismatch: fresh refresh, then refill the entry | not applicable |

### 3.5 What a future implementation must show (job prompt; this pack runs none of it)
- Cached and fresh scalar refreshes bit-for-bit equal on the 12k FENs and on long make/unmake walks (every accumulator value).
- Bench pins net on and net off, and perft.
- Full fens12k net on and net off at go depth 13, with the option ON and OFF.
- Warm-state identity, including reuse across searches, `Hash` / `Clear Hash` / `UseNNUE` changes and a network reload.
- Threads 1 node identity.
- A compile-time-0 build byte-identical to its parent. A gate build with the option default OFF, pc1 = pc2.
- NPS is advisory only. Any node or eval drift fails the speed-only qualification.
