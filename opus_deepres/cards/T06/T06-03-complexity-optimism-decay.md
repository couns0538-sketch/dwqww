# T06-03-complexity-optimism-decay: complexity decay of the eval (and complexity-weighted optimism), complexity = |residual|
Status: COMPLETE

## Source
Stockfish commit text + fishtest logs only (no source):
- https://github.com/official-stockfish/Stockfish/commit/4c4cb185aa "Play turbulent when defending, simpler when attacking"
- https://github.com/official-stockfish/Stockfish/commit/1066119083 "Tweak optimism with complexity" (PR 3875)
- survivorship: titles 7f1333c "Blend nnue complexity with classical", d6b6360 "Tweak the formula for NNUE complexity",
  5ab3fe6 "Simplify blending eval with nnue complexity" (non-regression), 45b2b06 (Feb 2025) "Use same term for small
  and large net for nnue complexity adjustment" (PR 5886 text).
- Own: E3 README_E3_CANDIDATE.md names "optimism weighted by NNUE-vs-material agreement" as an E3 follow-up; own gate
  F:/forge_push/uhoE3b_evaloptimism40_r6k_vs_AL1lp/RESULT.md (EvalOptimism=40 rerun H0).

## Licence
Stockfish GPL-3.0 (Copying.txt at d212e663bb): ideas only - commit text, PR text and fishtest logs, never source.

## Mechanism
Complexity = how far the sophisticated eval is from a plain material count. Two uses, each tested on its own:
(b) the eval itself is decayed by up to a few per cent when complexity is large, so a defender prefers chaotic lines
and an attacker prefers stable ones at the same nominal score; (a) the optimism bonus grows with complexity. Titles
show both still present, simplified, in 2025 (verify: UNVERIFIABLE for (a) - the 2025 texts read, 45b2b06 / PR
5886, name only the "nnue complexity adjustment", not optimism).
Forge form (own): complexity C = |residual net output| (the net's disagreement with the HCE, already a separate
number at search.cpp:616) - no extra eval. (b) v' = v - v min(C, Cmax)/Kd; (a) o' = o (1 + C/Ko). Start values from
the FIT_RECIPE C-bucket slope curve, not from Stockfish. Placed inside E3's `e3_post_eval` (raw -> optimism ->
scale -> rule50 -> clamp -> correction); the TT keeps the raw eval; mate / TB scores bypass, as in E3.

## Forge fit
Lock has neither (search.cpp:616-620). E3 has optimism weighted by material only and no decay. (b) stands alone.
(a) needs E3's EvalOptimism ON, and the EvalOptimism=40 rerun is H0 (2,360 games, -5.30 +/- 7.20, LLR -2.99) after
the first run's +6.95 (3,000 games, LLR 2.08): so (a) waits for an optimism refit with the real root score
(FIT_RECIPE step 5) and a positive re-gate. C needs the network value kept next to the raw eval (one int per ply).

## Expected gain
Stockfish (fishtest, Elo from W/L/D): (b) 4c4cb18 STC +0.85 (268,448 games, <0,2>, LLR 2.93), LTC +1.30 (141,060
games); (a) 1066119 STC +1.45 (88,392 games, <0,2.5>, LLR 2.94), LTC +2.54 (37,848 games, <0.5,3>, LLR 2.93);
complexity blends 7f1333c STC +2.36 (42,320), LTC +2.69 (34,600); d6b6360 STC +1.47 (93,288), LTC +1.63 (84,168).
Forge estimate: (b) 0 to +1.5 Elo; (a) 0 to +2 Elo only if a refitted optimism gates positive **UNPROVEN**.

## Effort
Crew: ~2 h code (C in the stack, two options, expose build) + ~2 h proofs. CPU: one STC SPRT per part (a capped
6,000-game gate took ~14 h at concurrency 4, uhoE3a r6k) plus LTC if positive. GPU: none.

## Test plan
Pre-gate: OFF bench / perft = lock pins; ON bench differs; mateN d18 screen; WAC300 OFF/ON/OFF. Offline: FIT_RECIPE
step 4 (calibration slope by C bucket) must show a falling slope before (b) is gated. Gates: (b) alone UHO SPRT
[0,5] at STC vs the lock, then LTC; (a) only after a positive refitted-optimism gate, as optimism + (a) vs optimism
alone, UHO SPRT [0,5] STC, then LTC.

## OFF-by-default design
UCI `EvalComplexityDecay` (Kd, 0..20000, 0 = OFF) and `EvalOptComplexity` (Ko, 0..2000, 0 = OFF). With both 0 the
code path is skipped, the eval is unchanged and search is node-identical to the lock (bench pins).
