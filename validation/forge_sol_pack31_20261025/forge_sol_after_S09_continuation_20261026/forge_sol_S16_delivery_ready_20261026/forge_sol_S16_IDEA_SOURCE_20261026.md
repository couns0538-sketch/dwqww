# S16 source and reuse record, 2026-10-26

The task specification was read from the root all-jobs inventory's verbatim
S16 entry. QA_sol_jobD_return_20261025.md supplied the five requested fixes and
the real916 diagnostic reference counts. RECORD_FORMAT_v3b_pos_hce_20261025.md,
the holdout note and train_resid_v3b.py established format and input limits.

The same project's unchanged Job D filter and tests are included under their
original names and exact hashes as explicit dependencies. The new version
reuses their Record, Reader, writer, text parser, identity and selection helpers;
it does not implement another binary/text record parser. Its orchestration is
derived from that original same-project filter and extended for this task.
No source, constants or tables from another chess engine were used.

An independent read-only review confirmed that boundary rates cannot prove
absence of synchronized interleaving. It measured the supplied real916 text's
11 boundaries, 12 inferred groups and at most 2 boundaries in any 100 rows.
Production therefore requires owner-authoritative ID maps instead of treating
the diagnostic anomaly tripwire or inferred grouping as authentic game proof.

The original dataset and code hashes, exact diagnostic scope, tested paths and
unavailable real inputs are recorded in the delivery receipt and reports.
