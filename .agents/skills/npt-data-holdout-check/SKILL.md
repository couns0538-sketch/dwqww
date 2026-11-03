---
name: npt-data-holdout-check
description: Use when qualifying Forge or nnue-pytorch training exports against holdout shards 013 and 014, checking game-level separation, or verifying that full-FEN castling and en-passant state survived conversion.
---

# NPT Data Holdout Check

Independently audit frozen exports; never modify the running NPT trainer, its inputs or a gate. Reuse `validate-chess-engine` for wider qualification and `grok-pc-safe-run` before any authorized PC workload.

## Establish the evidence boundary

For inferred source IDs or PGN identity comparisons, read
[movetext and inferred IDs](movetext-and-inferred-ids.md). Exact movetext hashes
and authentic row bindings are distinct evidence; missing bindings keep overlap unknown.

For deduplicated row streams, legal continuation searches or inferred source
groups, read [bounded chain evidence](bounded-chain-evidence.md). It separates
observed chains, possible continuations and authenticated original game identity.

Inspect the actual trainer reader, source format, converter and provenance. A `.pos` board record cannot recover missing castling, en passant, clocks or authentic game IDs. Use the original row-aligned FEN sidecar and trustworthy original game identifiers. If IDs are absent or guessed, **game split is UNVERIFIED**; the earlier whole-shard policy does not satisfy this newly requested game-ID proof.

Respect an explicit prohibition on trainer access or imports. Record the blocked
reader check instead of accessing a protected runtime to satisfy this workflow.

Freeze the complete real 013/014 shard hashes and row counts from a trusted crew manifest, not from an arbitrary supplied prefix. Freeze train/source identities, decoder versions and commands. Missing complete holdouts blocks real clearance. A synthetic fixture can test the checker only.

## Independent checks

1. Decode with the authoritative current record reader into a documented normalized audit export; verify counts and round-trip full state. Do not invent NPT/binpack layouts or copy GPL decoding code into Forge. Keep licensing and external adapters explicit.
2. Independently scan training keys against **both complete holdouts**, using a separate audit implementation/index. Report overlap rows and key semantics. Conservative board+side-to-move matching also excludes collisions with different rights/clocks.
3. Independently compare authentic game IDs across train and holdout. Any overlap fails even when positions differ. Never derive IDs from row order or silently prefix identical real IDs by shard to hide leakage.
4. Match each retained row to its original source provenance and compare all six FEN fields, including castling and en-passant. Preserve legal-but-noncapturable EP exactly when the authoritative representation carries it; engine normalization is not proof of source identity.
5. Publish a new audit report with original input/reader hashes, row counts, overlap counts, FEN mismatches, missing-ID count, command and status per check. Keep audit indexes/evidence; no pruning step is authorized.

The bundled `python scripts/audit_exports.py --help` audits **normalized exports only**. Read [the export contract and PowerShell recipe](references.md). Its PASS does not certify an untested native-format adapter or the identity of a real private shard. It requires trusted export hashes/counts, exact source provenance and real IDs; missing IDs yield UNVERIFIED. Files/commands must go through the PC safety workflow.

## Decision

Any position/game overlap or changed full-FEN provenance is FAIL. Missing formats, identities, complete holdouts, authentic IDs or native reader evidence remain UNVERIFIED/BLOCKED. Training readiness requires every applicable check, not just a zero position-overlap number. Do not claim training gain or Elo.

Test a known overlap, different-position same-game leak, stripped castling/EP and missing IDs before trusting a new adapter. Preserve failed examples. Update this skill rather than create another overlapping holdout workflow.
