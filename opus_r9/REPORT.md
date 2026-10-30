# R9 SPSA search-parameter tuning for Forge — IN PROGRESS

Branch `opus-r9-spsa` = AL1 lock `d4f4312` + CI baseline `0d99f02` + R9 commits. PC clock times. Machine exclusive:
no (PC gates, live self-play and the NNUE trainer ran beside it; the user paused self-play at about 23:30).
**No Elo claims:** only QA's gate can show whether the tuned values are better.

## Acceptance
| step | result | evidence |
|---|---|---|
| 1 parameters behind one `R9Tune` switch, default off | 74 tunables (the lock's 51 `forge::tune` constants + 23 former literals) as advertised spin options with the lock values as defaults. `R9Tune` off: bench **312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609** (and kiwipete 193690690) = ALL OK; `R9Tune` on at the defaults: ALL OK too (the former literals are reproduced exactly); off + a changed tunable: bench unchanged; on: 58 of 74 move bench 11 by themselves (time-manager parameters cannot move a fixed-depth bench; the rest need larger values or are off in the lock) | `opus_r9/logs/identity_off_c.log`, `identity_on_defaults_c.log`, `option_check_c.log/.json`, `option_check_b_probes.log` |
| 1 tests | box build 0 warnings, FMA 0; CMake 30 targets + CTest 14 tests: only the 4 known `forge_tests` lines; opus-ci green on `8856be4a` and `22b1f2ba` (release ALL OK, ASan/TSan KNOWN-FAILURE CHECK: PASS, TSan 0 reports) | `opus_r9/logs/ctest_c1.log(.known)`, runs 40932114844, 40935706032 |
| 2 own SPSA tuner driving fastchess | `opus_r9/tuner/r9_spsa.py` (Fishtest-style schedule counted in game pairs, values rounded to the engine's integers, append-only resumable state, `history.csv`, `tuner.log`, every game kept as PGN, STOP file, load governor), report with a null-gradient noise level per parameter, trajectory chart; ideas only, sources in `IDEA_SOURCE.md` | `opus_r9/tuner/`, `opus_r9/IDEA_SOURCE.md` |
| 2 tests | simulated matches with a known optimum: up z +8.5, down z -8.4, at-optimum within 3 sigma, stopped+resumed == uninterrupted; real games: every sanity2 result re-counted from the PGNs (0 attribution mismatches), option values checked in the engine logs | `opus_r9/tuner/test_r9_spsa_sim.py`, `opus_r9/logs/tuner_sim_test_trajectories.svg` |
| 3 sanity: one parameter set wrong | both runs moved the wrong parameter **toward its lock value**: LmrQuietDivisor 120 -> 138.6 (lock 220, z +1.27, 200 pairs), LmrQuietBase 250 -> 189.3 (lock 85, z +1.48 toward it, 240 pairs); neither beyond 2 sigma alone, combined z 1.94 (one-sided p about 0.03); controls (HistoryMalusPercent at its lock value) z +1.02 and -1.88 | `opus_r9/results/sanity2/`, `opus_r9/results/sanity3/` (tables + charts) |
| 4 real run, STC 8+0.08 | RUNNING (`F:\opus_scratch\r9\runs\stc1`, until 04:45) | `opus_r9/runs/stc1/` (snapshots every 10 min) |
| 5 deliver | after the run | |

## Sanity runs (4+0.04, Threads 1, Hash 16, 2 pairs per batch)
- sanity2 (`configs/sanity.json`): LmrQuietDivisor started at 120 (lock 220). 200 pairs, +47 -64 =289 (72% draws). It waited for CPU from 20:56 to 23:31 under the first 70% cap.
- sanity3 (`configs/sanity3.json`): LmrQuietBase started at 250 (lock 85, +1.65 plies of reduction on every late quiet move), larger perturbation. 240 pairs, +62 -60 =358 (75% draws).
- Reading: the direction is right in both runs, the size is not beyond the noise band of 200-240 pairs. Games of
  nearly equal engines at 4+0.04 end drawn 72-75% of the time, so each pair carries little information; the same limit
  applies to the STC run (see below). The update rule itself is proven by the simulated test (z +-8.5).

## Load and the governor
- 19:50-23:30: the PC sat at 72-82% CPU without this job (gate conc 4 x Threads 2 = 8.0 CPUs, live self-play 2.1, NNUE
  trainer 1.3); under the first 70% cap no game could run (the governor waited, sanity2 waited 8,820 s).
- 23:3x: the user raised the cap: start a batch while the load without the tuner is <= 80%, play as many games as keep
  the total <= 90% (at most 4, BelowNormal, CPUs 0-3), pause between batches if the total stays above 90% for 60 s or
  free RAM < 8 GB (never kill). The user paused self-play at about 23:30; the gate ended at its 3,000-game cap at 00:10.
- Every batch records the load it started at, its concurrency and what it saw while it played (`iterations.jsonl`).

## Findings
- The lock already kept 51 search constants in `forge::tune`, accepted silently by `setoption`; R9 makes them
  advertised options (the gate runner checks that options it sets are advertised) and gates them behind `R9Tune`.
- Truncating fractional LMR adjustments made a sub-ply change invisible unless the sum crossed a whole ply; R9 rounds to
  the nearest ply (identical for the lock's whole-ply values).
- `AspirationGrowPercent = 0` with `AspirationGrowAdd = 0` (inside the old-style ranges) would never widen the window: R9
  floors them at 10 and 1.
- Short SPSA runs at fast TCs are noise-limited (72-75% draws at 4+0.04): read every move against its noise sigma; a gate
  of many noise-sized moves of near-optimal parameters can cost Elo, so the likely-real subset is the safer second gate.

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

## Time
Commits on this branch after the base: 17, 2026-10-29 20:31:25 -0700 .. 2026-10-30 00:53:51 -0700 (git log). The work before them (R7/R8 fixes) is on `opus-r7-speed` and `opus-r8-datagen`.

