# T04F feature diff: Forge lock search vs Caissa (MIT)

Lock = FD3A5190 source `src_al1s198_clean`: `s` = `src/search.cpp` (1,531 lines), `h` = `include/forge/search.hpp`
(408 lines), `board.cpp` for repetition. Caissa = github.com/Witek902/Caissa @ 57cae7ef71 (MIT, read 2026-11-05 00:00):
`S` = `src/backend/Search.cpp` (2,385 lines), `MO` / `MOh` = `MoveOrderer.cpp` / `.hpp`, `MP` = `MovePicker.cpp`,
`TT` / `TTh` = `TranspositionTable.cpp` / `.hpp`, `SU` = `SearchUtils.cpp`. Read: those files only, in <= 300-line
windows. Mechanisms are described in own words; no Caissa constant is proposed as a Forge value.
Verdict: HAS (same idea), DIFFERS (both have it, other rule), LACKS (Forge has nothing like it), CAISSA-LACKS (Forge
has it, Caissa does not), DONE (already ported / tried / prepared by the crew: see WORKER_RULES, notes/T04/TABLE.md).
Section B gives the Caissa commit and its logged test for every LACKS / DIFFERS row that was looked up.

## A. Feature rows

### A1. Draws, repetition, mate distance
| # | technique | Caissa (file:line) | lock (file:line) | verdict |
|---|---|---|---|---|
| 1 | upcoming-repetition (game cycle) test: alpha raised to the draw score when one reversible move can repeat a position (cuckoo table), non-PV, alpha < 0, in search and qsearch | S:1229-1238, S:1540-1549, SU:68-113 | none (`forge_has.sh 'cuckoo|upcoming|game_cycle'` = 0 hits) | LACKS |
| 2 | in-tree repetition: twofold = draw only in non-PV nodes, PV needs threefold; no twofold on the root | S:1114-1158, S:1561 | twofold after the root = draw in every node type, `board.cpp:903-916`, used `s:700` | DIFFERS |
| 3 | stalemate detection at every node before TT / stand pat | none (only "no legal move" at the end, S:2276-2285) | `s:692-702` (`has_legal_move` in `is_draw`) | CAISSA-LACKS (speed cost on the lock side, kept for correctness) |
| 4 | insufficient material checked only after a capture | S:1241, S:1559 | every node, `s:700` | DIFFERS (speed only) |
| 5 | mate distance pruning | S:1563-1567 | `s:895-898` | HAS |

### A2. Transposition table
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 6 | cluster layout | 3 x 10-byte entries, 16-bit key, 32-byte cluster (TTh:56) | 4 x 16-byte entries, 32-bit key, 64-byte cluster (`h:67-93`) | DIFFERS (lock keeps more key bits) |
| 7 | replacement victim | lowest depth - age (TT:220-241) | lowest depth - 4 x age, chosen at probe (`s:272-280`) | HAS (weight differs, tunable-sized) |
| 8 | keep a deeper same-key entry unless exact or older generation; keep old move when the new one is none | TT:248-266 | `s:293-301` (same rule, margin 4) | HAS |
| 9 | TT cutoff depth rule | `tt depth >= depth + 1` only when the TT score is just above beta (within a margin), S:1599 | `tt_depth >= depth` for all bounds, `s:921` | DIFFERS (T04 table A4, Caissa d39fcfb; not re-carded) |
| 10 | TT cutoff off near rule 50 | halfmove < tunable limit, S:1600 (qsearch S:1267) | halfmove < 90 main `s:922`; qsearch uses `score_usable` only `s:790` | HAS (limit tunable-sized) |
| 11 | mate scores from TT made unproven near rule 50 | TT.cpp ScoreFromTT (lines 26-51) | rule50 stamp + `score_usable`, `h:83-86` | HAS (other mechanism) |
| 12 | static eval stored in TT at first evaluation (score none, depth 0) | S:1290, S:1686 | stored only with the node result `s:817`, `s:1214`; RFP / NMP / razor exits store nothing | DONE (EvalOnlyStore 49 near-miss port, WORKER_RULES) |
| 13 | TT score refines the static eval by bound | S:1700-1709, qsearch S:1305-1314 | `s:938-942`, qsearch `s:810-814` | HAS |
| 14 | no TT cutoff in PV nodes | S:1595 | `s:921` (`!pv_node`) | HAS |

