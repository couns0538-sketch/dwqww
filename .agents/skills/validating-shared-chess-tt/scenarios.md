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

## Bounded owner lease

This is a conditional ownership protocol, not a general exemption from locking.
Default public Shared/SMP calls retain coherent striped access. Only an explicit
opt-in with exactly one search worker may acquire a coarse gate across recursive
search; no helper may be launched or joined while that lease exists. Keep
per-entry stripes scoped to individual operations or drain steps.

| Application scenario | Required decision |
|---|---|
| Threads1 worker skips locks; public foreign probe/store/hashfull still lock | Reject. Worker count and ordinary foreign locks do not synchronize a bypassing owner. A standalone model pass cannot establish actual-engine exclusion. |
| Owner holds all1024stripes; default GCC14 TSan enters main, acquires64 and CHECKs on65 | Preserve detector-capacity failure and deadline as incomplete evidence. No data race was reported, and no race-free completion occurred. Do not disable the detector to manufacture GREEN. Use one gate plus at most one stripe during sequential drain and validate the actual engine separately. The observed64 limit belongs to this runtime, not every TSan build. |
| Explicit exact1T opt-in holds one gate, drains all stripes, publishes table-bound TLS and routes foreign access through wait/retry | Eligible for bounded review. Verify the ordering below, default Shared/SMP fallback, exact search/replacement parity and actual-engine correctness. The gate is the reviewed exception across recursion; helper launch/join remains outside it. Finite passing tests do not prove universal correctness or positive speed/Elo. |
| Lease ends and search worker joins, but a foreign accessor was blocked on the gate | It may now resume. Join/quiesce it and every diagnostic/metadata/prefetch caller before clear/resize/new_search/destruction. Lease release is not a foreign-accessor drain barrier. Foreign calls must not retain locks needed by search, including output locks. |
| TLS lookup recognizes A in one thread's A→B→A ownership chain | This avoids reacquiring that thread's existing owner. It proves no arbitrary cross-thread A→B/B→A deadlock freedom. Require a consistent inter-table acquisition order or an independently justified liveness contract; do not test same-Searcher recursive search by reentering mutable Worker state. |

The reviewed protocol acquires the coarse gate, release-stores `requested=true`,
then acquires/releases every stripe **sequentially**. Publish owner TLS only after
all stripes drain. A foreign caller locks its stripe, acquire-loads the flag and
keeps the stripe only when false; when true it releases the stripe, waits on the
gate and retries. Never wait on the gate while holding a stripe. A caller that
passed false before the request must complete before its stripe drains. A
post-drain stripe acquire synchronizes with the drain's unlock and therefore
cannot observe pre-request false. Owner exit restores prior TLS, release-stores
false **after its final entry access**, then unlocks the gate. That release also
publishes owner writes to a newcomer that never waited on the gate. Partial-drain
constructor failure resets the flag before releasing the gate; publish no TLS on
failure. Same-table nested guards must preserve the outer request and ownership.
Storage and generation remain stable throughout; lifecycle still needs all
accessors quiescent.

## Recorded engineering evidence

The [original checkpoint](../../../validation/tt-coherence-20261019/STATUS.md) preserves the actual full-engine failing control and source/build provenance. With Threads4, Hash1, OwnBook=false and `go nodes 200000`, the instrumented baseline reported a worker write in `TranspositionTable::store` (`search.cpp:222`) conflicting with a worker read in `probe` (`search.cpp:199`). It halted with exit66 before bestmove. That is an observed race; it is not a completed search or match.

The superseded store-time-reselection proposal and revised opaque probe-time destination were reviewed before integration. The delayed-store case above discriminates their semantics by static reasoning; this document does not claim a historical test run of the superseded proposal.

An external driver's stderr-reader exception initially appeared only in event logs and could have escaped the pass/fail decision. A deterministic closed-stream regression failed, then passed after reader failures became explicit incomplete-capture failures. Its six subprocess contract checks passed with python-chess enabled; those checks validate the driver, not the repaired engine.

Frozen source `8865666cc0ab4961cd507bae40ff6ce44e9319df` and its
[independent source/API audit](../../../validation/single-thread-tt-20261020/AUDIT.md)
record the opted-in gate/drain candidate. The superseded all-stripes prototype
`a5d2fcb5b3270c50b96bcc1b2ebd3bc42db5f2fc` reached the default TSan detector's
64-held-lock capacity and CHECKed at65; its separate smoke remains preserved.
The revised lock-pattern smoke completed with the detector unchanged, but that
alone was not engine validation. The candidate subsequently passed all9 Release,
all9 ASan/UBSan and all9 TSan CTests, seven actual-API groups in each profile,
eight active-UCI TSan edges and eight Windows/Wine checks plus artifact audit.
The [frozen checkpoint](../../../validation/single-thread-tt-20261020/SOURCE-FREEZE.json)
links original evidence; the [verified complete archive](../../../validation/single-thread-tt-20261020/archive-complete/VERIFY-RECEIPT.json)
retains source, binaries and raw failures. Actual API tests include foreign
probe/store/hashfull blocking, default/SMP fallback, 1→4→1, delayed destinations,
external stop, different-table nesting and injected constructor/output exceptions.
One-thread parity and mutex-count evidence are separate; fewer mutex operations
establish neither a measured speedup nor Elo. These finite tests cover recorded
paths and do not extend the public lifecycle or arbitrary nested-table contract.

## Verification performed for this skill

The original scenario table was checked statically; it did not establish a
fresh-agent behavior gain. For this ownership update, a fresh agent first applied
the unchanged skill to five preregistered scenarios. It correctly rejected unsafe
bypass, invalid sanitizer acceptance, premature resize and an ABBA guarantee, but
its literal application categorically prohibited the otherwise reviewable coarse
gate because the old instruction had no ownership distinction. The updated skill
is tested on the same applications; retain the exact outputs and bounded verdict
in [skill validation](../../../validation/single-thread-tt-skill-20261020/REPORT.md).
This documentation exercise executes no engine or matches and does not upgrade
engine correctness, performance or strength evidence.
