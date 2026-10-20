# Application scenarios and verification limits

These are documentation checks, not new engine tests or match evidence.

| Scenario | Required decision |
|---|---|
| Probe locks, returns a live `TTEntry*`, unlocks; stores lock too | Callers still race when reading fields. Inspect the escaped pointer and replace shared reads with a coherent local copy and opaque destination. |
| Snapshot store selects a new victim after recursion | This changes one-thread replacement behavior. Probe X on empty slot0; independently store colliding Y there; delayed exact store through X's original handle must overwrite slot0. A reselecting implementation incorrectly preserves Y in slot0 and chooses another slot. |
| Another store overwrites a selected slot | Preserve the original destination; evaluate baseline admission against its current contents. Distinguish ordinary overwrite from lifecycle invalidation. |
| Model passes; candidate exits66 with `FATAL: ThreadSanitizer: unexpected memory mapping` before UCI | Model-only evidence and a failed runtime startup. Preserve logs and repair the environment; no actual-engine race-free claim. |
| UCI joins search/helpers; diagnostic hashfull or prefetch caller remains active during resize | Storage is not quiescent. Stop every accessor before lifecycle mutation. `isready` is only a processing response; use the engine's stop/join path. |
| Remote status claims success, but no changed engine source is present | Inspect fetched tree/history and recover the actual patch/API before rebuilding or reconstructing it. Keep status/model claims separate from implementation provenance. |
| Stderr capture fails, engine exits0; baseline exit66 is expected | Capture failure invalidates validation. Accept expected baseline race evidence only with intact report/capture and the declared exit; never classify it as candidate GREEN. |
| Candidate passes one-thread parity and gains SMP NPS on a VM | Report those checks and measured settings. Neither result establishes equal-clock Elo, target Ryzen/Windows speed, nor absence of unexercised races. |

## Recorded engineering evidence

The [original checkpoint](../../../validation/tt-coherence-20261019/STATUS.md) preserves the actual full-engine failing control and source/build provenance. With Threads4, Hash1, OwnBook=false and `go nodes 200000`, the instrumented baseline reported a worker write in `TranspositionTable::store` (`search.cpp:222`) conflicting with a worker read in `probe` (`search.cpp:199`). It halted with exit66 before bestmove. That is an observed race; it is not a completed search or match.

The superseded store-time-reselection proposal and revised opaque probe-time destination were reviewed before integration. The delayed-store case above discriminates their semantics by static reasoning; this document does not claim a historical test run of the superseded proposal.

An external driver's stderr-reader exception initially appeared only in event logs and could have escaped the pass/fail decision. A deterministic closed-stream regression failed, then passed after reader failures became explicit incomplete-capture failures. Its six subprocess contract checks passed with python-chess enabled; those checks validate the driver, not the repaired engine.

## Verification performed for this skill

The scenario table was checked statically against the API, lifecycle code, regression sources, driver and retained failure reports. Generic judgments such as rejecting model-only TSan or NPS-to-Elo claims are already supported by ordinary engineering knowledge; they are not demonstrated improvements caused by this skill.

No fresh-agent comparative behavior study, pressure-test result, new sanitizer run or match was performed for authoring these files. Candidate full-engine GREEN, deterministic parity, performance and playing-strength outcomes must be established by their own retained run evidence. The skill consolidates a practical reference and recorded failure lessons; it does not upgrade an ongoing experiment's status.
