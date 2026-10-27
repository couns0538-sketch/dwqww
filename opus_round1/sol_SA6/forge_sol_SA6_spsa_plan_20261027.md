# S-A6: SPSA re-tune of the search after a new net locks — PLAN ONLY (UNPROVEN)

- **Source:** test plan row 6, gate G-A6, srand 881917307; `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 42.
- **Trigger:** run only after a G-A1 net (more self-play data, h256 retrain) or a G-A4 net (hidden 512) locks.
- **Where:** in QA slots only.
- **Status:** no games were played, and nothing is applied or queued.
- **Machine-readable plan:** `forge_sol_SA6_spsa_plan_20261027.json`, checked by `opus_sa6_plan_check.py`
  (`logs/step1_plan_check.log`: PASS).

## 1. Why re-tune after a net change
Many of the 51 tunables are in eval units: margins in centipawns and eval-derived divisors. Their best values depend on
the net's eval scale and accuracy. A new net changes both; an H512 net also changes NPS, and with it the depth reached
per move.
- AL1's values were tuned (or inherited) for earlier nets.
- A re-tune is the standard step after a net change. In public engines, SPSA retunes after a net switch are routine.
- The expected gain is small: a few Elo. It needs a gate like any other change.

## 2. Step 0: eval-scale check (cheap, deterministic, no games)
- **Measure.** Run the S41 eval-scale check (branch `opus-sol-S41`) on the new lock net against AL1's net over the
  fixed 10k-FEN set. It gives the regression slope s of the new static eval on the old one.
- **Rescale or not.** If |s − 1| > 0.05, multiply the stage-A centipawn margins (RfpMargin, RfpImproving, RazorBase,
  RazorMultiplier, FutilityBase, FutilityMultiplier, QsFutilityMargin, ProbcutMargin, AspirationDelta) by s, and
  NullMoveEvalDivisor by s. Use these as the SPSA start values. Otherwise start from AL1's values.
- **Record** s, the start values and the bench of the exposed start build in the run's RUN_INFO.

## 3. Which parameters (all 51 accounted for; checked by the tool)
| group | params | treatment | why |
|---|---|---|---|
| **A: eval scale** (11) | RfpMargin, RfpImproving, RazorBase, RazorMultiplier, FutilityBase, FutilityMultiplier, QsFutilityMargin, ProbcutMargin, NullMoveEvalDivisor, AspirationDelta, MaterialCorrectionWeight | SPSA stage A | centipawn margins and eval-derived divisors. MaterialCorrectionWeight blends correction history into the static eval, so its optimum moves with the net's error |
| **B: search shape** (9) | LmrQuietBase, LmrQuietDivisor, LmrNoisyBase, LmrNoisyDivisor, HistoryPruneMultiplier, LmrHistoryDivisor, SeeQuietMultiplier, SeeNoisyMultiplier, QsSeeMargin | SPSA stage B, after A is applied | tree shape and SEE thresholds; they move with NPS and with ordering quality |
| depth gates (12) | NullMoveMinDepth, NullMoveBase, NullMoveDepthDivisor, RfpDepth, RazorDepth, FutilityDepth, HistoryPruneDepth, SingularDepth, IirDepth, ProbcutDepth, CheckExtensionDepth, CaptureFutilityDepth | excluded | small integers (ranges 5-29): a ±1 SPSA step is 10-30% of the value. Change them only by hand, one gate each |
| small-range integers (3) | LmpBase (0-20), SingularMargin (0-10), LmrCutoffThreshold (0-20) | excluded | same reason |
| dead or off features (3) | CaptureFutilityBase (0), CaptureFutilityMultiplier, FailLowContinuationBonus (0) | excluded | capture futility runs only if CaptureFutilityBase > 0 (search.cpp:1075), so its multiplier is dead; FailLowContinuationBonus is 0 = off. Tuning a dead parameter only adds noise (S08-4) |
| history-table dynamics (3) | HistoryBonusQuadratic, HistoryBonusLinear, HistoryBonusMax | excluded | they rescale every history table and interact with Astra A1 (history rework, `opus-sol-A1`). Tune them only together with A1 if A1 locks |
| time management (10) | Tm* | excluded | they depend on the time control. SPSA at one fixed time control would overfit; time management needs its own method (time-odds tests at the gate controls) |

c_end (the final perturbation, in parameter units) is 1-4% of each range, about 5-10% of the default value; the tool
prints every one. The first perturbation is c_1 = c_end × N^0.101, about 2.2-2.3 × c_end. Only LmrNoisyBase (default
10) gets clamped at its bound 0 early on; that is acceptable, since the clamp only shortens its first steps.

## 4. SPSA settings
- **Schedule** (Spall / fishtest style):
  - a_k = a / (A + k + 1)^0.602 and c_k = c / (k + 1)^0.101, with A = 10% of the iterations;
  - per-parameter c_end, with r_end = a_end / c_end² = 0.002 (fishtest's usual end learning rate).
- **Games:** each iteration plays 4 game pairs between θ+ and θ− with reversed colours (8 games), which fills 8
  slots per iteration.
- **Conditions:** time control 8+0.08 (between the gate's 10+0.1 and half of it), Threads 1, Hash 16, the gate
  opening book with fresh offsets, fastchess `-strict`.
- **Build:** the exposed build (`-DFORGE_EXPOSE_TUNABLES=1`), required because fastchess refuses unadvertised options
  (S15 finding 1).

| stage | params | games | iterations | seconds per game per slot | QA-slot hours (conc 8) |
|---|---|---|---|---|---|
| A eval scale | 11 | 24,000 | 3,000 (A = 300) | 23.2 (ESTIMATE) | **19.3** |
| B search shape | 9 | 20,000 | 2,500 (A = 250) | 23.2 | **16.1** |
| STC gate (cap) | — | ≤ 1,500 | — | 29 (measured) | ≤ 1.5 |
| LTC confirm (cap) | — | ≤ 1,500 | — | 116 (ESTIMATE) | ≤ 6.0 |
| **total** | | | | | **≤ 43** |

**Throughput basis.**
- **Measured:** 24 gates at 10+0.1 (G98-G125 RESULT.md / RUN_INFO.json, the copies used by S44) took 29 s per game
  per slot at every concurrency: 955-987 games/h at conc 8, 840-859 at conc 7, 604-625 at conc 5.
- **Model:** game time = 2 × (0.8 × base + inc × 65 moves per side), which reproduces the measured 29 s at 10+0.1.
  8+0.08 and 40+0.4 are scaled from it (labelled ESTIMATE).

**Cheaper fallback.** Stage A only, 12,000 games at 6+0.06 (17.6 s per game per slot): about 7.3 QA-slot hours. It
is noisier, so expect less of the possible gain.

## 5. Harness: what S15 v2 has and what a real tune needs
S15 v2 (`opus-sol-S15`, `forge_sol_S15_spsa_v2.py run`) already has: the catalog with ranges parsed from the source,
the exposed-build check, fastchess with game pairs, pentanomial cross-checking with the owned checker, pinned inputs,
and Idle priority.

Before stage A it needs these changes (a v3, with its own tests and a CR):
1. **Spall schedule.** v2 uses gain/√(k+1) and c/(k+1)^(1/6) with no A. That gives fast decay and its largest steps in
   the noisiest first iterations. Add A, α = 0.602, γ = 0.101.
2. **Per-parameter c_end.** v2 has one global perturbation in normalized [0, 1] units. Read c_end per parameter from
   the plan JSON.
3. **Long-running fastchess.** v2 starts fastchess per iteration, which costs about 2-3 s per 23 s iteration at
   8 games (ESTIMATE). Keep one fastchess session per block of iterations, or accept the overhead.
4. **Resumable state and checkpoints.** Write θ every 50 iterations; on a restart, continue from the last θ, so a
   multi-hour run survives PC reboots and gate preemption.
5. **QA-slot priority.** Run at the gate engines' priority (BelowNormal) in QA slots, never next to a gate and never
   above self-play or training. v2's default `--priority idle` is for side runs, like the S15 fixture.

## 6. Applying and validating
1. **End of stage A.** Round θ to integers and apply only the parameters that moved by more than c_end from their start
   (the rest is noise). Write them as new defaults in the tune table (`src/search.cpp`, values only, diff reviewed by
   CR).
2. **Stage B** starts from the stage-A result. Apply it the same way.
3. **Build.** Box recipe, FMA 0. The bench changes (new search), so new pins come through QA's pin process. We never
   run the lock or pin kit ourselves.
4. **STC gate.** SPRT [0,10] at 10+0.1, cap 1500, conc 8, **srand 881917307**, against the new lock (the G-A1/G-A4 net
   with AL1 search values).
5. **LTC confirm** at 40+0.4 before any lock: SPSA at a short time control can fail to transfer. The test plan
   requires a 40+0.4 confirm for EVAL changes; we recommend it here as well. Use a fresh srand and log it.
6. **If the STC gate caps or fails:** keep the lock's values; the SPSA logs remain as data. Do not re-run the same
   SPSA to "get a pass".

## 7. Risks and limits
- **Noise:** 24k games over 11 parameters is a modest budget. The expected gain is a few Elo, and part of the measured
  movement is noise; hence the "moved more than c_end" filter and the gate.
- **Time-control overfit:** 8+0.08 against the gates' 10+0.1 and 40+0.4. The LTC confirm guards against it.
- **Interactions:** the stage order (A then B) and the excluded groups are judgment calls, chosen to keep the
  dimension per stage at 9-11.
- **No measured c_end:** the c_end values are heuristics (about 5-10% of the default). A short pilot (2,000 games)
  can check that ±c_end moves the score measurably before the full stage is spent.
