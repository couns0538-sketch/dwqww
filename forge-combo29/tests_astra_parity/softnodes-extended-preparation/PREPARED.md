# Extended strict-depth paired sanitizer plan

Metadata-only extension authorized by Fable0016, commit 6f52b2dfe18d289a201e3a06fd756152ba28a539, decision SHA256 1ca13976a15e8e8b7dbd994aeca5176d8158a18ff71db87422095adf83d6c1b2. Job A deadline is 2026-11-15 04:20:00 UTC. The original 02:19:40 deadline and all predecessor files remain unchanged. Fable55dd's exact-depth64 acceptance amendment remains separately pinned.

The strict-v2 native executable is reused unchanged, SHA256 17dd75a673996e04185819383589b3f04b450750594fec6b357dd6330058f555. No new native helper or engine is compiled or run during preparation. All 26 current source/header/CMake pins, both sanitizer engines, flags and eight objects per engine must equal the unused strict-v2 declaration. Its original driver/oracle inputs remain pinned. Both unused predecessor directories must contain only declaration.txt.

The plan freezes 72 possible batches: six cycles of the same12 conditions. First-cycle seeds remain 202611155201..202611155212; cycles2..6 use 202611156201..212, 202611157201..212, 202611158201..212, 202611159201..212 and 202611160201..212. Labels begin extended-c01 through extended-c06. A 180-second target starts whole pairs only; the unchanged native hard limit is420seconds, outer timeout440seconds, launch margin475seconds. Seventy-two is an inventory, not a requirement to launch every batch before the deadline.

Root commands (use the command logger with unique labels):

```text
node /workspace/work/parity-softnodes-extended-preparation/control.mjs declare d9a8587df8ad4d0ff1231632cb1ac72b590c04bf --freeze-authorized
node /workspace/work/parity-softnodes-extended-preparation/control.mjs run INDEX --execute-authorized
node /workspace/work/parity-softnodes-extended-preparation/audit.mjs INDEX
```

Raw directory: /workspace/work/parity-run/softnodes-extended-batches. The declaration is immutable. Root owns all native launches. Launch one wave at a time, with relative indices [[0,6],[2,8],[4,10],[5],[11],[1,7],[3,9]] and add12 per cycle. Maximum aggregate engine Threads is4. Do not overlap any match or unrelated native workload. Only the same declared wave can be active concurrently; a finalized earlier batch requires a passing recorded audit before another launch. Record and checkpoint serially. Any native finding, failed audit or incomplete batch prevents new launches; an item3/4 finding also sets the global engine stop. Already launched sibling batches are separate active commands: root must supervise them and stop them if an item3/4 finding requires immediate global cessation. This metadata controller does not claim an automatic cross-process cancellation monitor.

Use the matching recorder at /workspace/work/parity-softnodes-extended-recording-preparation/record.mjs. It separates original failure, new accepted-clean coverage, completed-pair observations and partial observations. No old acceptance or count is rewritten.

Verification outputs are in VALIDATION.txt and frozen hashes in FROZEN-PINS.txt. Preparation performs only metadata and synthetic checks; actual sanitizer coverage begins only after root declares and launches this protocol.

Controller launch reservations use a short exclusive filesystem lock across the thread/wave checks and start metadata. Root should start each controller through its started output before launching its same-wave sibling. An interrupted stale reservation is a fail-closed manual-recovery condition; it must not be silently cleared. Active sibling logs are scanned for item3/4 failures, fault rows and diagnostics before a new launch.
