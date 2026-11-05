# T04G table - move ordering, history and picker candidates (Altair / Patricia vs the lock)

Lock = FD3A5190 source `src_al1s198_clean` (S = `src/search.cpp`, H = `include/forge/search.hpp`); "Forge has it"
cells are `tools/forge_has.sh` greps or reads of those files. Source numbers are the engines' own OpenBench blocks in
the PR text (Elo +- 95 % error, TC, games n, SPRT bounds; Threads=1; books not stated). Forge estimates **UNPROVEN**.
Both repos MIT at the commits read (notes/T04G/licences.md). Full mechanism comparison: notes/T04G/DIFF.md. Rows are
numbered once for the whole file; row N of section A is card T04G-0N.

## A. Gaps with a logged test (carded; row 3 merged)
| # | idea (card) | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
| 1 | null-search quiet cutoffs fill only killer slot 2 when slot 1 is set (T04G-01) | [Altair PR 105](https://github.com/Alex2262/AltairChessEngine/pull/105) | MIT | 8+0.08 +4.07 +- 3.28 n=22,696 [0,5] LLR 2.95; no LTC | LACKS: unconditional shift S:733-736; null child / singular / verification frames S:972-979, S:1095, S:990 | full card; 0 to +3 UNPROVEN; ~1.5 crew h |
| 2 | capture history split by SEE class, class-local malus (T04G-02) | [Altair PR 120](https://github.com/Alex2262/AltairChessEngine/pull/120) | MIT | 8+0.08 +3.63 +- 2.92 n=27,168 [0,5] LLR 2.97; no LTC; same PR moved the class threshold | LACKS: one table H:255, S:714-718; malus to all tried captures S:752-766 | one-line card since 00:29 (4-card rule, top 2 full); full design kept in notes/T04G/DESIGNS.md; 0 to +3 UNPROVEN; ~5 crew h (lazy design) |
| 3 | quiet malus shrinking with the move index (was card T04G-03; DUPLICATE of T04E-03 and T04C-04) | [Patricia PR 172](https://github.com/Adam-Kulju/Patricia/pull/172) | MIT | LTC 60+0.6 +2.39 +- 1.78 n=35,124 [0,3] LLR 2.95; no STC logged (weaker than T04E-03's STC +4.67 / LTC +5.18) | LACKS: uniform -bonus S:747-748; uniform scale HistMalusPct=125 TRIED (gate 67 -7.41, 1,500 g) | MERGED here at 00:29 (the card file now points to this row): evidence for T04E-03. Exact rule readable (MIT): the malus of each failed quiet starts ABOVE the bonus for the first tried quiets and falls with the index to a floor well below it. Own form for T04E-03's design: start 125 %, minus 5 % per index, floor 40 % (ranges start 100-150 %, slope 2-10 %, floor 25-75 %); 0 to +2 UNPROVEN for this exact form |
| 4 | killer 1 / killer 2 / counter tried in quiet-history order (T04G-04) | [Altair PR 89](https://github.com/Alex2262/AltairChessEngine/pull/89) | MIT | 8+0.08 +3.37 +- 2.66 n=35,552 [0,5] LLR 2.97; no LTC | LACKS: fixed stage order S:366-381 | one-line card; 0 to +2 UNPROVEN; ~2 crew h |
| 5 | history update one ply deeper when the score reached the node's eval (T04G-05) | [Altair PR 182](https://github.com/Alex2262/AltairChessEngine/pull/182) | MIT | 8+0.08 +5.61 +- 3.85 n=9,422 [0,5] LLR 3.01 (test 7457); no LTC; short stop, inflated | LACKS the eval test: only depth + (best_score > beta + 100) for quiets S:1198, captures at plain depth S:1200; `eval` = TT-adjusted corrected static eval S:929-943 | full card; 0 to +3 UNPROVEN; ~1.5 crew h. T04 TABLE row "history depth bonus" said HAS from the title only |

## B. Looked at, not carded
| # | idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
| 6 | quiet history split by from / to attacked (any enemy attacker) | [Altair PR 184](https://github.com/Alex2262/AltairChessEngine/pull/184) | MIT | 8+0.08 +5.87 +- 4.79 n=9,880 [0,4] | TRIED: ThreatHist any-attacker twin (gate 64 +4.63, 1,500 g, no decision); A1 lesser-attacker variant PREPARED | no card; evidence for the tried line (Altair's form replaces the main table, Forge's blended a twin) |
| 7 | 4th-ply continuation read in ordering | [Altair PR 129](https://github.com/Alex2262/AltairChessEngine/pull/129), [Patricia PR 143](https://github.com/Adam-Kulju/Patricia/pull/143) | MIT | +4.14 +- 3.35 n=20,288 [0,5]; +4.03 +- 2.59 n=21,570 [0,3] (8+0.08) | TRIED: ContHist4Pct gates 31-33 (45 %: +7.88, 1,500 g), part of bundle 68 (ported) | no card; evidence for ContHist4Pct |
| 8 | continuation history inside the pruning / LMR history score | [Altair PR 130](https://github.com/Alex2262/AltairChessEngine/pull/130) | MIT | +3.61 +- 2.92 n=27,136 [0,5] | HAS: quiet_history = main + cont1 + cont2, used at S:1058 / S:1070 / S:1146 | no card |
| 9 | larger bonus when the best score beat beta by a margin | [Patricia PR 145](https://github.com/Adam-Kulju/Patricia/pull/145) | MIT | +3.57 +- 2.44 n=24,360 [0,3] | HAS S:1198 (depth + 1 when best > beta + 100) | no card (the eval-based variant is row 5) |
| 10 | staged move generation | [Patricia PR 141](https://github.com/Adam-Kulju/Patricia/pull/141), [Altair PR 143](https://github.com/Alex2262/AltairChessEngine/pull/143) | MIT | +8.71 +- 4.14 n=8,498 [0,3]; cleanup +0.25 +- 2.87 (simplification) | HAS S:343-426 | no card |
| 11 | clear the next ply's killer before each move loop | [Patricia PR 65](https://github.com/Adam-Kulju/Patricia/pull/65) | MIT | +4.31 +- 2.81 n=20,872 [0,3] | lock clears grandchildren at entry S:907 | no card: the number measures "never cleared -> cleared per parent", the lock already clears; delta does not transfer |
| 12 | pv / improving / null-search terms in the history bonus | [Altair PR 50](https://github.com/Alex2262/AltairChessEngine/pull/50) | MIT | +1.64 +- 1.86 n=73,928 [0,5], LLR -1.61 (not passed) | LACKS (S:153-155) | dropped: under +3, did not pass |
| 13 | base margin for bad captures in a merged quiet + bad-capture list | [Altair PR 117](https://github.com/Alex2262/AltairChessEngine/pull/117) | MIT | +1.89 +- 1.29 n=138,192 [0,3] | LACKS: bad captures after all quiets S:394-399 | table only: under +3 STC, no LTC |
| 14 | ordering bundle: TT margin, MVV-LVA form (victim scale minus attacker), promotion scoring | [Altair PR 92](https://github.com/Alex2262/AltairChessEngine/pull/92) | MIT | +4.80 +- 3.83 n=17,792 [0,5] | lock: 10 x victim + capture history, no attacker term S:516 | no card: bundle of retuned margins, no isolated part |
| 15 | "aggressive bad capture" | [Altair PR 118](https://github.com/Alex2262/AltairChessEngine/pull/118) | MIT | +4.06 +- 3.26 n=21,568 [0,5] | patch = LMR for noisy moves, not ordering; capture LMR TRIED (STB1 / STB2) | other track, no card |
| 16 | separate gravity limit per table | [Altair PR 174](https://github.com/Alex2262/AltairChessEngine/pull/174) | MIT | none ("no effective change") | one HistoryMax S:107 | no number: no card |
| 17 | small fixed history bonus on alpha raise in qsearch | [Altair PR 4](https://github.com/Alex2262/AltairChessEngine/pull/4); HEAD sr:532-544 | MIT | none (bench line only) | none (stats only at S:1198-1200) | no number: no card |
| 18 | bonus / malus on every alpha raise (not only at the cutoff) | Altair HEAD sr:1095-1106 (introducing PR not found) | MIT | none found | cutoff-only + PV best bonus / 4 S:1196-1205 | no number: no card |
| 19 | piece-to main history instead of butterfly | Altair sh:95, Patricia ut:38 | MIT | none found | butterfly H:252 | no number: no card |
| 20 | legality split from make_move; faster is_legal | [Patricia PR 57](https://github.com/Adam-Kulju/Patricia/pull/57), [PR 83](https://github.com/Adam-Kulju/Patricia/pull/83) | MIT | bench lines only | HAS pseudo-legal + is_legal per move S:829, S:1051 | no number: no card |
| 21 | fused accumulator updates | [Patricia PR 47](https://github.com/Adam-Kulju/Patricia/pull/47) | MIT | 4+0.04 +7.44 +- 3.86 n=10,596 [0,3] | NNUE speed, not ordering (T05 territory) | other track, no card |
| 22 | capture-history-shifted SEE split, 2x immediate continuation, victim scale | [Patricia PR 209](https://github.com/Adam-Kulju/Patricia/pull/209) | MIT | +3.29 +- 2.38 n=31,038 [0,3] (bundle) | T04 A7; CaptSeeDiv relax-by-ordering-score TRIED (gates 47 / 48; verify: no gate 22 exists) | no card (T04 has it); form still at HEAD mp:12-17, 100-112, 158-162 |
| 23 | binary heap for long quiet lists | [Altair PR 196](https://github.com/Alex2262/AltairChessEngine/pull/196) | MIT | speed ~+1.7 % | T04 A10 | no card (T04 has it); still at HEAD mo.cpp:145-194, mo.inl:74-79 |
| 24 | check bonus in quiet ordering | neither engine has one | - | - | HAS +12000 S:532; CheckOrderSee TRIED (gate 65) | no card |
| 25 | counter move | neither engine has one | - | no removal test found | HAS S:334-340, S:376-381 | no card |
| 26 | pawn history | neither engine has one | - | - | TRIED PawnHist (gates 29 / 37 / 44) | no card |
| 27 | capture history decides the good / bad class at the extremes, SEE only in between ("Skip SEE") | [Altair PR 95](https://github.com/Alex2262/AltairChessEngine/pull/95) (patch read) | MIT | 8+0.08 +4.32 +- 3.46 n=20,672 [0,5] LLR 2.95 (test 2389); 2023 Altair; the same patch swapped a fixed SEE weight for a winning-capture margin parameter | LACKS: GoodCaptures runs see_ge >= 0 for every capture it picks, no history test S:360; threshold hook stub S:479 | no card: evidence for T04 A7 (history moves the class) with an isolated two-sided number; the "very good history skips SEE" side overlaps CaptSeeDiv (TRIED, relax only), the "very bad history goes straight to the bad list" side is the new angle; 4-card cap |
| 28 | remove the extra reduction in null-search subtrees | [Altair PR 191](https://github.com/Alex2262/AltairChessEngine/pull/191) | MIT | +2.98 +- 2.39 n=23,292 [0,5] | lock never had such a term (no null-search flag: forge_has.sh 'null_search' -> only null_move_allowed S:966, S:989) | does not transfer: no card |
| 29 | do not reset continuation history every move (bug fix) | [Altair PR 59](https://github.com/Alex2262/AltairChessEngine/pull/59) | MIT | +17.87 +- 9.00 n=3,056 [0,5] | lock never resets per move (cleared at ucinewgame only) | no card |
| 30 | continuation history (introduction) | [Altair PR 25](https://github.com/Alex2262/AltairChessEngine/pull/25) | MIT | +10.74 +- 6.80 n=5,824 [0,5] | HAS S:704-727 | no card |
| 31 | SEE in capture ordering | [Altair PR 34](https://github.com/Alex2262/AltairChessEngine/pull/34) | MIT | +4.25 +- 5.13 n=10,312, LLR 1.31 (not passed) | HAS (lazy SEE split S:360) | no card |
| 32 | recapture ordering bonus | [Altair PR 31](https://github.com/Alex2262/AltairChessEngine/pull/31) | MIT | +1.18 +- 2.14 n=58,184, LLR -2.98 (failed) | LACKS (forge_has.sh 'recapture': only SEE helpers in board.cpp) | dropped: failed |
| 33 | capture score fix | [Altair PR 125](https://github.com/Alex2262/AltairChessEngine/pull/125) | MIT | -1.97 +- 2.24 n=44,240 [-5,0] (merged as a code fix) | - | no card |
| 34 | history pruning | [Patricia PR 136](https://github.com/Adam-Kulju/Patricia/pull/136) | MIT | +2.12 +- 1.68 n=53,176 [0,3] | HAS S:1070 | no card |
| 35 | history in LMR | [Patricia PR 59](https://github.com/Adam-Kulju/Patricia/pull/59) | MIT | +6.75 +- 3.67 n=12,156 [0,3] | HAS S:1146 (quiets, clamp +-2) | no card |
| 36 | check masks in legal move generation | [Patricia PR 82](https://github.com/Adam-Kulju/Patricia/pull/82) (PR text only) | MIT | 4+0.04 +13.16 +- 5.38 n=6,260 [0,3] (test 8377) | lock: pseudo-legal lists + is_legal per move S:829, S:1051 | no card here: legality cost is T05C-01's field (evidence for its family; Elo, not nps; patch not read) |
| 37 | history heuristic (introduction) | [Patricia PR 4](https://github.com/Adam-Kulju/Patricia/pull/4) | MIT | +228 +- 65, 99 games | HAS | no card |
| 38 | "remove the deadweight bonus1" | [Patricia PR 53](https://github.com/Adam-Kulju/Patricia/pull/53) | MIT | "20-30 elo" in the text, no test block | patch not read, mechanism unknown | no number: no card |

## C. Evidence for existing cards and T04 rows
- T04-02 (LMR re-search deeper / shallower): [Altair PR 146](https://github.com/Alex2262/AltairChessEngine/pull/146)
  8+0.08 +8.62 +- 6.33 n=5,642 [0,5] LLR 2.89; [Patricia PR 146](https://github.com/Adam-Kulju/Patricia/pull/146)
  "do shallower" 8+0.08 +8.95 +- 4.22 n=8,194 [0,3] LLR 2.94 (test https://chess.swehosting.se/test/9914/); Altair
  still carries the deeper margin at HEAD (search_parameters.h:65).
- T04-04 (minor / major correction keys): Altair HEAD keeps all four correction tables (pawn, non-pawn, major, minor:
  search.h:98-101); no new number.
- T04 A7 (no card): Patricia HEAD movepick.h:12-17, 100-112, 158-162 still has the PR 209 form. New isolated number
  for the same family (row 27): [Altair PR 95](https://github.com/Alex2262/AltairChessEngine/pull/95) +4.32 +- 3.46
  n=20,672 [0,5], 8+0.08, two-sided (history far below zero = bad without SEE, far above = good without SEE).
- T04 A10 (no card): Altair HEAD still uses the heap (move_ordering.cpp:145-194; switched on in move_ordering.inl:74-79).
- T04 TABLE row "history depth bonus" (Altair PR 182, verdict HAS): the patch tests the score against the node's
  eval, not against beta + margin; the lock has only the beta form (S:1198) -> carded as T04G-05 (row 5).
- T04E-03 (decaying quiet malus): [Patricia PR 172](https://github.com/Adam-Kulju/Patricia/pull/172) LTC 60+0.6
  +2.39 +- 1.78 n=35,124 [0,3] LLR 2.95 (row 3; filed first as T04G-03, now merged).
- T05C-01 (check-info legality cache): [Patricia PR 82](https://github.com/Adam-Kulju/Patricia/pull/82) "check masks
  in movegen" 4+0.04 +13.16 +- 5.38 n=6,260 [0,3] (row 36): legality work moved into generation, measured in Elo at a
  very short TC; a different mechanism from T05C-01's per-node cache, so family evidence only.
