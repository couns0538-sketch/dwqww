# Changelog

## 6.0.0 - 2026-10-12

Strength release. The move generator, search and evaluation were rewritten; the
5.x correctness philosophy of refusing reductions that change zero-window bounds
is replaced by a modern pruning/reduction search validated by match results.

- Board: magic bitboard sliding attacks, bitboard pawn/knight/king generation,
  incremental checkers, `is_pseudo_legal` validation for hash moves,
  `gives_check`, x-ray `see_ge`, repetition detection that counts a single
  repetition inside the search tree. Perft runs at roughly 130 Mnps.
- Search: PVS with aspiration windows; 16-byte TT entries in 4-way clusters
  with generation aging and stored static evaluation; staged move picker with
  SEE-filtered captures, killers, countermove and history-ordered quiets (checks
  first); butterfly, continuation (1/2/4 ply), capture and correction
  histories; LMR, LMP, futility, reverse futility, razoring, SEE and history
  pruning; null move with adaptive reduction and verification at depth 14+;
  ProbCut; IIR; singular extensions with double/negative extension and
  multi-cut; safe-check extensions; quiescence search with TT, futility and
  SEE pruning; soft/hard time management with best-move stability and
  node-effort scaling. The engine reaches depth 20+ in a few seconds from the
  starting position; 5.31.0 reached depth 9.
- Evaluation: tapered PeSTO piece-square tables plus mobility, hashed pawn
  structure, passed pawns, king shelter/storm and attack-unit danger with safe
  checks, threats, outposts, rook files, bishop pair and endgame scaling. All
  terms are entries of one parameter table (`src/eval_params_table.inc`) with a
  coefficient trace for tuning.
- Tuning: `tools/tune/extract.cpp` and `tools/tune/texel.cpp` (multi-threaded
  Adam with rarity-scaled steps and regularisation). The shipped table was fitted
  on 22,000 self-play games (1.72M quiet positions); at fixed nodes it scores
  68.0 % (300 games) against the hand-set table.
- UCI: `bench [depth]` command; `movestogo` is no longer assumed to be 30 when
  absent (increment time controls allocate from the remaining clock).
- Tests rewritten around behaviour (perft, make/unmake and hash consistency,
  pseudo-legality, SEE, evaluation symmetry, transposition table, tactical
  cases, searchmoves/terminal roots); the UCI regression no longer pins
  evaluation-specific centipawn values.
- Strength against Stockfish 19 (`UCI_LimitStrength`, `UCI_Elo 2800`, 10+0.1,
  one thread, Hash 64, 8moves_v3 openings): 5.31.0 scored 10.0 % over 20 games;
  6.0.0 before tuning scored 57.5 % over 100 games. See
  `validation/release-6.0.0/` for the final tuned-engine results.

## 5.31.0 - 2026-10-09

- Fixes a reproduced depth-9 LMR false fail-low on `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1`. Unchanged 5.30.0 returns 53 for depth-9 interior [53,54] and 54 for [54,55]; a no-LMR full-depth reference returns 54 and 55 respectively. Depth-9 full-window scores differ (baseline +57, no-LMR +62), but the zero-window discrepancy is the focused bound regression.
- The only search change is in `Searcher::alpha_beta`, raising the LMR depth floor from 9  to 10. `tests/tests.cpp` checks both boundary windows and board/FEN/key/reversible-context  restoration with parent null pruning disabled to isolate LMR. The added tests fail on unchanged 5.30.0 and pass on 5.31.0. Root TT context, searchmoves, mate, pondering, SEE, null-move, qsearch, and legal move generation are preserved.
- GCC 14.2, Clang 17, Clang 17 ASan+UBSan compile under strict C++20 -Werror and pass all 4 CTest groups. Extended UCI protocol, mate, searchmoves, stop/ponder, options, transactional position handling and reference perfts (119060324/4085603/674624) all pass.
- Seven CPU0-pinned interleaved baseline/candidate pairs: shallow total nodes 908968 both, median aggregate time 490.824 → 480.926 ms; deep total nodes 11713955 → 12911443, median 7841.932 → 8458.033 ms. All eight position scores and best moves unchanged. Extra nodes are expected correctness work, not a speed or Elo improvement.
- Windows AMD64 PE target Ryzen 9 7950X3D/Zen 4 via pinned LLVM-MinGW with -O3, ThinLTO, -march=znver4, -mtune=znver4, static C++ runtime; PE-verified, not Windows-runtime-tested.

## 5.30.0 - 2026-10-09

- Fixes a reproduced false-checkmate report when `searchmoves` has no legal intersection in a nonterminal in-check root. Unchanged 5.29.0 printed `info depth 1 score mate 0` on `4r2k/8/8/8/8/8/8/4K3 w - - 0 1` with `go depth 1 searchmoves a1a8`, despite legal White evasions. This affected UCI analysis trust but not ordinary unrestricted play.
- In `Searcher::alpha_beta`, evaluates the unfiltered legal root list for real mate/stalemate before filtering requested root moves; an empty intersection returns neutral non-mate score. `Searcher::search` publishes `SearchInfo.restricted_root_empty` and a single `info string searchmoves ...` diagnostic when needed. Restricted roots continue to avoid TT bound publication. Normal search/evaluation and pondering remain unchanged.
- Adds C++ and process-level tests for in-check and quiet nonterminal empty intersections, real checkmate and stalemate, warm/cold TT isolation and immutable FEN/key/history/clock/moves. Existing interrupted permitted-root and historical regressions pass. Baseline 5.29.0 demonstrably fails the new UCI regression.
- Strict GCC/Clang warnings-as-errors and Clang ASan+UBSan builds pass all 4 CTest groups each. Three reference perfts remain 119060324 / 4085603 / 674624. Three interleaved CPU0 search benchmarks preserve all shallow/deep nodes, scores, moves and PVs. Shallow and deep median aggregate time deltas +1.75% / -1.84% are noisy diagnostics, NOT strength evidence. Fastchess baseline A/A: 4 pairs, 8 normal games, 50%.
- PE32+ Windows x86-64 Zen 4 executable built with the provenance-pinned MIT-compatible LLVM-MinGW/UCRT toolchain using -O3, ThinLTO, -march=znver4, -mtune=znver4, static C++ runtime. NOT tested on Windows or Wine. No A/B Elo gain or superhuman claim.

## 5.29.0 - 2026-10-09

- Adds functional UCI pondering with a `Ponder` check option, `go ponder`, `ponderhit`, and
  `bestmove ... ponder <legal predicted reply>` when a principal-variation reply exists.
- While pondering, Forge keeps analyzing without spending its own clock. `ponderhit` changes
  the in-progress search to a timed search using a monotonic atomic hit timestamp; before a hit,
  completion is never published. `stop` safely interrupts either kind of search.
- Adds focused and stress UCI regression coverage (terminal roots, restricted roots,
  time/clock/node limits, invalid option, 16 early-hit races, hit/miss, and predicted legality).
  Original 5.28.0 fails the new UCI feature test as intended.
- Strict GCC, Clang, ASan+UBSan, engine, match-tool, extended-UCI and required perft gates pass.
  Four paired fixed-depth benchmark repetitions preserve all scores/best moves/nodes.
  Fastchess 30 paired games without pondering score 27W/6D/27L (50.00%); the actual pondering
  strength effect remains **unmeasured**. No Elo or superhuman-strength claim.
- Delivers a genuine Zen 4-targeted PE32+ Windows executable via pinned LLVM-MinGW toolchain.
  Windows runtime has not been tested on native Windows or Wine. Multi-threaded search and
  an opening-book file remain absent; they are not advertised as available.

## 5.28.0 - 2026-10-06

- Fixes proven depth-8 late-move-reduction false fail-low results by raising the ordinary LMR depth floor from 8 to 9. Nominal depth-8 quiet late moves now search at full depth.
- Primary regression: `rn1qk1nr/ppp2p1p/3pb1p1/4p3/1bPP4/2N1P2N/PP3PPP/R1BQKB1R w KQkq - 0 1` changes from unchanged 5.27.0 full-window +38 / false fail-low +134 at `[134,135]` to nominal-depth +135 / +135.
- Independent regression: `rnbqkb1r/p2pp1pp/1p5n/2p2p2/3P1PP1/2P1B2N/PP2P2P/RN1QKB1R w KQkq - 0 1` changes from -22 / -19 to -18 / -18.
- GCC, Clang, and ASan+UBSan reproduce both baseline failures and corrected results; a broader diagnostic that also disables shallow late-move pruning returns the same nominal-depth results, isolating depth-8 LMR.
- Five CPU0-pinned interleaved runs preserve shallow benchmark signatures; deep nodes increase 8,062,226 -> 11,713,955 (+45.29%) and deep median time 4,817.760 -> 7,515.447 ms (+55.99%). No speed or Elo claim.

