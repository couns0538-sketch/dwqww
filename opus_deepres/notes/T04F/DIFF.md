# T04F feature diff: Forge lock search vs Caissa (MIT)

Lock = FD3A5190 source `src_al1s198_clean`: `s` = `src/search.cpp` (1,531 lines), `h` = `include/forge/search.hpp`
(408 lines), `board.cpp` for repetition. Caissa = github.com/Witek902/Caissa @ 57cae7ef71 (MIT, read 2026-11-05 00:00):
`S` = `src/backend/Search.cpp` (2,385 lines), `MO` / `MOh` = `MoveOrderer.cpp` / `.hpp`, `MP` = `MovePicker.cpp`,
`TT` / `TTh` = `TranspositionTable.cpp` / `.hpp`, `SU` = `SearchUtils.cpp`. Read: those files only, in <= 300-line
windows (plus, in sections C-D, Stockfish commit messages, Stormphrax PR text and fishtest run records, never their
source). Mechanisms are described in own words; no Caissa constant is proposed as a Forge value.
Verdict: HAS (same idea), DIFFERS (both have it, other rule), LACKS (Forge has nothing like it), CAISSA-LACKS (Forge
has it, Caissa does not), DONE (already ported / tried / prepared by the crew: see WORKER_RULES, notes/T04/TABLE.md).
Section B gives the Caissa commit and its logged test for every LACKS / DIFFERS row that was looked up.

## A. Feature rows

### A1. Draws, repetition, mate distance
| # | technique | Caissa (file:line) | lock (file:line) | verdict |
|---|---|---|---|---|
| 1 | upcoming-repetition (game cycle) test: alpha raised to the draw score when one reversible move can repeat a position (cuckoo table), non-PV, alpha < 0, in search and qsearch | S:1229-1238, S:1540-1549, SU:68-113 | none (forge_has.sh for cuckoo, upcoming or game_cycle: 0 hits) | LACKS |
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
| 51 | which moves | move index > 1; in PV nodes quiets only, S:2083-2085 | `depth >= 2`, move > 1 (+1 at root), `quiet` or `!tt_pv` or `move_count > 4`, `s:1137` | DIFFERS |
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
| 73 | continuation plies READ (ordering, pruning stat, LMR) | ordering 1, 2, 4, 6 (MO:433-437); move stat for pruning / LMR 1, 2, 4 (S:1908-1915) | 1 and 2 only, `s:704-712` (one shared table: the ply-4 write at `s:721` lands in sub-tables that other nodes read as their ply 1 / 2) | DIFFERS on the offsets read; the 4-ply term is the crew's ContHist4Pct (Pack E P15, gates 31-33): TRIED |
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

## B. Caissa commit and logged test per LACKS / DIFFERS row
Source of every number: the Caissa commit message (tools/mine_commits.py --since 2022-01-01, cached; --show), link
https://github.com/Witek902/Caissa/commit/SHA. OpenBench / furybench blocks give TC, Threads, Hash, SPRT bounds,
LLR, N; older (2022-2023) cutechess blocks give W-L-D, Elo +- error and LLR but often no TC and no Elo bounds
("TC n/s"). 1 thread unless noted. Books are never stated. "bundle" = several changes in one test.

