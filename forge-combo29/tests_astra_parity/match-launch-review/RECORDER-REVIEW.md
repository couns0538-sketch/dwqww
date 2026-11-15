# Bounded recorder review

Reviewed at 2026-11-15T01:38:58Z. No engine, Git or root-state writes. The reviewed file hashes and six independent fixture/state checks are in `RECORDER-CHECKS.txt`.

No blocking accounting or publication issue was found against the actual prepared controller schema. The recorder checks declaration/source/tool pins, receipt and raw-manifest contents, the reconstructed plan and preceding receipt chain, exact command/process evidence, and an independent replay of the retained audit. It copies PGN, trace, event, config and command text through the existing chunk-and-hash packager, whose allowlist includes their extensions. It checks root-state bytes before replacement and retains prior state fields.

The read-only accounting check independently confirmed 400 completed games receive credit; the 314 finished games in the incomplete fixture receive zero credit; combined observations remain 714 while credited games remain 400. A previously set global stop is preserved on a later passing record, unrelated historical fields are preserved, and the recorder clears its own active batch.

One evidence improvement was reported to the author: the reviewed version saved the inner re-audit stdout/stderr only after assertions, so a failed or mismatching re-audit could lose that inner raw output. It should log that subprocess before asserting in mutation mode. The original full native artifacts would remain preserved regardless. The author owns any subsequent change and final hashes.

This review does not claim that the full recorder has processed a live Job B declaration or batch. Root must inspect its first live run, especially declaration snapshots, raw-package reconstruction and the resulting state transaction.

Follow-up: inspected the author's exact delta at record SHA256 `785a1a90039b543cdfb6bc59a61e10c8f6a4d060b3921cd87c19738f4a511e75`. The failed-re-audit logging gap is resolved: mutation mode saves stdout, stderr and command metadata before assertions; read-only check failures print the full inner output to the caller. Accounting is unchanged. The frozen external pins contain text helpers only, so their metadata snapshot does not copy a binary. No remaining blocking issue was found in this bounded review.
