# T04R-01: Best-move history bonus scaled by its child fail-highs
Status: COMPLETE

## Source
Renegade (pkrisz99/Renegade) commit a7d8f48c92, 2025-04-14, "Apply move ordering bonuses as many times as failing
high (#107)": https://github.com/pkrisz99/Renegade/commit/a7d8f48c92 ; test log in the commit message, OpenBench
page https://zzzzz151.pythonanywhere.com/test/2526/ (fetched 04:44: the host now serves a placeholder, the test is gone). The message credits the idea to a search rewrite
of Alexandria (GPL-3.0; its source not read). Read with tools/mine_commits.py --show and the commit diff (gh api).

## Licence
pkrisz99/Renegade LICENSE at 2a134aecbc (HEAD, 2026-10-13) = MIT (tools/licence_at.py --row, notes/T04R/licences.md):
copy with notice allowed; the cited diff (125 lines) was read, nothing is copied, the mechanism below is own words.

## Mechanism
Inside the move loop each searched move gets a counter of how many of its child searches came back above alpha: the
reduced (LMR) null-window search, the full-depth null-window re-search, and in PV nodes the full-window search (counted
when it reaches beta). When the node fails high, the history BONUS of the best move (main + continuation history for a
quiet, capture history for a capture) is multiplied by that counter (1..3); the malus of the other tried moves stays at
the base size. A move that refutes even at reduced depth and again at full depth is promoted faster in later ordering;
a move that only fails high once (no reduction, non-PV) gets the old bonus, so most cutoffs are unchanged.

## Forge fit
Lacks it: `bash tools/forge_has.sh 'fail_?high_?count|fh_count|failHighCount|cutoff_?count'` finds only the per-ply
`cutoff_count` used by LMR (`include/forge/search.hpp:273`, `src/search.cpp:905/1145/1180`), no per-move child
fail-high count. Child searches: reduced `src/search.cpp:1148`, re-search `:1151`, null-window full `:1160`, PV full
window `:1163`. Update at the cutoff: `update_quiet_stats(..., depth + (best_score > beta + 100), ...)` `:1198` and
`update_capture_stats` `:1200`; both use ONE `bonus = history_bonus(depth)` (`:731`, `:753`) for the best move and,
negated, for the malus; `apply_history` clamps to +-HistoryMax (`:157-160`), so a larger bonus stays in range.
Change: count child fail-highs per move, keep the count of the move that became best, and pass a separate best-move
bonus = base x (100 + k x (count - 1)) / 100 to the two update functions; the malus loops keep the base bonus.
Not a duplicate: T04G-05 deepens bonus AND malus when the best score beats the eval, T04C-04 / T04D-03 / T04G-03 scale
the malus; this one scales only the best move's bonus by its own fail-high count. Same update site as T04G-05: gate
them one at a time.

## Expected gain
Source: Renegade, +3.35 +- 2.29 Elo (95 %), 10+0.1 s, Threads=1, Hash=16MB, SPRT [0.00, 3.00] (OpenBench Elo bounds),
LLR 2.90 (-2.25, 2.89), N=22,922 games (W 5,291 L 5,070 D 12,561), penta [48, 2640, 5882, 2825, 66] (own conversion
of that penta: about +6.6 nElo); book missing (not in the message, test host gone); no LTC run in the commit history.
Forge estimate: +0 to +3 Elo **UNPROVEN** (Forge's ordering uses killers + counter + main + cont 1/2 with a different
bonus curve; an STC-only source and a gain this size may end capped at 3,000 games = UNPROVEN / no decision).

## Effort
Crew hours: about 1 h code (counter, best-move capture of the count, option, two update signatures) + 1 h proofs
(OFF bench / perft pins, ON bench changes, box tests). CPU: one SPRT up to the 3,000-game cap at the measured
430-502 games/h = about 6-7 h, plus one extension of the same size only if a capped run is positive. GPU: none.

## Test plan
Pre-gate: OFF build bench and perft equal to the lock pins (node-identical), ON at the start value changes bench nodes,
ON with k = 0 equals OFF, sanity FENs (mate, stalemate) at depth 12, no history overflow (apply_history clamp).
Gate: crew route, Threads=1, UHO book, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games;
capped = UNPROVEN / no decision, one extension if its Elo is positive; STC first, then LTC if STC passes.

## OFF-by-default design
UCI spin `FailHighCountBonus` (percent extra bonus per extra child fail-high), default 0 = off, range 0-150, own start
value for the ON build 60 (SPSA-able later). With 0 the code path is skipped (`if (tune::FailHighCountBonus)`), the
best-move bonus equals the old `history_bonus(depth)`, so the search tree and the bench pins are identical to the lock.
