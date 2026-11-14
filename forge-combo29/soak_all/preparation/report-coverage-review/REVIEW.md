# Minimal report coverage and historical-status correction proposal

Read-only review snapshot: 2026-11-14 15:10:45 UTC. All writes are in this scratch folder. Live state, renderer, controller, repository files and branches are unchanged. No engine, native test or workload was run. Original snapshots and their hashes are recorded in `commands.txt`.

## Findings supported by current evidence

- Part1's stored counts are the initial checkpoint: release T1 100/T2 400, ASan T1 100/T2 40. The stored status accurately describes that checkpoint but is misleading without a later-retry qualifier in the current report.
- `state.totals.2KRKsplit.counts` records two completed invocations, T1 200 reference checks, T2 400 main trials, zero misses and zero sanitizer diagnostics. Each raw batch has config 40 roots, 5 trials/root, Threads2, Hash16, depth14; matching binary hashes; complete SUMMARY; native exit0; no diagnostics. The same 40 deterministic roots therefore have ten T2 split trials each, as five plus five.
- The combined completed ASan executions are T1 **300** and T2 **440** when adding the initial reduced retry. These are repeated checks, not 300/440 distinct positions. The split trials alone provide the requested ten-per-root coverage.
- The initial full attempt timed out at 440 seconds. The later isolated 2KRKfull attempt timed out at 435 seconds, has `completed:false`, `passed:false`, an empty `completedCountsRecorded`, and remains in `state.incomplete`. Its wrapper exit3/native exit124 is retained; it contributes zero completed coverage. Neither timeout is converted to a pass.
- Existing test/check records total61 with six nonzero checks and zero sanitizer marker reports in the current input set. The initial Part1 table has58/five because it excludes the three later KRK attempts. Both are accurate for their stated scope; the proposal does not change them.
- The repository `soak_all/BRANCH_REVIEW.md` still presents the initial13:51:59 snapshot with r3-21/23 at e04556dd and11 changed/13 placeholder heads. The completed static review at `all-run/branch-review-r3-complete/BRANCH_REVIEW.md` supersedes this with the15:00:12.976 snapshot and all24 implemented heads. Historical evidence must stay historical, not be deleted or silently rewritten as if the earlier heads had already moved.

## Proposed changes

1. `renderer-proposal.patch.txt`: only adds context to Part1's status and replaces the stale generic KRK sentence with initial, supplemental and combined counts taken from existing totals. It does not mutate state, accumulate raw attempts, relabel timeouts, change any denominator, or alter runtime/sanitizer classification.
2. `integration-docs-proposal.patch.txt`: two paragraph changes distinguish the initial one-trial retry from later completed five-plus-five coverage; adds the combined300/440 execution total while keeping both timeout durations and all evidence links.
3. `historical-branch-proposal.patch.txt`: preserves the old snapshot's exact SHAs and counts, adds a clear historical/superseded notice, changes the old review label to initial inventory, and makes r3-21/23 placeholder findings explicitly historical. **Apply this only when the final24 review is published.** The proposed destination/link is `soak_all/BRANCH_REVIEW_R3_COMPLETE.md`; root owns the final naming and should adjust the relative link if publishing elsewhere.

Proposed full copies and a rendered preview are beside the patches. Do not copy `SOAK_ALL_REPORT.proposed.md` over a later live report; regenerate from current state after applying the approved renderer change at an idle boundary. The original renderer snapshot hash is `2cd55f4111e92f788c7f59cdf31f2181e1a68b0230e51cf665a1ab5bb1741b66`; reconcile if the live renderer has changed since then.

## Verification and preserved limitations

`node --check` accepted the proposed scratch renderer. A pure renderer check using copied state, audit and test inputs confirmed: input state unchanged; initial100/40, split200/400 and combined300/440 displayed; missing counters remain unavailable rather than zero; no combined count appears without the split data. Mate, cost, match, runtime/sanitizer sections and the incomplete-attempt/evidence appendices were byte-identical to the original renderer for those same inputs. Only the Part1 status text and KRK coverage paragraph changed. Exact command/output and proposed rendered diff are in `commands.txt`; the check source is `verify-renderer-proposal.mjs`.

The complete report still contains running phases and unverified match work; this proposal makes no global completion, sanitizer-clean, strength, speed or candidate-fix acceptance claim. An initial read looked for a nonexistent `batches/2KRKfull-0001.txt`; incomplete evidence actually resides under `batches/2KRKfull-0001.evidence/`, which was then read. That inspection-path error is retained in the command log and is not an engine failure.
