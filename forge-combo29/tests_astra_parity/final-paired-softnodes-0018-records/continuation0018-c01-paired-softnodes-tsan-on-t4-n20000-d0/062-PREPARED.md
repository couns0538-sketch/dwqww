# Continuation0018 immutable recorder

Prepared in the cloud. This preparation ran only syntax checks and 25 synthetic accounting cases: no engines, Git, or root-state writes. Full commands and output are retained in VALIDATION.txt.

Usage, after the root controller finishes and the frozen auditor produces a retained result:

`node /workspace/work/parity-soak-0018-recording-preparation/record.mjs INDEX AUDIT_FILE AUDIT_SHA256 --check`

Then the same command without --check publishes immutable text evidence and atomically records the result. The root must serialize recording and other state mutations. INDEX is 0 through 71. AUDIT_FILE must be under /workspace/work/parity-run. The recorder reruns only the frozen read-only auditor, never an engine or Git.

The decision is Fable0018 at fe59dc3ab072480f7360f0b356ff01a900d2ab35, SHA256 a85053e51b66fb82cbc2033acf27d5e4cb83f22d64938c430870a15eeaf7fe3b. Explicit root authorization must be present as continuation0018Resolution with matching commit and sha256 and oldAuditsUnchanged=true. No tool clears stop flags. Controller, auditor, plan, decision inputs, native, source, engine binary/object/flags, prior proofs and all current raw files are hash-verified.

New rows and aggregates use continuationPairedSoftnodesRows and continuationPairedSoftnodes, plus validation.continuationPairedSoftnodes and soakTotals.finalTree.continuationPairedSoftnodes. All original, unused depth64/v2, extended, SMP and preliminary namespaces remain unchanged. Historical original failure count 1, extended failure count 2 and SMP failure count 2 remain counted. The extended clean 108 games/15514 searches and SMP clean 148 games/21436 searches remain separate historical coverage; they are not added to new continuation totals. Top-level finalTree games/searches count only accepted-clean continuation games/searches; finalTree faults include historical and new finding batches.

A clean complete batch receives accepted credit once. Faulted finalized batches retain completed-pair observations separately and receive zero accepted-clean credit. Interrupted batches receive zero accepted-clean credit. Every raw diagnostic/fault remains retained, including incomplete item3/4 failures. An item3/4 fault blocks further engine work. Repeated group batches do not increase unique matrix coverage: inventory72, distinct required groups12. Raw pair counts, soft X sum/count/mean/caps, SMP exception observations and shutdown timings remain separate from accepted-clean accounting.

The new protocol is softnodes-0018-continuation. Runtime batches are /workspace/work/parity-run/softnodes-0018-batches. Text evidence is published only to forge-combo29/tests_astra_parity/final-paired-softnodes-0018 and final-paired-softnodes-0018-records. Old evidence and prior unused declarations are verified and never rewritten. The native driver is unchanged; TSan ordinary-half limits are changed by controller metadata only to nodes20000/depth0.

No real continuation batch has been recorded or validated by this preparation. Synthetic tests do not count as engine coverage. A native/runtime fault requires recording and review; this helper does not fix it.
