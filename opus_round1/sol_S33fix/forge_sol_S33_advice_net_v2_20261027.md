# ADVICE — net gate planning (v2, 2026-10-27: approx-model labels, QA S33-1)

v2 of Sol's `forge_sol_S33_advice_net_20261026.md`: same advice and numbers, now labelled; gate figures are quoted
only as fastchess printed them (RESULT.md); an exact-GSPRT cross-check of the same cells is added below.

Keep the current crew protocol until a separate vote changes it. A parent H1 is
followed by a fresh confirm at the parent's concurrency and a new seed/openings.
Neither a capped positive estimate nor the highest stopped Elo is a lock.

The pair shape is G119's measured profile (fastchess-printed G119: Elo 9.50 +/- 8.84, LLR 1.72, capped at 1500
games, conc 5), tilted to an assumed true +10 logistic Elo; hypotheses are nElo. These are not measured gains.

**approx model** — Sol's S33 planner (Gaussian online-LLR approximation, 20,000 modeled trials per cell; not
fastchess's exact GSPRT, not played games):

|Bounds/cap games|P(H1) approx model|P(cap) approx model|Mean games approx model|
|---|---:|---:|---:|
|[0,10]/1500|0.21235|0.78760|1434.38|
|[0,10]/2500|0.62280|0.37710|2005.53|
|[0,10]/3000|0.75895|0.24095|2158.27|
|[0,5]/4000|0.53325|0.46675|3552.69|

Cross-check, **approx model** pair profile (same G119 shape and tilt) with the **exact fastchess 1.8.2 GSPRT**
stopping rule (normalized pentanomial, constrained-MLE LLR; S44 implementation, 20,000 trials per cell, seeds
2026102733+i; `logs/approx_vs_exact_v2.json`):

|Bounds/cap games|P(H1) exact-LLR|P(cap) exact-LLR|Mean games exact-LLR|P(H1) exact minus approx|
|---|---:|---:|---:|---:|
|[0,10]/1500|0.20920|0.79075|1437.98|-0.0032|
|[0,10]/2500|0.61255|0.38745|2023.43|-0.0102|
|[0,10]/3000|0.75560|0.24435|2169.62|-0.0034|
|[0,5]/4000|0.52430|0.47570|3568.16|-0.0090|

The two models agree within about one percentage point on these cells (MC standard error ~0.3 points); the
Gaussian approximation is slightly optimistic for H1. The advice below holds under both.

If the crew wants more decisions for effects near this assumed size, preregister
a longer cap rather than extending a particular capped run after inspecting its
outcome. A narrower hypothesis gap does not automatically improve finite-cap
power: here [0,5]/4000 has less H1 probability than [0,10]/3000 (both models). Under the frozen
true+9.5 G119 validation case, cap is the most likely outcome: approx model P(cap)=0.8177, exact-LLR P(cap)=0.82865.

Use the complete table to choose a future design before play and examine all
three unpooled profile shapes. Training loss, epochs and one H1-stopped estimate
cannot determine the true effect. S48 shows substantial selection bias under a
true+10 model (S48 v2, exact model: an H1 stop sits about +8.6 to +9.3 above the assumed truth for the G104/G120
shapes). These conc5/profile assumptions cannot be transferred to conc7 or 8. Only original native
gate/confirm evidence decides.
