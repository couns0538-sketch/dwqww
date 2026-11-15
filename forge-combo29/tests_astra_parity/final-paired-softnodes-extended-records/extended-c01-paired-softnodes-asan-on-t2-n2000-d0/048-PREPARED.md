# Extended paired sanitizer recorder

Root invokes after each actual finalized batch:

```text
node /workspace/work/parity-run/command.mjs extended-audit-INDEX node /workspace/work/parity-softnodes-extended-preparation/audit.mjs INDEX
sha256sum /workspace/work/parity-run/logs/extended-audit-INDEX.stdout.txt
node /workspace/work/parity-softnodes-extended-recording-preparation/record.mjs INDEX /workspace/work/parity-run/logs/extended-audit-INDEX.stdout.txt ACTUAL_SHA256 --check
node /workspace/work/parity-run/command.mjs extended-record-INDEX node /workspace/work/parity-softnodes-extended-recording-preparation/record.mjs INDEX /workspace/work/parity-run/logs/extended-audit-INDEX.stdout.txt ACTUAL_SHA256
```

Index is0..71. Recording reruns only the read-only auditor, validates frozen tools/declarations/source/binaries/objects/oracle/raw pins, verifies the original failed batch and historical stop unchanged, publishes immutable text evidence and atomically updates root state. Duplicate identical index is a no-op; a conflicting identity is rejected. Serial recorder invocations are required. Existing command.txt is required; incomplete evidence cannot invent an exit or count.

New namespaces: extendedPairedSoftnodesRows, extendedPairedSoftnodes, validation.extendedPairedSoftnodes and soakTotals.finalTree.extendedPairedSoftnodes. All prior namespaces and preliminary counts remain intact. The original failed batch remains separately retained and is never credited. Top finalTree games/searches use only clean new coverage; faults include new finding batches plus the one retained original contract failure. Item3/4 faults set the global stop; no recorder silently clears it.

Reporting fields: uniqueGroupsTested, uniqueGroupsPassed, matrixCoverageComplete (12 distinct groups), passedBatches and recordedBatches (actual repeats), repeatBatches, cycles, plannedBatchInventory=72, unrunPlannedBatches. completePlan/passedPlan refer to the72 inventory and must not be displayed as the coverage requirement. Report deadline-bound unrun inventory without claiming an execution failure. Clean usual/soft counts, completedPairObservations, observedIncludingPartialPair, softXSum/softXCount/softMeanX, cap counts, diagnostic/fault rows and measured/forced shutdown timing remain separate.

Suggested renderer: “Extended strict-v2: G/12 distinct groups have clean coverage; B clean batches from R recorded (72 reserved), C completed pairs, U ordinary games/searches, S soft games/searches; X sum/count/mean; caps; new findings; retained original contract failure1; unused inventory N at deadline.” Show per-condition groups and cycles so repeated coverage is visible. Report the original02:19:40 deadline and explicit0016 extension04:20 separately. Do not merge historical raw observations into accepted-clean totals.

New repository packages: tests_astra_parity/final-paired-softnodes-extended/LABEL and final-paired-softnodes-extended-records/LABEL. VM metadata lives under /workspace/work/parity-run/softnodes-extended-recording/LABEL. No source, engine, Git or root state is changed by preparation. The synthetic suite retains12 prior cases and adds repeated-group coverage, distinct12-group coverage, and predecessor/deadline preservation.

A fourth new synthetic case confirms a later item3/4 finding overrides the already-covered matrix status. The final suite therefore has16 passing cases.