## 5.27.0 - 2026-10-06

- Fixes proven depth-7 late-move-reduction false fail-low results by raising the ordinary LMR depth floor from 7 to 8. Nominal depth-7 quiet late moves now search at full depth.
- Primary regression: on `r1bqkb1r/pp4pp/n1pp1n2/4pp2/P4P2/1P1P3N/2PBP1PP/RN1QKB1R w KQkq e6 0 1`, unchanged 5.26.0 returns -6 full-window and falsely fails low at -1 for `[-1,0]`; nominal-depth/no-depth-7-LMR search returns 0 for both, as does 5.27.0.
- Adds independent depth-7 coverage on `r1bqkbnr/pp2p1p1/2n2p1p/1B1p4/2pP4/N1P1PN2/PP3PPP/R1BQK2R w KQkq - 0 1`, changing +34 / false fail-low +37 to +38, plus board-restoration checks.
- Leaves depth-8+ LMR and its existing full-depth zero-window re-search on reduced improvement unchanged; null move, qsearch, TT/repetition identity, evaluation, move generation, timing, threading, and UCI grammar are unchanged.
- The exact 5.26.0 source archive was freshly revalidated before editing with strict GCC/Clang, ASan+UBSan, engine/match/UCI tests, and exact reference perfts. Stale inherited top-level 5.26 validation pointer/hash files were detected and excluded from baseline-identity evidence; 5.27 regenerates its own manifests from the frozen tree.
- Eleven CPU0-pinned interleaved benchmark runs preserve all tested scores/best moves; aggregate nodes increase 813,917 -> 908,968 (+11.68%) and median aggregate time 452 -> 494 ms (+9.29%). No speed or Elo claim.

## 5.26.0 - 2026-10-06

- Fixes proven depth-6 late-move-reduction false fail-low results by raising the ordinary LMR depth floor from 6 to 7. Nominal depth-6 quiet late moves now search at full depth.
- Primary regression: on `rnbqk2r/1p1ppp1p/5n1b/p1p3p1/2P5/BPN1P3/P2PBPPP/R2QK1NR w KQkq - 0 1`, unchanged 5.25.0 returns +77 full-window and falsely fails low at +128 for `[128,129]`; both no-LMR and no-LMR-plus-no-shallow-LMP references return +129, as does 5.26.0.
- Adds adjacent depth-6 coverage on `rnbqkb1r/pp5p/3p3n/2p1ppp1/2PP1B2/4P3/PP1NBPPP/R2QK1NR w KQkq - 0 1`, changing -37 / false fail-low +8 to the full-depth +9 result, plus board-restoration checks.
- Leaves depth-7+ LMR and its existing full-depth zero-window re-search on reduced improvement unchanged; null move, qsearch, TT/repetition identity, evaluation, move generation, timing, threading, and UCI grammar are unchanged.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Five CPU0-pinned interleaved comparisons show shallow aggregate nodes 498,923 -> 813,917 (+63.13%) and deep aggregate nodes 3,167,118 -> 5,909,935 (+86.60%). Median aggregate times were 394.485 -> 673.003 ms shallow and 2,822.817 -> 5,854.366 ms deep. Tested scores/best moves remain unchanged. No speed or Elo claim.

## 5.25.0 - 2026-10-06

- Fixes proven depth-5 late-move-reduction search misses by raising the ordinary LMR depth floor from 5 to 6. Nominal depth-5 quiet late moves now search at full depth.
- Primary regression: on `3r1bnr/1k1Pp1p1/p7/1p1n1p1p/8/2N3N1/PPPQ1PbP/2R1K2R w - - 1 22`, unchanged 5.24.0 returns +338 and falsely fails low at +472 for `[472,473]`; both no-LMR and no-LMR-plus-no-shallow-LMP references return +473 with `h1g1`, as does 5.25.0.
- Adds adjacent depth-5 coverage on `2rq1b1r/4p1p1/npk1bp1n/3p3p/pP1P1P2/4K1P1/P1P1P1BP/R2QB2R w - - 6 20`, changing -668 / false fail-low -409 to the full-depth -408 result with `b4b5`, plus board-restoration checks.
- Leaves depth-6+ LMR and its existing full-depth verification-on-improvement behavior unchanged; null move, qsearch, TT/repetition identity, evaluation, move generation, timing, threading, and UCI grammar are unchanged.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Five fully completed CPU0-pinned interleaved comparisons show shallow aggregate nodes 324,363 -> 498,923 (+53.82%) and deep aggregate nodes 2,578,920 -> 3,167,118 (+22.81%). Median aggregate times were 176.015 -> 270.161 ms shallow and 1,666.383 -> 1,961.804 ms deep. Search signatures change as previously reduced depth-5 branches are searched fully. No speed or Elo claim.

## 5.24.0 - 2026-10-06

- Fixes proven shallow late-move-reduction search misses by raising the LMR depth floor from 3 to 5. Nominal depths 3-4 now search quiet late moves at full depth.
- Exact depth-4 regression: on `r2qkbnr/ppp3pp/2np3B/4pp2/1P1P4/N1P2P1b/P3P1PP/R2QKBNR w KQkq - 0 1`, unchanged 5.23.0 returns +41 and falsely fails low at +232 for `[232,233]`; the no-LMR/exhaustive-shallow reference and 5.24.0 return +233 with best move `h6d2`.
- Adds adjacent depth-3 coverage on `rnbqkbnr/3p3p/pp2p1p1/2p2p2/2P2P2/N2P2PN/PP2P2P/R1BQKB1R w KQkq - 0 1`, changing -7 / false fail-low +14 to the full-depth +15 result, with board-restoration checks.
- Leaves depth-5+ LMR, very-late extra reduction, shallow late-move pruning, null move, qsearch, TT/repetition semantics, evaluation, move generation, and UCI behavior otherwise unchanged.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven CPU0-pinned interleaved comparisons show the expected cost: shallow aggregate nodes 217,134 -> 324,363 (+49.38%) and deep aggregate nodes 1,229,258 -> 2,578,920 (+109.79%). Several deterministic search signatures change. No speed or Elo claim.

## 5.23.0 - 2026-10-06

- Fixes proven shallow null-move false lower bounds by disabling null-move pruning at depths 3-5, where previous cutoffs were unverified.
- Exact depth-3 regression: on `r1bqkb1r/1p1pn1pp/n1p1pp2/p7/7P/N1PPBN2/PP2PPP1/R2QKB1R w KQkq - 0 1`, unchanged 5.22.0 returns beta +37 for zero-window `[36,37]` after one two-node null cutoff, while the full depth-3 score and the same window without null are +36. 5.23.0 returns +36.
- Adds a second depth-5 regression on `rnbqkbnr/1p3ppp/2p5/p2ppP2/1P6/B1N4N/P1PPP1PP/R2QKB1R w KQkq - 0 1`, changing the false -176 cutoff to the correct fail-low -177, plus board-restoration and null-cutoff assertions.
- Keeps null pruning active only at depth 6+, where the existing verification path is retained. The targeted 5.15 depth-5 floor is therefore superseded.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven interleaved CPU0-pinned comparisons show the expected extra work: shallow aggregate nodes 181,075 -> 217,134 and deep aggregate nodes 1,129,159 -> 1,229,258. Deep search signatures change on some positions. No speed or Elo claim.

## 5.22.0 - 2026-10-06

- Fixes a proven quiescence false in-window score for favorable quiet stalemates. On `5k1K/7P/8/8/8/8/8/8 w - - 0 1`, unchanged 5.21.0 has static evaluation +288 and no legal moves; qsearch `[0,388]` incorrectly returns +288 instead of the draw score 0.
- Extends the existing quiet-terminal probe only when zero can change the alpha-beta result: the original alpha is negative or stand-pat raised alpha above the caller's original lower bound.
- Adds a direct regression for the exact favorable-stalemate window and board restoration.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven interleaved CPU-pinned benchmark runs preserve all deterministic nodes, scores and best moves; mixed sub-percent timing movement is treated as host noise. No speed or Elo claim.

