# Diagnostic recording-integrity finding

Ten cold replay result summaries and console entries record normal completion.
Nine raw transcripts match their original completion hashes. Exactly one of
twenty recorded trial-artifact digests differs from the file now available:

- File: `diagnostics/timeout-cold-replay/trial-06-candidate-events.jsonl`.
- Original recorded SHA-256: `f54678999550fcc9bd286a62954d790ec20c3900d0663970891dd5ac5566774a`.
- Available SHA-256: `036a75d3630b1781afd94db6f30dc0ed04f2f4ae6b18eedac87ed9ebeb81b2bb`.
- Available length: 3,442 bytes and 25 lines; it ends during startup, before search.

The separate sixth result file matches its original digest, and the console
entry is present. Both record e7e4, depth 11, 98,549 nodes, 141.414 ms, normal exit
and no explicit stop. The missing raw search events cannot independently
corroborate that one result.

The accessible expected workspace and temporary copies contain the same
truncation. No authentic complete copy was recovered, and the cause is unknown.
No synthetic transcript or rerun was substituted. The original recorded digest,
available bytes and exact prepared archive remain unchanged.

Archive/member hashes authenticate the bytes packaged. They do not prove
original-recording completeness. Future packaging must compare raw files with
pre-existing execution digests and disclose any mismatch.
