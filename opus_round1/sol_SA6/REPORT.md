# S-A6 SPSA re-tune plan (G-A6) — DONE (plan only; UNPROVEN, no games)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 42 ("S-A6 SPSA re-tune plan (run only after an A1/A4 net locks)");
`OPUS_TEST_PLAN.md` row 6 (G-A6, search, QA slots only, srand 881917307).
- **Branch:** `opus-sol-SA6` = `d4f4312` + `0d99f02` cherry-picked (`1f868642`) + this job.
- **Scope:** plan only, so there is no engine change (`[skip ci]`), no games, no tune applied.
- **Overlap:** S15 (`opus-sol-S15`) delivered the SPSA harness and catalog; this job is the plan for a real re-tune.

## Acceptance
| item | result | evidence |
|---|---|---|
| plan for an SPSA re-tune after a G-A1/G-A4 net locks | **DONE** | `forge_sol_SA6_spsa_plan_20261027.md`: trigger, step 0 eval-scale check (S41), parameter groups, settings, budget, harness changes, apply/validate, risks |
| every one of the 51 tunables accounted for | **PASS** | `opus_sa6_plan_check.py`: stage A 11, stage B 9, excluded 31 (depth gates 12, small-range integers 3, dead/off features 3, history dynamics 3, time management 10). Each parameter appears once; the catalog sha256 `85601714…` equals S15's SHA256SUMS (`logs/step1_plan_check.log`) |
| ranges and perturbations valid | **PASS** | every SPSA parameter's default lies inside its range, the range is ≥ 50, and c_end is 1-10% of the range (1.0-3.8% in this plan). One warning: LmrNoisyBase's first perturbation (±17.6 around 10) is clamped at 0 |
| budget from measured numbers | **DONE** | 24 gates at 10+0.1 took 29 s per game per slot. Stage A: 24,000 games at 8+0.08 = 19.3 QA-slot hours (conc 8); stage B: 20,000 games = 16.1 h; STC gate ≤ 1.5 h; LTC confirm ≤ 6.0 h; total ≤ 43 h |
| validation | **DONE** | STC SPRT [0,10] at 10+0.1, cap 1500, srand 881917307, against the new lock; then a 40+0.4 confirm with a fresh srand |
| tool tested | **PASS** | `test_opus_sa6.py` 6/6 (`logs/step2_tests.log`); planted bugs 6/6 caught (`logs/step3_mutation_check.log`) |

## Findings
1. **Six of the 51 "tunables" should not be in an SPSA run.**
   - Capture futility runs only when CaptureFutilityBase > 0 (`search.cpp:1075`), and its default is 0, so
     CaptureFutilityMultiplier is dead.
   - FailLowContinuationBonus is 0 (off).
   - SingularMargin, LmpBase and LmrCutoffThreshold have ranges of 10-20, where a ±1 step is far too coarse.
2. **The S15 v2 harness needs changes before a real tune.**
   - Its schedule (gain/√(k+1), c/(k+1)^(1/6), no A) takes its largest steps in the noisiest early iterations.
   - It has one global normalized perturbation instead of per-parameter c_end.
   - It starts fastchess per iteration.
   - It has no checkpointed θ for multi-hour runs.
   §5 of the plan lists the changes (a v3 with tests and a CR).
3. **Gate throughput is very regular:** 29 s per game per slot at 10+0.1, at conc 5, 7 and 8 alike, over 24 gates.
   Concurrency scales throughput almost linearly up to 8.

## Files
- `forge_sol_SA6_spsa_plan_20261027.md`, `forge_sol_SA6_spsa_plan_20261027.json`;
- `inputs/forge_sol_S15_parameter_catalog_20261027.json`;
- `opus_sa6_plan_check.py`, `test_opus_sa6.py`, `mutation_check_sa6.py`;
- `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`, `logs/step1-3`.

How it was run: the checker and tests are pure Python (read-only venv, `-I -B`, `nice -n 19`); the mutant copies are
in `F:\opus_scratch\sol_SA6\mutants\run1`. No engine, fastchess or GPU ran. Machine exclusive: no.

## Left / UNVERIFIED
- The whole tune. It runs only after a G-A1 or G-A4 net locks, in QA slots.
- The c_end values are heuristics; a 2,000-game pilot should confirm them first.
- The 8+0.08 and 40+0.4 game times are ESTIMATEs scaled from the measured 10+0.1.
- The harness v3 changes are specified here but not built.
