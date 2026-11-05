# T06E verify (adversarial re-check of cards/T06E, 2026-11-05, started 06:35 PC clock)

Scope: 2 cards (T06E-01 full, T06E-02 one-line), notes/T06E/{sources,licences,TABLE}.md.
Method: every card source re-fetched with `gh api` (commit messages and PR bodies only, no source file, no diff;
scratch F:/odr/work/T06E-verify/), every Elo recomputed from the W/L/D or the pentanomial with an own script
(F:/odr/work/T06E-verify/elo.py, not the worker's), every lock `file:line` re-read in src_al1s198_clean, the 7
licence rows re-run, both forge_has greps re-run, tried_gates, duplicate grep over all cards, card_lint, names grep.

## 1. Source numbers: 11 of 11 reproduce (no correction)
Logistic Elo, 95 % error from the per-game (trinomial) or per-pair (pentanomial) variance. Card | recomputed:
- Stockfish 6d8f583 STC 7346/7052/20731 -> +2.91 +- 2.33 (35,129 g) | +2.91 +- 2.33; LTC 6695/6414/29333 ->
  +2.30 +- 1.84 (42,442 g) | same. Message re-fetched: LLR 2.96 (-2.94,2.94) [0.00,5.00] both, dated 2018-03-07.
- Stockfish 1093047 STC 4817/4570/13610 -> +3.73 +- 2.87 (22,997 g) | same; LTC 1891/1705/8330 -> +5.42 +- 3.42
  (11,926 g) | same. Message re-fetched: LLR 2.95 [0.00,4.00] both, "Closes PR 1473", dated 2018-03-09.
- Sirius 271 penta [417,3837,7364,4045,456] (16,119 pairs = 32,238 g) -> +3.08 +- 2.25 | +3.08 +- 2.25; the PR body
  prints the same block (8.0+0.08s Threads=1 Hash=16MB, LLR 2.96 [0.00,3.00], W/L/D 8575/8289/15374), merge
  64b845b139 on 2025-04-01, body = "Idea from stockfish and berserk" + the three links the card names.
- Sirius 185 penta [169,2049,3926,2135,221] (8,500 pairs = 17,000 g) -> +3.88 +- 3.04 | +3.88 +- 3.04; body = one
  test block (LLR 2.95 [0.00,5.00], W/L/D 4410/4220/8370) and nothing else, merge 867546045e on 2024-09-15: the
  card's "own form from the PR title only" is accurate.
- TABLE-only rows (arithmetic from the logged counts): Sirius 258 penta -> +7.89 +- 4.07 | same; Perseus 100 penta
  -> +9.85 +- 4.62 | same; Berserk 219 W/L/D 983/833/1792 -> +14.45 +- 8.04 | same (see section 7 for the texts).
- "[0,5] BayesElo era" for the 2018 Stockfish tests is right (fishtest bounds were BayesElo then); "no LTC" for both
  Sirius PRs is right (one block each). Each 95 % error in the cards is the pentanomial one where a pentanomial exists.

## 2. Reading rule and constants: no violation
- The four card sources are two commit messages and two PR bodies; no source file or diff of Stockfish (GPL) or
  Sirius (no licence) was named or fetched (sources.md 1, 2, 4, 7 and my re-fetch agree). The Perseus README read
  (sources.md 8) is allowed for a GPL repo.
- 6d8f583's message names a fixed bonus pair; the card says "not carried" and neither value appears in the card. All
  new rows start at 0, fit box -10 .. +40 cp (T06E-01) / -30 .. +30 cp (T06E-02) are own; K 2.25, b 0.6 and the 639
  rows are the crew's own T06C-01 settings (cards/T06C/T06C-01 lines 16-20). No other engine's tuned constant is
  proposed as a Forge value.
- Both mechanisms are own forms: T06E-01's landing-mask variants (a)-(e) and T06E-02's StormBlocked[d] outside the
  shelter sum are not in any read text (PR 185 has no description at all).

## 3. Licence rows: 7 of 7 reproduce
tools/licence_at.py --row re-run: Stockfish 6d8f583af2 and 1093047e7d GPL-3.0 (Copying.txt); Sirius 64b845b139,
867546045e, 08def86738 absent = no licence; berserk 5a5ec85439 GPL-3.0; Perseus-Engine 3c95481452 GPL-3.0
(LICENSE.txt). All identical to notes/T06E/licences.md.

## 4. Forge has it: greps and file:line reproduce
- `forge_has.sh 'OnQueen|queen_threat|QueenThreat|[Tt]hreat.*[Qq]ueen|[Qq]ueen.*[Tt]hreat'` = 0 hits (as the card).
- `forge_has.sh '[Ss]torm'` = 4 hits (eval_params.hpp:47-48, eval.cpp:225, eval_params.cpp:71); none splits a blocked
  storm pawn from a free one; `'[Bb]locked|flank'` = 5 hits, all PassedBlocked / mobility, none in the shelter loop.
- Re-read lines: evaluate_threats eval.cpp:276-316 (current attacks only), strongly_protected :282, per-type
  attacked_by :135 with bishop / rook x-ray through own queens / rooks :124-130, WeakQueen :189-192 (enemy slider on
  our queen now = the opposite relation, as the card says), shelter loop :212-227 with the storm row :225, attacker
  gate :232-233, queen_checks :246, no-queen halving :249, KingDanger index :250-252; eval_params.hpp:39-45 threat
  rows, :47 StormDistance, :49 KingDanger, :72-83 KingSafetyWeights. All as cited.

## 5. Duplicates and tried gates: none
- No other card has a next-move queen threat (grep over cards/*/ for queen/threat: 0 outside T06E). "storm" outside
  T06E = the engine name Stormphrax and T05B-01's pawn-king cache (a speed card that caches the existing shelter /
  storm loop; T06E-02 names it as compatible, correctly). Non-linear king safety (Sirius 258) and the flank term
  (Perseus 100) were folded into T06C-03 / T06D-01 as evidence, not new cards: correct per the Round 2 rule.
- tried_gates.py --grep 'queen|storm|threat|shelter|king': only QsQueenPromoOnly (gate 58) and ThreatHist (gate 64),
  both search options, neither an eval term.
- Cross-references exist: cards/T06C/T06C-01, T06C-03, T06D-01, T05B-01; holdout threshold 0.014310 and the S31
  scorer wording match T06C-01 and the three T06D cards.

## 6. Card rules, lint, names
- card_lint: 0 findings, 0 PENDING in both cards. T06E-01 is 60 lines (cap 60, met). T06E-02 is one line in the
  ONE-LINE field order. 1 full + 1 one-line card is within "top 2 full, at most 4 per sub-track".
- Full-card status of T06E-01 holds under the written rule (a one-liner is "under 3 at STC with no LTC": both
  Stockfish steps passed LTC, Sirius 271 is above 3); the card itself flags that these are the smallest numbers of
  T06D / T06E. T06E-02 as a one-liner is the conservative choice (one engine, STC only).
- Gate route in both cards = the crew's 7-0 decision (Threads=1, [0,5] nElo, alpha = beta = 0.05, pentanomial, cap
  3,000, capped = UNPROVEN / no decision, one extension if positive; STC then LTC). 3,000 g at 430-502 g/h = 6.0-7.0
  h: the "~6-7 h" is right. Both Forge estimates are labelled UNPROVEN; no Forge Elo claim anywhere.
- Names grep (vendor / model-company names) over cards/T06E and notes/T06E: clean. Nothing written outside F:/odr
  by the worker except its board lines.

## 7. Not re-verified / unverifiable
- Sirius as a hand-crafted-eval engine rests on notes/T04S/TABLE.md row 20 (the cards say "not re-verified"); not
  re-checked here either (the Sirius repo has no licence, so only its README would be admissible).
- The Stockfish test pages themselves (tests.stockfishchess.org) were not opened; the W/L/D in the commit messages
  were used, as the card states.
- TABLE rows 4, 6, 7 (Berserk 219, Sirius 258, Perseus 100) are evidence rows, not card sources: see the appended
  line below for whether their texts were re-opened.

## Verdict
- T06E-01: COMPLETE stands. No correction, no violation, no duplicate.
- T06E-02: ONE-LINE stands. No correction, no violation, no duplicate.

## Appended 06:39: TABLE rows 4, 6, 7 re-opened
Berserk 219 (merge 5a5ec85439; body = bench + one block, LLR 2.98 [-1.00,4.00], N 3,608 W/L/D 983/833/1792, no
description), Sirius 258 (merge 08def86738; one block, LLR 2.95 [0.00,3.00], N 10,352, penta as logged), Perseus 100
(merge 3c95481452; one block, LLR 2.95 [0.00,3.00], N 8,182, penta as logged): all three texts match the TABLE and
sources.md; the Berserk term indeed cannot be named from its text, as the dead-end line says. Verify ended 06:39.
