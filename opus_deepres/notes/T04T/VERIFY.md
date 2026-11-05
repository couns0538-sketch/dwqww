# T04T verify (adversarial pass, fable, started 05:56 PC clock; end time = the board Done line)
Scope: cards/T04T/T04T-01..03. Re-opened every cited source number (gh api PR bodies, PR text only), recomputed Elo /
error / nElo from the published pentanomials (F:/odr/work/T04T-verify/elo.py), re-ran the licence rows at the cited
merge commits and the Forge-has greps against the lock, read the cited lock lines, checked duplicates against all
cards and notes/TRIED_GATES.md, re-ran tools/card_lint.py. No source file or diff of any GPL / AGPL repo was opened;
no engine edit, build or run. Verdict: 3 cards checked, 3 confirmed, 3 in-line corrections / notes, 0 violations,
0 duplicates, lint clean.

## 1. Sources re-opened (live PR bodies, 2026-11-05 06:00)
| source | checked against the card | result |
|---|---|---|
| Clockwork #380 (b10cbf0133, merged 2026-03-16) | STC 8+0.08 16 MB +5.33 +- 3.19 n=15,584 LLR 2.95 [0,3] penta [177,1808,3606,2001,200]; LTC 40+0.4 64 MB +9.69 +- 4.28 n=7,068 LLR 2.95 penta [27,769,1758,940,40]; links ob.cwchess.org/test/1267, /1272; text "saw this in sf ... heavily interacts with the conthist patch" | all match |
| Clockwork #234 / #181 / #252 | sum-base update merged 2025-09-28; 4-ply conthist 2025-09-12; 6-ply conthist 2025-10-01 (all before #380) | match |
| Clockwork #332 (4915ccded1, merged 2025-11-24) | STC +2.46 +- 1.89 n=42,732 LLR 2.96 [0,3] penta [453,5091,9969,5406,447]; LTC +3.50 +- 2.36 n=23,344 LLR 2.96 penta [123,2660,5878,2881,130]; links clockworkopenbench.pythonanywhere.com/test/999, /1000; body = test blocks only | all match. Title says "with quiet history"; "the TT move's" is the worker's reading (noted in the card) |
| Clockwork #339 (8d70304fdf, merged 2025-12-24) | 40+0.4 +0.23 +- 1.08 n=111,196 LLR -2.96 (H0); 120+1.2 128 MB +1.92 +- 1.52 n=52,904 LLR 2.95 | match |
| pawnocchio #57 (64a744b5ee, merged 2026-04-17) | STC 10+0.1 16 MB +2.18 +- 1.85 n=34,816 LLR 2.42 of (-2.25, 2.89), not concluded; LTC 40+0.4 64 MB +2.92 +- 2.05 n=25,426 LLR 2.90 passed; penta both match; furybench.com/test/6040, /6050; body = test blocks only | all match |
| Reckless #759 (c23dfb39f8, merged 2026-03-08) | STC +2.37 +- 1.76 n=39,016; LTC +3.35 +- 2.23 n=20,920 (T04E row 21 numbers) | numbers match T04E. T04E's row gives no TC / bounds; the body says STC 8+0.08 LLR 3.04 and LTC 40+0.4 LLR 2.89, [0,3], Threads=1, both passed. Title "Standardize fail-firm in ProbCut": whether ProbCut already had a fail-firm form there or only now got the engine's standard one is not stated (body = test blocks only). Corrected in card 02 |
No book is named in any of the five bodies (the cards say "book missing": correct).

## 2. Elo recompute from the pentanomials (own script, 95 % error, nElo per game = (mu - 0.5) / sqrt(2 var_pair) * 800 / ln 10)
01 STC +5.33 +- 3.18 nElo +9.1 | 01 LTC +9.69 +- 4.28 +18.4 | 02 STC +2.18 +- 1.85 +4.3 | 02 LTC +2.92 +- 2.05 +6.1 |
03 STC +2.46 +- 1.89 +4.3 | 03 LTC +3.50 +- 2.36 +6.6. All equal the cards (one error bar 3.18 vs 3.19 = rounding).

