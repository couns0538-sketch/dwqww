# Lean independent suite-tool review — corrections reviewed

Status: the three reported material issues and the direct-state-write observation are corrected in the current recorder. This follow-up was source inspection only; no synthetic fixtures, native execution, recorder execution, state writes, or engine/tool edits were performed by the reviewer.

## Corrected findings

1. **Incomplete counting corrected.** The recorder now reports attempted, completed (`!incomplete`), incomplete, notAttempted, and remaining separately. An incomplete row remains outstanding instead of inflating completed coverage. No automatic rerun was introduced.

2. **Provenance checks added.** Publication now checks recorded planSha256 against the current plan hash; compares env, stdinFile, expectedPerftNodes, argv and cwd; checks inputSha256 against the actual stdin bytes; verifies output hashes; and verifies every prior stored metadata pin before rebuilding cumulative totals.

3. **Explicit finalized-result recovery added.** An unfinished controller batch requires `--recover-finalized`. Recovery scans `/proc` and rejects a matching live controller; every listed entry must have final metadata with valid identity, planned settings and output hashes. The original batch log is retained byte-for-byte and a separate immutable controller-recovery.txt records its hash and finalized metadata pins. The recorder verifies that the controller log did not change before updating state. Unfinished executor metadata remains blocked for explicit review, which is appropriate for this bounded recovery path.

4. **Atomic state publication added.** The final state is written through the shared immutable writer to a fresh temporary path, then renamed over state.json after the unchanged-state check.

## Previously confirmed behavior

- 50 builds per mode (100 total) have final passed metadata, exit 0, no incomplete flag, and matching stdout/stderr hashes.
- Each mode has 59 unique runtime IDs and 177 unique output basenames, avoiding flattened package-name collisions.
- All 118 runtime entries use inner `timeout -k 2 440` and outerTimeoutMs=450000. No command starts after the controller's first 15 seconds; nominal bound is 15+450+3=468 seconds, below 480 seconds with 12 seconds available for overhead. This is a code/plan bound review, not an observed runtime guarantee.
- Controller gates on equalityTotals.targetMet only, so a fully covered equality corpus with differences/faults does not block unrelated test execution.
- Failed native exits, sanitizer findings, output review markers, and incomplete flags are retained. Marker-bearing exit-0 rows are excluded from aggregate passed counts and create immutable fault records.
- Fault files verify exact byte identity; publication uses fresh staging, package reconstruction/hash checks, atomic directory rename, and verification of an existing final package before reuse.


## Scope and retained evidence

The stage gate still requires only equality corpus targetMet. Failure markers, sanitizer findings, incomplete attempts, immutable faults, and verified staged packages remain preserved. No additional material defect was identified within the requested correction review.

The original report and original recorder snapshot are preserved as REVIEW.initial.md and record-suite-batch.initial.mjs.txt. The current inert recorder snapshot is record-suite-batch.mjs.txt; correction-review.json.txt records its SHA256 and review time. Existing inspection.stdout.txt describes the initial revision and its hashes, so it should not be read as execution validation of the corrected recorder. The earlier counting-formula example is historical. No runtime or synthetic validation is claimed for this follow-up.

The recorder continues to preserve executor-derived diagnostics rather than independently rescanning raw output. Pattern coverage and broader failure recovery were outside this follow-up scope.
