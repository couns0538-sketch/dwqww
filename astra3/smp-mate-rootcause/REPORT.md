# A2 — bounded SMP mate investigation

Status: **WIP — native serial reproduction completed; root cause and production fix UNVERIFIED**. The dated sections below supersede preparation status. No A2 engine/header/CMake changes, no fix, no Elo claim.

Base: integration `93c51b3` (engine source `926c55f33227bc4a030d7ce5b1140528aeba75af`). The driver under `source/a2_tt_seed_repro.cpp` uses Forge's public `Worker`/TT APIs and logs raw main/helper results before any selector. It is not compiled or run yet.

First experiment: fresh 16 MB shared TT and workers per condition/trial, serial helper seed K=1..14, then main depth 14, two searches retaining TT/worker histories. Compare fresh empty-TT controls. If a cp miss repeats without concurrent workers, helper-generated TT content is sufficient. An optional concurrent mode waits for seeded atomic helper-node targets; it records observed nodes and delay, without claiming deterministic OS scheduling.

TT snapshots cover unique positions through three legal plies, only after both searches finish. `probe()` ages entries, so snapshots must not be moved between measured searches. They cannot identify the worker that stored an entry or establish GHI provenance.

The source-grounded follow-up is preserved in `astra3/integration/A2_HANDOFF_PREPARATION.md`: distinguish score effects from move ordering, inspect LOWER/EXACT versus UPPER bounds at the child after d5c5, trace repetition provenance through ancestors, and separately inspect cold mate-3 root reductions. These causal hypotheses remain unverified.

Next: finish safety review, verify exact core/header source and compile flags, compile against the qualified A1 library only after parent GO, then run one bounded serial sweep. Preserve stdout/stderr, original TSVs, hashes, and timeout/error status. No test failure rate has been measured by this harness.

IDEA_SOURCE: user Round 3 A2 handoff and Forge's existing public worker/TT interfaces; no external engine code or tuned constants.

## Native first sweep — 2026-10-29 02:45:26 PDT

Build and native execution now completed. The build helper verified71 frozen source/header/CMake hashes against both worktrees and exact Release flags before linking the original A1 core archive. Build receipt and source/binary hashes are in build_first; exact invocation and original stdout/stderr are in native_serial_first_command. No engine source changed.

All28 empty-TT main results were31995/d5c5. Of28 helper-seeded main results,9 were CP at full actual/nominal depth14,18 were31995/d5c5 and1 was a longer mate score that remains unverified. Zero timeouts. K1 round1 reproduces CP484/e8e4; K2 both rounds reproduce CP449/e8e4. The selector is never called, and main starts after helper completes in this mode. This narrows the failure without asserting a specific TT semantic root cause. Counts are diagnostic, not a playing-strength estimate.

The final TT snapshots are after round2 only. They cannot prove the pre-main K1 entry or per-store provenance. K2/K10/K12 have CP LOWER entries at depth9 after d5c5; these need provenance/oracle investigation. Next: fresh-round1 K1 targeted score-only rewrite using ValueNone, paired with identical-score rewrites, and require every non-score field to remain identical. Public TT store preserves an existing move on MoveNone, so it cannot supply a clean move-only mask. No fix is claimed.

## Score-only diagnostic checkpoint — 2026-10-29T02:55:00.355835-07:00

The bounded rewrite mode is implemented in the existing test driver, with separately fresh no-touch, identical-rewrite and score-mask controls for root and child. All public non-score fields must remain identical; the opaque slot is not introspected. Source SHA2563f76a90bb0836f79fdd4e7598f2ff34a5dcd9122c8ca7abb21e85874a4fabbe6. Compilation and independent review are in progress; native rewrite results remain UNVERIFIED. Prior original serial evidence remains unchanged.
