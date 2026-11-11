# JOB D - Fair evaluation-candidate builds - STATUS

**Job start:** 2026-11-11 12:38 PC clock (PST label). **Last update:** 2026-11-11 12:50 PC clock.
**Elapsed useful work:** about 1.2 h (planning and evidence reading before the clone included).
**Branch:** `fable/fair-eval-builds-20261111`, cut from lock `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**State: IN PROGRESS - Step 2 (per-configuration profiling).**

## Done
- Isolated clone `D:\forge_jobs_20261111\fairD` (core.autocrlf=false, files byte-exact).
- Identities verified: 20/20 lock source files pass the manifest (sha256 `3389cfe3...7645`); lock exe md5
  `c0051c99695f48bf93272d96fe7548c3`; s198 `nnue_weights.inc` md5 `22b4b9e2c61b37c0450f13a3a92c19b3`; workload v1
  sha256 `1d52720a...ce30`. Original lock exe: all ten bench pins + perft 5 reproduced
  (`results/lock_ref/pins_original_lock_exe.txt`).
- `EVIDENCE_MATRIX.md` written (INT8 defect confirmed from its own BENCH.md; KB8 U8 / run 5 are a different case).
- Engine tree `forge-combo29/` now carries both candidates behind switches that default to 0:
  - INT8/VNNI: `int8_vnni_after_w6.patch` (md5 `9a2ad0b4`) applied with no fuzz; weights md5 `25982cc2`.
  - v2 net path: diff `fe0da8d..9037f2a` of `D:\o30\repos\v2root` (= the v2p4 gate source), one trivial reject fixed.
  - `tools/apply_switch_guards.py` added `FORGE_NNUE_V2`, `FORGE_NNUE_V2_HOT`, `FORGE_NNUE_INT8_DEFAULT`, `FORGE_FAIR_DIAG`.
  - With all switches 0 the eight units preprocess identically to the pinned lock source (`results/pp_identity_macro0.txt`).
- `build_fair.ps1` + `configs.json` + `tools/profile_coverage.py` work. Built so far (about 11 s each, 16 jobs):

| config | training nodes d11/d13/d16 | coverage from the profile | exe md5 |
|---|---|---|---|
| `base_resid` | 312866 / 862329 / 3024920 (= lock pins) | float `nnue::evaluate` 2,530,181 entries | `b794beb419d3140354ff8b10f452b5d0` |
| `int8` | 326976 / 760289 / 3282449 (= the ON nodes the INT8 job recorded) | `int8_l1_sum` 2,832,503, `update_int8` 3,412,421 | `09b80085063b1949a23f6077a3b9f4b7` |
| `int8_cold` | 312866 / 862329 / 3024920 | `int8_l1_sum`, `refresh_int8`, `update_int8` all **0** = the defect reproduced | `a192f1ef57326f50349bb5e4d7aa705c` |

Exes are local only: `D:\forge_jobs_20261111\fairD\_work\builds\<config>_<identity>\forge_fair_<config>.exe`.

## Pending (plan order)
1. v2 nets into `_work\nets` (lock replica KB8 written by the v2 net tool, U8, run 5; sha256 checked), then configs
   `v2kb8_lockrep`, `v2kb8_lockrep_hot`, `v2kb8_U8`, `v2kb8_r5`.
2. Diag twins + `diag_ref`; 12k FEN arithmetic controls (acceptance bounds are in the approved plan, repeated in REPORT.md).
3. ABBA vs the lock exe, 16 pairs per arm, `bench 20`, one pinned core.
4. REPORT.md.

## Process ownership
No long-running process of this job is alive between commands. Six `python` processes existed before the job
started; not mine, untouched.

## Next exact command
`git show origin/o30:opus_30h/a/o30_v2net.py > fair_eval/tools/o30_v2net.py` then write the lock net as a KB8 file,
then `pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config v2kb8_lockrep`.

## Blockers
None.
