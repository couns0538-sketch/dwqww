# Prepared, unused: prescribed second-candidate-timeout diagnostic

No engine runs or real diagnostic declarations were performed during preparation. The native helper compiled successfully; the measured transport is byte-identical to the frozen v3 `uci_process.hpp` (SHA-256 `606bd7cd54e94acba10da32bacc9c2620b7e5d8882b360e2492294ac197d40d2`). Syntax and synthetic parser validation passed in `VALIDATION.txt`. `BUILD.txt` preserves the exact successful build command and outputs. The initial local compile failure and its source are retained separately.

This is conditional preparation for Fable answer 0012, SHA-256 `c43cf885c83df3be5453fbe71087e8311506cbd7a97af298b43d3c24c2515642`. Root must first audit a real second classified candidate shutdown timeout. Nothing here grants continuation past that finding, changes the equality policy, or waives score differences or other faults.

## Root invocation, only after the prescribed trigger

Run the declaration using the actual audited batch, for example with `speed S1-NNNN` or `final S2-NNNN`:

```text
node /workspace/work/parity-shutdown-diagnostic-preparation/control.mjs declare STAGE BATCH
```

The declaration requires the finalized v3 receipt, its exact audit hash, at least two cumulative candidate timeout occurrences, `escalationRequired`, and a pure candidate shutdown occurrence other than the original S1-0001 event. It verifies the stage/tool/decision/summary/artifact pins and the selected full attempt, extracts the actual FEN, and pins the candidate/reference binaries. If several FEN groups qualify, append the selected zero-based index in the audit's `shutdownTiming.timeoutOccurrences` array; the helper does not guess chronological order.

The declaration creates one immutable directory under `/workspace/work/parity-run/shutdown-diagnostics/`, prints its exact path, and refuses another diagnostic declaration for this Job A. Use the command it prints:

```text
timeout -k 3 440 node /workspace/work/parity-shutdown-diagnostic-preparation/control.mjs run DIRECTORY --execute-second-candidate-diagnostic
```

A read-only repeat audit is available:

```text
node /workspace/work/parity-shutdown-diagnostic-preparation/control.mjs audit DIRECTORY
```

Do not run the native executable directly. Declaration and execution remain root actions; this preparation made no root-state, Git, production-source, or engine changes.

## Exact scope and evidence

The target is **2,000 cycles total**, strictly candidate/reference alternating from candidate, 1,000 each. Each cycle creates a fresh process and uses depth 9, Threads 1, Hash 16, OwnBook false, `ucinewgame`, the exact trigger FEN, and otherwise fresh-process defaults. Both default-false HindsightDepth and MateAlphaGuard advertisements are checked. The trigger FEN is not substituted with the first timeout's FEN.

Each attempted cycle has a flushed start marker. Each finalized cycle records the search tuple, PV, response/error status, full stdout/stderr/command transcript, shutdown exit/signal/escalation status, timing and transcript filename. All finalized transcripts are hashed by the auditor. The raw JSONL, raw stderr, exact argv/cwd, input hashes, actual process result and UTC timestamps are retained. Changed inputs or mismatched raw stream hashes invalidate completion.

The diagnostic explicitly requests a **250 ms shutdown allowance** per cycle. Its measured value starts immediately before the successful quit send call and ends at observed `waitpid` exit; it includes send-call duration. Timing is unavailable if quit was not sent or exit was not observed. No duration or allowance is inferred for the original unmeasured S1-0001 shutdown.

Counts and timing distributions remain separate by side and by forced/budget-interrupted status, including timeout counts, signal/nonzero exits, maximum measured time, values over 100 ms, missing timings, and tuple frequencies. `completePrescribed2000` reports that all 2,000 prescribed search/quit cycles have finalized with depth-9 results and observed exits; it is **not an all-faults-pass flag**. Inspect the retained timeout/error/sanitizer fields even when the requested cycle count completes. This diagnostic alone cannot prove a physical cause for a shutdown delay.

## Bounds and limitations

The native allowance is at most 390 seconds, shortened to leave 30 seconds before Job A's absolute end, `2026-11-15T02:19:40.000Z`; launch requires at least 30 native seconds. The inner timeout is allowance +5 seconds with a further 3-second kill grace, and the controller wait is allowance +9 seconds. The displayed outer command is bounded at 440+3 seconds, below eight minutes. Startup/search has a combined per-cycle cap of 15 seconds, clipped by the overall native deadline; shutdown is separately bounded.

A limited or interrupted run retains actual attempted/finalized/per-side counts and unfinalized start markers; it never rounds them to 2,000 or credits a missing cycle. A hard external kill can prevent the currently live process's in-memory transcript from being finalized; that incomplete attempt is retained as a start marker and cannot satisfy completion. There is no automatic rerun or top-up. Root must retain the actual shortfall if the deadline prevents completion.

Validation exercised the 2,000-total/1,000-each case, a 37-cycle partial (19 candidate/18 reference), an unfinished next cycle, wrong alternation, and missing required timing. These were synthetic parser fixtures only. Real engine integration is deliberately unexecuted.

For publication, use the text/source files and identical `.mjs.txt` twins. The compiled `diagnostic` ELF is VM-only and must not be archived into the source/report repository. `FILE-PINS.txt` lists all retained files, including the VM-only native binary's hash for provenance.
