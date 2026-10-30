# Converter policy refinement — 2026-10-30

Starting commit: `2bf555965d63c3f8b0ec8e4c03cd8ae680ebd1e0`.
Code checkpoint: `663b955` on the same branch; follow-up adds evidence/docs only.

- Conversion, resume and ordinary verification retain all indexes.
- `verify --prune-indexes` takes the output lock, verifies and only then removes
  marked owned indexes. Legacy/unowned data remains untouched.
- The separate holdout audit also retains its database by default. Explicit
  `--prune-indexes` cleans its owned database only after validated completion;
  identity failures retain it, with truthful path/size/prune metadata.
- Both conversion and verification require `--accept-gpl3` whenever an adapter
  is selected. A shared helper also checks the dependency fetch destination.
  Actual Git repositories, worktrees, bare repositories and aliases into them
  are rejected; empty managed-filesystem `.git` placeholders are not repos.
- The path check resolves the original spelling before normalizing `..`.
  Independent review reproduced and then verified repair of an actual adapter
  execution through `external/link/../adapter` into a repository.

Validation: **110/110 data2 tests passed** with the external native adapter
explicitly enabled. Independent runs include the original red cases and source
hashes. Native verification of 100 original shard003 rows retained its16,384-byte
index through conversion and ordinary verify; missing acknowledgement refused;
explicit acknowledged verification plus pruning removed exactly16,384bytes.
The evidence harness initially parsed JSONL progress as one JSON document; this
harness error is retained, and the completed conversion was not repeated.

Original earlier QA logs/manifests remain snapshots of their original commits.
This folder's manifest pins this refinement. No Windows, GPU or grok-pc work
ran. Private full013/014 clearance remains UNVERIFIED and blocks training.
No engine source, accepted network, speed or Elo result changed.

IDEA_SOURCE: user's explicit opt-in policies and original source/path regressions.