| row | Caissa commit (date) | what it changed | logged result | verdict for Forge |
|---|---|---|---|---|
| 1 | 50b25dc (2022-07-07) "Upcoming repetition detection"; b58f4a8 (2022-07-05) early exit | cuckoo cycle test added | none logged (message is the title only) | LACKS; number missing; table only |
| 1 | 8e9ce37 (2024-02-23) | cycle test also in qsearch | +1.03 +- 1.33, 10+0.1, [0,2], LLR 2.05 (not passed), n=124,388 | below the bar |
| 2 | 47fc56a (2023-10-21) "Better repetition handling" | twofold only in non-PV; no twofold on the root; cycle test only in non-PV (bundle) | +6.4 +- 5.3, 8+0.08, cutechess H1 llr 2.95, n=7,704 | card T04F-03 (one-line; part of the bundle only) |
| 16 | gravity form at HEAD (commit not looked up) | corr update with gravity | - | TRIED on the lock side: CorrUpdateMode (S1 CorrGravity), gates 63 / 68 (T04 TABLE A9) |
| 19 | b02c47f (2026-05-24) "Speedup: Prefetch correction histories" | prefetch of the child's corr entries | +2.40 +- 1.60, 5+0.05, n=49,432 (speed change measured in games) | LACKS; speed-only (nps ABBA route); lock corr tables 2 x 128 KB, cont table 1.38 MB; table only (T05 domain) |
| 23 | b746e2b (2024-02-10) | improving discounted when the opponent threatens a capture (RFP) | +1.41 +- 1.44, 8+0.08, n=106,544 | below the bar |
| 23 | 324f1f9 (2026-10-20) | RFP margin smaller when no TT entry | +1.18 +- 1.16 | below the bar |
| 23 | c44b34f (2024-05-20) "Tweak RFP" | margin floor (never below a small constant) | 8+0.08 +3.08 +- 2.65 [0,2.5] n=31,518; 30+0.3 +3.52 +- 3.31 [0,3] LLR 2.65 n=19,148 | n/a: fixes a zero margin at depth 1 improving; the lock's margin there is 72 - 40 = 32 cp, never 0 |
| 27-28 | 336745a (2023-11-19), 7081a74 (2023-06-15) | NMP parameter tweaks; the improving term and the reduce-depth-on-fail-high form predate 2022 (not found by title) | +1.58 +- 1.64 10+0.1 n=79,944; +2.9 +- 2.4 n=36,831 TC n/s | number for the mechanism missing; table only |
| 31 | e137a02 (2024-02-05) "In-check probcut" | TT-based probcut when in check | +2.01 +- 2.00, 8+0.08, n=54,628 | below the bar (STC only, under 3) |
| 37 | b990faf (2023-03-10) | history term in the futility margin + skip quiets | "+4.5 Elo" free text, no TC / games | number unusable; same idea as Stormphrax PR 272 in T04B's notes |
| 37 | 8e30145 (2026-10-20) | futility depth limit removed | +2.69 +- 2.61 non-reg [-3,0] 10+0.1 n=17,572 | lock: FutilityDepth is a tunable (raise it in SPSA), no code |
| 38 | d19eff8 (2024-09-08) | history term in the quiet SEE threshold | +1.04 +- 1.10, 10+0.1, n=177,074 | below the bar |
| 42 | 90670d9 (2026-09-01) | tighter singular margin on an exact TT bound | +1.48 +- 1.13; second test +0.85 +- 1.47 | below the bar (T04 TABLE B retune row) |
| 44-47 | fd723a2 (2024-02-19) "Singular Extensions tweaks" | TT depth gate depth-2 -> depth-3; TT score >= beta: -2 PV / -3 non-PV; new -1 when TT score <= alpha (bundle) | +3.81 +- 3.05, 10+0.1, [0,2.5], n=23,502 | lock has depth-3; -3 non-PV is in SingularV2 (branch fable-fb2-j3 src/search.cpp:1227-1228, never gated); the "TT score <= alpha -> -1" part has no number of its own: evidence for SingularV2 / T04-06, no card |
| 44 | c6c7cbd (2023-11-18) "Tweak extensions" | singular / double-extension margins and cap values | +4.56 +- 3.67, 20+0.2, Hash 128 MB, [0,3], n=15,474 | parameter values only: SPSA, not code |
| 48 | d1a2867 (2025-11-17) "Recapture extension" | PV-node TT-move recapture +1 | +0.94 +- 0.75, 10+0.1, n=221,198 | below the bar |
| 49 | 607753e (2025-06-29) "Simplify extensions" | check extension, queen-promotion and 7th-rank pawn extensions removed | +1.98 +- 2.25 non-reg [-2.5,0.5] 10+0.1 n=24,776 | lock keeps a check extension (`s:1112-1115`): a simplification line with non-regression bounds if the crew wants one; table only |
| 51-53 | b5c60ac (2023-10-29) "Tweaking LMR" | bundle: LMR for PV quiets from move 2, cut-node +2 / +1, TT promotion counts as capture, recapture term removed | +2.93 +- 2.75, 8+0.08, [0,3], n=28,796 | lock already has the main terms; below the bar as a code change |
| 52 | refutation term at HEAD (commit not found by title) | killer / counter reduced less | - | number missing; table only |
| 58 | d9f2914 (2025-09-30) | PV TT move never dropped into qsearch | +1.08 +- 1.03, 40+0.4, n=107,784 | below the bar |
| 59 | AlphaImprovementMinDepth at HEAD (commit not found by title grep) | depth - 1 after alpha is raised | - | number missing here; Stormphrax PR 284 "reduce after alpha raised" is in T04B's list |
| 60 | a1aa5e5 (2025-12-28) "Fail high adjustments" | fail-high score blended toward beta | +1.84 +- 1.34, 10+0.1, n=71,362 | below the bar |
| 60 | cecdba1 (2026-01-02) | same blend in multicut | +2.02 +- 1.42 | DONE (multicut blend queued crew line) |
| 63 | c8a30a7 (2023-08-17) "QSearch tweaks" | stop at the first quiet evasion in check (bundle with a futility retune) | +5.9 +- 4.8, cutechess H1 llr 3.18 [-3.18,3.18], n=8,606, TC n/s | card T04F-01 |
| 63 | a677c89 (2023-08-23) "QSearch: Aggressive check evasion pruning" | stop after the first evasion | +3.3 +- 2.6, cutechess H1 llr 2.95, n=25,531, TC n/s | card T04F-01 |
| 65 | a677c89 / c8a30a7 keep "skip underpromotions" | - | - | TRIED: QsQueenPromoOnly gate 58 (+4.40, 1,500 games, no decision) |
| 68 | qsearch capture-history update (commit not looked up) | - | - | number missing; table only |
| 71 | 2fd8f56 (2023-10-12) "Improve continuation history" | key bit "previous move was a capture" + one table for all plies + pointers across null moves (bundle) | +6.5 +- 5.3, 6+0.06, cutechess H1 llr 2.95, n=7,745 | card T04F-02 (capture bit only transfers) |
| 72-73 | 80efe30 (2023-02-24) "Continuation history change" | plies 1/2/4/6 read and written | none logged | ply-4 weight TRIED (ContHist4Pct gates 31-33); 6-ply read: number missing |
| 72-73 | 40f313f (2023-12-28) | lower weight of the 4- and 6-ply reads | +1.30 +- 1.33, 10+0.1, n=122,284 | below the bar |
| 72 | ce8e364 (2025-02-10) | also update the 3-ply table | +0.72 +- 0.62, n=332,766 | below the bar |
| 76 | 2b51bb9 (2023-11-17) "Only one killer move" | 2 killers -> 1 | +1.78 +- 2.09, 8+0.08, [-0.5,2.5], n=49,522 | below the bar |
| 78 | 294f63e (2024-01-27) | history bonus grows with the score gap above beta | +1.01 +- 1.07, 10+0.1, n=188,774 | below the bar (lock has a one-step version, `s:1198`) |
| 78 | 1b9935c (2023-10-21) | SPSA of history bonus values | +4.5 +- 4.2, 8+0.08, n=12,012 | values only: SPSA |
| 79 | no-update-when-one-move rule (commit not looked up) | - | - | number missing; table only |
| 80 | fc8c746 (2025-03-29) "Clear history tables with non-zero value" | positive start values | +1.50 +- 1.16, 8+0.08, n=96,590 | below the bar |
| 81 | 74a0957 / 22c8670 (2026-07) | 50 % -> 75 % -> 87.5 % kept between searches | STC +4.34 / LTC +0.81; +1.15 | T04 TABLE B: lock keeps 100 %, no change |
| 85 | caa3a6b (2022-07-04) "Bonus for moving hanging pieces" | first escape bonus | none logged | - |
| 85 | bc921e8 (2023-01-17) | escape / enter bonus by attacker class (minor-pawn, rook-minor, queen-rook) | +3.0 +- 2.7, cutechess, n=32,463, TC n/s, no SPRT line | DONE/parked: crew P14 ThreatOrderPct (static threat order bonus) parked after a tactics loss and d22 +91 % nodes; A1 HistRework (threat-keyed learned history with "lesser attacker" classes) built, never gated; table only |
| 85 | 357a686 (2023-06-07) "Bonus for pawn push threats" | quiet pawn push that attacks a piece gets a bonus | +2.8 +- 2.3, cutechess H1, n=46,463, TC n/s | below the bar; same family as P14 |
| 86 | eb1dc04 (2023-02-04) "Introduce NodeCache" | node-count ordering at ply < 3 | none logged | number missing; table only |
| 90-92 | ebe60f8 (2022-08-25) | fail-high re-search depth - 1, fail-low beta = midpoint, window values by depth, and the abs(score) term changed from multiplicative to additive (the term itself is older; diff re-read 00:31) (bundle) | +9.0 +- 4.0, cutechess, n=16,179, TC n/s | fail-high reduce TRIED: AspFailHighReduce (packc gates 15 / 28, +5.91 / +9.27 capped; packc 28 near-miss port DONE); fail-low midpoint HAS (`s:1394`); score term: no own number (TABLE row 39) |
| 90-92 | 723807a (2024-09-12) | re-search may lose more depth on fail high | +1.15 +- 1.26, 10+0.1, n=134,784 | as above |
| 90 | f042a6f (2023-11-11), 0dbc287 (2023-06-05), cc7d02c (2023-09-19) | f042a6f: depth schedule removed + abs(score) divisor changed (bundle); 0dbc287: window values, widening 1/2 -> 1/3, fail-low depth reset, NO score term (diff re-read 00:30; the earlier "score scaling" label for 0dbc287 was wrong); cc7d02c: averaged base score | +2.22 +- 2.22 8+0.08 [0,3] n=43,946; +4.0 +- 3.1 n=24,755; +3.0 +- 2.3 n=40,006 (TC n/s) | window values: SPSA; score term: number missing (no isolated test found, TABLE row 39); score averaging: evidence for T04 TABLE C (836ffcf / ecbcc95, gain vanished at LTC) |
| 6 | d84b705 (2024-01-04) "Smaller TT entries" | 16 -> 10-byte entries, 3 per 32-byte cluster | 5+0.05 Threads=4 Hash 8 MB +4.30 +- 3.00 [0,2] n=23,832; 8+0.08 Hash 4 MB +2.79 +- 2.28 [0,2] n=41,766 | table only: both tests at 4-8 MB hash; the crew gate uses Hash=16 at 10+0.1, so the number does not transfer |
| 9 | 9d566cc (2026-09-24) "Tweak TT cutoff margin" | margin of the depth+1 rule | +1.35 +- 1.06 | evidence for T04 TABLE A4 (d39fcfb) |
| 8 | 08b6fa0 (2026-09-14) | overwrite entries from earlier searches regardless of depth | +1.69 +- 1.26 | lock already overwrites an older generation (`s:294`) |

