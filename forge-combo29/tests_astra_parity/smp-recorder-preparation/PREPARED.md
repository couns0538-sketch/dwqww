# SMP amended paired sanitizer recorder

Prepared 2026-11-15 around 02:40 UTC. No engine, Git, root-state or prior evidence was changed. The engine source remains unchanged; this is a fresh metadata recorder for Fable's explicit item4 amendment at commit `8bd329545d4ad9d0ac50d8dc1dd697f14b0daa1a`.

The new harness still enforces the strict rule with Threads1. Above one thread, it additionally accepts an info-node count below2500 when the final X sample is at least2500. Items2/3, legality, sanitizers and normal-exit requirements remain enforced. Earlier failed batches are never reinterpreted or credited through this recorder.

After each actual finalized batch, root runs the frozen auditor, records its actual stdout hash, then invokes:

```text
node /workspace/work/parity-softnodes-smp-recording-preparation/record.mjs INDEX AUDIT_STDOUT_PATH ACTUAL_SHA256 --check
node /workspace/work/parity-softnodes-smp-recording-preparation/record.mjs INDEX AUDIT_STDOUT_PATH ACTUAL_SHA256
```

The first invocation is read-only; the second publishes immutable text and atomically updates state. Both rerun only the read-only auditor. Index0..71 is the reserved inventory, not a requirement to run72 batches. Root retains unique command labels and its outer timeout below eight minutes. Serial recorder/state writers are required.

The required explicit root authorization is:

```text
smpSoftnodesResolution = {
  commit: "8bd329545d4ad9d0ac50d8dc1dd697f14b0daa1a",
  sha256: "c6c15eb30c204424339dbad34bdebeed320440358ce9c2f5afdac3efee35848c",
  oldAuditsAndFaultsUnchanged: true
}
```

The recorder never clears a global stop. A new item3/4 finding sets it. Failed, incomplete or externally interrupted batches receive zero accepted-clean coverage; observed games/searches, completed-pair observations, diagnostic/fault rows and shutdown timing remain separate.

New namespaces are `smpPairedSoftnodesRows`, `smpPairedSoftnodes`, `validation.smpPairedSoftnodes` and `soakTotals.finalTree.smpPairedSoftnodes`. Original and extended row/totals namespaces are frozen by exact digests and verified against immutable raw packages and proof records. Extended failed indices2/8 retain zero clean credit. The earlier Threads1 clean coverage—108 games,15,514 searches—is separately reported in `retainedExtendedCleanCoverage`; it is not added to the new protocol totals. Top-level final-tree games/searches reflect the new clean coverage, while its fault count includes the separately retained original contract failure and two extended contract failures.

`smpSamplingExceptions` contains three counts:

- `observed`: amendment-dependent CHECK rows, including partial or failed batches.
- `completedPairObservations`: such CHECK rows within pairs with completion records.
- `acceptedClean`: completed-pair sampling cases credited only when the whole batch passed.

The same fields are aggregated by group and across batches. They count only cases that needed the new SMP exception; mate, depth64 and hard-cap cases already accepted by the old rule do not count. Marker values must be0/1; an amendment marker on Threads1, an X below2500, or an X already at the10000 hard cap is rejected. Counts must match the frozen auditor. Raw CHECK rows remain retained.

Source/header/CMake pins, both sanitizer engines and their16 objects, oracle/driver inputs, all protocol tools, explicit decisions, previous declarations, actual batch command/stdout/stderr and the fresh audit are checked. Source/engine maps must equal the unused strict-v2 declaration. Historical flags, accepted counts, expected values and outputs remain untouched.

Publication uses the existing UTF-8/text-only chunker and reconstruction checks:

- `tests_astra_parity/final-paired-softnodes-smp/LABEL`
- `tests_astra_parity/final-paired-softnodes-smp-records/LABEL`

VM metadata is under `/workspace/work/parity-run/softnodes-smp-recording/LABEL`. A root-state hash guards the atomic transaction; concurrent state mutation causes refusal after evidence is retained. Identical duplicate recording is idempotent, and a conflicting identity is rejected.

Validation completed: all16 predecessor synthetic cases plus8 sampling/history cases passed; three syntax checks passed; current historical namespace digests and zero-credit failed indices were verified read-only. No tests were dropped and no live SMP batch was run by this preparation. The first actual `--check` and publication remain root work.

Frozen recorder SHA256: `8ebb7808c92ca68b38c2874535e70533e70e1cd8786432a4419cfdeaa9fb9c27`.

Frozen accounting SHA256: `8a65c7dd8db052bd133c3573377041de82516092a666c986c845a89c04eb5e82`.

The native harness pin is `ab599afccbdd999555c4ba30c32e41d94b6a32de9ea1b13ebf4ebcaae6bc3af7`. Tool files have matching inert text copies for later publication. No Elo or speed claim is made.

Independent final review passed: `/workspace/work/parity-softnodes-smp-peer-review/REVIEW.md`, SHA256 `ed12bf905f4df089fccce6430b2769b4ee675efdcb3b1270ff0f9649b6e3637f`. The peer verified all6 own and13 external pins and independently reran all24 accounting cases. No blocking finding remained.
