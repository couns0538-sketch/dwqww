# Deferred Job A closeout helper

This preparation is not a closure. **Do not execute `close.mjs` before real UTC2026-11-15T04:20:00.000Z.** The CLI checks `Date.now()` against that frozen cutoff before any output-directory write and has no clock override. Preparation uses syntax checks and pure synthetic fixtures only.

Root's invocation at or after the cutoff:

```text
node /workspace/work/parity-run/command.mjs job-a-closeout-0420 node /workspace/work/parity-job-a-closeout-preparation/close.mjs --close-authorized
```

Run it serially with state recorders/checkpoints so the captured state can remain stable during assembly; Job B's native match may continue. No engine or Git command is launched by the helper. It never writes root state or the main renderer.

The helper verifies its frozen tools and all26 source/header/CMake hashes, both sanitizer binaries/flags/16objects, and the final release binary. It invokes the existing read-only snapshot helper with **fixed as-of04:20**, even if evidence publication occurs later. Recorded passes count only when the paired command interval is valid, audit-accepted and ended by the cutoff. Late, straddling, missing or unverified intervals are explicitly excluded rather than assigned invented partial credit. Failed attempts remain timed only in the all-attempt union. Preliminary checks, matches and all42 diagnostic searches have zero final-soak credit.

The report distinguishes observed finalized batch union, accepted-clean union, summed batch duration, elapsed soak window and unaccounted gaps. It states a duration shortfall whenever actual clean sanitizer time is below7200seconds; covering12 conditions never becomes a claim of two continuous hours. It retains raw Step2 gate=false and the separate effective acceptance, all historical failures, and the measured0018 diagnostic/finding0019 evidence. Source checks are read from their recorded results; no validation is rerun. Actual owner-PC compiler/PGO/tuning/network and per-node incremental/full NNUE equality remain unverified.

Immutable VM output:

- `/workspace/work/parity-run/job-a-closeout-0420/evidence/CLOSURE.txt` and `REPORT.md`.
- `SNAPSHOT.txt`, `STATE-SNAPSHOT.txt`, timing metadata pins, current renderer snapshot, source text snapshot, diagnostics and fault inventory.
- `PROPOSED-STATE-PATCH.txt`: one proposed add operation at `/jobAClosure`, with capture state SHA256 and absence precondition. **It is not applied.**
- `/workspace/work/parity-run/job-a-closeout-0420/PUBLICATION.txt`: immutable report/closure/package hashes.

Immutable repository text package: `forge-combo29/tests_astra_parity/job-a-closeout-0420`. Root owns its Git publication. Only text is packaged; no engine binaries or objects are copied.

Root may apply the proposed single-field update after reviewing it and checking the capture precondition. If Job B has updated state since capture, compare the retained Job A evidence with current Job A fields, then add only that field to the latest state. **Never replace current state with STATE-SNAPSHOT.txt**, which is historical evidence and contains old match counters. The helper performs no apply command; the root's existing state/checkpoint transaction remains authoritative. Existing identical closure state is accepted on replay; a conflicting existing closure is rejected.

Job B's declaration deadline is asserted as05:06:50.313UTC and remains unchanged. Its live counters, active job, phase, global stop and source fields are not modified. The closure tells the live report to continue treating B separately; it neither restarts nor prematurely closes B. Job C is not started.

The first completed evidence assembly is retained permanently. Replaying the command verifies/reuses it and its package without changing the closed timestamp. A failed assembly remains under a distinct immutable attempt directory; a later invocation can capture again. A publication interrupted after evidence assembly resumes from the same evidence. A stale exclusive close lock fails closed and needs explicit root recovery; it is never silently removed. No full-root-state rollback is proposed.

Verification actually performed is recorded in FINAL-VALIDATION.txt: JavaScript syntax, eight pure synthetic tests for early/exact clock boundaries, late-pass exclusion, overlap, actual-duration shortfall, preserved raw/effective gates and single-field patch scope. **Actual closure invocations0, engines0, root-state writes0, Git writes0.** First live closeout remains root's responsibility at the fixed cutoff.

The pinned time accountant is rerun after the snapshot; its final/preliminary timing and issues must exactly match. Every input hash (including state and preliminary metadata), missing-command absence and protocol inventory is checked again before the immutable evidence rename. A pure mismatch test proves disagreement is rejected. All26 source copies use allowed text extensions, including .inc.txt for include data.
