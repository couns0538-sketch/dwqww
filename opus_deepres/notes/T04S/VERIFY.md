# T04S verify (adversarial pass over cards/T04S, board slot S1)
Start 05:21 PC clock (date); all checks finished by 05:26 (date); write-up after that; done time = the board's Done line.
Wrap-up note F:/odr/work/pool_wrapup.txt: checked before every source and file, never present.
Scratch: F:/odr/work/T04S-verify/ (elo.py recompute script copied from T04R-verify; pr_*.json = the five cited PR
bodies re-fetched with gh api pulls/N: number, title, merged_at, merge sha, head sha, body; no diff, no file).

## Result: 2 cards checked, 2 confirmed, 1 correction (T04S-01, missing test and variant labels added), 0 violations, 0 duplicates, lint 0 findings after the correction (60 / 59 lines)

## Numbers (recomputed from the W/L/D and penta blocks of the PR bodies, gh api; Elo and error to 0.02, nElo own)
| card | source / test | W / L / D | Elo +- 95 % (card) | recomputed (penta error) | nElo own (card) | published LLR / bounds |
|---|---|---|---|---|---|---|
| T04S-01 | Sirius #328 test 1091 STC (blend 3/4 S + 1/4 entry) | 3,623 / 3,391 / 6,734 (N 13,748) | +5.86 +- 3.36 | +5.86 +- 3.36 | +10.14 (+10.1) | 2.95 (-2.94, 2.94) [0,3] |
| T04S-01 | Sirius #328 test 1092 pure sum vs that blend (was missing) | 7,597 / 7,327 / 14,162 (N 29,086) | not in card | +3.23 +- 2.30 | +5.60 | 2.97 [0,3] |
| T04S-01 | Sirius #328 test 1093 LTC (variant not labelled) | 1,220 / 1,028 / 2,394 (N 4,642) | +14.38 +- 5.27 | +14.38 +- 5.26 | +27.32 (+27.3) | 2.97 [0,3] |
| T04S-01 | Sirius #330 test 1100 STC (stage 2) | 4,916 / 4,675 / 9,013 (N 18,604) | +4.50 +- 2.83 | +4.50 +- 2.83 | +7.94 (TABLE +7.9) | 2.97 [0,3] |
| T04S-01 | Tarnished #132 test 4877 STC | 11,636 / 11,380 / 16,792 (N 39,808) | +2.23 +- 1.70 | +2.23 +- 1.70 | +4.48 (+4.5) | 2.95 [0,3] |
| T04S-01 | Tarnished #132 test 4888 LTC | 8,233 / 7,999 / 15,890 (N 32,122) | +2.53 +- 1.85 | +2.53 +- 1.85 | +5.21 (+5.2) | 2.96 [0,3] |
| T04S-01 | Clockwork #234 test 497 STC | 952 / 806 / 1,702 (N 3,460) | +14.67 +- 7.14 | +14.67 +- 7.12 | +23.85 (not in card) | 3.04 [0,5] |
| T04S-02 | Sirius #229 test 488 STC | 4,267 / 4,024 / 7,685 (N 15,976) | +5.29 +- 3.19 | +5.29 +- 3.19 | +8.94 (+8.9) | 2.95 [0,3] |
TCs, Threads=1 and Hash as in the cards (Sirius 16 / 64 MB, Tarnished 32 / 128 MB, Clockwork 16 MB); no book named in
any body (the cards say so). Merge shas and dates match gh api: 9d808836c6 2025-11-17, 3b2cd0247b 2025-11-23,
b91b2a1e75 2024-12-21, 2bd208333e 2025-11-26, 413106d9bc 2025-09-28.

## Correction applied (T04S-01, Expected gain, inside line 39 so the card stays at 60 lines)
The Sirius #328 body holds three tests and labels the +5.86 STC run "base = 3/4 x conthist + 1/4 x entry" - a blend of
the summed score and the entry's own value. Its test 1092 then ran the pure-sum base against that blend and won
(+3.23 +- 2.30, n=29,086, [0,3], LLR 2.97), so the form Sirius merged is the pure sum, which is also what the Tarnished
and Clockwork titles say ("sum as base"); the LTC +14.38 is "against main" without a variant label. The card had the
blend's STC number next to the pure-sum engines' numbers with no label and without test 1092. Added as "(corrected by
verify: ...)". Consequence for the design (the researcher's start value stands): the only A/B in the sources
favours p = 100 over 75, so the first ON sweep of ContHistSumBase should include 100, not only the start 60. Status
stays COMPLETE (a gap in the numbers, not a violation).

## Reading rule, licences, constants
- Licence rows re-run at the five cited merge commits (tools/licence_at.py --row): Sirius 9d808836c6 / 3b2cd0247b /
  b91b2a1e75 = no LICENSE file (all rights reserved); Tarnished 2bd208333e = no LICENSE file (API tier GPL-3.0, the
  file came later); Clockwork 413106d9bc = AGPL-3.0. Identical to notes/T04S/licences.md. All ideas-only; the cards say so.
