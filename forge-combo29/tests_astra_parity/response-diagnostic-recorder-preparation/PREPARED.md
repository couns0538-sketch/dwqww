# Root-only diagnostic recording tools

These VM helpers add no engine changes, perform no Git operation and never update root experiment state. Preparation ran only synthetic JavaScript checks. The existing native controllers, auditors, transport and declarations remain frozen and unchanged.

## Sequential release runner

```text
node /workspace/work/parity-diagnostic-recording-0018-preparation/run-release.mjs R-001 4 --execute-authorized
```

Replace the first ID and count as needed: count is 1–4, IDs must be consecutive and not previously started. The runner logs each controller with `release-diag-r001` and its audit with `release-diag-audit-r001`, advancing the suffix for every ID. The existing controller enforces global row order, native exclusivity, immutable runtime outputs, source/build/tool pins and the original 60-second search deadline. Each search gets its own fresh process. Within each case and repeat, the order is T1 depth9, T1 depth12, T2 depth9, T2 depth12. No depth12 search inherits a warm hash from depth9.

Each controller wrapper is capped at90 seconds and audit at12 seconds; the total runner budget is425 seconds with a105-second guard before starting another row. The underlying native process has a75-second command bound and250ms shutdown allowance. These are maximum harness allowances, not completed measurements. The main agent must keep other native workloads out while this runner executes. Use no competing engine commands.

A well-formed retained response timeout can proceed to the next diagnostic under Fable0018. It receives zero completion and zero soak credit. The runner stops on missing or malformed evidence, non-timeout failure, sanitizer report, illegal returned move, abnormal shutdown or unexpected process outcome. Audit success alone does not mean search completion. Raw completed-depth lines before `quit` remain available even when the target depth times out.

## Immutable report snapshot

After root has finalized the desired rows and their audits:

```text
node /workspace/work/parity-diagnostic-recording-0018-preparation/record.mjs snapshot-01
```

Use a new lowercase letters/digits/hyphens ID for every snapshot. The recorder consumes all finalized saved release audits and both TSan audits. Expected TSan labels are `tsan-diagnostic-audit-4` and `tsan-diagnostic-audit-10`; controller labels remain `tsan-diagnostic-4` and `tsan-diagnostic-10`.

The recorder re-executes only the read-only frozen auditors and requires their actual outputs and exits to reproduce. It verifies source, binary, tool and saved-output hashes, then packages existing raw text using the existing evidence packer. It never launches engines. Missing native rows remain pending; a finalized row without a saved audit is packaged but receives no inferred completion. An audit that validly describes a timeout is classified separately from a completed search. Diagnostic reports, abnormal shutdowns and unexpected outcomes stay visible as blocked findings.

Snapshots are written under `/workspace/work/parity-run/response-diagnostic-recording-0018/<ID>` and text packages under `forge-combo29/tests_astra_parity/response-diagnostic-records-0018/<ID>`. Raw case packages are under `forge-combo29/tests_astra_parity/response-diagnostics-0018/`. Existing raw packages are verified and reused; no output is overwritten. The final snapshot's packaging command is logged outside its immutable source directory, so the package manifest remains valid. The main agent owns any commit or push. The recorder has a420-second deadline; package operations are individually capped at60 seconds and read-only audits at12 seconds.

Outputs include a concise report, complete parsed result records, every finished pre-quit depth in a text CSV, raw evidence package identities, saved and repeated audits, and frozen source excerpts. The source explains that multi-worker bare-king mode disables several pruning/reduction paths, but does not itself prove the cause of any measured difference. The tool makes only a descriptive workload observation if both five-repeat same-depth groups complete and every T2 node count exceeds every T1 count. It does not infer a node ratio from incomplete groups, claim speed or strength, or classify the original event as sanitizer overhead without evidence.

All42 diagnostic searches have zero soak credit. Replaying the exact move history reconstructs board/repetition history, not the original warm TT or internal search history. Release depths9 and12 are cold, separate-process comparisons. Original failed soak batches retain their original evidence and zero credit. No warm-state timeout recurrence is established by these diagnostics.

## Verification limits

`test.mjs` tests18 synthetic classification/accounting cases, including natural completion, retained timeout, postconditions that block continuation, incomplete five-repeat comparisons and an empty snapshot. A timeout permits only the expected `bestmove_count` parser error; other parser errors stop continuation. A nonempty exact score whose legal-range check failed also blocks continuation. JavaScript syntax is checked separately. The new runner and recorder have not been executed against native diagnostics during preparation: root owns their first use. No actual missing diagnostic counts are invented.
