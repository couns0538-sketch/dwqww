Synthetic holdout-clearance validation, 2026-10-30 UTC

The focused command is recorded in focused-tests.txt and run-status.txt. All fixture FPOS files are tiny generated examples; no private real013/real014 file was available or examined. Real-data zero-overlap status is UNVERIFIED. These tests do not authorize training.

review-regressions-red.txt records four reproduced failures before the review fixes: destination writes inside sealed output, insufficient index preflight, tool-source mutation, and temporary holdout mutation/restoration. focused-tests.txt verifies the fixes plus overlap counts, zero overlap, empty-output blocking, full-shard hash/count binding, sealed corruption, source/path changes, free-space guards, cleanup and CLI exit behavior. SHA256SUMS.txt pins the audited sources and test file.

The production command requires explicit real013 and real014 FPOS paths, independently trusted SHA-256 values and full-shard row counts, a new report path outside the sealed output, and an existing scratch directory. Default reserve is 20480 MiB. PASS/exit 0 requires a nonempty sealed output and zero overlap; FAIL/exit 1 means overlap; BLOCKED or BLOCKED_EMPTY_OUTPUT/exit 2 prevents clearance. JSON, JSONL log and claim evidence remain; only the owned disposable index is removed. Game-ID clearance is never inferred.