## 3. Reading rule and constants
- F:/odr/work/T04T/ holds only PR-listing jsonl pages (metadata + bodies), parsed test tables, commit-message listings
  and own scripts: no .diff, .patch or source file. sources.md (8 lines) names PR text / commit messages only. OK.
- No other engine's tuned constant is proposed: card 01 is a binary skip; card 02's subtraction is own design (the
  sources state no formula); card 03 keeps the lock's own margin 24 and an own knob. Gap (not a violation): card 03
  gives no own start value / range for DextHistDiv (one-liner; noted in the card).
- Card 01's indirect-path claim checked in the lock: `ss->continuation` (:1121) is one table set indexed by
  [moved piece][to] with no offset dimension, so ply-4 writes (:721-725) land where :708-709 read at offsets 1 and 2:
  ON is not a no-op, the claim holds. Card 02: entry guard `!is_mate_score(beta)` (:1002) and exit test
  `value >= probcut_beta` (:1022) exist, so `value - (probcut_beta - beta) >= beta` holds. Card 03: :1102 fixed margin,
  `!pv_node`, `inherited_double_extensions <= 6`; :1105-1106 multicut. All cited lines (:704-712, :721-748, :784,
  :902, :948, :1001-1024, :1100-1115, :1121, :1137, :1156, :1198, :1208; search.hpp:275) read as cited.

## 4. Licence rows at the merge commits (tools/licence_at.py --row, 06:00)
Clockwork b10cbf0133 AGPL-3.0; Clockwork 4915ccded1 AGPL-3.0; pawnocchio 64a744b5ee GPL-3.0: identical to
notes/T04T/licences.md. (#339's 8d70304fdf and Reckless c23dfb39f8 have no row; same repos / tiers, PR text only.)

## 5. Forge-has greps (re-run)
`for \(const int back : \{1, 2, 4\}\)` -> :721 (1 hit); `ss - 4` -> :948 (1 hit); `ContHist4` -> 0 hits;
`return value;` -> 3 hits (:165, :1024 ProbCut exit, uci.cpp:80; the card names :1024, correct);
`singular_beta - 24` -> :1102 (1 hit). All as in the cards.

## 6. Duplicates and tried gates
- Cards grepped for probcut / fail-firm / double-ext / conthist / continuation: T04C-01 (qsearch fail-firm, other
  site, named in card 02), T04S-01 (sum-base, named in card 01), T04-06 (triple step), T04C-02 (singular beta at
  ttpv), T04F-02, T04G-05, T04R-01/03: none is the same idea. No ProbCut card exists in cards/T04E (table-only row).
  No duplicates.
- tried_gates: no Probcut gate; ContHist4Pct gates 31-33 (no decision) and bundle gate 68 (ContHist4Pct=45 inside,
  H1 at [0,10]) - added to card 01 as a neighbour, not a duplicate (weight vs in-check skip); FailHighBlend 36/42
  (no decision) and RfpReturnBlend gate 86 (H0, -16.42) as card 02 says; CheckExtDepthCap gate 59 (-1.85, no
  decision) as TABLE row 5 says.

## 7. Caps, lint, format
8 sources (<= 15), 0 forum threads, 3 engines deep-read (Clockwork, pawnocchio, Horsie) plus Seer by the miner listing
only (borderline, not a deep read); 3 cards (<= 4), 2 full + 1 one-liner; card 01 = 60 lines (at the cap, edits kept
in-line), card 02 = 53, card 03 = 1. No vendor names. card_lint.py: 0 findings, 0 PENDING on all three after the edits.

## 8. Corrections made (in-line, nothing deleted)
- T04T-02 line 37: Reckless #759 TC / bounds / LLR added from the PR body and the "Standardize" title caveat
  (whether #759 introduced or only changed ProbCut fail-firm is not stated).
- T04T-01 line 56: bundle gate 68 (ContHist4Pct=45, H1) named as a tried neighbour.
- T04T-03: note that "the TT move's" is the worker's reading of "quiet history" and that DextHistDiv needs an own
  start value and range.
Unverifiable from PR text: the exact ply set Clockwork skips (#380), the fail-firm formulas (#57, #759), the sign of
the history term (#332). The cards already say so. Status lines unchanged (no violation, no duplicate).