## 5.21.0 - 2026-10-06

- Fixes a proven false alpha-beta bound caused by reducing an entire zero-window depth-4 node to depth 3 when no TT move exists. On `rnbqkb1r/pp1pn1pp/2p5/3P4/2P1pp2/4B2N/PP2PPPP/RN1QKB1R w KQkq - 0 1`, full nominal depth 4 is +139; unchanged 5.20.0 falsely fails low at +138 for `[138,139]`, while 5.21.0 reaches beta +139.
- Removes only the `zero_window && depth >= 4 && !checked && no_tt_move` whole-node `--depth` shortcut. LMR, null move, late-move pruning, qsearch, evaluation, TT identity/context, repetition semantics, and UCI behavior are otherwise unchanged.
- Adds focused full-window/zero-window and board-restoration regression coverage. A 1,000-position diagnostic screen keeps all full-window depth-4 scores identical while the old shortcut changes 505 adjacent zero-window outcomes; this is consistency evidence, not a gameplay-frequency or Elo estimate.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven CPU0-pinned interleaved benchmark runs show the expected search-cost increase. No speed or Elo claim.

## 5.20.0 - 2026-10-06

- Fixes a proven shallow reverse-futility false lower bound. On `rnbqk1nr/pp3pb1/2p1p1p1/3p3p/2B3PP/1P2PP2/P1PP4/RNBQK1NR w KQkq - 0 1`, static evaluation is +17; unchanged 5.19.0 returns beta=-103 immediately for the depth-1 zero-window `[-104,-103]`, while a no-RFP search fails low at -104 and a full-window depth-1 search is -340.
- Removes only the `depth <= 2 && static_eval - 120 * depth >= beta` reverse-futility early return. Null move, LMR, late-move pruning, quiescence, TT identity/context, repetition semantics, and UCI behavior are otherwise unchanged.
- Adds a focused internal regression for the exact zero-window failure, full-window score, and board restoration. Updates the inherited shallow-null singleton score expectation from +1374 to +1471; the stronger combined root remains `g4g3 / +1498`.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven CPU0-pinned interleaved benchmark runs show the expected cost of searching previously cut nodes: shallow aggregate nodes 131,267 -> 160,684 and deep aggregate nodes 524,282 -> 794,411. No speed or Elo claim.

## 5.19.0 - 2026-10-06

- Fixes a proven qsearch false bound caused by hard material-delta pruning. On `r1b1k2r/Nppp1pp1/n6n/4p2p/Pb2P2q/5RP1/2PP1P1P/2BQKBNR b Kkq - 2 10`, unchanged 5.18.0 returns 296 for zero-window qsearch `[296,297]`; an otherwise equivalent no-delta reference and 5.19.0 return the correct fail-high 297.
- The causal capture `h4e4` has SEE=+100. With stand-pat 46, the old `stand_pat + victim + 150 <= alpha` test pruned it exactly at alpha=296 even though recursive qsearch reaches beta. The hard-delta discard and its now-unused victim-value plumbing are removed; no other search heuristic is intentionally changed.
- Adds focused internal regression coverage for the exact bound, board restoration, static evaluation and causal capture SEE.
- Strict GCC 14.2, Clang 17, and Clang ASan+UBSan test gates pass; GCC/Clang extended UCI suites preserve reference perfts 119060324 / 4085603 / 674624.
- Eleven CPU0-pinned interleaved benchmark runs show the expected search-cost increase: the standard four-position depth 6-7 suite grows 100,022 -> 131,267 nodes; all tested scores and best moves remain unchanged. No speed or Elo claim.

## 5.18.0 - 2026-10-06

- Fixes a proven qsearch false score caused by treating negative material SEE as a correctness proof. On the retained tactical FEN, unchanged 5.17.0 reports +1037 at depth 1 while an unpruned reference and 5.18.0 both return +689 with the same best move `g5d8`; the missing reply is `f8a3` with SEE=-10.
- Removes only the negative-SEE early skip from non-check quiescence. Hard delta pruning remains unchanged and is tracked separately.
- Updates the two older promotion-recapture regressions to assert score correctness and board restoration instead of requiring the removed optimization's exact one-node count. Adds direct qsearch, public depth-1, board-restoration, and SEE-classification regressions for the new fixture.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI suites, extended UCI lifecycle checks, and reference perfts pass. Eleven interleaved CPU0-pinned comparisons preserve tested scores/best moves but increase search nodes materially, so no speed or Elo claim is made.
- A deferred-negative-SEE ordering experiment was rejected: it preserved correctness but added SEE classification overhead and was slower in a five-run screen than the simpler removal.

Historical small-sample Elo estimates below are inherited journal entries, not validated
strength claims. This audit does not adopt them as evidence.

## 5.17.0 - 2026-10-05

- Fixes the explicit-zero UCI `nodes` sentinel collision. `go nodes 0` is now a present zero-node budget instead of being treated as if the `nodes` token were absent.
- `SearchLimits` and `Searcher` track node-limit presence separately from the unsigned numeric limit; valid UCI `nodes` parsing sets both fields. Positive direct-API callers that set `nodes` without the new flag remain supported.
- Exact process regression: unchanged 5.16.0 `go nodes 0 searchmoves e2e4` continues through iterative deepening until externally stopped; 5.17.0 returns `bestmove e2e4` immediately with no completed-depth `info` record.
- Adds direct tests for explicit zero, absent node limits, and legacy positive direct-API limits, plus the process-level zero-node regression.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI suites, extended UCI lifecycle checks, and reference perfts pass. Eleven interleaved CPU0-pinned deterministic comparisons preserve every finite-search node count, score, and best move. No speed or Elo claim is made.

## 5.16.0 - 2026-10-05

- Fixes proven transposition-table score/bound reuse across incompatible reversible repetition histories while preserving the validated 5.15.0 depth-5 null-move safeguard.
- The selected baseline is the later completed 5.15.0 lineage (source SHA-256 `af910d2ad7903cf86ed486ecf3a286fb744317956709fae621a993f542e8227a`). A separately completed earlier 5.15.0 sibling had already validated this repetition-history correction but did not contain the later null-move fix; 5.16.0 reconciles those lineages by applying exactly this one behavior change to the later baseline.
- Adds a history-aware legal-search TT key derived from the ordinary Zobrist position key plus an incremental 64-bit multiset fingerprint of known reversible legal history. Pawn moves, captures, and castling-right loss reset obsolete history; synthetic-null branches retain their dedicated 5.9 null context.
- Exact regression `6nk/8/8/8/8/8/8/1Q2K1N1 w - - 0 1` with knight repetition changes from `fresh=-967 warm_repeated=-967 cold_repeated=0` on unchanged 5.15.0 to `fresh=-967 warm_repeated=0 cold_repeated=0` on 5.16.0 under GCC, Clang, and ASan+UBSan.
- Adds make/unmake, pawn-reset, and castling-right-reset identity regressions. Ordinary `Board::key()` remains unchanged for repetition detection and position-only caches.
- Strict GCC/Clang warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests, the inherited shallow-null regression, and reference perfts pass. Interleaved finite-search signatures retain all best moves; node/score changes caused by removing incompatible TT reuse are documented without a speed or Elo claim.

## 5.15.0 - 2026-10-05

- Fixes a proven depth-5 high-margin null-move false bound: the aggressive reduction can collapse the synthetic-null probe directly into quiescence and suppress a required PVS re-search.
- Preserves one reduced normal ply for exactly that depth-5/high-margin path; the existing shallow cutoff policy and depth-6+ verification remain otherwise unchanged.
- Adds unit and process-level regressions for `2rqNN2/4k3/ppp2pB1/3p4/PPPp1Prb/n3P2b/K7/4Q3 b - - 0 34`: the combined `searchmoves a3b5 g4g3` search must select `g4g3` at +1498 rather than `a3b5` at +1374.
- The isolated seeded child probe changes from `with_null=-1374` with one false null cutoff to `with_null=-1375`, matching the non-null zero-window result and recording no cutoff.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests and exact reference perfts pass.
- Eleven interleaved CPU-pinned comparisons preserve all shallow benchmark nodes/scores/best moves; the deep suite differs by only 11 nodes with identical scores/best moves. Mixed timing is treated as host noise; no speed or Elo claim is made.

