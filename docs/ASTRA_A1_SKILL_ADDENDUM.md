# Proposed training-data validation addendum

Status: **PROPOSED; NOT INSTALLED** (2026-10-30). Extend the existing
[validate-chess-engine skill](skill://user/6ad5f7d7bfb4819190376efc04503df1/validate-chess-engine/SKILL.md)
under its correctness/evidence guidance; do not create another engine skill.
The provider exposes reading, but no callable skill-creator or skill-edit tool
was found in this session. The actual proposed skill files are now in
[`skills/validate-chess-engine`](../skills/validate-chess-engine/SKILL.md), retaining
the existing name and recovered references. This document records their provenance
and validation limits. See the [bundle notes](../skills/validate-chess-engine/BUNDLE.md)
for the unavailable provider script and how to preserve an existing installation.

IDEA_SOURCE: Forge's own FPOS/FHCE producer, trainer and Job D parser;
the user’s immutable-data and exact-label requirements; local regression tests.
Skill authoring guidance: `superpowers:writing-skills` and
`superpowers:test-driven-development`. No other engine code is used.

## Proposed reusable guidance

The consolidated guidance is now in
[`references/training-data.md`](../skills/validate-chess-engine/references/training-data.md).
It requires complete row/metadata validation, state-origin preservation, output
accounting, real-holdout scope, native exit evidence, sealed publication, and
separate format, throughput and strength conclusions. It also covers writable
fsync descriptors, POSIX-only inode-change semantics for ctime, PowerShell 5.1
stderr handling, and per-shard storage measurements with all retained indexes
and cumulative prior keys. Under the crew retention policy, no routine prune or
delete step is authorized; explicit crew approval is required.

## Evidence and validation status

The earlier I/O report recorded **16/16**, both normally and with `python -O`,
against source hashes in `validation/astra-a1-data/format_tests/evidence_manifest.json`.
That historical manifest is absent from this checkout; this bundle does not
reverify the earlier result.
The earlier report identifies original normal/optimized stdout, stderr, exit
metadata, and the earlier manifest failure at that location. It records a
manifest regression failing first (exit 1), then passing after publication was
repaired, with the failed source snapshot retained. Those historical preservation
claims were not independently rechecked for this bundle.

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

**Broad skill behavioral validation remains UNVERIFIED.** A bounded baseline
and with-guidance review is recorded in the bundle's
[`review-scenarios.md`](../skills/validate-chess-engine/review-scenarios.md).
The baseline already recognized the principal defects; this is a retrieval and
technical-review check, not evidence that the guidance caused a behavioral gain.
It does not replace Windows runtime checks or original software regressions.
The interrupted-agent and CPU-accounting guidance still lacks workflow-level
validation. No installation or provider edit has been performed.

## Proposed QA extension: optional dependencies and large indexes

Status remains PROPOSED / NOT INSTALLED. No duplicate skill was created. The
installed skill provider is read-only in this environment; these additions belong
in the same existing validator's training-data guidance after review.

These requirements are consolidated in the same training-data reference: full
dependency notice/include review, retained-index disk accounting, trusted complete
holdout identities, Windows native launch and portable file validation. The
repository bundle extends the existing skill; it introduces no duplicate skill.

Evidence for these concrete workflow failures and regressions is in
`validation/astra-converter-20261030/qa_licence_fix/`, `qa_fix_disk/`, and
`qa_holdout_clearance/`, plus Job1's `qa_windows_fix/` on the exporter branch.
These are software regression checks, not evidence of skill installation or
general agent compliance. Historical raw logs remain unchanged.
