# T06E-01-queen-threat-next-move: safe next-move threats on the enemy queen as new HCE rows
Status: COMPLETE

## Source
- Stockfish 6d8f583 "Knight threats on Queen" (2018-03-07) https://github.com/official-stockfish/Stockfish/commit/6d8f583af26daa1c158324d5c13cf01b17c746a5
- Stockfish 1093047 "Two steps slider threats on queen" (PR 1473) https://github.com/official-stockfish/Stockfish/commit/1093047e7d72ed0c82e143c2cc0af9ef7b0380ed
- Sirius PR 271 (credits both and Berserk PR 219) https://github.com/mcthouacbb/Sirius/pull/271 ; test links: notes/T06E/sources.md 1, 2, 7

## Licence
Stockfish GPL-3.0 at 6d8f583af2 and 1093047e7d, Sirius no licence at 64b845b139 (notes/T06E/licences.md): ideas only -
commit messages, PR text, test blocks; never source or diff. 6d8f583's message names a fixed value: not carried; every
new row starts at 0 and is fitted; all ranges below are own.

## Mechanism
Own form, only when the opponent has exactly one queen (square q). For side Us: N = knight-move squares around q that
an own knight attacks now; B = squares on q's diagonals (current occupancy) an own bishop attacks; R = the same on q's
ranks / files for own rooks. Each set is cut by a landing mask L; own variants for the holdout filter: (a) L = empty or
enemy-held and not strongly protected by the enemy (the :282 mask); (b) (a) and not attacked by the enemy at all unless
we attack it twice; (c) (a) plus squares held by an own non-pawn piece (two-step threat: that piece moves first, as both
messages say in prose); (d) each set counted once (min(count, 1)); (e) x-ray landings (Forge fit) kept. New rows (mg/eg,
compiled at 0): QueenThreatKnight (per N square), QueenThreatSlider (per B or R square). Fit = T06C-01 recipe: lock net
frozen as a per-row constant inside the sigmoid, K 2.25, b 0.6, own FPOS rows (013/014 held out); only the 4 new values
free, own fit box -10 .. +40 cp each (a value at the box edge = the form is wrong, drop it).

## Forge fit
Lacks it: `forge_has.sh 'OnQueen|queen_threat|QueenThreat|[Tt]hreat.*[Qq]ueen|[Qq]ueen.*[Tt]hreat'` = 0 hits.
evaluate_threats (src/eval.cpp:276-316, rows eval_params.hpp:39-45) scores current attacks only. WeakQueen (eval.cpp:
189-192) is the opposite relation (an enemy slider lined up on our own queen now), not a weaker form. Inputs exist:
strongly_protected (:282), per-type attacked_by (:135; the bishop / rook maps see through own queens / rooks, :124-130:
mask with direct attacks, or keep x-ray landings = variant (e)); new = one knight load + two slider lookups from q.

## Expected gain
Hand-crafted-eval engines (Stockfish 2018 classical; Sirius per notes/T04S/TABLE.md row 20, not re-verified). Stockfish
6d8f583 (own logistic calc from W/L/D): STC +2.91 +- 2.33 (35,129 g, [0,5] BayesElo era, LLR 2.96), LTC +2.30 +- 1.84
(42,442 g, LLR 2.96); 1093047 on top: STC +3.73 +- 2.87 (22,997 g, [0,4], LLR 2.95), LTC +5.42 +- 3.42 (11,926 g,
[0,4], LLR 2.95). Sirius 271: STC +3.08 +- 2.25 (8+0.08s, Threads=1, [0,3], LLR 2.96, 32,238 g), no LTC. Full card
although each STC is near 3: both Stockfish steps also passed LTC (one-liner rule = under 3 at STC with no LTC); still
the smallest source numbers of T06D / T06E. Why less here: the knight form is a pair relation of two piece squares
(learnable by the 768->256 SCReLU residual); the landing mask and the slider form need a third piece or empty squares
between (learnt poorly); the residual was trained on this HCE's errors; search sees a queen threat one ply later, so
the static term pays mainly at quiet leaves. Forge estimate: 0 to +2 Elo **UNPROVEN**.

## Effort
Crew ~5 h: sets + rows in evaluate and evaluate_traced ~1.5 h, option ~1 h, fit ~1 h, proofs ~1.5 h (T06C-01 tooling
if missing, once: notes/T06D/TABLE.md shared prerequisite). CPU: fit ~1-2 h at <= 3 threads Idle; STC SPRT at the
3,000-game cap ~6-7 h at 430-502 games/h, LTC ~3x per game. GPU none. Eval cost per node (the HCE runs at every static
eval): only with exactly one enemy queen; per side one table load, two magic lookups, three ANDs + popcounts; own
estimate 0.3-0.8 % nps, measured by nps ABBA ON vs OFF before the gate (a check, not a gate).

## Test plan
Unit test on the perft positions vs a slow reference (per landing square: play the own move, ask whether the piece then
attacks q). Fit, holdout filter (S31 scorer, lock net, holdout_013_014_s16, b 0.6; drop unless clearly below 0.014310;
rows near 0 = drop without a gate), OFF bench / perft = lock pins, ON bench differs, 2-minute smoke, nps ABBA. Crew
route: UHO, Threads=1, SPRT [0,5] nElo, alpha = beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision,
one extension if positive; STC, then LTC; alone, not stacked with T06C / T06D cards untested; non-zero rows -> T06C-02.

## OFF-by-default design
UCI check `HceQueenThreat`, default false. New rows in their own small array (not params::table): params::Count, the
639-row tuner layout and T06C-01's 639-entry `HceParamsFile` check stay; the traced path emits the extra coefficients
for the fit tool only. OFF skips the block, reads no new row -> node-identical (bench / perft pins).