## 5.14.0 - 2026-10-05

- Fixes asynchronous UCI output-record interleaving. Search-thread `info` telemetry and command-thread replies are now emitted atomically with a shared mutex-protected UCI output critical section.
- Adds a process-level 512-readiness stress regression during `go infinite`; unchanged 5.13.0 deterministically produces malformed lines such as `... nodes readyok241 ...`, while 5.14.0 preserves every `readyok` as a standalone record.
- Applies the synchronized-stream rule to handshake/options, readiness, diagnostics, perft records, `info` telemetry, and `bestmove`, so every stdout writer uses the same atomic-emission mechanism.
- Preserves all validated 5.8–5.13 correctness fixes and leaves explicit-zero `nodes` plus search-selectivity backlog items for separate releases.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests and exact reference perfts pass.
- Eleven interleaved CPU-pinned finite-search comparisons preserve all nodes, scores and best moves. Mixed timing changes are treated as host noise; no speed or Elo claim is made.

## 5.13.0 - 2026-10-05

- Fixes explicit-zero UCI time-control sentinel collisions. `go movetime 0` and zero side-to-move clocks now receive the existing minimum one-millisecond bounded budget instead of being interpreted as absent/unbounded.
- Uses `-1` as the internal “not specified” sentinel for `SearchLimits::movetime_ms` and `SearchLimits::time_ms`; `go infinite` still takes precedence and remains unbounded until explicit stop.
- Adds direct-API regressions for zero movetime, zero side clock and truly absent fields, plus process-level UCI regressions for zero movetime and both side-to-move clock cases. These public cases fail to stop autonomously on unchanged 5.12.0 and pass on 5.13.0.
- Leaves the separate explicit-zero `nodes` sentinel behavior unchanged for a future single-issue release.
- Preserves the validated 5.8–5.12 correctness fixes. Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests and exact reference perfts pass.
- Eleven interleaved CPU-pinned finite-search comparisons preserve all nodes, scores and best moves. Mixed timing changes are treated as host noise; no speed or Elo claim is made.

## 5.12.0 - 2026-10-05

- Fixes terminal-root `SearchInfo` result commitment. Completed iterative-deepening iterations now commit their score and depth even when no PV move exists.
- Preserves the existing legal fallback best-move convention for already adjudicated roots that still have legal moves, while checkmate/stalemate roots continue to report a null best move and empty PV.
- Adds focused regressions for an already-checkmated root, stalemate, and insufficient-material roots. The exact new assertions fail on unchanged 5.11.0 and pass on 5.12.0.
- Preserves the 5.11.0 `go infinite` publication lifecycle fix, the 5.10.0 restricted-root TT fix, the 5.9.0 halfmove/null TT-context fix and the 5.8.0 king-safe SEE fix.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests and exact reference perfts pass. Interleaved finite-search benchmarking preserves nodes, scores and best moves; mixed timing changes are treated as host noise.
- No Elo or speed claim is made. Other search, TT, UCI-output, time-limit and pruning backlog items remain separate.

## 5.11.0 - 2026-10-05

- Fixes premature final-result publication for `go infinite`. If internal search returns naturally (for example, a terminal or immediately adjudicated root reaches the current depth-64 ceiling), the UCI worker now waits for an explicit stop/termination event before printing `bestmove`.
- Adds process-level regressions for the historical terminal checkmate reproducer and an insufficient-material root that still has legal moves. Both must remain silent after depth 64 until `stop`, then publish exactly one final best move.
- Registers the UCI regression driver with CTest when Python is available, so the lifecycle behavior is part of the ordinary test gate.
- Preserves the 5.10.0 restricted-root TT fix, the 5.9.0 halfmove/null TT-context fix and the 5.8.0 king-safe SEE fix.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match/UCI tests and exact reference perfts pass. The finite-search benchmark driver is byte-identical between 5.10.0 and 5.11.0 because the search core is unchanged; timing variation is treated as shared-host noise.
- No Elo or speed claim is made. Terminal `SearchInfo` commitment and other search-pruning/time-control backlog items remain separate.

## 5.10.0 - 2026-10-05

- Fixes restricted-root `searchmoves` transposition-table contamination. A score obtained by maximizing over only the allowed root subset is no longer published as a normal Exact/Upper/Lower TT result for the unrestricted position.
- Restricted-root result/PV reporting now carries the chosen root move separately, so correctness does not depend on leaving an unsound root TT entry behind. Interior nodes remain unrestricted and continue to use/store TT entries normally.
- Adds focused regressions proving that a restricted root publishes no TT score/bound, still reports completed depth/PV, does not alter a later unrestricted transposition, and does not disable ordinary unrestricted root TT storage. The new regression set fails twice on unchanged 5.9.0 and passes on 5.10.0.
- Public process reproducer changes from warm `+59 / e6e5` on 5.9.0 to the cold-consistent `+67 / b8c6` on 5.10.0 after the same `a2a3` restricted warmup.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, Clang ASan+UBSan, engine/match-tool tests, UCI regressions and reference perfts pass.
- Twenty-one CPU0-pinned interleaved deterministic comparisons versus a freshly rebuilt unchanged 5.9.0 baseline preserve the exact normal-search node counts, scores and best moves. Timing medians are treated as host noise, not a speed or Elo claim.
- No Elo claim is made. Known unrelated search/UCI defects remain tracked separately rather than being batched into this release.

## 5.9.0 - 2026-10-03

- Fixes TT score/bound reuse across incompatible fifty-move-rule contexts without changing the repetition/Zobrist key.
- Matching TT moves remain available for ordering, while score/bound cutoffs require an exact halfmove-clock context; synthetic-null branches use a separate context because they suppress draw adjudication.
- Packs depth, bound and rule-50 context into the same two metadata bytes used by 5.8.0 depth/bound fields, avoiding a new TT-entry field.
- Adds deterministic public-search and qsearch regressions covering warm/cold/cleared tables, reverse warmup, clocks 98/99/100, null-branch separation, checkmate precedence and irreversible clock resets. The new regression set fails on unchanged 5.8.0 and passes on 5.9.0.
- Reference perfts remain exact; strict GCC/Clang and ASan+UBSan gates pass.
- Interleaved benchmarks show a larger search tree from intentionally reduced TT cutoff reuse; this is documented as the correctness cost, not a performance or Elo improvement.
- Terminal `go infinite` lifecycle behavior remains a separate known issue. No Elo claim.

## 5.8.0 - 2026-10-03

- One engine-behavior change: SEE recapture selection now rejects moves that expose their
  own king or move a king onto an attacked square. No new evaluation/search/order/TT/time
  heuristic is combined with it.
- Thirteen focused legal-exchange fixtures and quiescence regressions expose the prior
  pinned-defender blind spot; the free-rook example changes qscore -363 to +208 without
  changing evaluation weights. Existing regressions, strict compilers and sanitizers pass.
- Establishes original MIT-licensed fixed openings, external Fastchess orchestration,
  A/A controls, retained PGNs, independent paired/pentanomial checks and an executable SPRT gate.
- 32-game time-based pilots versus unchanged 5.7.0 and 5.6.0 remain inconclusive. A later 100-pair/200-game fixed-10,000-node screen versus unchanged 5.7.0 scored W69 D65 L66, pentanomial [3,21,50,22,4]; this is directional regression screening, not Elo evidence. No Elo claim.
- Observed median search runtime is slightly higher, not lower; deterministic score/move
  signatures remain unchanged and Kiwipete node changes are intentional. See VALIDATION.md.
- Documents, but does not bundle fixes for, TT/rule-50 context leakage and terminal infinite
  search completing before stop. 5.8.0 is promoted as a correctness release after the full
  correctness gate; strength remains unproven and no Elo claim is made.

## 5.7.0 - 2026-10-03

