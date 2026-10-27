# ADVICE — search gate planning (v2, 2026-10-27: approx-model labels, QA S33-1)

v2 of Sol's `forge_sol_S33_advice_search_20261026.md` (unchanged wording except labels and the gate-figure line).
Every probability below is an **approx model** forecast: Sol's S33 planner, Gaussian online-LLR approximation of
the SPRT, modeled trials, not fastchess's exact GSPRT and not played games. Gate figures are quoted only as
fastchess printed them (RESULT.md).

Finish correctness, legal-move/state/TT tests and frozen input/build checks before
any strength gate. Compare one isolated change against its exact accepted parent.
The planner changes no engine option, tuning value or live gate.

The pair shape used is G119's (fastchess-printed: Elo 9.50 +/- 8.84, LLR 1.72, capped at 1500 games, conc 5).
At the assumed true+20 logistic Elo, [0,10]/1500 produces approx-model P(H1)=0.91375 and P(cap)=0.08625. At true+10
the same design produces approx-model P(H1)=0.21235 and P(cap)=0.78760. Thus 1500 games often fail
to resolve a useful smaller effect. A cap is inconclusive, not a regression or
positive acceptance. Select bounds, cap, openings and stopping rule beforehand;
never pool capped attempts, reseeds or different concurrency.

For a future adequately resourced trial near the smaller modeled effect,
[0,10]/3000 is one design worth voting on: its G119-shape true+10 approx-model H1 forecast is
0.75895. This is advice about operating characteristics, not permission to alter
the current crew rule. Search changes may have a different pair profile; repeat
planning with their actual profile when available. Synthetic draw-ratio profiles
are sensitivity checks, not substitutes for missing real data.

Keep source correctness, speed and equal-clock Elo separate. A node reduction or
tactical screen cannot establish a gain. The analytic calculation is a Gaussian/
Brownian approximation; agreement with modeled trials does not establish native
Fastchess error rates. The exact-GSPRT cross-check of these cells is in
`forge_sol_S33_advice_net_v2_20261027.md`. A clean independent confirm remains necessary. Native PC,
actual search candidate outcomes and Stockfish superiority are UNVERIFIED here.
