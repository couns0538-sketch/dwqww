# T06 - fit recipe for eval post-processing on licence-clean data (complements the E3 self-play fit)

Status: COMPLETE as a recipe; nothing here was run (research job). Every number below that is not a citation is an
own derivation, labelled as such. All fits are calibration only: they pick shapes, signs and start values; only
games (SPSA, then UHO SPRT [0,5] at STC, then LTC) decide strength.

## Datasets and licences
| set | what | licence | use |
|---|---|---|---|
| D1 | own gate PGNs, Forge vs Forge (F:\forge_push gate folders): R13 extraction al1gates.* (11,888 games, 495,015 positions, hashes in opus_r13/p7/logs/inputs.sha256) and the R14 re-extraction (13,795 games, 574,366 positions, logs/r14_extraction.sha256); plus the E3 gate PGNs uhoE3a/b/c (+ r6k reruns) | own data (crew games). Openings come from the gate book UHO_Lichess_4852_v1.epd - its provenance is the crew's / 30-Oct round's record, not re-checked here | main fit set, split by game |
| D2 | own self-play shards (selfplay_out / nnue_data, Forge at fixed nodes) | own data | second-domain check only (different TC and engine version); whether the files keep the halfmove clock and the result per position: PENDING (check with the forge-nnue-data skill) |
| D3 | own relabel set (R14-B relabel2, 20k-node labels) | own data | optional: deeper-search score as a low-noise target for the decay / grain checks |
| D4 | Lichess open game database | CC0 per database.lichess.org - NOT re-checked in this job (PENDING verification); human games | optional sign check of drawishness by material / clock only; never used to set engine values |
Not used: CCRL / TCEC / fishtest game files (no data licence checked), any engine-labelled set from a GPL tool run.

## What the E3 fit did and where it is blind (fit_e3.py, branch opus-r13-p7-e3fit)
1. Loss: soft-label cross-entropy of sigmoid(a v / 400) vs the side-to-move result, one global slope a, every 3rd ply
   from ply 16, not in check, 80/20 split by game, game bootstrap 2000. Good, keep it.
2. Lower bounds: every grid starts at 0, the refine clamps at 0, and only upper bounds are flagged. "MatScale = 0" is an
   unflagged lower-bound hit; s < 0, knees and a separate pawn weight were never tried.
3. One global slope plus a material factor are entangled: a slope that differs by material IS a material scaling,
   so the fit should look at per-bucket slopes first (step 2) instead of asking one factor shape to explain them.
4. Optimism input: the static eval stands in for the previous-iteration root score (weak evidence; CR noted that a
   planted s=20 refits as k=120 nearly as well). The gate PGNs carry the real score (step 5). The hand value K=40
   is now H0 on its rerun (2,360 games, -5.30 +/- 7.20, LLR -2.99), after +6.95 on the first 3,000 games.
5. The material column is the total of both sides only; per-side material, pawn counts and the HCE / residual split
   are missing (step 1).
6. Calibration is not strength: MatScale fit 0, yet the s=12 gates read +6.72 / +3.47 (caps). Stockfish's own text
   says the scale works through trade decisions in search (1dbd2a1, a5a89b2) - invisible to a static loss.

## Recipe
Step 1 - extraction (tool change only, the lock is untouched). Per sampled position write: game_id, ply, result
(side to move), clock, npm_w, npm_b, pawns_w, pawns_b, hce (side to move), residual (network part), the raw sum, and
r = the score the side to move printed for the move played FROM this position (fastchess comment "{+0.65/18 ...}",
pawns x 100; mate scores -> flag, excluded from optimism). raw_eval needs a variant that prints hce and residual
separately (both are separate at lock search.cpp:616-620).
Step 2 - per-bucket slope curve (picks the material shape for T06-01). Bucket by (NPM bucket x pawn bucket), e.g. 6 x
4; fit a slope a_b per bucket on training games with v untouched; the ratio a_b / a_all is the multiplicative factor
the data want in that bucket. A monotone ratio along NPM gives the sign of "a", along pawns the sign of "b"; a flat
ratio says calibration does not ask for scaling (then only SPSA can find a trade-decision gain). Game-bootstrap CIs.
Step 3 - two-sided refit. MatScale on [-50, 50] and the T06-01 form (a, b) on [-50, 50]^2; flag hits on BOTH bounds.
Step 4 - complexity curve (T06-03). Bucket by C = |residual|; a slope that falls as C grows means the eval is
over-confident in complex positions and supports the decay; the slope ratio gives the start value of Kd.
Step 5 - optimism with the real input. Refit K with r from step 1 (the root search's own final score, a close stand-in
for the previous iteration's score); report K alone and jointly with MatScale to measure the overlap CR found.
Optimism showed its Stockfish gain only at LTC (a5a89b2: STC failed yellow, LTC passed), so a refitted K is gated at
STC and, whatever the STC verdict short of H0, at LTC.
Step 6 - rule50 shape. D on [0, 100] (R14: optimum ~81) and a knee form D max(0, c - c0) with a c0 grid; same split.
Step 7 - grain from the slope (own derivation, T06-04). At p = 1/2, dp/dv = a / 1600 per eval unit, so a grain G moves
p by about G a / 1600. Pick three small win-probability steps and convert; e.g. with the OFF slope a = 1.85, G = 4, 8,
12 units are about 0.5, 0.9, 1.4 % steps. Sweep the three, gate the best.
Step 8 - joint fit, then games. Only after steps 2-7: one joint fit of the retained terms on training games with a
held-out check -> start values; then SPSA (forge-o30-spsa) from those values; then each new form alone UHO SPRT
[0,5] at STC vs the lock, then LTC. Never gate a bundle before its parts (R14 rule).
Step 9 - domain checks. Repeat steps 2 and 4 on D2 (and, optionally, D4 for the sign of the drawishness-by-clock
curve). A shape that flips between domains is not trusted.

## Run rules and cost
CR run rule: start at CPU <= 80 % and >= 8 GB free RAM, Idle / BelowNormal on the allowed CPUs, never on a running
gate's cores, outputs never overwritten (fit_e3.py already refuses). Cost (own estimate): tool changes ~3-4 crew
hours; each fit is seconds to minutes on ~0.5M rows; a 2,000-resample game bootstrap is tens of minutes on one CPU.
