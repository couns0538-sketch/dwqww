# S15 tool usage and deferred real smoke — 2026-10-27

This is source-only preparation, not completed S15 delivery. The tool runs Python catalog/math/file bookkeeping only and never launches an engine, compiler, Fastchess or another process. Every invocation requires a NEW own output directory; existing outputs are refused. Inputs are read-only and hash-pinned. The original owned PGN checker must retain its exact SHA256/line endings. Python bytecode writing is disabled before dynamic imports.

Pure demonstration (all51 actual parameters, no NetScale):

```bash
PYTHONDONTWRITEBYTECODE=1 python -B forge_sol_S15_spsa_20261027.py demo --source /path/to/exact_L --seed 20261027 --iterations 20 --out /path/to/NEW_s15_demo
```

The objective is negative mean squared normalized distance from0.5. Projected integer probes differ in every coordinate, including source bounds; effective integer differences are used in the estimate. Gains are demo controls, not tuned chess values. Determinism means identical inputs/code/Python and seed, with output paths excluded from result content. No objective gain implies chess strength.

After root separately releases native resources, the bounded real smoke plan is:

1. Pin an exact-L private source tree and the existing strict S27 recipe. Reuse the existing compiler/flags and build with only CMake `FORGE_EXPOSE_TUNABLES=ON`; do not change engine source. Before UCI, the new main ELF's FIRST execution must be bare `bench 11` and return308972. Reuse the existing full Std checks to establish the exposed build's fixed node references/perft/FMA/default behavior. These steps have NOT RUN in this preparation.
2. Use the existing S07 Capture/transport under the S08 SubreaperScope/owned cleanup wrappers to capture complete UCI/EOF with a preregistered120s deadline. Require the source-defined51 spin declarations plus Hash/Threads/OwnBook support. Prove both selected plus/minus settings were applied by issuing setoption, then `uci` again: L advertises the current pointed-to value. Bind each complete transcript and settings to the actual executable SHA, source/recipe/network hashes and exact planned command. Hidden options without this support proof are rejected by the new planner. Preserve all raw stdout/stderr; don't substitute a generated transcript for an actual engine response.
3. First run the existing L tools/match/run_match.py A/A calibration with the same exposed executable in both slots, `--mode smoke --pairs 2 --aa --nodes 1000 --disable-book --seed 20261027 --hash-mb 16`, a verified deterministic two-opening EPD and CPU2. Preserve raw PGN/logs and require normal, legal complete reversed-color pairs. This is infrastructure only, not equal-time Elo evidence.
4. Prepare one SPSA iteration selecting only `LmrQuietBase,QsSeeMargin`, explicitly excluding unsupported NetScale. Use the actual initial UCI response from step2 and exact binaries/openings:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B forge_sol_S15_spsa_20261027.py plan --source /path/to/exact_L --engine /path/to/exposed_forge --fastchess /path/to/fastchess --openings /path/to/verified_two_positions.epd --uci-transcript /path/to/ACTUAL_initial_uci.stdout --select LmrQuietBase,QsSeeMargin --seed 20261027 --pairs 2 --tc 0.25+0.01 --out /path/to/NEW_s15_real_iteration0
```

5. Read `forge_sol_S15_match_plan_20261027.json`. Execute its exact `command` argument array from its `command_cwd` through the existing owned-process wrapper, CPU2/nice19, timeout120s, no other timed/native workload. The generated command is two engines from the same pinned ELF with distinct integer plus/minus settings, Threads1/Hash16/OwnBookfalse, deterministic openings, reversed colors, concurrency1, strict mode, original PGN/logs, no SPRT and a200-move smoke cap. Preserve exact command/returncode/normal EOF and rehash all inputs. Reject any crash, timeout, illegal move, incomplete pair or non-normal termination; don't count these as losses or gradients. No engine process is launched by the `plan` command itself.
6. Only after those independent execution/legality/option checks, import the actual completed PGN:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B forge_sol_S15_spsa_20261027.py observe --plan /path/to/NEW_s15_real_iteration0/forge_sol_S15_match_plan_20261027.json --pgn /path/to/NEW_s15_real_iteration0/forge_sol_S15_original_games_20261027.pgn --out /path/to/NEW_s15_observed_iteration0
```

The observer rehashes pinned inputs/selected openings, imports the existing paired-PGN checker, refuses incomplete/non-normal/mismatched pairs, preserves the original PGN byte-for-byte and makes one projected SPSA update from `score_plus` and `1-score_plus`. It deliberately labels execution binding UNVERIFIED because PGN tags alone cannot prove binary/options or move legality. That label cannot be upgraded by source-only tests. A later plan may consume `--state /path/to/observed_state.json` with the same source/catalog/selection/seed. Keep real optimization disabled until the independent execution receipt is verified; no tuned constants or acceptance patch is emitted.

Stop after this single real iteration and report infrastructure results, source hashes and raw outcomes. It is too small for an Elo conclusion. NetScale needs its own authoritative source/default/range if later implemented; no source patch to invent it is part of S15.
