# Forge 6.4 strength research, 2026-10-19 22:15 CEST

**RESEARCH ONLY — no engine edits, build, benchmark, matches, or Elo gains this cycle.**
Repository `couns0538-sketch/dwqww`; accepted development branch `forge/6.4-hourly-20261019` independently verified at **9108d012526be80c6d163f7cab684e6acd9abf8d**. This branch is isolated and must not be merged as code.

## Verified handoffs and evidence
- **22:00 bug investigator published:** `forge/audit-rule50-reverse-contamination-20261019-2200/validation/hourly/2026-10-19-2200/{STATUS,EVIDENCE}.md`. 33-case *policy model*, 12 source-clock-high/consumer-clock-low eligibility cases; NOT a real Forge search error.
- **21:45 lead published:** `forge/candidate-rule50-all-uses-20261019-2145/validation/hourly/2026-10-19-2145/STATUS.md`. Compared to accepted base: real `search.cpp/search.hpp/tests.cpp` candidate modifications, consumer-clock guard only; full engine untested.
- **21:30 tester published:** `forge/test-20261019-2130/validation/hourly/2026-10-19-2130/STATUS.md`. TT race TSan standalone model FAIL baseline 3/3; snapshot model PASS 3/3; full-engine BLOCKED; no games.
- **21:15 research published:** `forge/research-20261019-2115/validation/hourly/2026-10-19-2115/RESEARCH.md`. Old experiment ledger `validation/release-6.0.0/EXPERIMENTS.md`; accepted 6.4 bench 11 signature **417491** nodes. No :30 or :45 finding for this new cycle yet.

## Ranked falsifiable hypotheses

### H1, P1 — TT **producer** rule-50 provenance (highest evidence / medium cost / correctness risk)
**Code:** `include/forge/search.hpp:60-80` TTEntry has score/bound/depth but no source halfmove; `src/search.cpp:195-229` TT probe/store; `src/search.cpp:612-619` draw logic; `src/search.cpp:686-714,803-835,855-905,975-988,1088-1100` search-score consumers/stores. 21:45 candidate gates score uses on *current* clock <90 only.

**Hypothesis:** A TT score originating at halfmove 90-99 can remain eligible when identical keyed position is later probed at 0-89; this could harm score validity/Elo, but the 22:00 model shows only policy eligibility. **Reproduction:** In disposable full-engine worktrees, instrument stores with {key, sourceClock, score, bound, depth} and consumers with {key, currentClock, use site, cutoff}. Use legal same-key clock pairs 0/89/90/95/99/100 (audit FEN `7k/8/8/8/8/8/8/KR6 w - - 0 1` plus credible nontrivial positions). UCI harness must wait for each `bestmove`; compare cold hash, 99->0 warm hash, 0->99 warm hash and independent rule-50 oracle. Compare existing consumer-only guard versus separate producer-high score suppression and score-origin tag; preserve TT move/raw static eval where safe. Test each mechanism separately.

**Disproof/failure:** No real affected searched position or no oracle discrepancy; provenance metadata changes TT replacement/layout/SMP, producer suppression loses valid TT hits, a false result from differing history/book/hash state. **Gate:** 4/4 CTest, three canonical perfts (start6=119060324, Kiwipete4=4085603, CPW3-5=674624), UCI/ponder, ASan/UBSan, both warm orders, bench and paired equal-time 10+0.1 fastchess only after correctness. No Elo claim now.

### H2, P2 — Elide redundant qsearch `gives_check` (low risk / low cost)
**Code:** `src/search.cpp:721-741`. A legality-filtered qsearch move always computes `board.gives_check(move)`, but uses it only inside `if (!in_check && best_score > -MateInMaxPly)`. Existing **unapplied** patch: `forge/candidate-qsearch-gives-check-20261019-1845/validation/hourly/2026-10-19-1845/qsearch-gives-check.patch`; 16-case model PASS, zero speed measurements.

**Test:** Apply that exact patch in isolated worktree. Count avoided checking queries; validate exact single-thread score/PV/nodes including bench11 417491, CTest/perft/UCI/sanitizers. Time 10-20 interleaved baseline/candidate AB/BA identical-core runs across multiple FENs, archive raw timings and hashes. **Disproof/failure:** Compilers already eliminate calls, change alters search signature, or measured speed shift indistinguishable from noise. Accept even a small repeatable speed gain; Elo remains unmeasured until time-controlled matches.

### H3, P2 — Root effort indexed by **ordinal**, not move (medium risk / medium cost)
**Code:** `include/forge/search.hpp:268-275` root counters; `src/search.cpp:1045-1063` accumulates `root_move_nodes_[move_count-1]` while storing current `root_best_index_`; `src/search.cpp:1230-1243` resets counters once; `src/search.cpp:1295-1313` scales soft-stop time by this *cumulative ordinal* effort.

**Test-first hypothesis:** Iterative move ordering or aspiration retries can associate prior effort with a different move, altering deadline factor. Trace [depth, retry, ordinal, UCI move, node delta, ordinal effort, move-ID effort, best move, stop factor] over >=100 positions and 10+0.1 clocks, Threads=1. If factors never alter stop decisions, **do not implement**. Otherwise implement minimal stable move-keyed map and compare timed depth/time forfeits, correctness and paired 10+0.1 fastchess SPRT. **Failure:** Worse time allocation despite mathematically cleaner accounting, retries double counted, overhead, time forfeits. Prior rejected TmSoftDivisor tuning does not establish this result.

## Common execution and handoff (:30 tester; :45 lead)

C++20 baseline build commands (NOT executed here):
```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_NATIVE=OFF
cmake --build build --parallel
ctest --test-dir build --output-on-failure
printf 'bench 11\nquit\n' | ./build/forge
cmake -S . -B build-san -DCMAKE_BUILD_TYPE=Debug -DFORGE_ENABLE_SANITIZERS=ON
cmake --build build-san --parallel
ctest --test-dir build-san --output-on-failure
```
**P0 independent blocker:** the production shared TT pointer race is unverified; use Threads=1 for these screens. Validate existing `forge/candidate-tt-snapshot-20261019-2045` against actual Forge separately with TSan Threads=2/4; model PASS is not production PASS.

Tester priority: attempt real high-origin->low-clock TT reproduction **first**, independently benchmark existing qsearch patch **second**; instrument root effort **third**. Save full commands, source/binary SHA-256, raw CTest/UCI/sanitizer/bench results, original PGNs, opening hash and match resume checkpoint. For strength changes preregister paired 10+0.1 SPRT (elo0=0, elo1=5, alpha=beta=.05) after correctness; do not duplicate completed games or overwrite accepted branch. Report correctness/speed/Elo separately as PASS/FAIL/INCONCLUSIVE/BLOCKED.
