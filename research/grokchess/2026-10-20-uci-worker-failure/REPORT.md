# GrokChess 1.7.50 research: UCI recovery after unrecoverable SMP startup failure

Date: 2026-10-20. Isolated research branch; no production merge.

## GitHub audit / avoiding overlap
Inspected couns0538-sketch/dwqww before the experiment, including recent commits, branch refs, open PRs, and source/checkpoints. Forge core `forge/6.4-hourly-20261019` remained at `356e863d`. Sol's OwnBook candidate `af194137` on `forge/candidate-ownbook-native-20261020-1145` differs from Forge core only in `src/uci.cpp` (1 insertion, 1 deletion). The 11:45 OwnBook candidate was identical to the 10:45 candidate, and the 11:30 test branch identical to Forge core, so neither represents an additional tested fix. We did not modify Forge.

## Baseline and red case
Baseline is the **unmerged compiled-JavaScript** GrokChess research candidate from the 2026-10-20 11:05 worker-crash checkpoint, NOT the authoritative TypeScript release. Its `uci/main.js` launched an async `setImmediate` search with `try/finally` but no `catch`; if `ensurePool` rejected (after both startup attempts failed), the unhandled promise rejection terminated Node.

A fault-injection test temporarily prepended `throw new Error("TEST INJECTED permanent SMP worker failure")` to a copied `search/smp_worker.js`, leaving both the original and modified deliverable sources untouched. The predecessor responded to `uci` / `isready`, but exited with code 1 and **no bestmove** when issued `position startpos; go depth 2`. The stderr trace showed an unhandled `SMP worker 0 exited before ready` rejection.

## Patch and green case
`uci/main.js` catches async search failures, emits one warning and a **legal fallback** move (or `bestmove 0000` at a terminal position). `search/smp.js` clears active search bookkeeping on worker-pool admission failure before rethrowing for UCI handling.

With the same permanently failing worker fixture, the modified UCI stayed alive, emitted `bestmove a2a3` twice in consecutive start-position searches, then exited normally on `quit` (exit code 0). A black-to-move checkmated FEN similarly yielded `bestmove 0000` twice, without a process crash.

## Normal-path tests (Linux / Node.js 22.16.0)
- Move-generation checks: **36/36 PASS**.
- Perft checks: **25/25 PASS**.
- Six-position depth-9 benchmark: **219,323 nodes**, same as predecessor; same per-position nodes and best moves.
- Six-position depth-10 benchmark: **286,029 nodes**, same as predecessor; same per-position nodes and best moves.
- Two-thread UCI depth-8 on 3 positions: **3/3 PASS**.
- Real-worker UCI stop validation: **PASS**.
- Patch applies cleanly to the 11:05 predecessor and yields byte-identical modified files.

Timing data was not treated as a speed benchmark, and there was **no equal-time match or Elo measurement**.

## Limitations and decision
**Verified bounded correctness candidate** for the injected worker-startup failure, not production-ready. Startup failure is intentionally injected, not known to be occurring in normal Windows deployments. Previous SMP changes remain unmerged. No matched authoritative TypeScript port, Windows/Node 20/24 validation, or strength test yet. Preserve the preceding research checkpoint and patch sequence.

Patch: [uci-worker-failure.patch](uci-worker-failure.patch). Complete modified compiled-JavaScript source, original source, raw logs and fault-injection test are in the corresponding downloadable local run archive.
