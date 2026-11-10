# opus_spsa_resume: resumable paired SPSA, two-family joint config, independent confirmation (combo29)

**State:** built and qualified without playing a single game. Real tuning is **PENDING QA EXECUTION**. No tuned values and no Elo are claimed anywhere in this pack.
- Live state and resume steps: `STATUS.md`.
- Every engine and synthetic check with its exact command: `BENCH.md`.
- Test suites: `TESTS.md`.
- Review record: `review/REVIEW_LOG.md`.
- Code Review → QA handoff, with the exact order of steps: `HANDOFF.md`.

## What the pack contains
| Path | Content |
|---|---|
| `spsa/` | The harness. `opus3_spsa.py` is the CLI: run, status, verify, rollback, export. `space.py` holds the parameter space, the R9 gain schedule, the feasible perturbation and the projection onto bounds and constraints. `ledger.py` holds the hash-chained pair ledger, atomic checkpoints and crash hooks. `synth_qualify.py` runs the synthetic run-size qualification. `r9_spsa*.py` is the verbatim import from `opus-r9-spsa` 73eb280a (see `PROVENANCE.md`). |
| `configs/` | `joint_razor_qs.json`: the proposed joint run, live disabled. `baseline_combo29.json`: the lock values, used as the rollback target. |
| `patches/` | `tune_gate_after_combo29.patch`: default-OFF switches `RazorTune` and `QsTune` for the combo29 source. Adds `include/forge/tune_gate.hpp` and makes three insertions in `uci.cpp`; `search.cpp` is unchanged. |
| `engine/` | The derived build recipe, its interdiff and a guarded wrapper (`build_o3.ps1`); the UCI driver; the identity battery (`qualify.py`); the PE comparison; the FEN-result and warm-transcript comparisons; and the mask-only copy of QA's warm-identity tool with its interdiff. |
| `partition/` | The opening partition of `8moves_v3` into train / screen / holdout G1–G3, frozen before any fitting and pairwise disjoint (`PARTITION_MANIFEST.json`). |
| `confirm/` | The independent confirmation pack: `confirm_runner.py`, the fixed candidate rule `select_candidate.py`, `power_table.py`, `CONFIRM_PROTOCOL.md`, `PROPOSED_QA_ENTRY.json`, `HOLDOUT_MANIFEST.json`, `ROLLBACK.md` and the protocol configs. It never imports tuner code. |
| `bin/` | PowerShell 5.1 entry points. Each sets Idle and mask 0xF000 on itself and reads both back before starting a child. `spsa.ps1`, `confirm.ps1`, `rollback.ps1`, `selftest.ps1`, `freeze_inputs.ps1`. |
| `tests/` | R9 saved-run replay equivalence, harness tests (synthetic, replay, crash at every boundary, refusals, rollback) and confirmation tests. |
| `evidence/` | Freeze manifests, lineage, INC-01, build receipts, PE comparisons, identity battery, synthetic qualification, fens12k and warm runs. |
| `AUDIT.md`, `PLAN.md`, `IDEA_SOURCE.md` | Tunable inventory with tuning history, the plan as revised after M1, and sources and licences. |

## The two families
- **F1 razoring:** `RazorBase`, `RazorMultiplier`.
- **F2 qsearch pruning:** `QsFutilityMargin`.
- **Frozen:** `RazorDepth` 2 and `QsSeeMargin` 40.

None of these values was ever tuned (`AUDIT.md`). They are coupled in the code: razoring returns the verdict of qsearch, so the qsearch margins decide whether a razor attempt cuts. The coupling is code-level only; no measurement supports an interaction. In-flight work that would make the configuration stale (DR01, DR04, DR06, DR12, DR14, DR15) is listed in `PLAN.md` §5. The exe pin enforces the staleness rule.

## How QA would run it
Nothing below starts a game unless QA passes all three live guards.
1. **Code Review** of `patches/tune_gate_after_combo29.patch` and this pack.
2. **Tuning uses the lock exe itself.** The tuned scalars are existing UCI options of the lock (`FORGE_EXPOSE_TUNABLES=1`), and `configs/joint_razor_qs.json` pins its SHA256.
   - Dry-run first. It prints the exact fastchess command and writes nothing:
     `powershell.exe -NoProfile -ExecutionPolicy Bypass -File bin\spsa.ps1 -Config configs\joint_razor_qs.json -RunDir <run dir>`
   - **Live mode** needs all three of: `-Mode live -Live`, `live.enabled = true` in QA's copy of the config, and `<run dir>\LIVE_ACK.txt` holding that config's sha256.
   - Run size: see `BENCH.md` §6 and `PLAN.md` §4 before choosing N.
3. **Resume after any interruption:** the same command with `-Resume`. The ledger is replayed, and only the missing pairs of the pending batch are played. Each update is applied exactly once.
4. **Candidate:** `bin\confirm.ps1 -Command select -TrainingRun <run dir> -CandidateOut <cand.json>`.
   - This is the fixed rule: the final θ of a COMPLETE **live** run, as the nearest feasible integers.
   - The spec is hashed and records the training mode and config sha256.
   - A synthetic run is refused unless `-AllowNonLive` is given; that switch is for tests and demonstrations only.
5. **Confirmation:**
   - QA's own runner with `confirm/PROPOSED_QA_ENTRY.json`: UHO book, SPRT [0,5], recommended cap 40,000.
   - Or the G1 route, capped at 4,816 games (`confirm/CONFIRM_PROTOCOL.md` §3). This pack's runner never plays a game: its dry-run prints the exact fastchess command, QA plays it, and `-Mode replay` recomputes the decision.
   - In the protocol, QA pins `training_config_sha256`, its live config's RUN.json `config_sha256`.
   - Then run `bin\confirm.ps1 -Command audit` on the gate PGN. It rebuilds start positions from FEN tags or `{book}` moves and reports leakage and candidate issues.
6. **Rollback** (`confirm/ROLLBACK.md`):
   - the lock exe with no options;
   - or `option.RazorTune=0 option.QsTune=0` on the gate build;
   - or `bin\rollback.ps1 -RunDir <run> -ToCkpt <n>` for a tuning run.

**Script defaults.** The `bin\*.ps1` defaults for `-Python` (the grok-pc venv) and `-TempDir` (this job's `tmp\`) name this PC's paths. Pass your own when running elsewhere or for another job.

## Verify the pack
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File bin\selftest.ps1`: all no-engine tests; writes `TESTS.md`.
- `MANIFEST.md5` and `MANIFEST.sha256`: hashes of every file in the pack.
