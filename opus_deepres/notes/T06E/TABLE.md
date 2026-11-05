# T06E: T06D's pending HCE leads (queen threats, blocked storm, non-linear king safety, king flank origin)

Every row: idea | source + link | licence | logged numbers (re-opened once) | Forge has it (file:line) | verdict.
Numbers: Stockfish W/L/D and Berserk W/L/D by own logistic calc with trinomial error, Sirius / Perseus pentanomial by
own calc (F:/odr/work/T06E/scripts/elo.py, penta.py); every printed Elo reproduces. Stockfish 2018 = classical
(hand-crafted) eval era; Sirius = HCE per notes/T04S/TABLE.md row 20 (not re-verified); Perseus = HCE at PR 100 by its README at 3c95481452
(sources.md line 8: hand-crafted evaluation features, no net).

| # | idea | source + link | licence | logged numbers | Forge has it | verdict |
|---|---|---|---|---|---|---|
| 1 | knight threat on the enemy queen next move (safe landing squares, incl. squares held by an own piece = two-step) | [Stockfish 6d8f583](https://github.com/official-stockfish/Stockfish/commit/6d8f583af26daa1c158324d5c13cf01b17c746a5) | GPL-3.0, commit message only | STC 7346/7052/20731 = +2.91 +- 2.33 (35,129 g, [0,5] BayesElo era, LLR 2.96); LTC 6695/6414/29333 = +2.30 +- 1.84 (42,442 g, LLR 2.96) | no: `forge_has.sh 'OnQueen\|queen_threat\|QueenThreat\|[Tt]hreat.*[Qq]ueen\|[Qq]ueen.*[Tt]hreat'` = 0 hits; threats eval.cpp:276-316 score current attacks only; WeakQueen eval.cpp:189-192 = slider x-ray on the queen now | CARD T06E-01 |
| 2 | slider threats on the queen next move, two-step from a square held by a harmless own attacker, only when the opponent has exactly one queen | [Stockfish 1093047](https://github.com/official-stockfish/Stockfish/commit/1093047e7d72ed0c82e143c2cc0af9ef7b0380ed) (PR 1473) | GPL-3.0, commit message only | STC 4817/4570/13610 = +3.73 +- 2.87 (22,997 g, [0,4], LLR 2.95); LTC 1891/1705/8330 = +5.42 +- 3.42 (11,926 g, [0,4], LLR 2.95) | no (same grep) | CARD T06E-01 |
| 3 | threats against the enemy queen (HCE engine, 2025) | [Sirius #271](https://github.com/mcthouacbb/Sirius/pull/271) | none, PR text only | STC +3.08 +- 2.25 (8+0.08s, [0,3], LLR 2.96, 32,238 g), no LTC, penta [417,3837,7364,4045,456] (re-fetched, reproduced) | no | CARD T06E-01 (third engine; re-fetched first-hand, notes/T06E/sources.md line 7) |
| 4 | "Queen Checks" (credited by Sirius #271 for queen threats) | [Berserk PR 219](https://github.com/jhonnold/berserk/pull/219) | GPL-3.0, PR text only | +14.45 +- 8.04 (8+0.08s, Threads=1, [-1,4], LLR 2.98, 3,608 g, W/L/D 983/833/1792), no LTC | cannot be mapped: the PR text has no description; if it means safe queen checks in king safety, the lock has them (eval.cpp:246-248 queen_checks) | no card; not used as T06E-01 evidence beyond "credited" |
| 5 | blocked pawn storm (storming pawn blocked by a pawn in front of it scored apart) | [Sirius #185](https://github.com/mcthouacbb/Sirius/pull/185) | none, PR text only | STC +3.88 +- 3.04 (8+0.08s, Threads=1, [0,5], LLR 2.95, 17,000 g, penta [169,2049,3926,2135,221]), no LTC | weaker form: StormDistance by rank distance only (loop eval.cpp:212-227, storm row :225, eval_params.hpp:47); `forge_has.sh '[Ss]torm'` = 4 hits, no blocked split | ONE-LINE T06E-02 (one engine, STC only) |
| 6 | non-linear king-safety adjustment + penalty for an attack without a queen | [Sirius #258](https://github.com/mcthouacbb/Sirius/pull/258) | none, PR text only | STC +7.89 +- 4.07 (8+0.08s, Threads=1, [0,3], LLR 2.95, 10,352 g, penta [147,1186,2302,1367,174]), no LTC | yes in a fixed form: KingDanger[100] table by units (eval_params.hpp:49, eval.cpp:252) is already a non-linear response; no-queen halving eval.cpp:249; the 10 unit weights are fixed ints (eval_params.hpp:71-84) | evidence for T06C-03 (second HCE engine with a non-linear king-safety gain; the lock's table form is closer to it than a linear sum, so less is left). Addition for T06C-03: the lock's no-queen halving (`units /= 2`, eval.cpp:249) and the attacker gate (two attackers unless a queen joins, :232-233) are hard-coded and not among T06C-03's 10 unit weights; add the divisor (own grid 1.5 .. 3) and the gate (1 vs 2 attackers) to its grid search |
| 7 | attack and defence status of flank squares in king safety (the origin Sirius #267 credits) | [Perseus PR 100](https://github.com/TheRealGioviok/Perseus-Engine/pull/100) | GPL-3.0 at 3c95481452, PR text only | STC +9.85 +- 4.62 (8+0.08s, Threads=1, [0,3], LLR 2.95, 8,182 g, penta [123,916,1801,1108,143]), no LTC | no (`flank` 0 hits, per T06D-01) | evidence for T06D-01 (a third engine with the same term and a similar STC gain: Sirius +10.77, Clockwork +18.10, Perseus +9.85) |

## Dead ends (one line each)
- Berserk PR 219 "Queen Checks": PR text = bench + test block, no description; the term cannot be named without source
  (GPL: not read). If it is safe queen checks in king safety, the lock has them (eval.cpp:246-248).
- Stockfish 1093047's follow-up ideas (threat by queen, queen overload, queen mobility retune): message text only, no
  test number - no card.
- Sirius #258: no new card - the lock already has a non-linear (table) king-danger response; folded into T06C-03 above.
- Perseus PR 100: same term as T06D-01 - evidence only.

## Pending
- None from T06D's list. Not re-fetched here: Clockwork / Stockfish flank numbers (T06D VERIFY reproduced them).
- Sirius as an HCE engine still rests on notes/T04S/TABLE.md row 20 (not re-verified by T06D or T06E).