### A3. Static eval, correction history
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 15 | correction keys | pawn, non-pawn white, non-pawn black, continuation (moves 1+2 plies and 1+4 plies back), S:1180-1191 | pawn + material, `s:638-645` | DIFFERS: non-pawn TRIED (packa, CorrHistPlus=4), continuation TRIED (CorrHistPlus bit 1, CorrHistV2), see T04 TABLE D |
| 16 | correction update rule | gravity: entry += bonus - entry x abs(bonus) / G, bonus = clamp(diff x depth / k), S:1168-1171, S:2368-2378 | additive step, diff x min(depth+1,16) / 256, hard clamp at the limit, `s:647-656` | DIFFERS (see B) |
| 17 | correction update conditions | not in check; best move none, quiet or SEE-losing capture; bound direction, S:2363-2366 | not in check, no capture best move, bound direction, `s:1218-1221` | DIFFERS: T04-05 (54aef4a) |
| 18 | correction tables shared between threads (per NUMA node) | S:192-197, S:284-290 | per worker, `h:322-323` | DIFFERS, SMP only (T04 TABLE D, 24fde49) |
| 19 | prefetch of the child's correction entries after make-move | S:2056-2066 | none | LACKS (speed only, see B) |
| 20 | eval scaled toward 0 with the halfmove clock | S:1196 | not in search (eval side) | DONE (EvalRule50Damp gated, WORKER_RULES) |
| 21 | improving: plies 2 / 4, false when unknown | S:1728-1734 | plies 2 / 4, true when unknown, `s:945-950` | DIFFERS (default only; tiny) |
| 22 | "opponent worsening" flag | S:1736-1739 | none | DONE (RfpOppWorse gate 62, T04 TABLE B) |

### A4. Node-level pruning (before the move loop)
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 23 | reverse futility: margin terms | linear (+quadratic) depth, improving only when the opponent cannot win material (threat test), opponent-worsening, extra discount when no TT entry; returns a blend toward beta, S:1747-1760 | linear depth - improving, returns eval, `s:960-963` | DIFFERS: threat-gated improving + no-TT discount LACKS (see B); blend TRIED (gate 86 H0) |
| 24 | razoring | depth <= tunable, against beta, not when beta is a big win, S:1762-1771 | depth <= 2, against alpha, `s:953-958` | HAS (win guard LACKS, tiny) |
| 25 | null move: node type | cut nodes only, S:1780 | any non-PV, `s:965` | DIFFERS (T04 TABLE B 47604ad, dropped < +1) |
| 26 | null move: eval margin | small extra margin at low depth, discount when the child ply had few cutoffs, S:1776-1782 | `static_eval >= beta - 24 x depth + 180`, `s:965` | DIFFERS: T04-03 (e53fe6e) |
| 27 | null move: reduction | base + depth / k + min(cap, (eval - beta) / k) + improving, S:1793-1795 | base + depth / 3 + min((eval - beta) / 200, 3), no improving term, `s:970-971` | DIFFERS (see B) |
| 28 | null move: high-depth fail high | node depth reduced by a fixed amount and the node searched on (falls to qsearch at depth <= 0), S:1811-1825 | separate verification search with null move off, depth >= 14, `s:984-997` | DIFFERS (see B) |
| 29 | null move after null | not if parent or grandparent was a null move, S:1786-1788 | not if the parent move was null, `s:966` | HAS (grandparent rule tiny) |
| 30 | ProbCut | qsearch then reduced search, SEE gate, TT depth gate, TT store depth - margin, S:1446-1508 | same structure, plus an improving term in the margin, `s:1000-1027` | HAS |
| 31 | in-check ProbCut from the TT (TT capture move with a lower bound well above beta returns at once) | S:1842-1851 | none (ProbCut only when not in check, `s:952`) | LACKS (see B) |
| 32 | IIR | cut / PV node, no TT move OR TT entry much shallower, S:1719-1723 | cut / PV node, no TT move, `s:1031` | DONE (R15 C4 IirShallowTt prepared) |
| 33 | eager accumulator update in check for PV / non-cut nodes | S:1676-1680, S:1688-1691 | lazy walk-back, `s:599-621` | DIFFERS (speed only) |

