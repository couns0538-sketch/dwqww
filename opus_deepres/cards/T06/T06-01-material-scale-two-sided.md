# T06-01-material-scale-two-sided: two-sided material scaling with separate pawn and piece terms
Status: PARTIAL (every unfinished field says PENDING)

## Source
- Stockfish commit text + fishtest logs (no source): https://github.com/official-stockfish/Stockfish/commit/1dbd2a1ad5
  "Tweak nnue scaling to keep more material" (PR 3154); https://github.com/official-stockfish/Stockfish/commit/5af09cfda5
  "Include pawns in NNUE scaling" (PR 3164); https://github.com/official-stockfish/Stockfish/commit/ee53f8ed2f
  "Reintroduce nnue eval pawn count multipliers again" (PR 4681).
- Caissa (MIT) src/backend/Evaluate.cpp at 57cae7ef (Evaluate): piece-phase factor, pawns left out.
- Own: E3 fit C:/o13/p7/fit_e3.json, fit_e3.py grids (branch opus-r13-p7-e3fit, opus_r13/p7); gates UE3A, UE3A-R6K.

## Licence
Stockfish GPL-3.0 (Copying.txt at d212e663bb): ideas only - commit text and fishtest logs read, never source.
Caissa MIT at 57cae7ef: source may be read; only the shape is used here, no constants. Own E3 data: own.

## Mechanism
E3 multiplies the final eval by one factor that is linear in total material (pawns at their MG value), equal to 1 at
half the start material, with one slope s >= 0 (EvalMatScale 0..50). Two gaps:
1. Shape: Stockfish's history has two separately tested effects - a piece-material factor (larger with heavy pieces
   on, 1.0 in pawn endgames) that makes the side ahead avoid trading heavy pieces, and a separate pawn-count term
   (keep pawns when ahead, trade them when defending). Later the pawn weight became separate for the eval and for the
   optimism weighting - then removed again at no loss (9739ed7); what survives in 2025 is ONE material sum with its
   own pawn weight (7858f9d, 4d87627). Caissa uses a piece-only phase factor, pawns left out. E3 ties pawns to pieces
   through fixed MG values (pawn 82) and allows only one sign.
2. Fit: the E3 static fit reported "MatScale = 0", but its grid starts at 0 and the refine clamps at 0, and only the
   upper bound is flagged (fit_e3.py grids / refine clamp). So 0 is an unflagged lower-bound hit: a negative slope,
   a knee, or a pawn term of the other sign were never examined. And log-loss calibration is the wrong objective
   for the gain Stockfish describes (trade decisions in search), which is why the E3 fit said 0 while the gate of
   s = 12 measured +6.72 / +3.47.
Proposed form (own): factor = 1 + a (NPM - NPMref)/NPM0 + b (P - Pref)/16, NPM = non-pawn material of both sides,
P = pawn count, references at half the start values (E3's anchor, so search margins keep their meaning in the
middlegame); a and b signed, independent; applied at E3's MatScale step (raw -> optimism -> scale -> rule50 -> clamp
-> correction; the TT keeps the raw eval).

## Forge fit
Lock: no final-eval scaling - the residual is added unscaled (src/search.cpp:616-620); `scale_factor()`
(src/eval.cpp:346) scales only the HCE endgame term. E3 has the one-sided single-slope form. Change: two new signed
options inside E3's `e3_post_eval`, next to EvalMatScale (which stays).

## Expected gain
Stockfish (fishtest, TC not in the commit text; Elo from W/L/D): 1dbd2a1 STC +4.0 (14,744 games, {-0.25,1.25},
LLR 2.95), LTC +4.6 (8,912 games, {0.25,1.25}, LLR 2.95); 5af09cf STC +3.7 (15,072 games), LTC +2.0 (25,880 games);
ee53f8e STC +1.0 (173,632 games, <0,2>), LTC +1.0 (277,644 games, <0.5,2.5>), later simplified away (9739ed7). Forge's own one-sided line: UE3A
EvalMatScale=12 +6.72 (3,000 games, LLR 1.95, cap, no decision), UE3A-R6K +3.47 (6,000 games, LLR 0.78).
Forge estimate: 0 to +4 Elo over the EvalMatScale=12 line **UNPROVEN**.

## Effort
Crew: ~2 h code (two options + expose build) + ~2 h proofs. CPU: one 2-parameter SPSA (~3,000 STC pairs) plus two
SPRTs; hours = games / the crew's gate games-per-hour (PENDING the crew's rate). GPU: none.

## Test plan
Pre-gate: OFF bench / perft = the E3 OFF pins (= lock pins), ON bench differs, mateN d18 screen, WAC300 OFF/ON/OFF.
Offline (FIT_RECIPE step 2): per-material-bucket slope curve picks the signs of a and b before any game is spent.
Then SPSA (forge-o30-spsa) on (a, b), start (0, 0); gate the tuned pair: UHO SPRT [0,5] at STC vs the lock, then
LTC; a second STC SPRT vs the EvalMatScale=12 line measures the increment.

## OFF-by-default design
UCI `EvalMatScaleNpm` and `EvalMatScalePawn`, signed -50..50 (per cent of the factor), default 0. With both 0 the
branch is skipped and the factor is exactly 1, so search is node-identical to the lock (E3 OFF pins hold).