- Fixes a v5.6.0 quiescence fast-path edge case: an equal-value capture onto the first or eighth rank can still have negative SEE when an enemy pawn recaptures and promotes. Back-rank captures now run exact SEE before pruning decisions; mirrored regression positions cover both colors.
- Ensures an interrupted root search with `searchmoves` still returns an allowed legal fallback move when the budget expires before depth 1 completes. An explicitly empty legal root intersection continues to return `0000`.
- Makes clock-budget arithmetic overflow-safe by widening time, increment, moves-to-go, and overhead calculations before multiplication/addition; maximum signed-int clock inputs now pass UBSan and produce a bounded budget.
- Clamps direct-API `mate_moves` before converting it to a ply horizon, matching the UCI parser's supported range and avoiding unchecked arithmetic for out-of-range callers.
- Extended reference perft remains exact at start depth 6 = 119,060,324, Kiwipete depth 4 = 4,085,603, and CPW position 3 depth 5 = 674,624.
- On an AMD EPYC 9V74 pinned to one CPU, 15 interleaved runs versus a freshly rebuilt v5.6.0 kept start-position perft-5 at 4,865,609 nodes with identical 67 ms medians, and kept the four-position suite at 62,196 nodes with identical scores/best moves (31 ms v5.7.0 vs 32 ms v5.6.0 median, within millisecond timer granularity).
- The depth-8/9 suite remains exactly 275,026 nodes with identical scores/best moves; 11 interleaved pinned runs produced the same 171 ms median for v5.6.0 and v5.7.0.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, ASan+UBSan, regression/tactical tests, and scripted UCI handshake/readiness/finite/searchmoves/mate/infinite-stop/perft/option gates pass.
- No Elo claim is made; v5.7.0 is a correctness release with deterministic benchmark behavior preserved.

## 5.6.0 - 2026-10-03

- Adds a material-safe quiescence SEE fast path: non-promotion captures skip full static-exchange evaluation when the captured piece value is at least the attacker value, because such captures cannot have a negative material SEE.
- Reuses the already computed victim value for quiescence delta pruning, avoiding duplicate board lookups on captures.
- Rewrites en-passant hash-legality probing to use incremental occupancy plus the existing bitboard attack detector instead of copying and editing the full 64-square mailbox for each candidate capture.
- A deterministic 866-position/capture legality corpus examined 2,105 legal captures; 738 qualified for the SEE bypass and none had a negative exact SEE.
- A 434-position differential corpus against v5.5.0 matched exactly for FEN progression, full/pawn Zobrist keys, legal-move counts, depth-2 perft, and static evaluation.
- The standard four-position deterministic search remains exactly 62,196 nodes with identical scores and best moves; pinned 15-run interleaved median aggregate time improved 45 -> 43 ms (-4.4%) versus a fresh v5.5.0 build.
- The historical depth-8/9 suite remains exactly 275,026 nodes with identical scores and best moves; pinned 11-run interleaved median aggregate time improved 230 -> 222 ms (-3.5%).
- Start-position perft-5 remains exactly 4,865,609 nodes with the same 86 ms pinned median in the 15-run comparison, consistent with unchanged move generation.
- Extended perft gates pass at start depth 6 = 119,060,324, Kiwipete depth 4 = 4,085,603, and CPW position 3 depth 5 = 674,624.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, ASan+UBSan, the full regression suite, and UCI handshake/finite/searchmoves/mate/infinite-stop/perft/malformed-option/non-power-of-two-Hash gates pass.
- Rejected experiments: bitboard slider move emission was 6-9% slower in the pinned benchmark, and a bitboard-only exact SEE rewrite materially slowed search; both were reverted.
- No Elo claim is made; this release is a deterministic hot-path optimization with no controlled paired-game evidence.

## 5.5.0 - 2026-10-03

- Replaces mailbox walking in bishop/rook/queen mobility evaluation with compile-time directional ray masks, occupancy bit scans, and popcounts while preserving the exact mobility score.
- Iterates non-pawn evaluation directly by color/type bitboards instead of scanning combined occupancy and re-reading each piece from the mailbox; material, phase, piece-square, mobility, rook-file, bishop-pair, king-shelter, and tempo scores are unchanged.
- Differential evaluation validation covered 400 deterministic legal positions across five starting FENs; v5.4.0 and v5.5.0 produced identical position keys, legal-move counts, and exact static evaluations on every position.
- Fresh pinned 15-run interleaved comparison versus v5.4.0 on Intel Xeon Platinum 8573C: the standard four-position deterministic search remains exactly 62,196 nodes with identical scores/best moves while median aggregate time improves 52 -> 48 ms (-7.7%).
- The historical depth-8/9 suite remains exactly 275,026 nodes with identical scores/best moves; pinned 15-run median aggregate time improves 302 -> 272 ms (-9.9%) against a fresh v5.4.0 build under the same conditions.
- Start-position perft-5 remains exactly 4,865,609 nodes and is effectively unchanged in throughput (fresh pinned medians 91 ms for v5.4.0 and 92 ms for v5.5.0), as expected because move generation is unchanged.
- Extended perft gates pass at start depth 6 = 119,060,324, Kiwipete depth 4 = 4,085,603, and CPW position 3 depth 5 = 674,624.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, ASan+UBSan, regression/tactical/reference-perft tests, UCI finite/restricted/mate/infinite-stop/perft tests, non-power-of-two Hash, and malformed-option handling pass.
- Rejected experiments include lazy stable move selection (no repeatable deep-suite benefit) and material-value-scaled MVV-LVA (increased the deterministic search tree); neither is shipped.
- No Elo claim is made; this release improves deterministic evaluation throughput without controlled paired-game evidence.


## 5.4.0 - 2026-10-03

- Adds exact per-color occupancy bitboards maintained across FEN load, normal captures, en passant, castling, promotion, make/unmake, and null moves.
- Rewrites king-safety legality filtering to evaluate the post-move occupancy directly. Candidate legal moves no longer mutate and restore mailbox squares solely to test whether the king is attacked.
- Adds bitboard attack probes using precomputed pawn, knight, king, and slider-ray masks; slider attacks locate the nearest occupied ray square with bit scans.
- Uses cached occupancy directly in pseudo-legal generation and evaluation instead of repeatedly ORing all six piece bitboards for a color.
- Replaces modulo indexing with bit-mask indexing for the fixed power-of-two evaluation/pawn caches and for power-of-two transposition-table sizes; arbitrary TT sizes retain the exact modulo fallback.
- Adds occupancy-consistency regression checks across ordinary moves, captures, castling, promotion, en passant, unmake, and long deterministic random walks.
- Differential validation against v5.3.0 covered 128 deterministic legal positions; legal-move counts and depth-3 perft totals matched exactly for every position.
- Nine-run interleaved comparison versus v5.3.0 on Intel Xeon Platinum 8573C: start-position perft-5 median 150 -> 91 ms (-39.3%) with the exact same 4,865,609 nodes.
- The four-position deterministic search remains exactly 62,196 nodes with identical scores/best moves; median aggregate time 61 -> 51 ms (-16.4%).
- The depth-8/9 suite remains exactly 275,026 nodes with identical scores/best moves; median aggregate time 303 -> 258 ms (-14.9%).
- Extended perft gates pass at start depth 6 = 119,060,324, Kiwipete depth 4 = 4,085,603, and CPW position 3 depth 5 = 674,624.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, ASan+UBSan, regression/tactical/reference-perft tests, UCI finite/restricted/mate/infinite-stop/perft tests, and malformed-option handling all pass.
- No Elo claim is made; this release changes hot-path implementation while preserving deterministic search decisions and has no controlled match evidence.

## 5.3.0 - 2026-10-03

- Replaces repeated knight/king edge arithmetic with compile-time jump-target tables while preserving the exact historical move order.
- Replaces slider boundary walking in legal generation and attack detection with compile-time directional ray tables, again preserving direction and near-to-far ordering.
- Fuses non-pawn piece-square, mobility, and rook-file evaluation into one occupied-piece traversal instead of scanning all occupied squares twice.
- Uses precomputed knight attack masks and side occupancy for exact knight mobility scoring; evaluation values remain unchanged.
- Adds an exact complex-position evaluation regression in addition to the existing evaluation property tests.
- Seven-run final interleaved comparison versus v5.2.0 on Intel Xeon Platinum 8573C: start-position perft-5 median 214 -> 150 ms (-29.9%) and the four-position deterministic search median 75 -> 59 ms (-21.3%), with the same 62,196 nodes, scores, and best moves.
- Seven-run interleaved depth-8/9 suite remains exactly 275,026 nodes with identical scores/best moves; median aggregate time 386 -> 302 ms (-21.8%).
- Strict GCC 14.2 and Clang 17 warning-as-error builds, regression/reference-perft suite, ASan+UBSan, and UCI finite/infinite/stop/restriction/mate/perft checks pass.
- No Elo claim is made: this release is a deterministic hot-path optimization with no controlled match evidence.

