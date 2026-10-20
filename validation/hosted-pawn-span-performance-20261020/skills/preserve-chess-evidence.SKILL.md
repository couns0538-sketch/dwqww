---
name: preserve-chess-evidence
description: Preserve and audit chess-engine experiment evidence. Use for Forge, GrokChess, or other UCI engine checkpoints, raw PGNs/logs, source and binary hashes, interrupted fastchess matches, paired-game ledgers, resume planning, or handoff archives. Do not treat this helper as an engine validator, automatic match runner, or Elo estimator.
---

# Preserve Chess Evidence

Preserve exact inputs, executed outputs, and unfinished work before drawing conclusions. Use `validate-chess-engine` for correctness and strength decisions, and `coordinate-chess-pipeline` for shared-stage handoffs when available.

## Freeze identities first

Read [the evidence contract](references/evidence-contract.md). Record source commit/tree, binary and network SHA-256, compiler/runtime, commands, openings, options, clocks, resources, adjudication, and SPRT hypotheses before starting an experiment. Fingerprint the complete immutable protocol; changed builds, settings, openings, or hypotheses require a separate experiment.

## Preserve a checkpoint

Stop only processes owned by this run, or use the runner's supported checkpoint operation. Close writers before snapshotting. Keep original stdout/stderr, PGNs, errors, incomplete games, and runner state. Keep corrected harness attempts distinct from their originals. Do not overwrite a previous checkpoint or recursively duplicate old archives when verified durable references suffice.

Run the bundled helper through Python 3.10 or newer, resolving script paths relative to this skill directory:

```text
python scripts/evidence.py snapshot /path/to/frozen-evidence /path/to/manifest-new.json
python scripts/evidence.py verify /path/to/frozen-evidence /path/to/manifest-new.json
python scripts/evidence.py protocol-hash /path/to/protocol.json
python scripts/evidence.py audit-ledger /path/to/ledger.json
```

Place the manifest outside the evidence root. Snapshot creation refuses overwrite; verification rejects altered, missing, extra, duplicate, or unsafe-path entries and symlinks. Treat failures as evidence problems to investigate, not a reason to erase original files. The helper reads local files and only creates a new manifest; it does not contact services or run engines.

## Reconcile matches before resume

Read [the ledger contract](references/ledger-contract.md). Use immutable experiment/pair/leg identities, not similarity of PGN moves. Count completed games and complete color-swapped pairs separately. Preserve aborted/in-progress slots, failures, and all raw evidence.

A consistent ledger is not resume authorization. Inspect `resume_status`, verify the actual runner checkpoint and PGNs/logs, and establish exclusive experiment ownership. Check the installed fastchess version's supported continuation behavior. A partial pair never permits replaying its completed leg. If continuation cannot be proved safe, report BLOCKED and retain the partial match; do not fabricate a resume command or silently restart a failed experiment.

## Verify the handoff

Verify manifests again after copying or extracting evidence, then verify the durable upload and report its actual location. A hash proves byte identity relative to a manifest, not source authenticity, PGN legality, or SPRT acceptance. Do not call a local package installed, published, or shared until that action is independently confirmed.

Run `python -B -m unittest discover -s tests -v` after modifying the helper. Read [validation scope](references/validation-scope.md) before describing what its checks prove.
