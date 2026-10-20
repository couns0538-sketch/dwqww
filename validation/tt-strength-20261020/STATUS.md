# Prospective TT strength package

Candidate 6.4.12 source is frozen at
8865666cc0ab4961cd507bae40ff6ce44e9319df against baseline 6.4.11
c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e. The launch gate is
**PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH**, source_gates_status=PASSED,
after the final proof hashes and `root-ready-check.json` validate that state.
Full Release, ASan/UBSan and TSan CTests passed 9/9 each; seven actual public-API
groups passed in all three profiles; eight active-UCI lifecycle edges passed
under TSan with default deadlock detection; eight Windows/Wine checks and
the independent Windows artifact audit passed. Source/driver inputs remained
unchanged. Exact proof-file hashes are recorded in the protocol.
No engine, build, timing trial, game, branch mutation, commit, push or launch
was performed by package preparation. No speed or Elo result exists.

Adapted runner safety tests pass 42/42; archive byte-preservation tests pass
8/8. Tests cover finally rehash, fault/signal/deadline cleanup, unrelated-process
survival, orphan rejection, incremental warning/output mutation detection,
strict native plus independent 0/+5 likelihood, natural cap behavior, CLI
settings and source/review gates. Mocked Python children are not chess engines.
Original >100MiB binary logs, ZIP splitting/reassembly and every payload hash
are verified by the archive suite. All raw test stdout/stderr are retained.

72 frozen source-export input hashes for both exact Git objects, the original
diff and changed-path lists are retained. Only TT synchronization and UCI/bench
explicit Exclusive selection affect runtime behavior beyond version labels;
NNUE/eval inputs are unchanged. Match helper changes and the counter driver
are non-engine build inputs recorded separately. Root must finish review;
mutex operation counts do not establish NPS or playing strength.

The initial opening preparation used system Python and failed before replay
because chess was unavailable. Its traceback is retained as attempt1. The
corrected attempt reuses /workspace/.cloud-setup/venv/bin/python with installed
python-chess 1.11.2; it introduces no dependency or environment changes.
Opening reservation/check results and final static/hash results are recorded
in the adjacent JSON/stdout/stderr files when complete.

This new package owns fresh 4+1024 opening pools, excludes every original
42-registry/unused-tail position and explicit 164 confirmation positions,
and excludes all 1028 reserved active NNUE strength positions. It never edits
or reruns the active NNUE package/job39348571407/frozen563bd406. No old game is
reused and no outcome selects openings. Parent source correctness, host
readiness, speed and Elo remain separate from these preparation checks.

ROOT_CHECK_COMMANDS.md describes the no-engine checks and the final root gate.

## Completed preparation checks

The separate read-only opening verifier passed all 34700 legal 16-ply replays,
34700 unique positions, 3097 actual-EP exclusions without rewriting, 31603
strict EP-none before exclusions and 30575 eligible after the complete frozen
exclusion set. It confirmed all 42 original registry hashes, the explicit 164
confirmation cohort and all 1028 active NNUE reservations, zero overlap, fresh
4/1024 pools, exact selector ordering/source indices and runtime seed20261022
order/EPD hashes. All 1028 ranking hashes, runtime pool metadata and the
one-reservation marker were also checked directly.

Static YAML/bash/Python checks, 72 source-export file hashes against both Git
objects, all 23 package/workflow inventory entries and both disjoint EP-none
pools pass. The original NNUE package's 22-entry checksum inventory and empty
tracked diff pass. --require-ready was run and rejected this pending package
as expected; its original traceback is retained as an expected rejection.

The final protocol is PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH with
source_gates_status=PASSED. The earlier pending-gate rejection is retained;
root-ready-check.json records the final static gate.
The verified raw mutex count is 706157 baseline versus 8204 gated, as recorded
in single-thread-tt-20261020/gated-green-counts.json; this is not NPS or Elo.
No games or launch occurred during preparation. Final source and correctness
review passed; source886 remains frozen (full SHA above). A single new trigger
push is the separate next action.