## 5.2.0 - 2026-10-03

- Preserves move-generation order while iterating only occupied side-to-move squares via piece bitboards instead of scanning all 64 board squares at every pseudo-legal generation.
- Moves shallow reverse-futility eligibility ahead of full legal-move construction; a legal-move probe is performed only when an RFP cutoff would otherwise fire, preserving stalemate semantics.
- Adds a zero-window favorable-stalemate regression specifically covering the new reverse-futility precheck path.
- Fresh interleaved benchmark on the validation host: start-position perft 5 median 230 ms versus 280 ms for v5.1.0; deterministic four-position search median 78 ms versus 97 ms, with the same 62,196 nodes, scores, and best moves.
- Deeper depth-8/9 suite remains exactly 275,026 nodes with identical scores/best moves; five-run median aggregate 475 ms versus 491 ms for v5.1.0 on the same host.
- Strict GCC 14.2 and Clang 17 warning-as-error builds, regression/reference-perft suite, ASan+UBSan, and UCI protocol smoke/regression checks pass.
- No Elo claim is made; these changes are deterministic hot-path optimizations rather than evidence from a sufficiently large controlled match.

## 5.1.0 - 2026-10-03

- Replaced per-node heap-backed move vectors with a fixed-capacity 256-entry stack `MoveList`; legal filtering now compacts the list in place.
- Removed recursive principal-variation and quiet-history vector allocations; completed PVs are reconstructed from verified TT moves after each iteration.
- Added depth-0 quiescence transposition-table probing/storing with mate-distance-normalized bounds; deeper TT entries are used only for move ordering and are not overwritten by qsearch.
- Moved promotions ahead of ordinary captures in tactical ordering, including capture promotions.
- Reused cached king locations when validating en-passant hashing instead of scanning copied boards.
- Added a regression proving a repeated quiescence call hits an exact depth-0 TT entry and preserves its score.
- Fresh interleaved comparison versus v5.0.0: shallow four-position tree 65,371 -> 62,196 nodes (-4.9%); deep suite 295,704 -> 275,026 nodes (-7.0%).
- Median start-position perft-5 time improved 197 -> 186 ms (-5.6%) across nine interleaved runs; all 4,865,609 nodes remain exact.

## 5.0.0 - 2026-10-03

- Separated a reached search budget from a recursively interrupted iteration.
- A root iteration completed on exactly the node limit is now retained; partial iterations remain hidden.
- Added an exact-budget regression and verified live 21-node completion at depth one.
- Final release gates pass under strict GCC, ASan/UBSan, reference perfts, deterministic benchmarks, and scripted UCI lifecycle checks.

## 4.9.0 - 2026-10-03

- Rejects FEN positions where the side that just moved left its own king attacked.
- Added paired regressions that reject an impossible prior move while allowing the side to move to be in check.
- Replaced two illegal synthetic fixtures with legal equivalents; the promotion-mate proof remains covered.

## 4.8.0 - 2026-10-03

- Saturated 16-bit halfmove and fullmove counters instead of allowing wraparound.
- Extended undo state to restore the exact fullmove counter, including at saturation.
- Added a black quiet-move regression at both 65,535 limits with exact unmake verification.

## 4.7.0 - 2026-10-03

- Strengthened en-passant FEN validation to require an empty target and double-push origin square.
- Added regressions for both impossible-history cases.
- Existing capturable, non-capturable, and king-pinned en-passant key behavior remains verified.

## 4.6.0 - 2026-10-03

- FEN parsing now requires exactly six fields and rejects trailing tokens.
- Added a regression proving a rejected trailing-field FEN leaves the existing board unchanged.
- All reference perfts and search regressions remain clean.

## 4.5.0 - 2026-10-03

- Made numeric UCI option updates transactional with complete-token integer validation.
- Malformed Hash and Move Overhead values now report a diagnostic and preserve prior settings.
- Rejected depth-preferred TT replacement after a W5 L15 D12 equal-node screen despite 0.7% fewer benchmark nodes.

## 4.4.0 - 2026-10-03

- Added bounded negative history updates for quiet moves searched before a quiet beta cutoff.
- Reduced the four-position tree from 71,182 to 65,371 nodes (8.2%).
- Screens versus v4.3.0: W9 L10 D13 at 10k nodes and W15 L13 D4 at 10 ms/move.
- Rejected shallow quiet futility pruning after a W6 L12 D14 equal-node screen despite a smaller tree.

## 4.3.0 - 2026-10-03

- Defined safe depth-zero perft behavior as one current-position leaf.
- Rejects negative, malformed, and impractically large UCI perft depths instead of recursing indefinitely.
- Added API and live-UCI regressions for zero, negative, malformed, and ordinary perft commands.

## 4.2.0 - 2026-10-03

- Counted depth-positive terminal alpha-beta visits against the configured node budget.
- Avoided double-counting quiescence leaves while making mate/draw-heavy equal-node tests fair.
- Added an exact terminal-root accounting regression; the nonterminal benchmark signature is unchanged.

## 4.1.0 - 2026-10-03

- Replaced the fixed 1,024-node deadline poll with adaptive 1/32/256-node intervals.
- Ultra-short searches now react at every node, while long searches avoid unnecessary clock reads.
- Preserved the complete v4.0 deterministic benchmark signature and verified live short-budget completion.

## 4.0.0 - 2026-10-03

- Added 35-centipawn aspiration windows from depth four with a full-window recovery search on failure.
- Preserved all reference moves/scores while reducing the four-position tree from 72,760 to 71,182 nodes (2.2%).
- Screens versus v3.9.0: W13 L5 D14 at 10k nodes and W13 L14 D5 at 10 ms/move; the latter is neutral at this sample size.

## 3.9.0 - 2026-10-03

- Added FEN inventory validation for the eight-pawn and sixteen-piece limits per side.
- Rejects excess promoted material unless enough original pawns are absent to explain it.
- Added impossible-pawn and impossible-promotion regressions; all legal-move perfts remain exact.

## 3.8.0 - 2026-10-03

- Made UCI `position` commands transactional across FEN parsing and complete move lists.
- An illegal move now preserves the last valid engine position instead of committing a partial sequence.
- Verified the preserved position through a live restricted search after a deliberately malformed command.

## 3.7.0 - 2026-10-03

- Made explicit `searchmoves` restrictions authoritative even when none of the supplied moves are legal.
- Prevented transposition-table PV reconstruction from reintroducing an excluded root move.
- Added direct and live-UCI regressions; an illegal-only restriction now returns `bestmove 0000`.

## 3.6.0 - 2026-10-03

- Added complete-token integer validation and range clamping for depth, mate, movetime, moves-to-go, clocks, and increments.
- Malformed or negative values now degrade safely instead of being partially parsed.
- Verified a mixed malformed command returns a legal move without hanging or overflowing.

## 3.5.0 - 2026-10-03

- Replaced signed-int UCI node parsing with validated full-token unsigned 64-bit parsing.
- Verified a live five-billion-node request continues until asynchronous `stop` rather than overflowing.
- Rejected qsearch TT bound storage after a negative W11 L14 D7 equal-time screen.

## 3.4.0 - 2026-10-03

- Reused matching transposition-table moves in quiescence ordering for warm and transposed tactical positions.
- Cold deterministic fields remain unchanged.
- Rejected SEE-aware delta margins and SEE capture tie-breaking after inferior node/time or match evidence.

## 3.3.0 - 2026-10-03

- Integrated accelerated SEE to prune losing non-promotion captures outside check in quiescence.
- Reduced the four-position tree from 105,630 to 72,760 nodes (31.1%) and aggregate time to about 67 ms.
- Screens versus v3.2.0: W11 L11 D10 at 10k nodes and W13 L9 D10 at 10 ms/move.

## 3.2.0 - 2026-10-02

- Replaced SEE's repeated 64-square attacker scans with per-piece bitboard candidate iteration.
- Reduced a one-million-call poisoned-pawn SEE workload from 445-472 ms to 39-40 ms, over 10x faster, with identical results.
- Rejected broad SEE capture ordering and the initial slow SEE qsearch filter after negative equal-time screens; search remains unchanged in this release.

## 3.1.0 - 2026-10-02

