# Final paired UCI evidence recorder

Prepared in the cloud for root's final Job A sanitizer workload. No engine, Git or root-state mutation ran during preparation. The predecessor's unfinished accounting source is preserved as `accounting.pre-recovery.mjs.txt`. This directory is frozen by `RECORDER-PINS.txt`; do not modify its tools after use.

Root commands after a batch has finalized:

```text
node /workspace/work/parity-run/command.mjs final-paired-audit-0 node /workspace/work/parity-softnodes-preparation/audit.mjs 0
sha256sum /workspace/work/parity-run/logs/final-paired-audit-0.stdout.txt
node /workspace/work/parity-softnodes-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/final-paired-audit-0.stdout.txt ACTUAL_SHA256 --check
node /workspace/work/parity-run/command.mjs final-paired-record-0 node /workspace/work/parity-softnodes-recording-preparation/record.mjs 0 /workspace/work/parity-run/logs/final-paired-audit-0.stdout.txt ACTUAL_SHA256
```

Replace index and unique labels for later groups. Use the actual displayed audit hash; no expected hash is supplied here. An auditor exit1 is a retained finding or incomplete batch, not permission to discard it. The recorder reruns only the frozen read-only auditor, never an engine. `--check` verifies and previews without writing files or state. Wait for a recording transaction to finish before a checkpoint or other root-state write.

The recorder verifies the final declaration, all26 source/header/CMake pins, both instrumented engines and their eight object files, build flags, driver and independent oracle pins, exact batch arguments, raw output hashes, saved auditor hash, current frozen tool hashes, and prior immutable record/package proofs. It compares the reproduced auditor result while ignoring only its newly generated `utc` field. New tools and actual read-only auditor/package commands are archived. Text packages preserve full raw data with SHA256 reconstruction manifests; binaries are never copied.

Raw packages: `tests_astra_parity/final-paired-softnodes/LABEL/`.
Metadata packages: `tests_astra_parity/final-paired-softnodes-records/LABEL/`.
VM transaction records: `/workspace/work/parity-run/softnodes-recording/LABEL/`.

State fields are `finalPairedSoftnodesRows`, `finalPairedSoftnodes`, `validation.finalPairedSoftnodes`, and `soakTotals.finalTree.pairedSoftnodes`. The last namespace also exposes `games`, `searches`, `faults`, `faultCountingUnit`, and `status` for the existing report renderer. Those game/search totals contain **accepted-clean coverage only** from passed final paired batches. Earlier in-process and preliminary paired checks remain unchanged and excluded.

Each row has three distinct count sets:

- `credit`: complete pairs from a passed batch only.
- `completedPairObservations`: complete pairs before a finalized fault, retained without calling them accepted-clean coverage.
- `observedIncludingPartialPair`: all parsed game/search observations, including a partial pair.

Interrupted or externally timed-out batches receive zero credit and zero finalized-pair credit. Their raw observations remain visible. Duplicate evidence is a verified no-op; conflicting duplicate indices fail. Totals are recomputed from unique immutable rows, not incremented from caller claims. Soft mean X is cumulative `softXSum / softXCount`; cap cases are `softHardCaps`. Per-group counts, actual shutdown timing, forced/unavailable shutdown groups, diagnostic lines, fault reasons, timeout counts and missing-audit counts remain separate. A diagnostic-line count is not a distinct-race count; root must examine/report actual sanitizer reports if any occur.

`faults` counts batches with observed engine, label, diagnostic or shutdown findings. It does not call every incomplete or zero-coverage batch an engine fault. `failedBatches`, `incompleteBatches`, `zeroCoverageBatches`, `auditUnavailableBatches`, `manualReviewRequired` and `continuationAllowed` make those limits explicit.

Any item3/item4 violation in a complete soft `CHECK` row, `FAULT.label_fault`, or summary sets `blockFurtherEngineWork`. This remains true when there is no summary. Exact failing checks and their triggers are retained. Root must send that finding before another engine run; the recorder does not launch or authorize later workloads.

The frozen auditor parses all JSON rows before handling interruption. If a truncated row makes it throw, the recorder retains its real failed invocation and raw output, performs a supplementary scan of complete newline-terminated records and diagnostic text, and records `auditUnavailable=true`, zero accepted coverage and required manual review. The supplement is never a passing audit. Malformed/truncated records themselves remain listed. If a controller/environment interruption prevents `command.txt` from being finalized at all, this interface refuses safely: preserve that unfinished directory separately and document/recover it explicitly; do not invent an exit status or success.

Publication is immutable and root state uses an atomic replacement guarded by its original SHA256. If another root-state write occurs during packaging, the recorder refuses the replacement; existing packages are retained for a safe retry. Unrelated active work, source commits, push metadata and preliminary counts are preserved.

Validation: three JavaScript syntax checks and eleven synthetic accounting cases passed. Cases cover clean and faulted complete pairs, interrupted runs, an item3 failure without summary, truncated JSON, unequal soft-X sample counts, duplicate/conflicting indices, shutdown timing, corrupt soft sums, invalid pair IDs and negative X. Independent read-only review found no acceptance or transaction blocker after these corrections. Full wrapper publication/state mutation has not been exercised during preparation; its first live invocation belongs to root. No final sanitizer count is claimed by this preparation.