### A5. Move-loop pruning
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 34 | lmrDepth used by the pruning rules | S:1931-1936 | `s:1063` | HAS |
| 35 | late move pruning | threshold on the quiet count, depth + bonus in PV nodes, improving, S:1939-1948 | move count vs `LmpBase + d^2` (halved if not improving), `s:149-151`, `s:1062` | HAS (PV term tiny) |
| 36 | history pruning | quiet count > 1, depth < 9, threshold quadratic in lmrDepth, S:1950-1957 | `lmr_depth <= 3 && history < -k x depth`, `s:1070` | DIFFERS (form only; tunable-sized) |
| 37 | quiet futility | corrected eval + c x lmrDepth^2 + history / k < alpha, skip remaining quiets, first quiet kept, S:1958-1967 | `static_eval + base + mult x lmr_depth <= alpha`, no history term, `s:1065-1069` | DIFFERS (history term LACKS, see B) |
| 38 | quiet SEE pruning | threshold -c x lmrDepth - history / k, only if the target square is attacked, S:1972-1984 | `-24 x lmr_depth^2`, every quiet, `s:1071` | DIFFERS (history term: d19eff8 +1.04, below the bar) |
| 39 | capture SEE pruning | only bad-bucket captures, depth <= 5, S:1974-1979 | `-150 x depth`, all non-quiets, `s:1081-1083` | DIFFERS (tunable-sized) |
| 40 | capture futility | none | off by default (`CaptureFutilityBase = 0`), `s:1075-1080` | CAISSA-LACKS |

### A6. Extensions
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 41 | singular verification node type | non-cut, S:2016 | inherits `cut_node`, `s:1095` | DIFFERS: T04-01 (1b7a871) |
| 42 | singular margin by TT bound | tighter margin when the TT bound is exact, S:2000-2004 | `SingularMargin x depth` for every bound, `s:1091` | LACKS (see B) |
| 43 | singular depth | linear in depth with an offset, S:2005 | `(depth - 1) / 2`, `s:1092` | HAS (tunable-sized) |
| 44 | extension budget | ply < 2 x root depth for any positive extension, S:2028 | per-path double-extension counter <= 6, `s:1102`, `s:1116` | DIFFERS |
| 45 | double / triple extension | double and triple, PV nodes need a much larger gap, S:2031-2033 | double only, non-PV, `s:1102-1104` | DIFFERS: T04-06 (f2967c1) |
| 46 | multicut return value | blend of the singular score and beta weighted by the verification depth, S:2037-2038 | returns `singular_beta`, `s:1105-1106` | DONE (multicut blend queued crew line, T04 TABLE B) |
| 47 | negative extensions | TT score >= beta: -2 (PV) / -3 (non-PV); cut node: -2; TT score <= alpha: -1, S:2040-2045 | TT score >= beta: -2; cut node: -1, `s:1107-1111` | DIFFERS (deeper set; "deeper negative extensions" PREPARED in SingularV2, T04 TABLE B) |
| 48 | recapture extension (PV node, TT move recaptures on the previous to-square) | S:2047-2048 | none | LACKS (see B) |
| 49 | check extension | none | gives check, depth >= 2, SEE >= 0, `s:1112-1115` | CAISSA-LACKS |

