# T06D candidates: hand-crafted eval terms with logged Elo that the lock's HCE lacks

Every row: idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict.
Lock HCE layout read once (include/forge/eval_params.hpp:11-58, 639 mg/eg rows): psqt, mobility x4, bishop pair, rook
files / seventh, outposts, minor behind pawn, bishop pawns, queen development, tempo, pawn structure (isolated, doubled,
backward, connected, phalanx, double support), passers (rank, blocked, unstoppable path, safe push, king distances),
threats (minor, rook, king, pawn, pawn push, hanging, restricted), shelter / storm / open king file, KingDanger[100],
knight / rook pawn adjust, rook behind passers, space, long diagonal, WeakQueen, weak unopposed pawn, king-pawn distance;
fixed-rule scale_factor (src/eval.cpp:346-372); x-ray mobility (eval.cpp:124-130).

| # | idea | source + link | licence | logged numbers | Forge has it | verdict |
|---|---|---|---|---|---|---|
| 1 | king flank attacks + defences (attacked / double-attacked / defended squares in the king's flank and camp) | [Sirius #267](https://github.com/mcthouacbb/Sirius/pull/267), [Clockwork bedb1e8](https://github.com/official-clockwork/Clockwork/commit/bedb1e8b26), [Stockfish PR 722](https://github.com/official-stockfish/Stockfish/pull/722), [PR 2415](https://github.com/official-stockfish/Stockfish/pull/2415) | none / AGPL-3.0 / GPL-3.0, ideas only | Sirius STC +10.77 +- 4.83 (7,290 g, [0,3]); Clockwork STC +18.10 +- 6.18 (4,266 g) / LTC +17.48 +- 5.89 (3,918 g); Stockfish 722 STC +2.52 / LTC +5.99, 2415 STC +2.47 / LTC +2.93 (own calc from W/L/D) | no (`flank` 0 hits; king danger eval.cpp:230-252 counts zone attackers, weak zone squares, safe checks) | CARD T06D-01 (full) |
| 2 | endgame winnability / initiative (eg-only, sign-preserving clamp; pawns, wings, asymmetry, passers, outflanking, pure pawn ending, bias) | [Clockwork 92b9cb8](https://github.com/official-clockwork/Clockwork/commit/92b9cb844a), [ef52bf5](https://github.com/official-clockwork/Clockwork/commit/ef52bf5ce9), [4dd87cf](https://github.com/official-clockwork/Clockwork/commit/4dd87cf3d2), [Sirius #164](https://github.com/mcthouacbb/Sirius/pull/164), [#167](https://github.com/mcthouacbb/Sirius/pull/167), [#184](https://github.com/mcthouacbb/Sirius/pull/184) | AGPL-3.0 / none, ideas only | Clockwork base STC +2.95 +- 2.18 (33,896 g) / LTC +7.04 +- 3.62 (10,266 g); asymmetry +8.34 / +4.35; pure pawn ending +6.78 / +4.23; Sirius +4.07 (15,978 g, [0,5]), +4.57 (13,086 g); mg half ~0 (#184) | partly: fixed-rule scale_factor eval.cpp:346-372, not fitted, no wing / passer / outflanking input (`initiative\|complexity\|winnable` 0 hits) | CARD T06D-03 (full); not the T06-03 / T06B-01 complexity C = abs(residual) |
| 3 | pinned pieces (mobility on the pin line + per-type penalty) and discoverers in the eval | [Sirius #335](https://github.com/mcthouacbb/Sirius/pull/335), [#120](https://github.com/mcthouacbb/Sirius/pull/120) | none, PR text only | #335 STC +4.62 +- 2.88 (18,120 g, [0,3], tested with a known discoverer bug); #120 pins + x-rays in mobility +10.46 +- 6.06 (5,218 g, [0,5], 2024) | pin half no (pin logic only in board.cpp:55-61 / :982-988 for check detection); x-ray half yes (eval.cpp:124-130) | ONE-LINE T06D-02 (one engine, STC only, nps risk 0.5-1.5 %) |
| 4 | threats against the enemy queen on the next move (safe squares from which a knight / slider would attack the queen) | [Sirius #271](https://github.com/mcthouacbb/Sirius/pull/271) (credits Stockfish 6d8f583 / 1093047, Berserk PR 219) | none, PR text only | STC +3.08 +- 2.25 (32,238 g, [0,3], LLR 2.96), no LTC | no (`OnQueen\|queen_threat\|QueenThreat\|threat.*queen` 0 hits; WeakQueen eval.cpp:192 is the pin / discovery on the queen) | no card: 3-card cap; next candidate for a later round (Stockfish / Berserk numbers not read) |
| 5 | blocked pawn storm (storming pawn blocked by a pawn in front of it scored apart) | Sirius #185 (title only) | none | not read (source cap) | partly: StormDistance by rank distance only (eval.cpp:225, eval_params.hpp:47) | no card (number missing) |
| 6 | weak king ring squares | Sirius #216, simplified by #260 (titles) | none | not read | yes: weak zone squares in king danger (eval.cpp:236-238) | no card (Forge has it) |
| 7 | free passers (path not controlled by the enemy) | Sirius #141 (title) | none | not read | yes in a form: PassedUnstoppablePath, PassedSafePush (eval_params.hpp:35-36) | no card |
| 8 | exclude own king and blocked pawns from mobility | Sirius #233 (title) | none | not read | yes: mobility_area eval.cpp:437-438 | no card (Forge has it) |
| 9 | non-linear king safety + penalty for an attack without a queen | Sirius #258 (title) | none | not read | yes in fixed form: KingDanger[100] by units, no-queen halving eval.cpp:249 | evidence pointer for T06C-03 (number not read) |
| 10 | specialized endgame eval and scaling (KRvKN etc.) | Sirius #235, fix #351 (titles) | none | not read | partly: scale_factor rules only; specialized endgame functions not grepped | no card (number missing) |
| 11 | king proximity measured from the square in front of the passer; isolated pawns with threats not counted | Sirius #273, #199 (titles) | none | not read | Forge passer king distances eval_params.hpp:37-38 (measured square not checked) | no card (tweak level) |
| 12 | eval damping by the half-move clock | Clockwork fe1121c #352 (title listing); Sirius #345 reverted by #349 (titles) | AGPL-3.0 / none | Clockwork STC +3.03 +- 2.20 (32,028 g) / LTC +4.27 +- 2.68 (18,248 g); Sirius revert reason not read | E3 EvalRule50Damp (gated D=30 cap), packb FiftyDamp | evidence for T06-05 (plus a survivorship minus: Sirius reverted its own) |
| 13 | complexity-based soft time-management scaling | Clockwork 6007f70 #269 (title listing) | AGPL-3.0 | STC +4.92 +- 3.57 (11,292 g) / LTC +4.47 +- 3.28 (11,726 g) | not checked (time track) | pointer for the time-management track (T07), not an eval term |
| 14 | AVX-512 ray fill for pin detection | Clockwork ebc8c9f #348 (title listing) | AGPL-3.0 | +3.42 +- 3.16 (4+0.04s, 16,240 g) | n/a (speed of an existing pin path) | no card; shows Clockwork has a pin path, no pin-in-eval title found |

## Shared prerequisite (counted once, not per card)
All three cards fit their new rows with T06C-01's recipe (lock net frozen inside the sigmoid). If T06C-01's tooling
does not exist yet: tuner per-row net column + fixed K ~1.5 h and the FPOS -> trace + lock-net-cp row writer ~2 h
(T06C-01 Effort), i.e. ~3.5 crew h once. Each card keeps its rows in its own array, so T06C-01's 639-entry
`HceParamsFile` check is unchanged; if T06C-01 is adopted first, refit the new rows on top of its table.

## Why the residual net lowers each estimate (short)
The net is 768 one-hot piece squares -> 256 SCReLU -> 1, trained on this HCE's errors. Pair relations of piece squares
(material lead x pawn structure, king square x pawn squares) are learnable; relations that need empty squares between
pieces (slider attacks, pins) are not. Hence the order of discount: winnability (most overlap) > flank (partial: piece
attacks yes, slider attacks no) > pins (least, but search sees pins tactically). The frozen-net fit measures the rest.
