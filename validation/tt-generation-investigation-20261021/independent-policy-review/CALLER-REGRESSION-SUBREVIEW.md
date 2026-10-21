# TT refresh policy: caller and regression subreview

Reviewed 2026-10-21T01:58:56.674753+00:00. Source-only; no edits to policy/source, builds, tests, engine searches, timings or Git commands. This report contains its input hash manifest; no separate manifest or JSON was created.

The **actual guarded trial** at `src/search.cpp` SHA-256 `1ef518e8c6f87824a70e653e237bc09acdd64493c4cf183330b573c25e88ec11` is suitable for a bounded correctness trial. It refreshes only occupied matching-tag hits whose stored generation differs, under the existing stripe lock or valid exclusive-owner lease, before the immutable snapshot. The original archived **UNAPPLIED** patch `49808b3a3b124dc7c1ff60ccb14db46f9a46827c158f48d0525cbf603e2c5d3b` also assigns `gen_bound` on current-generation hits. Keep that historical patch unchanged; it is not the actual trial. Frozen22 search identity is `40cf7fd45d0bd6d5dd075cf1392bd1ed3c7fa2cbffbbc275b4edeb6fe5b37f0b`. Root reports the isolated23 trial branch; this reviewer binds files rather than querying Git.

The recorded nine actual-parent table checks and twelve baseline/observer roots justify trying this isolated hypothesis. They do **not** validate the policy candidate: the nine checks establish baseline behavior and some intentionally reverse under refresh; twelve-root parity authenticates observer neutrality, not candidate parity. The report records 6,461 old hits and 3,366 actual direct-cutoff branches, but zero tracked evictions with a bounded collision-prone tracker. Recency benefit, speed and Elo remain unproved. Parent owns independent raw-log/source/core authentication; no additional observer or pressure workload was run here.

## Callers and invariant boundaries

- Both main search and qsearch call `probe` before checking score usability or cutoff eligibility. Thus refresh includes rule50-rejected scores, PV/window/depth-rejected cutoffs, excluded-move verification searches, move-order-only and raw-eval-only hits. It is a **hit-recency** policy, not a useful-score-only policy. Terminal draw/max-ply returns occur before the relevant probe and must not be assumed to touch it.
- `TTEntry::score_usable` remains unchanged: both clocks below90 may reuse; near the boundary the capped clocks must match. Main direct cutoffs additionally require current clock below90. Both searches guard TT-score-as-eval substitution with usable `tt_score`; raw `tte.eval`, `tt_move` and PV metadata can still be consulted separately. Refresh must neither make an unusable score usable nor change its rule50 clock.
- Low three bits retain bound/occupied status and was-PV; key, move, score, raw eval, depth, rule50 and padding remain untouched. The immutable returned entry reflects the refreshed generation. `ss->tt_pv` and qsearch's PV metadata must retain the same low-bit meanings.
- Snapshot owner/slot/cluster/key/epoch construction is unchanged. Refresh must not increment epoch, reselect a slot at store, invalidate a live same-epoch handle or make a stale lifecycle handle valid. Store still examines the selected slot's **current** contents and updates a nonempty move independently of score admission.
- Replacement score remains `depth - 4 * relative_age`. However probe refresh removes the old-age reason for a subsequent shallow nonexact same-key overwrite. That includes a deep **rule50-incompatible** old score: it may now remain protected even when its score was rejected by the caller. Exact or sufficiently deep stores still admit normally. This coupling is intended experimental scope, not a correctness fix.
- `hashfull` remains locked and sampled, but a touched old occupied entry now counts as current without any store. Total occupancy has not increased; do not interpret the new metric as more allocated capacity.
- Shared callers retain striped locking. The one-worker Exclusive path retains its gate, stripe drain and TLS ownership; foreign callers wait. `new_search`, clear, resize and destruction still require all accessors quiescent. Do not add concurrent lifecycle operations to a stress test.

## Exact regression work for this trial

