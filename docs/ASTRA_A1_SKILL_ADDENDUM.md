# Proposed training-data validation addendum

Status: **PROPOSED; NOT INSTALLED** (2026-10-30). Extend the existing
[validate-chess-engine skill](skill://user/6ad5f7d7bfb4819190376efc04503df1/validate-chess-engine/SKILL.md)
under its correctness/evidence guidance; do not create another engine skill.
The provider exposes reading, but no callable skill-creator or skill-edit tool
was found in this session. This repository document is the reviewable change.

IDEA_SOURCE: Forge's own FPOS/FHCE producer, trainer and Job D parser;
the user’s immutable-data and exact-label requirements; local regression tests.
Skill authoring guidance: `superpowers:writing-skills` and
`superpowers:test-driven-development`. No other engine code is used.

## Proposed reusable guidance

For training-data work, record the following before claiming an output valid:

| Required field | Validation contract |
|---|---|
| Format and orientation | Identify the producer/trainer revision and hashes. FPOS v1 is columnar, not row-interleaved: header, packed boards, STM scores, metadata. Results are White-relative. FHCE stores STM HCE values. Verify counts, sizes, piece nibbles and label ranges. |
| State provenance | FPOS omits castling, en passant, clocks, game IDs and best moves. Exact labels require an authoritative full-state sidecar. Match every full text row by board, STM, original score and White result, with identical row count/order. Counting a suffix without decoding it proves count only. |
| Derived-state provenance | A reconstructed no-castling/no-EP/clock-zero FEN is a distinct input policy. Keep that origin in every downstream manifest and require explicit origin when consuming FEN-only sidecars. Saving reconstructed state as a full FEN does not make it original; exclude it from exact-label counts. |
| Holdout scope | Exclude supplied holdout 013 and 014 positions. Record which complete holdouts or prefixes were actually available. Position overlap zero does not prove game exclusion: that requires authoritative game IDs. Missing 014 or game IDs remains an explicit limitation. |
| Immutable inputs and publication | Hash original inputs, binary and source. Write only new output prefixes; retain failed partials and original evidence. Publish success after all checks and owned workers exit cleanly. Serialize manifests before publication; malformed metadata must not leave a final manifest. |
| Native process evidence | Retain original requests, responses, stderr, command and actual child exit status. Check request IDs, operations, response count, output bounds and binary identity. A shell pipeline’s last exit code is not the test process exit code. Terminate only processes owned by this run. |
| CPU throughput | Report actual OS CPU time for the measured process scope and wall time separately. Per-query timers omit startup/idle/shutdown; cores × elapsed time is allocated capacity, not measured CPU. Include thread/hash/node settings, affinity, sample scope and counted successful rows. |
| Interrupted collaboration | Check agent status after user steering. A message alone does not resume an interrupted/idle worker; use a follow-up task to trigger continuation, preserving file ownership and current progress. |
| Seal boundary | Keep external verification and console receipts outside sealed output folders. Adding an unmanifested file changes the bundle even if its data bytes are unchanged. Require process exit zero, all hashes and independent accounting checks before accepting a legacy run whose summary was published before its manifest. |
| Search completion | Distinguish completed search depth/score from an aborted iteration's displayed depth and partial bestmove. An initial UCI cp0 placeholder is not a completed label. A documented insufficient-budget response is an explicit exclusion, not permission to invent a score. |
| Portable evidence | Validate one case-insensitive namespace for archive files, explicit directories, implied parents and the built-in manifest. File-only collision checks miss Windows file/directory aliases. Re-read every archived payload and verify the published server digest. |

Report format correctness, native legality/search validity, trainer compatibility,
throughput and training/playing strength as separate conclusions. Unit fixtures
are not real sample measurements; loss or throughput changes establish no Elo.

## Evidence and validation status

The I/O suite passed **16/16**, both normally and with `python -O`, against
the exact source hashes recorded in
[`format_tests/evidence_manifest.json`](../validation/astra-a1-data/format_tests/evidence_manifest.json).
Original normal/optimized stdout, stderr, exit metadata, and the earlier manifest
failure are preserved there. The manifest regression failed first (exit 1), then
passed after publication was repaired; the failed source snapshot is retained.

Relevant executable regressions:

- [`test_forge_pos.py`](../tests/data/test_forge_pos.py): columnar bytes,
  result orientation, complete text alignment, truncation, no-overwrite,
  explicit reconstruction, empty outputs, and manifest failure publication.
- [`test_relabel_positions.py`](../tests/data/test_relabel_positions.py):
  complete sidecar validation even for a slice, reconstructed-origin propagation,
  invalid native responses and failed-shutdown outputs. These are test pointers;
  their latest run status belongs to the project report.
- [`test_filter_positions.py`](../tests/data/test_filter_positions.py):
  supplied-holdout overlap, rule ordering and explicitly limited prefix validation.
- [`test_probe_client.py`](../tests/data/test_probe_client.py): original IPC,
  framing/ID mismatches, nonzero shutdown, changed executable and owned timeout.

**Skill behavioral validation is UNVERIFIED.** Code regression tests establish the
data-tool contracts, not future agent compliance. Before applying this addendum
to the provider skill, run no-guidance/with-guidance scenarios covering a partial
sidecar, a reconstructed sidecar relabeled twice, unavailable holdout game IDs,
and a successful query followed by nonzero child exit. Preserve actual responses
and correct any omissions. The interrupted-agent rule and CPU accounting rule
also require workflow-level checks; they are not claimed as covered by the I/O
suite. No installation or provider edit has been performed.

The additional seal-boundary, search-completion and portable-evidence guidance
comes from this session's preserved failures and subsequent regressions. Those
code checks do not replace the behavioral skill-validation requirement above.
