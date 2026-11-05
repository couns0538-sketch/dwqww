# T06D verify (adversarial re-check of cards/T06D, 2026-11-05 05:57-06:0x PC clock)

Scope: 3 cards (T06D-01 full, T06D-02 one-line, T06D-03 full), notes/T06D/{sources,licences,TABLE}.md.
Method: every cited PR body / commit message re-fetched with `gh api` (PR text and commit messages only, no source
file, no diff; scratch F:/odr/work/T06D-verify/), every Elo recomputed from the W/L/D and the pentanomial, every
lock `file:line` re-read in src_al1s198_clean, licence rows re-run, forge_has greps re-run, tried_gates, duplicate
grep over all cards, card_lint, names grep.

## 1. Source numbers: 19 of 19 reproduce (no correction)
Recomputed with the logistic formula, 95 % error from the per-game (trinomial) or per-pair (pentanomial) variance
(F:/odr/work/T06D-verify/elo.py). Card value | recomputed:
- Stockfish PR 722 STC 9832/9481/29060 -> +2.52 +- 1.96 | +2.52 +- 1.96; LTC 1408/1255/6218 -> +5.99 +- 3.96 | same.
- Stockfish PR 2415 STC 5819/5632/14847 -> +2.47 +- 2.77 | same; LTC 5042/4784/20774 -> +2.93 +- 2.21 | same.
  (Card calls these "own logistic calc from W/L/D": correct, trinomial error, and the PR text gives no Elo.)
- Sirius 267 +10.77 +- 4.83 (penta [93,812,1653,950,137], 7,290 g) | +10.77 +- 4.83; 335 +4.62 +- 2.88 | same;
  120 +10.46 +- 6.06 | same; 164 +4.07 +- 3.15 | same; 167 +4.57 +- 3.42 | same; 184 +0.92 +- 5.20 | same.
- Clockwork 387 STC +18.10 +- 6.18 | +18.10 +- 6.17; LTC +17.48 +- 5.89 | +17.48 +- 5.88; 364 STC +2.95 +- 2.18 |
  same; LTC +7.04 +- 3.62 | same; Endgames.epd +14.99 +- 4.97 | +14.99 +- 4.96; 367 +8.34 +- 4.10 / +4.35 +- 2.73 |
  +8.34 +- 4.09 / same; 368 +6.78 +- 3.67 / +4.23 +- 2.65 | same / same.
- Every pentanomial sums to N/2 pairs; TC, Threads=1, bounds, LLR and game counts match the re-fetched texts
  (Sirius 8+0.08 Threads=1 Hash 16; Clockwork STC 8+0.08 / LTC 40+0.4 Hash 64; Stockfish 722 [0,5] both, 2415 STC
  [-1.5,4.5], LTC [0,3.5]). PR 335's "tested with a bug (the same bug #309 ...)" is quoted as written.
- Stockfish 2016/2019 and Clockwork are hand-crafted-eval engines; Sirius as HCE rests on notes/T04S/TABLE.md row
  20 ("Sirius hand-crafted eval terms ... king flank, pins in eval"), as the cards say ("not re-verified").

## 2. Reading rule and constants: no violation
- All 15 sources are PR lists, PR bodies, commit messages and test blocks; no source file of Sirius (no licence),
  Stockfish (GPL) or Clockwork (AGPL) was named or fetched (sources.md 1-15 and my re-fetch agree).