| Target | Required observation |
|---|---|
| Old/current/empty hits | For BoundUpper/Lower/Exact with PV false/true, an occupied old hit changes only generation and returns the changed generation. Repeated current hits retain the whole tuple. Matching-tag empty/BoundNone entries and misses are not refreshed. Current-hit byte equality cannot alone prove absence of a redundant write; retain the explicit source guard. |
| Replacement and control | Reuse A(depth12/gen0), then B/C/D(depth8/gen1), touch A, miss a fifth key: choose B after refresh; untouched control still chooses A. Preserve first-slot ties, match-before-empty and miss selection. Avoid probing the untouched control A during assertions: `probe` itself now touches. |
| Admission coupling | After an old deep hit, a shallow nonexact store must retain score/eval/depth/bound/PV/rule50 while allowing the existing independent nonempty-move update; `Move::none` retains the move. Exact and sufficient-depth admissions still work. Include an old clock99 entry probed at clock0, then a shallow low-clock nonexact store: document the expected retained incompatible payload rather than silently changing admission policy. |
| Opaque delayed destinations | Select an old victim with a miss handle, refresh that victim with a separate hit so it is no longer the best replacement, then store through the miss handle: overwrite its originally selected slot. Keep prior local snapshots unchanged. |
| Clock and search callers | Extend existing real Worker rule50 fixtures by aging TT **quiescently** before the warm query. Cover low-to-high and high-to-low rejection, matching near-limit qsearch reuse, score-as-eval rejection and a legal clock-reset child. Existing targeted draw/mate results remain mandatory; do not impose universal warm/cold node parity. Include old main/qsearch direct cutoffs and excluded/PV/eval-only paths to demonstrate the broad touch contract. |
| Hashfull and wrap | Fill four sampled same-cluster entries, age without touching, confirm old count0; probe all four without stores, confirm current count1 permille. Exercise31→0 refresh and32-generation epoch invalidation even when generation bits repeat. |
| Concurrent old-hit mutation | Existing concurrent test uses generation0 throughout and therefore never exercises the new old-hit write. Seed, call `new_search` before starting threads, then mix same-stripe old-hit readers, correlated stores and hashfull. Check every returned tuple and final generation/count; retain current-only stress. Run the actual candidate under default TSan. |
| Lease and lifecycle | Reuse actual public-API coverage for Shared, Exclusive one-worker, multiworker fallback, foreign probe/store/hashfull blocking,1→4→1, stop/join and exception cleanup. Preserve stale/default/foreign/key-mismatched handles, allocation-failure behavior, resize/clear and immutable snapshots from all eight existing TT groups. |
| Search screening | A fresh empty-table one-worker search should retain the baseline tree/result because no entry becomes old within that root search. Warm-root policy results may legitimately differ. Require legal moves/PVs and full native correctness/sanitizers before controlled timing and a separate fresh paired equal-clock strength experiment. Do not pool with the ongoing21/22 experiment. |

The existing TT suite covers many invariant guards, but it has no old-hit refresh contract or old-hit concurrency mutation case. Its score-context test stays in one generation; its hashfull test refreshes through stores. Add the bounded targeted cases above rather than replacing these checks or demanding observer-style exact warm-tree parity from a policy change. The historical gated-lease API coverage is reusable infrastructure, not automatic validation of the new writes.

Decision: **proceed to isolated correctness validation of the guarded actual policy; no integration, performance acceptance or Elo claim from this review.** If correctness and controlled performance permit, preregister a distinct strength comparison against pinned22. Keep the coupled recency/admission/hashfull scope explicit.

## Input SHA-256 manifest

| File | SHA-256 |
|---|---|
| include/forge/search.hpp | 3d9208de205b4bd2f8e82f6c64137be253eb51aa0a418d5e39e1c06392e95eb9 |
| src/search.cpp | 1ef518e8c6f87824a70e653e237bc09acdd64493c4cf183330b573c25e88ec11 |
| tests/tt_coherence_tests.cpp | cc2fe3e9fb0059f409876345e8cfb3c008ede401751a4dad76b022f743238fd5 |
| tests/rule50_tests.cpp | c6faa20bf0ac2327d792e9dbacb867bdbbb93db0f5d8aafa188c3ad76a066673 |
| validation/tt-generation-investigation-20261021/REPORT.md | 6719aabfc22b0cff7591e831f4c483bd75f7006888d4376423ee1ff78b51e426 |
| validation/tt-generation-investigation-20261021/SUMMARY.json | e069e6fa4be6496795d562e35c9999de7ce90b8b893903f88a5f667247f99133 |
| validation/tt-generation-investigation-20261021/generation-refresh-policy.UNAPPLIED.patch | 49808b3a3b124dc7c1ff60ccb14db46f9a46827c158f48d0525cbf603e2c5d3b |
| validation/tt-generation-investigation-20261021/table_fixture.cpp | 2e0ccaed7305ed8eec93d8321cc2566a6dbbb3d628db759d75c9e5ad9d78194b |
| validation/tt-generation-investigation-20261021/search_walk.cpp | 3eac4f612ba8d972a3cd1679dc4c4b7addb3a87553390d951671dfb4bdc7ea78 |

## Closure update: actual twelve-group trial suite

Reviewed 2026-10-21T02:00:56.569110+00:00. The manifest above already binds the actual new test file `cc2fe3e9fb0059f409876345e8cfb3c008ede401751a4dad76b022f743238fd5` and guarded search `1ef518e8c6f87824a70e653e237bc09acdd64493c4cf183330b573c25e88ec11`. The earlier gap discussion describes the original eight-group baseline. I have now read all four added groups and the twelve calls in `main`; **no static blocker to the first native correctness run**. No test/build/search was executed by this reviewer.

The additions cover all three occupied bounds with both PV flags, complete payload/padding preservation, immutable snapshots, current repeated hits, shallow admission and independent move updates, stale/key-mismatched handles, empty/zero-key/BoundNone/miss behavior, replacement/hashfull consequences, and31→0 wrap. The new concurrency group ages only while quiescent and uses two disjoint initial readers plus a writer barrier: four genuinely old hits occur before the first new store. It then checks correlated tuples with stores/hashfull; the original current-generation concurrency group remains.

The detailed caller/rule50/lease and delayed-destination cases above remain integration-regression guidance, not claims of executed coverage or reasons to repeat the observer. Proceed with the bounded actual twelve-group/native/sanitizer validation owned by root. This closes the source-only review; no integration, timing or Elo acceptance follows.
