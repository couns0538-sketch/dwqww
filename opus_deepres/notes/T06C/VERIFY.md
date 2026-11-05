# T06C verify (adversarial pass, 2026-11-05, start 01:16 PC clock, stop by 01:36)
Scratch: F:/odr/work/T06C-verify/ (gh api commit texts eth_*.txt / cw_*.txt / sf_*.txt, licence_rows.txt, texel_wiki.html).
Method: every cited commit re-opened with `gh api repos/OWNER/REPO/commits/SHA` (commit text only, no source file of any
GPL / AGPL repo opened), Elo recomputed from W/L/D with -400 log10(1/s - 1), licence rows re-run with
tools/licence_at.py --row, lock lines re-read from src_al1s198_clean, tried gates re-grepped, all 71 other cards listed.

| card | claim | verdict | evidence |
|---|---|---|---|
| T06C-01 | Ethereal b552e36 STC +6.75 +- 4.22, 10+0.1s Threads 1, SPRT [0,4], LLR 2.99, 10,240 games | CONFIRMED | commit text: N 10240 W 2121 L 1922 D 6197 -> recomputed +6.75; LLR 2.99 [0.00,4.00]; test 7551 |
| T06C-01 | Ethereal b552e36 LTC +7.06 +- 3.88, 60+0.6s, LLR 2.96, 8,464 games | CONFIRMED | N 8464 W 1253 L 1081 D 6130 -> +7.06; LLR 2.96; test 7552 |
| T06C-01 | data 3 x ~10M self-play (1s/2s/4s) + ~12.5M FRC | CONFIRMED | commit text, verbatim |
| T06C-01 | 513a93c = [224,32,1] pawn+king net that augments the HCE, cp through a sigmoid "after being offset by a static evaluation" | CONFIRMED | commit text 2020-09-19; STC +25.81 (W484 L344 D1060 -> +25.81), LTC +23.39 (W362 L234 D1308 -> +23.39) |
| T06C-01 | order c8b7199 (09-24) -> b552e36 (09-24) | CONFIRMED | c8b7199 2020-09-24T19:24Z, b552e36 2020-09-24T21:53Z |
| T06C-01 | Ethereal 6771685 +10.51 +- 5.37 / +12.75 +- 5.34 (5,920 / 4,416 games) | CONFIRMED | W1180 L1001 D3739 -> +10.51 (12+0.12s, [0,4]); W684 L522 D3210 -> +12.75 |
| T06C-01 | Clockwork 2844edc +6.67 +- 3.62 / +11.88 +- 4.80 (8+0.08 / 40+0.4, 11,722 / 5,736 games) | CONFIRMED | W2948 L2723 D6051 -> +6.67 [0,3]; W1387 L1191 D3158 -> +11.88 |
| T06C-01 | c495be4 margins re-tune +4.66 / +2.49 | CONFIRMED (wording flag) | W2840 L2631 D10129 -> +4.66; W3928 L3704 D23600 -> +2.49. Flag: c495be4 is 2020-09-05, BEFORE the net (09-19); it followed the HCE-only re-tune 6771685, so it is not evidence of a margin re-tune after a hybrid refit (card line 54 says "after its eval tunes", literally true) |
| T06C-01 | "whether the tuner kept the net output in the loss is not in the commit text" | CONFIRMED | b552e36 text says only "following the NN additions"; nothing on the loss form |
| T06C-01 | lock eval_params.hpp:10 (layout shared with the tuner), eval_params.cpp:8-11, 639 entries | CONFIRMED | forge_has.sh 'texel|eval_params|EvalParam' = 5 hits at those lines; 639 S( entries counted in eval_params_table.inc |
| T06C-01 | eval_params_table.inc:1 = 61,536 games, 4.67M quiet positions, 10k nodes/move | CONFIRMED | header line read |
| T06C-01 | table byte-identical between src_h256_e12 and the lock | CONFIRMED | cmp: TABLE_IDENTICAL and eval_params.hpp HPP_IDENTICAL |
| T06C-01 | search.cpp:620 clamp(HCE runtime + network); board.cpp:17 SeeValue; eval.hpp:52-65 pawn cache; search.cpp:575-576 Worker::clear -> evaluator_.clear() | CONFIRMED | lines read |
| T06C-01 | texel.cpp (h256_e12 tree) K scan :181-196, lambda :226, no per-row net term | CONFIRMED | K loop 0.3..4.0 step 0.05 at :180-197, lambda blend at :226; grep nnue/net in texel.cpp = 0 hits |
| T06C-01 | lock tree holds only include/ and src/ | CONFIRMED | ls src_al1s198_clean |
| T06C-01 | lock b0.6 holdout 0.014310, HCE alone 0.017059; K 2.25; b 0.6 | CONFIRMED | skill forge-nnue-data SKILL.md:65-67 (holdout_013_014_s16, 1,024,286 rows) |
| T06C-01 | FPOS has no castling / ep / clocks; eval.cpp reads none | CONFIRMED | skill forge-nnue-data:86-87; grep castl/en_passant/halfmove/rule50 in lock eval.cpp = 0 hits |
| T06C-01 | hce_dump re-makes the production .hce exactly | CONFIRMED | skill forge-nnue-data:78 |
| T06C-01 | TRIED_GATES 0 of 110 match texel / hce / eval_param / table / psqt | CONFIRMED | tried_gates.py --grep 'texel|hce|eval_param|table|retune|psqt|king|danger|safety|refit' = 0 of 110; packb = ReSearchAdjust/FiftyDamp, packa = NonPawnCorr/PawnHist, E3 = EvalMatScale/EvalOptimism/EvalRule50Damp: none refits the table |
| T06C-01 | ~0.3-0.4 KB per row, <= ~15M rows under the 7 GB guard | UNVERIFIABLE | own estimate from the Sample/Term sizes; not measured |
| T06C-01 | "loss has not predicted Elo, S30" | UNVERIFIABLE | S30 result not re-opened in this pass |
| T06C-01 | STC SPRT ~13-15 h | CONFIRMED | WORKER_RULES Round 2 gate rate 430-502 games/h, ~6.6k games |
| T06C-01 | Forge estimate 0 to +3 Elo UNPROVEN | label present | no Forge Elo claim; labelled UNPROVEN |
| T06C-02 | Ethereal 8d02577 STC +4.72 +- 3.63 (10+0.1s, [0,5], LLR 2.95, 14,640 games) | CONFIRMED | W3152 L2953 D8535 -> +4.72; test 7644 |
| T06C-02 | 8d02577 LTC +2.71 +- 2.17 (60+0.6s, LLR 2.98, 29,072 games) | CONFIRMED | W4423 L4196 D20453 -> +2.71; test 7645 |
| T06C-02 | 8d02577 = S(MG, EG) output + mirroring, 4 days after b552e36; confounded; offset table not stated | CONFIRMED | title "Using Mirroring during mini-batch training, train a new NN to output an S(MG, EG) value", 2020-09-28 vs 09-24; text says nothing on the offset |
| T06C-02 | nnue_train.cpp:15-18 residual form, :48 per-row offset, :197 k = 2.25 | CONFIRMED | h256_e12 tree lines read (the "output layer starts at zero" sentence is at :17-18, the offset field at :48) |
| T06C-02 | standalone and residual nets reach the same holdout loss per position seen (2026-10-28) | CONFIRMED | skill forge-nnue-train-cpu:29 |
| T06C-02 | ~95M presentations per CPU hour, lock net ~7.4G presentations -> ~10 h per 1G, ~78 h full | CONFIRMED | skill forge-nnue-train-cpu:40-41; arithmetic holds |
| T06C-02 | ~305M training rows | UNVERIFIABLE | skill forge-nnue-data:16 gives 231.9M train + 16.4M holdout rows at 2026-10-27 growing ~10M/day (order consistent, exact figure untraced) |
| T06C-02 | .hce regeneration 1-3 h | UNVERIFIABLE | own guess, flagged as such in the card and notes |
| T06C-02 | skill forge-o30-v2net (EvalFileV2, CPU fine-tune trainer) | UNVERIFIABLE | that SKILL.md is not in the project skills folder (worker flagged it); cited from the skill listing only |
| T06C-02 | Forge estimate 0 to +2 Elo UNPROVEN | label present | ok |
| T06C-03 | Clockwork 753f884 STC +9.59 +- 4.45 (8+0.08s, Threads 1, [0,3], LLR 2.95, 7,940 games) | CONFIRMED | W2117 L1898 D3925 -> +9.59; ob.cwchess.org/test/1147 |
| T06C-03 | 753f884 LTC +9.78 +- 4.37 (40+0.4s, LLR 2.97, 7,320 games) | CONFIRMED | W1873 L1667 D3780 -> +9.78; test 1149 |
| T06C-03 | tunable sigmoid fitted by the gradient tuner, precomputed integer table at inference, HCE-only engine | CONFIRMED | commit text ("Idea from Perseus" - not in the card, no number attached) |
| T06C-03 | eval_params.hpp:72-84 KingSafetyWeights = 10 fixed ints (4 attacker units, weak_square, 4 check weights, shelter_divisor) | CONFIRMED | lines read; KingDanger = 100 table entries indexed by units (hpp:49, eval.cpp:252) |
| T06C-03 | texel.cpp --king-safety only sets the fields, never fits | CONFIRMED | texel.cpp:84-92 argument parse writes the 10 ints; no gradient on them |
| T06C-03 | ranges "each unit +-2 around the lock value" | ok (own ranges) | Forge's own values, no Clockwork constant carried |
| T06C-03 | Forge estimate 0 to +2 Elo UNPROVEN, crew ~3 h | labels present | ok |
| licences | 7 rows in notes/T06C/licences.md (Ethereal x4, Stockfish x1, Clockwork x2) | CONFIRMED | tools/licence_at.py --row re-run: all 7 rows identical (GPL-3.0 / AGPL-3.0 at the exact commits); chessprogramming row is a text-licence note, not re-fetched by the tool |
| TABLE.md | row 3 "eval_params.hpp:68-79" | CORRECTED | the struct is at 72-84 (card T06C-03 has it right); fixed in TABLE.md with "(corrected by verify)" |
| TABLE.md | row 4 names Clockwork 2844edc without a link while card T06C-01 line 9 points to that row for the link | CORRECTED | commit URL added to row 4 |
| TABLE.md | row 7 Stockfish e0bafa1 "~+1.3" LTC | CONFIRMED (rounding) | W19430 L18850 D121464 -> +1.26, NNUE=False as stated; 767b4f4 -> +0.86 / +2.62 as stated |
| TABLE.md | rows 8, 9 Ethereal 3112e84 (+5.46 / +3.36), 5e25d42 (+11.06 / +8.46; +0.22 at [-3,1], 62,056 games) | CONFIRMED | all recomputed from W/L/D |
| TABLE.md | row 5 Texel 1.03 series +99.6 over 7 steps, 32,000 games at 1+0.08 | CONFIRMED | wiki page fetched: 99.6, 39.4, 24.6, 32000, 1+0.08 present |
| sources.md | Ethereal b9b8463 (2021-05-29 full NNUE), Stockfish c25d4c4 (~+3.72 / ~+2.08), Clockwork datav3 / v5 / v4 series, "30 tuning commits mined" | see addendum below | not re-opened in the main pass (notes only, no card number depends on them) |

## Rule checks
- Reading rule: sources.md lists commit texts, test pages, one wiki page and one web search only; no source file of a GPL /
  AGPL repo named anywhere; Stockfish and nnue-pytorch source not read. VIOLATIONS: none.
- Constants: K 2.25 and blend 0.6 are Forge's own trainer values (skill forge-nnue-data); T06C-03 ranges are own; no other
  engine's tuned value proposed as a Forge value. ok.
- Names: grep for vendor / model-company names and the residual trainer's forbidden process-name prefix over cards/T06C and notes/T06C: none.
- Duplicates: all 71 other cards listed; grep texel / HCE table / king danger / refit / re-tune hits only T06-05 (own E3
  refit, a different idea). T06-02 is a two-scalar HCE-vs-net re-weighting (card T06C-01 already separates it); T06-01
  material scale, T06-05 rule50 damp, E3 = post-processing. No HCE-table refit or king-danger unit fit among the 110 tried
  gates (packa, packb, E3 options checked by name). DUPLICATES: none.
- Caps: 3 cards (<= 4), 2 full + 1 one-liner, crew hours in all three, UNPROVEN on every Forge estimate, Status lines
  present, card_lint 0 findings / 0 PENDING at start of the pass (re-run at the end, see addendum).

## Counts
Numbers re-opened: 23 Elo figures from W/L/D (23 match), 7 licence rows (7 match), 12 lock / tool line references (12
match), 6 skill-sourced figures (5 traced, 1 untraced). Corrections: 2 (both in notes/T06C/TABLE.md). Unverifiable: 6
(row count ~305M, .hce regeneration hours, KB per row, S30 loss-vs-Elo remark, forge-o30-v2net skill text, plus the
sources-only items in the addendum). Violations: 0. Duplicates: 0.

## Addendum (end of pass)
- sources.md Ethereal b9b8463 "full NNUE 2021-05-29": CONFIRMED (gh api: 2021-05-29, title "Introduce NNUE Evaluation using a
  private NNUE Network and Implementation").
- sources.md Stockfish c25d4c4 "~+3.72 / ~+2.08": CONFIRMED (2022-04-12; STC W6490 L6234 D11212 -> +3.72 at <0,2.5>;
  LTC W13629 L13327 D23420 -> +2.08 at <0.5,3>).
- sources.md Clockwork datav3 / v5 / v4 series and "30 Ethereal tuning commits mined": UNVERIFIABLE in this pass (commit
  lists not re-mined within the 20 minutes; no card number depends on them).
- card_lint re-run at the end: see hand-back (cards unchanged by verify; only notes/T06C/TABLE.md and this file written).
- Nothing written outside cards/T06C/, notes/T06C/ and F:/odr/work/T06C-verify/. No card deleted, no Status line changed
  (no violation or duplicate found).