- Added standalone static-exchange evaluation using least-valuable recaptures and dynamically opened slider lines.
- Handles ordinary captures, en passant, and promotion value changes.
- Added exact +500 undefended-rook and -800 poisoned-pawn regressions; search is intentionally unchanged until the next gated integration.

## 3.0.0 - 2026-10-02

- Added legal transposition-table PV reconstruction after every completed iteration.
- Stops reconstruction on invalid/stale moves, repeated keys, rule-50, and insufficient-material boundaries.
- Added cold/warm-hash complete-PV regression; deterministic search fields remain unchanged.

## 2.9.0 - 2026-10-02

- Added a pawn-structure cache keyed by the verified incremental pawn key.
- Reuses pawn material, placement, doubled, isolated, and passed-pawn analysis while retaining live king-shelter and rook-file evaluation.
- Preserved the depth-10 start result (276,925 nodes, +17, `g1f3`) while reducing median runtime by about 4% versus v2.8.0.

## 2.8.0 - 2026-10-02

- Added an independent incremental pawn Zobrist key across pushes, captures, en passant, promotions, and unmake.
- Added reconstruction and restoration checks in special-move fixtures and deterministic walks.
- Search behavior remains unchanged; a precomputed piece-square experiment with no repeatable gain was rejected.

## 2.7.0 - 2026-10-02

- Reworked evaluation passes to iterate occupied bits instead of scanning every square twice.
- Preserved all evaluations and deterministic search fields while reducing aggregate search time from about 102 ms to 95 ms (6.9%).

## 2.6.0 - 2026-10-02

- Replaced allocation-prone stable sorting with stable in-place ordering that scores each move exactly once.
- Preserved move order and every deterministic field while reducing aggregate search time from about 115 ms to 102 ms (11.3%).

## 2.5.0 - 2026-10-02

- Reserved realistic pseudo-legal/capture buffer capacities and reused pseudo-move counts for legal buffers.
- Preserved deterministic behavior while reducing median start-position perft from 204 ms to 192 ms (5.9%); aggregate search improved slightly.

## 2.4.0 - 2026-10-02

- Added incrementally cached king squares, including temporary legality probes and exact unmake restoration.
- Preserved every deterministic field while reducing median start-position perft from about 219 ms to 204 ms and aggregate search from about 126 ms to 116 ms on the validation host.

## 2.3.0 - 2026-10-02

- Added exact incremental bitboards for every piece through captures, en passant, promotions, castling, and unmake.
- Converted null-move material guards and insufficient-material detection to constant-time bit operations.
- Added bitboard/mailbox reconstruction checks across all special-move fixtures and deterministic walks.
- All perfts and deterministic search fields remain unchanged.

## 2.2.0 - 2026-10-02

- Added selective-depth tracking plus UCI `seldepth`, `nps`, and permille `hashfull` search telemetry.
- Added bounded hash-occupancy and selective-depth regressions.
- Preserved all deterministic search nodes, scores, and moves from v2.1.0.

## 2.1.0 - 2026-10-02

- Added the UCI `Clear Hash` button and separated search-cache clearing from full new-game heuristic reset.
- Fixed full reset to clear countermove state alongside history and killers.
- Added a direct TT occupancy/clear regression and verified live UCI option handling.

## 2.0.0 - 2026-10-02

- Added configurable UCI `Move Overhead` (0-1000 ms) and reserved it from fixed-movetime and clock-derived budgets.
- Upgraded `setoption` parsing to support multiword option names.
- Added a direct time-budget regression; UCI negotiation, perft, and deterministic search remain clean.

## 1.9.0 - 2026-10-02

- Hardened FEN parsing against pawns on promotion ranks, adjacent kings, duplicate or impossible castling rights, and inconsistent en-passant targets.
- Added permanent rejection tests for each malformed-state class.
- All reference perfts and deterministic search fields remain unchanged.

## 1.8.0 - 2026-10-02

- Added UCI `go mate N` parsing, mate-horizon depth limiting, and early exit once a mate within the requested distance is proven.
- Added a permanent mate-in-one limit regression and verified live UCI mate-score output.

## 1.7.0 - 2026-10-02

- Added UCI `searchmoves` parsing and exact root-move restriction, compatible with other `go` limits.
- Added a permanent root-restriction regression and verified the interactive UCI result.
- Unrestricted deterministic benchmarks remain unchanged.
- Rejected guarded ProbCut (W9 L11 D12 with more nodes) and a one-per-line check extension (W9 L15 D8).

## 1.6.0 - 2026-10-02

- Added one adaptive null-move reduction ply when static evaluation exceeds beta by at least 200 centipawns; deep verification remains mandatory.
- The shallow deterministic suite remains unchanged, while paired 10,000-node screening against v1.5.0 scored W13 L9 D10 over 32 games.
- Rejected negative quiet-history feedback after it scored W8 L13 D11 despite reducing nodes.

## 1.5.0 - 2026-10-02

- Added root-to-root quiet-history aging to prevent early-game cutoff scores from dominating later positions.
- Fresh-search benchmark nodes, scores, and moves remain unchanged.
- Paired 10,000-node screening against v1.4.0 scored W11 L6 D15 over 32 games.

## 1.4.0 - 2026-10-02

- Added native insufficient-material detection for bare kings, a lone bishop or knight, and bishop-only endings confined to one square color.
- Integrated dead-position draws into main search and quiescence, with direct board and search regressions.
- Corrected the royal-fork fixture's score expectation because its queen-winning line reaches the drawn K+N versus K ending; the required tactical move remains unchanged.
- Rejected both an unsafe razoring candidate that failed the queen-sacrifice regression and an improving-heuristic candidate that screened W7 L11 D14.

## 1.3.0 - 2026-10-02

- Added a 65,536-entry exact-Zobrist evaluation cache and clear-on-new-game lifecycle.
- Preserved every deterministic node count, score, and best move.
- Median aggregate search time fell from about 137 ms to 125 ms on the validation host (8.8%); timings remain host-specific.

## 1.2.0 - 2026-10-02

- Added exact mate-distance pruning so search windows cannot exceed the best physically possible mate score at the current ply.
- Passed the full tactical, regression, and perft gates; ordinary benchmark nodes, scores, and moves are unchanged as expected.
- Rejected a depth-preferred single-slot TT replacement after a neutral W11 L11 D10 screen and a slight node regression.

## 1.1.0 - 2026-10-02

- Added a second LMR ply for very late, non-checking, low-history quiet moves at depth 6+, retaining mandatory verification on improvement.
- Preserved all benchmark moves and scores while reducing the suite from 110,425 to 105,630 nodes (4.3%).
- Paired 10,000-node screening against v1.0.0 scored W8 L9 D15, statistically neutral at this sample size.
- Rejected a checking-quiescence candidate because a marginal W11 L10 D11 screen did not justify 9.3% more nodes and materially lower throughput.

## 1.0.0 - 2026-10-02

- Added a reply-specific countermove table for quiet beta cutoffs and integrated it below killer moves in ordering.
- Preserved all benchmark moves and scores with an essentially neutral aggregate node count (110,425 versus 110,356).
- Paired 10,000-node screening against v0.9.0 scored W9 L8 D15 over 32 games.
- Rejected a noisier capture-history candidate after it expanded the benchmark tree and changed the start-position result.

## 0.9.0 - 2026-10-02

- Added internal iterative reduction at deep, non-check, zero-window nodes lacking a transposition-table move.
- Preserved all benchmark moves and scores while reducing the four-position suite from 120,414 to 110,356 nodes (8.4%).
- Paired 10,000-node screening against v0.8.0 scored W10 L9 D13 over 32 games.

## 0.8.0 - 2026-10-02

- Added conservative late-move pruning for non-checking quiet moves at depth 1-2 when static evaluation is below alpha.
- Preserved all benchmark moves and scores while reducing the four-position suite from 134,043 to 120,414 nodes (10.2%).
- Paired 10,000-node screening against v0.7.0 scored W11 L10 D11 over 32 games.
- Rejected aspiration windows after they increased the aggregate tree by about 4%; the experiment was fully reverted.

## 0.7.0 - 2026-10-02

Accepted shallow reverse-futility upgrade:

