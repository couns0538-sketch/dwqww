# Forge 6.4 strength research — 2026-10-19 21:15 CEST

Status: RESEARCH ONLY; no source changes, compilation, benchmark or A/B match in this stage. Proposed experiments are falsifiable, not demonstrated improvements.

## Provenance / freshness
- Accepted development branch: `forge/6.4-hourly-20261019`, verified GitHub HEAD `9108d012526be80c6d163f7cab684e6acd9abf8d` (identical to last accepted SHA; no newer main commit).
- 21:00 bug investigator: `forge/audit-rule50-tt-bypass-20261019-2100` exists, but its GitHub report was missing (404); reviewed its supplied local report only. That report narrows *previous* rule-50 TT concern to qsearch cutoffs and TT-derived evaluation; source re-checked here. Do not imply GitHub synchronization.
- 20:45 lead: `forge/candidate-tt-snapshot-20261019-2045/validation/hourly/2026-10-19-2045/STATUS.md` is published; describes model-tested TT snapshots/striped locks, not modified engine source.
- 20:30 tester: supplied local TSan reproductions of TT read/write race; full engine remained untested. 20:15 research GitHub report absent.
- Prior ledger: `validation/release-6.0.0/EXPERIMENTS.md` (43 recorded experiments, including fixed-node SPRTs and rejected time-manager constant changes), `engine-improvement-log.md`, `RELEASE_STATE.md`. `validation/hourly/STATE.json` is stale (last updated 13:21 UTC) and cites older `24cc2cce`; do NOT use as accepted head.
- Avoid rerunning previously rejected single-parameter searches without new causal evidence.

## 1 — P1 correctness prerequisite: rule-50 TT score-policy mismatch (FIRST)
**Hypothesis.** Position-keyed TT bounds/search scores from a low halfmove clock can distort evaluation/cutoffs in near-draw states; main search guards *direct* TT cutoffs at halfmove >= 90, but quiescence TT cutoffs and both TT-score substitutions into corrected evaluation lack that guard. Raw static evaluation cache is position-based and should be considered separately from cached search scores.

**Exact anchors:** `src/search.cpp:686-713` (qsearch bound return and replacement of static eval); `src/search.cpp:808-834` (main-search direct cutoff guard and TT-derived eval); `src/board.cpp` `compute_key()` and FEN halfmove initialization. No production fix authorized in this research stage.

**Experiment:** In disposable worktrees, instrument each TT score *use* by [position key, halfmove clock, bound, depth, score, caller]. Build legal reversible non-terminal FEN pairs (e.g. clocks 0/90/98/99) from a frozen corpus; verify identical keys and varying halfmove clocks. Use Threads=1, disable OwnBook and clear Book File. Compare fresh-hash and warm-hash UCI scores and PVs at fixed depth, then compare to a direct rule-50-aware reference. For targeted ablation, independently suppress (a) qsearch TT score cutoff, (b) qsearch score-as-eval, (c) main score-as-eval when halfmove >=90; keep TT move ordering and position-only raw eval unchanged. If no effect after targeted instrumented triggers, report a negative finding, not a bug fix.

**Regression:** 4/4 CTest, three canonical perfts, stable legal PV/terminal mate and rule-50 outcomes, no warm/cold material divergence on demonstrated oracle cases; bench 11 baseline 417491 nodes is a reference for unchanged-engine runs, not a strict target after a behavior fix. ASan/UBSan + independent diff review. Only once correct, pair 10+0.1 fastchess with fixed openings, hashes, clocks and paired colors (SPRT elo0=0, elo1=5).

**Failure modes:** False improvement caused by comparing non-identical history or root Hash states; over-restricting valid TT scores, reduced TT efficiency/NPS; confusing raw evaluation with history-dependent search bounds; unrelated concurrency races if Threads>1. **Disproof:** no actual context-dependent score reuse affects any searched position under instrumented cold/warm tests, or ablation fails the legal reference.

## 2 — P1 SMP correctness/performance: TT coherent snapshots (EXISTING candidate, validation only)
**Hypothesis.** Shared mutable 16-byte entries read through `TTEntry* probe()` race with `store()`; by-value snapshots with coherently locked reads and writes eliminate races, but contended locking could reduce SMP NPS/Elo. Do not duplicate 20:45 candidate implementation.

**Exact anchors:** `include/forge/search.hpp:60-107` TT entry/probe pointer; `src/search.cpp:195-237` probe/store; `src/search.cpp:686-689,808-817` dereference after probe. Existing isolated candidate: `forge/candidate-tt-snapshot-20261019-2045` checkpoint, full patch in lead's archived handoff.

**Experiment:** Independent actual-engine ThreadSanitizer on baseline Threads=2/4, then separately build candidate and repeat contention, clear/resize/new_search lifecycle and hashfull probes. Enforce TSAN zero data races, perft, UCI/ponder, bench, and paired 1/2/4-thread NPS. Search-result parity only required in Threads=1; SMP roots are naturally nondeterministic. Then time-controlled paired SPRT (only if no regressions).

**Failure modes:** Locking stale pointer after lock release, deadlock on resizing, generation_/hashfull unguarded access, loss of replacement quality, mutex convoy/cross-core penalties. **Disproof:** no baseline race in full-engine TSAN with actual conflicting accesses or alternative patch does not fix them; performance may still reject otherwise-correct candidate.

## 3 — P2 potential equal-time Elo: root effort stored by move-order index (DIAGNOSTIC first)
**Hypothesis.** `root_move_nodes_[move_count-1]` accumulates effort across iterative deepening even though move ordering can change. `root_best_index_` is an ordinal for the current iteration; `root_move_nodes_[root_best_index_]/local_nodes_` may therefore include effort spent on *different* moves, distorting the soft-stop factor.

**Exact anchors:** `src/search.cpp:1046-1062` per-root-move accounting and best index; `src/search.cpp:1239` array initialization; `src/search.cpp:1298-1311` time-management effort factor; root MovePicker in same file.

**Experiment:** Trace [depth, search retry, ordinal, Move UCI, node delta], compute current ordinal-based factor versus stable Move-keyed factor at each completed iteration. Freeze a representative tactical/time-managed corpus with 10+0.1 and Threads=1. Only if factor differs on changed ordering implement minimal move-keyed accounting separately, verify no changes to `go depth/nodes` output, and measure clock allocation, time losses and paired 10+0.1 SPRT.

**Failure modes:** More expensive per-node bookkeeping, aspiration retry double counting, changing stop decisions without positional benefit, premature stop on tactical reversals. **Disproof:** root order never changes in reachable measured states, or factor/stop decisions never differ despite order changes. Prior `TmSoftDivisor=18` 200-game negative test is a different intervention and must not be reused as evidence for this mechanism.

## Handoff to independent tester :30 / lead :45
First request: inspect baseline TT scores in rule-50 contexts; report actual-engine reproduction or explicit BLOCKED. In parallel, validate the existing snapshot candidate but do not merge. Preserve raw UCI/TSAN logs, binary and source SHA-256, commands, FENs, opening-pair IDs, original match PGNs/console files and resume pair checkpoint. Do not start a match without a reproducible build and predeclared SPRT protocol. **Elo measured this cycle: none.**