### A7. Late move reductions
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 50 | table units | 1/1024 ply, separate quiet / capture tables, S:238-266 | whole plies, quiet / noisy tables, `s:125-147` | DIFFERS (T04 TABLE B: fractional LMR, small) |
| 51 | which moves | move index > 1; in PV nodes quiets only, S:2083-2085 | `depth >= 2`, move > 1 (+1 at root), `quiet || !tt_pv || move_count > 4`, `s:1137` | DIFFERS |
| 52 | quiet terms | non-PV +, TT move capture +, killer / counter (refutation) -, history (main + cont 1/2/4) -, cut node +, not improving +, gives check - | tt_pv -1, not improving +1, cut node +2, TT capture +1, gives check -1, in check -1, child cutoffs +1, history (main + cont 1/2) +-2, `s:1138-1146` | DIFFERS: refutation term LACKS (see B) |
| 53 | capture terms | winning-bucket capture -, bad-bucket capture +, cut node +, improving, gives check -, S:2107-2121 | table only + the shared terms, `s:1138-1146` | DIFFERS (capture LMR variants TRIED: LmrCapVictim, LmrTtCapAll) |
| 54 | PV low-ply term, deep TT entry term | S:2125-2130 | none | LACKS (T04 TABLE B 9a11bf6 / 2e6175e, under 3 Elo STC) |
| 55 | reduced depth floor | may reach 0 (qsearch), S:2136-2137 | at least 1, `s:1147` | DIFFERS |
| 56 | re-search deeper / shallower | S:2155-2163 | fixed `new_depth`, `s:1149-1153` | DIFFERS: T04-02 (434bbda) |
| 57 | post-LMR continuation bonus for a quiet that beat alpha | none | `s:1154-1157` | CAISSA-LACKS |
| 58 | PV re-search of the TT move never drops into qsearch late in the game | S:2189-2191 | none | LACKS (see B) |
| 59 | depth decrement after alpha is raised (remaining moves searched shallower) | S:2267-2268 | none | LACKS (see B) |

### A8. Scores returned
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 60 | main-search fail-high score blended toward beta by depth | S:2326-2328 | returns `best_score`, `s:1224` | LACKS (see B) |
| 61 | qsearch stand-pat / fail-high blend toward beta | S:1317-1318, S:1431-1432 | returns the raw score, `s:816-818` | DONE (T04 TABLE B ae2eb0c, dropped < +1) |
| 62 | RFP fail-firm blend | S:1759 | returns eval, `s:962` | DONE (gate 86 RfpReturnBlend H0) |

### A9. Quiescence search
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 63 | evasions in check | after the first evasion that raises the best score, stop (one evasion), S:1421 | all evasions, `s:828-864` | DIFFERS (see B) |
| 64 | move-count pruning | after a few moves when not losing, S:1353-1355 | none | DONE (R15 C2 QsMovePrune prepared) |
| 65 | underpromotions skipped | S:1362 | generated and searched (captures stage) `s:510-521`, pruned only by futility / SEE `s:831-839` | LACKS (see B) |
| 66 | futility | skip a capture when stand pat + margin <= alpha and SEE does not win material; not on the previous to-square, S:1365-1373 | stand pat + margin + victim value <= alpha, `s:834-837` | DIFFERS (see B) |
| 67 | SEE pruning | stop the loop at the first bad-bucket capture failing SEE >= 0, S:1376-1379 | skip SEE < -QsSeeMargin, `s:838` | DIFFERS (tunable-sized) |
| 68 | capture history updated on qsearch cutoffs | S:1411-1416 | none (no history update in `qsearch`, `s:771-870`) | LACKS (see B) |
| 69 | TT bound in qsearch | lower / upper only, S:1435-1436 | exact in PV qsearch nodes, `s:867` | DIFFERS (tiny) |

