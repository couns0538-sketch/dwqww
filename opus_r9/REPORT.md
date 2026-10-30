# R9 SPSA search-parameter tuning for Forge — IN PROGRESS (steps 1-2 done; 3-5 wait for CPU under the 70% cap)

Branch `opus-r9-spsa` = AL1 lock `d4f4312` + CI baseline `0d99f02` + R9 commits. PC clock times (2026-10-29).
Machine exclusive: no (gate conc 4 x Threads 2, live self-play, NNUE trainer). No Elo claims: only QA's gate decides.

## Acceptance
| step | result | evidence |
|---|---|---|
| 1 expose the parameters behind one `R9Tune` switch, default off | 74 tunables (the lock's 51 `forge::tune` constants + 23 former literals) as advertised spin options, lock values as defaults; `R9Tune` off: **bench 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690 = ALL OK**; `R9Tune` on at the defaults: **ALL OK** too (the new parameters reproduce the literals exactly); with R9Tune off a changed tunable leaves bench unchanged, with it on 58 of 74 move bench 11 by themselves (the 11 time-manager parameters cannot move a fixed-depth bench; the other 5 move it with larger values or are off in the lock: `CaptureFutility*` while its base is 0) | `opus_r9/logs/identity_off_c.log`, `identity_on_defaults_c.log`, `option_check_c.log/.json`, `option_check_b_probes.log` |
| 1 tests | box build 0 warnings, FMA 0; CMake all 30 targets + CTest 14 tests: only the 4 known `forge_tests` lines (KNOWN-FAILURE CHECK: PASS, also `uci_regression` with the new options); opus-ci green on `8856be4a` and `22b1f2ba` (release ALL OK, ASan / TSan KNOWN-FAILURE CHECK: PASS, TSan: 0 reports) | `opus_r9/logs/ctest_c1.log(.known)`, runs 40932114844, 40935706032 |
| 2 own SPSA tuner driving fastchess | `opus_r9/tuner/r9_spsa.py`: Fishtest-style schedule counted in game pairs, `pairs_per_batch` pairs per perturbation, values rounded to the engine's integers, append-only resumable state (`iterations.jsonl`, fsync per batch), `history.csv`, `tuner.log`, every game as PGN, STOP file, load governor for the 70% cap; report `r9_spsa_report.py` with a null-gradient noise level per parameter; ideas only (Fishtest, OpenBench, Weather Factory: `IDEA_SOURCE.md`) | `opus_r9/tuner/`, `opus_r9/IDEA_SOURCE.md` |
| 2 tests | simulated matches with a known optimum: a parameter 100 below its optimum moves up (z +8.5), one 100 above moves down (z -8.4), one at its optimum stays within 3 sigma, a stopped and resumed run equals an uninterrupted one batch for batch: SIM TESTS OK; fastchess smoke (2 games) shows the options reach both engines | `opus_r9/tuner/test_r9_spsa_sim.py`, `opus_r9/logs/` |
| 3 sanity check (one parameter wrong) | PENDING: `configs/sanity.json` (LmrQuietDivisor 120 vs lock 220, HistoryMalusPercent at its lock value as a control, 4+0.04, 200 pairs) is running and waits for CPU | `F:\opus_scratch\r9\runs\sanity2` |
| 4 real run STC 8+0.08 | PENDING: `configs/stc_main.json` (16 parameters, 1200 pairs planned) | |
| 5 deliver | PENDING | |

## Why steps 3-5 wait
The PC sat at 72-82% CPU without any of this job's work from 19:50 on (psutil and process CPU-time survey: gate
`gateR5D_matefix_t2_nonreg_vs_a3base` conc 4 x Threads 2 = 8.0 CPUs, the live self-play 2.1 CPUs since its owner restart,
the NNUE trainer 1.3 CPUs). One game of 8+0.08 needs about one CPU (6.25% of the 16): under the 70% cap no game fits
while that gate runs (at 20:50: 1,333 of 3,000 games, LLR -1.35). The tuner's governor samples the load between batches
and starts as soon as the cap leaves room. Asked the user at 19:56 for a temporary cap if the runs should start earlier.

