# Forge 6.4 lead integrator - 2026-10-19 21:45 CEST

Status: **ISOLATED CANDIDATE / INCONCLUSIVE - DO NOT MERGE**. This checkpoint includes an actual source change in its candidate branch, unlike the prior TT-snapshot model checkpoint. No complete Forge checkout or executable was available in this runtime; this fix has NOT passed full-engine build, CTest, UCI, perft, bench, sanitizers or an equal-clock match.

## Provenance and handoffs

- Accepted branch: `forge/6.4-hourly-20261019`; accepted HEAD `9108d012526be80c6d163f7cab684e6acd9abf8d` (verified by Git refs API).
- :00 bug investigator: local 21:00 audit archive read and baseline guard model rerun (15 scenarios, 6 qsearch cutoff mismatches and 6 score-as-eval high-clock mismatches). Its audit branch exists but its GitHub report is absent: no synchronization assumed.
- :15 strength researcher: published `forge/research-20261019-2115` report, commit `56c90436f1f85de5cad0a762be75d50d6b71c247`.
- :30 tester: published `forge/test-20261019-2130` STATUS, commit `2b4d354ca9992caca738c86a53e9caa43e6c66c8`; isolated TT TSan candidate model PASS but no production build.
- Prior record: `validation/release-6.0.0/EXPERIMENTS.md` and `validation/hourly/README.md`. Old `validation/hourly/STATE.json` points to `24cc2cce` and must not replace accepted head.

## Ranked priorities

1. **P0 production SMP TT race**: isolated baseline TSan reproduction exists, candidate synchronized snapshot tested only in a model. Integration blocked until actual-engine 2/4-thread sanitizer, locking lifecycle and SMP performance; keep separate.
2. **P1 TT search-score cross-context reuse near rule50**: this cycle's bounded candidate. No actual FEN score corruption established.
3. **P1 qsearch stalemate**: requires isolated, true-engine reproduction and verified correction, avoid adding overhead without measurement.
4. **P2 root effort accounting**: measure per-move root effort before changing time management.

## Source change in THIS branch

A single helper `tt_score_reusable(halfmove_clock)` encapsulates the **existing** main-search threshold `clock < 90`. It is now applied to every identified use of TT **search scores** in qsearch and main search:

- qsearch direct TT bound cutoff;
- qsearch and main search TT-search-score substitutes for static evaluation;
- existing main direct TT bound cutoff (same pre-existing threshold);
- null-move TT upper-bound pruning hint;
- ProbCut TT-bound skip hint;
- singular extension's TT-score comparisons and derived beta.

Preserves TT hash-move ordering, raw static TT evaluation, and behavior below halfmove 90 at policy level. This is conservative rather than a complete proof of correct rule50-aware hashing; TT entries contain no halfmove context. The 90-ply heuristic does not solve every rule50 search-history dependency. Node counts and Elo can change at high clocks.

## Testing and gates

- Prior 21:00 guard predicate reproducer was rerun in GCC 14.2 normal and ASan/UBSan and passed. **Model only**.
- Added `test_tt_rule50_score_policy` to full Forge tests with same-key FEN clocks 0/99 and 89/90 boundary checks; **not run on full engine**.
- Added `rule50_consumer_model.cpp` as an independent compileable model; separate run evidence should be attached to this checkpoint.
- Requires independently established actual-position warm/cold UCI oracle, full Release CTest including canonical perft, UCI/ponder, ASan/UBSan and Threads=1 deterministic bench against inherited bench11 417491 reference. Since a behavior fix may change search paths, exact node counts are diagnostic not mandatory.
- Preserve actual opening file hash, both binary hashes and raw logs, then preregister paired equal-time 10+0.1 fastchess SPRT (elo0=0, elo1=5, alpha=beta=0.05) before claiming strength gains. No games started; no PGNs or Elo.

## Next :00 bug investigator

Independently check ALL TT-score usages after this patch (qsearch, eval substitution, null move, ProbCut, singular extension); investigate whether rule50-high-clock entries can contaminate low-clock probes even with current gating and whether TT stores require context tagging. Also check SMP TT table resize/clear while worker threads are active. Verify real production code, not only models.

## Resumption

Start from accepted SHA 9108d012526be80c6d163f7cab684e6acd9abf8d. Compare this candidate branch; do not merge. Recover this experiment and test on a disposable full checkout; retain all raw outputs. Branch is intentionally isolated to prevent conflicts with the TT-snapshot proposal.
