# Current handoff evidence — UNPROVEN

The current v8 handoff includes reviewed native-input, manifest-identity and
Lichess repairs. Full suite:544 tests plus11 subtests PASS437.79s. Fresh selected
cohort admission, legacy/results/mirrors/filter proofs and both CPU preflights
PASS. Current implementation commit:d6e1aae8d3bfd542726ffcb8e0fd04d88b8fff7c.
The final review hour and final artifact inventory are still pending. Earlier
v6/v7 and native proofs retain their original source identities.
Use the two commands in [MIX_SPEC.md](MIX_SPEC.md); the crew owns training and gates.

Current manifest: `C:/astra8_data/extension5h_20261103/handoff_v8/manifest.json`.
SHA256: `0695d8a630e2d6247fc9a60237117d00e3cad0e79258e5e6ef71fbf21c216f5b`.
Its [repository copy](evidence/extension5h/verified_v8/handoff_v8/manifest.json) has identical bytes.

| Required check | Current proof |
|---|---|
| 1. No-flag legacy identity on 100k input | [All three artifacts match](evidence/extension5h/verified_v8/input_repair_validation/identity_receipt.json) |
| 2. Result sign and mirror | [1,000 actual binary records and 1,000 mirrors](evidence/extension5h/verified_v8/input_repair_validation/orientation_receipt.json) |
| 3. Deterministic filter | [Million-row run A](evidence/quality6h/filter_budget_million/recipe_a.report.json), [run B](evidence/quality6h/filter_budget_million/recipe_b.report.json); matching payload and metadata hashes |
| 4. Deliberate failures and all-off behavior | [544 tests + 11 subtests](evidence/extension5h/full_cpu_v2/pytest.log), including exact-byte/identity races, native transport, Lichess, optimized-Python checks and prior regressions |
| 5. Per-rule keep rate and timing | [README table](README.md), [six-case command timing](evidence/quality6h/filter_budget_million/selfplay.exit.json), [separate capture timing](evidence/quality6h/filter_budget_million/capture.exit.json) |
| 6. Selected-data sign and mirror | [Pearson 0.6635950368 and 1,000 mirrors](evidence/extension5h/verified_v8/handoff_v8/sign_audit.json) |
| 7. Handoff | [Published verification](evidence/extension5h/verified_v8/input_repair_validation/published_verify.json), [both CPU preflights](evidence/extension5h/verified_v8/handoff_v8/verification.json), [review log](REVIEW_LOG.md) |

[Fresh native input admission](evidence/extension5h/verified_v8/input_repair_validation/native_admission.json)
covers every999,953 selected row without native allocation. The
[shared-source comparison](evidence/extension5h/verified_v8/input_repair_validation/shared_selfplay_source.json)
binds unchanged self-play functions to the original audited records.py snapshot;
it does not replace that historical whole-module identity. The fresh
[bounded three-run filter proof](evidence/extension5h/verified_v8/input_repair_validation/bounded_filter.json)
uses the unchanged10,000-row sample and is not a new million-row timing.

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
[complete admission union](evidence/extension5h/closed_0728/admission_union_v1/SUMMARY.json)
also passes every304,999,573 row, retaining records.py a8ef0f43...7360be attribution.
It grants no
full-corpus holdout or game-ID clearance. [Original-line replay](evidence/quality6h/reservoir_audit/reservoir_receipt.json)
verifies 4,736 sampled labels; the [current native proof](evidence/quality6h/material_validation/native/report.json)
checks those positions, seven edge cases and all mirrors (9,486 perft2 vectors),
plus the five exact-lock bench pins. Perft establishes move/state compatibility,
not NNUE evaluation quality or playing strength.

Both recipes use the same 999,953 rows after excluding 47 board+STM matches with
the complete 013/014 holdouts. The 10,000-row [sample](sample/positions_stm_v1.jsonl)
is 3,139,111 bytes, SHA256
`c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c`.
The historical [full-output inventory](evidence/quality6h/final_pack_v3/full_output_hashes.json)
contains 9,797 retained files, SHA256
`cd198d5165b40dad8b0869d8e5555d7be47149fad30d8c8fce8b5e00a68650cb`.
Its own metadata directory is excluded to avoid self-reference and is bound
separately by the [correctness record](evidence/quality6h/final_pack_v3/correctness_record.json).
The [Forge checker](evidence/quality6h/final_pack_v3/checker.json) passes all 85
references; its scope is consistency and hashes, not independent experiment truth.
An expanded final inventory is pending after CodeRabbit and the final review hour.

The [fresh lock correction proof](evidence/extension5h/closed_0728/lock_correction_v1/REPORT.json)
matches all five corrected bench pins and both supplied perft5 counts, directly
byte-compares the intentionally identical cleared records/metadata streams, and
preserves the v7 file set and hashes. See [R12 handoff](R12_HANDOFF.md).

The [build, SIMD and timing skills](../../skills/SAVED_ENGINE_SKILLS.md) are saved
with exact upstream provenance and full MIT licences. The existing validation
skill was extended with the reusable conversion/audit findings.

No engine changes, training, GPU use or net export occurred. Next owners:
Code Review, Engine NNUE, then Engine QA. FD3A5190/UHO, separate 8moves_v3 and
WAC300 gates are required before any strength claim. **UNPROVEN**.
