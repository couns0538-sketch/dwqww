# Current handoff evidence — UNPROVEN

The v7 handoff includes the reviewed optimization-safe audit repair. The current
full suite passes 360 tests plus 11 subtests. Fresh legacy/result/bounded-filter
checks and both CPU preflights pass; the final review hour remains pending.

Runtime source: `de1de94bf2922f6ad21802e178644ba3799a2989`. Later checkpoints
package evidence and documentation. The reviewed material-admission repair and
v6 verification pass historically. Audit repair commit bc99ba38 changes seven
audit/filter proof guards; unchanged runtime/native results retain attribution.
Use the two commands in [MIX_SPEC.md](MIX_SPEC.md); the crew owns training and gates.

Current manifest: `C:/astra8_data/extension3h_20261103/handoff_v7/manifest.json`.
SHA256: `52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720`.
Its [repository copy](evidence/extension3h/handoff_v7/manifest.json) has identical bytes.

| Required check | Current proof |
|---|---|
| 1. No-flag legacy identity on 100k input | [All three artifacts match](evidence/extension3h/audit_repair_validation/identity_receipt.json) |
| 2. Result sign and mirror | [1,000 actual binary records and 1,000 mirrors](evidence/extension3h/audit_repair_validation/orientation_receipt.json) |
| 3. Deterministic filter | [Million-row run A](evidence/quality6h/filter_budget_million/recipe_a.report.json), [run B](evidence/quality6h/filter_budget_million/recipe_b.report.json); matching payload and metadata hashes |
| 4. Deliberate failures and all-off behavior | [360 tests + 11 subtests](evidence/extension3h/full_optimization_green/pytest.log), including optimization bypass, malformed FEN/PGN, publication, interruption and result-mask checks |
| 5. Per-rule keep rate and timing | [README table](README.md), [six-case command timing](evidence/quality6h/filter_budget_million/selfplay.exit.json), [separate capture timing](evidence/quality6h/filter_budget_million/capture.exit.json) |
| 6. Selected-data sign and mirror | [Pearson 0.6635950368 and 1,000 mirrors](evidence/extension3h/handoff_v7/sign_audit.json) |
| 7. Handoff | [Published verification](evidence/extension3h/audit_repair_validation/published_verify.json), [both CPU preflights](evidence/extension3h/handoff_v7/verification.json), [review log](REVIEW_LOG.md) |

Million-row filter timings belong to source 88b7c6b1, before the later admission
checks. The current validator [replays both complete measured cohorts](evidence/quality6h/material_validation/cohort_replay.json)
and reproduces their serialized hashes; that is a correctness check, not a new
filter-throughput measurement. Capture statistics use a separate completed-gate
PGN cohort, which is excluded from training. Original self-play has no best moves.
True static/root-qsearch comparison remains **BLOCKED** on FD3A5190; depth one is
not substituted. Other filter rules remain off by default.

The [complete descriptive profile](evidence/quality6h/corpus_report/DATA_PROFILE.md)
covers 304,999,573 rows across all 37 closed non-holdout sources using the
historical profiler's Python board-validity check. The newer strict Forge
admission checks have not been applied to every corpus row. It grants no
full-corpus holdout or game-ID clearance. [Original-line replay](evidence/quality6h/reservoir_audit/reservoir_receipt.json)
verifies 4,736 sampled labels; the [current native proof](evidence/quality6h/material_validation/native/report.json)
checks those positions, seven edge cases and all mirrors (9,486 perft2 vectors),
plus the five exact-lock bench pins. Perft establishes move/state compatibility,
not NNUE evaluation quality or playing strength.

Both recipes use the same 999,953 rows after excluding 47 board+STM matches with
the complete 013/014 holdouts. The 10,000-row [sample](sample/positions_stm_v1.jsonl)
is 3,139,111 bytes, SHA256
`c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c`.
The [full-output inventory](evidence/quality6h/final_pack_v3/full_output_hashes.json)
contains 9,797 retained files, SHA256
`cd198d5165b40dad8b0869d8e5555d7be47149fad30d8c8fce8b5e00a68650cb`.
Its own metadata directory is excluded to avoid self-reference and is bound
separately by the [correctness record](evidence/quality6h/final_pack_v3/correctness_record.json).
The [Forge checker](evidence/quality6h/final_pack_v3/checker.json) passes all 85
references; its scope is consistency and hashes, not independent experiment truth.

The [build, SIMD and timing skills](../../skills/SAVED_ENGINE_SKILLS.md) are saved
with exact upstream provenance and full MIT licences. The existing validation
skill was extended with the reusable conversion/audit findings.

No engine changes, training, GPU use or net export occurred. Next owners:
Code Review, Engine NNUE, then Engine QA. FD3A5190/UHO, separate 8moves_v3 and
WAC300 gates are required before any strength claim. **UNPROVEN**.