### A10. History and move ordering
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 70 | butterfly history | indexed by side, from-attacked, to-attacked, from, to (MOh:74, MO:221-230) | side, from, to (`h:252`) | DONE (ThreatHist gate 64 TRIED) |
| 71 | continuation history index | previous move: capture or not, both colours, piece, to (MOh:75, MO:158-176) | coloured piece + to of the previous move, no capture split (`h:253-254`, `s:842`, `s:1121`) | DIFFERS (see B) |
| 72 | continuation plies written | 1, 2, 3, 4, 6 with per-ply weights (MO:257-266) | 1, 2, 4 (ply 4 at half bonus), `s:720-727` | DIFFERS |
| 73 | continuation plies READ (ordering, pruning stat, LMR) | ordering 1, 2, 4, 6 (MO:433-437); move stat for pruning / LMR 1, 2, 4 (S:1908-1915) | 1 and 2 only, `s:704-712`; the ply-4 table is written (`s:721`) but never read | DIFFERS (see B: lock writes a table it never reads) |
| 74 | pawn-structure history | MOh:77, MO:300-303, MO:430-431 | none | DONE (PawnHist gates 29 / 37 / 44 TRIED) |
| 75 | capture history index | side, attacker, victim, to (MOh:76) | coloured attacker, to, victim (`h:255`) | HAS |
| 76 | killers | one per ply (MOh:80), cleared for the next ply at node entry (S:1571) | two per ply, grandchildren cleared (`s:907`, `s:733-736`) | DIFFERS (see B: 2b51bb9) |
| 77 | counter move | side, piece, to (MOh:78) | coloured piece, to (`h:256`, `s:737-740`) | HAS |
| 78 | history update formula | gravity /16384, separate bonus and malus curves, each with a score-gap term (best - beta, capped), MO:245-305 | gravity /16384, one bonus curve `min(max, a d^2 + b d - 32)`, depth + 1 when best > beta + 100, malus = -bonus, `s:153-160`, `s:1198` | DIFFERS (see B: 294f63e) |
| 79 | no history update when only one move was tried at low depth (quiets) / only one capture tried | MO:285-289, MO:326-330 | always updated, `s:729-766` | LACKS (see B) |
| 80 | history tables cleared to a positive value (not 0) | MO:205-218 | zero, `s:575-584` | LACKS (see B: fc8c746) |
| 81 | history kept between searches | scaled 7/8 at each new search (MO:183-195) | kept 100 % (cleared at ucinewgame) | DIFFERS (T04 TABLE B: no change) |
| 82 | prior counter-move bonus on fail low | S:2304-2309 | present, off (`FailLowContinuationBonus = 0`), `s:1205-1210` | HAS (retune only, T04 TABLE B) |
| 83 | PV-node non-cutoff best move bonus | none | main history + bonus / 4, `s:1201-1204` | CAISSA-LACKS |
| 84 | quiet ordering score | main + pawn hist + cont 1 + cont 2 + cont 4 + cont 6 (weights) + threat escape / enter bonuses + node-count bonus near the root, MO:422-464 | main + cont 1 + cont 2 + 12000 if a direct check, `s:523-536` | DIFFERS |
| 85 | threat escape / enter bonus (minor attacked by a pawn, rook by a minor, queen by a rook: moving away = bonus, moving onto = malus) | MO:439-454 | none | LACKS (see B) |
| 86 | node-count ordering near the root (ply < 3: share of nodes each move took earlier) | S:1859-1863, S:2202-2208, MO:458-464 | none | LACKS (see B) |
| 87 | capture ordering | bucket (attacker < victim / equal / SEE-good / bad) + MVV x k + capture history, MO:398-420 | 10 x victim value + capture history (+ queen promotion), SEE split in the picker, `s:510-521`, `s:356-365` | DIFFERS (T04 TABLE A7 Patricia 209 idea) |
| 88 | picker stages | TT, captures, killer, counter, quiets with the bad captures mixed in by score, MP:8-131 | TT, good captures, 2 killers, counter, quiets, bad captures last, `s:343-426` | DIFFERS (T04 TABLE B 67c0882: lock already defers bad captures) |
| 89 | direct-check bonus in quiet ordering | none | +12000, `s:532` | CAISSA-LACKS |

### A11. Root and iterative deepening
| # | technique | Caissa | lock | verdict |
|---|---|---|---|---|
| 90 | aspiration start window | base + abs(previous score) / k, S:1009 | fixed delta 18 (tunable), depth >= 4, `s:1381-1387` | DIFFERS (see B) |
| 91 | aspiration fail high | re-search at one ply less (bounded), S:1059-1065 | same depth, `s:1396-1397` | LACKS (see B) |
| 92 | aspiration widening | window += window / k, full window past a cap, S:1095-1097 | `delta += delta / 2 + 4`, `s:1401` | DIFFERS (tunable-sized) |
| 93 | no deeper re-search at the root | S:2159 | n/a (no deeper re-search) | n/a |
