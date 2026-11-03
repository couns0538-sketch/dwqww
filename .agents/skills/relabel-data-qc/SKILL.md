---
name: relabel-data-qc
description: Use when auditing immutable chess relabel outputs for mate-score outliers, score/result distributions, duplicate positions, or comparisons between old and new label cohorts.
---

# Relabel data QC

Use the task's explicit storage, CPU and input permissions. This package does not
authorize relabel searches, training, GPU use, engine changes or production mutation.
The R13 example tools are constrained to D:/a13; do not silently reuse that root
or its fixed input identities for another task.

## Establish the cohort

- Freeze completion metadata and published shard manifests, then verify actual
  bytes, ranges, final assembly and aligned source rows. A status counter alone
  is insufficient; missing historical shards are a failed completeness check.
- Determine publication semantics from the producer. R13 sealed shards retain
  `.part`/`.pending` files; their existence alone does not mean unfinished work.
- Keep repeat proof runs out of population counts. Compare their final label
  bytes for reproducibility and state precisely what was compared.
- A new cohort's `old_score_stm` is its own aligned source score. It is not a
  join key to a separate historical relabel cohort.

## Preserve semantics

- Identify score orientation and exact mate threshold from the source contract.
  R13/R14 use STM centipawns and inclusive `abs(score) >= 30000`.
- Flag original rows in a separate file with immutable source-row identity.
  Never overwrite a source, silently clip before profiling, or interpret a
  missing outcome as a draw.
- Report STM and White views explicitly. In FPOS v1, bit0 is STM and bits1..2
  encode White result; neither file order nor FEN turn changes that orientation.
- Distinguish exact six-field-FEN duplicate rates from board-only rates.
  Lost castling/EP/clocks change both the searched position and duplicate keys.
  Attaching an original FEN later cannot repair a label searched on lost state.
- Describe material phase as a proxy with explicit weights/bins. Do not call it
  authentic game phase or infer game boundaries from it.

## Evidence

The R13 examples are [the auditor](../../../tools/p5_qc.py),
[the parser](../../../tools/qc_core.py), [the containment guard](../../../tools/run_policy.py)
and [the regression fixtures](../../../tests/test_p5_audit.py) in this checkout. Run through the reviewed
launcher and retain input hashes, failed attempts, reports and full test logs.
Inspect the actual source/manifest schema before adapting these examples.

Rehash complete consumed inputs before publishing receipts; timestamp and size
checks alone miss same-size replacements with restored timestamps. Bind final
artifacts to successful process receipts and the source revision that produced
them. Preserve failed or superseded runs instead of overwriting their evidence.

Use `npt-data-holdout-check` for independent game/holdout qualification. Inferred
IDs, matching row counts and zero positional overlap do not prove game separation.
Keep QC integrity, provenance, checksum integrity, tests and strength claims separate.