## C. Rows added in the continuation pass (from 00:22; numbering continues section A)
Same sources and verdict words as above; the Caissa commit and its logged test are given inline (TC n/s = cutechess
block without TC, 1 thread). HEAD lines are from the 57cae7ef71 copy already read.

| # | technique | Caissa | lock | verdict | Caissa commit, logged test |
|---|---|---|---|---|---|
| 94 | move-loop pruning at the root and in check | in check yes; root no (`!isRootNode` guard, S:1929) | in check yes for LMP / history / SEE, futility not in check; root no (`s:1061-1083`) | HAS | 8bd0321 (2023-10-18) "Allow pruning in root node and when in check" +5.0 +- 4.6 n=9,299 H1 TC n/s; its root part is gone at HEAD |
| 95 | best move recorded only when the score beats alpha | since 411f352 (diff not read) | `s:1172-1173` | HAS | 411f352 (2023-06-15) +15.2 +- 7.3 n=3,747 H1 TC n/s |
| 96 | fail-soft TT cutoff (return the TT score) | S:1599-1609 | `s:925` | HAS | a728a15 (2023-06-07) +5.9 +- 4.1 n=13,963 H1 TC n/s |
| 97 | TT cutoff from a shallower entry when the TT score is far below alpha | gone at HEAD (one depth rule, S:1599) | one depth rule, `s:921` | n/a (source dropped it) | added 222642f (2023-07-27) +3.6 +- 3.5 n=17,336 H1 TC n/s; removed by d940dec (2025-06-30) "Simplify TT alpha cutoffs" 10+0.1 +2.05 +- 2.29 n=24,206 |
| 98 | more LMR when the TT move is a recapture | gone at HEAD | none | n/a (dropped by b5c60ac, row 51-53) | 1c17dae (2023-07-24) +4.1 +- 4.0 n=12,069 H1 TC n/s |
| 99 | less LMR in PV nodes | PV terms in the LMR block S:2083-2130 | tt_pv -1, `s:1138-1146` | HAS | 98688fc (2023-08-20) +2.3 +- 2.5 n=36,874 H1 TC n/s |
| 100 | less time when the opponent played the predicted move | time manager (not read; outside the search diff) | ponder move only printed, `uci.cpp:366-374` | LACKS (time management) | 188fec4 (2024-02-19) 10+0.1 +2.08 +- 2.09 n=49,714; 10+0.0 +2.94 +- 2.34 n=40,484 |
| 101 | no aspiration window when the previous score is a mate score | S:1012-1013 | window at any score from depth 4, `s:1384-1386` | LACKS (tiny) | not looked up |

