# T04G table - move ordering, history and picker candidates (Altair / Patricia vs the lock)

Lock = FD3A5190 source `src_al1s198_clean` (S = `src/search.cpp`, H = `include/forge/search.hpp`); "Forge has it"
cells are `tools/forge_has.sh` greps or reads of those files. Source numbers are the engines' own OpenBench blocks in
the PR text (Elo +- 95 % error, TC, games n, SPRT bounds; Threads=1; books not stated). Forge estimates **UNPROVEN**.
Both repos MIT at the commits read (notes/T04G/licences.md). Full mechanism comparison: notes/T04G/DIFF.md.

## A. Gaps with a logged test (carded)
| idea (card) | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|
| null-search quiet cutoffs fill only killer slot 2 when slot 1 is set (T04G-01) | [Altair PR 105](https://github.com/Alex2262/AltairChessEngine/pull/105) | MIT | 8+0.08 +4.07 +- 3.28 n=22,696 [0,5] LLR 2.95; no LTC | LACKS: unconditional shift S:733-736; null child / singular / verification frames S:972-979, S:1095, S:990 | full card; 0 to +3 UNPROVEN; ~1.5 crew h |
| capture history split by SEE class, class-local malus (T04G-02) | [Altair PR 120](https://github.com/Alex2262/AltairChessEngine/pull/120) | MIT | 8+0.08 +3.63 +- 2.92 n=27,168 [0,5] LLR 2.97; no LTC; same PR moved the class threshold | LACKS: one table H:255, S:714-718; malus to all tried captures S:752-766 | full card; 0 to +3 UNPROVEN; ~5 crew h (lazy design) |
| quiet malus shrinking with the move index (T04G-03 = DUPLICATE of T04E-03, evidence only) | [Patricia PR 172](https://github.com/Adam-Kulju/Patricia/pull/172) | MIT | LTC 60+0.6 +2.39 +- 1.78 n=35,124 [0,3] LLR 2.95; no STC logged | LACKS: uniform -bonus S:747-748; uniform scale HistMalusPct=125 TRIED (gate 67 -7.41, 1,500 g) | evidence for T04E-03 (found after writing; card file kept, no deletes) |
| killer 1 / killer 2 / counter tried in quiet-history order (T04G-04) | [Altair PR 89](https://github.com/Alex2262/AltairChessEngine/pull/89) | MIT | 8+0.08 +3.37 +- 2.66 n=35,552 [0,5] LLR 2.97; no LTC | LACKS: fixed stage order S:366-381 | one-line; 0 to +2 UNPROVEN |

## B. Looked at, not carded
| idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|
| quiet history split by from / to attacked (any enemy attacker) | [Altair PR 184](https://github.com/Alex2262/AltairChessEngine/pull/184) | MIT | 8+0.08 +5.87 +- 4.79 n=9,880 [0,4] | TRIED: ThreatHist any-attacker twin (gate 64 +4.63, 1,500 g, no decision); A1 lesser-attacker variant PREPARED | no card; evidence for the tried line (Altair's form replaces the main table, Forge's blended a twin) |
| 4th-ply continuation read in ordering | [Altair PR 129](https://github.com/Alex2262/AltairChessEngine/pull/129), [Patricia PR 143](https://github.com/Adam-Kulju/Patricia/pull/143) | MIT | +4.14 +- 3.35 n=20,288 [0,5]; +4.03 +- 2.59 n=21,570 [0,3] (8+0.08) | TRIED: ContHist4Pct gates 31-33 (45 %: +7.88, 1,500 g), part of bundle 68 (ported) | no card; evidence for ContHist4Pct |
| continuation history inside the pruning / LMR history score | [Altair PR 130](https://github.com/Alex2262/AltairChessEngine/pull/130) | MIT | +3.61 +- 2.92 n=27,136 [0,5] | HAS: quiet_history = main + cont1 + cont2, used at S:1058 / S:1070 / S:1146 | no card |
| larger bonus when the best score beat beta by a margin | [Patricia PR 145](https://github.com/Adam-Kulju/Patricia/pull/145) | MIT | +3.57 +- 2.44 n=24,360 [0,3] | HAS S:1198 (depth + 1 when best > beta + 100) | no card |
| staged move generation | [Patricia PR 141](https://github.com/Adam-Kulju/Patricia/pull/141), [Altair PR 143](https://github.com/Alex2262/AltairChessEngine/pull/143) | MIT | +8.71 +- 4.14 n=8,498 [0,3]; cleanup +0.25 +- 2.87 (simplification) | HAS S:343-426 | no card |
| clear the next ply's killer before each move loop | [Patricia PR 65](https://github.com/Adam-Kulju/Patricia/pull/65) | MIT | +4.31 +- 2.81 n=20,872 [0,3] | lock clears grandchildren at entry S:907 | no card: the number measures "never cleared -> cleared per parent", the lock already clears; delta does not transfer |
| pv / improving / null-search terms in the history bonus | [Altair PR 50](https://github.com/Alex2262/AltairChessEngine/pull/50) | MIT | +1.64 +- 1.86 n=73,928 [0,5], LLR -1.61 (not passed) | LACKS (S:153-155) | dropped: under +3, did not pass |
| base margin for bad captures in a merged quiet + bad-capture list | [Altair PR 117](https://github.com/Alex2262/AltairChessEngine/pull/117) | MIT | +1.89 +- 1.29 n=138,192 [0,3] | LACKS: bad captures after all quiets S:394-399 | table only: under +3 STC, no LTC |
| ordering bundle: TT margin, MVV-LVA form (victim scale minus attacker), promotion scoring | [Altair PR 92](https://github.com/Alex2262/AltairChessEngine/pull/92) | MIT | +4.80 +- 3.83 n=17,792 [0,5] | lock: 10 x victim + capture history, no attacker term S:516 | no card: bundle of retuned margins, no isolated part |
| "aggressive bad capture" | [Altair PR 118](https://github.com/Alex2262/AltairChessEngine/pull/118) | MIT | +4.06 +- 3.26 n=21,568 [0,5] | patch = LMR for noisy moves, not ordering; capture LMR TRIED (STB1 / STB2) | other track, no card |
| separate gravity limit per table | [Altair PR 174](https://github.com/Alex2262/AltairChessEngine/pull/174) | MIT | none ("no effective change") | one HistoryMax S:107 | no number: no card |
| small fixed history bonus on alpha raise in qsearch | [Altair PR 4](https://github.com/Alex2262/AltairChessEngine/pull/4); HEAD sr:532-544 | MIT | none (bench line only) | none (stats only at S:1198-1200) | no number: no card |
| bonus / malus on every alpha raise (not only at the cutoff) | Altair HEAD sr:1095-1106 (introducing PR not found) | MIT | none found | cutoff-only + PV best bonus / 4 S:1196-1204 | no number: no card |
| piece-to main history instead of butterfly | Altair sh:95, Patricia ut:38 | MIT | none found | butterfly H:252 | no number: no card |
| legality split from make_move; faster is_legal | [Patricia PR 57](https://github.com/Adam-Kulju/Patricia/pull/57), [PR 83](https://github.com/Adam-Kulju/Patricia/pull/83) | MIT | bench lines only | HAS pseudo-legal + is_legal per move S:829, S:1051 | no number: no card |
| fused accumulator updates | [Patricia PR 47](https://github.com/Adam-Kulju/Patricia/pull/47) | MIT | 4+0.04 +7.44 +- 3.86 n=10,596 [0,3] | NNUE speed, not ordering (T05 territory) | other track, no card |
| capture-history-shifted SEE split, 2x immediate continuation, victim scale | [Patricia PR 209](https://github.com/Adam-Kulju/Patricia/pull/209) | MIT | +3.29 +- 2.38 n=31,038 [0,3] (bundle) | T04 A7; CaptSeeDiv relax-by-ordering-score TRIED (gates 22 / 47 / 48) | no card (T04 has it); form still at HEAD mp:12-17, 100-112, 158-162 |
| binary heap for long quiet lists | [Altair PR 196](https://github.com/Alex2262/AltairChessEngine/pull/196) | MIT | speed ~+1.7 % | T04 A10 | no card (T04 has it); still at HEAD mo.cpp:145-194, mo.inl:74-79 |
| check bonus in quiet ordering | neither engine has one | - | - | HAS +12000 S:532; CheckOrderSee TRIED (gate 65) | no card |
| counter move | neither engine has one | - | no removal test found | HAS S:334-340, S:376-381 | no card |
| pawn history | neither engine has one | - | - | TRIED PawnHist (gates 29 / 37 / 44) | no card |

## C. Evidence for existing cards and T04 rows
- T04-02 (LMR re-search deeper / shallower): [Altair PR 146](https://github.com/Alex2262/AltairChessEngine/pull/146)
  8+0.08 +8.62 +- 6.33 n=5,642 [0,5] LLR 2.89; [Patricia PR 146](https://github.com/Adam-Kulju/Patricia/pull/146)
  "do shallower" 8+0.08 +8.95 +- 4.22 n=8,194 [0,3] LLR 2.94 (test https://chess.swehosting.se/test/9914/); Altair
  still carries the deeper margin at HEAD (search_parameters.h:65).
- T04-04 (minor / major correction keys): Altair HEAD keeps all four correction tables (pawn, non-pawn, major, minor:
  search.h:98-101); no new number.
- T04 A7 (no card): Patricia HEAD movepick.h:12-17, 100-112, 158-162 still has the PR 209 form.
- T04 A10 (no card): Altair HEAD still uses the heap (move_ordering.cpp:145-194; switched on in move_ordering.inl:74-79).
- T04E-03 (decaying quiet malus): [Patricia PR 172](https://github.com/Adam-Kulju/Patricia/pull/172) LTC 60+0.6
  +2.39 +- 1.78 n=35,124 [0,3] LLR 2.95 (MIT, exact rule readable: the malus starts ABOVE the bonus for the first
  tried quiets and falls hyperbolically with the index, floor well below the bonus); filed first as T04G-03, which is a
  duplicate of T04E-03 / T04C-04.
