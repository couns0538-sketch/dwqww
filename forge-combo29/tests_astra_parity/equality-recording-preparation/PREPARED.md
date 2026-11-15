# Equality publication/state recorder

Ready for root to run **after** the corresponding v3 audit receipt exists:

```text
node /workspace/work/parity-equality-recording-preparation/record-equality.mjs speed S1-0003
# Final stage uses: final S2-NNNN
# Read-only proof without publication or state changes:
node /workspace/work/parity-equality-recording-preparation/record-equality.mjs speed S1-0002 --check
```

Preparation ran only syntax and read-only evidence verification. It did not publish, update state, run engines or write Git/source files. Actual S1-0002 verification passed: 33,230 cumulative comparisons, zero differences, one retained operational finding, continuation allowed and completion gate false. Root state was byte-identical before/after the check. Root's manual S1-0002 totals are not added again: each update takes the authoritative cumulative audit values directly. S1-0003 is the next intended root recording action; recording S1-0002 during a different active batch is rejected before publication.

The helper verifies stage/tool/decision/binary/build/manifest pins, receipt/config/audit hashes, prior receipt pins, every referenced summary and every native artifact manifest entry. It checks cumulative receipt totals against the audit and independently applies the pinned v3 policy. A blocked audit is still preserved and recorded as blocked. First-stage gate success requires exactly100,000 selected positions, 99,958 low/42 high, all four original selected-index/FEN digests and final cursors, and `allows(audit)`. Operational1 remains visible. Final score differences can continue under policy, but completion remains pending attribution; no all-pass claim is made.

Raw packages go to `tests_astra_parity/equality-step1/S1-NNNN` or `equality-step2/S2-NNNN`. Missing earlier referenced raw packages are backfilled from their immutable originals. Existing packages are byte/hash verified and never overwritten. Current metadata snapshots go to `equality-step1-records/S1-NNNN` or `equality-step2-records/S2-NNNN`, separately from raw batches. They include stage/receipt/audit/config, original migration/failure evidence, current audit attempts, decision and driver pins, inert tool copies, and this recorder plus the frozen package helper. Existing manual snapshot paths remain untouched.

Publication invokes the pinned `/workspace/work/parity-run/package-evidence.mjs` into a fresh staging destination, verifies full reconstruction, then atomically renames to the final package. Failed staging outputs and exact package command/stdout/stderr logs remain retained. Metadata is text-validated; `.mjs` copies become `.mjs.txt`. Native binaries/objects are not archived. The packer enforces UTF-8/no-NUL text and non-executable publication modes. Each package process has at most90 seconds, reduced by the recorder's420-second command budget.

Only after all publication proofs succeed does the helper atomically replace state. It changes equality rows/totals, validation equality fields, explicit step gates, phase/progress/checkpoint note, and `active=null`. It preserves all other source/commit/push fields. A different active batch is never cleared. If root state changes during publication, the helper refuses replacement; verified packages remain reusable on retry. State-transaction attempts use unique immutable filenames so an interrupted prior update does not block retry. An already-recorded same receipt verifies existing packages and returns without updating state or double-counting.

Validation artifacts are in `VALIDATION.txt` and exact command/stdout/stderr files. A preparation syntax failure caused by a JavaScript replacement-string escape was caught before execution; its source and outputs are retained under `*.syntax-failed.txt` and `first-failure-*`. The correction passed both syntax and the actual read-only S1-0002 check. Publication/state-writing paths have been reviewed but are not live-tested by this preparer; root performs the first authorized recording invocation.
