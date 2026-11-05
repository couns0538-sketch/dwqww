# T04D-02-tt-cut-node-match: at low depth take a TT cutoff only when its direction matches the node type
Status: COMPLETE

## Source
- Stockfish commit [43e100a](https://github.com/official-stockfish/Stockfish/commit/43e100ae06) (2024-11-13), "Use
  cutnode as TT Cutoff Condition", PR text https://github.com/official-stockfish/Stockfish/pull/5670 .
  Tests: STC https://tests.stockfishchess.org/tests/view/6726357b86d5ee47d953da8c , LTC
  https://tests.stockfishchess.org/tests/view/6727326a86d5ee47d953db30 .
- Follow-up [a4edacb](https://github.com/official-stockfish/Stockfish/commit/a4edacb87a) (2025-02-13), "Tweak the
  cutnode depth condition for TT cutoffs", PR https://github.com/official-stockfish/Stockfish/pull/5876 (no text
  beyond the logs). Tests: STC https://tests.stockfishchess.org/tests/view/67ab396ab5c93ee812d851f3 , LTC
  https://tests.stockfishchess.org/tests/view/67ab9647133d55b1d3bc171e .
- TC, book, threads and SPRT bounds of all four runs read from the fishtest run API (`api/get_run/<id>`).

## Licence
Stockfish GPL-3.0 (Copying.txt at ff7cee4244, 2026-10-28): ideas only. Read: commit titles and messages, the two PR
texts, the four fishtest run records. No source file or diff was read.

## Mechanism
Below a depth limit, a non-PV node takes a TT cutoff only when the kind of stored result agrees with the node's
expected type (PR text: "allow TT cutoffs only if cutNode matches previous TT results"): a stored score at or above
beta (fail high) only in an expected cut node, a stored score below it (fail low) only in an expected all node. On a
mismatch the node is searched normally. The follow-up changed only the depth limit (no text). Own reading
(unproven): a mismatch means the tree's node-type guess and the stored bound disagree, so the stored result is more
likely stale for the current path, and a shallow re-search is cheap. (corrected by verify: the commit text states only the fail-high half, "fail high with TT only when expected cutnode"; the PR text "matches previous TT results" is ambiguous, so the fail-low half above and the two-sided rule in the design below are the card's own reading, not the source's stated mechanism.)

## Forge fit
`bash tools/forge_has.sh 'tt_depth >= depth &&'` -> `src/search.cpp:921`: the lock's cutoff (`:921-926`) needs a
non-PV node, no excluded move, a usable score, tt_depth >= depth, halfmove clock < 90 and a bound pointing the right
way; there is no node-type term, although `cut_node` is a parameter of `search` (`:875`). Change: one extra
condition at `:921` for depth <= TtCutNodeDepth. qsearch's own TT cutoff (no node type there) stays as is.
Related, not the same rule: T04 TABLE A4 (Caissa d39fcfb, fail-high cutoffs only from a one-ply-deeper entry,
40+0.4 +2.11; now card T04P-01, and the own off-lock port caissa_c123 already has its form B as spin TtCutExtraMargin, exe built, CR PASS 2026-10-30, never gated - review fix, FIXER3) changes the depth test on the same line (gate the two apart); Stockfish b280d2f (notes/T04D/TABLE.md) shows its
own rule kept that strictly-deeper requirement for fail highs while allowing equal depth for fail lows (the lock
allows equal depth for both). R15 x1 TtCutoffHistory (history on TT cutoffs) and C3 TtProbcut do not touch the
condition; TtPruneV2 has no TT-cutoff rule; tried gates: none on the TT cutoff condition (R7TtExclusive is locking).

## Expected gain
Source (Stockfish master, 1 thread, UHO_Lichess_4852_v1, normalized SPRT; Elo +- 95 % from the pentanomial, own
arithmetic):
- 43e100a: STC 10+0.1 [0,2] LLR 2.93, 41,184 games, Ptnml 131 / 4,728 / 10,554 / 5,046 / 133 = +2.72 +- 1.72;
  LTC 60+0.6 [0.5,2.5] LLR 2.94, 270,888 games, Ptnml 180 / 29,385 / 75,485 / 30,246 / 148 = +1.02 +- 0.62.
- a4edacb (depth limit of the same rule changed): STC [0,2] LLR 2.96, 83,648 games = +1.63 +- 1.23; LTC [0.5,2.5]
  LLR 2.94, 68,160 games = +1.96 +- 1.25.
Forge estimate: 0 to +3 Elo **UNPROVEN** (two passes on one rule in the source; Forge's TT and node-type flags are
simpler, and the right depth limit for Forge is unknown: SPSA it after a first STC run). Counter-evidence (T12C): Stockfish 76c319f (2025-02-24, "Simplify ttcut depth condition", GPL-3.0, message only) simplified the follow-up's depth limit at zero cost (non-regression [-1.75,0.25]: STC +0.00 +- 0.73, 235,328 g; LTC +0.97 +- 1.29, 63,744 g) while the node-type rule stayed, and the source's own LTC gain is only +1.02 +- 0.62 at 270,888 g: top lowered, 0 to +2 Elo **UNPROVEN**; gate it after T04D-01 is decided, not as a pair.

## Effort
Crew 1 h (condition + option, OFF pins, ON bench, smoke). CPU at 430-502 games/h: 3,000-game STC cap = 6-7 h,
+6-7 h one extension if positive (crew route [0,5] nElo) [last round, coordinator, unverified], LTC ~k times that; SPSA of the depth limit (forge-o30-spsa) after STC.

## Test plan
Pre-gate: OFF bench d11/d13/d16/d20/d22 = lock pins; ON bench differs (live); perft unchanged; on the bench set count
TT cutoffs per 1M nodes OFF vs ON by depth (only depths <= the limit may change) and the d20 node growth (fewer
cutoffs cost nodes); mate probe OFF/ON. Gate: UHO SPRT [0,5] at STC, then LTC.

## OFF-by-default design
UCI spin `TtCutNodeDepth`, default 0 = off, range 0-14, own start value 6 for the first gate. At 0 the new condition
is not evaluated, so every TT cutoff, node and bench pin equals the lock. At N > 0, for depth <= N, spin `TtCutNodeForm` (default 1, range 1-2, read only when N > 0; as in notes/SPEC_SEARCH2.md; review fix, second vote 2): 1 = the source-stated half, a fail-high cutoff
(stored score >= beta) also needs `cut_node`, fail-low cutoffs unchanged; 2 = the two-sided own reading, (stored score >= beta) must equal `cut_node`. Gate form 1 first; form 2 only after form 1 ends H0 or capped <= 0.
