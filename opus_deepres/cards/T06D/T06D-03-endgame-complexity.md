# T06D-03-endgame-complexity: endgame winnability (initiative) term on the HCE eg score (not T06-03's C)
Status: COMPLETE

## Source
- Clockwork #364 "Introduce endgame complexity evaluation by pawn count and bias" https://github.com/official-clockwork/Clockwork/commit/92b9cb844a
  (https://ob.cwchess.org/test/1190/ , /1191/ , /1192/); #367 "Winnable: Bias towards asymmetric pawns positions"
  .../commit/ef52bf5ce9 (/1197/, /1198/); #368 "Winnable: bias towards pure pawn endings" .../commit/4dd87cf3d2 (/1212/, /1213/).
- Sirius PR 164 "Complexity eval" https://github.com/mcthouacbb/Sirius/pull/164 , PR 167 /pull/167 , PR 184 /pull/184 .

## Licence
Clockwork AGPL-3.0 at 92b9cb844a and bedb1e8b26, Sirius no licence at a84d90b121 (notes/T06D/licences.md): ideas
only - commit messages, PR text, test blocks; never source; no constant carried over (none is given).

## Mechanism
Own form, eg only (Sirius 184: the fitted middlegame half was ~0). Inputs, mostly pawn-only: P = all pawns, Wg = both
wings (files a-d, e-h) hold pawns, As = files with pawns of one colour only (#367: asymmetry), Pp = passed pawns,
Ko = king outflanking (own: king file distance plus a signed rank term), Pe = no non-pawn piece left (#368), bias.
c = sum of new rows x inputs; eg' = eg + sign(eg) max(c, -abs(eg)): grows eg in winnable structures, shrinks it toward
0 (never past it) in drawish ones; applied before scale_factor (eval.cpp:457-458), so the sign and the lock scale's
strong side stay. Fit = T06C-01 recipe (lock net frozen as a per-row constant inside the sigmoid, K 2.25, b 0.6, own
FPOS rows, 013/014 held out), only the new rows free. The clamp is the only non-linearity (own): per pass fix each
row's clamp state at the current rows (a clamped row's term is -eg, no gradient), fit the rest linearly as T06C-01,
recompute the states, repeat until the active set is stable.

## Forge fit
Weaker form exists: scale_factor src/eval.cpp:346-372, fixed integer rules (pawnless with at most a minor ahead ->
0 / 12; opposite bishops -> 32 + 4p / 48 + 2p; else min(64, 44 + 5p), p = stronger side's pawns), used at :457-458;
not fitted, no wing / asymmetry / passer / outflanking / pawn-endgame input. `forge_has.sh
'initiative|complexity|winnable'` = 0 hits. Not E3 EvalMatScale / T06-01 either: those scale the final HCE + net
sum; this moves the HCE eg before the net is added (the board rule on scaling the residual is not touched).

## Expected gain
HCE engines: Clockwork by design, Sirius per the brief / T04S row 20 (not re-verified). Clockwork 364: STC +2.95 +- 2.18 (8+0.08s, Threads=1, SPRT [0,3], LLR
2.96, 33,896 games), LTC +7.04 +- 3.62 (40+0.4s, [0,3], LLR 2.95, 10,266 games), Endgames.epd STC +14.99 +- 4.97
(3,826 games); 367: STC +8.34 +- 4.10 (9,082 games) / LTC +4.35 +- 2.73 (18,052 games); 368: STC +6.78 +- 3.67
(11,782 games) / LTC +4.23 +- 2.65 (17,996 games), all [0,3], LLR >= 2.94. Sirius 164: STC +4.07 +- 3.15 (8+0.08s,
[0,5], 15,978 games); 167: +4.57 +- 3.42 ([0,5], 13,086 games); 184 (mg half dropped): 0.92 +- 5.20 ([-5,0], 6,054
games, unfinished). Why less here: the inputs are near-linear in the 768 piece-square inputs, and "shrink a lead in a
drawish structure" is a pair relation (lead x structure) SCReLU units can partly learn; drawish endings are a
frequent HCE error the residual net was trained on, and scale_factor covers the common cases - the most net overlap
of T06D's three; the frozen-net fit measures what is left (rows near 0 = drop without a gate).
Forge estimate: 0 to +2 Elo **UNPROVEN**.

## Effort
Crew ~5 h: inputs + clamp in evaluate and evaluate_traced ~1.5 h, active-set loop in the fit tool ~1.5 h, rows +
option ~0.5 h, proofs ~1.5 h (T06C-01 tooling, if missing, once: notes/T06D/TABLE.md). CPU: fit ~1-2 h at <= 3
threads Idle; STC SPRT at the 3,000-game cap ~6-7 h at 430-502 games/h, LTC ~3x per game. GPU none. Eval cost per
node: pawn-only inputs can sit in the pawn cache entry (eval.hpp:52-65), the rest is a few popcounts and two king
squares; own estimate under 0.3 % nps, measured by nps ABBA ON vs OFF before the gate (a check, not a gate).

## Test plan
Fit, holdout filter (S31 scorer, lock net, holdout_013_014_s16, b 0.6; drop unless clearly below 0.014310; report the
low-phase rows alone too, where the term acts), OFF bench / perft = lock pins, ON bench differs, smoke, nps ABBA. Crew
route: UHO, Threads=1, SPRT [0,5] nElo, alpha = beta = 0.05, pentanomial, cap 3,000; capped = UNPROVEN / no decision,
one extension if positive; STC, then LTC (the base term gained more at LTC than at STC in Clockwork); gate alone.

## OFF-by-default design
UCI check `HceWinnability`, default false. New rows in their own small array (not params::table): params::Count, the
639-row tuner layout and T06C-01's 639-entry `HceParamsFile` check stay; the traced path emits the extra coefficients
and clamp state for the fit tool only. OFF skips the term -> eg unchanged, node-identical (bench / perft pins).
