# A2 — bounded SMP mate investigation

Status: **WIP — native build and all experiments UNVERIFIED**. This is a test-only harness preparation while A1 finishes qualification; no A2 engine/header/CMake changes, no fix, no Elo claim.

Base: integration `93c51b3` (engine source `926c55f33227bc4a030d7ce5b1140528aeba75af`). The driver under `source/a2_tt_seed_repro.cpp` uses Forge's public `Worker`/TT APIs and logs raw main/helper results before any selector. It is not compiled or run yet.

First experiment: fresh 16 MB shared TT and workers per condition/trial, serial helper seed K=1..14, then main depth 14, two searches retaining TT/worker histories. Compare fresh empty-TT controls. If a cp miss repeats without concurrent workers, helper-generated TT content is sufficient. An optional concurrent mode waits for seeded atomic helper-node targets; it records observed nodes and delay, without claiming deterministic OS scheduling.

TT snapshots cover unique positions through three legal plies, only after both searches finish. `probe()` ages entries, so snapshots must not be moved between measured searches. They cannot identify the worker that stored an entry or establish GHI provenance.

The source-grounded follow-up is preserved in `astra3/integration/A2_HANDOFF_PREPARATION.md`: distinguish score effects from move ordering, inspect LOWER/EXACT versus UPPER bounds at the child after d5c5, trace repetition provenance through ancestors, and separately inspect cold mate-3 root reductions. These causal hypotheses remain unverified.

Next: finish safety review, verify exact core/header source and compile flags, compile against the qualified A1 library only after parent GO, then run one bounded serial sweep. Preserve stdout/stderr, original TSVs, hashes, and timeout/error status. No test failure rate has been measured by this harness.

IDEA_SOURCE: user Round 3 A2 handoff and Forge's existing public worker/TT interfaces; no external engine code or tuned constants.
