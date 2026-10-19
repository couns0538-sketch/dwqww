# Independent review: Forge 6.4 TT verification-tag correction

Reviewed 2026-10-19, read only. No builds, matches or repository changes were performed by this reviewer.

Base commit: `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`.

Reviewed diff: `include/forge/search.hpp`, `src/search.cpp`, `tests/tests.cpp`.

SHA-256 of `git diff --` for those three files at review time:
`954a804ba8ba624c2823dafa9d303dc29c618722bd8e38bc49d7a1b1709eeb39`.

## Verdict

**No blocking defect found in the targeted patch.** The change correctly removes substantial overlap between the cluster index and stored verification tag on the multiply-high backend. It preserves the appropriate high-half tag on the modulo backend, updates probe and store consistently, and introduces a regression that directly exposes the old false-hit behavior without relying on a chess search or probabilistic collision.

This is a narrowly scoped correctness improvement. It does not make the TT collision-free, synchronize shared TT accesses, repair rule-50/repetition score eligibility, or establish an Elo gain.

## Correctness of index/tag selection

`TTCluster` contains four `TTEntry` objects and is aligned to 64 bytes (`include/forge/search.hpp:76`). `resize` derives the cluster count from the requested MiB and `sizeof(TTCluster)` (`src/search.cpp:183`). For the current 64-byte cluster, 64 MiB gives `2^20` clusters.

The multiply-high index is `floor(key * cluster_count / 2^64)` (`include/forge/search.hpp:120`). When the cluster count is `2^m`, this is exactly the top `m` bits of the key. Previously, the tag was also the top 32 bits. Therefore, at Hash64 the top 20 bits of the stored tag merely repeated the index; only 12 additional bits distinguished unrelated full keys in the same cluster. At the default Hash32, only 13 additional bits remained.

The new low-32-bit tag (`include/forge/search.hpp:106`) is disjoint from those index bits for every supported power-of-two Hash size. Hash is exposed from 1 to 2048 MiB in `src/uci.cpp:164`, corresponding to at most `2^25` clusters with the current layout. Thus, the low 32 tag bits remain fully distinct from the index bits throughout this range.

For non-power-of-two counts, multiply-high buckets are intervals of consecutive 64-bit keys. Their width is approximately `2^64 / cluster_count`. Low-32-bit values cycle repeatedly within each interval, with frequencies differing by at most one. At 3 MiB, the 49,152-cluster buckets contain roughly 87,381 complete low-32-bit cycles. There can be slight boundary correlation; it is not the destructive high-bit reuse of the old tag. The implementation is sound for these sizes too.

The fallback uses `key % cluster_count` (`include/forge/search.hpp:122`). At power-of-two counts, that index consumes low bits, so keeping `key >> 32` is the correct complementary choice. For non-power-of-two counts it likewise retains strong discrimination: for a fixed high half, the low half spans many possible values per remainder. The fallback's effective behavior is unchanged by this patch.

**Minor wording observation, not a blocker:** the comment calling low bits “independent” is literally exact for power-of-two multiply-high table sizes. “Use the low bits so the index does not consume the tag bits” would avoid implying exact statistical independence for every non-power-of-two size. No code change is necessary for correctness.

## Probe/store consistency

Both `probe` and `store` call the same `verification_key` helper (`src/search.cpp:197` and `src/search.cpp:218`). This matters because `store` uses tag equality to decide whether it is updating the same position, including preserving an existing move and deciding whether to keep a deeper entry. The patch updates both paths consistently.

No replacement-depth, age, score, bound, move, generation, occupancy, cluster-index or prefetch policy changes are introduced. A zero low tag remains valid because emptiness is determined by `occupied()`/bound bits, rather than by a zero tag (`src/search.cpp:199`).

## Regression quality

The regression at `tests/tests.cpp:484` uses four keys per group, fitting the four-entry cluster exactly. It clears the table between groups, requires a miss before first storing each distinct key, then retrieves every key and checks its distinct score. There is no legitimate capacity eviction to confuse the expected result.

