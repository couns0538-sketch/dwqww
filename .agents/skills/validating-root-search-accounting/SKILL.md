---
name: validating-root-search-accounting
description: Use when changing chess-search root effort counters, move-identity accounting, aspiration-retry statistics or effort-based time allocation, especially when root move ordering changes between iterations.
---

# Validating root search accounting

Attribute work to stable move identities before interpreting its effect on stopping. Correct counters, offline timing arithmetic, observed timed stops and playing strength require separate evidence.

## Workflow

1. **Freeze the question.** Record parent/candidate source, network, compiler/flags, binaries, instrumentation patch and trace hashes. Read the current [status](../../../validation/root-effort-20261019/STATUS.md).
2. **Audit identity and scope.** A picker ordinal changes when ordering changes. Use canonical legal root identities with full `Move` equality: from, to, promotion and flags. From/to alone merges underpromotions. Initialize identities and reset counters once per root search. Preserve the specified cumulative policy across depths and aspiration retries, child-node delta boundaries, local-node denominator and exclusion of unfinished aborted children. Counter sums need not equal local nodes because search overhead also contributes.
3. **Keep costs and guards local.** Inspect current `root_effort_moves_`, `root_move_nodes_` and `TmEffortBase` call sites in `src/search.cpp` and `include/forge/search.hpp`. Scope lookup/end construction inside root-only branches. Bound fixed storage by canonical root capacity; retain debug assertions and release write guards. A missing identity must not silently charge another move. Audit early returns before counter consumption and helper-worker ownership.
4. **Use an actual-source oracle.** Instrument the frozen search's child events and completed iterations. Record search/depth/retry, move identity, ordinal, child delta, selected best move and local nodes; UCI identities require a canonical full-Move mapping. First establish untouched-versus-traced fixed-depth PV/score/node parity. Independently reconstruct ordinal buckets and per-Move totals, then compare candidate counters at every completed iteration. A model illustrates the mechanism but cannot establish actual-engine behavior. Preserve [original traces and proposals](../../../validation/root-effort-20261019/actual-baseline-and-proposals.zip).
5. **Check correctness cheaply first.** Exercise reorderings, promotion identities, searchmoves restrictions, sequential-search resets, aborted children and terminal/zero-budget paths. Run cheap Release checks first; complete required sanitizers, cold/warm untimed parent parity, trace oracles and Windows checks before timing or games. Independent checks may overlap when resources permit; timed measurements need an idle host. Do not retune timer constants, denominator or retry policy inside an accounting-only fix without separate tests.
6. **Bound conclusions.** Offline factors do not demonstrate a timed stop; Wine does not establish native deadline safety. Respect failed timing controls rather than repeating the same noisy experiment. Require actual target checks and separately frozen equal-clock games; only audited accepted H1 supports gain under its protocol.

See [scenarios and verification limits](scenarios.md). Report pending gates explicitly.
