# T06 - eval post-processing forms per engine (own words; no code, no tuned constants)

Legend: M = material on the board, NPM = non-pawn material, P = pawn count, c = halfmove (rule50) clock, v = static
eval (side to move), r = a search score, C = a complexity measure. Elo = the source's own number (W/L/D-based where
marked ~); fishtest TCs are not in the commit text (STC / LTC as named there). GPL / AGPL rows: commit titles, commit
messages, PR text and test logs only (never source). MIT rows: source read at the named commit, described in own words.

## Forge lock FD3A5190 (own source, read-only)
- HCE `scale_factor()` (src/eval.cpp:346-371): drawishness scale on the HCE endgame term only - strong side without
  pawns and at most a minor ahead, opposite-coloured bishops (with / without other pieces, by strong-side pawn count),
  few strong-side pawns; then the HCE tapers mg/eg by phase (eval.cpp:455-459).
- Residual net (src/search.cpp:616-620): final = clamp(HCE_runtime + network). The net output is not scaled by
  material, by the HCE scale factor, by the clock or by anything else. Both parts exist separately at that line.
- Draw score: exactly 0 at every draw return (search.cpp:692-700, 780, 893). rule50 drives only the draw at 100 and
  the TT-cutoff guard (search.hpp:75-85). Null moves advance the halfmove clock (board.cpp:823-835).
- No eval grain (CorrectionGrain 256 is the correction-history fixed point, search.hpp:258, search.cpp:644).

## Forge E3 candidate (own, e3_evalpost_al1; OFF-default options; gates UE3* + reruns)
Order: raw static eval (TT keeps raw) -> optimism -> material scale -> rule50 damp -> clamp -> correction history.
- EvalMatScale s (0..50 = 0..0.5): multiply by 1 + s(2M - M0)/M0, M = total MG material of both sides, M0 = start
  total. Centred at M0/2: factor 1 at half material, amplifies above, damps below. One sign only (s >= 0).
  Gates: s=12 +6.72 (3,000 games, LLR 1.95), rerun +3.47 +/- 4.64 (6,000 games, LLR 0.78), both caps.
- EvalOptimism K (0..150): o = K r/(|r| + 120) from the previous iteration's root score (depth >= 4, 0 for mates),
  +o for the root side, -o for the other, weighted by M/M0. Symmetric, no complexity term.
  Gates: K=40 +6.95 (3,000 games, LLR 2.08, cap); rerun H0 accepted -5.30 +/- 7.20 (2,360 games, LLR -2.99,
  uhoE3b_evaloptimism40_r6k_vs_AL1lp, finished 2026-11-04 ~22:53 PC clock).
- EvalRule50Damp D (0..60): v -= v D min(c,100)/10000, linear from clock 0. Gate D=30 +1.51 (3,000 games, LLR -0.53).
  R14 refit: held-out optimum ~81, past the option maximum.
- DrawJitter (0/1): draw score = (nodes & 2) - 1. Not gated.

## Stockfish (GPL-3.0, ideas only; commit titles / messages / PR text / fishtest logs of official-stockfish/Stockfish)
- Draw handling: 97d2cc9 (2018) draw score jitter by node parity, STC ~+0.71, LTC ~+0.58, VLTC ~+2.49; 770c8d9 more
  random draws ~+1.04 / ~+0.30 / VLTC ~+1.97; 70a38d7 removed the depth dependence (simplification).
- 50-move damping: 7b06475 (2019) clock shrinks the endgame scale factor, STC ~+4.15, LTC ~+2.94; 3af083a (2020)
  replaced by direct damping of the whole eval (also hits fortresses with heavy pieces, removes a sign oddity when
  mg and eg disagree), ~+2.03 / ~+2.54; later simplifications 180cab4, b8ccaf0; 7684b6e (2025) null moves no longer
  advance the clock, ~+0.98 then ~-0.11.
- Material scaling of the net output: 1dbd2a1 (2020) phase-dependent factor, high with pieces on, 1.0 in pawn
  endgames ("keep material when attacking"), ~+4.05 / ~+4.64; 5af09cf pawns added to the factor ~+3.71 / ~+1.96;
  ee53f8e (2023) separate pawn multipliers for eval and optimism ~+1.03 / ~+1.01, removed by 9739ed7 (non-regression);
  4d87627 same weights for eval and optimism; 7858f9d (Dec 2024) one pawn value for both nets - still present.
