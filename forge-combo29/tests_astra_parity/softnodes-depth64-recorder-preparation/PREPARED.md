# Amended depth64 paired recorder

This is a new immutable protocol. Original harness, audit, batch0, recorder, raw evidence, failed acceptance and historical stop flags remain untouched. The source tree and sanitizer binaries are unchanged. Fable's explicit decision is commit55ddf61a754ceffc4f940b847ad97143148d0434, text SHA2565e2d573b7e553ec49e84918bd1dfd6a28ccfd2ca7236b6834c3b041965945e2f. It adds a completed exact depth64 iteration to item4's exceptions, requests no targeted repeats and authorizes remaining work.

New native/controller/auditor: `/workspace/work/parity-softnodes-depth64-preparation/PREPARED.md`. It has12 fresh group labels and seeds202611155101..112, including a fresh group0. No old result becomes a new accepted result.

Root commands after each finalized new batch:

```text
node /workspace/work/parity-run/command.mjs depth64-audit-0 node /workspace/work/parity-softnodes-depth64-preparation/audit.mjs 0
sha256sum /workspace/work/parity-run/logs/depth64-audit-0.stdout.txt
node /workspace/work/parity-softnodes-depth64-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/depth64-audit-0.stdout.txt ACTUAL_SHA256 --check
node /workspace/work/parity-run/command.mjs depth64-record-0 node /workspace/work/parity-softnodes-depth64-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/depth64-audit-0.stdout.txt ACTUAL_SHA256
```

Use actual hashes and fresh command labels. Recording reruns only the read-only auditor. It never launches an engine or Git. Root state must contain the explicit `softnodesResolution` decision already written by root at01:06:43UTC, with matching commit/SHA and `oldAuditAndFaultUnchanged=true`. The recorder does not silently clear a historical stop. It verifies the original pinned row0, original raw/audit hashes, immutable proof/packages and original retained count1 before every publication.

New state: `depth64PairedSoftnodesRows`, `depth64PairedSoftnodes`, `validation.depth64PairedSoftnodes`, `soakTotals.finalTree.depth64PairedSoftnodes`. Original `finalPairedSoftnodesRows`, `finalPairedSoftnodes`, `validation.finalPairedSoftnodes` and `soakTotals.finalTree.pairedSoftnodes` remain unchanged. Thus both protocols can have index0 without collision. Top-level finalTree games/searches count only clean new-protocol coverage; its faults include the separately retained original contract failure plus any new finding batches. The original contract failure is resolved by the explicit decision, not reclassified as an accepted run or erased.

New raw packages: `tests_astra_parity/final-paired-softnodes-depth64/LABEL/`.
New metadata packages: `tests_astra_parity/final-paired-softnodes-depth64-records/LABEL/`.
VM metadata: `/workspace/work/parity-run/softnodes-depth64-recording/LABEL/`.

All original recorder integrity checks remain: fixed source/binary/object/oracle/build/tool/declaration/raw pins, reproduced auditor output, immutable text package reconstruction, duplicate no-op/conflict rejection and atomic state replacement guarded by its starting SHA256. Preliminary observations and source/push state are preserved. `credit`, `completedPairObservations`, and `observedIncludingPartialPair` remain separate. Soft mean X is summed X divided by summed count. A new item3/item4 violation sets the current global stop true; this recorder never clears one. Audit-unavailable or incomplete results credit zero and require review. Missing command.txt after a controller interruption still requires explicit manual recovery, never an invented exit.

Verification actually run:12 synthetic accounting cases, including old failed index0 preservation alongside new index0, plus JavaScript syntax checks. The new native harness independently passed23 parser cases: exact63 rejection, exact64 acceptance, bounded64 not replacing exact63, malformed-depth rejection and last-exact-line replacement. No engine was run during preparation. Independent review's two extra original-evidence checks were added before freeze. First live new-protocol declaration/batch/publication remains root's responsibility.
