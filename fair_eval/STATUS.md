# JOB D - Fair evaluation-candidate builds - STATUS

**Job start:** 2026-11-11 12:38 PC clock (PST label). **Last update:** 2026-11-11 12:55. **Elapsed useful work:** ~0.3 h.
**Branch:** `fable/fair-eval-builds-20261111`, cut from lock `16833ecc03b425586f91f4c8834dea8807bf4c22`. **State: IN PROGRESS (Step 1).**

## Done
- Isolated clone `D:\forge_jobs_20261111\fairD` (core.autocrlf=false so files are byte-exact).
- Identities verified:
  - lock source: 20/20 files pass `sha256sum -c windows_build/SOURCE_INPUTS.sha256`; manifest sha256 `3389cfe3...7645`.
  - lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe` md5 `c0051c99695f48bf93272d96fe7548c3`, sha256 `e1284f7f...802e`.
  - s198 net `src/nnue_weights.inc` md5 `22b4b9e2c61b37c0450f13a3a92c19b3`.
  - PGO workload v1 `windows_build/frozen_train_cmds.txt` sha256 `1d52720a...ce30`.
- Original lock exe run here: all ten bench pins equal LOCK.md (`fair_eval/results/lock_ref/pins_original_lock_exe.txt`).
- The lock UCI has no static-evaluation command (only `bench`, `go perft`), so 12k evals need a diagnostic build.

## Pending (plan order)
1. EVIDENCE_MATRIX.md (INT8/VNNI, KB8 U8, KB8 run 5: previous verdict, control, PGO coverage, open question).
2. Source switches FORGE_NNUE_INT8_VNNI / FORGE_NNUE_V2 / FORGE_FAIR_DIAG, macro-0 preprocess identity.
3. `fair_eval/build_fair.ps1` per-config PGO builds + coverage proof.
4. 12k FEN arithmetic controls. 5. ABBA vs lock. 6. REPORT.md.

## Process ownership
No long-running process of this job is alive. Six `python` processes existed before the job started; not mine, untouched.

## Next exact command
`git -C D:\forge_jobs_20261111\fairD show origin/int8:opus_nnue_int8_vnni/int8_vnni_after_w6.patch | git apply --check --directory=forge-combo29 -`

## Blockers
None.
