# A2 — bounded SMP mate investigation

## Current outcome — 2026-10-29T03:01:46.778165-07:00

**BLOCKED: root cause and production repair unresolved within the bounded budget.** The fallback deliverable is complete: a native, serialized reproducer yields9 CP main results in28 helper-seeded searches (32.14%), against0/28 CP in fresh empty-TT controls. Actual/nominal main depth14, zero timeouts. No selector is called and no helper searches concurrently with main. This is a controlled diagnostic frequency, not the live SMP failure rate or an Elo estimate.

The original Release engine/library remains source926c55f33227bc4a030d7ce5b1140528aeba75af; this branch changes no engine/header/CMake file. Diagnostic executables are test drivers linked to that verified library, not UCI engines with separate bench tables. A1 owns their linked engine's five-depth identity/perft/FMA qualification.

K1 root-score rewrite: no-touch, identical rewrite and ValueNone mask all returnCP484/e8e4 in round1, then31995/d5c5 in round2, with identical nodes/PVs across controls. All public non-score fields are identical after rewrite. The root's seeded score alone is therefore insufficient to explain this K1 miss. The child-after-d5c5 target is absent at K1: the driver exits2 withNO_INTERVENTION and does not create an entry. Its child-mask condition is NOTRUN; the five-condition experiment is incomplete, not PASS. Original stdout/stderr/TSVs and failing exit are retained in native_rewrite_k1*.

A direct per-store worker/history trace is not implemented; final TT snapshots cannot substitute for one. No before/after fix trials,500+500 SMP validation or200x native regression replay have run. No fix, strength improvement or comprehensive absence of races is claimed.

## Preserved chronological preparation and results

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

## Narrowed hypothesis tree / exact next action

| Hypothesis | Current verdict and evidence |
|---|---|
| Mate normalization on store/probe | UNVERIFIED causal role; source formulas look conventional. Need exact before/after per-store trace, not final snapshot inference. |
| Wrong bound or repetition-derived value | UNVERIFIED. Final K2/K10/K12 child entries include CP LOWER bounds; writer and search-history provenance are absent. Repetition return-before-store does not exclude ancestor contamination. |
| Helper depth+1 / TT depth trust | CONFIRMED helper actualK+1 in records; causality UNVERIFIED. Serial K1 seeding suffices; masking only the root score has no effect. |
| Even-helper aspiration widening | Not necessary for this two-worker reproduction: helperid1 has multiplier1. Other window/bound effects remain UNVERIFIED. |
| Torn concurrent TT access / selector | Not necessary for this symptom: serialized helper completes before main and selector never runs, LocklessTTfalse. This does not prove every concurrent path race-free. |
| Cold T1 go mate3 result | UNVERIFIED relationship. Ordinary selective depth5 is not a complete mate proof; requires a separate root reduced/full-research trace. |

Next task: keep this frozen reproducer; add a separate test-only provenance trace for TT score/eval/move decisions at root and the d5c5 child before proposing a production fix. First use a fresh K2-only condition (current driver loops K1 first and aborts on its missing child, so max-seed-depth2 alone will not reach K2). Preserve no-touch and identical-rewrite controls, never insert an absent target. Current root-score-mask negative evidence already answers K1; do not repeat it without a new question. Per-store worker/depth/window/history provenance is still required by A2.

Final diagnostic checkpoint at2026-10-29T03:01:46.778165-07:00. Independent source review found no blocking intervention bug. Native build succeeded; source hash3f76a90bb0836f79fdd4e7598f2ff34a5dcd9122c8ca7abb21e85874a4fabbe6. The failed missing-target experiment is saved, not hidden or reclassified as success. Parent final review remains running.

### Final evidence review checkpoint — 2026-10-29T03:10:40.858589-07:00

FINAL_REVIEW_AUDIT.json independently recomputes the original28/28 control exact mates,9/28 seeded CP results, zero timeouts, matching root rewrite nodes/PVs and all native evidence manifests. Engine/header/CMake are unchanged. This is an evidence-consistency PASS only; A2 remains BLOCKED with no production fix and the child rewrite remains incomplete. No further A2 experiment is running.
