# T04R verify (adversarial pass over cards/T04R, board slot S1)
Start 04:49 PC clock (date); all checks finished by 04:54 (date); write-up after that; done time = the board's Done line.
Wrap-up note F:/odr/work/pool_wrapup.txt: checked before every source and file, never present.
Scratch: F:/odr/work/T04R-verify/ (elo.py recompute script, Renegade/Search.cpp at a3ef409470 = MIT, read allowed).

## Result: 3 cards checked, 3 confirmed, 0 violations, 0 duplicates, lint 0 findings after the corrections

## Numbers (recomputed from the W/L/D and penta blocks in the commit messages, tools/mine_commits.py --show)
| card | commit | W / L / D | Elo +- 95 % (card) | recomputed | penta nElo (own) | LLR / bounds |
|---|---|---|---|---|---|---|
| T04R-01 | a7d8f48c92 | 5,291 / 5,070 / 12,561 (N 22,922) | +3.35 +- 2.29 | +3.35 +- 2.29 (penta error; trinomial would be 3.02) | +6.59 (card: about +6.6) | 2.90 on (-2.25, 2.89) = alpha 0.05 / beta 0.10 OpenBench default, Elo bounds [0,3] |
| T04R-02 | 74f88cf831 | 9,870 / 9,602 / 24,042 (N 43,514) | +2.14 +- 1.67 | +2.14 +- 1.67 | +4.18 | 2.90, same bounds |
| T04R-03 | a3ef409470 | 5,536 / 5,312 / 11,712 (N 22,560) | +3.45 +- 2.32 | +3.45 +- 2.32 | +6.74 | 2.93, same bounds |
All three: 10+0.1 s, Threads=1, Hash=16MB, Renegade's own OpenBench, no LTC in the commit history, book not stated
(the test host https://zzzzz151.pythonanywhere.com/test/2526/ serves a "Coming Soon" placeholder, saved by the researcher).

## Reading rule and constants
- Renegade = MIT at HEAD 2a134aecbc AND at the three cited commits (tools/licence_at.py --row re-run: a7d8f48c92,
  74f88cf831, a3ef409470 all MIT; rows appended to notes/T04R/licences.md). The researcher recorded only HEAD; the rule
  asks for the exact commit read -> recording gap, corrected in the three cards, not a violation (tier unchanged).
- Clover e647926a8f and Simbelmyne c0ee92c7a0 re-run: GPL-3.0; sources.md shows only commit titles / messages / test
  blocks / PR text for them (Clover PR #324 re-checked via API: title "Give bonus for move that matches bestmove of
  current king-pawn structure", merged 2025-04-14, body empty). No GPL source file or diff in the scratch folder.
- The three saved Renegade diffs (MIT) were re-read against the mechanism texts: all three match (count 1..3 on the
  best move only, malus at the base size; table by side to move and a pawn-key slice, bonus only when not killer /
  counter; update block widened to any best move, killers / counter / cutoff count kept for real cutoffs). None of
  Renegade's constants (table size, ordering bonus, bonus curve, the plain count multiplier) appears in a card; the
  cards propose own start values and ranges (k = 60 in 0-150; PawnRefutationBonus own; PvRaiseFullUpdate 25-100 %).
- Extra check for T04R-03: Renegade/Search.cpp at a3ef409470 sets bestMove only inside `score > alpha`, so the widened
  condition means "alpha was raised", exactly as the card says (it would otherwise have fired at fail-low nodes too).

## Forge-has-it (greps re-run, cited lock lines printed)
- T04R-01 grep reproduces: 4 hits, all the per-ply `cutoff_count` (hpp:273, s:905, s:1145, s:1180). Lines s:731, s:753,
  s:157-160, s:1148-1163, s:1198-1204 all match the card. CORRECTION: "Lacks it" is overstated - the lock already gives
  a quiet move whose reduced search beat alpha a fixed half continuation-history bonus (`src/search.cpp:1153-1156`,
  "a late quiet move that beat expectations"); that is a one-step version of counting the reduced-depth fail-high. The
  real gap is the count-scaled bonus at the final cutoff in main / capture history. Marked "partly" in the card.
- T04R-02 grep reproduces: 0 hits for positional_move / refutation / pawn_move_table / structure_move; pawn key exists
  (board.cpp:762, :1048) and is used only by correction history; quiet ordering = killers + counter (s:733-740).
- T04R-03: s:1201-1204 = quarter main-history bonus for a quiet PV best move without a cutoff, nothing else; matches
  notes/T04F/DIFF.md row 83. Card text correct.

## Duplicates (grep over cards/*/, notes/T04/TABLE.md, notes/TRIED_GATES.md, notes/T05/SPEED_LIST.md,
notes/T02/TABLE.md, notes/T01/recipes.md; tools/tried_gates.py --grep)
- Fail-high-count bonus: no other card. Tried gates with "FailHigh" are aspiration / blend options (15, 28, 36, 42),
  unrelated. T04G-05 shares the update site (depth + 1 when the score reached the eval) but a different trigger; the
  card already says gate them one at a time. T04C-04 / T04D-03 / T04G-03 are malus-by-count merge markers (malus side).
- Pawn-structure refutation move: grep hits T04-04, T05D-03, T05F-01 are pawn-key uses for correction history /
  prefetch / eval memo, not an ordering move. No duplicate.
- Full update on alpha raised: hits T04G-02 (capture-history split), T04H-01 (ttpv on fail-low) are unrelated. No
  duplicate. T04R-03 at +3.45 STC would clear the full-card bar by number; the researcher's downgrade to a one-liner
  because the lock already has the quarter-bonus path is a reasonable judgement, not a finding.
- Cross-references checked and present: T04F DIFF rows 62 / 83, T04D TABLE row 15, T04B TABLE low-depth SE row,
  T04C TABLE B28, T04 TABLE qsearch move-count row (named QsMovePrune there, QsMovePrun in TABLE.md: spelling only).

## Corrections applied (no card deleted, no Status line changed: no violation, no duplicate)
1. T04R-01 Licence: LICENSE at the cited commit a7d8f48c92 = MIT (row added). Forge fit: "lacks" -> partly (s:1153-1156).
2. T04R-02 licence field: LICENSE at 74f88cf831 = MIT; Elo field: W/L/D and about +4.2 nElo added.
3. T04R-03 licence field: LICENSE at a3ef409470 = MIT + the bestMove check; Elo field: W/L/D and about +6.7 nElo added.
4. notes/T04R/licences.md: three exact-commit rows appended.

## Unverifiable
- Book of Renegade's tests (not in the messages, host gone). No LTC for any of the three (none in the history).
- The published LLR values: an own GSPRT formula on the final counts gives 4.08 / 2.64 / 4.17, not 2.90 / 2.90 / 2.93;
  a sequential test's final LLR is the crossing value under the host's own variance model, so this is not a correction.
- Clover PR #324 and Simbelmyne "failhigh-lmr" mechanisms (GPL, no text): correctly left without numbers / cards.

## Other rule checks
No vendor / model-company names in cards/T04R or notes/T04R (grep clean). Nothing written on D: except the board
lines. T04R-01 stays <= 60 lines after the corrections; the one-liners keep 7 pipe-separated fields.