## D. Result of the diff (continuation pass, written 00:36, updated 00:40, research stop 01:07)
- Cards (bar: +3 Elo at STC, or +2 at STC with an LTC result): T04F-01 qsearch one evasion in check (row 63; a677c89
  +3.3 +- 2.6, c8a30a7 +5.9 +- 4.8), T04F-02 continuation history capture bit (row 71; 2fd8f56 +6.5 +- 5.3 bundle),
  T04F-03 twofold only in non-PV nodes (row 2; 47fc56a +6.4 +- 5.3 bundle, one-line card). The Caissa numbers are
  2023 cutechess runs (TC partly not stated, no LTC, wide error bars). Second engine (GPL-3.0, commit messages and
  fishtest records only): T04F-02 = Stockfish 2e96c51 (10+0.1 ~+2.4 N=79,702; 60+0.6 ~+3.1 N=29,147) and 472de89
  (~+2.3 / ~+2.2), the same capture key; T04F-01 = Stockfish 392b529 (10+0.1 ~+2.6 N=22,632; 60+0.6 ~+1.0
  N=105,432), same family with another rule (normal qsearch pruning in check under the mate guard); its SEE form is
  the tried P27R QsEvasionSeeNonPv line, so the card adds no option for it. Every Forge estimate is UNPROVEN.
