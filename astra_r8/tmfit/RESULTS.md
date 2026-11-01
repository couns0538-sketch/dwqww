# Astra R8 fitted time model — UNPROVEN

Source base: `905e2325caeabea92b1017b22b434218a43145a7`, the explicitly permitted
`forge-bundle-int` parent fallback. Lock executable identifier: FD3A5190 (AL1 s198).
Branch: `astra-r8-tmfit`. Crew builds the LTO+PGO gate executable.

## Checkpoint 1 — setup and implementation in progress

Done: isolated worktree; examined AL1 time allocation; delegated logger/model,
grouped logistic fitter, and native UCI validation harness; requested local Git
exclusions installed. No search algorithm changes authorized.

Storage: C: 182.1 GB, D: 83.8 GB, F: 49.1 GB at setup. User authorized D: scratch
instead of F: with 50 GB minimum free. Scratch is
`D:/grok-pc-data/dwqww/astra8-scratch`, capped at 5 GB.

| Test | Status | Evidence / next action |
|---|---|---|
| Data: >=50,000 real root iterations | NOT RUN | Build logger and collect seeded self-play |
| Fit: grouped 20% held-out AUC | NOT RUN | Final iteration excluded from labels |
| 1 OFF pins d11/13/16/20/22 | NOT RUN | 312866 / 862329 / 3024920 / 12389307 / 34048354 |
| 1 ON fixed-depth identity | NOT RUN | Same pins required |
| 1 perft5 | NOT RUN | start 4865609; kiwipete 193690690 |
| 2 timed live proof | NOT RUN | 20 positions, fresh processes, interleaved, median3 |
| 3 200-game average time | NOT RUN | ±3%; zero flags/illegal moves |
| 4 hard limits | NOT RUN | 50 positions, 1s + .01s, budget +20ms |
| 5 absurd coefficient clamp | NOT RUN | Expose-only TmFitA |
| 6 ASan+UBSan ON smoke | NOT RUN | Native toolchain capability to establish |
| 7 patch/README/fitter/tests/skill | IN PROGRESS | Patch must apply to base with -p1 |
| Crew SPRT | UNPROVEN | CR first, then Strength and QA; UHO primary, 8moves separate, longer TC confirm |

Blockers: none after D: scratch authorization; optional CodeRabbit/Sonar CLIs and
MCP analysis tools are not currently available. Never treat missing analysis as PASS.

Next: build and establish OFF pins; collect actual logs; fit coefficients;
calibrate multiplier on separate paired games; run success matrix and hand off.

## Checkpoint 2 � implemented, collecting; UNPROVEN

Logger, model, NumPy fitter, native referee and six harness modes implemented.
Fitter 13 tests PASS, harness 4 tests PASS, numeric bounds test PASS. An independent
review corrected unstable-search selection bias and noise-only live-proof criteria.
Initial build failed due to omitted FORGE_NNUE_HIDDEN=256; original failed log is
preserved in scratch. Corrected x86-64-v3 GCC15.2 O3, ffp-contract=off, static,
Expose+TM_LOG build succeeds. Embedded net SHA256:
`0cc9ac542ed4a2271459f3e4819277f3d9b77122ec1bf1ab536673d34af21807`.
OFF bench d11/d13/d16/d20 matches 312866/862329/3024920/12389307;
full matrix remains running. Collection at 8+0.08, seed2026110108, 8moves_v3,
Threads1/Hash16 is running. Coefficients remain UNFITTED neutral placeholders.
Source checkpoint1 published: 79ff4d68. New sanitizer workflow is branch-scoped.
Next: finish 50k data, real fit and mapping calibration, final binary validation.
Prior art limitation: requested named variants except TimeManV2 were not found in
available refs; see PRIOR_ART_AUDIT.md. No claim to have reviewed absent source.
