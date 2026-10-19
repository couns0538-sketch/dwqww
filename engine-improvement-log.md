# Forge improvement log — 5.31.0, 2026-10-09

Validated immediate source: 5.30.0 SHA-256 `fd2f0d249b78bc353bc3a439464be0c4aec7a01eb1664f2c923f985aef74d0d7`. Current run examined 10 deterministic MIT Forge corpus positions at interior depth 9 with three score-boundary windows each, comparing the exact frozen baseline against an isolated no-LMR reference. One position (Forge-2, `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1`) showed 3/3 discrepant boundary scores: baseline 52/53/54, no-LMR 53/54/55 around depth-8 center +54. An independent full-window probe returned depth-9 +57 with baseline LMR and +62 without LMR. The proved problem is an LMR-dependent false fail-low relative to full-depth boundary search, not a measured gameplay loss. Two new baseline-failing regression assertions and adjacent board-state check establish the fix.

The one selected change lifts the late-quiet LMR gate from depth 9 to 10; depth-10+ and other heuristics were not retuned. The immediate fixed-depth shallow suite is identical, deep nodes increase 10.22%, and timings are mixed. No Fastchess A/B, SPRT, NPS/Elo, physical Windows/Ryzen or external opponent strength claim is made. Future depth-10+ LMR and verified null probes remain independent.

---

# Forge improvement log — current cycle 2026-10-09

## Source lineage and overlap

Immediate baseline 5.29.0 archive SHA-256 `8de2079347384e029f8819ed71b98b5aae1fbbb5ac8e870fe1e604c52a330944`.
The ZIP CRC and 842-entry source hash manifest match. This is the newest fully
validated source archive accessible in this run. Other available packages contain this
same version or rejected experiments; no newer validated lineage was found. No evidence
of a concurrent implementation in the available artifacts, though remote concurrency
cannot be excluded. Baseline recompiled before edits with strict GCC, Clang, and ASan+UBSan.

## Ranking and objective

| Priority | Backlog | Item | Status and why | Impact/confidence/cost |
|---|---|---|---|---|
| A1 | Correctness | False root mate when empty `searchmoves` intersects a nonterminal in-check position | OBSERVED on 5.29.0; fixed/tested in 5.30.0 | High protocol integrity / certain / small, bounded tests |
| A2 | Correctness | Depth-9+ LMR false bound | HYPOTHESIS; historical shallower errors corrected; fresh reproducer required | Potential high tactical impact / medium-low confidence / high differential test cost |
| A3 | Correctness | Depth-6+ verified null and zugzwang contexts | HYPOTHESIS; require frozen corpus, no production threshold changes now | High potential / unproven / high validation cost |
| A4 | Correctness | Repetition fingerprint, TT history and stop/ponder regressions | PROTECTION: historical fixes preserved; no new failure reproduced | Severe if reopened / historically validated / regression checks |
| B1 | Strength | Bit-exact evaluator parameterization, before tuning | OPPORTUNITY / engineering prerequisite | High tuning leverage / good confidence in parity feasibility / moderate cost |
| B2 | Strength | Licensed held-out Texel-style tuning, separate weight-only candidate | OPPORTUNITY, requires data provenance and held-out metrics | Plausible Elo / uncertain gain / high data and match cost |
| B3 | Strength | Capture then continuation history independently | OPPORTUNITY; old color-history trial rejected after opposing 200/400-game results | Medium possible / uncertain / A/B cost |
| B4 | Strength | Soft/hard clock policy | OPPORTUNITY; time-control sensitivity | Medium possible / medium risk / long A/B |
| B5 | Strength | Replacement-aware clustered TT | OPPORTUNITY; prior candidate negative/inconclusive | Medium possible / high collision and cache risk / expensive |
| B6 | Strength | Calibrated external engine ladder | MEASUREMENT GAP, not Elo feature | Essential for superhuman claim / significant compute and licensing |

## Single causal change and provenance

5.29.0 reproduced `go depth 1 searchmoves a1a8` from
`4r2k/8/8/8/8/8/8/4K3 w - - 0 1` as `info depth 1 score mate 0 ... bestmove 0000`.
The legal root list had check evasions. `Searcher::alpha_beta` had filtered it before
classifying an empty list as checkmate. Correcting the terminal test to run before
restriction preserves the actual game state. When only the requested intersection
is empty, it returns neutral no-result; `Searcher::search` marks the result and UCI
reports `info string searchmoves restriction has no legal root moves`.

Engine behavior files: `src/search.cpp` (`Searcher::alpha_beta`, `Searcher::search`),
`include/forge/search.hpp` (`SearchInfo.restricted_root_empty`). Tests:
`tests/tests.cpp` (direct status/score/PV, genuine terminal, TT cold/warm, board/key/
reversible-history/clock/legal moves) and `tools/uci_regression.py` (protocol output).
The added process regression fails on unchanged 5.29.0; it passes on 5.30.0. No
LMR, null-move, evaluator, transposition-key, time-management or threading heuristic
was changed. This priority outranks speculative Elo features because it was reproduced,
low-risk and breaks protocol analysis semantics.

## Validation and outcome

Strict C++20 GCC 14.2 and Clang 17 -O3 -Wall -Wextra -Wpedantic -Wconversion
-Wshadow -Werror, plus Clang 17 -O1 ASan+UBSan: 4/4 CTest each (engine,
match-tool, UCI and ponder). Baseline same. Perfts exactly
119060324 / 4085603 / 674624. Deterministic 4-case shallow and deep search:
908968 and 11713955 total nodes respectively, identical depths/scores/bestmoves/PVs.
CPU0-pinned three-run interleaving on AMD EPYC 9V74 shared VM, baseline/candidate
median shallow 490.388/498.947 ms (+1.75%), deep 7863.258/7718.584 ms (-1.84%).
No meaningful speed claim; ordinary play was not measurably changed. Pinned Fastchess
baseline A/A 4 pairs scored 50% with all eight games normal, pentanomial [0,0,4,0,0].
No A/B SPRT performed; fix accepted for confirmed protocol correctness, not Elo.
Windows LLVM-MinGW Zen 4 PE-verified, not Windows-runtime-tested.

**Decision: ACCEPT 5.30.0 as correctness fix only, contingent on frozen-archive
re-extraction, rebuild/retest, and reproducible Windows PE/checksum validation.**
Preserve independent source artifacts and evidence without modifying old 5.29.0.

## Next independently testable objective

Stage A of the coding-agent plan is closed. Next run: **validation-only depth-9+ LMR
differential screen**, first predeclare corpus and reference modes (current, no extra
history-conditioned reduction, no LMR), full-window/boundary comparisons and
compilers/sanitizer replication. Do not modify production reduction thresholds without
a current reproducible wrong bound; return a negative/inconclusive result if none appears.
After that separately screen depth-6+ verified null pruning and set up bit-exact
evaluation parameterization, then held-out licensed-data tuning and SPRT.
