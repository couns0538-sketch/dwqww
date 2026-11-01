# Fitted time management — UNPROVEN

Candidate branch: `astra-r8-tmfit`. The authoritative gate patch is now
`tmfit-lock.patch`, based on actual AL1 s198 lock source
`294dbed3a15dfd821aaf9d4edc6e5f62832fd460`. Its SHA256 is
`ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3`,
identical to CR's supplied port. Apply with `git apply --check -p1` then
`git apply -p1` on that exact tree. CI builds this patched lock checkout.

The branch-root engine is the earlier reference implementation on the permitted
905e2325 fallback. Its unchanged historical patch is `tmfit-fallback-905.patch`;
its results cannot qualify the actual-lock port. The final fallback200 run passed
both timing bounds with zero faults. Actual-lock Linux identity, liveness, hard
limits, clamp, sanitizer and 200-game qualification checks passed.
See RESULTS.md. Crew builds must use the authoritative lock patch, not the
reference branch-root engine.

`TmFitModel` is one new default-off UCI spin option. It predicts whether the
last completed iteration's best move will differ from the current one, then
multiplies the existing soft-stop target by a bounded affine function of that
probability. The original hard deadline and maximum allocation stay unchanged.
No TT, pruning, reductions, extensions, history, evaluation or NNUE changes.

The driver snapshots enablement and coefficients once per search. Inference uses
Q10 bounded features, Q12 coefficients and an integer sigmoid table; no dynamic
allocation is added to inference. The legacy soft-factor calculation retains
its existing floating-point arithmetic. Clock allocation activates the model;
pure fixed-depth, movetime and infinite searches do not use its soft-stop adjustment.
ON `info string tmfit` lines show probability, multiplier, target, hard cap,
depth, best-move change, effort and score delta. OFF emits no model diagnostics.

## Fit

52,012 real completed root iterations, 19 OFF self-play games at 8+0.08,
Threads=1, Hash=16, seed2026110108, 8moves_v3. Logging is a default-OFF build
switch, `FORGE_TM_LOG`; its entire block is removed from ordinary builds.
Training and calibration used the905 fallback reference. The actual-lock port
retains those coefficients and mapping without refitting or tuning against its tests.
Root effort is cumulative within the search, matching the existing time manager.
Near-best root move count was omitted because this source does not expose it.

Final completed iterations supply labels and are excluded as training examples.
An aborted later iteration can revise the returned move: that is recorded, not
used to discard unstable searches. Whole opening groups are held out; the split
is 15 training /4 test groups,42,124 /7,276 eligible rows. The20% split is by
whole group (rounded up to4/19); unequal game lengths give14.73% held-out rows.
Related rows are not
independent samples, and opening separation does not prove transposition separation.

| Measure | Result |
|---|---:|
| Held-out AUC, floating / fixed point | 0.682619 /0.682835 |
| Held-out log loss / Brier | 0.344408 /0.101169 |
| Train / test positive rate | 13.53% /12.12% |
| Maximum probability quantization error | 0.007795 |

| Input (Q10, integer truncation) | Coefficient Q12 |
|---|---:|
| Bias=1 | -3201 |
| Depth/16, depth clipped0..64 | -5127 |
| Best move changed0/1 | 6120 |
| Best move node fraction | -3440 |
| Score clipped±2000cp /1000 | -1537 |
| Score delta clipped±1000cp /1000 | -167 |
| Elapsed/base soft allocation, clipped0..4 | 1284 |

The mapping is frozen after 40 paired calibration games: multiplier permille
`clamp(742 + 3000*p, 650, 1750)`. ON/OFF time ratios were 0.986462 per move
and 0.989479 per game-side, with zero faults. The separate200-game fallback
qualification measured0.990168 per move /0.990016 per game-side, zero faults.
These parameters are unchanged in the actual-lock port. Its fresh 200-game
qualification measured 0.990135 per move and 0.990286 per game-side, with zero
illegal moves or time losses. AUC is predictive discrimination on the training-source
holdout, not strength or a separate actual-lock prediction-quality estimate.
The 1% sample, full-data hashes, coefficients and split IDs are in
`evidence/fit_v0_001/`. Raw logs stay in authorized local scratch.

## Gate handoff

Code Review first, then Engine Strength (TM owner), then Engine QA.
The crew builds the LTO+PGO gate executable. Enable the frozen candidate with:

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name TmFitModel value 1
```

The comparison uses `TmFitModel value 0` against FD3A5190. Coefficients and
`TmFitA/B/Lo/Hi` are advertised only in `FORGE_EXPOSE_TUNABLES` builds; gate
invocations need only `TmFitModel=1`. All other experimental options stay OFF.
UHO is the primary SPRT book; 8moves_v3 is separate, never pooled. A TM H1 needs
longer-TC confirmation. No Elo claim is made: **UNPROVEN**.

The actual-lock qualification ran on GitHub Ubuntu 24.04 with plain Release O3,
x86-64-v3, ffp-contract=off, `FORGE_NNUE_HIDDEN=256`, Expose ON and TM_LOG OFF.
OFF and ON matched all five bench pins; perft5 matched both pins. Timed medians
changed on 11/20 positions. All 50 hard-budget positions and all 50 absurd-A
positions passed, and ASan+UBSan completed 389 ON plies without reports.
The final source and evidence package is
`evidence/qualification_actual_lock_final_v2/`; `candidate-source.tar` contains
the exact 77 source files qualified in CI. Its candidate ID is
`55114017bc763b71c097ad5e65acec6a6ff2b0e4d2d1353ddf9166fbafc679e5`.
The installed C++ evidence checker passes; it checks hashes and declarations,
with producer source/binary/test links audited separately. CI run:
https://github.com/couns0538-sketch/dwqww/actions/runs/41296951735.

Historical fallback Windows validation used GCC15.2 plain O3, not crew LTO+PGO.
No actual-lock Windows compiler or engine launched: the governor waited through
56 startup checks above 80% CPU, then the main agent cancelled its own waiting
request. No process suspension was used. For a future authorized native build, use
`build_native.py --source-root <patched-294-source> --base-commit 294dbed3a15dfd821aaf9d4edc6e5f62832fd460 --patch astra_r8/tmfit/tmfit-lock.patch --out <authorized-scratch/new-dir> --expose`.
The native builder uses CR's sleep governor. It never suspends processes.
The crew still owns the LTO+PGO gate build and strength acceptance.
The fitter requires NumPy; the runner and referee use only Python stdlib and
Forge Board code. The referee is same-family legality validation, not an
independent chess implementation. Exact commands and hashes are retained in
each run manifest. See IDEA_SOURCE.md and PRIOR_ART_AUDIT.md for attribution.
