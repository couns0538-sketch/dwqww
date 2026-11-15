# Strict-depth v2 paired recorder

This is a new immutable protocol. Original harness, audit, batch0, recorder, raw evidence, failed acceptance and historical stop flags remain untouched. The source tree and sanitizer binaries are unchanged. Fable's explicit decision is commit55ddf61a754ceffc4f940b847ad97143148d0434, text SHA2565e2d573b7e553ec49e84918bd1dfd6a28ccfd2ca7236b6834c3b041965945e2f. It adds a completed exact depth64 iteration to item4's exceptions, requests no targeted repeats and authorizes remaining work.

New native/controller/auditor: `/workspace/work/parity-softnodes-depth64-v2-preparation/PREPARED.md`. It has12 fresh group labels and seeds202611155201..212, including a fresh group0. No old result becomes a new accepted result.

Root commands after each finalized new batch:

```text
node /workspace/work/parity-run/command.mjs depth64-v2-audit-0 node /workspace/work/parity-softnodes-depth64-v2-preparation/audit.mjs 0
sha256sum /workspace/work/parity-run/logs/depth64-v2-audit-0.stdout.txt
node /workspace/work/parity-softnodes-depth64-v2-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/depth64-v2-audit-0.stdout.txt ACTUAL_SHA256 --check
node /workspace/work/parity-run/command.mjs depth64-v2-record-0 node /workspace/work/parity-softnodes-depth64-v2-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/depth64-v2-audit-0.stdout.txt ACTUAL_SHA256
```

Use actual hashes and fresh command labels. Recording reruns only the read-only auditor. It never launches an engine or Git. Root state must contain the explicit `softnodesResolution` decision already written by root at01:06:43UTC, with matching commit/SHA and `oldAuditAndFaultUnchanged=true`. The recorder does not silently clear a historical stop. It verifies the original pinned row0, original raw/audit hashes, immutable proof/packages and original retained count1 before every publication.

New state: `depth64v2PairedSoftnodesRows`, `depth64v2PairedSoftnodes`, `validation.depth64v2PairedSoftnodes`, `soakTotals.finalTree.depth64v2PairedSoftnodes`. Original `finalPairedSoftnodesRows`, `finalPairedSoftnodes`, `validation.finalPairedSoftnodes` and `soakTotals.finalTree.pairedSoftnodes` remain unchanged. Thus both protocols can have index0 without collision. Top-level finalTree games/searches count only clean new-protocol coverage; its faults include the separately retained original contract failure plus any new finding batches. The original contract failure is resolved by the explicit decision, not reclassified as an accepted run or erased.

New raw packages: `tests_astra_parity/final-paired-softnodes-depth64-v2/LABEL/`.
New metadata packages: `tests_astra_parity/final-paired-softnodes-depth64-v2-records/LABEL/`.
VM metadata: `/workspace/work/parity-run/softnodes-depth64-v2-recording/LABEL/`.

All original recorder integrity checks remain: fixed source/binary/object/oracle/build/tool/declaration/raw pins, reproduced auditor output, immutable text package reconstruction, duplicate no-op/conflict rejection and atomic state replacement guarded by its starting SHA256. Preliminary observations and source/push state are preserved. `credit`, `completedPairObservations`, and `observedIncludingPartialPair` remain separate. Soft mean X is summed X divided by summed count. A new item3/item4 violation sets the current global stop true; this recorder never clears one. Audit-unavailable or incomplete results credit zero and require review. Missing command.txt after a controller interruption still requires explicit manual recovery, never an invented exit.

Verification actually run:12 synthetic accounting cases, including old failed index0 preservation alongside new index0, plus JavaScript syntax checks. The new native harness independently passed29 parser cases: exact63 rejection, exact64 acceptance, bounded64 not replacing exact63, malformed-depth rejection and last-exact-line replacement. No engine was run during preparation. Independent review's two extra original-evidence checks were added before freeze. First live new-protocol declaration/batch/publication remains root's responsibility.

The prior depth64 protocol was declared but never ran an engine. Its declaration remains pinned at6ea2f582ab117ba9e9dd5122a70406cd49319f502759d758a811e057c9d34e04; this recorder verifies that namespace still contains only declaration.txt. Its source/parser tests and the separately recorded synthetic64junk/duplicate-depth findings remain intact. V2 validates the entire decimal depth token, rejects negative/out-of-range values and invalidates duplicate depth fields in one info line. The six additional tests explicitly cover those cases, including a malformed last exact line replacing a prior valid64 line. No real output was malformed; original0015 remains the valid exact64 contract failure resolved by Fable. No old protocol counts are accepted through v2.
