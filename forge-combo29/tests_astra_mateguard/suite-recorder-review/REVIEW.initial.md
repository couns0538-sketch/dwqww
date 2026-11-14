# Lean independent suite-tool review

Read-only review of run-suite-batch.mjs, record-suite-batch.mjs, execute-suite-step.mjs, both unchanged plans, and existing build metadata. No tool edits, engine/test execution, state writes, or Git operations. Reviewed source snapshots are retained as inert .mjs.txt files. Inspection command/output and exact inspector are retained alongside this report.

## Material findings

1. **Incomplete attempts inflate completed totals.** record-suite-batch.mjs:42 uses `completed: all.length` and `remaining: 59-all.length`, including timeout/signal rows. One timed-out attempt produces completed=1, incomplete=1, remaining=58; 59 timed-out attempts would report completed=59 and remaining=0. Preserve `attempted`, define `completed` using `!incomplete`, and distinguish unattempted from incomplete outstanding tests. Tests need not be automatically repeated.

2. **Recorded plan/input hashes are not enforced on publication.** record-suite-batch.mjs:15 checks only argv/cwd, ignoring the executor's planSha256, env, stdinFile/inputSha256 and other planned fields such as expectedPerftNodes. Six tests per mode consume stdin, and ASAN settings are carried in env. Thus changed input bytes or sanitizer env between execution and recording can still be published as matching an unchanged plan. Verify the whole plan hash/item and stdin hash; verify prior stored metadata pins when recomputing cumulative totals. Existing output byte hashes are checked correctly.

3. **Interrupted controller recovery can strand finished evidence.** run-suite-batch.mjs:15 skips every metadata file with `ended`, regardless of whether it was recorded in state. record-suite-batch.mjs:6 rejects a controller batch without its final `ended`. If the controller is interrupted after one or more executor results are finalized but before its batch footer is written, a fresh controller label skips those results, while the original batch cannot be recorded directly. Preserve/recover finished entries from that batch with an explicit interrupted-batch state, or stop on finalized-but-unrecorded entries until recovery. All raw files remain retained, so this is an accounting/recovery problem rather than deleted evidence.

## Confirmed behavior

- 50 builds per mode (100 total) have final passed metadata, exit 0, no incomplete flag, and matching stdout/stderr hashes.
- Each mode has 59 unique runtime IDs and 177 unique output basenames, avoiding flattened package-name collisions.
- All 118 runtime entries use inner `timeout -k 2 440` and outerTimeoutMs=450000. No command starts after the controller's first 15 seconds; nominal bound is 15+450+3=468 seconds, below 480 seconds with 12 seconds available for overhead. This is a code/plan bound review, not an observed runtime guarantee.
- Controller gates on equalityTotals.targetMet only, so a fully covered equality corpus with differences/faults does not block unrelated test execution.
- Failed native exits, sanitizer findings, output review markers, and incomplete flags are retained. Marker-bearing exit-0 rows are excluded from aggregate passed counts and create immutable fault records.
- Fault files verify exact byte identity; publication uses fresh staging, package reconstruction/hash checks, atomic directory rename, and verification of an existing final package before reuse.

## Additional bounded observations

- record-suite-batch.mjs:46 writes state.json directly rather than through a temporary file and rename. An interruption during that write can truncate shared state; matching the equality recorder's atomic final state update would close that small recovery gap.
- The recorder preserves executor-derived diagnostics rather than independently rescanning raw output. This review did not expand sanitizer-pattern coverage or run failure fixtures, consistent with the requested lean scope.
