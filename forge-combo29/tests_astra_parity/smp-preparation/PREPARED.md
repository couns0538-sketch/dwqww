# SMP-amended paired sanitizer harness

Fable0017 explicitly changes item4 for Threads above1, without an engine change. Decision commit: 8bd329545d4ad9d0ac50d8dc1dd697f14b0daa1a; exact text SHA256 c6c15eb30c204424339dbad34bdebeed320440358ce9c2f5afdac3efee35848c. Earlier0015 depth64 and0016 deadline decisions remain separately pinned.

Threads1 keeps the exact strict-v2 rule. For Threads>1, the extra accepted case is last exact info nodes<2500 with a valid X>=2500. X<2500 remains a failure unless an existing mate/depth64 exception applies. Items2/3, exact-line parsing and completeness, legal moves, score bounds, diagnostics and normal exit checks remain unchanged. The old parser's entire strict item4 expression is retained before the extra clause. Native transport is byte-identical to strict-v2. The engine source, both sanitizer engines and all26 source/header/CMake pins are unchanged.

The new CHECK field `smp_sampling_exception` is0/1 and is1 only when the old strict item4 failed and the added SMP clause makes item4 pass. Existing mate/depth64/hard-cap cases do not count as reliance on the new rule. Audit fields `smpSamplingExceptions` and `smpSamplingExceptionsCompletedPairs` count all observed flagged checks and flagged checks in completed pairs, respectively. A faulted or incomplete batch still receives zero clean credit. The recorder separately handles accepted-clean counts.

Only the harness/parser source is new. `compile.txt` records the exact bounded compiler invocation and output, using the same frozen independent Board/bitboard objects. `parser-selftest.txt` records46 passing synthetic cases: the previous29 plus17 new SMP checks, including both observed sample patterns, T1 preservation, T2/T4 thresholds, X2499 rejection, X2500 acceptance, invalid X, still-enforced items2/3, bounded-info isolation and malformed-depth rejection. These are synthetic parser checks; no engine process was started. Source diff commands and full outputs are retained in `*.diff.txt`.

Root commands, after independent review and explicit authorization:

```text
node /workspace/work/parity-softnodes-smp-preparation/control.mjs declare d9a8587df8ad4d0ff1231632cb1ac72b590c04bf --freeze-authorized
node /workspace/work/parity-softnodes-smp-preparation/control.mjs run INDEX --execute-authorized
node /workspace/work/parity-softnodes-smp-preparation/audit.mjs INDEX
```

The required new root authorization is `smpSoftnodesResolution = {commit:"8bd329545d4ad9d0ac50d8dc1dd697f14b0daa1a",sha256:"c6c15eb30c204424339dbad34bdebeed320440358ce9c2f5afdac3efee35848c",oldAuditsAndFaultsUnchanged:true}`. The current global stop must be cleared explicitly by root under that decision. The controller and recorder never clear historical failure or stop fields.

New runtime: `/workspace/work/parity-run/softnodes-smp-batches`. New state namespace: `smpPairedSoftnodesRows` / `smpPairedSoftnodes`. All previous tools, native executables, declarations and raw evidence remain unchanged. Old original failure and both extended T2 failures retain zero clean credit. The two earlier T1 passing batches remain separately reported by the recorder.

Six cycles reserve72 fresh batches, while coverage is12 unique groups. First-cycle seeds202611160101..202611160112, increasing1000 per cycle. New labels start `smp-c01-` through `smp-c06-`. Relative wave order is [[2,8],[4,10],[5],[11],[1,7],[3,9],[0,6]], plus12 per cycle. Earlier waves must have recorded passing audits before a later wave can launch, so the first run is the new T2 wave. Same-wave reservations are atomic, aggregate engine Threads<=4, and active sibling findings block new launches. Root supervises already-running siblings; no automatic cancellation monitor is claimed. Do not overlap matches or unrelated native workloads. Record/checkpoint state serially.

Deadline remains2026-11-15T04:20:00.000Z. Target180seconds per batch, unchanged420-second native bound,440-second outer timeout and475-second launch margin.72 is an inventory, not a claim that every batch will finish. Build/parser/metadata/syntax command outputs are retained; final file identities are in FROZEN-PINS.txt. No engine source, root state or Git change occurs during preparation. Future Job C is not started.