- No fourth card. Gaps checked against the bar and rejected: score-scaled aspiration start window (row 90: the term
  is older than every commit read, ebe60f8 only changed its form inside a +9.0 bundle whose fail-high part the crew
  already TRIED; no own number), depth - 1 after alpha is raised (row 59: no Caissa number; T04B SP 284 and T04E
  Viridithas #431 / Reckless #714 do not meet the STC bar), upcoming-repetition test (row 1: no Caissa number; T04E
  row Viridithas #465 LTC only), in-check ProbCut (row 31, +2.01 STC only), corr-entry prefetch (row 19, speed, +2.40
  STC), TT-recapture LMR and shallow below-alpha TT cutoff (rows 97-98: the source removed them again).
- Evidence for existing cards / rows (no new card): fd723a2 +3.81 +- 3.05 10+0.1 [0,2.5] n=23,502 (bundle) for T04-06 /
  SingularV2 (deeper negative extensions); cecdba1 +2.02 +- 1.42 for the queued multicut-blend line (T04 TABLE B);
  9d566cc +1.35 +- 1.06 for T04 TABLE A4 (d39fcfb); cc7d02c +3.0 +- 2.3 n=40,006 (averaged aspiration base) for T04
  TABLE C (the averaging gain vanished at LTC there); 222642f then d940dec as a caution for the TT-cutoff-direction
  family (T04D-02, SP 195): the source added a below-alpha cutoff rule and later removed it with a passing
  simplification. Stormphrax PR 203 (STC +3.91 / LTC +3.36) is the guard the lock already has (T04B TABLE row 50),
  kept as the safety rule in T04F-01.
- Corrections made in this pass: row 90 (0dbc287 has no score term; f042a6f only changed the divisor; ebe60f8 changed
  the form), TABLE row 16 / DIFF row 94 (Caissa HEAD does not prune at the root).
- PENDING (number missing; full-message greps of the cached 2022+ commit list found nothing, so these features likely
  predate 2022 and finding them needs file history, which the caps forbid): refutation
  term in LMR (row 52), depth - 1 after alpha raise (row 59), capture-history update in qsearch (row 68), no history
  update when only one move was tried (row 79), node-count ordering (row 86), NMP improving term and NMP fail-high
  depth cut (rows 27-28), origin of the abs(score) aspiration term (row 90).