Independent integer arithmetic confirms the chosen fixtures:

| Size | Group | Multiply-high cluster indices | Modulo cluster indices |
| --- | --- | --- | --- |
| 1 MiB / 16,384 clusters | Same high half; low halves 1,2,3,4 | 1165,1165,1165,1165 | 1,2,3,4 |
| 1 MiB / 16,384 clusters | Same low half; separated high halves | 1165,4237,7309,10381 | 7920,7920,7920,7920 |
| 3 MiB / 49,152 clusters | Same high half; low halves 1,2,3,4 | 3495,3495,3495,3495 | 1,2,3,4 |
| 3 MiB / 49,152 clusters | Same low half; separated high halves | 3495,12711,21927,31143 | 7920,7920,7920,7920 |

In group two, neighboring full keys differ by `3 * 2^60`, which is divisible by both tested cluster counts. This deliberately makes the fallback case meaningful at both sizes. The same group occupies separate clusters under multiply-high, so identical low tags there are harmless and correctly accepted.

The parent's reported **12 baseline failures** match the mechanism exactly: under the old multiply-high implementation, the first group's last three insert probes falsely hit, then the first three retrievals return the last stored score. That is six failures per table size, over two sizes. This is a precise negative control, not a regression that simply restates the patched expression.

The existing `test_transposition_table` checks intact data retrieval, deeper-entry/move preservation and clearing. Together, these tests cover the changed lookup and same-position paths appropriately for this fix.

A native multiply-high test run does not execute the modulo conditional branch. The fixture is valid for that branch by inspection and arithmetic; a fallback-build result should only be described as tested if the parent actually runs one. Because the fallback expression itself is unchanged, this is not a blocking gap in the fix.

## ABI and performance

- The helper is a private static constexpr member defined in the class. It adds no instance field, virtual function or table storage. `TTEntry` and `TTCluster` layouts are unchanged.
- The conditional is compile-time and mirrors the existing indexing conditional. In an optimized build the helper should inline to the cast/shift already needed for the tag. It introduces no allocation, lock, lookup or runtime backend selection.
- On multiply-high builds, forming the tag no longer requires shifting the key down by 32 bits. This is not evidence of an NPS improvement; generated code and measurements remain the authority.
- The existing TT is allocated/cleared per process and is not a persistent file format, so changing the in-memory tag interpretation creates no network, book, UCI or saved-file migration requirement.
- An unchanged short bench signature is compatible with this fix: the benchmark need not encounter a harmful collision. The patch may intentionally change search results where the old table reused a colliding entry. It must not be advertised as universal search equivalence solely because `bench 11` stays at 417491.

## Boundaries of the fix

1. **Truncated-tag collisions remain.** Distinct full keys can still share both cluster index and the selected 32-bit tag. The patch restores tag discrimination; it does not compare all 64 key bits.
2. **SMP races remain outside scope.** The pre-existing unlocked non-atomic TT accesses and comment about catching torn entries are not corrected here. Matching a tag and checking move legality cannot generally certify that the entire concurrently written entry was read consistently. This is an existing issue, not introduced by the patch.
3. **Rule-50/repetition eligibility remains outside scope.** The patch does not add halfmove/history state to keys or change score-reuse policy.
4. **Strength remains a separate gate.** Baseline-negative/fixed-positive regression evidence establishes this bug repair. Equal-clock fastchess SPRT is still required for a new measured strength claim under the user's requested acceptance policy.

## Evidence status

The parent reported the unchanged baseline passed all four CTest tests and `bench 11` produced 417491, then reported 12 new-regression failures when linking the added tests against the unchanged baseline core. Those executions were not independently rerun by this reviewer. This review independently inspected the diff and surrounding code and verified the collision fixtures by integer arithmetic only. Candidate build/test/bench/strength results belong to the parent's validation logs.
