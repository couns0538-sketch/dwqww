# Job B final report and closure proposal

Prepared 2026-11-15 around04:14UTC. This helper never executes an engine, Git command or root-state mutation. It verifies retained evidence and, only when root explicitly invokes `close`, creates new immutable text evidence plus a proposed patch containing only `jobBClosure`.

The actual declaration is pinned: start03:06:50.313UTC, deadline05:06:50.313UTC,6000-game target,100-game batches,50000 nodes per move. Launches require470 seconds remaining. Therefore the clock gate permits a budget-limited closure strictly after04:59:00.313UTC, or earlier once all6000 games have been credited. It also requires no active native executable, no occupied root active slot, no incomplete match batch, and no raw batch artifacts awaiting a receipt. A prepared but never launched future plan is listed separately.

The actual wall clock is read internally. There is no command-line time override. A global engine stop does not prevent recording an honest budget-limited shortfall; the helper preserves that stop and records its current state, phase and the separate ASan shutdown finding0020, including fault/audit hashes and resolved status. It never grants permission for another engine run.

Root commands:

```text
node /workspace/work/parity-match-closure-preparation/close.mjs check
node /workspace/work/parity-match-closure-preparation/close.mjs close /workspace/work/parity-run/match-closure/FINAL_LABEL
```

Use a new destination. Root should wrap the command with its existing logging helper and a bound below eight minutes. `check` is fully read-only and can report that closure is not yet eligible. `close` verifies everything again; if eligible, it writes:

- `CLOSURE.txt`: exact verified counts, conditions, hashes, clock data, pause state, faults and receipt/package index.
- `REPORT.md`: concise counts-only summary, actual timing, remaining target, optional250000-node leg not run in this experiment, and any separate sanitizer pause.
- `INDEX.txt`: immutable evidence references and reconstruction manifests.
- `PROPOSED-STATE-PATCH.txt`: one top-level key, `jobBClosure`; it is not applied.

The current main report remains root-owned. Applying the proposed closure is a separate root action. The helper neither rewrites match totals nor marks JobA's sanitizer work complete.

Verification includes the frozen declaration, source and binary pins, authority0018 and accepted Step2 evidence, every receipt/plan/summary/command/process outcome, exact per-row accounting re-derived through the frozen recorder, cumulative totals, previous receipt chains, source artifact hashes/byte counts, immutable proof rows, and complete reconstruction of every raw and metadata package. A root-state hash check rejects a concurrent recorder/checkpoint change. No native result is rerun. Verification has a420-second internal bound; source/package checks fail closed when that bound is reached.

Timing is explicit: declaration start and deadline; actual last native-batch process finish; sum of actual native-batch process wall times; declaration-to-last-stop elapsed time; and the separate closure-evidence timestamp. The report does not claim two continuous hours of play. Counts distinguish W/L/D and five pair bins from illegal games/events, disconnects, stalls, time forfeits, process exits, crash signals, cleanup signals, aborts, unattributed records and excluded raw finished games. Process deaths and disconnect games are not added together as separate crashing games. Full raw details remain in the indexed summaries and packages.

Validation: fourteen pure/history checks and three syntax checks passed. An actual read-only check verified the currently retained500 games, five receipts and ten immutable packages, correctly reporting closure ineligible before04:59:00.313. It also verified the newly retained0020 fault/audit hashes while leaving the global stop unchanged. No actual closure was executed. The earlier pre-pause helper/pins and read-only check remain under `*.before-pause.txt` and the original check outputs.

Frozen close helper SHA256: `6d22581c76cc255a4bba6f65402b4974522b430e4d95ff1c51a467934821c6e2`.

Frozen model SHA256: `1ffeb57497968a8550cec3633d24a774a8e1c19d835af1e97d29eb20c6e74d10`.

Counts only; no Elo or speed conclusion.

Independent final pause-delta review passed: `/workspace/work/parity-match-closure-peer-review/PAUSE-ADDENDUM.md`, SHA256 `c3bce207890abf47346837c4b796590e33f46a881e16b40915994493870497b0`. The reviewer verified all seven revised pins and the0020 fault/audit hashes, confirmed the gate was unchanged, and reran all fourteen checks and three syntax checks. Readiness does not assert current closure eligibility.