## The 74 parameters
| # | parameter | lock value | engine range | origin | bench 11 moves | tuned in stc_main (range, c_end) |
|---|---|---|---|---|---|---|
| 1 | LmrQuietBase | 85 | 0..300 | lock tune:: | yes | yes (0..200, 12) |
| 2 | LmrQuietDivisor | 220 | 100..500 | lock tune:: | yes | yes (120..400, 16) |
| 3 | LmrNoisyBase | 10 | 0..300 | lock tune:: | yes |  |
| 4 | LmrNoisyDivisor | 340 | 100..800 | lock tune:: | yes |  |
| 5 | NullMoveMinDepth | 3 | 1..10 | lock tune:: | yes |  |
| 6 | NullMoveBase | 3 | 1..6 | lock tune:: | yes |  |
| 7 | NullMoveDepthDivisor | 3 | 1..10 | lock tune:: | yes |  |
| 8 | NullMoveEvalDivisor | 200 | 50..1000 | lock tune:: | yes |  |
| 9 | RfpDepth | 8 | 0..15 | lock tune:: | yes |  |
| 10 | RfpMargin | 72 | 10..300 | lock tune:: | yes | yes (30..150, 7) |
| 11 | RfpImproving | 40 | 0..200 | lock tune:: | yes |  |
| 12 | RazorDepth | 2 | 0..6 | lock tune:: | yes |  |
| 13 | RazorBase | 150 | 0..1000 | lock tune:: | yes |  |
| 14 | RazorMultiplier | 350 | 0..1000 | lock tune:: | yes |  |
| 15 | FutilityDepth | 7 | 0..15 | lock tune:: | yes |  |
| 16 | FutilityBase | 100 | 0..500 | lock tune:: | yes | yes (0..250, 14) |
| 17 | FutilityMultiplier | 110 | 0..500 | lock tune:: | yes | yes (40..250, 12) |
| 18 | LmpBase | 4 | 0..20 | lock tune:: | yes |  |
| 19 | HistoryPruneDepth | 3 | 0..10 | lock tune:: | no |  |
| 20 | HistoryPruneMultiplier | 2048 | 0..20000 | lock tune:: | yes |  |
| 21 | SeeQuietMultiplier | 24 | 0..200 | lock tune:: | yes | yes (5..60, 3) |
| 22 | SeeNoisyMultiplier | 150 | 0..1000 | lock tune:: | yes |  |
| 23 | SingularDepth | 7 | 2..20 | lock tune:: | yes |  |
| 24 | SingularMargin | 2 | 0..10 | lock tune:: | yes |  |
| 25 | IirDepth | 4 | 1..20 | lock tune:: | yes |  |
| 26 | ProbcutDepth | 5 | 1..20 | lock tune:: | yes |  |
| 27 | ProbcutMargin | 180 | 0..1000 | lock tune:: | yes | yes (80..350, 16) |
| 28 | QsFutilityMargin | 160 | 0..1000 | lock tune:: | yes |  |
| 29 | QsSeeMargin | 40 | 0..500 | lock tune:: | no |  |
| 30 | AspirationDelta | 18 | 4..200 | lock tune:: | yes | yes (6..50, 2.5) |
| 31 | HistoryBonusQuadratic | 20 | 0..100 | lock tune:: | yes |  |
| 32 | HistoryBonusLinear | 48 | 0..500 | lock tune:: | yes |  |
| 33 | HistoryBonusMax | 2048 | 100..10000 | lock tune:: | yes |  |
| 34 | LmrHistoryDivisor | 6000 | 1000..30000 | lock tune:: | yes |  |
| 35 | CheckExtensionDepth | 2 | 1..30 | lock tune:: | yes |  |
| 36 | LmrCutoffThreshold | 3 | 0..20 | lock tune:: | yes |  |
| 37 | MaterialCorrectionWeight | 100 | 0..300 | lock tune:: | yes |  |
| 38 | TmSoftDivisor | 22 | 5..80 | lock tune:: | no |  |
| 39 | TmIncrementPercent | 75 | 0..150 | lock tune:: | no |  |
| 40 | TmHardPercent | 60 | 10..95 | lock tune:: | no |  |
| 41 | TmHardSoftMultiple | 5 | 1..20 | lock tune:: | no |  |
| 42 | TmStableFactor | 60 | 20..150 | lock tune:: | no |  |
| 43 | TmSemiStableFactor | 80 | 20..150 | lock tune:: | no |  |
| 44 | TmUnstableFactor | 140 | 50..300 | lock tune:: | no |  |
| 45 | TmEffortBase | 155 | 100..250 | lock tune:: | no |  |
| 46 | TmFallingEvalPercent | 100 | 0..400 | lock tune:: | no |  |
| 47 | TmMinFactorPercent | 45 | 10..100 | lock tune:: | no |  |
| 48 | CaptureFutilityBase | 0 | 0..1000 | lock tune:: | yes |  |
| 49 | CaptureFutilityMultiplier | 250 | 0..1000 | lock tune:: | no |  |
| 50 | CaptureFutilityDepth | 6 | 0..15 | lock tune:: | no |  |
| 51 | FailLowContinuationBonus | 0 | 0..300 | lock tune:: | yes |  |
| 52 | NmpEvalDepthMargin | 24 | 0..100 | R9 (former literal) | yes |  |
| 53 | NmpEvalBase | 180 | -200..600 | R9 (former literal) | yes | yes (-100..500, 30) |
| 54 | NullMoveEvalMax | 3 | 0..10 | R9 (former literal) | yes |  |
| 55 | NullMoveVerifyDepth | 14 | 6..64 | R9 (former literal) | no |  |
| 56 | ProbcutImproving | 50 | 0..200 | R9 (former literal) | yes |  |
| 57 | ProbcutReduction | 4 | 2..8 | R9 (former literal) | yes |  |
| 58 | SingularTtDepth | 3 | 1..8 | R9 (former literal) | yes |  |
| 59 | SingularDoubleMargin | 24 | 0..200 | R9 (former literal) | yes | yes (0..80, 5) |
| 60 | SingularDoubleLimit | 6 | 0..20 | R9 (former literal) | no |  |
| 61 | LmrTtPv | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 62 | LmrNotImproving | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 63 | LmrCutNode | 2048 | 0..6144 | R9 (former literal) | yes | yes (0..4096, 256) |
| 64 | LmrTtCapture | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 65 | LmrGivesCheck | 1024 | 0..4096 | R9 (former literal) | yes | yes (0..3072, 192) |
| 66 | LmrInCheck | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 67 | LmrCutoffCount | 1024 | 0..4096 | R9 (former literal) | yes |  |
| 68 | HistoryBonusOffset | 32 | -200..300 | R9 (former literal) | yes |  |
| 69 | HistoryMalusPercent | 100 | 0..300 | R9 (former literal) | yes | yes (40..200, 10) |
| 70 | HistoryDepthBonusMargin | 100 | 0..1000 | R9 (former literal) | yes |  |
| 71 | AspirationMinDepth | 4 | 1..16 | R9 (former literal) | yes |  |
| 72 | AspirationGrowPercent | 50 | 10..300 | R9 (former literal) | yes |  |
| 73 | AspirationGrowAdd | 4 | 1..100 | R9 (former literal) | yes |  |
| 74 | QuietCheckBonus | 12000 | 0..40000 | R9 (former literal) | yes | yes (0..30000, 1500) |

Ranges are the engine's clamps (`setoption` values outside are clamped); the tuner uses the narrower ranges in its
config. LMR adjustments are in 1/1024 ply, summed and rounded to the nearest whole ply (`(r1024 + 512) >> 10`; the lock's
integer adjustments are the multiples of 1024, so the default reductions are unchanged). Aspiration growth has floors
(10% and 1) so no setting can stop the window from widening.
