# T06D-01-king-flank-attacks: king flank attacks and defences as new HCE rows
Status: COMPLETE

## Source
- Sirius PR 267 "Introduce king flank attacks and defenses eval in king safety" (merge 3a2c3d72d1, 2025-03):
  https://github.com/mcthouacbb/Sirius/pull/267 , test https://mcthouacbb.pythonanywhere.com/test/631/
- Clockwork #387 https://github.com/official-clockwork/Clockwork/commit/bedb1e8b26 , https://ob.cwchess.org/test/1323/ , /1324/
- Stockfish PR 722 "King tropism" https://github.com/official-stockfish/Stockfish/pull/722 and PR 2415 "Introduce king
  flank defenders" https://github.com/official-stockfish/Stockfish/pull/2415 (fishtest links in the PR texts).

## Licence
Sirius no licence at 3a2c3d72d1 (all rights reserved), Clockwork AGPL-3.0 at bedb1e8b26, Stockfish GPL-3.0 at
691a8ce271 (notes/T06D/licences.md): ideas only - PR text, commit messages, test blocks; never source. No mask or
constant is given (Stockfish 722 names only the double-attack rule); everything below is own design.

## Mechanism
Own form. Flank = a fixed set of files around the king, camp = the defender's own first five ranks; two own flank
variants go to the holdout filter: (a) king file +- 1, (b) the same widened by one file toward the centre for an
edge-file king. Inputs from attack maps the HCE already builds: A = flank-and-camp squares the enemy attacks, A2 =
those it attacks twice, D = those the defender attacks. New rows (mg/eg pairs, compiled at 0): KingFlankAttack[min(A,
15)] (count-indexed like the mobility tables, eval_params.hpp:13-16: the response can bend, the fit stays linear),
KingFlankDouble (per A2 square), KingFlankDefence (per D square). A as integer units inside the KingDanger index is
a later variant (T06C-03's non-linear grid fit), not this card. Fit = T06C-01 recipe: lock net frozen as a per-row
constant inside the sigmoid, K 2.25, b 0.6, own FPOS rows (013/014 held out); only the 18 new rows are free.

## Forge fit
Lacks it: `forge_has.sh 'flank'` = 0 hits. King danger src/eval.cpp:230-252: zone attacker units :145-148, weak zone
squares :236-238, safe checks :243-247, no-queen halving :249, shelter :250, KingDanger table :252. attacked_by /
attacked_twice exist (:45, :133-135), so A, A2, D are masked popcounts; new: a flank mask per king file + 2 camp masks.
Overlap: the zone units already count attackers / weak squares next to the king; the flank adds area and defence.

## Expected gain
HCE engines then: Clockwork, Stockfish 2016/19; Sirius per the brief / T04S row 20 (not re-verified). Sirius 267: STC +10.77 +- 4.83 (8+0.08s, Threads=1,
SPRT [0,3], LLR 2.95, 7,290 games), no LTC. Clockwork 387: STC +18.10 +- 6.18 (8+0.08s, [0,3], LLR 3.08, 4,266
games), LTC +17.48 +- 5.89 (40+0.4s, [0,3], LLR 3.01, 3,918 games). Stockfish 722 (own logistic Elo from W/L/D):
STC +2.52 +- 1.96 (48,373 games, old [0,5] BayesElo bounds, LLR 2.96), LTC +5.99 +- 3.96 (8,881 games, LLR 2.95);
Stockfish 2415 (defenders): STC +2.47 +- 2.77 (26,298 games), LTC +2.93 +- 2.21 (30,600 games, [0,3.5], LLR 2.96).
Why less here: the 768->256 SCReLU residual net reads piece squares, not attacks: knight, pawn and king attacks on
flank squares follow from piece squares (pair features one hidden layer can learn), slider attacks depend on the
squares between (many pieces at once) and are learnt poorly; the net was trained on this HCE's errors, so it already
corrects part of the king-attack error. The frozen-net fit measures the overlap: rows near 0 or no clear holdout
drop = drop without a gate. Forge estimate: 0 to +4 Elo **UNPROVEN**.

## Effort
Crew ~5 h: masks + term in evaluate and evaluate_traced ~1.5 h, rows + option ~1 h, fit ~1 h, proofs ~1.5 h (T06C-01
tooling, if missing, once: notes/T06D/TABLE.md). CPU: fit ~1-2 h at <= 3 threads Idle; STC SPRT at the 3,000-game
cap ~6-7 h at 430-502 games/h, LTC ~3x per game. GPU none. Eval cost per node (the HCE runs at every static eval,
search.cpp:620; the pawn cache does not cover attacks): per side 3 AND + popcount and one mask load, own estimate
under 0.5 % nps, measured by nps ABBA ON vs OFF before the gate (a check, not a gate).

## Test plan
Fit, holdout filter (S31 scorer, lock net, holdout_013_014_s16, b 0.6; drop unless clearly below 0.014310 - a filter,
not an Elo predictor, S30), OFF bench / perft = lock pins, ON bench differs, 2-minute smoke, nps ABBA. Crew route:
UHO, Threads=1, SPRT [0,5] nElo, alpha = beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision, one
extension if positive; STC, then LTC; alone, not stacked with T06C-01 / T06D-02 / T06D-03 before each has a result.

## OFF-by-default design
UCI spin `HceKingFlank` 0/1, default 0 (a spin as in the other cards) [last round, coordinator, unverified]. New rows in their own small array (not params::table): params::Count, the
639-row tuner layout and T06C-01's 639-entry `HceParamsFile` check stay as they are; the traced path emits the extra
coefficients for the fit tool only. OFF skips the block, reads no new row -> node-identical (bench / perft pins).
