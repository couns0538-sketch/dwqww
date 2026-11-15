# Read-only sanitizer time accounting

Run `node /workspace/work/parity-soak-time-review/review.mjs --as-of 2026-11-15T02:30:00.000Z` for JSON, or add `--markdown` for a concise table. Use the actual snapshot time, not a future endpoint. The helper writes only stdout; redirection/publication is the caller's choice.

The helper discovers current and future `softnodes*-batches` directories under `/workspace/work/parity-run`. Add `--final-dir /absolute/other-protocol-directory` if a future protocol uses a different name. It accepts root-level arrays named `*PairedSoftnodesRows` as recorded final evidence. It reports an unrecorded successful command as unreviewed rather than inventing a passing audit. Preliminary Step1 command metadata is reported separately.

Exact UTC timestamps with milliseconds and a valid end no later than the report time are required. Missing/reversed/future intervals are excluded with issues; incomplete starts remain visible without credited duration. Overlap is counted once in the union. Per-status unions may overlap each other and must not be added. Batch-duration sums include concurrent batches separately and are not CPU time. Elapsed time and gaps do not count as testing. The current output is a snapshot, not an assertion that all final protocols have run.

No engine, source, Git or root state changes are performed. `test.mjs` checks UTC rejection, overlapping intervals, gaps and missing-end exclusion using synthetic values only.