- Added reverse futility pruning at depth 1-2 only in zero-window nodes outside check and mate-score bounds, after terminal move detection.
- Reused the guarded static evaluation for null-move pruning rather than evaluating twice.
- Preserved every deterministic benchmark score and best move while reducing the four-position suite from 160,055 to 134,043 nodes (16.3%), and from v0.5.0's 242,603 nodes by 44.7% cumulatively.
- Paired 10,000-node screening against v0.6.0 scored 13 wins, 9 losses, and 10 draws over 32 games, a provisional +44 Elo point estimate with high uncertainty.
- Rejected an adaptive soft/hard timer experiment after it scored 7 wins, 11 losses, and 14 draws in 32 equal-time games at 50 ms/move; it was fully reverted.

## 0.6.0 - 2026-10-02

Accepted quiescence efficiency upgrade:

- Added conservative delta pruning for non-promotion captures outside check and mate-score windows.
- Added a hard quiescence ply guard consistent with the main search limit.
- Preserved every deterministic benchmark score and best move while reducing the four-position suite from 242,603 to 160,055 nodes (34.0%).
- Median aggregate search time fell from a fresh v0.5.0 baseline of 257 ms to 192 ms (25.3%).
- Paired 10,000-node screening scored 12 wins, 10 losses, and 10 draws over 32 games, a provisional +22 Elo point estimate with high uncertainty.
- Rejected a preceding four-way clustered-TT experiment after it scored 10-10-12 and added about 10% shallow runtime; it is not included in v0.6.0.

## Rejected 0.6 evaluation experiments - 2026-10-02

- Rejected a broad original handcrafted evaluation bundle covering nonlinear king danger, shelter and pawn storms, connected/protected/blocked passers, backward pawns, outposts, and development. It passed correctness tests but scored 11 wins, 12 losses, and 9 draws against v0.5.0 at 10,000 nodes, while materially reducing evaluation throughput.
- Rejected an isolated optimized king-attack-map evaluator after it scored 9 wins, 11 losses, and 12 draws in the same paired screen.
- Both experiments were fully reverted. Version 0.5.0 remains the active baseline with no engine-code change.
- The evidence does not support reaching a +200 Elo target through additional hand-tuned centipawn terms. The credible next route is a trained evaluator with an explicit data, teacher, and licensing plan.

## 0.5.0 - 2026-10-02

Accepted verified null-move selective-search upgrade:

- Added reversible null-move board state with exact en-passant and side-key handling while preserving clocks and excluding synthetic positions from repetition history.
- Added null-move pruning only at non-root zero-window nodes outside check, with static-evaluation gating, mate-window guards, non-pawn-material requirements, consecutive-null prevention, and verification searches at depth 6 and above.
- Suppressed repetition and rule-50 adjudication inside synthetic null subtrees while preserving mate/stalemate detection.
- Saturated history updates to prevent long-session integer overflow.
- Added a permanent seven-position, license-clear synthetic tactical suite covering back-rank mates, smothered mate, queen-sacrifice mate, forks, discovered attacks, and promotion mate.
- Added null-state/key restoration, repetition-history, rule-50-clock, activity, cutoff, and pawn-only zugzwang-guard regressions.
- Reduced the shallow four-position suite from 296,117 to 242,603 nodes (18.1%) and the deeper depth-8/9 suite from 3,084,169 to 2,225,080 nodes (27.9%).
- Equal-node paired play scored 24 wins, 19 losses, and 21 draws over 64 games at 10k and 20k nodes. Equal-time play scored 23 wins, 15 losses, and 26 draws over 64 games at 50 and 100 ms/move, a 56.25% score and provisional +44 Elo point estimate; the naive approximate 95% interval of about -22 to +113 Elo is not conclusive.
- Rejected dynamic LMR and full check extension: the combined build cut deeper nodes by 48.4% but scored only 10 wins, 10 losses, and 12 draws at 10k nodes, while conservative null move alone scored 14 wins, 10 losses, and 8 draws in the same workload.

## 0.4.0 - 2026-10-02

Accepted move-path performance and terminal-correctness upgrade:

- Replaced full-board position-key recomputation on every move with exact incremental Zobrist updates for pieces, promotions, captures, castling, en passant, castling rights, and side to move.
- Reused a lightweight temporary-board legality probe in legal move filtering and removed full `Board`/history copies from en-passant key normalization.
- Fixed favorable quiet stalemate returning a positive static evaluation in quiescence.
- Fixed checkmate at halfmove 100 being adjudicated as a rule-50 draw; checkmate now takes precedence over draw claims.
- Added permanent incremental-key cross-checks for every legal move in special-move fixtures and across eight deterministic 160-ply walks.
- Preserved all deterministic search nodes, scores, and best moves. On the validation AMD EPYC host, median start-position perft depth 5 fell from 926 ms to 222 ms (76.0%), while the four-position search suite fell from 555 ms to 332 ms (40.2%).
- At a 500 ms UCI budget, the middlegame benchmark completed depth 7 instead of v0.3.0's depth 6. This is direct time-to-depth evidence; no Elo gain is claimed without paired games.

## 0.3.0 - 2026-10-02

Accepted tapered-evaluation overhaul:

- Replaced the material/centralization evaluator with separate middlegame and endgame scores blended by game phase.
- Added mobility, doubled and isolated pawns, passed-pawn scaling, bishop pair, open and semi-open rook files, king shelter, endgame king activity, and tempo.
- Added permanent qualitative evaluation regressions without introducing external tables or dependencies.
- Reduced the four-position suite from 451,754 to 296,117 nodes (34.5%) and median aggregate search time from 844 ms to 543 ms (35.7%) despite greater work per evaluation.
- Scored 37/48 against v0.2.0 across equal 10,000-, 20,000-, and 40,000-node paired games: 30 wins, 4 losses, and 14 draws.
- The match gives a provisional +211 Elo estimate; the naive approximate 95% interval of +130 to +320 is optimistic because the same eight paired openings were reused at each budget.

## 0.2.0 - 2026-10-02

Accepted selective-search and repetition-correctness upgrade:

- Added principal-variation search and verified late-move reductions for later quiet moves outside check.
- Reduced the four-position fixed-depth suite from 2,018,204 to 451,754 nodes (77.6%).
- Normalized position keys so en-passant targets are hashed only when a legal capture exists, including king-pinned cases.
- Added capturable, non-capturable, pinned en-passant, and rules-equivalent threefold regressions.
- Scored 18/32 in paired self-play against v0.1.2 at equal 10,000- and 20,000-node budgets: 10 wins, 6 losses, and 16 draws.
- The match implies a provisional +44 Elo estimate with a wide approximate 95% interval of -42 to +135; no confirmed Elo gain is claimed.
- Rejected standalone PVS, 32-centipawn aspiration windows, and a stricter LMR threshold because their aggregate evidence was inferior.

## 0.1.2 - 2026-10-02

Accepted quiescence terminal-correctness fix:

- Correctly score quiet stalemate as a draw at the quiescence horizon instead of returning static material evaluation.
- Added an early-exit legal-move probe that preserves board and hash state.
- Added direct horizon stalemate/checkmate tests and a parent-move stalemate regression.
- Preserved all deterministic search fields at depth 7: 262,257 nodes, +16 score, and `a2a4` best move.
- Measured an approximately 5% runtime cost in an interleaved five-pair comparison: 307 ms versus 293 ms median on Intel Xeon Platinum 8573C.

## 0.1.1 - 2026-10-02

Accepted correctness-gate update:

- Added CPW position 5 at depth 3 (62,379 nodes) to permanent regression coverage.
- Repeated the release benchmark three times and recorded the median without changing engine behavior.
- Reverified strict-warning compilation, all regression tests, ASan/UBSan, and UCI protocol diagnostics.

## 0.1.0 - 2026-10-02

Accepted initial baseline:

- Added portable C++20/CMake project with MIT license and no runtime dependencies.
- Added FEN, complete legal move generation, make/unmake, repetition keys, and perft.
- Added iterative-deepening alpha-beta, quiescence, transposition table, move ordering, evaluation, and safe time/node/depth limits.
- Added asynchronous UCI frontend, regression tests, sanitizer configuration, benchmark, and usage documentation.
- Corrected the Kiwipete regression fixture during validation; no engine defect was implicated.
- Included quiet promotions in quiescence and preserved root PV reconstruction across warm transposition-table searches.
- Verified strict GCC build, all regression/perft tests, ASan/UBSan, benchmark, and UCI stop behavior.