- Reading: the researcher's scratch F:/odr/work/T04S/ holds PR lists (jsonl with number / title / merged date / body
  only), parsed test blocks, mine_commits outputs, Tarnished's README (allowed) and four own scripts; grep for
  "diff --git", "+++ b/", "#include": no hit. No source file or diff of any engine was fetched. The Sirius #328 body links
  a PlentyChess commit with a diff anchor (PlentyChess = GPL-3.0 in WORKER_RULES); the name appears only inside the
  cached PR bodies, and sources.md / the card say "not read": the link was not opened by the researcher and not by me.
- Constants: Sirius's 3/4 : 1/4 blend and "half of main history" (#330) are not carried over; the card proposes own
  start 60 in 0-100 and own 25 for stage 2. "Ply 4 at half weight" is the lock's own existing rule (search.cpp:725).
  T04S-02 carries no constant (Caissa's non-PV / alpha-below-draw condition is a condition, not a tuned value).
- Mechanism texts: both in own words, no code; T04S-02 builds on the Caissa (MIT) description already in
  notes/T04F/DIFF.md row 1 and is consistent with it.

## Forge-has-it, lock lines, tried gates, duplicates
- `bash tools/forge_has.sh 'apply_history|skip_quiets'`: 17 hits, apply_history at src/search.cpp:157 as the card
  says; `'cuckoo|upcoming|game_cycle|has_repeated'`: 0 hits. Lock lines read: HistoryMax :107, apply_history :157-160
  (entry-local gravity), quiet_history :704-712 (main + cont1 + cont2), update_continuation :720-727 (plies 1, 2, 4;
  ply 4 at bonus / 2), callers :743 / :748 / :1156 / :1208; is_draw :692-702 called at :780 (qsearch) and :893
  (search); Board::is_repetition src/board.cpp:892-910; halfmove_clock include/forge/board.hpp:157. All as cited.
  "base can reach about 2.5 x HistoryMax" = 16384 + 16384 + 8192: correct.
- Tried gates (tools/tried_gates.py --grep): ContHist4Pct gates 31-33 (an ordering weight), ContCorrectionWeight 87,
  CorrUpdateMode 63 / 68, ThreatHist 64; nothing changes the history update's gravity base, nothing on repetition or
  cycle detection. The TABLE's gate numbers are right.
- Duplicates (grep over all 98 card files under cards/*/): no card proposes the summed-base update; T04E-03 (index-decayed malus) and
  T04F-02 (capture-keyed conthist tables, itself a DUPLICATE of R15 C5) are different levers; T04F-03 (twofold rule)
  states Forge "cannot receive" cycle detection (0 hits) - T04S-02 fills exactly that gap with a different test and
  different code. Cross-track rows cited by the cards match: notes/T04E/TABLE.md row 39 (Viridithas #370 LTC +2.84
  +- 2.00 n=28,128) and row 40 (#465 LTC +2.27 +- 1.70 n=36,622), notes/T04B/TABLE.md row 28 (Stormphrax PR 270 LTC
  +1.28 +- 1.03 n=105,480), notes/T04F/TABLE.md row 4 / DIFF.md row 1 (Caissa 8e9ce37 +1.03 +- 1.33 [0,2] n=124,388,
  not passed).
- Reverts: the cached Sirius list (352 PRs, 1-356) has three reverts: #224 (reverts #219 and #222, bad worker), #269
  (reverts #268), #349 (reverts #345, eval scaled by the half-move clock, LTC -0.06). None touches #328, #330 or #229.
  #228 "Start checking for repetitions from 4 plies back instead of from 2 plies back" merged 2024-12-19, body = bench
  only: as the card says. Tarnished (58-160): no revert of #132; the later #143 "Conthist 4 ply" is a different change.
- Lint: tools/card_lint.py on both cards = 0 findings, 0 PENDING, before and after the correction; 60 and 59 lines.

## Unverifiable (recorded, not chased: usage budget, 15-minute window)
- Published LLR values: my pentanomial GSPRT recompute with Elo bounds gives 4.46 / 3.76 / 5.37 / 4.31 / 4.30 / 2.92 /
  3.48 / 4.61 against published 2.95 / 2.97 / 2.97 / 2.97 / 2.95 / 2.95 / 2.96 / 3.04 (table order); the hosts' LLR
  variant (normalized vs Elo bounds, update timing) is not stated in the bodies. Elo and error bars all reproduce, so
  the cards' numbers stand; the LLRs are quoted as published.
- Test-host pages (the three OpenBench instances) not opened; the PR bodies via gh api were used instead. The Clockwork
  VLTC "+34" (test 503) is second-hand from the Sirius text, as the card already says.
- Viridithas #370 / #465 and Caissa 8e9ce37 numbers taken from the T04E / T04F tables, not re-opened.
- "Sirius = hand-crafted eval", "Clockwork = hand-crafted eval", "Tarnished = NNUE" and "Sirius was a weak engine in
  2024-12" were not checked (no README of Sirius or Clockwork read); the card's "HCE engines gain more" reasoning and
  the +1 to +4 range rest on them. The Sirius PR titles 115-335 that add eval terms (TABLE row 20) are consistent with HCE.
- Books: none named in any body; recorded as missing by the cards.
