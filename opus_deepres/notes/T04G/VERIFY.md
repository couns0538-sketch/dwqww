# T04G verify (adversarial pass, start 00:35 PC clock, stop by 00:55)

Scratch: F:/odr/work/T04G-verify/ (PR texts and patches via gh api, Elo recompute). Verdicts: CONFIRMED /
CORRECTED / UNVERIFIABLE / VIOLATION / DUPLICATE. Sources re-opened: the five PR texts (gh api pulls/N), the four
Altair PR patches (MIT, pulls/N/files), the Patricia PR 172 patch (MIT), the Altair HEAD windows from the worker's
saved raw file (F:/odr/work/T04G/altair/, b2447b825b), the lock source lines, notes/TRIED_GATES.md, FORGE_RESULTS.md,
the packc / packb / packa / E3 option lists, all 69 card files (ls cards/*/, pointer files included).

## Source numbers (check 1) - recomputed from W/L/D in the PR bodies
| card | claim | verdict | evidence |
|---|---|---|---|
| T04G-05 | Altair PR 182 +5.61 +- 3.85, 8+0.08, Threads=1, Hash 32 MB, [0,5] LLR 3.01, n=9,422, W 2,323 L 2,171 D 4,928, penta 73/1044/2330/1186/78, test 7457, merge cbb5e27ab2 2024-07-18 | CONFIRMED | PR body has exactly these; recompute: score 0.50807 -> +5.61; pentanomial 95 % error 3.85 (trinomial would be 4.85); merged_at 2024-07-18T14:09:56Z |
| T04G-01 | Altair PR 105 +4.07 +- 3.28, 8+0.08, Threads=1, Hash 32 MB, [0,5] LLR 2.95, n=22,696, W 6,120 L 5,854 D 10,722, test 2639, merge e42311036d 2023-07-17 | CONFIRMED | PR body; recompute +4.07, trinomial error 3.28 (no penta published); merged_at 2023-07-17 |
| T04G-02 | Altair PR 120 +3.63 +- 2.92, [0,5] LLR 2.97 (-2.25, 2.89), n=27,168, merge 99df021453 2023-09-21 (DESIGNS.md) | CONFIRMED | PR body W 6,934 L 6,650 D 13,584; recompute +3.63, error 2.92; bounds (-2.25, 2.89) as in DESIGNS.md |
| T04G-04 | Altair PR 89 +3.37 +- 2.66, [0,5] LLR 2.97, n=35,552 | CONFIRMED | PR body W 9,874 L 9,529 D 16,149; recompute +3.37, trinomial error 2.67 vs 2.66 claimed (rounding, penta not published) |
| T04G-04 | "PR 92 four days later raised both killer margins a lot" | CONFIRMED | PR 89 merged 2023-07-03, PR 92 merged 2023-07-07; PR 92 patch: first_killer_margin 12000 -> 30000, second 11000 -> 25000 (search.h tunable rows) |
| T04G-03 / TABLE row 3 | Patricia PR 172 LTC 60+0.6 +2.39 +- 1.78, n=35,124, [0,3] LLR 2.95, no STC | CONFIRMED | PR body W 5,360 L 5,118 D 24,646, penta 160/3460/10087/3688/167, Hash 128 MB; recompute +2.39, penta error 1.78; no STC block in the PR text |
| all | opening book | UNVERIFIABLE | no PR text names a book ("book not stated" in the cards is correct) |
| all | the chess.swehosting.se test pages | UNVERIFIABLE | numbers confirmed from the PR bodies only; the test pages were not fetched |
| T04G-01 | "Mid-2023 Altair (weaker, hand-crafted era)" | CONFIRMED | repo tree at e42311036d: evaluation.cpp + evaluation_constants.h, no nnue file |

## Mechanism vs patch (checks 1-2: MIT patches read; nothing copied here; no foreign constant proposed)
| card | claim | verdict | evidence |
|---|---|---|---|
| T04G-05 | the +1 depth applies when the alpha-raising score is at least the node's eval; HEAD :1103-1104; eval set :665-685; in check the test is false | CONFIRMED | PR 182 patch (+2/-1): the history depth becomes depth plus (alpha >= eval), in the alpha-raise (EXACT) block; HEAD raw :1103-1104 identical; HEAD eval block :665-685 = corrected static eval replaced by the TT value when the bound allows; Altair's eval starts at NO_EVALUATION = 500,000 (constants.h:27 at b2447b825b, raw :587) and is only set when not in check, so the test is false in check in Altair AND in the lock (ValueNone 32002 at include/forge/search.hpp:59, S:930-931) |
| T04G-05 | "in a singular search it is the plain static eval" | CORRECTED | S:932-933: eval = ss->static_eval = the corrected static eval (set at the first visit), without the TT adjustment; "plain" replaced in the card |
| T04G-05 | history_bonus = min(2048, 20 d^2 + 48 d - 32); x4 at d 1, +48 % at d 4, +24 % at d 8, nothing from d 10 | CONFIRMED | S:44-46 defaults 20 / 48 / 2048, S:153-155; recompute 36 -> 144 (x4.00), 480 -> 708 (+47.5 %), 1632 -> 2020 (+23.8 %), 2020 -> 2048 at d 9 (+1.4 %), capped from d 10 |
| T04G-05 | lock: quiets depth + (best_score > beta + 100) at S:1198, captures plain depth S:1200, PV best bonus / 4 S:1203-1205, eval S:929-943 | CONFIRMED | lines read; forge_has.sh 'best_score > beta \+ 100' -> S:1198 only |
| T04G-05 | T04 TABLE row "history depth bonus" judged HAS from the title | CONFIRMED | notes/T04/TABLE.md:33 says HAS `search.cpp:1198` for PR 182; the patch tests the eval, the lock tests beta + 100: a new angle, not a duplicate |
| T04G-05 | not in TRIED_GATES; no own prior code does it | CONFIRMED | tried_gates.py --grep 'Hist|Bonus|Killer|Null|Capt|Eval|ReSearch|Fifty|Malus': PawnHist, ContHist4Pct, ThreatHist, HistMalusPct, CheckOrderSee, CaptSeeDiv, EvalOnlyStore, E3 (EvalMatScale / Optimism / Rule50Damp), packb ReSearchAdjust / FiftyDamp, packa NonPawnCorr, packc AspFailHigh + EvalSwing; packc EvalSwing (src_packc src/search.cpp:980-987) is a continuation bonus from the parent / child static-eval swing, not a depth term on the cutoff update |
| T04G-05 | options HistEvalDepth 0-3, HistEvalDepthMargin -60..+60, own start 3 / 0 | CONFIRMED | Altair has no margin and no bits; nothing carried over |
| T04G-01 | null-search quiet cutoff fills slot 2 only when slot 1 is set; HEAD :584 flag, :1128-1136 update; call sites :733 / :743 / :931; killers cleared only in reset :56-66 called at :1490 | CONFIRMED | PR 105 patch (+6/-2) has exactly that rule; raw :584 null_search = !do_null && !root; :733 null child, :743 verification and :931 singular all pass false; :66 memset of killer_moves in Engine::reset, :1490 engine.reset() at search start |
| T04G-01 | lock: unconditional shift S:733-736; null child S:972-979 writes (ss+1)->killers; grandchildren cleared S:907; singular S:1095 and verification S:990 on the same ss; copy at S:335; detection via S:966 / excluded_move / S:989; counter needs a real previous move S:738 | CONFIRMED | all lines read as cited |
| T04G-01 | option KillerNullSlot2 bits 0-3, own start 1 | CONFIRMED | own design, no constant from Altair |
| T04G-02 | PR 120 = class-indexed capture history, class from SEE at scoring, class-local malus; HEAD search.h:96, move_ordering.cpp:87-100, search.cpp:388-404 | CONFIRMED | patch and saved HEAD windows match (capture_history[2][12][12][64]; malus only when the tried capture's class equals the best capture's) |
| T04G-02 | "the same PR also moved the class threshold (not isolated)" | CORRECTED | the patch has THREE changes: threshold -108 -> -85, the class split, and removal of the earlier history-decided SEE skip (SEE was skipped when the capture score was beyond +-3000, PR 95 form), so SEE became eager for every scored capture; added to the card |
| T04G-02 | "not CaptSeeDiv (TRIED, gates 22 / 47 / 48)" | CORRECTED | notes/TRIED_GATES.md and FORGE_RESULTS.md carry CaptSeeDiv only in gates 47 and 48; no row 22 exists in either; fixed in the card, TABLE.md row 22 and DIFF.md |
| T04G-02 | lock cites H:255, S:714-718, S:752-766, S:516, S:360, S:479; +12 KB per worker | CONFIRMED | lines read; 13 x 64 x 7 x int16 = 11,648 bytes |
| T04G-04 | PR 89 = killers also get the quiet + continuation history on top of their margin; kept at HEAD move_ordering.cpp:51-64 | CONFIRMED | PR 89 patch (evaluation.cpp +26/-28, the only file): the history terms moved out of the non-killer else branch; HEAD :51-64 adds history and continuation after the killer margins |
| T04G-04 | lock fixed stages Killer1 -> Killer2 -> CounterMove S:366-381 | CONFIRMED | forge_has.sh 'Killer1|Killer2|CounterMove:' -> S:366-381, S:434 |
| TABLE row 3 | Patricia 172 malus starts above the bonus and falls with the index to a floor well below | CONFIRMED | PR 172 patch (search.h +6/-4): malus = bonus x 15 / (10 + min(index, 30)): 1.5x at index 0, 1.0x at 5, 0.375x floor from 30; the 4-ply continuation gets half; TABLE's own form (125 % / -5 % / 40 %) is not Patricia's |

## Licence rows (check 3; tools/licence_at.py --row re-run 00:36-00:37)
| repo | sha | verdict |
|---|---|---|
| Alex2262/AltairChessEngine | b2447b825b (HEAD read), cbb5e27ab2 (PR 182), b68643baab (PR 95), e42311036d (PR 105) | CONFIRMED MIT, rows identical to notes/T04G/licences.md (e42311036d is a new row, below) |
| Adam-Kulju/Patricia | 67d83d7056 (HEAD read) | CONFIRMED MIT |
| merge commits of PR 89 (b38d5ea001), PR 120 (99df021453), Patricia PR 172 (67cdfcb55f) | see "late checks" below | rows run at the end of this pass |

## Forge-has-it greps (check 4) - re-run 00:36
'killers\[' -> S:733-735 (3 hits); 'best_score > beta \+ 100' -> S:1198 (1 hit); 'capture_history_' -> H:319, H:359,
S:516, S:714-717, S:757, S:764, S:1058 (10 hits); 'Killer1|Killer2|CounterMove:' -> S:366-381, S:434 (6 hits). All
as the cards say. CONFIRMED.

## Duplicates (check 5) - all 69 card files listed
- T04G-05 vs T04C-03 (merged pointer: eval-difference quiet history = packc EvalSwing), T04B-01 / T04B-02 (capture
  history in SEE pruning / pruning), T04F-02 (continuation keyed by capture), T04D-04 (root decay): different
  mechanisms. Not a duplicate. T04 TABLE row 33 covers the same PR with the wrong verdict (HAS); T04G-05 corrects it.
- T04G-01: no other killer card; no killer gate in TRIED_GATES. Not a duplicate.
- T04G-02 vs T04B-01 (Stormphrax: capture history in the SEE pruning margin), T04 A7 / TABLE row 22 (threshold shift),
  CaptSeeDiv (TRIED): those move the SEE threshold; T04G-02 splits the learned table. Not a duplicate.
- T04G-04: no other killer-order card. Not a duplicate.
- T04G-03: DUPLICATE of T04E-03 (also T04C-04, T04D-03 pointers): confirmed; the worker already merged it into
  TABLE.md row 3. Status line added to the pointer file (it stays a pointer, not a card).

## Rules (checks 2 and 6)
- Reading rule: both repos MIT at every commit read (LICENSE commits 7f28fb4127 / ffc0f5f6f5 predate every patch
  read); no GPL source opened; the saved Altair files under F:/odr/work/T04G/ are MIT. CONFIRMED.
- No foreign tuned constant proposed as a Forge value: option ranges and start values are the worker's own
  (KillerNullSlot2 1, CapHistSplit 2 with SEE >= 0, KillerHistOrder with -4000, HistEvalDepth 3 / margin 0). CONFIRMED.
- Names: grep for vendor / model-company names and the agent-config folder name over cards/T04G and notes/T04G: no hit.
- Cards: 4 real cards (2 full, 2 one-line) + 1 pointer file; crew hours in all 4; every Forge estimate UNPROVEN; no
  Forge Elo claim.
- card_lint: the 4 cards exit 0 with 0 findings; the folder glob exits 1 with 8 findings (9 before the DUPLICATE Status line was added), all on the
  T04G-03 pointer line (the T04C-03 / T04D-03 pointer files of other tracks lint the same way: job-wide convention, not a card).
- VIOLATION (track level, self-reported in the hand-back): notes/T04G/sources.md has 20 entries, 17 external
  (cap 15); the last three external entries (Altair commit miner, Patricia search.h windows, Altair legality grep)
  gave no card, so the "stop after 2 sources in a row with no new card" rule was also passed by one. The over-cap
  reads filled DIFF.md cells; no card rests on them, so no card Status line carries this mark.
- Round 2 caps: 2 engines deep-read (<= 3), 0 forum threads, 4 cards (<= 4, top 2 full). CONFIRMED.

## Not re-opened in the window (UNVERIFIABLE here)
TABLE.md rows 6-38 beyond the carded ones and the DIFF.md cells (Patricia movepick / search.h line cites) were not
re-read; only the lines named in the four cards and row 3 were checked.

## Late checks (00:45 PC clock)
- T04G-05 "the score that raised alpha": CONFIRMED - Altair HEAD raw :1095-1097 sets alpha = return_eval inside the
  "move has raised alpha" block, two lines above the depth test at :1103, so the test compares the raising score with eval.
- Card length: T04G-01 52 lines, T04G-05 56 lines (<= 60). CONFIRMED.
- Licence rows for the merge commits of PR 89 (b38d5ea001), PR 120 (99df021453) and Patricia PR 172 (67cdfcb55f):
  MIT (rows appended to notes/T04G/licences.md with e42311036d). CONFIRMED.
- Edits made by verify: T04G-02 (two corrections), T04G-05 (singular-search eval wording), T04G-03 (DUPLICATE Status
  line), TABLE.md row 22 and DIFF.md (gate 22 removed), licences.md (4 rows). No card deleted; nothing written outside
  cards/T04G/, notes/T04G/ and F:/odr/work/T04G-verify/.