- No other engine's weight is proposed: all new rows start at 0 and are fitted with Forge's own T06C-01 recipe
  (K 2.25, b 0.6 are the crew's own fit settings, cards/T06C/T06C-01 lines 18-20). The one PR that names a rule
  (722: double attacks not covered by a pawn count twice) is cited as a rule, not a value; 2415 says "constant is
  arbitrary" and gives none.
- Provenance note (not a violation): T06D-01's "camp = own first five ranks" and T06D-03's sign-preserving clamp
  are shapes of the older public Stockfish HCE that the fetched PR texts do not state; both are masks / forms
  without a carried constant and go to the holdout filter as variants. The crew should treat the camp depth (4-6
  ranks) as a free design choice.

## 3. Lock greps and line references: all reproduce
- `forge_has.sh 'flank'` 0; `'initiative|complexity|winnable'` 0; `'tropism'` 0; `'OnQueen|queen_threat|...'` 0.
- `'pinn|pin_|xray|x_ray|discover'` = 9 hits: 8 in src/board.cpp (:55-61, :982-988, check detection) and 1
  comment in src/eval.cpp:189 inside the WeakQueen block ("not pinned down"). T06D-02 said "all src/board.cpp,
  none in eval.cpp": corrected inline in the card; the conclusion (no pinned mask for the eval) stands.
- Re-read and correct: eval.cpp:45 attacked_by, :124-130 x-ray mobility (bishops through own queens, rooks through
  own queens and rooks), :133-135 attacked_twice, :145-148 zone units, :192 WeakQueen, :225 StormDistance,
  :230-252 king danger (weak :236-238, safe checks :243-247, no-queen halving :249, shelter :250, KingDanger :252),
  :346-372 scale_factor with exactly the rules the card quotes (0 / 12; 32 + 4p / 48 + 2p; min(64, 44 + 5p)),
  :437-438 mobility_area, :457-458 scale applied; eval_params.hpp:13-16, :35-38, :47; eval.hpp:52-65 PawnEntry;
  search.cpp:620 HCE + network.
- tried_gates.py --grep 'flank|tropism|pin|winnab|complex|initiative|discover|KingFlank|Hce': 0 of 111 gates.

## 4. Licence rows: all 6 reproduce; 3 rows added
Sirius 8fb68a9d72 / 3a2c3d72d1 / a84d90b121 no licence; Stockfish 691a8ce271 GPL-3.0; Clockwork bedb1e8b26 /
92b9cb844a AGPL-3.0: identical to notes/T06D/licences.md. Gaps closed (appended, tagged "added by verify"):
Clockwork ef52bf5ce9 and 4dd87cf3d2 (cited by T06D-03, no row) AGPL-3.0; Stockfish PR 2415 at its head commit
6c048ce44f GPL-3.0 (the PR's merge sha b3292e06eb is a dead test-merge, HTTP 422, as the worker noted). Sirius PRs
120 / 167 / 184 (a9c753678b, 903af0e47b, 1f0dbb1ba0) have no own row; the repo has no licence file at any date
read, so the tier is the same - note only.

## 5. Duplicates: none
Grep over all cards for flank / tropism / pinned / pin-aware / winnab / complexit / initiative / discoverer: the
only hits are T06-03 (complexity = |residual|, post-net) and T06B-01 (complexity in LMR), which T06D-03 names and
distinguishes; T05C-01 (pin cache for legality, search speed) and T12B-02 are unrelated. notes/T06/DEAD_ENDS.md
line 7 ruled classical winnable terms "out of track" for T06 (post-net transforms) because they need a retrain;
T06D-03 answers that with the frozen-net fit, so it is a new angle, not a duplicate. Neither full card names
T06C-02 (residual retrain after a refit) as the follow-on if the fitted rows are non-zero - worth one line later.

## 6. Format
card_lint: 0 findings, 0 PENDING on all three. T06D-01 and T06D-03 are exactly 60 lines (the cap), so nothing was
added to them. One-liner T06D-02 has the 8 fields. Names grep over cards/T06D and notes/T06D: clean.

## Verdict
3 cards checked, 3 confirmed. Corrections: 1 (T06D-02 hit-count split, inline). Violations / duplicates: 0.
Unverifiable from PR text: Sirius = HCE (T04S row 20 only); the camp / clamp provenance note above; "no pin-in-eval
title among 406 Clockwork titles" (not re-run). Scratch: F:/odr/work/T06D-verify/ (fetched texts + elo.py).
