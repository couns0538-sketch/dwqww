# Job B closeout applier review

Reviewed 2026-11-15 around04:54UTC. The revised applier has no remaining blocker for the planned budget-limited closeout. No actual applier, closure helper, engine or Git operation was executed, and no root state or existing helper was modified during this review.

Reviewed applier: `/workspace/work/parity-run/apply-job-b-closeout.mjs`, SHA256 `9937801340036d327ce495b1eca15b57f825bd34a5d287122ea927d32f5e36f0`. Reviewed source snapshots and hashes are retained alongside this report.

The applier now matches the frozen closure schema: the proposed patch has only `jobBClosure`; removing its four publication fields must reproduce the parsed immutable `CLOSURE.txt` exactly. Evidence/report paths must be the supplied base's files, and both local and published closure/report hashes must agree. The closure's verified root-state hash, current match totals, source commit and declared deadline are checked before publication.

Only `jobBClosure` and `jobBClosurePublication` are assigned in state. Existing match counts, receipts, source, Job A data/deadline and global stop remain unchanged. Context text is separate from frozen closure evidence. Its8291 matching searches and38.103431ms natural exit agree with the retained replay report and state; it keeps the original shutdown cause unresolved and grants no new test credit.

Two initial review issues were corrected before execution: missing exact binding between the patch body and frozen closure JSON, and a non-atomic/non-retryable publication sequence. The revised code uses deterministic context bytes with identical-content reuse, followed by a fresh temporary state file, fsync, a repeated state-hash check and atomic rename. A different existing context is preserved and blocks the write.

Five synthetic tests executed the reviewed source against an isolated in-memory filesystem only:

1. Only closure/publication fields are added; source, counts and an active global stop remain unchanged.
2. A patch altered independently of frozen closure evidence is rejected before writes.
3. A simulated atomic-replacement failure leaves state intact; a fresh retry reuses identical context and succeeds.
4. Different existing context is preserved and blocks application.
5. A published closure hash mismatch blocks the state update.

All five passed. These are synthetic integrity tests, not a real closeout or new experiment evidence. Exact test source/output are adjacent. The current main renderer correctly reports the verified game count and actual native timing, links the frozen closeout/context, and preserves the separate unresolved shutdown finding and successful diagnostic. Its “closed at the declared batch-budget limit” wording describes the planned budget-limited branch of the closure gate.

Operational sequence remains root-owned: finish/audit/record the final eligible batch; wait until the actual target/time gate permits closure with no native work; run the frozen helper; package its four output files under `tests_astra_parity/job-b-closeout-final`; then apply without an intervening root-state update. A stale state hash is a refusal, not permission to change the frozen closure evidence.