- Materialist / positional balance: a2f01c0 (2021) the net's two outputs re-weighted towards the positional part only
  when piece material is level, ~+3.38 / ~+2.65.
- Optimism: a5a89b2 (2021) adds a small root-side "optimism" to the eval BEFORE the material scaling, which moves
  the turning point between keeping material (ahead) and seeking exchanges (defending); displayed scores keep their
  meaning on average. STC finished yellow (LLR -2.94, ~+0.20, 165,048 games), LTC passed ~+1.36 - the gain showed
  only at the longer TC. The commit text also says the scaling factor then roughly halved from early middlegame to
  pure endgames;
  1066119 optimism grows with complexity C = |material - net eval|, ~+1.45 / ~+2.54; 22b7909 tune scale and optimism
  ~+3.21 / ~+1.77; 908811c (2023) asymmetric optimism ~+1.46 / ~+1.76, removed two weeks later by f9d8717
  "Symmetrize optimism" (non-regression); many simplifications 2023-2024 (4b085c4, 7e9b131, 54ad986, 365aa85,
  2f3e619) - the term itself survives.
- Complexity: 7f1333c blend net complexity with classical ~+2.36 / ~+2.69; d6b6360 formula tweak ~+1.47 / ~+1.63;
  4c4cb18 (2023) decay the eval a few per cent when C is large ("turbulent when defending, simpler when attacking")
  ~+0.85 / ~+1.30; 5ab3fe6, 86b5640, 45b2b06 (Feb 2025) simplify but keep the complexity adjustment.
- Eval grain: d212e66 (2024) round the eval to a grain plus a +-1 random component, ~+0.91 / ~+2.42.
- Out of T06 scope (search / speed uses, listed for completeness): complexity in search and TM (7678d63, 2b03723,
  08ac4e9, 442c40b), hybrid / lazy eval thresholds (3dca13a, 16b4578, cd0b8b4, 0470bce, b25d68f, 7831131),
  classical "dynamic complexity" HCE terms (6d0eabd, 1d3efff).

## Caissa (MIT, Witek902/Caissa @ 57cae7ef; src/backend/Evaluate.cpp Evaluate, Search.cpp AdjustEvalScore)
- Known-endgame evaluator overrides the net for small piece counts.
- Net output times a factor linear in a piece phase (minors, rooks, queens weighted; pawns left out): below 1 in bare
  endgames, above 1 in the opening.
- Post-net castling-rights bonus (the net input does not see castling rights).
- Soft saturation: evals beyond a threshold are compressed (slope well below 1) to stay under the known-win range.
- In search: correction history (pawn + two non-pawn tables) first, then a linear 50-move scale on the corrected eval
  (tunable divisor). No logged Elo for any of these in the commit log since 2022 (titles without test blocks).

## Patricia (MIT, Adam-Kulju/Patricia @ 67d83d70; engine/src/search.h eval / correct_eval)
- Style bonus: if the root side has sacrificed material along the current search path and much material is left, a
  root-side-signed bonus, larger when the eval is clearly winning and scaled by the sacrifice size (a style term).
- Material multiplier linear in total material, plus an extra root-relative cut when the root side is winning in low
  material or has no queen (do not trade down into an "easy" endgame; keep attacking).
- 50-move linear damping applied before the correction terms (pawn, non-pawn, continuation correction).
- Logged: PR 135 "a more balanced material scale impl" +12.43 +/- 5.01 (8+0.08, 5,704 games, LLR 2.95, [0,3]) vs
  its previous form; PR 153 "50mr scaling" +0.96 +/- 1.31 (8+0.08, 83,172 games, LLR 0.51, not passed, merged).

## Not read in this track (stopped by the two-sources-without-a-new-card rule; PENDING for a later pass)
Altair (MIT) source; GPL engines' commit logs (Berserk, Obsidian, Stormphrax, PlentyChess, Alexandria, Viridithas
(AGPL), Reckless (AGPL)) for their material-scaling / 50mr / optimism numbers.
