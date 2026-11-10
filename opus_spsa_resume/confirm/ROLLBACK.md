# ROLLBACK: exact artifacts

| Situation | Rollback | Evidence |
|---|---|---|
| Confirmation H0, cap without decision, invalid run, or any doubt | Keep the lock: `forge_clang_combo29_trial_w6.exe`, SHA256 e1284f7f…802e, no options | `configs/baseline_combo29.json`, `CURRENT_LOCK.json` (read-only) |
| Gate build already deployed for testing | `option.RazorTune=0 option.QsTune=0`. The family values return to the start (lock) values whatever else was set, and the search is node-identical to the lock. | `BENCH.md` (gate semantics, bench and fens12k identity) |
| Gate build not wanted at all | Build with both macros at 0, or simply do not apply `patches/tune_gate_after_combo29.patch`. With both macros at 0 the patched `uci.cpp` preprocesses to the parent's exact text, and the image is normalized-identical to an unpatched build of the same recipe. | `BENCH.md` (pe_compare) |
| Tuning run went wrong (while it runs) | `bin\rollback.ps1 -RunDir <run> -ToCkpt <n>` appends a logged rollback record and writes a new checkpoint with θ and k of checkpoint n; history is never rewritten. **A COMPLETE run is refused** unless `-ReopenComplete` is given, and a reopened run can never yield a candidate (`select_candidate.py`: no re-tuning until lucky). To retry after completion, start a new run. `bin\rollback.ps1 -Config <cfg> -Baseline` prints the baseline values and writes nothing. | `tests/test_spsa_harness.py` rollback tests; `tests/test_confirm.py` (post-completion rollback refused) |
