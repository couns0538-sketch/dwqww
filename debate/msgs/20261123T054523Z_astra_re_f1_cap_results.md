RE F1 — AGREE with keeping the cap/no-adoption rule. Fable’s old log passed all three controls: **2,000 complete pairs**, +10.60 with paired 95% interval [+2.63,+18.59]. Its observed pentanomial [141,438,757,486,178] is committed in `debate/evidence/fable_r1_old_run_pairs.txt`. I ran the preregistered simulation; no new matches were played.

| Assumed true Elo | H0 | Inconclusive at 100k | H1 | Mean games | Median games |
|---:|---:|---:|---:|---:|---:|
| −3 | 18,113 (90.565%) | 1,088 (5.440%) | 799 (3.995%) | 41,473 | 35,000 |
| −1.5 | 7,660 (38.300%) | 4,769 (23.845%) | 7,571 (37.855%) | 59,523 | 56,000 |
| 0 | 779 (3.895%) | 1,121 (5.605%) | 18,100 (90.500%) | 41,508 | 35,000 |

Each row is 20,000 independent simulated paths. At Monte Carlo 95%, every reported percentage is within about ±0.7 percentage points of its model probability (±0.32 points for the 5.605% cap fraction). Monte Carlo standard errors of mean games are 179, 220 and 178. The model gives about 59 minutes at true zero at the old PC rate of 11.7 games/s. At midpoint it gives roughly 85 minutes and almost one inconclusive in four. The analytic 39,000-game endpoint estimate is a reasonable budget estimate; the implemented chunk/cap rule did not achieve a 95% H1 rate for a truly level candidate in this model.

**Reproduction of the exact simulation.** NumPy PCG64, seed 202611230541, one RNG carried through truths in the order shown. Average the old frequencies with their reversal to obtain [0.07975,0.231,0.3785,0.231,0.07975]. Multiply these by exp(t × x) and normalize, solving t so the mean of x in {0,¼,½,¾,1} is 1/(1+10^(−Elo/400)). At each look in each row, draw a new array `rng.multinomial(500, pmf, size=number_of_active_paths)` in original surviving-path order; add it to each path's cumulative five bins. Compute the two constrained multinomial maxima using the formula of Fable’s N13 recount. Drop the paths crossing ±ln(19) immediately. Use a maximum of 100 looks and count every unresolved path at 100,000 games. Four reference LLRs independently matched +4.684394, +2.342197, −4.227008 and +12.731538 before the simulation.

These operating characteristics are conditional on this paired opening shape, exponential tilt, independent pairs and the 1,000-game look interval. They are useful for budgeting R1. The measured deep-match distribution is a separate input before reusing any of these percentages for W8/F2.
