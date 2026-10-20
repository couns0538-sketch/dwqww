# Forge 6.4 research checkpoint — 2026-10-20 02:15 CEST

Research-only document; no engine changes, matches, or Elo/speed claims.

**Pinned source**: `couns0538-sketch/dwqww` development branch `forge/6.4-hourly-20261019`, SHA `2fc649effb6d2f09f4fdf63b44d59283fe26b616`. Original 6.4 release SHA `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`. Last engine source change was TT-tag commit `9108d012526be80c6d163f7cab684e6acd9abf8d`. Neither baseline is changed here.

**Agent freshness**: 02:00 bug-investigator finding not published as a unique checkpoint. Last verified bug finding is [2026-10-19 23:57](https://github.com/couns0538-sketch/dwqww/blob/forge/audit-20261019-2357-review/validation/hourly/2026-10-19-2357/BUG-STATUS.md): no new production bug validated, actual engine tests blocked. Latest independently published [research 00:15](https://github.com/couns0538-sketch/dwqww/blob/forge/research-20261020-0015/validation/hourly/2026-10-20-0015/STATUS.md) and [tester 00:30](https://github.com/couns0538-sketch/dwqww/blob/forge/test-20261020-0030/validation/hourly/2026-10-20-0030/TESTER-STATUS.md). Research 01:15 and tester 01:30 branches contain no separate publication. Prior TT-tag 10+0.1 match ended in a Candidate time forfeit after 3 completed pairs; no usable Elo result. Ten cold replay summaries were normal, but one associated detailed transcript was incomplete. Separately, a hosted NNUE performance trial failed same-binary A/A timing calibration and never reached candidate A/B.

## Ranked falsifiable experiments

### P0 — Time-control robustness under warmed TT and competing workloads
**Hypothesis:** Under 10+0.1 clocks a delayed hard-limit poll or output handoff might contribute to candidate-only timeout, rather than an overloaded host. **Unproven**.

**Code:** `src/search.cpp:561-590` elapsed time and should_stop; `src/search.cpp:674-676,778-780` stop polling; `src/search.cpp:1111-1153` soft/hard allocation; `src/search.cpp:1230-1315` iterative and time management; `src/uci.cpp:320-365` worker creation. All at pinned SHA.

**Test:** Recover actual frozen binaries and time control, verify hashes, then independently preregister 30 paired searches per serial / concurrency-2 / concurrency-6 scenario with warmed hash and controlled openings. Capture UCI input, clock, bestmove output, stop latency, process outcomes and resource usage. Keep the prior failed trial separate. **Falsifier:** no candidate-specific overrun under controlled conditions or issue attributable solely to host scheduling. **Failure modes:** shared CPU starvation, stale clock/ponder state, buffering, incorrectly reproduced game history. **Gate:** exact UCI/ponder, no illegal moves/forfeits, CTest 4/4, reference perfts, sanitizers; a replacement equal-clock 0/+5 Elo fastchess SPRT only on a stable host using a new frozen protocol and genuine H1 acceptance.

### P1 — Rule-50 contextual TT score reuse in qsearch
**Hypothesis:** A bound written near the 50-move threshold can wrongly influence the same position at a different halfmove clock. A prior model established possible reuse eligibility, not an actual mis-searched position.

**Code:** `include/forge/search.hpp:60-80` stores score/bound/depth but no originating halfmove; `src/search.cpp:678-715` qsearch TT cutoff and stand-pat reuse; `src/search.cpp:800-845` main cutoff has a consumer-clock <90 guard but eval score substitution does not; `src/search.cpp:1083-1100` TT storage.

**Test:** Full-engine one-thread trace for matching legal positions at clocks 0, 89, 90, 95, 99, 100: record producer clock, consumer clock, bound, score, cutoff, and compare cold versus both high-to-low and low-to-high warm-hash orders to independent rule-50 oracle. Check pre-existing isolated `forge/rule50-context-20261019` candidate first; do not reimplement prior 6.4.4 repair. **Falsifier:** no actual invalid score use or decision after legitimate history effects are isolated. **Failure modes:** repetition-dependent score, checkmate precedence, TT replacement, lost legitimate hits, SMP races. **Gate:** all 4 CTest, canonical perfts 119060324/4085603/674624, UCI/ponder, ASan/UBSan, 1T controlled regression; strength SPRT only after P0 safety.

### P2 — Measure existing NNUE fused dirty updates
**Hypothesis:** Already implemented order-preserving quiet/capture accumulator fusion reduces whole-engine CPU time, but benefit may be too small or offset by code size. No speed/Elo result is established.

**Code:** `src/nnue.cpp:57-111` accumulator update; `src/nnue.cpp:169-193` dirty list (captures, promotion, castling, en passant). Existing isolated source: 6.4.9 `4edda780c68a742f20565d4e6a54a0c99a2c88a6`, 6.4.10 `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`, 6.4.11 `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`. [Existing capture fusion evidence](https://github.com/couns0538-sketch/dwqww/blob/forge/nnue-capture-fusion-20261019/validation/nnue-capture-fusion-20261019/HYPOTHESIS.md). A source traffic estimate of 11 KiB to 5 KiB per capture is not NPS.

**Test:** Complete remaining candidate sanitizer/Windows gates; verify original network and full source hashes; predeclare a new A/A calibration at fixed same-core workload, abort if noisy. Only then paired ABBA/BAAB whole-process CPU and wall comparisons 6.4.10 vs 6.4.11 (marginal) and 6.4.9 vs 6.4.11 (combined); verify exact per-position moves, scores, PVs, nodes, NNUE accumulator bytes. **Falsifier:** failed calibration or repeatable whole-engine speed at/below noise; negative speed also disproves. **Failure modes:** compiler already optimized, capture rarity, cache instruction pressure, altered float association. **Gate:** strict `-ffp-contract=off`, exact behavior, CTest/perft/sanitizer, calibrated performance, and only afterward equal-clock SPRT if appropriate.

## Tester (:30) and developer (:45) handoff
Tester: first look for newly published investigator finding; otherwise use the 23:57 verified checkpoint. Prioritize P0 timeout mechanism and P1 actual rule-50 reproduction; only use P2 if a calibrated host is available. The isolated OwnBook=false candidate requires its separately prepared three-state real-UCI check. Record exact tests and negative findings without inventing a pass. Developer: preserve current integration and independent candidates; do not redo 6.4.6 qsearch guard, 6.4.7 check masks, 6.4.8 root-effort map, or 6.4.10/6.4.11 NNUE changes. Promote only measured, regression-verified improvements. Status: P0 diagnostic pending; P1 actual-engine falsification pending; P2 performance inconclusive. **No Elo or speed gain claimed.**
